"""Shared visual styling for the Streamlit interface."""
import streamlit as st


def apply_global_styles() -> None:
    """Apply restrained BusinessFlow styling."""
    st.markdown(
        """
        <style>
        :root {
            --bf-navy: #142b45;
            --bf-teal: #0f9f91;
            --bf-muted: #667085;
        }
        .stApp { background: #f5f7fa; }
        [data-testid="stSidebar"] { background: var(--bf-navy); }
        [data-testid="stSidebar"] * { color: #f8fafc; }
        .block-container { padding-top: 1.8rem; padding-bottom: 2.5rem; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5eaf0;
            border-radius: 10px;
            padding: 14px 16px;
        }
        .bf-muted { color: var(--bf-muted); }
        </style>
        """,
        unsafe_allow_html=True,
    )
