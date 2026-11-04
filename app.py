"""BusinessFlow Automation Suite application entry point."""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from database.session import initialize_database
from logging_config.setup import configure_logging
from ui.navigation import build_navigation
from ui.styles import apply_global_styles


def main() -> None:
    """Configure and run the Streamlit application."""
    settings = get_settings()
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    configure_logging(settings.log_level)
    initialize_database(settings.database_url)
    apply_global_styles()
    build_navigation().run()


if __name__ == "__main__":
    main()
