"""Shared light-and-minimal visual styling for BusinessFlow."""
import streamlit as st


def apply_global_styles() -> None:
    """Apply the Version 3 light workspace theme."""
    st.markdown(
        """
        <style>
        :root {
            --bf-green: #23845b; --bf-green-dark: #176744;
            --bf-green-soft: #e8f5ed; --bf-ink: #172b25;
            --bf-muted: #718078; --bf-border: #e5ebe6;
            --bf-surface: #ffffff; --bf-canvas: #f7f9f7;
        }
        .stApp { background: var(--bf-canvas); color: var(--bf-ink); }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--bf-border); }
        [data-testid="stSidebar"] * { color: #263b31; }
        [data-testid="stSidebar"] [aria-current="page"] {
            background: var(--bf-green-soft); color: var(--bf-green-dark);
            border-radius: 8px; font-weight: 700;
        }
        [data-testid="stSidebar"] a:hover, [data-testid="stSidebar"] button:hover {
            background: #f1f7f2; border-radius: 8px;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
            background: #f8fbf8;
        }
        .block-container { max-width: 1500px; padding-top: 1.8rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--bf-ink); letter-spacing: -.025em; }
        h1 { font-weight: 730; font-size: clamp(1.8rem, 3vw, 2.3rem); }
        h2 { font-size: 1.3rem; font-weight: 680; }
        h3 { font-size: 1.08rem; font-weight: 650; }
        [data-testid="stCaptionContainer"] { color: var(--bf-muted); }
        .bf-page-eyebrow { color: var(--bf-green); font-size: .7rem; font-weight: 800;
            letter-spacing: .13em; margin-bottom: -.55rem; }
        .bf-section-note { color: var(--bf-muted); font-size: .88rem; }
        div[data-testid="stMetric"] {
            background: var(--bf-surface); border: 1px solid var(--bf-border);
            border-radius: 13px; padding: 17px 18px;
            box-shadow: 0 2px 8px rgba(25, 55, 37, .035);
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p {
            color: #65746b !important; font-weight: 600;
        }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] div {
            color: var(--bf-ink) !important; font-weight: 730;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--bf-border); border-radius: 10px;
            overflow: hidden; background: #fff;
        }
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {
            border-color: #d5dfd7; border-radius: 8px;
        }
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] p { color: #34483c; }
        [data-testid="stTabs"] button[role="tab"] { color: #53665a !important; font-weight: 600; }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--bf-green-dark) !important;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--bf-green); border-color: var(--bf-green); color: #fff !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px; font-weight: 650; min-height: 2.5rem;
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--bf-green-dark); border-color: var(--bf-green-dark);
        }
        [data-testid="stForm"], [data-testid="stExpander"] {
            background: #fff; border: 1px solid var(--bf-border); border-radius: 12px;
        }
        [data-testid="stAlert"] { border-radius: 10px; }
        [data-testid="stAlert"] p { color: #31443a !important; }
        hr { border-color: var(--bf-border); }
        @media (max-width: 900px) {
            .block-container { padding-top: 1.1rem; }
            div[data-testid="stMetric"] { padding: 12px; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { transition-duration: .01ms !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
