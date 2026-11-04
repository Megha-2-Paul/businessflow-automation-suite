"""Unit tests for bounded PDF invoice text extraction."""
from io import BytesIO

import pymupdf
import pytest

from invoices.extraction import InvoiceExtractionError, extract_invoice_pdf


def make_pdf(text: str) -> bytes:
    output = BytesIO()
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((50, 50), text)
    document.save(output)
    document.close()
    return output.getvalue()


def test_extracts_basic_invoice_fields():
    text = (
        "Acme Supplies\nInvoice Number: INV-1042\nInvoice Date: 2025-02-03\n"
        "Due Date: 2025-03-03\nSubtotal: $100.00\nTax: $18.00\n"
        "Grand Total: $118.00"
    )
    draft = extract_invoice_pdf(make_pdf(text), max_bytes=100_000)
    assert draft.supplier == "Acme Supplies"
    assert draft.invoice_number == "INV-1042"
    assert str(draft.invoice_date) == "2025-02-03"
    assert draft.subtotal == 100
    assert draft.tax == 18
    assert draft.total == 118
    assert draft.currency == "USD"
    assert draft.page_count == 1
    assert draft.warnings


def test_rejects_empty_invalid_oversized_and_scanned_pdfs():
    with pytest.raises(InvoiceExtractionError, match="empty"):
        extract_invoice_pdf(b"", max_bytes=100)
    with pytest.raises(InvoiceExtractionError, match="configured limit"):
        extract_invoice_pdf(b"1234", max_bytes=3)
    with pytest.raises(InvoiceExtractionError, match="valid"):
        extract_invoice_pdf(b"not a pdf", max_bytes=100)
    with pytest.raises(InvoiceExtractionError, match="No selectable text"):
        extract_invoice_pdf(make_pdf(" "), max_bytes=100_000)


def test_rejects_page_limit():
    document = pymupdf.open()
    document.new_page()
    document.new_page()
    content = document.tobytes()
    document.close()
    with pytest.raises(InvoiceExtractionError, match="more than 1 pages"):
        extract_invoice_pdf(content, max_bytes=100_000, max_pages=1)
