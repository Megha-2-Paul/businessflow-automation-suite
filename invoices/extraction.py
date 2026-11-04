"""Conservative text extraction for text-based PDF invoices."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pymupdf


class InvoiceExtractionError(ValueError):
    """Raised when an invoice PDF cannot be safely processed."""


@dataclass(slots=True)
class InvoiceLineDraft:
    """A line item inferred from invoice text; always requires review."""

    description: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None


@dataclass(slots=True)
class InvoiceDraft:
    """Extracted invoice values and review warnings."""

    supplier: str = ""
    invoice_number: str = ""
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str = ""
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    line_items: list[InvoiceLineDraft] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page_count: int = 0


_AMOUNT = (
    r"(?:[A-Z]{3}\s*)?[$€£₹]?\s*\(?-?\d[\d,]*(?:\.\d{1,2})?\)?"
)
_DATE = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})"


def _amount(value: str) -> Decimal | None:
    cleaned = re.sub(r"^[A-Z]{3}\s*|[$€£₹,\s]", "", value.strip())
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    try:
        result = Decimal(cleaned)
    except InvalidOperation:
        return None
    return -result if negative else result


def _date(value: str) -> date | None:
    patterns = (
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%m-%d-%Y", "%d/%m/%y", "%m/%d/%y",
    )
    for pattern in patterns:
        try:
            if pattern == "%Y-%m-%d":
                return date.fromisoformat(value)
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None


def _label_value(text: str, labels: str, pattern: str) -> str | None:
    expression = rf"(?:{labels})\s*[:#-]?\s*{pattern}"
    match = re.search(expression, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_invoice_pdf(
    content: bytes, *, max_bytes: int, max_pages: int = 100
) -> InvoiceDraft:
    """Extract likely invoice fields from a bounded, text-based PDF in memory."""
    if not content:
        raise InvoiceExtractionError("The uploaded PDF is empty.")
    if len(content) > max_bytes:
        raise InvoiceExtractionError(
            "The PDF exceeds the configured limit for upload size."
        )
    try:
        document = pymupdf.open(stream=content, filetype="pdf")
    except (pymupdf.FileDataError, ValueError) as exc:
        raise InvoiceExtractionError(
            "The file is not a valid, readable PDF."
        ) from exc

    with document:
        if document.needs_pass:
            raise InvoiceExtractionError(
                "Password-protected PDFs are not supported."
            )
        if document.page_count == 0:
            raise InvoiceExtractionError("The PDF does not contain any pages.")
        if document.page_count > max_pages:
            raise InvoiceExtractionError(
                f"The PDF has more than {max_pages} pages; split it before uploading."
            )
        text = "\n".join(page.get_text("text") for page in document)
        page_count = document.page_count

    if not text.strip():
        raise InvoiceExtractionError(
            "No selectable text was found. This appears to be a scanned PDF; "
            "OCR is not included yet."
        )

    draft = InvoiceDraft(page_count=page_count)
    value = _label_value(
        text, r"invoice\s*(?:number|no\.?|#)",
        r"([A-Z0-9][A-Z0-9/_-]{1,})",
    )
    if value:
        draft.invoice_number = value
    value = _label_value(text, r"invoice\s*date|date\s*of\s*issue", _DATE)
    if value:
        draft.invoice_date = _date(value)
    value = _label_value(text, r"due\s*date|payment\s*due", _DATE)
    if value:
        draft.due_date = _date(value)

    total_labels = r"grand\s*total|total\s*due|amount\s*due|(?<!sub)total"
    for label, attribute in (
        (r"subtotal|sub-total", "subtotal"),
        (r"tax|vat|gst", "tax"),
        (total_labels, "total"),
    ):
        value = _label_value(text, label, rf"({_AMOUNT})")
        if value:
            setattr(draft, attribute, _amount(value))

    currency_match = re.search(r"\b(USD|EUR|GBP|INR|CAD|AUD)\b|([$€£₹])", text)
    if currency_match:
        symbol = currency_match.group(2)
        symbols = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}
        draft.currency = currency_match.group(1) or symbols.get(symbol, "")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ignored = re.compile(
        r"invoice|subtotal|sub-total|tax|vat|gst|total|balance|due date|invoice date",
        re.IGNORECASE,
    )
    item_pattern = re.compile(
        rf"^(.+?)\s{{2,}}(\d+(?:\.\d+)?)\s+({_AMOUNT})\s+({_AMOUNT})$"
    )
    for line in lines:
        match = item_pattern.match(line)
        if match and not ignored.search(line):
            draft.line_items.append(
                InvoiceLineDraft(
                    description=match.group(1).strip(),
                    quantity=_amount(match.group(2)),
                    unit_price=_amount(match.group(3)),
                    amount=_amount(match.group(4)),
                )
            )

    first_lines = [
        line for line in lines[:8]
        if not re.search(r"invoice|bill to|ship to|date", line, re.IGNORECASE)
    ]
    if first_lines:
        draft.supplier = first_lines[0][:200]
    if not draft.invoice_number:
        draft.warnings.append("Invoice number was not confidently identified.")
    if not draft.invoice_date:
        draft.warnings.append("Invoice date was not confidently identified.")
    if not draft.total:
        draft.warnings.append("Invoice total was not confidently identified.")
    if not draft.line_items:
        draft.warnings.append(
            "No line items matched the supported text layout; "
            "enter or review them manually."
        )
    draft.warnings.append(
        "All extracted values must be checked against the original invoice before saving."
    )
    return draft
