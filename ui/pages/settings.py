"""Application configuration overview page."""
import streamlit as st

from config.settings import get_settings

settings = get_settings()
st.title("Settings")
st.caption("Current local application configuration.")
st.text_input("Application name", value=settings.app_name, disabled=True)
st.text_input("Environment", value=settings.environment, disabled=True)
database_label = (
    "SQLite" if settings.database_url.startswith("sqlite") else "Configured database"
)
st.text_input("Database", value=database_label, disabled=True)
st.text_input("Maximum upload size (MB)", value=str(settings.max_upload_mb), disabled=True)
st.caption(
    "Configuration is managed through environment variables; secrets are not displayed here."
)
