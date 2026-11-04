"""Decision-focused dashboard metrics derived from saved workspace records."""
from __future__ import annotations

from calendar import month_abbr
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from database.models import Business, Invoice, Order, Product
from database.session import get_session_factory


ACTIVE_ORDER_STATUSES = {"Confirmed", "Processing", "Fulfilled"}


def dashboard_insights(database_url: str, *, today: date | None = None) -> dict:
    """Build current/previous-month KPIs and six-month trends from persisted data.

    Order value is not labelled revenue because the application does not track
    payment settlement. Currency totals are kept separate.
    """
    today = today or date.today()
    month_start = today.replace(day=1)
    previous_month_end = month_start.fromordinal(month_start.toordinal() - 1)
    previous_month_start = previous_month_end.replace(day=1)
    with get_session_factory(database_url)() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            return {"business_name": "No workspace", "currency": "USD", "kpis": {},
                    "monthly_trend": [], "status_mix": [], "inventory": [],
                    "currency_totals": [], "invoice_summary": {}}
        orders = session.scalars(select(Order).where(Order.business_id == business.id)).all()
        products = session.scalars(select(Product).where(Product.business_id == business.id)).all()
        invoices = session.scalars(select(Invoice).where(Invoice.business_id == business.id)).all()

    currency = business.currency
    active_orders = [o for o in orders if o.status in ACTIVE_ORDER_STATUSES]
    this_month = [o for o in active_orders if month_start <= o.order_date <= today]
    previous_month = [o for o in active_orders if previous_month_start <= o.order_date <= previous_month_end]
    month_value = sum((o.total for o in this_month if o.currency == currency), Decimal("0"))
    previous_value = sum((o.total for o in previous_month if o.currency == currency), Decimal("0"))
    month_count = len(this_month)
    previous_count = len(previous_month)
    fulfilled_month = sum(o.status == "Fulfilled" for o in this_month)
    fulfillment_rate = (fulfilled_month / month_count * 100) if month_count else 0.0
    avg_order = month_value / max(sum(o.currency == currency for o in this_month), 1)
    low_stock = [p for p in products if p.is_active and p.stock_on_hand <= p.reorder_level]
    active_products = [p for p in products if p.is_active]

    trend = []
    for offset in range(5, -1, -1):
        month_index = today.year * 12 + today.month - 1 - offset
        year, month_zero = divmod(month_index, 12)
        month = month_zero + 1
        first = date(year, month, 1)
        next_first = date(year + (month == 12), month % 12 + 1, 1)
        rows = [o for o in active_orders if first <= o.order_date < next_first and o.currency == currency]
        trend.append({"Month": f"{month_abbr[month]} {str(year)[-2:]}",
                      "Orders": len(rows), "Order value": float(sum((o.total for o in rows), Decimal("0")))})

    status_counts = {}
    for order in orders:
        if order.status != "Cancelled":
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
    currency_totals = {}
    for order in active_orders:
        bucket = currency_totals.setdefault(order.currency, {"Currency": order.currency, "Orders": 0, "Order value": Decimal("0")})
        bucket["Orders"] += 1
        bucket["Order value"] += order.total
    invoice_summary = {
        "confirmed": sum(i.review_status == "confirmed" for i in invoices),
        "total": len(invoices),
    }
    return {
        "business_name": business.name,
        "currency": currency,
        "kpis": {
            "order_value": float(month_value),
            "order_value_change": float(month_value - previous_value),
            "orders": month_count,
            "orders_change": month_count - previous_count,
            "average_order": float(avg_order),
            "fulfillment_rate": fulfillment_rate,
            "fulfilled_orders": fulfilled_month,
            "low_stock": len(low_stock),
            "active_products": len(active_products),
        },
        "monthly_trend": trend,
        "status_mix": [{"Status": key, "Orders": value} for key, value in sorted(status_counts.items())],
        "inventory": [{"SKU": p.sku, "Product": p.name, "On hand": float(p.stock_on_hand),
                       "Reorder level": float(p.reorder_level),
                       "Status": "Reorder" if p.stock_on_hand <= p.reorder_level else "Healthy"}
                      for p in sorted(active_products, key=lambda item: item.stock_on_hand / max(item.reorder_level, Decimal("1")))],
        "currency_totals": [{**item, "Order value": float(item["Order value"])} for item in currency_totals.values()],
        "invoice_summary": invoice_summary,
    }
