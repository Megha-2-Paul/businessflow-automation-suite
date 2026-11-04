"""Decision-focused dashboard for the selected business workspace."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.dashboard import dashboard_insights
from ui.workspace import get_database_url

settings = get_settings()
database_url = get_database_url(settings.database_url)
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"
data = dashboard_insights(database_url)
kpis = data["kpis"]

st.markdown('<div class="bf-page-eyebrow">BUSINESS PERFORMANCE</div>', unsafe_allow_html=True)
st.title("Business overview")
st.caption(f"{data['business_name']} · A live view of saved orders, fulfilment and stock.")
if demo_mode:
    st.info("DEMO DATA · Fictional business records for product demonstration. Switch to Live workspace to see your own saved records.")
else:
    st.caption("Live workspace · Figures below are calculated from records saved in your configured database.")

currency = data["currency"]
st.subheader("This month's performance")
st.caption(f"Order activity from {pd.Timestamp.today().strftime('%B %Y')} · Order values shown in {currency}. This is order value, not collected revenue.")
columns = st.columns(5)
metrics = [
    ("Order value", f"{currency} {kpis.get('order_value', 0):,.2f}", f"{kpis.get('order_value_change', 0):+,.2f} vs prior month"),
    ("Orders", f"{kpis.get('orders', 0):,}", f"{kpis.get('orders_change', 0):+} vs prior month"),
    ("Average order", f"{currency} {kpis.get('average_order', 0):,.2f}", "Current month · selected currency"),
    ("Fulfilment rate", f"{kpis.get('fulfillment_rate', 0):.1f}%", f"{kpis.get('fulfilled_orders', 0)} fulfilled this month"),
    ("Low-stock items", f"{kpis.get('low_stock', 0):,}", f"of {kpis.get('active_products', 0)} active products"),
]
for column, (label, value, help_text) in zip(columns, metrics):
    column.metric(label, value, help_text)

if kpis.get("low_stock", 0):
    st.warning(f"{kpis['low_stock']} active products are at or below their reorder level. Review the inventory list below before accepting more orders.")
else:
    st.success("All active products are currently above their reorder levels.")

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Order activity · last 6 months")
    trend = pd.DataFrame(data["monthly_trend"])
    if not trend.empty:
        fig = px.bar(trend, x="Month", y="Orders", text_auto=True)
        fig.update_traces(marker_color="#72b987", marker_line_width=0, textposition="outside")
        fig.update_layout(height=315, margin=dict(l=10, r=10, t=20, b=10),
                          plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                          font_color="#435349", yaxis_title="Orders", xaxis_title=None,
                          showlegend=False)
        fig.update_yaxes(gridcolor="#edf1ed", rangemode="tozero")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Order trend will appear after orders are recorded.")
with right:
    st.subheader("Order value trend")
    if not trend.empty and trend["Order value"].sum() > 0:
        fig = px.area(trend, x="Month", y="Order value")
        fig.update_traces(line_color="#23845b", fillcolor="rgba(115,185,135,.18)")
        fig.update_layout(height=315, margin=dict(l=10, r=10, t=20, b=10),
                          plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                          font_color="#435349", yaxis_title=f"Order value ({currency})",
                          xaxis_title=None, showlegend=False)
        fig.update_yaxes(gridcolor="#edf1ed", rangemode="tozero")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Order value trend will appear when non-cancelled orders exist in this currency.")

st.divider()
left, right = st.columns([1, 1.2])
with left:
    st.subheader("Orders by status")
    status = pd.DataFrame(data["status_mix"])
    if not status.empty:
        fig = px.pie(status, names="Status", values="Orders", hole=.62,
                     color_discrete_sequence=["#75b989", "#a9d6b5", "#3d8d64", "#cbd8ce"])
        fig.update_layout(height=300, margin=dict(l=8, r=8, t=12, b=8),
                          paper_bgcolor="#ffffff", font_color="#435349",
                          legend_title_text="")
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Status distribution will appear after orders are saved.")
with right:
    st.subheader("Inventory health")
    inventory = pd.DataFrame(data["inventory"])
    if not inventory.empty:
        st.dataframe(inventory, use_container_width=True, hide_index=True,
                     column_config={"On hand": st.column_config.NumberColumn(format="%.3f"),
                                    "Reorder level": st.column_config.NumberColumn(format="%.3f")})
    else:
        st.info("Add products to start monitoring stock levels.")

st.subheader("Order value by currency")
st.caption("Currencies are intentionally reported separately; different currencies are never added together.")
if data["currency_totals"]:
    st.dataframe(pd.DataFrame(data["currency_totals"]), use_container_width=True, hide_index=True)
else:
    st.info("No order values are available yet.")

st.subheader("Invoice processing")
invoice = data["invoice_summary"]
invoice_columns = st.columns(3)
invoice_columns[0].metric("Invoices saved", invoice.get("total", 0))
invoice_columns[1].metric("Confirmed invoices", invoice.get("confirmed", 0))
invoice_columns[2].metric("Awaiting review", max(invoice.get("total", 0) - invoice.get("confirmed", 0), 0))
st.caption("Invoice counts reflect saved review records; payment status and accounts-receivable balances are not tracked by this application.")

st.divider()
st.subheader("Continue working")
nav_left, nav_middle, nav_right = st.columns(3)
nav_left.page_link("ui/pages/data_workbench.py", label="Process spreadsheets", icon=":material/table_view:")
nav_middle.page_link("ui/pages/invoices.py", label="Review invoices", icon=":material/receipt_long:")
nav_right.page_link("ui/pages/inventory.py", label="Manage inventory", icon=":material/inventory_2:")
