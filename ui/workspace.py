"""Workspace selection and isolated demonstration data."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import streamlit as st
from sqlalchemy import select

from config.settings import PROJECT_ROOT
from database.models import (
    Business, Invoice, InvoiceLineItem, Order, OrderLineItem,
    ProcessingJob, ProcessingLog, Product, StockMovement,
)
from database.session import get_session_factory, initialize_database

DEMO_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'data' / 'businessflow-demo.db').as_posix()}"


def get_database_url(default_url: str) -> str:
    """Return the database selected for the current Streamlit session."""
    return DEMO_DATABASE_URL if st.session_state.get("bf_workspace_mode") == "Demo" else default_url


def configure_workspace(default_url: str) -> str:
    """Render the workspace selector and initialise the isolated demo database."""
    selected = st.sidebar.selectbox(
        "Workspace",
        ["Live workspace", "Demo workspace"],
        key="bf_workspace_selector",
        help="Demo data is stored in a separate local database and never changes live records.",
    )
    mode = "Demo" if selected == "Demo workspace" else "Live"
    st.session_state["bf_workspace_mode"] = mode
    if mode == "Demo":
        initialize_demo_workspace()
        st.sidebar.info("Demonstration data · isolated from live records")
        return DEMO_DATABASE_URL
    st.sidebar.caption("Live business data")
    return default_url


def initialize_demo_workspace(database_url: str = DEMO_DATABASE_URL) -> None:
    """Create a small, clearly fictional dataset once in the demo database."""
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    with factory.begin() as session:
        if session.scalar(select(Business.id).limit(1)) is not None:
            return

        business = Business(name="Demo Business", currency="USD", timezone="UTC")
        session.add(business)
        session.flush()

        products = [
            Product(
                business_id=business.id, sku="DEMO-1001", name="Wireless Mouse",
                unit="unit", stock_on_hand=Decimal("42"), reorder_level=Decimal("10"),
            ),
            Product(
                business_id=business.id, sku="DEMO-1002", name="USB-C Keyboard",
                unit="unit", stock_on_hand=Decimal("8"), reorder_level=Decimal("12"),
            ),
            Product(
                business_id=business.id, sku="DEMO-1003", name="Laptop Stand",
                unit="unit", stock_on_hand=Decimal("25"), reorder_level=Decimal("8"),
            ),
        ]
        session.add_all(products)
        session.flush()

        session.add_all([
            StockMovement(
                product_id=products[0].id, movement_type="opening_balance",
                quantity_delta=Decimal("42"), quantity_after=Decimal("42"),
                reference="DEMO-OPENING", notes="Fictional demonstration opening balance",
            ),
            StockMovement(
                product_id=products[1].id, movement_type="opening_balance",
                quantity_delta=Decimal("8"), quantity_after=Decimal("8"),
                reference="DEMO-OPENING", notes="Fictional demonstration opening balance",
            ),
            StockMovement(
                product_id=products[2].id, movement_type="opening_balance",
                quantity_delta=Decimal("25"), quantity_after=Decimal("25"),
                reference="DEMO-OPENING", notes="Fictional demonstration opening balance",
            ),
        ])

        order = Order(
            business_id=business.id, order_number="DEMO-ORD-1001",
            customer_name="Sample Customer", customer_email="customer@example.invalid",
            order_date=date.today(), currency="USD", status="Confirmed",
            total=Decimal("79.98"),
        )
        session.add(order)
        session.flush()
        session.add(OrderLineItem(
            order_id=order.id, description="Wireless Mouse", quantity=Decimal("2"),
            unit_price=Decimal("39.99"), amount=Decimal("79.98"),
            product_id=products[0].id,
        ))

        job = ProcessingJob(
            business_id=business.id, job_type="invoice_extraction",
            status="completed", records_processed=1, records_succeeded=1,
            records_failed=0,
        )
        session.add(job)
        session.flush()
        session.add(Invoice(
            business_id=business.id, processing_job_id=job.id,
            supplier="Example Office Supplies", invoice_number="DEMO-INV-2001",
            invoice_date=date.today() - timedelta(days=2),
            due_date=date.today() + timedelta(days=28), currency="USD",
            subtotal=Decimal("120.00"), tax=Decimal("12.00"),
            total=Decimal("132.00"), source_filename="demo-invoice.pdf",
            page_count=1, review_status="confirmed",
        ))
        session.add(ProcessingLog(
            job_id=job.id, level="INFO",
            message="Fictional demonstration invoice reviewed and saved.",
        ))
