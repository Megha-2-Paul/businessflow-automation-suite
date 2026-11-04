"""Application page registration."""
import streamlit as st


def build_navigation():
    """Build the application navigation."""
    overview = st.Page(
        "ui/pages/overview.py",
        title="Overview",
        icon=":material/dashboard:",
        default=True,
    )
    data_workbench = st.Page(
        "ui/pages/data_workbench.py",
        title="Data Workbench",
        icon=":material/table_view:",
    )
    history = st.Page(
        "ui/pages/history.py",
        title="Processing History",
        icon=":material/history:",
    )
    settings = st.Page(
        "ui/pages/settings.py",
        title="Settings",
        icon=":material/settings:",
    )
    return st.navigation(
        {
            "Workspace": [overview, data_workbench, history],
            "Application": [settings],
        }
    )
