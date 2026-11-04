"""Application page registration."""
import streamlit as st


def build_navigation():
    """Build the multipage navigation for the initial application shell."""
    overview = st.Page("ui/pages/overview.py", title="Overview", icon=":material/dashboard:", default=True)
    settings = st.Page("ui/pages/settings.py", title="Settings", icon=":material/settings:")
    return st.navigation({"Workspace": [overview], "Application": [settings]})
