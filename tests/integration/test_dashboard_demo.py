"""Integration tests for the demo seeder and live dashboard analytics."""
from collections import defaultdict

import pytest
from sqlalchemy import func, select

from database.demo_data import seed_demo_data
from database.models import (
    Business,
    Invoice,
    Order,
    OrderLineItem,
    Product,
    StockMovement,
)
from database.session import get_session_factory
from reporting.dashboard import dashboard_metrics


def test_demo_seed_is_repeatable_and_relationally_consistent(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    seed_demo_data(url)
    seed_demo_data(url)

    factory = get_session_factory(url)
    with factory() as session:
        assert session.scalar(select(func.count(Business.id))) == 1
        assert session.scalar(select(func.count(Product.id))) == 12
        assert session.scalar(select(func.count(Order.id))) == 30
        assert session.scalar(select(func.count(Invoice.id))) == 20
        assert session.scalar(select(func.count(OrderLineItem.id))) == 60
        assert session.scalar(select(func.count(StockMovement.id))) == 36

        products = session.scalars(select(Product)).all()
        movements = session.scalars(select(StockMovement)).all()
        ledger_totals = defaultdict(int)
        for movement in movements:
            ledger_totals[movement.product_id] += int(movement.quantity_delta)
        for product in products:
            assert ledger_totals[product.id] == int(product.stock_on_hand)
            assert product.stock_on_hand >= 0

        assert session.scalar(
            select(func.count(Order.id)).where(Order.status == "Fulfilled")
        ) > 0
        assert session.scalar(
            select(func.count(Order.id)).where(Order.status == "Processing")
        ) > 0


def test_dashboard_metrics_are_calculated_from_saved_records(tmp_path):
    url = f"sqlite:///{tmp_path / 'analytics.db'}"
    seed_demo_data(url)

    summary = dashboard_metrics(url, 90)

    assert summary["business_name"] == "Northstar Office & Tech (Demo)"
    assert summary["period_days"] == 90
    assert summary["orders_count"] > 0
    assert summary["active_products"] == 12
    assert summary["confirmed_invoices"] > 0
    assert summary["order_trend"]
    assert sum(row["Orders"] for row in summary["order_statuses"]) == summary["orders_count"]
    assert {row["Currency"] for row in summary["currency_totals"]} == {"USD"}
    assert summary["low_stock_count"] > 0
    assert {row["Stock status"] for row in summary["stock_groups"]} == {
        "Healthy", "Low stock", "Out of stock"
    }


def test_dashboard_rejects_unsupported_period_and_handles_empty_database(tmp_path):
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    with pytest.raises(ValueError, match="30, 90 or 365"):
        dashboard_metrics(url, 60)

    summary = dashboard_metrics(url, 30)
    assert summary["business_name"] == "No workspace"
    assert summary["orders_count"] == 0
    assert summary["order_trend"] == []


def test_order_value_kpis_exclude_draft_and_cancelled_orders(tmp_path):
    url = f"sqlite:///{tmp_path / 'order-value.db'}"
    seed_demo_data(url)
    summary = dashboard_metrics(url, 365)
    factory = get_session_factory(url)
    with factory() as session:
        committed = session.scalars(
            select(Order).where(Order.status.in_(["Confirmed", "Processing", "Fulfilled"]))
        ).all()
    expected = sum(order.total for order in committed)
    assert summary["currency_totals"][0]["Order value"] == float(expected)
