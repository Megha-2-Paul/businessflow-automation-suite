"""Application page registration and navigation."""
from __future__ import annotations

import streamlit as st


def build_navigation():
    """Build the application navigation."""
    overview = st.Page(
        "ui/pages/overview.py", title="Overview",
        icon=":material/dashboard:", default=True,
    )
    data_workbench = st.Page(
        "ui/pages/data_workbench.py", title="Data Workbench",
        icon=":material/table_view:",
    )
    invoices = st.Page(
        "ui/pages/invoices.py", title="Invoices",
        icon=":material/receipt_long:",
    )
    orders = st.Page(
        "ui/pages/orders.py", title="Orders",
        icon=":material/shopping_cart:",
    )
    inventory = st.Page(
        "ui/pages/inventory.py", title="Inventory",
        icon=":material/inventory_2:",
    )
    reports = st.Page(
        "ui/pages/reports.py", title="Reports & Exports",
        icon=":material/analytics:",
    )
    history = st.Page(
        "ui/pages/history.py", title="Processing History",
        icon=":material/history:",
    )
    settings = st.Page(
        "ui/pages/settings.py", title="Settings",
        icon=":material/settings:",
    )
    return st.navigation(
        {
            "WORKSPACE": [overview, data_workbench, invoices, orders, inventory],
            "INSIGHTS": [reports, history],
            "APPLICATION": [settings],
        }
    )
