"""Invoice confirmation and persistence services."""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select

from database.models import (
    Business,
    Invoice,
    InvoiceLineItem,
    ProcessingJob,
    ProcessingLog,
)
from database.session import get_session_factory, initialize_database


class InvoiceSaveError(ValueError):
    """Raised when a reviewed invoice cannot be saved."""


def _decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise InvoiceSaveError(f"{field_name} must be a valid number.") from exc
    if not result.is_finite():
        raise InvoiceSaveError(f"{field_name} must be a finite number.")
    return result


def save_reviewed_invoice(
    database_url: str,
    *,
    supplier: str,
    invoice_number: str,
    invoice_date: date | None,
    due_date: date | None,
    currency: str,
    subtotal: Any,
    tax: Any,
    total: Any,
    filename: str,
    page_count: int,
    line_items: list[dict[str, Any]],
) -> int:
    """Persist user-confirmed invoice fields without retaining the source PDF."""
    supplier = supplier.strip()
    invoice_number = invoice_number.strip()
    currency = currency.strip().upper()
    if not supplier or not invoice_number:
        raise InvoiceSaveError(
            "Supplier and invoice number are required before saving."
        )
    if currency and (len(currency) != 3 or not currency.isalpha()):
        raise InvoiceSaveError(
            "Currency must be a three-letter code, such as USD."
        )
    if page_count < 1:
        raise InvoiceSaveError("Page count must be at least one.")

    amounts = {
        name: _decimal(value, name)
        for name, value in (
            ("subtotal", subtotal), ("tax", tax), ("total", total)
        )
    }
    clean_items = []
    for index, item in enumerate(line_items, start=1):
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        quantity = _decimal(item.get("quantity"), f"Line {index} quantity")
        unit_price = _decimal(item.get("unit_price"), f"Line {index} unit price")
        amount = _decimal(item.get("amount"), f"Line {index} amount")
        if quantity is not None and quantity < 0:
            raise InvoiceSaveError(f"Line {index} quantity cannot be negative.")
        clean_items.append((description[:500], quantity, unit_price, amount))

    initialize_database(database_url)
    factory = get_session_factory(database_url)
    now = datetime.now(UTC)
    with factory.begin() as session:
        business = session.scalar(
            select(Business).order_by(Business.id).limit(1)
        )
        if business is None:
            business = Business(name="Local Workspace")
            session.add(business)
            session.flush()
        duplicate = session.scalar(
            select(Invoice).where(
                Invoice.business_id == business.id,
                Invoice.supplier == supplier,
                Invoice.invoice_number == invoice_number,
            )
        )
        if duplicate:
            raise InvoiceSaveError(
                "An invoice with this supplier and invoice number already exists."
            )

        job = ProcessingJob(
            business_id=business.id,
            job_type="invoice_extraction",
            status="completed",
            records_processed=1,
            records_succeeded=1,
            records_failed=0,
            started_at=now,
            completed_at=now,
        )
        session.add(job)
        session.flush()
        invoice = Invoice(
            business_id=business.id,
            processing_job_id=job.id,
            supplier=supplier,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            currency=currency or None,
            subtotal=amounts["subtotal"],
            tax=amounts["tax"],
            total=amounts["total"],
            source_filename=filename[:255],
            page_count=page_count,
            review_status="confirmed",
        )
        session.add(invoice)
        session.flush()
        for description, quantity, unit_price, amount in clean_items:
            session.add(
                InvoiceLineItem(
                    invoice_id=invoice.id,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                )
            )
        session.add(
            ProcessingLog(
                job_id=job.id,
                level="INFO",
                message=(
                    f"Invoice {invoice_number} reviewed and saved; "
                    "source PDF not retained."
                ),
            )
        )
        return invoice.id
