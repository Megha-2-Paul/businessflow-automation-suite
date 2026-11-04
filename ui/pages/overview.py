"""Live operational dashboard for the selected business workspace."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.service import dashboard_summary
from ui.workspace import get_database_url

settings = get_settings()
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"
summary = dashboard_summary(get_database_url(settings.database_url))

st.markdown('<div class="bf-page-eyebrow">BUSINESS OPERATIONS</div>', unsafe_allow_html=True)
st.title("Business overview")
st.caption(
    f"Operational snapshot · {summary['business_name']} · "
    "Figures are calculated from records saved in the selected workspace."
)
if demo_mode:
    st.info(
        "Demo workspace: all records shown here are fictional examples stored "
        "separately from your live business database."
    )

metric_columns = st.columns(5)
metrics = [
    ("Total orders", summary["orders_total"]),
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

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Order status")
    if summary["order_statuses"]:
        status_frame = pd.DataFrame(summary["order_statuses"])
        chart = px.bar(
            status_frame, x="Status", y="Orders", text_auto=True,
            color="Orders", color_continuous_scale=["#bfdbfe", "#1769c2"],
        )
        chart.update_layout(
            height=320, margin=dict(l=12, r=12, t=20, b=12),
            plot_bgcolor="white", paper_bgcolor="white",
            coloraxis_showscale=False, xaxis_title=None, yaxis_title="Orders",
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Order status analysis will appear after orders are saved.")
with right:
    st.subheader("Order value by currency")
    st.caption("Currencies are kept separate and are never added together.")
    if summary["currency_totals"]:
        st.dataframe(summary["currency_totals"], use_container_width=True, hide_index=True)
    else:
        st.info("No order values are available yet.")

st.subheader("Inventory position")
if summary["stock_levels"]:
    st.dataframe(
        pd.DataFrame(summary["stock_levels"]),
        use_container_width=True, hide_index=True,
    )
else:
    st.info(
        "No products have been added. Add catalogue items and opening balances "
        "in Inventory Management."
    )

st.subheader("Recent processing activity")
if summary["recent_jobs"]:
    st.dataframe(
        pd.DataFrame(summary["recent_jobs"]),
        use_container_width=True, hide_index=True,
    )
else:
    st.info(
        "No workflow activity has been recorded yet. Process a spreadsheet, "
        "confirm an invoice, or update an order or product to begin building history."
    )

st.divider()
st.subheader("Continue working")
nav_left, nav_middle, nav_right = st.columns(3)
nav_left.page_link(
    "ui/pages/data_workbench.py", label="Process spreadsheets",
    icon=":material/table_view:",
)
nav_middle.page_link(
    "ui/pages/invoices.py", label="Review invoices",
    icon=":material/receipt_long:",
)
nav_right.page_link(
    "ui/pages/inventory.py", label="Manage inventory",
    icon=":material/inventory_2:",
)
