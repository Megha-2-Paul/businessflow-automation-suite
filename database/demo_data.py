"""Idempotent fictional data seeder for the isolated demonstration workspace."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from database.models import (
    Business, Invoice, Order, OrderLineItem, ProcessingJob, ProcessingLog,
    Product, StockMovement,
)
from database.session import get_session_factory, initialize_database


def seed_demo_data(database_url: str) -> None:
    """Populate an empty demo database with internally consistent sample records.

    Existing workspaces are left untouched. All names, addresses and amounts
    are fictional and are intended only for product demonstrations.
    """
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    with factory.begin() as session:
        if session.scalar(select(Business.id).limit(1)) is not None:
            return

        today = date.today()
        now = datetime.now(UTC)
        business = Business(name="Northstar Office & Tech (Demo)", currency="USD")
        session.add(business)
        session.flush()

        catalogue = [
            ("DEMO-1001", "Wireless Mouse", "unit", 58, 12),
            ("DEMO-1002", "USB-C Keyboard", "unit", 34, 10),
            ("DEMO-1003", "Aluminium Laptop Stand", "unit", 9, 12),
            ("DEMO-1004", "1080p Webcam", "unit", 27, 8),
            ("DEMO-1005", "Noise-Cancelling Headset", "unit", 6, 8),
            ("DEMO-1006", "USB-C Docking Station", "unit", 19, 6),
            ("DEMO-1007", "Portable SSD 1TB", "unit", 42, 10),
            ("DEMO-1008", "Ergonomic Desk Mat", "unit", 31, 10),
            ("DEMO-1009", "LED Desk Lamp", "unit", 4, 7),
            ("DEMO-1010", "Laptop Sleeve 15-inch", "unit", 23, 8),
            ("DEMO-1011", "Bluetooth Speaker", "unit", 16, 6),
            ("DEMO-1012", "Wireless Presenter", "unit", 11, 5),
        ]
        products: list[Product] = []
        for sku, name, unit, stock, reorder in catalogue:
            product = Product(
                business_id=business.id, sku=sku, name=name, unit=unit,
                stock_on_hand=Decimal(stock), reorder_level=Decimal(reorder),
            )
            session.add(product)
            products.append(product)
        session.flush()

        # Each product's ledger starts with its opening balance. Subsequent
        # receipts/issues are reflected in both the ledger and current balance.
        for index, product in enumerate(products):
            opening = int(product.stock_on_hand)
            session.add(StockMovement(
                product_id=product.id, movement_type="opening_balance",
                quantity_delta=Decimal(opening), quantity_after=Decimal(opening),
                reference="DEMO-OPENING",
                notes="Fictional opening balance for demonstration.",
                created_at=datetime.combine(today - timedelta(days=190), time(9), UTC),
            ))
            balance = opening
            for movement_index in range(2):
                delta = 5 + ((index + movement_index * 3) % 8)
                if movement_index == 1 and balance - delta < 0:
                    delta = 1
                signed = delta if movement_index == 0 else -delta
                balance += signed
                session.add(StockMovement(
                    product_id=product.id,
                    movement_type="receipt" if signed > 0 else "issue",
                    quantity_delta=Decimal(signed),
                    quantity_after=Decimal(balance),
                    reference=f"DEMO-MOVE-{index + 1:02d}-{movement_index + 1}",
                    notes="Fictional sample stock movement.",
                    created_at=datetime.combine(
                        today - timedelta(days=120 - movement_index * 35 + index % 9),
                        time(11), UTC,
                    ),
                ))
            product.stock_on_hand = Decimal(balance)

        customers = [
            "Avery Morgan", "Jordan Lee", "Taylor Bennett", "Casey Rivera",
            "Riley Parker", "Morgan Ellis", "Cameron Brooks", "Quinn Bailey",
            "Drew Foster", "Alex Harper", "Jamie Collins", "Reese Murphy",
            "Skyler Reed", "Peyton Ross", "Rowan James",
        ]
        prices = [("19.99", "39.99"), ("29.50", "59.00"), ("44.00", "88.00"),
                  ("24.99", "49.98"), ("34.50", "69.00"), ("79.00", "158.00")]
        statuses = ["Fulfilled", "Fulfilled", "Processing", "Confirmed", "Draft",
                    "Cancelled"]
        for index in range(30):
            age = (index * 7) % 175
            order_date = today - timedelta(days=age)
            first = products[index % len(products)]
            second = products[(index * 5 + 3) % len(products)]
            quantity_one = 1 + index % 3
            quantity_two = 1 + (index // 3) % 2
            price_one, price_two = prices[index % len(prices)]
            amount_one = Decimal(price_one) * quantity_one
            amount_two = Decimal(price_two) * quantity_two
            order = Order(
                business_id=business.id,
                order_number=f"DEMO-ORD-{1001 + index}",
                customer_name=customers[index % len(customers)],
                customer_email=f"buyer{index + 1:02d}@example.invalid",
                order_date=order_date, currency="USD",
                status=statuses[index % len(statuses)],
                total=amount_one + amount_two,
                created_at=datetime.combine(order_date, time(10 + index % 7, 15), UTC),
                updated_at=datetime.combine(order_date, time(10 + index % 7, 15), UTC),
            )
            session.add(order)
            session.flush()
            session.add_all([
                OrderLineItem(
                    order_id=order.id, product_id=first.id,
                    description=first.name, quantity=Decimal(quantity_one),
                    unit_price=Decimal(price_one), amount=amount_one,
                ),
                OrderLineItem(
                    order_id=order.id, product_id=second.id,
                    description=second.name, quantity=Decimal(quantity_two),
                    unit_price=Decimal(price_two), amount=amount_two,
                ),
            ])

        suppliers = [
            "Brightline Wholesale", "Evergreen Business Supply",
            "Metro Office Distribution", "Summit Technology Traders",
            "Cedar & Co. Stationery",
        ]
        for index in range(20):
            age = (index * 9) % 170
            invoice_date = today - timedelta(days=age)
            job = ProcessingJob(
                business_id=business.id, job_type="invoice_extraction",
                status="completed", records_processed=1, records_succeeded=1,
                records_failed=0,
                started_at=datetime.combine(invoice_date, time(9), UTC),
                completed_at=datetime.combine(invoice_date, time(9, 1), UTC),
                created_at=datetime.combine(invoice_date, time(9, 1), UTC),
            )
            session.add(job)
            session.flush()
            subtotal = Decimal(75 + index * 17) + Decimal("0.50")
            tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            session.add(Invoice(
                business_id=business.id, processing_job_id=job.id,
                supplier=suppliers[index % len(suppliers)],
                invoice_number=f"DEMO-BILL-{3001 + index}",
                invoice_date=invoice_date,
                due_date=invoice_date + timedelta(days=30),
                currency="USD", subtotal=subtotal, tax=tax, total=subtotal + tax,
                source_filename=f"sample-invoice-{index + 1:02d}.pdf",
                page_count=1, review_status="confirmed",
                created_at=datetime.combine(invoice_date, time(9, 2), UTC),
            ))
            session.add(ProcessingLog(
                job_id=job.id, level="INFO",
                message="Fictional invoice extraction reviewed and confirmed.",
                created_at=datetime.combine(invoice_date, time(9, 2), UTC),
            ))

        for index in range(12):
            job_date = today - timedelta(days=index * 11)
            job = ProcessingJob(
                business_id=business.id,
                job_type="spreadsheet_clean" if index % 2 == 0 else "spreadsheet_consolidation",
                status="completed" if index % 4 else "completed_with_errors",
                records_processed=120 + index * 13,
                records_succeeded=118 + index * 13,
                records_failed=2 if index % 4 == 0 else 0,
                started_at=datetime.combine(job_date, time(14), UTC),
                completed_at=datetime.combine(job_date, time(14, 2), UTC),
                created_at=datetime.combine(job_date, time(14, 2), UTC),
            )
            session.add(job)
            session.flush()
            session.add(ProcessingLog(
                job_id=job.id, level="INFO",
                message="Fictional spreadsheet workflow completed for demonstration.",
                created_at=datetime.combine(job_date, time(14, 2), UTC),
            ))
