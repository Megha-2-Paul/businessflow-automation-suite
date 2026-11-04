"""Decision-focused business dashboard for the selected workspace."""
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

st.markdown('<div class="bf-page-eyebrow">BUSINESS PERFORMANCE</div>', unsafe_allow_html=True)
st.title("Business overview")
st.caption(
    f"{summary['business_name']} · Live indicators calculated from saved workspace records"
)
if demo_mode:
    st.info(
        "DEMO DATA · Fictional records in an isolated workspace. Switch to Live workspace "
        "to view your own saved business data."
    )

st.subheader("At a glance")
metric_columns = st.columns(4)
metrics = [
    ("Orders this month", f"{summary['orders_this_month']:,}"),
    ("Open orders", f"{summary['orders_open']:,}"),
    (
        "Fulfilment rate",
        f"{summary['fulfillment_rate']:.1f}%"
        if summary["fulfillment_rate"] is not None else "—",
    ),
    ("Products to reorder", f"{summary['products_low_stock']:,}"),
]
for column, (label, value) in zip(metric_columns, metrics):
    column.metric(label, value)

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Order value this month")
    st.caption("Saved order value grouped by currency. This is not collected revenue.")
    if summary["current_month_order_totals"]:
        st.dataframe(
            pd.DataFrame(summary["current_month_order_totals"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No orders have been recorded this month.")
with right:
    st.subheader("Confirmed vendor invoices")
    st.caption("Supplier invoice liabilities, shown separately by currency.")
    if summary["confirmed_vendor_payables"]:
        st.dataframe(
            pd.DataFrame(summary["confirmed_vendor_payables"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No confirmed supplier invoices are recorded.")

if summary["overdue_invoice_count"]:
    st.warning(
        f"{summary['overdue_invoice_count']} confirmed supplier invoice(s) are past due. "
        "Review the invoice register before scheduling payments."
    )
else:
    st.success("No confirmed supplier invoices are currently past due.")

st.divider()
trend_column, status_column = st.columns([1.25, 1])
with trend_column:
    st.subheader("Order trend")
    st.caption("Monthly order value from saved records; currencies are never combined.")
    if summary["monthly_order_trend"]:
        frame = pd.DataFrame(summary["monthly_order_trend"])
        chart = px.line(
            frame, x="Month", y="Order value", color="Currency",
            markers=True, hover_data=["Orders"],
        )
        chart.update_layout(
            height=330, margin=dict(l=8, r=8, t=18, b=8),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            legend_title_text="Currency", xaxis_title=None,
            yaxis_title="Order value",
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Order trends will appear after orders are saved.")
with status_column:
    st.subheader("Order status")
    if summary["order_statuses"]:
        frame = pd.DataFrame(summary["order_statuses"])
        chart = px.pie(frame, names="Status", values="Orders", hole=.62)
        chart.update_layout(
            height=330, margin=dict(l=8, r=8, t=18, b=8),
            paper_bgcolor="#ffffff", legend_title_text="Status",
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("No order records are available yet.")

st.divider()
st.subheader("Inventory requiring attention")
stock_column, attention_column = st.columns([1.2, 1])
with stock_column:
    if summary["stock_levels"]:
        frame = pd.DataFrame(summary["stock_levels"])
        chart = px.bar(
            frame, x="SKU", y=["On hand", "Reorder level"], barmode="group",
            color_discrete_sequence=["#55a875", "#e7b65c"],
        )
        chart.update_layout(
            height=330, margin=dict(l=8, r=8, t=18, b=8),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            xaxis_title=None, yaxis_title="Quantity", legend_title_text="",
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Add products to see stock levels.")
with attention_column:
    attention = pd.DataFrame(summary["stock_levels"])
    if not attention.empty:
        attention = attention[attention["Status"] == "Low stock"]
    if not attention.empty:
        st.warning(f"{len(attention)} product(s) need a reorder review.")
        st.dataframe(
            attention[["SKU", "Product", "On hand", "Reorder level", "Unit"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.success("All active products are above their reorder levels.")

st.subheader("Recent processing activity")
if summary["recent_jobs"]:
    st.dataframe(
        pd.DataFrame(summary["recent_jobs"]), use_container_width=True, hide_index=True
    )
else:
    st.info("Spreadsheet, invoice and other workflow activity will appear here after processing.")

st.divider()
st.subheader("Continue working")
nav_left, nav_middle, nav_right = st.columns(3)
nav_left.page_link("ui/pages/data_workbench.py", label="Process spreadsheets", icon=":material/table_view:")
nav_middle.page_link("ui/pages/invoices.py", label="Review invoices", icon=":material/receipt_long:")
nav_right.page_link("ui/pages/inventory.py", label="Manage inventory", icon=":material/inventory_2:")
