"""Integration tests for the seeded demo dataset and business dashboard insights."""
from database.models import Business, Invoice, Order, Product, ProcessingJob
from database.session import get_session_factory
from database.demo_data import seed_demo_dataset
from reporting.dashboard import dashboard_insights


def test_demo_seed_is_repeatable_and_populates_related_business_records(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    seed_demo_dataset(url)
    seed_demo_dataset(url)

    with get_session_factory(url)() as session:
        assert session.query(Business).count() == 1
        assert session.query(Product).count() == 12
        assert session.query(Order).count() == 30
        assert session.query(Invoice).count() == 12
        assert session.query(ProcessingJob).count() == 16


def test_dashboard_insights_are_derived_from_seeded_records(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo-insights.db'}"
    seed_demo_dataset(url)

    insights = dashboard_insights(url)
    assert sum(row["Orders"] for row in insights["monthly_orders"]) > 0
    assert {row["Currency"] for row in insights["order_value_by_currency"]} == {"USD", "EUR"}
    assert insights["eligible_orders"] == 25
    assert insights["fulfilled_orders"] == 10
    assert insights["fulfilment_rate"] == 40.0
    assert len(insights["low_stock_products"]) >= 3
    assert insights["confirmed_invoice_count"] == 12
    assert {row["Currency"] for row in insights["invoice_totals"]} == {"USD", "EUR"}
