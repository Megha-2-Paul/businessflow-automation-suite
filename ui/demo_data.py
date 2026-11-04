"""Deterministic, isolated synthetic data for the BusinessFlow demo workspace."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from database.models import (
    Business,
    DatasetSource,
    Invoice,
    Order,
    OrderLineItem,
    ProcessingJob,
    ProcessingLog,
    Product,
    StockMovement,
)
from database.session import get_session_factory


def seed_demo_dataset(database_url: str) -> None:
    """Add a realistic demo dataset once; never modify existing business records."""
    factory = get_session_factory(database_url)
    today = date.today()
    now = datetime.now(UTC)
    products_data = [
        ("DEMO-2001", "Wireless Mouse", "unit", "38", "12"),
        ("DEMO-2002", "USB-C Keyboard", "unit", "24", "8"),
        ("DEMO-2003", "Laptop Stand", "unit", "17", "6"),
        ("DEMO-2004", "HD Webcam", "unit", "9", "10"),
        ("DEMO-2005", "USB-C Hub", "unit", "31", "10"),
        ("DEMO-2006", "Monitor Light", "unit", "14", "5"),
        ("DEMO-2007", "Desk Mat", "unit", "45", "15"),
        ("DEMO-2008", "Laptop Sleeve", "unit", "7", "10"),
        ("DEMO-2009", "Wireless Headset", "unit", "19", "7"),
        ("DEMO-2010", "Portable SSD", "unit", "11", "5"),
        ("DEMO-2011", "Ergonomic Chair", "unit", "6", "3"),
        ("DEMO-2012", "Desk Organizer", "unit", "28", "8"),
    ]
    customers = [
        "Northstar Studio", "Cedar & Co.", "Brightline Design", "Maple Works",
        "Harbor Office", "Summit Creative", "Urban Desk", "Bluebird Media",
        "Oakridge Consulting", "Silverline Labs",
    ]
    suppliers = [
        "Apex Wholesale", "Greenfield Supply", "Metro Components",
        "Northstar Distribution", "Summit Trade",
    ]
    statuses = ["Draft", "Confirmed", "Processing", "Fulfilled", "Cancelled"]
    currencies = ["USD", "USD", "USD", "EUR", "GBP"]

    with factory.begin() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return
        seeded = session.scalar(
            select(DatasetSource.id).where(
                DatasetSource.business_id == business.id,
                DatasetSource.source_name == "BusinessFlow synthetic demonstration dataset",
                DatasetSource.source_version == "2026.1",
            )
        )
        if seeded is not None:
            return

        session.add(DatasetSource(
            business_id=business.id,
            source_name="BusinessFlow synthetic demonstration dataset",
            publisher="BusinessFlow Automation Suite",
            source_url="https://example.invalid/businessflow-synthetic-demo",
            license_name="Original synthetic data",
            attribution="Generated for software demonstration; contains no real customer data.",
            source_version="2026.1",
        ))
        session.flush()

        products = []
        for sku, name, unit, stock, reorder in products_data:
            product = Product(
                business_id=business.id, sku=sku, name=name, unit=unit,
                stock_on_hand=Decimal(stock), reorder_level=Decimal(reorder),
            )
            session.add(product)
            products.append(product)
        session.flush()

        for index, product in enumerate(products):
            quantity = Decimal(products_data[index][3])
            session.add(StockMovement(
                product_id=product.id, movement_type="opening_balance",
                quantity_delta=quantity, quantity_after=quantity,
                reference="DEMO-SEED-OPENING",
                notes="Synthetic opening balance for demonstration.",
                created_at=now - timedelta(days=95),
            ))

        for index in range(30):
            days_ago = (index * 11 + 3) % 175
            order_date = today - timedelta(days=days_ago)
            currency = currencies[index % len(currencies)]
            status = statuses[index % len(statuses)]
            quantity = Decimal(index % 3 + 1)
            unit_price = Decimal(18 + (index * 7) % 83) + Decimal("0.99")
            total = (quantity * unit_price).quantize(Decimal("0.01"))
            order = Order(
                business_id=business.id,
                order_number=f"DEMO-ORD-{2000 + index}",
                customer_name=customers[index % len(customers)],
                customer_email=f"buyer{index + 1}@example.invalid",
                order_date=order_date, currency=currency, status=status, total=total,
                created_at=datetime.combine(
                    order_date, datetime.min.time(), tzinfo=UTC
                ),
            )
            session.add(order)
            session.flush()
            session.add(OrderLineItem(
                order_id=order.id, description="Business equipment bundle",
                quantity=quantity, unit_price=unit_price, amount=total,
            ))

        for index in range(20):
            invoice_date = today - timedelta(days=(index * 9 + 4) % 100)
            due_date = today + timedelta(days=(index % 9) * 4 - 12)
            currency = currencies[(index + 1) % len(currencies)]
            subtotal = Decimal(85 + (index * 19) % 240)
            tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            total = subtotal + tax
            job = ProcessingJob(
                business_id=business.id, job_type="invoice_extraction",
                status="completed", records_processed=1, records_succeeded=1,
                records_failed=0,
                created_at=datetime.combine(
                    invoice_date, datetime.min.time(), tzinfo=UTC
                ),
            )
            session.add(job)
            session.flush()
            session.add(Invoice(
                business_id=business.id, processing_job_id=job.id,
                supplier=suppliers[index % len(suppliers)],
                invoice_number=f"DEMO-BILL-{3000 + index}",
                invoice_date=invoice_date, due_date=due_date, currency=currency,
                subtotal=subtotal, tax=tax, total=total,
                source_filename=f"fictional-invoice-{index + 1:02d}.pdf",
                page_count=1, review_status="confirmed",
                created_at=datetime.combine(
                    invoice_date, datetime.min.time(), tzinfo=UTC
                ),
            ))
            session.add(ProcessingLog(
                job_id=job.id, level="INFO",
                message="Synthetic invoice record prepared for demonstration.",
            ))

        for index in range(8):
            created = now - timedelta(days=index * 5)
            job = ProcessingJob(
                business_id=business.id, job_type="spreadsheet_clean",
                status="completed" if index != 5 else "completed_with_errors",
                records_processed=120 + index * 17,
                records_succeeded=120 + index * 17 if index != 5 else 130,
                records_failed=0 if index != 5 else 7,
                created_at=created,
            )
            session.add(job)
            session.flush()
            session.add(ProcessingLog(
                job_id=job.id, level="INFO",
                message="Synthetic spreadsheet workflow recorded for demonstration.",
            ))
