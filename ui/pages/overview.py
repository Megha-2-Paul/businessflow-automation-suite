"""Operational dashboard with period-based KPIs and live business charts."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.dashboard import dashboard_metrics
from ui.workspace import get_database_url

settings = get_settings()
database_url = get_database_url(settings.database_url)
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"

st.markdown('<div class="bf-page-eyebrow">BUSINESS PERFORMANCE</div>', unsafe_allow_html=True)
st.title("Business overview")
period_label = st.selectbox(
    "Reporting period",
    ["Last 30 days", "Last 90 days", "Last 12 months"],
    index=0,
    label_visibility="collapsed",
    help="KPIs and order charts use the selected order-date range.",
)
period_days = {"Last 30 days": 30, "Last 90 days": 90, "Last 12 months": 365}[period_label]
summary = dashboard_metrics(database_url, period_days)

st.caption(
    f"{summary['business_name']}  ·  {summary['period_start']:%d %b %Y} – "
    f"{summary['period_end']:%d %b %Y}  ·  Calculated from saved workspace records"
)
if demo_mode:
    st.info(
        "DEMO WORKSPACE · Fictional sample records are isolated from your live business database."
    )

def _delta(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:+.1f}% vs previous period"


def _money(value: float) -> str:
    return f"{value:,.2f}"


currency_rows = summary["currency_totals"]
if len(currency_rows) == 1:
    currency = currency_rows[0]["Currency"]
    order_value = f"{currency} {_money(currency_rows[0]['Order value'])}"
    average_value = f"{currency} {_money(currency_rows[0]['Average order value'])}"
else:
    order_value = "See currency breakdown"
    average_value = "See currency breakdown"

metric_columns = st.columns(5)
metric_columns[0].metric(
    "Orders", f"{summary['orders_count']:,}", delta=_delta(summary["orders_change"])
)
metric_columns[1].metric("Open orders", f"{summary['open_orders']:,}")
metric_columns[2].metric("Order value", order_value)
metric_columns[3].metric("Avg. order value", average_value)
metric_columns[4].metric("Confirmed invoices", f"{summary['confirmed_invoices']:,}")

inventory_columns = st.columns(3)
inventory_columns[0].metric("Active products", f"{summary['active_products']:,}")
inventory_columns[1].metric("Products needing attention", f"{summary['low_stock_count']:,}")
inventory_columns[2].metric("Fulfilled orders", f"{summary['fulfilled_orders']:,}")

if summary["low_stock_count"]:
    st.warning(
        f"{summary['low_stock_count']} active product(s) are at or below their reorder level. "
        "Review the stock attention list below."
    )
else:
    st.success("All active products are currently above their reorder levels.")

st.divider()
left, right = st.columns([1.25, 1])
with left:
    st.subheader("Order trend")
    st.caption("Number of orders by calendar month, based on saved order dates.")
    if summary["order_trend"]:
        frame = pd.DataFrame(summary["order_trend"])
        chart = px.line(
            frame, x="Month", y="Orders", markers=True,
            color_discrete_sequence=["#258653"],
        )
        chart.update_traces(line_width=3, marker_size=8, fill="tozeroy",
                            fillcolor="rgba(37, 134, 83, 0.10)")
        chart.update_layout(
            height=300, margin=dict(l=10, r=10, t=16, b=10),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            xaxis_title=None, yaxis_title="Orders",
            font_color="#52645a", hovermode="x unified",
        )
        chart.update_yaxes(rangemode="tozero", gridcolor="#edf2ee")
        chart.update_xaxes(showgrid=False)
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("No orders were recorded in this period.")
with right:
    st.subheader("Order status")
    st.caption("Current status of orders created during the selected period.")
    if summary["order_statuses"]:
        frame = pd.DataFrame(summary["order_statuses"])
        chart = px.pie(
            frame, names="Status", values="Orders", hole=.62,
            color_discrete_sequence=["#258653", "#8dc9a1", "#e8b85b",
                                     "#7d9e8a", "#d9e4dc"],
        )
        chart.update_layout(
            height=300, margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="#ffffff", font_color="#52645a",
            legend_title_text="",
        )
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.info("Order status distribution will appear when orders are saved.")

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Inventory health")
    st.caption("Active catalogue products grouped by current stock position.")
    if summary["stock_groups"]:
        frame = pd.DataFrame(summary["stock_groups"])
        frame = frame[frame["Products"] > 0]
        if not frame.empty:
            chart = px.bar(
                frame, x="Stock status", y="Products", text_auto=True,
                color="Stock status",
                color_discrete_map={
                    "Healthy": "#258653", "Low stock": "#e8b85b",
                    "Out of stock": "#d96b63",
                },
            )
            chart.update_layout(
                height=270, margin=dict(l=10, r=10, t=16, b=10),
                showlegend=False, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                xaxis_title=None, yaxis_title="Products", font_color="#52645a",
            )
            chart.update_yaxes(rangemode="tozero", gridcolor="#edf2ee")
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("No active products are available.")
    else:
        st.info("Add products to see inventory health.")
with right:
    st.subheader("Order value by currency")
    st.caption("Values are based on orders in the selected period. Currencies are never combined.")
    if currency_rows:
        display = pd.DataFrame(currency_rows)[
            ["Currency", "Orders", "Order value", "Average order value", "Change"]
        ].copy()
        display["Order value"] = display["Order value"].map(_money)
        display["Average order value"] = display["Average order value"].map(_money)
        display["Change"] = display["Change"].map(
            lambda value: "—" if value is None else f"{value:+.1f}%"
        )
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No order values are available for this period.")

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Stock attention")
    st.caption("Products at or below their configured reorder level.")
    if summary["low_stock_products"]:
        st.dataframe(
            pd.DataFrame(summary["low_stock_products"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.success("No low-stock products.")
with right:
    st.subheader("Confirmed invoice value")
    st.caption("Confirmed invoices dated within the selected reporting period.")
    if summary["invoice_values"]:
        st.dataframe(
            pd.DataFrame(summary["invoice_values"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No confirmed invoices in this period.")

st.caption(
    "Business insight note: order value is based on saved order totals, not cash collected. "
    "Invoice totals are shown separately; payment status and profit are not currently tracked."
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
