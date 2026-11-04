"""Live operational dashboard for the current business workspace."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.service import dashboard_summary

settings = get_settings()
summary = dashboard_summary(settings.database_url)
st.title("Business overview")
st.caption(
    f"Live operational snapshot · {summary['business_name']} · "
    "Values reflect saved records only"
)

metric_columns = st.columns(5)
metrics = [
    ("Orders", summary["orders_total"]),
    ("Open orders", summary["orders_open"]),
    ("Awaiting fulfilment", summary["orders_awaiting_fulfilment"]),
    ("Confirmed invoices", summary["invoices_confirmed"]),
    ("Active products", summary["products_active"]),
]
for column, (label, value) in zip(metric_columns, metrics):
    column.metric(label, f"{value:,}")

low_stock = summary["products_low_stock"]
if low_stock:
    st.warning(
        f"{low_stock} active product(s) are at or below their reorder level. "
        "Review Inventory Management."
    )
else:
    st.success("No active products are currently at or below their reorder level.")

left, right = st.columns([1, 1])
with left:
    st.subheader("Order status")
    if summary["order_statuses"]:
        status_frame = pd.DataFrame(summary["order_statuses"])
        chart = px.bar(status_frame, x="Status", y="Orders", text_auto=True)
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Order status analysis will appear after orders are saved.")
with right:
    st.subheader("Order value by currency")
    st.caption("Currencies are intentionally kept separate; values are not combined.")
    if summary["currency_totals"]:
        st.dataframe(summary["currency_totals"], use_container_width=True, hide_index=True)
    else:
        st.info("No order values are available yet.")

st.subheader("Inventory position")
if summary["stock_levels"]:
    stock_frame = pd.DataFrame(summary["stock_levels"])
    st.dataframe(stock_frame, use_container_width=True, hide_index=True)
else:
    st.info(
        "No products have been added. Add real catalogue items and opening "
        "balances in Inventory Management."
    )

st.subheader("Recent processing activity")
if summary["recent_jobs"]:
    st.dataframe(pd.DataFrame(summary["recent_jobs"]), use_container_width=True, hide_index=True)
else:
    st.info(
        "No workflow activity has been recorded yet. Process a spreadsheet, "
        "confirm an invoice, or update an order or product to begin building history."
    )

st.divider()
nav_left, nav_middle, nav_right = st.columns(3)
nav_left.page_link(
    "ui/pages/data_workbench.py",
    label="Open Data Workbench",
    icon=":material/table_view:",
)
nav_middle.page_link(
    "ui/pages/reports.py",
    label="Explore reports",
    icon=":material/analytics:",
)
nav_right.page_link(
    "ui/pages/history.py",
    label="Review processing history",
    icon=":material/history:",
)
