"""Workspace selection and isolated demonstration data."""

import streamlit as st
from sqlalchemy import select

from config.settings import PROJECT_ROOT
from database.demo_data import seed_demo_records
from database.models import Business
from database.session import get_session_factory, initialize_database


DEMO_DATABASE_URL = (
    f"sqlite:///{(PROJECT_ROOT / 'data' / 'businessflow-demo.db').as_posix()}"
)


def get_database_url(default_url: str) -> str:
    """Return the database selected for the current Streamlit session."""
    if st.session_state.get("bf_workspace_mode") == "Demo":
        return DEMO_DATABASE_URL
    return default_url


def configure_workspace(default_url: str) -> str:
    """Render the workspace selector and initialise the isolated demo database."""
    selected = st.sidebar.selectbox(
        "Workspace",
        ["Live workspace", "Demo workspace"],
        key="bf_workspace_selector",
        help="Demo data is stored in a separate local database and never changes live records.",
    )
    mode = "Demo" if selected == "Demo workspace" else "Live"
    st.session_state["bf_workspace_mode"] = mode
    if mode == "Demo":
        initialize_demo_workspace()
        st.sidebar.info("Demonstration data · isolated from live records")
        return DEMO_DATABASE_URL

    st.sidebar.caption("Live business data")
    return default_url


def initialize_demo_workspace(database_url: str = DEMO_DATABASE_URL) -> None:
    """Create and seed the demo workspace without modifying other businesses."""
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    should_seed = False

    with factory.begin() as session:
        business = session.scalar(
            select(Business).order_by(Business.id).limit(1)
        )
        if business is None:
            session.add(Business(name="Demo Business", currency="USD", timezone="UTC"))
            should_seed = True
        elif business.name == "Demo Business":
            should_seed = True

    if should_seed:
        seed_demo_records(database_url)
