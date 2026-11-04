"""Order creation, editing, status and persistence services."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.models import (
    Business, Order, OrderLineItem, Product, ProcessingJob, ProcessingLog, StockMovement,
)
from database.session import get_session_factory, initialize_database
from orders.validation import OrderValidationError, clean_line_items

STATUSES = ("Draft", "Confirmed", "Processing", "Fulfilled", "Cancelled")
_TRANSITIONS = {
    "Draft": {"Confirmed", "Cancelled"},
    "Confirmed": {"Processing", "Cancelled"},
    "Processing": {"Fulfilled", "Cancelled"},
    "Fulfilled": set(),
    "Cancelled": set(),
}


class OrderServiceError(ValueError):
    """Raised when an order operation cannot be completed."""


def _business_id(session) -> int:
    business = session.scalar(select(Business).order_by(Business.id).limit(1))
    if business is None:
        business = Business(name="Local Workspace")
        session.add(business)
        session.flush()
    return business.id


def _validate_product_links(session, business_id: int, lines: list[dict[str, Any]]) -> None:
    """Ensure linked order products belong to this workspace and are active."""
    product_ids = {line["product_id"] for line in lines if line.get("product_id") is not None}
    if not product_ids:
        return
    products = session.scalars(select(Product).where(Product.id.in_(product_ids))).all()
    if len(products) != len(product_ids) or any(
        product.business_id != business_id or not product.is_active for product in products
    ):
        raise OrderServiceError("Order products must be active items in this workspace.")


def _record_activity(session, business_id: int, message: str) -> None:
    now = datetime.now(UTC)
    job = ProcessingJob(
        business_id=business_id, job_type="order_management", status="completed",
        records_processed=1, records_succeeded=1, records_failed=0,
        started_at=now, completed_at=now,
    )
    session.add(job)
    session.flush()
    session.add(ProcessingLog(job_id=job.id, level="INFO", message=message))


def create_order(
    database_url: str, *, order_number: str, customer_name: str,
    customer_email: str = "", order_date: date | None = None,
    currency: str = "USD", line_items: list[dict[str, Any]],
) -> int:
    """Create a draft order and its lines atomically."""
    number, customer, code = order_number.strip(), customer_name.strip(), currency.strip().upper()
    if not number or not customer:
        raise OrderServiceError("Order number and customer name are required.")
    if len(code) != 3 or not code.isalpha():
        raise OrderServiceError("Currency must be a three-letter code, such as USD.")
    try:
        lines = clean_line_items(line_items)
    except OrderValidationError as exc:
        raise OrderServiceError(str(exc)) from exc
    total = sum((line["amount"] for line in lines), Decimal("0.00"))
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    try:
        with factory.begin() as session:
            business_id = _business_id(session)
            _validate_product_links(session, business_id, lines)
            order = Order(
                business_id=business_id, order_number=number[:120],
                customer_name=customer[:200],
                customer_email=customer_email.strip()[:254] or None,
                order_date=order_date or date.today(), currency=code,
                status="Draft", total=total,
            )
            session.add(order)
            session.flush()
            order.line_items.extend(
                OrderLineItem(order_id=order.id, **line) for line in lines
            )
            _record_activity(session, business_id, f"Order {number} created as draft.")
            return order.id
    except IntegrityError as exc:
        raise OrderServiceError(
            "An order with this number already exists in this workspace."
        ) from exc


def update_order(
    database_url: str, order_id: int, *, customer_name: str,
    customer_email: str = "", order_date: date | None = None,
    currency: str = "USD", line_items: list[dict[str, Any]],
) -> None:
    """Replace editable order details and lines without changing its status."""
    customer, code = customer_name.strip(), currency.strip().upper()
    if not customer:
        raise OrderServiceError("Customer name is required.")
    if len(code) != 3 or not code.isalpha():
        raise OrderServiceError("Currency must be a three-letter code, such as USD.")
    try:
        lines = clean_line_items(line_items)
    except OrderValidationError as exc:
        raise OrderServiceError(str(exc)) from exc
    total = sum((line["amount"] for line in lines), Decimal("0.00"))
    with get_session_factory(database_url).begin() as session:
        order = session.get(Order, order_id)
        if order is None:
            raise OrderServiceError("Order was not found.")
        if order.status != "Draft":
            raise OrderServiceError("Only draft orders can be edited.")
        _validate_product_links(session, order.business_id, lines)
        order.customer_name = customer[:200]
        order.customer_email = customer_email.strip()[:254] or None
        order.order_date = order_date or order.order_date
        order.currency = code
        order.total = total
        order.line_items.clear()
        session.flush()
        order.line_items.extend(
            OrderLineItem(order_id=order.id, **line) for line in lines
        )
        _record_activity(session, order.business_id, f"Draft order {order.order_number} updated.")


def change_order_status(database_url: str, order_id: int, new_status: str) -> None:
    """Apply an allowed forward status transition and record the change."""
    if new_status not in STATUSES:
        raise OrderServiceError("Select a valid order status.")
    with get_session_factory(database_url).begin() as session:
        order = session.get(Order, order_id)
        if order is None:
            raise OrderServiceError("Order was not found.")
        if new_status not in _TRANSITIONS.get(order.status, set()):
            raise OrderServiceError(
                f"Cannot change an order from {order.status} to {new_status}."
            )
        previous = order.status
        if new_status == "Fulfilled":
            linked_lines = [line for line in order.line_items if line.product_id is not None]
            required: dict[int, Decimal] = {}
            for line in linked_lines:
                required[line.product_id] = required.get(line.product_id, Decimal("0")) + line.quantity
            for product_id, quantity in required.items():
                product = session.scalar(
                    select(Product).where(Product.id == product_id).with_for_update()
                )
                if product is None or product.business_id != order.business_id or not product.is_active:
                    raise OrderServiceError("An order product is unavailable in this workspace.")
                if product.stock_on_hand < quantity:
                    raise OrderServiceError(
                        f"Insufficient stock for {product.sku}: "
                        f"{product.stock_on_hand} available, {quantity} required."
                    )
                product.stock_on_hand -= quantity
                session.add(StockMovement(
                    product_id=product.id, order_id=order.id,
                    movement_type="order_fulfilment", quantity_delta=-quantity,
                    quantity_after=product.stock_on_hand,
                    reference=f"Order {order.order_number}",
                ))
        order.status = new_status
        _record_activity(
            session, order.business_id,
            f"Order {order.order_number} status changed: {previous} to {new_status}.",
        )
