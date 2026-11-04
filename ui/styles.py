"""Shared light-and-minimal visual theme for BusinessFlow."""
import streamlit as st


def apply_global_styles() -> None:
    """Apply the Version 3 light palette consistently across application pages."""
    st.markdown(
        """
        <style>
        :root {
            --bf-green: #24845a;
            --bf-green-dark: #176b47;
            --bf-green-soft: #e8f4ed;
            --bf-ink: #172b25;
            --bf-muted: #687a70;
            --bf-border: #e4ebe6;
            --bf-surface: #ffffff;
            --bf-canvas: #f7f9f7;
        }
        .stApp { background: var(--bf-canvas); color: var(--bf-ink); }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--bf-border);
        }
        [data-testid="stSidebar"] * { color: #263b31; }
        [data-testid="stSidebar"] [aria-current="page"] {
            background: var(--bf-green-soft);
            color: var(--bf-green-dark) !important;
            border-radius: 8px;
            font-weight: 700;
        }
        [data-testid="stSidebar"] a:hover,
        [data-testid="stSidebar"] button:hover {
            background: #f0f6f1;
            border-radius: 8px;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
            background: #ffffff;
        }
        .block-container { max-width: 1500px; padding-top: 1.7rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--bf-ink); letter-spacing: -0.025em; }
        h1 { font-weight: 740; font-size: clamp(1.8rem, 3vw, 2.35rem); }
        h2 { font-weight: 680; font-size: 1.35rem; }
        h3 { font-weight: 650; font-size: 1.08rem; }
        [data-testid="stCaptionContainer"] { color: var(--bf-muted); }
        .bf-page-eyebrow {
            color: var(--bf-green-dark); font-size: .7rem; font-weight: 800;
            letter-spacing: .13em; margin-bottom: -.5rem;
        }
        div[data-testid="stMetric"] {
            background: var(--bf-surface); border: 1px solid var(--bf-border);
            border-radius: 11px; padding: 15px 17px;
            box-shadow: 0 2px 8px rgba(30, 65, 45, .035);
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] label { color: #627369 !important; font-weight: 600; }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] div {
            color: var(--bf-ink) !important; font-weight: 720;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--bf-border); border-radius: 9px;
            overflow: hidden; background: var(--bf-surface);
        }
        [data-testid="stDataFrame"] [role="columnheader"] { font-weight: 700; }
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {
            border-color: #d5dfd8; border-radius: 8px;
        }
        [data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--bf-green); box-shadow: 0 0 0 1px var(--bf-green);
        }
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label, [data-testid="stMarkdownContainer"] p {
            color: #34483d;
        }
        [data-testid="stTabs"] button[role="tab"] { color: #53665b !important; font-weight: 600; }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--bf-green-dark) !important;
        }
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--bf-green); border-color: var(--bf-green); color: #fff !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px; font-weight: 650; min-height: 2.5rem;
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background: var(--bf-green-dark); border-color: var(--bf-green-dark);
        }
        [data-testid="stForm"], [data-testid="stExpander"] {
            background: var(--bf-surface); border: 1px solid var(--bf-border);
            border-radius: 11px;
        }
        [data-testid="stAlert"] { border-radius: 9px; }
        [data-testid="stAlert"] p { color: #34483d !important; }
        hr { border-color: var(--bf-border); }
        @media (max-width: 900px) {
            .block-container { padding-top: 1rem; }
            div[data-testid="stMetric"] { padding: 12px; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { transition-duration: .01ms !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
