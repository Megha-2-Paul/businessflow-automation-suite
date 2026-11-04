"""Database-backed operational summaries and report datasets."""
from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import (
    Business,
    Invoice,
    Order,
    ProcessingJob,
    Product,
    StockMovement,
)
from database.session import get_session_factory

REPORT_TYPES = ("orders", "invoices", "inventory", "stock_movements", "processing")


def _business_id(session: Session) -> int | None:
    return session.scalar(select(Business.id).order_by(Business.id).limit(1))


def _date_bounds(
    start_date: date | None, end_date: date | None
) -> tuple[datetime | None, datetime | None]:
    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be after end date.")
    start = datetime.combine(start_date, time.min, tzinfo=UTC) if start_date else None
    end = datetime.combine(end_date, time.max, tzinfo=UTC) if end_date else None
    return start, end


def dashboard_summary(database_url: str) -> dict[str, Any]:
    """Return live operational counts and grouped values for the first workspace."""
    with get_session_factory(database_url)() as session:
        business_id = _business_id(session)
        empty = {
            "business_name": "No workspace",
            "orders_total": 0,
            "orders_open": 0,
            "orders_awaiting_fulfilment": 0,
            "invoices_confirmed": 0,
            "products_active": 0,
            "products_low_stock": 0,
            "recent_jobs": [],
            "order_statuses": [],
            "stock_levels": [],
            "currency_totals": [],
        }
        if business_id is None:
            return empty
        business = session.get(Business, business_id)
        orders = session.scalars(
            select(Order).where(Order.business_id == business_id)
        ).all()
        products = session.scalars(
            select(Product).where(Product.business_id == business_id)
        ).all()
        statuses = session.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.business_id == business_id)
            .group_by(Order.status)
            .order_by(Order.status)
        ).all()
        currencies = session.execute(
            select(Order.currency, func.count(Order.id), func.sum(Order.total))
            .where(Order.business_id == business_id)
            .group_by(Order.currency)
            .order_by(Order.currency)
        ).all()
        jobs = session.scalars(
            select(ProcessingJob)
            .where(ProcessingJob.business_id == business_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(8)
        ).all()
        active_products = [item for item in products if item.is_active]
        return {
            "business_name": business.name,
            "orders_total": len(orders),
            "orders_open": sum(
                item.status not in {"Fulfilled", "Cancelled"} for item in orders
            ),
            "orders_awaiting_fulfilment": sum(
                item.status in {"Confirmed", "Processing"} for item in orders
            ),
            "invoices_confirmed": session.scalar(
                select(func.count(Invoice.id)).where(
                    Invoice.business_id == business_id,
                    Invoice.review_status == "confirmed",
                )
            )
            or 0,
            "products_active": len(active_products),
            "products_low_stock": sum(
                item.stock_on_hand <= item.reorder_level for item in active_products
            ),
            "recent_jobs": [
                {
                    "id": job.id,
                    "workflow": job.job_type.replace("_", " ").title(),
                    "status": job.status.replace("_", " ").title(),
                    "created_at": job.created_at,
                    "processed": job.records_processed,
                    "failed": job.records_failed,
                }
                for job in jobs
            ],
            "order_statuses": [
                {"Status": status, "Orders": count} for status, count in statuses
            ],
            "stock_levels": [
                {
                    "SKU": item.sku,
                    "Product": item.name,
                    "On hand": float(item.stock_on_hand),
                    "Reorder level": float(item.reorder_level),
                    "Unit": item.unit,
                    "Status": (
                        "Low stock"
                        if item.stock_on_hand <= item.reorder_level
                        else "In range"
                    ),
                }
                for item in sorted(active_products, key=lambda product: product.sku)
            ],
            "currency_totals": [
                {
                    "Currency": currency,
                    "Orders": count,
                    "Order value": str(total or 0),
                }
                for currency, count, total in currencies
            ],
        }


def report_data(
    database_url: str,
    report_type: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Build one report from persisted records, optionally filtered by date."""
    if report_type not in REPORT_TYPES:
        raise ValueError("Choose a supported report type.")
    start, end = _date_bounds(start_date, end_date)
    with get_session_factory(database_url)() as session:
        business_id = _business_id(session)
        if business_id is None:
            return pd.DataFrame()
        if report_type == "orders":
            query = select(Order).where(Order.business_id == business_id)
            if start:
                query = query.where(Order.created_at >= start)
            if end:
                query = query.where(Order.created_at <= end)
            rows = [
                {
                    "Order number": item.order_number,
                    "Customer": item.customer_name,
                    "Email": item.customer_email or "",
                    "Order date": item.order_date,
                    "Status": item.status,
                    "Currency": item.currency,
                    "Total": float(item.total),
                    "Created (UTC)": item.created_at,
                }
                for item in session.scalars(query.order_by(Order.created_at.desc())).all()
            ]
        elif report_type == "invoices":
            query = select(Invoice).where(Invoice.business_id == business_id)
            if start:
                query = query.where(Invoice.created_at >= start)
            if end:
                query = query.where(Invoice.created_at <= end)
            rows = [
                {
                    "Supplier": item.supplier,
                    "Invoice number": item.invoice_number,
                    "Invoice date": item.invoice_date,
                    "Due date": item.due_date,
                    "Currency": item.currency or "",
                    "Subtotal": float(item.subtotal) if item.subtotal is not None else None,
                    "Tax": float(item.tax) if item.tax is not None else None,
                    "Total": float(item.total) if item.total is not None else None,
                    "Review status": item.review_status,
                    "Saved (UTC)": item.created_at,
                }
                for item in session.scalars(query.order_by(Invoice.created_at.desc())).all()
            ]
        elif report_type == "inventory":
            items = session.scalars(
                select(Product)
                .where(Product.business_id == business_id)
                .order_by(Product.sku)
            ).all()
            rows = [
                {
                    "SKU": item.sku,
                    "Product": item.name,
                    "Unit": item.unit,
                    "On hand": float(item.stock_on_hand),
                    "Reorder level": float(item.reorder_level),
                    "Stock status": (
                        "Inactive"
                        if not item.is_active
                        else (
                            "Low stock"
                            if item.stock_on_hand <= item.reorder_level
                            else "In range"
                        )
                    ),
                    "Active": item.is_active,
                }
                for item in items
            ]
        elif report_type == "stock_movements":
            query = (
                select(StockMovement)
                .join(Product)
                .where(Product.business_id == business_id)
            )
            if start:
                query = query.where(StockMovement.created_at >= start)
            if end:
                query = query.where(StockMovement.created_at <= end)
            movements = session.scalars(
                query.order_by(StockMovement.created_at.desc())
            ).all()
            rows = [
                {
                    "Date (UTC)": item.created_at,
                    "SKU": item.product.sku,
                    "Product": item.product.name,
                    "Movement": item.movement_type,
                    "Quantity change": float(item.quantity_delta),
                    "Balance after": float(item.quantity_after),
                    "Reference": item.reference or "",
                    "Notes": item.notes or "",
                    "Order number": item.order.order_number if item.order else "",
                }
                for item in movements
            ]
        else:
            query = select(ProcessingJob).where(
                ProcessingJob.business_id == business_id
            )
            if start:
                query = query.where(ProcessingJob.created_at >= start)
            if end:
                query = query.where(ProcessingJob.created_at <= end)
            jobs = session.scalars(query.order_by(ProcessingJob.created_at.desc())).all()
            rows = [
                {
                    "Job ID": job.id,
                    "Workflow": job.job_type,
                    "Status": job.status,
                    "Records processed": job.records_processed,
                    "Records succeeded": job.records_succeeded,
                    "Records failed": job.records_failed,
                    "Created (UTC)": job.created_at,
                    "Started (UTC)": job.started_at,
                    "Completed (UTC)": job.completed_at,
                    "Error count": len(job.errors),
                }
                for job in jobs
            ]
    return pd.DataFrame(rows)


def processing_history(
    database_url: str,
    *,
    workflow: str = "All workflows",
    status: str = "All statuses",
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """Return filtered processing jobs with their logs and errors."""
    start, end = _date_bounds(start_date, end_date)
    with get_session_factory(database_url)() as session:
        business_id = _business_id(session)
        if business_id is None:
            return []
        query = select(ProcessingJob).where(ProcessingJob.business_id == business_id)
        if workflow != "All workflows":
            query = query.where(ProcessingJob.job_type == workflow)
        if status != "All statuses":
            query = query.where(ProcessingJob.status == status)
        if start:
            query = query.where(ProcessingJob.created_at >= start)
        if end:
            query = query.where(ProcessingJob.created_at <= end)
        jobs = session.scalars(
            query.order_by(ProcessingJob.created_at.desc()).limit(
                max(1, min(limit, 1000))
            )
        ).all()
        return [
            {
                "id": job.id,
                "workflow": job.job_type,
                "status": job.status,
                "records_processed": job.records_processed,
                "records_succeeded": job.records_succeeded,
                "records_failed": job.records_failed,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "logs": [
                    {
                        "level": log.level,
                        "message": log.message,
                        "created_at": log.created_at,
                    }
                    for log in sorted(job.logs, key=lambda entry: entry.created_at)
                ],
                "errors": [
                    {
                        "row_number": error.row_number,
                        "issue_type": error.issue_type,
                        "details": error.details,
                        "created_at": error.created_at,
                    }
                    for error in sorted(job.errors, key=lambda entry: entry.created_at)
                ],
            }
            for job in jobs
        ]
