"""Workspace selection and isolated demonstration data."""
from __future__ import annotations

import streamlit as st

from config.settings import PROJECT_ROOT
from database.demo_data import seed_demo_data

DEMO_DATABASE_URL = (
    f"sqlite:///{(PROJECT_ROOT / 'data' / 'businessflow-demo.db').as_posix()}"
)


def get_database_url(default_url: str) -> str:
    """Return the database selected for the current Streamlit session."""
    if st.session_state.get("bf_workspace_mode") == "Demo":
        return DEMO_DATABASE_URL
    return default_url


def configure_workspace(default_url: str) -> str:
    """Render the workspace selector and initialise isolated demo records."""
    selected = st.sidebar.selectbox(
        "Workspace",
        ["Live workspace", "Demo workspace"],
        key="bf_workspace_selector",
        help="Demo records are fictional and stored separately from live business data.",
    )
    mode = "Demo" if selected == "Demo workspace" else "Live"
    st.session_state["bf_workspace_mode"] = mode
    if mode == "Demo":
        seed_demo_data(DEMO_DATABASE_URL)
        st.sidebar.info("DEMO DATA · fictional records · isolated database")
        return DEMO_DATABASE_URL
    st.sidebar.caption("Live business data")
    return default_url


def initialize_demo_workspace(database_url: str = DEMO_DATABASE_URL) -> None:
    """Compatibility entry point for tests and scripts that seed demo records."""
    seed_demo_data(database_url)
