"""Decision-focused dashboard for the selected business workspace."""
import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import get_settings
from reporting.dashboard import dashboard_insights
from ui.workspace import get_database_url


def _style_chart(fig, *, height: int = 330) -> None:
    """Apply consistent typography, spacing and grid styling to Plotly charts."""
    fig.update_layout(
        height=height,
        margin={"l": 12, "r": 12, "t": 24, "b": 12},
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"color": "#435349", "size": 12},
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#172b25"},
        legend={"bgcolor": "rgba(255,255,255,0)", "font": {"color": "#435349"}},
    )
    fig.update_xaxes(showgrid=False, automargin=True)
    fig.update_yaxes(
        gridcolor="#edf1ed",
        zerolinecolor="#dfe7e0",
        rangemode="tozero",
        automargin=True,
    )


settings = get_settings()
database_url = get_database_url(settings.database_url)
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"
data = dashboard_insights(database_url)
kpis = data["kpis"]
currency = data["currency"]

st.markdown(
    '<div class="bf-page-eyebrow">BUSINESS PERFORMANCE</div>',
    unsafe_allow_html=True,
)
st.title("Business overview")
st.caption(
    f"{data['business_name']} · A live view of saved orders, fulfilment and stock."
)

if demo_mode:
    st.info(
        "DEMO DATA · Fictional business records for product demonstration. "
        "Switch to Live workspace to see your own saved records."
    )
else:
    st.caption(
        "Live workspace · Figures below are calculated from records saved "
        "in your configured database."
    )

st.subheader("This month's performance")
st.caption(
    f"Order activity for {data.get('period_label', 'the current month')}. "
    f"Order values and average order value are shown in {currency}; "
    "these figures are not collected revenue."
)
metrics = [
    (
        "Order value",
        f"{currency} {kpis['order_value']:,.2f}",
        f"{kpis['order_value_change']:+,.2f} vs prior month",
        "Confirmed, processing and fulfilled orders in the business currency.",
    ),
    (
        "Orders",
        f"{kpis['orders']:,}",
        f"{kpis['orders_change']:+,} vs prior month",
        "Active orders across all currencies; drafts and cancelled orders excluded.",
    ),
    (
        "Average order",
        f"{currency} {kpis['average_order']:,.2f}",
        "Current month · selected currency",
        "Average value of active orders denominated in the business currency.",
    ),
    (
        "Fulfilment rate",
        f"{kpis['fulfillment_rate']:.1f}%",
        f"{kpis['fulfilled_orders']} of {kpis['eligible_orders']} active orders",
        "Fulfilled orders divided by confirmed, processing and fulfilled orders.",
    ),
    (
        "Low-stock items",
        f"{kpis['low_stock']:,}",
        f"of {kpis['active_products']} active products",
        "Products at or below their configured reorder level.",
    ),
]
for start in (0, 3):
    row = st.columns(3 if start == 0 else 2)
    for column, metric in zip(row, metrics[start : start + len(row)]):
        label, value, delta, help_text = metric
        column.metric(label, value, delta, help=help_text)

if kpis["low_stock"]:
    st.warning(
        f"{kpis['low_stock']} active products are at or below their reorder "
        "level. Review the inventory list before accepting more orders."
    )
else:
    st.success("All active products are currently above their reorder levels.")

trend = pd.DataFrame(data["monthly_trend"])
st.divider()
st.subheader("Sales and order trends")
st.caption(
    "Order counts include all currencies. Order values include only the "
    f"selected business currency ({currency}) and are not collected revenue."
)
left, right = st.columns(2)
with left:
    st.markdown("**Order activity · last 6 months**")
    if not trend.empty:
        fig = px.bar(
            trend,
            x="Month",
            y="Orders",
            text_auto=True,
            labels={"Month": "Month", "Orders": "Orders"},
        )
        fig.update_traces(
            marker_color="#72b987",
            marker_line_width=0,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>%{y} orders<extra></extra>",
        )
        _style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Order activity will appear after orders are recorded.")

with right:
    st.markdown(f"**Order value · {currency}**")
    if not trend.empty and trend["Order value"].sum() > 0:
        fig = px.area(
            trend,
            x="Month",
            y="Order value",
            labels={"Month": "Month", "Order value": f"Order value ({currency})"},
        )
        fig.update_traces(
            line={"color": "#23845b", "width": 3},
            fillcolor="rgba(115,185,135,.18)",
            hovertemplate="%{x}<br>%{y:,.2f} " + currency + "<extra></extra>",
        )
        _style_chart(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            f"Order value trend will appear when active {currency} orders exist."
        )

st.divider()
st.subheader("Operations snapshot")
left, right = st.columns([0.9, 1.35])
with left:
    st.markdown("**Orders by status**")
    st.caption("Draft orders are included; cancelled orders are excluded.")
    status = pd.DataFrame(data["status_mix"])
    if not status.empty:
        fig = px.pie(
            status,
            names="Status",
            values="Orders",
            hole=0.62,
            color_discrete_sequence=[
                "#23845b",
                "#83bd98",
                "#a9d6b5",
                "#d4e2d7",
                "#5b9b78",
            ],
        )
        fig.update_layout(
            height=330,
            margin={"l": 8, "r": 8, "t": 18, "b": 8},
            paper_bgcolor="#ffffff",
            font={"color": "#435349", "size": 12},
            legend_title_text="",
            legend={"orientation": "h", "y": -0.08},
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}: %{value} orders (%{percent})<extra></extra>",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Status distribution will appear after orders are saved.")

with right:
    st.markdown("**Inventory health**")
    st.caption("Products closest to or below their configured reorder level.")
    inventory = pd.DataFrame(data["inventory"])
    if not inventory.empty:
        st.dataframe(
            inventory,
            use_container_width=True,
            hide_index=True,
            column_config={
                "On hand": st.column_config.NumberColumn(format="%.3f"),
                "Reorder level": st.column_config.NumberColumn(format="%.3f"),
            },
        )
    else:
        st.info("Add products to start monitoring stock levels.")

st.divider()
st.subheader("Order value by currency")
st.caption(
    "Currencies are reported separately. Active orders only; "
    "draft and cancelled orders are excluded."
)
if data["currency_totals"]:
    st.dataframe(
        pd.DataFrame(data["currency_totals"]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No active order values are available yet.")

st.subheader("Invoice processing")
invoice = data["invoice_summary"]
invoice_columns = st.columns(3)
invoice_columns[0].metric("Invoices saved", invoice["total"])
invoice_columns[1].metric("Confirmed invoices", invoice["confirmed"])
other_review_statuses = invoice["total"] - invoice["confirmed"]
invoice_columns[2].metric("Other review statuses", other_review_statuses)
st.caption(
    "Counts reflect saved invoice review records. Payment status and "
    "accounts-receivable balances are not tracked by this application."
)

st.divider()
st.subheader("Continue working")
nav_left, nav_middle, nav_right = st.columns(3)
nav_left.page_link(
    "ui/pages/data_workbench.py",
    label="Process spreadsheets",
    icon=":material/table_view:",
)
nav_middle.page_link(
    "ui/pages/invoices.py",
    label="Review invoices",
    icon=":material/receipt_long:",
)
nav_right.page_link(
    "ui/pages/inventory.py",
    label="Manage inventory",
    icon=":material/inventory_2:",
)
