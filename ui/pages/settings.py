"""Application configuration and workspace information."""
import streamlit as st

from config.settings import get_settings
from ui.workspace import get_database_url

settings = get_settings()
demo_mode = st.session_state.get("bf_workspace_mode") == "Demo"
st.title("Settings")
st.caption("Application configuration and current workspace details.")

left, right = st.columns(2)
with left:
    st.text_input("Application name", value=settings.app_name, disabled=True)
    st.text_input("Environment", value=settings.environment, disabled=True)
with right:
    database_url = get_database_url(settings.database_url)
    database_label = (
        "SQLite" if database_url.startswith("sqlite") else "Configured database"
    )
    st.text_input("Database", value=database_label, disabled=True)
    st.text_input(
        "Maximum upload size (MB)", value=str(settings.max_upload_mb), disabled=True
    )

st.subheader("Selected workspace")
if demo_mode:
    st.info(
        "Demo workspace is active. Fictional sample records are stored in a "
        "separate local SQLite database and do not modify live business data."
    )
else:
    st.success("Live workspace is active. Changes are saved to the configured business database.")

st.caption(
    "Configuration is managed through environment variables; secrets are not "
    "displayed in this application."
)
