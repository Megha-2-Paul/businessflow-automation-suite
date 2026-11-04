"""Shared light-and-minimal visual system for BusinessFlow."""
import streamlit as st


def apply_global_styles() -> None:
    """Apply the Version 3 light palette and consistent application styling."""
    st.markdown(
        """
        <style>
        :root {
            --bf-green: #258653;
            --bf-green-dark: #176b40;
            --bf-green-soft: #e8f5ec;
            --bf-ink: #17251e;
            --bf-muted: #68766f;
            --bf-border: #e4ebe6;
            --bf-surface: #ffffff;
            --bf-canvas: #f7faf8;
        }
        .stApp { background: var(--bf-canvas); color: var(--bf-ink); }
        [data-testid="stHeader"] { background: rgba(247, 250, 248, .94); }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--bf-border);
        }
        [data-testid="stSidebar"] * { color: #293a31; }
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
            border-color: #d7e4da;
        }
        .block-container { max-width: 1480px; padding-top: 1.5rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--bf-ink); letter-spacing: -.025em; }
        h1 { font-weight: 730; font-size: clamp(1.85rem, 3vw, 2.4rem); }
        h2 { font-weight: 680; font-size: 1.35rem; }
        h3 { font-weight: 650; font-size: 1.08rem; }
        [data-testid="stCaptionContainer"] { color: var(--bf-muted); }
        .bf-page-eyebrow {
            color: var(--bf-green-dark); font-size: .7rem; font-weight: 800;
            letter-spacing: .13em; margin-bottom: -.5rem;
        }
        .bf-section-note { color: var(--bf-muted); font-size: .88rem; }
        div[data-testid="stMetric"] {
            background: var(--bf-surface); border: 1px solid var(--bf-border);
            border-radius: 11px; padding: 15px 17px;
            box-shadow: 0 2px 8px rgba(24, 55, 35, .035);
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] label {
            color: #637269 !important; font-weight: 600;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] div {
            color: var(--bf-ink) !important; font-weight: 720;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--bf-border); border-radius: 9px;
            overflow: hidden; background: #ffffff;
        }
        [data-testid="stDataFrame"] [role="columnheader"] { font-weight: 700; }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTextArea"] textarea {
            border-color: #d3dfd6; border-radius: 8px;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--bf-green); box-shadow: 0 0 0 1px var(--bf-green);
        }
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stMarkdownContainer"] p { color: #35463c; }
        [data-testid="stTabs"] button[role="tab"] {
            color: #52645a !important; font-weight: 600;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--bf-green-dark) !important;
        }
        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: var(--bf-green); border-color: var(--bf-green);
            color: #ffffff !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px; font-weight: 650; min-height: 2.5rem;
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background: var(--bf-green-dark); border-color: var(--bf-green-dark);
        }
        [data-testid="stForm"] {
            background: #ffffff; border: 1px solid var(--bf-border);
            border-radius: 11px; padding: 1rem;
        }
        [data-testid="stExpander"] {
            background: #ffffff; border: 1px solid var(--bf-border); border-radius: 9px;
        }
        [data-testid="stAlert"] { border-radius: 9px; }
        [data-testid="stAlert"] p { color: #2e4135 !important; }
        hr { border-color: var(--bf-border); }
        .bf-muted { color: var(--bf-muted); }
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
