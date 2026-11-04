"""Integration coverage for dashboard summaries, reports and exports."""
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import pytest

from database.models import Business, ProcessingError, ProcessingJob, ProcessingLog
from database.session import get_session_factory, initialize_database
from reporting.exports import export_csv, export_xlsx
from reporting.service import dashboard_summary, processing_history, report_data
from services.inventory_service import create_product
from services.invoice_service import save_reviewed_invoice
from services.order_service import create_order


def populated_database(tmp_path):
    url = f"sqlite:///{tmp_path / 'reporting.db'}"
    initialize_database(url)
    factory = get_session_factory(url)
    with factory.begin() as session:
        session.add(Business(name="Reporting Workspace", currency="USD"))
    create_order(
        url,
        order_number="R-100",
        customer_name="Example Buyer",
        currency="USD",
        line_items=[{"description": "Service", "quantity": "2", "unit_price": "15.00"}],
    )
    create_product(
        url, sku="SKU-1", name="Stock item", opening_stock="4", reorder_level="5"
    )
    save_reviewed_invoice(
        url,
        supplier="Vendor",
        invoice_number="INV-1",
        invoice_date=date(2026, 1, 2),
        due_date=None,
        currency="EUR",
        subtotal="20",
        tax="2",
        total="22",
        filename="invoice.pdf",
        page_count=1,
        line_items=[],
    )
    with factory.begin() as session:
        job = ProcessingJob(
            business_id=1,
            job_type="spreadsheet_clean",
            status="completed",
            records_processed=3,
            records_succeeded=2,
            records_failed=1,
        )
        session.add(job)
        session.flush()
        session.add(ProcessingLog(job_id=job.id, level="INFO", message="Cleaned input."))
        session.add(
            ProcessingError(
                job_id=job.id,
                row_number=3,
                issue_type="invalid_value",
                details="Amount is invalid.",
            )
        )
    return url


def test_dashboard_uses_saved_records_and_keeps_currencies_separate(tmp_path):
    url = populated_database(tmp_path)
    summary = dashboard_summary(url)
    assert summary["business_name"] == "Reporting Workspace"
    assert summary["orders_total"] == 1
    assert summary["orders_open"] == 1
    assert summary["invoices_confirmed"] == 1
    assert summary["products_active"] == 1
    assert summary["products_low_stock"] == 1
    assert {item["Currency"] for item in summary["currency_totals"]} == {"USD"}


def test_report_content_and_empty_date_range(tmp_path):
    url = populated_database(tmp_path)
    orders = report_data(url, "orders")
    invoices = report_data(url, "invoices")
    stock = report_data(url, "inventory")
    jobs = report_data(url, "processing")
    assert orders.loc[0, "Order number"] == "R-100"
    assert invoices.loc[0, "Currency"] == "EUR"
    assert stock.loc[0, "On hand"] == 4.0
    assert "Error count" in jobs.columns
    assert report_data(url, "orders", start_date=date(2030, 1, 1)).empty


def test_history_filters_logs_and_errors(tmp_path):
    url = populated_database(tmp_path)
    jobs = processing_history(url, workflow="spreadsheet_clean", status="completed")
    assert len(jobs) == 1
    assert jobs[0]["logs"][0]["message"] == "Cleaned input."
    assert jobs[0]["errors"][0]["details"] == "Amount is invalid."
    assert processing_history(url, workflow="spreadsheet_consolidation") == []


def test_exports_are_readable_and_formula_text_is_neutralised(tmp_path):
    url = populated_database(tmp_path)
    frame = report_data(url, "orders")
    frame.loc[0, "Customer"] = "=HYPERLINK(\"https://example.invalid\")"
    frame.loc[0, "Formula edge cases"] = "\t=1+1"
    frame.loc[0, "Carriage return"] = "\r=2+2"
    frame.loc[0, "Line feed"] = "\n=3+3"
    csv_data = export_csv(frame)
    assert b"'=HYPERLINK" in csv_data
    assert b"'\t=1+1" in csv_data
    assert b"'\r=2+2" in csv_data
    assert b"'\n=3+3" in csv_data
    workbook = pd.ExcelFile(BytesIO(export_xlsx(frame)))
    assert workbook.sheet_names == ["Report"]
    with pytest.raises(ValueError, match="Start date"):
        report_data(
            url,
            "orders",
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),
        )
    with pytest.raises(ValueError, match="supported"):
        report_data(url, "unknown")
