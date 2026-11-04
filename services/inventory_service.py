"""Transactional product, stock movement and stocktake operations."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.models import (
    Business, InventoryCount, InventoryCountLine, Product, ProcessingJob,
    ProcessingLog, StockMovement,
)
from database.session import get_session_factory, initialize_database
from inventory.validation import (
    InventoryValidationError, nonnegative_quantity, positive_quantity,
)


class InventoryServiceError(ValueError):
    """Raised when an inventory operation cannot be completed."""


def _business_id(session) -> int:
    business = session.scalar(select(Business).order_by(Business.id).limit(1))
    if business is None:
        business = Business(name="Local Workspace")
        session.add(business)
        session.flush()
    return business.id


def _activity(session, business_id: int, message: str) -> None:
    now = datetime.now(UTC)
    job = ProcessingJob(
        business_id=business_id, job_type="inventory_management", status="completed",
        records_processed=1, records_succeeded=1, records_failed=0,
        started_at=now, completed_at=now,
    )
    session.add(job)
    session.flush()
    session.add(ProcessingLog(job_id=job.id, level="INFO", message=message))


def create_product(
    database_url: str, *, sku: str, name: str, unit: str = "unit",
    reorder_level: Any = "0", opening_stock: Any = "0",
) -> int:
    """Create a catalogue product and optional opening-balance ledger entry."""
    sku_value, name_value, unit_value = sku.strip().upper(), name.strip(), unit.strip()
    if not sku_value or not name_value or not unit_value:
        raise InventoryServiceError("SKU, product name and unit are required.")
    if len(sku_value) > 80 or len(name_value) > 200 or len(unit_value) > 30:
        raise InventoryServiceError("SKU, name or unit exceeds its allowed length.")
    try:
        reorder = nonnegative_quantity(reorder_level, "Reorder level")
        opening = nonnegative_quantity(opening_stock, "Opening stock")
    except InventoryValidationError as exc:
        raise InventoryServiceError(str(exc)) from exc
    initialize_database(database_url)
    try:
        with get_session_factory(database_url).begin() as session:
            business_id = _business_id(session)
            product = Product(
                business_id=business_id, sku=sku_value, name=name_value,
                unit=unit_value, stock_on_hand=opening, reorder_level=reorder,
            )
            session.add(product)
            session.flush()
            if opening:
                session.add(StockMovement(
                    product_id=product.id, movement_type="opening_balance",
                    quantity_delta=opening, quantity_after=opening,
                    reference="Opening balance",
                ))
            _activity(session, business_id, f"Product {sku_value} created.")
            return product.id
    except IntegrityError as exc:
        raise InventoryServiceError("A product with this SKU already exists in this workspace.") from exc


def update_product(
    database_url: str, product_id: int, *, name: str, unit: str,
    reorder_level: Any, is_active: bool,
) -> None:
    """Update catalogue details without changing stock balances."""
    if not name.strip() or not unit.strip():
        raise InventoryServiceError("Product name and unit are required.")
    try:
        reorder = nonnegative_quantity(reorder_level, "Reorder level")
    except InventoryValidationError as exc:
        raise InventoryServiceError(str(exc)) from exc
    with get_session_factory(database_url).begin() as session:
        product = session.get(Product, product_id)
        if product is None:
            raise InventoryServiceError("Product was not found.")
        product.name, product.unit = name.strip()[:200], unit.strip()[:30]
        product.reorder_level, product.is_active = reorder, bool(is_active)
        _activity(session, product.business_id, f"Product {product.sku} updated.")


def adjust_stock(
    database_url: str, product_id: int, *, movement_type: str, quantity: Any,
    reference: str = "", notes: str = "",
) -> None:
    """Receive, issue or adjust stock and append an immutable ledger entry."""
    if movement_type not in {"receipt", "issue", "adjustment"}:
        raise InventoryServiceError("Choose receipt, issue or adjustment.")
    try:
        amount = positive_quantity(quantity)
    except InventoryValidationError as exc:
        raise InventoryServiceError(str(exc)) from exc
    with get_session_factory(database_url).begin() as session:
        product = session.scalar(
            select(Product).where(Product.id == product_id).with_for_update()
        )
        if product is None:
            raise InventoryServiceError("Product was not found.")
        if not product.is_active:
            raise InventoryServiceError("Inactive products cannot receive stock movements.")
        delta = amount if movement_type == "receipt" else -amount if movement_type == "issue" else amount
        if movement_type == "adjustment":
            delta = amount
        new_balance = product.stock_on_hand + delta
        if new_balance < 0:
            raise InventoryServiceError("This movement would make stock negative.")
        product.stock_on_hand = new_balance
        session.add(StockMovement(
            product_id=product.id, movement_type=movement_type,
            quantity_delta=delta, quantity_after=new_balance,
            reference=reference.strip()[:120] or None, notes=notes.strip() or None,
        ))
        _activity(session, product.business_id, f"Stock {movement_type} recorded for {product.sku}.")


def create_stocktake(database_url: str, *, counts: list[dict[str, Any]], notes: str = "") -> int:
    """Create a draft stocktake snapshot from actual physical counts."""
    if not counts:
        raise InventoryServiceError("Enter at least one physical stock count.")
    normalized: list[tuple[int, Decimal]] = []
    seen: set[int] = set()
    try:
        for row in counts:
            product_id = int(row["product_id"])
            if product_id in seen:
                raise InventoryServiceError("A product can appear only once in a stocktake.")
            seen.add(product_id)
            normalized.append((product_id, nonnegative_quantity(row["counted_quantity"], "Counted quantity")))
    except (KeyError, TypeError, ValueError, InventoryValidationError) as exc:
        if isinstance(exc, InventoryServiceError):
            raise
        raise InventoryServiceError(str(exc) or "Invalid stocktake row.") from exc
    with get_session_factory(database_url).begin() as session:
        business_id = _business_id(session)
        stocktake = InventoryCount(business_id=business_id, notes=notes.strip() or None)
        session.add(stocktake)
        session.flush()
        for product_id, counted in normalized:
            product = session.get(Product, product_id)
            if product is None or product.business_id != business_id or not product.is_active:
                raise InventoryServiceError("Stocktake contains an unknown or inactive product.")
            session.add(InventoryCountLine(
                inventory_count_id=stocktake.id, product_id=product.id,
                recorded_quantity=product.stock_on_hand, counted_quantity=counted,
            ))
        _activity(session, business_id, f"Stocktake #{stocktake.id} prepared for review.")
        return stocktake.id


def reconcile_stocktake(database_url: str, stocktake_id: int) -> None:
    """Apply all reviewed count variances atomically and close the stocktake."""
    with get_session_factory(database_url).begin() as session:
        stocktake = session.scalar(
            select(InventoryCount).where(InventoryCount.id == stocktake_id).with_for_update()
        )
        if stocktake is None:
            raise InventoryServiceError("Stocktake was not found.")
        if stocktake.status != "draft":
            raise InventoryServiceError("This stocktake has already been reconciled.")
        for line in stocktake.lines:
            product = session.scalar(
                select(Product).where(Product.id == line.product_id).with_for_update()
            )
            if product is None:
                raise InventoryServiceError("A stocktake product no longer exists.")
            if product.stock_on_hand != line.recorded_quantity:
                raise InventoryServiceError(
                    f"Stock for {product.sku} changed after this count began. "
                    "Create a new stocktake before reconciling."
                )
            delta = line.counted_quantity - product.stock_on_hand
            if delta:
                product.stock_on_hand = line.counted_quantity
                session.add(StockMovement(
                    product_id=product.id, movement_type="stocktake_adjustment",
                    quantity_delta=delta, quantity_after=line.counted_quantity,
                    reference=f"Stocktake #{stocktake.id}",
                    notes=f"Recorded at count start: {line.recorded_quantity}; "
                          f"physical count: {line.counted_quantity}",
                ))
        stocktake.status = "reconciled"
        stocktake.reconciled_at = datetime.now(UTC)
        _activity(session, stocktake.business_id, f"Stocktake #{stocktake.id} reconciled.")


def list_products(database_url: str, *, active_only: bool = False) -> list[Product]:
    """Return products in the current workspace ordered by SKU."""
    with get_session_factory(database_url)() as session:
        business_id = _business_id(session)
        query = select(Product).where(Product.business_id == business_id)
        if active_only:
            query = query.where(Product.is_active.is_(True))
        return list(session.scalars(query.order_by(Product.sku)).all())


def list_movements(database_url: str, *, limit: int = 100) -> list[StockMovement]:
    """Return recent stock movements for the current workspace."""
    with get_session_factory(database_url)() as session:
        business_id = _business_id(session)
        return list(session.scalars(
            select(StockMovement).join(Product).where(Product.business_id == business_id)
            .order_by(StockMovement.created_at.desc()).limit(max(1, min(limit, 500)))
        ).all())
