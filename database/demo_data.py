"""Deterministic fictional records for a useful, repeatable demo workspace."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from database.models import (
    Business, Invoice, InvoiceLineItem, Order, OrderLineItem, ProcessingJob,
    ProcessingLog, Product, StockMovement,
)
from database.session import get_session_factory, initialize_database

PRODUCTS = [
    ("DEMO-SKU-01", "Wireless Mouse", "42", "10", "24.99"),
    ("DEMO-SKU-02", "USB-C Keyboard", "8", "12", "49.99"),
    ("DEMO-SKU-03", "Laptop Stand", "25", "8", "34.50"),
    ("DEMO-SKU-04", "HD Webcam", "6", "8", "59.00"),
    ("DEMO-SKU-05", "USB-C Hub", "31", "10", "29.95"),
    ("DEMO-SKU-06", "Desk Lamp", "0", "5", "22.00"),
    ("DEMO-SKU-07", "Monitor Riser", "17", "6", "39.00"),
    ("DEMO-SKU-08", "Notebook Set", "64", "20", "12.50"),
    ("DEMO-SKU-09", "Bluetooth Headset", "4", "7", "74.00"),
    ("DEMO-SKU-10", "Portable SSD", "19", "6", "89.00"),
    ("DEMO-SKU-11", "Ergonomic Mouse Pad", "38", "12", "15.00"),
    ("DEMO-SKU-12", "Laptop Sleeve", "13", "5", "27.50"),
]

CUSTOMERS = [
    "Northstar Studio", "Greenfield Consulting", "Harbor & Co", "Summit Design",
    "Brightpath Learning", "Oakline Retail", "Bluebird Creative", "Westway Services",
    "Maple Street Office", "Cedarworks", "Pioneer Analytics", "Meadowbrook Media",
]


def seed_demo_dataset(database_url: str) -> None:
    """Add a deterministic dataset once, preserving any existing demo records."""
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    with factory.begin() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            business = Business(name="Demo Business", currency="USD", timezone="UTC")
            session.add(business)
            session.flush()
        if session.scalar(
            select(Product.id).where(
                Product.business_id == business.id, Product.sku == "DEMO-SKU-01"
            )
        ) is not None:
            return

        today = date.today()
        now = datetime.now(timezone.utc)
        products = []
        for sku, name, stock, reorder, price in PRODUCTS:
            product = Product(
                business_id=business.id, sku=sku, name=name, unit="unit",
                stock_on_hand=Decimal(stock), reorder_level=Decimal(reorder),
            )
            products.append((product, Decimal(price)))
            session.add(product)
        session.flush()

        for index, (product, _) in enumerate(products):
            opening = Decimal(PRODUCTS[index][2])
            if opening > 0:
                session.add(StockMovement(
                    product_id=product.id, movement_type="opening_balance",
                    quantity_delta=opening, quantity_after=opening,
                    reference=f"DEMO-OPEN-{product.sku}",
                    notes="Fictional demonstration opening balance.",
                    created_at=now - timedelta(days=180 - index),
                ))
            if index % 3 == 0:
                receipt = Decimal("5")
                product.stock_on_hand += receipt
                session.add(StockMovement(
                    product_id=product.id, movement_type="receipt",
                    quantity_delta=receipt, quantity_after=product.stock_on_hand,
                    reference=f"DEMO-PO-{index + 1:03d}",
                    notes="Fictional demonstration supplier receipt.",
                    created_at=now - timedelta(days=45 - index),
                ))

        statuses = ["Fulfilled", "Fulfilled", "Processing", "Confirmed", "Draft", "Cancelled"]
        for index in range(30):
            age = (index * 7) % 175
            order_date = today - timedelta(days=age)
            status = statuses[index % len(statuses)]
            currency = "USD" if index % 5 else "EUR"
            product, price = products[index % len(products)]
            quantity = Decimal(index % 3 + 1)
            amount = (price * quantity).quantize(Decimal("0.01"))
            order = Order(
                business_id=business.id,
                order_number=f"DEMO-ORD-{2001 + index}",
                customer_name=CUSTOMERS[index % len(CUSTOMERS)],
                customer_email=f"buyer{index + 1}@example.invalid",
                order_date=order_date, currency=currency, status=status, total=amount,
                created_at=datetime.combine(order_date, time(10 + index % 8), tzinfo=timezone.utc),
            )
            session.add(order)
            session.flush()
            session.add(OrderLineItem(
                order_id=order.id, description=product.name, quantity=quantity,
                unit_price=price, amount=amount, product_id=product.id,
            ))

        for index in range(16):
            job = ProcessingJob(
                business_id=business.id,
                job_type=["invoice_extraction", "spreadsheet_clean", "spreadsheet_consolidation"][
                    index % 3
                ],
                status="completed" if index % 5 else "completed_with_errors",
                records_processed=12 + index,
                records_succeeded=12 + index - (1 if index % 5 == 0 else 0),
                records_failed=1 if index % 5 == 0 else 0,
                created_at=now - timedelta(days=index * 8),
                started_at=now - timedelta(days=index * 8, minutes=3),
                completed_at=now - timedelta(days=index * 8, minutes=2),
            )
            session.add(job)
            session.flush()
            session.add(ProcessingLog(
                job_id=job.id, level="INFO",
                message="Fictional demo workflow completed; review the sample output.",
                created_at=job.completed_at,
            ))
            if index % 5 == 0:
                session.add(ProcessingLog(
                    job_id=job.id, level="WARNING",
                    message="One demonstration row requires manual review.",
                    created_at=job.completed_at,
                ))
            if index < 12:
                currency = "USD" if index % 4 else "EUR"
                subtotal = Decimal("80.00") + Decimal(index * 7)
                tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
                total = subtotal + tax
                invoice_date = today - timedelta(days=index * 9 + 2)
                invoice = Invoice(
                    business_id=business.id, processing_job_id=job.id,
                    supplier=["Apex Office Supply", "Greenline Wholesale", "Metro Tech Trading"][
                        index % 3
                    ],
                    invoice_number=f"DEMO-BILL-{3001 + index}",
                    invoice_date=invoice_date, due_date=invoice_date + timedelta(days=30),
                    currency=currency, subtotal=subtotal, tax=tax, total=total,
                    source_filename=f"fictional-invoice-{index + 1:02d}.pdf",
                    page_count=1, review_status="confirmed",
                    created_at=datetime.combine(invoice_date, time(9), tzinfo=timezone.utc),
                )
                session.add(invoice)
                session.flush()
                session.add(InvoiceLineItem(
                    invoice_id=invoice.id, description="Office and technology supplies",
                    quantity=Decimal("1"), unit_price=subtotal, amount=subtotal,
                ))
