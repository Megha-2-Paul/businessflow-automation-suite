"""Integration tests for demo seeding and business dashboard calculations."""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from database.demo_data import seed_demo_records
from database.models import (
    Business,
    Invoice,
    Order,
    ProcessingJob,
    Product,
    StockMovement,
)
from database.session import get_session_factory, initialize_database
from reporting.dashboard import dashboard_insights

DEMO_DATE = date(2026, 11, 4)


def create_business(url: str, name: str = "Test Business") -> int:
    initialize_database(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        business = Business(name=name, currency="USD")
        session.add(business)
        session.flush()
        return business.id


def test_demo_seed_is_repeatable_and_stock_ledger_balances(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    create_business(url, "Synthetic Test Business")
    factory = get_session_factory(url)
    seed_demo_records(url, today=DEMO_DATE)
    seed_demo_records(url, today=DEMO_DATE)

    with factory() as session:
        assert session.scalar(select(func.count(Product.id))) == 12
        assert session.scalar(select(func.count(Order.id))) == 29
        assert session.scalar(select(func.count(Invoice.id))) == 19
        assert session.scalar(select(func.count(ProcessingJob.id))) == 33
        assert session.scalar(select(func.count(StockMovement.id))) == 22
        assert session.scalar(
            select(func.count(Order.id)).where(Order.status == "Fulfilled")
        ) == 10

        for product in session.scalars(select(Product)):
            movements = session.scalars(
                select(StockMovement)
                .where(StockMovement.product_id == product.id)
                .order_by(StockMovement.created_at, StockMovement.id)
            ).all()
            balance = Decimal("0")
            for movement in movements:
                balance += movement.quantity_delta
                assert movement.quantity_after == balance
            assert product.stock_on_hand == balance


def test_demo_seed_preserves_existing_products(tmp_path):
    url = f"sqlite:///{tmp_path / 'existing.db'}"
    business_id = create_business(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        session.add(Product(
            business_id=business_id, sku="EXISTING-001",
            name="Existing product", stock_on_hand=Decimal("5"),
            reorder_level=Decimal("2"),
        ))

    seed_demo_records(url, today=DEMO_DATE)
    seed_demo_records(url, today=DEMO_DATE)
    with factory() as session:
        assert session.scalar(select(func.count(Product.id))) == 13
        assert session.scalar(
            select(func.count(Product.id)).where(Product.sku == "EXISTING-001")
        ) == 1


def test_dashboard_uses_saved_data_and_keeps_currencies_separate(tmp_path):
    url = f"sqlite:///{tmp_path / 'dashboard.db'}"
    business_id = create_business(url, "Dashboard Test")
    factory = get_session_factory(url)
    seed_demo_records(url, today=DEMO_DATE)

    with factory.begin() as session:
        session.add_all([
            Order(
                business_id=business_id, order_number="EUR-001",
                customer_name="Currency Test", order_date=DEMO_DATE,
                currency="EUR", status="Confirmed", total=Decimal("100"),
            ),
            Order(
                business_id=business_id, order_number="CANCELLED-001",
                customer_name="Cancelled Test", order_date=DEMO_DATE,
                currency="USD", status="Cancelled", total=Decimal("500"),
            ),
            Order(
                business_id=business_id, order_number="DRAFT-001",
                customer_name="Draft Test", order_date=DEMO_DATE,
                currency="USD", status="Draft", total=Decimal("250"),
            ),
        ])

    result = dashboard_insights(url, today=DEMO_DATE)
    assert result["business_name"] == "Dashboard Test"
    assert result["currency"] == "USD"
    assert len(result["monthly_trend"]) == 6
    assert result["kpis"]["orders"] > 0
    assert result["kpis"]["order_value"] > 0
    assert 0 <= result["kpis"]["fulfillment_rate"] <= 100
    assert result["kpis"]["active_products"] == 12
    assert result["kpis"]["low_stock"] >= 2
    assert all(row["Order value"] >= 0 for row in result["monthly_trend"])

    totals = {row["Currency"]: row for row in result["currency_totals"]}
    assert totals["EUR"]["Orders"] == 1
    assert totals["EUR"]["Order value"] == 100.0
    statuses = {row["Status"] for row in result["status_mix"]}
    assert "Cancelled" not in statuses
    assert "Draft" in statuses


def test_dashboard_returns_zeroed_metrics_for_empty_workspace(tmp_path):
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    initialize_database(url)
    result = dashboard_insights(url, today=DEMO_DATE)

    assert result["business_name"] == "No workspace"
    assert result["kpis"]["orders"] == 0
    assert result["kpis"]["order_value"] == 0.0
    assert result["monthly_trend"] == []
    assert result["invoice_summary"]["total"] == 0
