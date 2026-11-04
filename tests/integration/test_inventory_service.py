"""Integration tests for catalogue, stock ledger and order fulfilment."""
from decimal import Decimal

import pytest

from database.models import InventoryCount, Product, StockMovement
from database.session import get_session_factory
from services.inventory_service import (
    InventoryServiceError,
    adjust_stock,
    create_product,
    create_stocktake,
    reconcile_stocktake,
)
from services.order_service import (
    OrderServiceError,
    change_order_status,
    create_order,
)


def test_product_opening_balance_receipt_issue_and_sku_validation(tmp_path):
    url = f"sqlite:///{tmp_path / 'inventory.db'}"
    product_id = create_product(
        url, sku="sku-1", name="Paper", unit="ream",
        reorder_level="3", opening_stock="10",
    )
    with get_session_factory(url)() as session:
        product = session.get(Product, product_id)
        assert product.stock_on_hand == Decimal("10.000")
        assert session.query(StockMovement).count() == 1
    adjust_stock(url, product_id, movement_type="receipt", quantity="2.5")
    adjust_stock(url, product_id, movement_type="issue", quantity="4")
    with get_session_factory(url)() as session:
        assert session.get(Product, product_id).stock_on_hand == Decimal("8.500")
        assert session.query(StockMovement).count() == 3
    with pytest.raises(InventoryServiceError, match="already exists"):
        create_product(url, sku="SKU-1", name="Duplicate")
    with pytest.raises(InventoryServiceError, match="negative"):
        adjust_stock(url, product_id, movement_type="issue", quantity="9")
    with pytest.raises(InventoryServiceError, match="greater than zero"):
        adjust_stock(url, product_id, movement_type="receipt", quantity="0")


def test_stocktake_requires_review_and_reconciles_once(tmp_path):
    url = f"sqlite:///{tmp_path / 'stocktake.db'}"
    product_id = create_product(url, sku="A-1", name="Cable", opening_stock="12")
    count_id = create_stocktake(
        url, counts=[{"product_id": product_id, "counted_quantity": "9"}],
        notes="Monthly count",
    )
    with get_session_factory(url)() as session:
        count = session.get(InventoryCount, count_id)
        assert count.status == "draft"
    reconcile_stocktake(url, count_id)
    with get_session_factory(url)() as session:
        assert session.get(Product, product_id).stock_on_hand == Decimal("9.000")
        count = session.get(InventoryCount, count_id)
        assert count.status == "reconciled"
        movement = session.query(StockMovement).filter_by(
            movement_type="stocktake_adjustment"
        ).one()
        assert movement.quantity_delta == Decimal("-3.000")
    with pytest.raises(InventoryServiceError, match="already been reconciled"):
        reconcile_stocktake(url, count_id)


def test_stocktake_rejects_duplicate_products_and_stale_snapshots(tmp_path):
    url = f"sqlite:///{tmp_path / 'stale.db'}"
    product_id = create_product(url, sku="A-2", name="Adapter", opening_stock="5")
    with pytest.raises(InventoryServiceError, match="only once"):
        create_stocktake(url, counts=[
            {"product_id": product_id, "counted_quantity": "5"},
            {"product_id": product_id, "counted_quantity": "4"},
        ])
    count_id = create_stocktake(
        url, counts=[{"product_id": product_id, "counted_quantity": "4"}]
    )
    adjust_stock(url, product_id, movement_type="receipt", quantity="1")
    with pytest.raises(InventoryServiceError, match="changed since"):
        reconcile_stocktake(url, count_id)


def test_order_fulfilment_deducts_stock_atomically_and_once(tmp_path):
    url = f"sqlite:///{tmp_path / 'order-stock.db'}"
    product_id = create_product(url, sku="P-1", name="Widget", opening_stock="5")
    order_id = create_order(
        url, order_number="SO-1", customer_name="Customer",
        line_items=[{
            "description": "Widget", "quantity": "3", "unit_price": "10",
            "product_id": product_id,
        }],
    )
    change_order_status(url, order_id, "Confirmed")
    change_order_status(url, order_id, "Processing")
    change_order_status(url, order_id, "Fulfilled")
    with get_session_factory(url)() as session:
        assert session.get(Product, product_id).stock_on_hand == Decimal("2.000")
        movement = session.query(StockMovement).filter_by(order_id=order_id).one()
        assert movement.quantity_delta == Decimal("-3.000")
    with pytest.raises(OrderServiceError, match="Cannot change"):
        change_order_status(url, order_id, "Fulfilled")
    with get_session_factory(url)() as session:
        assert session.get(Product, product_id).stock_on_hand == Decimal("2.000")


def test_insufficient_stock_rolls_back_order_fulfilment(tmp_path):
    url = f"sqlite:///{tmp_path / 'rollback.db'}"
    product_id = create_product(url, sku="P-2", name="Monitor", opening_stock="1")
    order_id = create_order(
        url, order_number="SO-2", customer_name="Customer",
        line_items=[{
            "description": "Monitor", "quantity": "2", "unit_price": "100",
            "product_id": product_id,
        }],
    )
    change_order_status(url, order_id, "Confirmed")
    change_order_status(url, order_id, "Processing")
    with pytest.raises(OrderServiceError, match="Insufficient stock"):
        change_order_status(url, order_id, "Fulfilled")
    with get_session_factory(url)() as session:
        from database.models import Order

        assert session.get(Order, order_id).status == "Processing"
        assert session.get(Product, product_id).stock_on_hand == Decimal("1.000")
        assert session.query(StockMovement).filter_by(order_id=order_id).count() == 0
