"""Decision-focused overview built entirely from saved workspace records."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.dashboard import dashboard_insights
from reporting.service import dashboard_summary
from ui.workspace import get_database_url

settings = get_settings()
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"
database_url = get_database_url(settings.database_url)
summary = dashboard_summary(database_url)
insights = dashboard_insights(database_url)

st.markdown('<div class="bf-page-eyebrow">BUSINESS PERFORMANCE</div>', unsafe_allow_html=True)
st.title("Business overview")
st.caption(
    f"{summary['business_name']} · Live operational snapshot · "
    "All figures are calculated from saved workspace records."
)
if demo_mode:
    st.info(
        "DEMO DATA · Fictional example records for product demonstration. "
        "Switch to Live workspace to view your own saved business records."
    )

low_stock = insights["low_stock_products"]
orders_total = summary["orders_total"]
fulfilled = insights["fulfilled_orders"]
fulfilment_rate = insights["fulfilment_rate"]
metric_columns = st.columns(5)
metric_columns[0].metric("Total orders", f"{orders_total:,}")
metric_columns[1].metric("Fulfilled orders", f"{fulfilled:,}")
metric_columns[2].metric(
    "Fulfilment rate", f"{fulfilment_rate:.1f}%" if fulfilment_rate is not None else "—",
    help="Fulfilled orders divided by all non-cancelled orders. Drafts are included.",
)
metric_columns[3].metric("Products to reorder", f"{len(low_stock):,}")
metric_columns[4].metric("Confirmed invoices", f"{insights['confirmed_invoice_count']:,}")

if low_stock:
    st.warning(
        f"{len(low_stock)} active product(s) are at or below their reorder level. "
        "Review the stock risk list below before accepting more demand."
    )
else:
    st.success("No active products are currently at or below their reorder level.")

st.subheader("Order activity")
st.caption("Monthly order counts for the last six calendar months, based on order dates.")
if insights["monthly_orders"]:
    trend = pd.DataFrame(insights["monthly_orders"])
    chart = px.bar(
        trend, x="Month", y="Orders", text_auto=True,
        color_discrete_sequence=["#72b58c"],
    )
    chart.update_layout(
        height=300, margin=dict(l=8, r=8, t=16, b=8),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title=None, yaxis_title="Orders",
    )
    chart.update_traces(marker_line_width=0, textposition="outside")
    st.plotly_chart(chart, use_container_width=True)
else:
    st.info("Order activity will appear after orders are saved.")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Order value by currency")
    st.caption("Non-cancelled order totals. Different currencies are never combined.")
    if insights["order_value_by_currency"]:
        st.dataframe(
            pd.DataFrame(insights["order_value_by_currency"]),
            use_container_width=True, hide_index=True,
        )
        if insights["monthly_revenue"]:
            revenue = pd.DataFrame(insights["monthly_revenue"])
            revenue_chart = px.line(
                revenue, x="Month", y="Order value", color="Currency",
                markers=True, facet_row="Currency",
                color_discrete_sequence=["#24845a", "#77a98c", "#a7c9b4"],
            )
            revenue_chart.update_layout(
                height=max(220, 190 * revenue["Currency"].nunique()),
                margin=dict(l=8, r=8, t=16, b=8),
                plot_bgcolor="white", paper_bgcolor="white",
                showlegend=False, xaxis_title=None, yaxis_title="Order value",
            )
            st.plotly_chart(revenue_chart, use_container_width=True)
    else:
        st.info("Order values will appear after non-cancelled orders are saved.")

with right:
    st.subheader("Inventory health")
    if insights["inventory_status"]:
        inventory = pd.DataFrame(insights["inventory_status"])
        inventory = inventory[inventory["Products"] > 0]
        if not inventory.empty:
            stock_chart = px.pie(
                inventory, names="Stock status", values="Products", hole=0.62,
                color="Stock status",
                color_discrete_map={
                    "Healthy": "#63a77e", "Low stock": "#e7b84b",
                    "Out of stock": "#d96b63",
                },
            )
            stock_chart.update_layout(
                height=290, margin=dict(l=8, r=8, t=16, b=8),
                paper_bgcolor="white", legend_title=None,
            )
            st.plotly_chart(stock_chart, use_container_width=True)
        else:
            st.info("No active catalogue products are available.")
    else:
        st.info("Inventory status will appear after products are added.")

    st.subheader("Average order value")
    st.caption("Calculated separately for each currency, excluding cancelled orders.")
    if insights["average_order_value"]:
        st.dataframe(
            pd.DataFrame(insights["average_order_value"]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Average order value is unavailable until eligible orders exist.")

st.subheader("Stock requiring attention")
if low_stock:
    st.dataframe(pd.DataFrame(low_stock), use_container_width=True, hide_index=True)
else:
    st.caption("No products currently require a reorder review.")

st.subheader("Recent processing activity")
if summary["recent_jobs"]:
    st.dataframe(
        pd.DataFrame(summary["recent_jobs"]),
        use_container_width=True, hide_index=True,
    )
else:
    st.info("Completed spreadsheet and invoice workflows will appear here.")

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
