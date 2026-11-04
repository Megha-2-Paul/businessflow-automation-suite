"""Integration tests for order persistence and lifecycle."""
from decimal import Decimal

import pytest

from database.models import Order, OrderLineItem, ProcessingJob
from database.session import get_session_factory
from services.order_service import (
    OrderServiceError,
    change_order_status,
    create_order,
    update_order,
)


def payload():
    return {
        "order_number": "SO-100",
        "customer_name": "Northwind",
        "currency": "USD",
        "line_items": [
            {"description": "Widget", "quantity": "2", "unit_price": "12.50"}
        ],
    }


def test_create_update_and_transition_order(tmp_path):
    url = f"sqlite:///{tmp_path / 'orders.db'}"
    order_id = create_order(url, **payload())
    with get_session_factory(url)() as session:
        order = session.get(Order, order_id)
        assert order.total == Decimal("25.00")
        assert len(order.line_items) == 1
        assert order.status == "Draft"
    update_order(
        url, order_id, customer_name="Northwind Ltd", currency="USD",
        line_items=[
            {"description": "Widget", "quantity": "3", "unit_price": "10"}
        ],
    )
    change_order_status(url, order_id, "Confirmed")
    change_order_status(url, order_id, "Processing")
    with get_session_factory(url)() as session:
        order = session.get(Order, order_id)
        assert order.customer_name == "Northwind Ltd"
        assert order.total == Decimal("30.00")
        assert order.status == "Processing"
        assert session.query(OrderLineItem).count() == 1
        assert session.query(ProcessingJob).filter_by(
            job_type="order_management"
        ).count() == 4


def test_duplicate_number_and_invalid_transition(tmp_path):
    url = f"sqlite:///{tmp_path / 'duplicates.db'}"
    order_id = create_order(url, **payload())
    with pytest.raises(OrderServiceError, match="already exists"):
        create_order(url, **payload())
    with pytest.raises(OrderServiceError, match="Cannot change"):
        change_order_status(url, order_id, "Fulfilled")


def test_rejects_invalid_order_and_edit_after_confirmation(tmp_path):
    url = f"sqlite:///{tmp_path / 'invalid.db'}"
    data = payload()
    data["line_items"] = [
        {"description": "Widget", "quantity": "0", "unit_price": "1"}
    ]
    with pytest.raises(OrderServiceError, match="greater than zero"):
        create_order(url, **data)
    order_id = create_order(url, **payload())
    change_order_status(url, order_id, "Confirmed")
    with pytest.raises(OrderServiceError, match="Only draft"):
        update_order(
            url, order_id, customer_name="Changed", currency="USD",
            line_items=payload()["line_items"],
        )
