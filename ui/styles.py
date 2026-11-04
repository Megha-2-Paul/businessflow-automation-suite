"""Shared visual styling for the BusinessFlow interface."""
import streamlit as st


def apply_global_styles() -> None:
    """Apply the blue-and-white theme and consistent application spacing."""
    st.markdown(
        """
        <style>
        :root {
            --bf-navy: #142b45;
            --bf-blue: #1769c2;
            --bf-blue-dark: #1055a2;
            --bf-ink: #172b4d;
            --bf-muted: #66758a;
            --bf-border: #e2e8f0;
            --bf-surface: #ffffff;
            --bf-canvas: #f3f6fa;
        }
        .stApp { background: var(--bf-canvas); color: var(--bf-ink); }
        [data-testid="stSidebar"] { background: var(--bf-navy); }
        [data-testid="stSidebar"] * { color: #f8fafc; }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
            background: #203c5b;
        }
        .block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--bf-ink); letter-spacing: -0.025em; }
        h1 { font-weight: 700; }
        [data-testid="stCaptionContainer"] { color: var(--bf-muted); }
        div[data-testid="stMetric"] {
            background: var(--bf-surface);
            border: 1px solid var(--bf-border);
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(16, 36, 64, .04);
        }
        div[data-testid="stMetricLabel"] { color: var(--bf-muted); font-weight: 600; }
        div[data-testid="stMetricValue"] { color: var(--bf-ink); font-weight: 700; }
        div[data-testid="stDataFrame"], div[data-testid="stTable"] {
            border: 1px solid var(--bf-border);
            border-radius: 10px;
            overflow: hidden;
        }
        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: var(--bf-blue);
            border-color: var(--bf-blue);
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
            min-height: 2.55rem;
        }
        [data-testid="stExpander"] {
            background: var(--bf-surface);
            border: 1px solid var(--bf-border);
            border-radius: 10px;
        }
        [data-testid="stAlert"] { border-radius: 10px; }
        hr { border-color: var(--bf-border); }
        .bf-muted { color: var(--bf-muted); }
        </style>
        """,
        unsafe_allow_html=True,
    )
