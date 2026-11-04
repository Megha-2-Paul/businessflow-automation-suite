"""Integration tests for isolated synthetic demo data and dashboard metrics."""
from sqlalchemy import func, select

from database.models import Business, DatasetSource, Invoice, Order, Product, StockMovement
from database.session import get_session_factory, initialize_database
from reporting.service import dashboard_summary
from ui.demo_data import seed_demo_dataset


def test_demo_seed_is_repeatable_and_populates_related_business_records(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    initialize_database(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        session.add(Business(name="Synthetic Demo", currency="USD"))

    seed_demo_dataset(url)
    seed_demo_dataset(url)

    with factory() as session:
        assert session.scalar(select(func.count(Product.id))) == 12
        assert session.scalar(select(func.count(Order.id))) == 30
        assert session.scalar(select(func.count(Invoice.id))) == 20
        assert session.scalar(select(func.count(StockMovement.id))) == 12
        assert session.scalar(select(func.count(DatasetSource.id))) == 1

    summary = dashboard_summary(url)
    assert summary["orders_total"] == 30
    assert summary["products_active"] == 12
    assert summary["orders_this_month"] >= 0
    assert summary["monthly_order_trend"]
    assert summary["current_month_order_totals"] == sorted(
        summary["current_month_order_totals"], key=lambda row: row["Currency"]
    )
    assert summary["confirmed_vendor_payables"]
    assert summary["overdue_invoice_count"] > 0


def test_empty_workspace_has_safe_dashboard_metrics(tmp_path):
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    initialize_database(url)
    with get_session_factory(url)() as session:
        session.add(Business(name="Empty Workspace", currency="USD"))
        session.commit()

    summary = dashboard_summary(url)
    assert summary["orders_this_month"] == 0
    assert summary["fulfillment_rate"] is None
    assert summary["monthly_order_trend"] == []
    assert summary["confirmed_vendor_payables"] == []
