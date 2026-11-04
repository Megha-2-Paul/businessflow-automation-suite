"""Integration tests for invoice confirmation and persistence."""
import pytest

from database.models import Invoice, InvoiceLineItem
from database.session import get_session_factory
from services.invoice_service import InvoiceSaveError, save_reviewed_invoice


def test_saves_reviewed_invoice_and_line_items(tmp_path):
    url = f"sqlite:///{tmp_path / 'invoice.db'}"
    invoice_id = save_reviewed_invoice(
        url,
        supplier="Acme Supplies",
        invoice_number="INV-1",
        invoice_date=None,
        due_date=None,
        currency="USD",
        subtotal="100",
        tax="18",
        total="118",
        filename="invoice.pdf",
        page_count=1,
        line_items=[
            {
                "description": "Paper",
                "quantity": "2",
                "unit_price": "50",
                "amount": "100",
            }
        ],
    )
    with get_session_factory(url)() as session:
        invoice = session.get(Invoice, invoice_id)
        assert invoice is not None
        assert invoice.review_status == "confirmed"
        assert invoice.total == 118
        assert len(invoice.line_items) == 1
        assert session.query(InvoiceLineItem).count() == 1


def test_requires_supplier_and_number_and_prevents_duplicates(tmp_path):
    url = f"sqlite:///{tmp_path / 'duplicates.db'}"
    with pytest.raises(InvoiceSaveError, match="required"):
        save_reviewed_invoice(
            url,
            supplier="",
            invoice_number="",
            invoice_date=None,
            due_date=None,
            currency="",
            subtotal=None,
            tax=None,
            total=None,
            filename="x.pdf",
            page_count=1,
            line_items=[],
        )
    values = {
        "supplier": "Vendor",
        "invoice_number": "A-1",
        "invoice_date": None,
        "due_date": None,
        "currency": "USD",
        "subtotal": None,
        "tax": None,
        "total": None,
        "filename": "x.pdf",
        "page_count": 1,
        "line_items": [],
    }
    save_reviewed_invoice(url, **values)
    with pytest.raises(InvoiceSaveError, match="already exists"):
        save_reviewed_invoice(url, **values)


def test_rejects_invalid_amounts_and_currency(tmp_path):
    url = f"sqlite:///{tmp_path / 'invalid.db'}"
    with pytest.raises(InvoiceSaveError, match="valid number"):
        save_reviewed_invoice(
            url, supplier="Vendor", invoice_number="A", invoice_date=None,
            due_date=None, currency="USD", subtotal="NaN?", tax=None,
            total=None, filename="x.pdf", page_count=1, line_items=[],
        )
    with pytest.raises(InvoiceSaveError, match="three-letter"):
        save_reviewed_invoice(
            url, supplier="Vendor", invoice_number="B", invoice_date=None,
            due_date=None, currency="US", subtotal=None, tax=None,
            total=None, filename="x.pdf", page_count=1, line_items=[],
        )
