"""Repeatable fictional records for the isolated demonstration workspace."""
from datetime import date, datetime, time, timedelta, UTC
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
from database.session import get_session_factory, initialize_database


CUSTOMERS = [
    ("Avery Bennett", "avery@example.invalid"),
    ("Jordan Ellis", "jordan@example.invalid"),
    ("Morgan Reed", "morgan@example.invalid"),
    ("Taylor Brooks", "taylor@example.invalid"),
    ("Casey Morgan", "casey@example.invalid"),
    ("Riley Parker", "riley@example.invalid"),
    ("Cameron Hayes", "cameron@example.invalid"),
    ("Quinn Foster", "quinn@example.invalid"),
    ("Drew Sullivan", "drew@example.invalid"),
    ("Jamie Collins", "jamie@example.invalid"),
    ("Alex Rivera", "alex@example.invalid"),
    ("Sam Bennett", "sam@example.invalid"),
    ("Robin Murphy", "robin@example.invalid"),
    ("Charlie Ward", "charlie@example.invalid"),
    ("Dakota Price", "dakota@example.invalid"),
    ("Emerson Gray", "emerson@example.invalid"),
    ("Finley James", "finley@example.invalid"),
    ("Harper Lane", "harper@example.invalid"),
    ("Kendall Ross", "kendall@example.invalid"),
    ("Logan Bell", "logan@example.invalid"),
]

PRODUCTS = [
    ("DEMO-1004", "Wireless Headset", "unit", "54.00", "12"),
    ("DEMO-1005", "USB-C Hub", "unit", "38.50", "10"),
    ("DEMO-1006", "Portable SSD 1TB", "unit", "96.00", "8"),
    ("DEMO-1007", "Webcam 1080p", "unit", "47.00", "9"),
    ("DEMO-1008", "Mechanical Keyboard", "unit", "82.00", "10"),
    ("DEMO-1009", "Laptop Sleeve", "unit", "24.00", "15"),
    ("DEMO-1010", "Wireless Presenter", "unit", "29.00", "8"),
    ("DEMO-1011", "Monitor Light Bar", "unit", "61.00", "7"),
    ("DEMO-1012", "Desk Mat", "unit", "18.00", "12"),
    ("DEMO-1013", "USB Microphone", "unit", "73.00", "6"),
    ("DEMO-1014", "Ergonomic Mouse Pad", "unit", "16.00", "10"),
    ("DEMO-1015", "Laptop Riser", "unit", "42.00", "8"),
]
DATASET_NAME = "BusinessFlow synthetic demo dataset"
DATASET_VERSION = "1.0"
ORDER_STATUSES = (
    "Fulfilled",
    "Fulfilled",
    "Processing",
    "Confirmed",
    "Draft",
    "Cancelled",
)
JOB_TYPES = (
    "spreadsheet_clean",
    "spreadsheet_consolidation",
    "order_management",
    "inventory_reconciliation",
)


def _at_utc(day: date) -> datetime:
    """Return midnight UTC for a date-only business event."""
    return datetime.combine(day, time.min, UTC)


