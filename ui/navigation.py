"""Application page registration."""
from __future__ import annotations

import streamlit as st


def build_navigation():
    """Build the application navigation."""
    overview = st.Page(
        "ui/pages/overview.py", title="Overview", icon=":material/dashboard:", default=True
    )
    data_workbench = st.Page(
        "ui/pages/data_workbench.py", title="Data Workbench", icon=":material/table_view:"
    )
    orders = st.Page(
        "ui/pages/orders.py", title="Order Management", icon=":material/shopping_cart:"
    )
    invoices = st.Page(
        "ui/pages/invoices.py", title="Invoice Processing", icon=":material/receipt_long:"
    )
    history = st.Page(
        "ui/pages/history.py", title="Processing History", icon=":material/history:"
    )
    settings = st.Page(
        "ui/pages/settings.py", title="Settings", icon=":material/settings:"
    )
    return st.navigation(
        {"Workspace": [overview, data_workbench, invoices, orders, history], "Application": [settings]}
    )
