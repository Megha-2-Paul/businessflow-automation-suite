"""Product catalogue, stock movements and physical stocktake workflows."""
import streamlit as st
from sqlalchemy import select

from config.settings import get_settings
from database.models import InventoryCount, InventoryCountLine
from database.session import get_session_factory
from services.inventory_service import (
    InventoryServiceError,
    adjust_stock,
    create_product,
    create_stocktake,
    list_movements,
    list_products,
    reconcile_stocktake,
    update_product,
)

settings = get_settings()
factory = get_session_factory(settings.database_url)
st.title("Inventory management")
st.caption("Maintain your product catalogue, record stock movements and reconcile physical counts.")

products = list_products(settings.database_url)
active_products = [item for item in products if item.is_active]
low_stock = [item for item in active_products if item.stock_on_hand <= item.reorder_level]
col1, col2, col3 = st.columns(3)
col1.metric("Active products", len(active_products))
col2.metric("Low stock", len(low_stock))
col3.metric("Inactive products", len(products) - len(active_products))
if low_stock:
    st.warning("Reorder level reached: " + ", ".join(
        f"{item.sku} ({item.stock_on_hand} {item.unit})" for item in low_stock
    ))

tab_products, tab_movements, tab_stocktake = st.tabs(
    ["Products", "Stock movements", "Stocktake"]
)
with tab_products:
    with st.expander("Add product", expanded=not products):
        with st.form("add_inventory_product"):
            sku = st.text_input("SKU")
            name = st.text_input("Product name")
            unit = st.text_input("Unit", value="unit")
            reorder = st.number_input("Reorder level", min_value=0.0, step=1.0, format="%.3f")
            opening = st.number_input("Opening stock", min_value=0.0, step=1.0, format="%.3f")
            add_product = st.form_submit_button("Add product", type="primary")
        if add_product:
            try:
                create_product(
                    settings.database_url, sku=sku, name=name, unit=unit,
                    reorder_level=reorder, opening_stock=opening,
                )
                st.success("Product added.")
                st.rerun()
            except InventoryServiceError as exc:
                st.error(str(exc))
    if products:
        st.dataframe(
            [{
                "SKU": item.sku, "Product": item.name, "On hand": item.stock_on_hand,
                "Unit": item.unit, "Reorder at": item.reorder_level,
                "Status": "Active" if item.is_active else "Inactive",
            } for item in products],
            use_container_width=True, hide_index=True,
        )
        selected = st.selectbox(
            "Edit product", products, format_func=lambda item: f"{item.sku} — {item.name}"
        )
        with st.form("edit_inventory_product"):
            edit_name = st.text_input("Name", value=selected.name)
            edit_unit = st.text_input("Unit", value=selected.unit)
            edit_reorder = st.number_input(
                "Reorder level", min_value=0.0, value=float(selected.reorder_level),
                step=1.0, format="%.3f",
            )
            edit_active = st.checkbox("Active", value=selected.is_active)
            save_product = st.form_submit_button("Save product")
        if save_product:
            try:
                update_product(
                    settings.database_url, selected.id, name=edit_name, unit=edit_unit,
                    reorder_level=edit_reorder, is_active=edit_active,
                )
                st.success("Product updated.")
                st.rerun()
            except InventoryServiceError as exc:
                st.error(str(exc))
    else:
        st.info("No products yet. Add a product to start recording real stock.")
    if active_products:
        st.subheader("Record a stock movement")
        with st.form("stock_movement_form"):
            movement_product = st.selectbox(
                "Product", active_products,
                format_func=lambda item: f"{item.sku} — {item.name}",
            )
            movement_type = st.selectbox(
                "Movement", ["receipt", "issue", "adjustment"],
                format_func=lambda value: {
                    "receipt": "Stock received", "issue": "Stock issued",
                    "adjustment": "Positive adjustment",
                }[value],
            )
            movement_quantity = st.number_input(
                "Quantity", min_value=0.001, step=1.0, format="%.3f"
            )
            reference = st.text_input("Reference (optional)")
            notes = st.text_area("Notes (optional)")
            save_movement = st.form_submit_button("Record movement")
        if save_movement:
            try:
                adjust_stock(
                    settings.database_url, movement_product.id,
                    movement_type=movement_type, quantity=movement_quantity,
                    reference=reference, notes=notes,
                )
                st.success("Stock movement recorded.")
                st.rerun()
            except InventoryServiceError as exc:
                st.error(str(exc))

with tab_movements:
    movements = list_movements(settings.database_url)
    if movements:
        st.dataframe(
            [{
                "Date (UTC)": item.created_at.strftime("%Y-%m-%d %H:%M"),
                "SKU": item.product.sku, "Type": item.movement_type.replace("_", " ").title(),
                "Change": item.quantity_delta, "Balance": item.quantity_after,
                "Reference": item.reference or "",
            } for item in movements],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No stock movements have been recorded.")

with tab_stocktake:
    if active_products:
        st.caption("Enter physical counts. Differences are reviewed before any stock is changed.")
        with st.form("create_stocktake_form"):
            count_rows = []
            for product in active_products:
                counted = st.number_input(
                    f"{product.sku} — {product.name} (recorded: {product.stock_on_hand})",
                    min_value=0.0, value=float(product.stock_on_hand),
                    step=1.0, format="%.3f", key=f"count_{product.id}",
                )
                count_rows.append({"product_id": product.id, "counted_quantity": counted})
            count_notes = st.text_input("Stocktake notes (optional)")
            save_count = st.form_submit_button("Save counts for review")
        if save_count:
            try:
                count_id = create_stocktake(
                    settings.database_url, counts=count_rows, notes=count_notes
                )
                st.success(f"Stocktake #{count_id} saved. Review its variances below.")
                st.rerun()
            except InventoryServiceError as exc:
                st.error(str(exc))
    with factory() as session:
        drafts = session.scalars(
            select(InventoryCount).where(InventoryCount.status == "draft")
            .order_by(InventoryCount.created_at.desc())
        ).all()
        if drafts:
            count = st.selectbox(
                "Stocktake awaiting reconciliation", drafts,
                format_func=lambda item: f"#{item.id} · {item.created_at:%Y-%m-%d %H:%M}",
            )
            lines = session.scalars(select(InventoryCountLine).where(
                InventoryCountLine.inventory_count_id == count.id
            )).all()
            st.dataframe(
                [{
                    "Product": line.product.sku, "Recorded": line.recorded_quantity,
                    "Physical count": line.counted_quantity,
                    "Difference": line.counted_quantity - line.recorded_quantity,
                } for line in lines],
                use_container_width=True, hide_index=True,
            )
            confirmed = st.checkbox(
                f"I reviewed the differences in stocktake #{count.id} and confirm reconciliation.",
                key=f"confirm_count_{count.id}",
            )
            if st.button("Apply stocktake adjustments", disabled=not confirmed):
                try:
                    reconcile_stocktake(settings.database_url, count.id)
                    st.success("Stocktake reconciled and ledger updated.")
                    st.rerun()
                except InventoryServiceError as exc:
                    st.error(str(exc))
        else:
            st.info("There are no stocktakes awaiting reconciliation.")
