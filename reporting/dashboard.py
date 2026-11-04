"""Decision-focused dashboard aggregates derived from saved workspace records."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from database.models import Business, Invoice, Order, Product
from database.session import get_session_factory


def dashboard_insights(database_url: str, *, today: date | None = None) -> dict:
    """Build dashboard KPIs and six-month trends from persisted records only."""
    today = today or date.today()
    month_start = date(today.year, today.month, 1)
    months = []
    cursor = month_start
    for _ in range(5):
        cursor = date(cursor.year - 1, 12, 1) if cursor.month == 1 else date(
            cursor.year, cursor.month - 1, 1
        )
    for _ in range(6):
        months.append(cursor)
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(
            cursor.year, cursor.month + 1, 1
        )
    month_keys = {item.strftime("%Y-%m"): item.strftime("%b %Y") for item in months}

    with get_session_factory(database_url)() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return {
                "monthly_orders": [], "monthly_revenue": [], "order_value_by_currency": [],
                "average_order_value": [], "inventory_status": [], "invoice_totals": [],
                "fulfilment_rate": None, "fulfilled_orders": 0, "eligible_orders": 0,
                "low_stock_products": [], "confirmed_invoice_count": 0,
            }

        orders = session.scalars(
            select(Order).where(Order.business_id == business.id)
        ).all()
        products = session.scalars(
            select(Product).where(Product.business_id == business.id, Product.is_active.is_(True))
        ).all()
        invoices = session.scalars(
            select(Invoice).where(
                Invoice.business_id == business.id,
                Invoice.review_status == "confirmed",
            )
        ).all()

        monthly_order_counts = defaultdict(int)
        monthly_revenue = defaultdict(Decimal)
        monthly_revenue_counts = defaultdict(int)
        order_totals = defaultdict(Decimal)
        order_counts = defaultdict(int)
        for order in orders:
            key = order.order_date.strftime("%Y-%m")
            if key in month_keys:
                monthly_order_counts[key] += 1
                monthly_revenue[(key, order.currency)] += order.total
                monthly_revenue_counts[(key, order.currency)] += 1
            if order.status != "Cancelled":
                order_totals[order.currency] += order.total
                order_counts[order.currency] += 1

        eligible_orders = [order for order in orders if order.status != "Cancelled"]
        fulfilled_orders = sum(order.status == "Fulfilled" for order in eligible_orders)
        fulfilment_rate = (
            fulfilled_orders / len(eligible_orders) * 100 if eligible_orders else None
        )

        inventory_buckets = {"Healthy": 0, "Low stock": 0, "Out of stock": 0}
        low_stock_products = []
        for product in products:
            if product.stock_on_hand <= 0:
                inventory_buckets["Out of stock"] += 1
            elif product.stock_on_hand <= product.reorder_level:
                inventory_buckets["Low stock"] += 1
            else:
                inventory_buckets["Healthy"] += 1
            if product.stock_on_hand <= product.reorder_level:
                low_stock_products.append({
                    "SKU": product.sku, "Product": product.name,
                    "On hand": float(product.stock_on_hand),
                    "Reorder level": float(product.reorder_level),
                })

        invoice_totals = defaultdict(Decimal)
        invoice_counts = defaultdict(int)
        for invoice in invoices:
            if invoice.total is not None and invoice.currency:
                invoice_totals[invoice.currency] += invoice.total
                invoice_counts[invoice.currency] += 1

        return {
            "monthly_orders": [
                {"Month": month_keys[key], "Orders": monthly_order_counts[key]}
                for key in month_keys
            ],
            "monthly_revenue": [
                {"Month": month_keys[key], "Currency": currency, "Order value": float(value)}
                for (key, currency), value in sorted(monthly_revenue.items())
            ],
            "order_value_by_currency": [
                {"Currency": currency, "Order value": float(value), "Orders": order_counts[currency]}
                for currency, value in sorted(order_totals.items())
            ],
            "average_order_value": [
                {"Currency": currency, "Average order value": float(
                    order_totals[currency] / order_counts[currency]
                )}
                for currency in sorted(order_totals) if order_counts[currency]
            ],
            "inventory_status": [
                {"Stock status": label, "Products": count}
                for label, count in inventory_buckets.items()
            ],
            "invoice_totals": [
                {"Currency": currency, "Confirmed invoices": invoice_counts[currency],
                 "Confirmed invoice value": float(invoice_totals[currency])}
                for currency in sorted(invoice_totals)
            ],
            "fulfilment_rate": fulfilment_rate,
            "fulfilled_orders": fulfilled_orders,
            "eligible_orders": len(eligible_orders),
            "low_stock_products": sorted(low_stock_products, key=lambda row: row["SKU"]),
            "confirmed_invoice_count": len(invoices),
        }