def seed_demo_records(database_url: str, *, today: date | None = None) -> None:
    """Add a relational sample dataset once, without replacing existing records.

    The caller is responsible for passing the isolated Demo workspace URL.
    All inserts run in one transaction, so a failed seed leaves no partial
    dataset marker or records behind.
    """
    today = today or date.today()
    initialize_database(database_url)
    factory = get_session_factory(database_url)

    with factory.begin() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return

        marker = session.scalar(
            select(DatasetSource.id).where(
                DatasetSource.business_id == business.id,
                DatasetSource.source_name == DATASET_NAME,
                DatasetSource.source_version == DATASET_VERSION,
            )
        )
        if marker is not None:
            return

        source = DatasetSource(
            business_id=business.id,
            source_name=DATASET_NAME,
            publisher="BusinessFlow Automation Suite",
            source_url="local://businessflow-synthetic-demo",
            license_name="Original fictional demonstration data",
            attribution="All names, email addresses, orders and values are synthetic.",
            source_version=DATASET_VERSION,
        )
        session.add(source)
        session.flush()

        products = []
        for sku, name, unit, price, reorder_level in PRODUCTS:
            product = Product(
                business_id=business.id,
                sku=sku,
                name=name,
                unit=unit,
                stock_on_hand=Decimal("40"),
                reorder_level=Decimal(reorder_level),
            )
            session.add(product)
            products.append((product, Decimal(price)))
        session.flush()

        opening_date = today - timedelta(days=190)
        for product, _price in products:
            session.add(
                StockMovement(
                    product_id=product.id,
                    movement_type="opening_balance",
                    quantity_delta=Decimal("40"),
                    quantity_after=Decimal("40"),
                    reference="DEMO-OPENING",
                    notes="Synthetic demonstration opening balance",
                    created_at=_at_utc(opening_date),
                )
            )

        orders_with_products = []
        for index in range(29):
            customer, email = CUSTOMERS[index % len(CUSTOMERS)]
            product, price = products[index % len(products)]
            quantity = Decimal(str(1 + index % 3))
            status = ORDER_STATUSES[index % len(ORDER_STATUSES)]
            order_date = today - timedelta(days=(index * 7) % 175)
            order = Order(
                business_id=business.id,
                order_number=f"DEMO-ORD-{1002 + index:04d}",
                customer_name=customer,
                customer_email=email,
                order_date=order_date,
                currency=business.currency,
                status=status,
                total=price * quantity,
                created_at=_at_utc(order_date),
            )
            session.add(order)
            session.flush()
            session.add(
                OrderLineItem(
                    order_id=order.id,
                    description=product.name,
                    quantity=quantity,
                    unit_price=price,
                    amount=price * quantity,
                    product_id=product.id,
                )
            )
            if status == "Fulfilled":
                orders_with_products.append((order, product, quantity))

        # Apply fulfilled quantities chronologically so each ledger balance
        # agrees with the sequence of recorded movements.
        for order, product, quantity in sorted(
            orders_with_products,
            key=lambda item: (item[0].order_date, item[0].order_number),
        ):
            product.stock_on_hand -= quantity
            session.add(
                StockMovement(
                    product_id=product.id,
                    order_id=order.id,
                    movement_type="order_fulfilment",
                    quantity_delta=-quantity,
                    quantity_after=product.stock_on_hand,
                    reference=order.order_number,
                    notes="Synthetic demo order fulfilment",
                    created_at=_at_utc(order.order_date),
                )
            )

        suppliers = (
            "Northstar Office Co.",
            "Brightline Technology",
            "Cedar & Stone Supplies",
            "Summit Wholesale",
            "Harbor Business Goods",
        )
        for index in range(19):
            invoice_date = today - timedelta(days=(index * 9) % 180)
            subtotal = Decimal(80 + index * 13)
            tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            created_at = _at_utc(invoice_date)
            job = ProcessingJob(
                business_id=business.id,
                job_type="invoice_extraction",
                status="completed",
                records_processed=1,
                records_succeeded=1,
                records_failed=0,
                started_at=created_at,
                completed_at=created_at,
                created_at=created_at,
            )
            session.add(job)
            session.flush()
            session.add(
                Invoice(
                    business_id=business.id,
                    processing_job_id=job.id,
                    supplier=suppliers[index % len(suppliers)],
                    invoice_number=f"DEMO-BILL-{3001 + index:04d}",
                    invoice_date=invoice_date,
                    due_date=invoice_date + timedelta(days=30),
                    currency=business.currency,
                    subtotal=subtotal,
                    tax=tax,
                    total=subtotal + tax,
                    source_filename=f"demo-bill-{index + 1:02d}.pdf",
                    page_count=1,
                    review_status="confirmed",
                    created_at=created_at,
                )
            )
            session.add(
                ProcessingLog(
                    job_id=job.id,
                    level="INFO",
                    message="Synthetic invoice review completed for demonstration.",
                    created_at=created_at,
                )
            )

        for index in range(14):
            created_at = _at_utc(today - timedelta(days=(index * 11) % 160))
            job_type = JOB_TYPES[index % len(JOB_TYPES)]
            failed = index in {4, 11}
            job = ProcessingJob(
                business_id=business.id,
                job_type=job_type,
                status="completed_with_errors" if failed else "completed",
                records_processed=24 + index,
                records_succeeded=24 + index - int(failed),
                records_failed=int(failed),
                started_at=created_at,
                completed_at=created_at,
                created_at=created_at,
            )
            session.add(job)
            session.flush()
            session.add(
                ProcessingLog(
                    job_id=job.id,
                    level="WARNING" if failed else "INFO",
                    message=(
                        "Synthetic sample includes a row requiring review."
                        if failed
                        else "Synthetic demonstration workflow completed."
                    ),
                    created_at=created_at,
                )
            )
