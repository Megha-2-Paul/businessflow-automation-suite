"""Order entry, editing and lifecycle management."""
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import or_, select

from config.settings import get_settings
from database.models import Business, Order
from database.session import get_session_factory
from services.inventory_service import list_products
from services.order_service import (
    STATUSES,
    OrderServiceError,
    change_order_status,
    create_order,
    update_order,
)

settings = get_settings()
factory = get_session_factory(settings.database_url)
catalogue = list_products(settings.database_url, active_only=True)
sku_to_id = {item.sku: item.id for item in catalogue}
product_options = ["Non-stock", *sku_to_id]


def resolve_product_lines(frame):
    """Translate visible SKU choices into optional catalogue product IDs."""
    rows = frame.to_dict(orient="records")
    for row in rows:
        row["product_id"] = sku_to_id.get(row.pop("product_sku", "Non-stock"))
    return rows


st.title("Order management")
st.caption("Create customer orders, edit drafts and track fulfilment status.")

with st.expander("Create an order", expanded=False):
    with st.form("create_order_form"):
        number = st.text_input("Order number")
        customer = st.text_input("Customer name")
        email = st.text_input("Customer email")
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input("Order date", value=date.today())
        with col2:
            currency = st.text_input("Currency", value="USD", max_chars=3)
        st.caption("Line amounts and order total are calculated using decimal arithmetic.")
        lines = st.data_editor(
            pd.DataFrame([{
                "description": "", "quantity": 1, "unit_price": 0.0,
                "product_sku": "Non-stock",
            }]),
            num_rows="dynamic", use_container_width=True, key="create_order_lines",
            column_config={
                "product_sku": st.column_config.SelectboxColumn(
                    "Inventory product (optional)", options=product_options, required=True
                )
            },
        )
        submitted = st.form_submit_button("Save draft order", type="primary")
    if submitted:
        try:
            new_id = create_order(
                settings.database_url, order_number=number, customer_name=customer,
                customer_email=email, order_date=order_date, currency=currency,
                line_items=resolve_product_lines(lines),
            )
            st.success(f"Draft order #{new_id} saved.")
            st.rerun()
        except OrderServiceError as exc:
            st.error(str(exc))

st.divider()
st.subheader("Orders")
search = st.text_input("Search order number or customer")
status = st.selectbox("Filter by status", ["All statuses", *STATUSES])
with factory() as session:
    query = select(Order).join(Business).order_by(Order.created_at.desc())
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(Order.order_number.ilike(term), Order.customer_name.ilike(term))
        )
    if status != "All statuses":
        query = query.where(Order.status == status)
    orders = session.scalars(query.limit(250)).all()
    rows = [
        {
            "ID": item.id,
            "Order": item.order_number,
            "Customer": item.customer_name,
            "Date": item.order_date,
            "Status": item.status,
            "Total": f"{item.currency} {item.total:,.2f}",
        }
        for item in orders
    ]
if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
    order_id = st.selectbox("Manage order", [row["ID"] for row in rows])
    with factory() as session:
        order = session.get(Order, order_id)
        if order:
            st.write(
                f"**{order.order_number}** · {order.customer_name} · "
                f"{order.currency} {order.total:,.2f}"
            )
            if order.status == "Draft":
                with st.form(f"edit_order_{order.id}"):
                    edit_customer = st.text_input("Customer", value=order.customer_name)
                    edit_email = st.text_input(
                        "Customer email", value=order.customer_email or ""
                    )
                    edit_currency = st.text_input(
                        "Currency", value=order.currency, max_chars=3
                    )
                    frame = pd.DataFrame(
                        [
                            {
                                "description": line.description,
                                "quantity": float(line.quantity),
                                "unit_price": float(line.unit_price),
                                "product_sku": line.product.sku if line.product else "Non-stock",
                            }
                            for line in order.line_items
                        ]
                    )
                    edit_lines = st.data_editor(
                        frame, num_rows="dynamic", use_container_width=True,
                        column_config={
                            "product_sku": st.column_config.SelectboxColumn(
                                "Inventory product (optional)", options=product_options,
                                required=True,
                            )
                        },
                    )
                    edit = st.form_submit_button("Save draft changes")
                if edit:
                    try:
                        update_order(
                            settings.database_url, order.id,
                            customer_name=edit_customer, customer_email=edit_email,
                            currency=edit_currency,
                            line_items=resolve_product_lines(edit_lines),
                        )
                        st.success("Draft order updated.")
                        st.rerun()
                    except OrderServiceError as exc:
                        st.error(str(exc))
            allowed = {
                "Draft": ["Confirmed", "Cancelled"],
                "Confirmed": ["Processing", "Cancelled"],
                "Processing": ["Fulfilled", "Cancelled"],
                "Fulfilled": [],
                "Cancelled": [],
            }[order.status]
            if allowed:
                next_status = st.selectbox("Change status to", allowed)
                if st.button("Update order status"):
                    try:
                        change_order_status(settings.database_url, order.id, next_status)
                        st.success(f"Order status changed to {next_status}.")
                        st.rerun()
                    except OrderServiceError as exc:
                        st.error(str(exc))
            else:
                st.caption("This order is in a final status and cannot be changed.")
else:
    st.info("No orders match the current search and status filter.")
