"""Decision-focused dashboard metrics derived from saved workspace records."""
from __future__ import annotations

from calendar import month_abbr
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from database.models import Business, Invoice, Order, Product
from database.session import get_session_factory


ACTIVE_ORDER_STATUSES = {"Confirmed", "Processing", "Fulfilled"}


def _empty_dashboard() -> dict:
    """Return a stable dashboard shape when a workspace has no business yet."""
    return {
        "business_name": "No workspace",
        "currency": "USD",
        "kpis": {
            "order_value": 0.0,
            "order_value_change": 0.0,
            "orders": 0,
            "orders_change": 0,
            "average_order": 0.0,
            "fulfillment_rate": 0.0,
            "fulfilled_orders": 0,
            "eligible_orders": 0,
            "low_stock": 0,
            "active_products": 0,
        },
        "monthly_trend": [],
        "status_mix": [],
        "inventory": [],
        "currency_totals": [],
        "invoice_summary": {"confirmed": 0, "total": 0},
    }


def dashboard_insights(database_url: str, *, today: date | None = None) -> dict:
    """Build operational KPIs and trends from persisted workspace records.

    Order value is not labelled revenue because payment settlement is not
    tracked. Monetary totals and average order value use the business currency;
    order counts include all currencies and are never summed as money.
    """
    today = today or date.today()
    month_start = today.replace(day=1)
    previous_month_end = date.fromordinal(month_start.toordinal() - 1)
    previous_month_start = previous_month_end.replace(day=1)

    with get_session_factory(database_url)() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return _empty_dashboard()

        orders = session.scalars(
            select(Order).where(Order.business_id == business.id)
        ).all()
        products = session.scalars(
            select(Product).where(Product.business_id == business.id)
        ).all()
        invoices = session.scalars(
            select(Invoice).where(Invoice.business_id == business.id)
        ).all()
        business_name = business.name
        currency = business.currency

    active_orders = [order for order in orders if order.status in ACTIVE_ORDER_STATUSES]
    this_month = [
        order for order in active_orders if month_start <= order.order_date <= today
    ]
    previous_month = [
        order
        for order in active_orders
        if previous_month_start <= order.order_date <= previous_month_end
    ]

    this_month_currency = [
        order for order in this_month if order.currency == currency
    ]
    previous_month_currency = [
        order for order in previous_month if order.currency == currency
    ]
    month_value = sum(
        (order.total for order in this_month_currency), Decimal("0")
    )
    previous_value = sum(
        (order.total for order in previous_month_currency), Decimal("0")
    )
    fulfilled_month = sum(order.status == "Fulfilled" for order in this_month)
    fulfillment_rate = (
        fulfilled_month / len(this_month) * 100 if this_month else 0.0
    )
    average_order = (
        month_value / len(this_month_currency) if this_month_currency else Decimal("0")
    )

    active_products = [product for product in products if product.is_active]
    low_stock = [
        product
        for product in active_products
        if product.stock_on_hand <= product.reorder_level
    ]

    monthly_trend = []
    for offset in range(5, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        year, month_zero = divmod(month_index, 12)
        month = month_zero + 1
        first_day = date(year, month, 1)
        next_month = date(year + (month == 12), month % 12 + 1, 1)
        month_orders = [
            order
            for order in active_orders
            if first_day <= order.order_date < next_month
        ]
        currency_orders = [
            order for order in month_orders if order.currency == currency
        ]
        monthly_trend.append(
            {
                "Month": f"{month_abbr[month]} {str(year)[-2:]}",
                "Orders": len(month_orders),
                "Order value": float(
                    sum((order.total for order in currency_orders), Decimal("0"))
                ),
            }
        )

    status_counts: dict[str, int] = {}
    for order in orders:
        if order.status != "Cancelled":
            status_counts[order.status] = status_counts.get(order.status, 0) + 1

    currency_totals: dict[str, dict] = {}
    for order in active_orders:
        bucket = currency_totals.setdefault(
            order.currency,
            {"Currency": order.currency, "Orders": 0, "Order value": Decimal("0")},
        )
        bucket["Orders"] += 1
        bucket["Order value"] += order.total

    invoice_summary = {
        "confirmed": sum(invoice.review_status == "confirmed" for invoice in invoices),
        "total": len(invoices),
    }
    inventory = [
        {
            "SKU": product.sku,
            "Product": product.name,
            "On hand": float(product.stock_on_hand),
            "Reorder level": float(product.reorder_level),
            "Status": (
                "Reorder"
                if product.stock_on_hand <= product.reorder_level
                else "Healthy"
            ),
        }
        for product in sorted(
            active_products,
            key=lambda item: (
                item.stock_on_hand / item.reorder_level
                if item.reorder_level > 0
                else item.stock_on_hand
            ),
        )
    ]

    return {
        "business_name": business_name,
        "currency": currency,
        "kpis": {
            "order_value": float(month_value),
            "order_value_change": float(month_value - previous_value),
            "orders": len(this_month),
            "orders_change": len(this_month) - len(previous_month),
            "average_order": float(average_order),
            "fulfillment_rate": fulfillment_rate,
            "fulfilled_orders": fulfilled_month,
            "eligible_orders": len(this_month),
            "low_stock": len(low_stock),
            "active_products": len(active_products),
        },
        "monthly_trend": monthly_trend,
        "status_mix": [
            {"Status": status, "Orders": count}
            for status, count in sorted(status_counts.items())
        ],
        "inventory": inventory,
        "currency_totals": [
            {**item, "Order value": float(item["Order value"])}
            for item in currency_totals.values()
        ],
        "invoice_summary": invoice_summary,
    }
