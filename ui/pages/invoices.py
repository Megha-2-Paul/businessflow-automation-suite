"""PDF invoice extraction, human review and confirmation workspace."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select

from config.settings import get_settings
from database.models import Business, Invoice
from database.session import get_session_factory
from invoices.extraction import InvoiceExtractionError, extract_invoice_pdf
from services.invoice_service import InvoiceSaveError, save_reviewed_invoice
from ui.workspace import get_database_url

settings = get_settings()
database_url = get_database_url(settings.database_url)
st.title("Invoice processing")
st.caption(
    "Extract text from PDF invoices, review every field, then confirm what should be saved."
)
uploaded = st.file_uploader("Upload a PDF invoice", type=["pdf"], key="invoice_pdf")

if uploaded is not None and st.button("Extract invoice details", type="primary"):
    try:
        draft = extract_invoice_pdf(
            uploaded.getvalue(),
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        )
        st.session_state["invoice_draft"] = {
            "supplier": draft.supplier,
            "invoice_number": draft.invoice_number,
            "invoice_date": draft.invoice_date,
            "due_date": draft.due_date,
            "currency": draft.currency,
            "subtotal": str(draft.subtotal or ""),
            "tax": str(draft.tax or ""),
            "total": str(draft.total or ""),
            "line_items": [
                {
                    "description": item.description,
                    "quantity": str(item.quantity or ""),
                    "unit_price": str(item.unit_price or ""),
                    "amount": str(item.amount or ""),
                }
                for item in draft.line_items
            ],
            "warnings": draft.warnings,
            "page_count": draft.page_count,
            "filename": uploaded.name,
        }
        st.success(
            f"Read selectable text from {draft.page_count} page(s). "
            "Review the extracted values below."
        )
    except InvoiceExtractionError as exc:
        st.error(str(exc))

draft = st.session_state.get("invoice_draft")
if draft:
    st.subheader("Review extracted details")
    for warning in draft["warnings"]:
        st.warning(warning)
    with st.form("invoice_review_form"):
        supplier = st.text_input("Supplier / vendor", value=draft["supplier"])
        invoice_number = st.text_input(
            "Invoice number", value=draft["invoice_number"]
        )
        date_col, due_col, currency_col = st.columns(3)
        with date_col:
            has_invoice_date = st.checkbox(
                "Invoice date is known", value=draft["invoice_date"] is not None
            )
            invoice_date = None
            if has_invoice_date:
                invoice_date = st.date_input(
                    "Invoice date", value=draft["invoice_date"] or date.today()
                )
        with due_col:
            has_due_date = st.checkbox(
                "Due date is known", value=draft["due_date"] is not None
            )
            due_date = None
            if has_due_date:
                due_date = st.date_input(
                    "Due date", value=draft["due_date"] or date.today()
                )
        with currency_col:
            currency = st.text_input(
                "Currency code", value=draft["currency"], max_chars=3
            )
        amount_col1, amount_col2, amount_col3 = st.columns(3)
        with amount_col1:
            subtotal = st.text_input("Subtotal", value=draft["subtotal"])
        with amount_col2:
            tax = st.text_input("Tax", value=draft["tax"])
        with amount_col3:
            total = st.text_input("Total", value=draft["total"])
        st.caption(
            "Line items are best-effort text matches. Correct or remove rows before confirmation."
        )
        line_frame = pd.DataFrame(
            draft["line_items"],
            columns=["description", "quantity", "unit_price", "amount"],
        )
        edited_lines = st.data_editor(
            line_frame,
            num_rows="dynamic",
            use_container_width=True,
            key="invoice_line_editor",
        )
        confirmed = st.checkbox(
            "I checked these details against the original PDF and confirm they are correct."
        )
        save = st.form_submit_button("Confirm and save invoice", type="primary")

    if save:
        if not confirmed:
            st.error(
                "Please confirm that you checked the extracted details against the original PDF."
            )
        else:
            try:
                invoice_id = save_reviewed_invoice(
                    database_url,
                    supplier=supplier,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    currency=currency,
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    filename=draft["filename"],
                    page_count=draft["page_count"],
                    line_items=edited_lines.to_dict(orient="records"),
                )
                st.success(f"Invoice saved as record #{invoice_id}.")
                st.session_state.pop("invoice_draft", None)
            except InvoiceSaveError as exc:
                st.error(str(exc))

st.divider()
st.subheader("Saved invoices")
factory = get_session_factory(database_url)
with factory() as session:
    statement = (
        select(Invoice)
        .join(Business)
        .order_by(Invoice.created_at.desc())
        .limit(100)
    )
    invoices = session.scalars(statement).all()
    if invoices:
        rows = [
            {
                "ID": item.id,
                "Supplier": item.supplier,
                "Invoice number": item.invoice_number,
                "Invoice date": item.invoice_date,
                "Currency": item.currency or "",
                "Total": str(item.total) if item.total is not None else "",
                "Review": item.review_status,
            }
            for item in invoices
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No invoices have been confirmed and saved yet.")
