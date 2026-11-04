"""Period-based operational dashboard metrics from persisted business records."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from database.models import Business, Invoice, Order, Product
from database.session import get_session_factory, initialize_database


def dashboard_metrics(database_url: str, period_days: int = 30) -> dict[str, Any]:
    """Calculate dashboard KPIs and chart series from the selected workspace.

    Order value is grouped by currency and is never combined across currencies.
    Trend series use order_date, while inventory indicators use current balances.
    """
    if period_days not in {30, 90, 365}:
        raise ValueError("Dashboard period must be 30, 90 or 365 days.")
    initialize_database(database_url)

    today = date.today()
    start = today - timedelta(days=period_days - 1)
    previous_start = start - timedelta(days=period_days)
    with get_session_factory(database_url)() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return _empty_metrics(period_days, start, today)

        orders = list(session.scalars(
            select(Order).where(
                Order.business_id == business.id,
                Order.order_date >= previous_start,
                Order.order_date <= today,
            ).order_by(Order.order_date)
        ))
        current_orders = [order for order in orders if order.order_date >= start]
        previous_orders = [order for order in orders if order.order_date < start]
        products = list(session.scalars(
            select(Product).where(Product.business_id == business.id)
        ))
        active_products = [product for product in products if product.is_active]
        invoices = list(session.scalars(
            select(Invoice).where(
                Invoice.business_id == business.id,
                Invoice.invoice_date >= start,
                Invoice.invoice_date <= today,
                Invoice.review_status == "confirmed",
            )
        ))

        values: dict[str, Decimal] = defaultdict(Decimal)
        previous_values: dict[str, Decimal] = defaultdict(Decimal)
        included_statuses = {"Confirmed", "Processing", "Fulfilled"}
        for order in current_orders:
            if order.status in included_statuses:
                values[order.currency] += order.total
        for order in previous_orders:
            if order.status in included_statuses:
                previous_values[order.currency] += order.total

        trend: dict[str, int] = defaultdict(int)
        statuses: dict[str, int] = defaultdict(int)
        for order in current_orders:
            bucket = order.order_date.strftime("%Y-%m")
            trend[bucket] += 1
            statuses[order.status] += 1

        stock_groups = {"Healthy": 0, "Low stock": 0, "Out of stock": 0}
        low_stock = []
        for product in active_products:
            if product.stock_on_hand <= 0:
                group = "Out of stock"
            elif product.stock_on_hand <= product.reorder_level:
                group = "Low stock"
            else:
                group = "Healthy"
            stock_groups[group] += 1
            if group != "Healthy":
                low_stock.append({
                    "SKU": product.sku,
                    "Product": product.name,
                    "On hand": float(product.stock_on_hand),
                    "Reorder level": float(product.reorder_level),
                    "Status": group,
                })

        invoice_values: dict[str, Decimal] = defaultdict(Decimal)
        for invoice in invoices:
            if invoice.total is not None and invoice.currency:
                invoice_values[invoice.currency] += invoice.total

        currency_rows = []
        for currency in sorted(values):
            count = sum(
                order.currency == currency and order.status in included_statuses
                for order in current_orders
            )
            total = values[currency]
            previous_total = previous_values[currency]
            currency_rows.append({
                "Currency": currency,
                "Orders": count,
                "Order value": float(total),
                "Average order value": float(total / count) if count else 0,
                "Previous period value": float(previous_total),
                "Change": _percentage_change(total, previous_total),
            })

        return {
            "business_name": business.name,
            "period_days": period_days,
            "period_start": start,
            "period_end": today,
            "orders_count": len(current_orders),
            "previous_orders_count": len(previous_orders),
            "orders_change": _percentage_change(
                Decimal(len(current_orders)), Decimal(len(previous_orders))
            ),
            "open_orders": sum(
                order.status not in {"Fulfilled", "Cancelled"}
                for order in current_orders
            ),
            "fulfilled_orders": statuses.get("Fulfilled", 0),
            "confirmed_invoices": len(invoices),
            "invoice_values": [
                {"Currency": code, "Confirmed invoice value": float(amount)}
                for code, amount in sorted(invoice_values.items())
            ],
            "active_products": len(active_products),
            "low_stock_count": stock_groups["Low stock"] + stock_groups["Out of stock"],
            "stock_groups": [
                {"Stock status": label, "Products": count}
                for label, count in stock_groups.items()
            ],
            "low_stock_products": low_stock,
            "order_trend": [
                {"Month": month, "Orders": count}
                for month, count in sorted(trend.items())
            ],
            "order_statuses": [
                {"Status": label, "Orders": count}
                for label, count in sorted(statuses.items())
            ],
            "currency_totals": currency_rows,
        }


def _percentage_change(current: Decimal, previous: Decimal) -> float | None:
    if previous == 0:
        return None
    return float((current - previous) / previous * Decimal("100"))


def _empty_metrics(period_days: int, start: date, today: date) -> dict[str, Any]:
    return {
        "business_name": "No workspace",
        "period_days": period_days,
        "period_start": start,
        "period_end": today,
        "orders_count": 0,
        "previous_orders_count": 0,
        "orders_change": None,
        "open_orders": 0,
        "fulfilled_orders": 0,
        "confirmed_invoices": 0,
        "invoice_values": [],
        "active_products": 0,
        "low_stock_count": 0,
        "stock_groups": [],
        "low_stock_products": [],
        "order_trend": [],
        "order_statuses": [],
        "currency_totals": [],
    }
