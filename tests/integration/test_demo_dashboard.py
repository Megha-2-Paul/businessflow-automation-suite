"""Integration tests for repeatable demo seeding and business dashboard metrics."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from database.demo_data import seed_demo_records
from database.models import Business, Invoice, Order, Product, ProcessingJob, StockMovement
from database.session import get_session_factory, initialize_database
from reporting.dashboard import dashboard_insights


def test_demo_seed_is_repeatable_and_relationships_are_persisted(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    initialize_database(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        session.add(Business(name="Synthetic Test Business", currency="USD"))

    seed_demo_records(url, today=date(2026, 11, 4))
    seed_demo_records(url, today=date(2026, 11, 4))

    with factory() as session:
        assert session.scalar(select(func.count(Product.id))) == 12
        assert session.scalar(select(func.count(Order.id))) == 29
        assert session.scalar(select(func.count(Invoice.id))) == 19
        assert session.scalar(select(func.count(ProcessingJob.id))) == 33
        assert session.scalar(select(func.count(StockMovement.id))) == 22
        assert session.scalar(select(func.count(Order.id)).where(
            Order.status == "Fulfilled"
        )) > 0
        assert session.scalar(select(func.count(Order.id)).where(
            Order.total <= Decimal("0")
        )) == 0


def test_dashboard_insights_are_derived_from_records_and_currency(tmp_path):
    url = f"sqlite:///{tmp_path / 'dashboard.db'}"
    initialize_database(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        session.add(Business(name="Dashboard Test", currency="USD"))
    seed_demo_records(url, today=date(2026, 11, 4))

    result = dashboard_insights(url, today=date(2026, 11, 4))
    assert result["business_name"] == "Dashboard Test"
    assert result["currency"] == "USD"
    assert len(result["monthly_trend"]) == 6
    assert result["kpis"]["orders"] > 0
    assert result["kpis"]["order_value"] > 0
    assert 0 <= result["kpis"]["fulfillment_rate"] <= 100
    assert result["kpis"]["active_products"] == 12
    assert result["kpis"]["low_stock"] >= 0
    assert all(row["Order value"] >= 0 for row in result["monthly_trend"])
