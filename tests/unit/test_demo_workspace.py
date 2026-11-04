"""Tests for isolated demonstration workspace data."""
from sqlalchemy import func, select

from database.models import Business, Invoice, Order, Product
from database.session import get_session_factory, initialize_database
from reporting.service import dashboard_summary
from ui.workspace import initialize_demo_workspace


def test_demo_workspace_seeds_isolated_sample_records(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'demo.sqlite').as_posix()}"

    initialize_demo_workspace(database_url)
    initialize_demo_workspace(database_url)

    factory = get_session_factory(database_url)
    with factory() as session:
        assert session.scalar(select(func.count(Business.id))) == 1
        assert session.scalar(select(func.count(Product.id))) == 12
        assert session.scalar(select(func.count(Order.id))) == 29
        assert session.scalar(select(func.count(Invoice.id))) == 19

    summary = dashboard_summary(database_url)
    assert summary["business_name"] == "Demo Business"
    assert summary["orders_total"] == 29
    assert summary["invoices_confirmed"] == 19
    assert summary["products_active"] == 12
    assert summary["products_low_stock"] == 2


def test_demo_workspace_preserves_existing_database_records(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'existing.sqlite').as_posix()}"
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    with factory.begin() as session:
        session.add(Business(name="Real Workspace"))

    initialize_demo_workspace(database_url)

    with factory() as session:
        names = session.scalars(select(Business.name)).all()
    assert names == ["Real Workspace"]
