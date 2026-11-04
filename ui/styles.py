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
        [data-testid="stSidebar"] [aria-current="page"] {
            background: #24496d;
            border-radius: 8px;
            font-weight: 700;
        }
        [data-testid="stSidebar"] a:hover,
        [data-testid="stSidebar"] button:hover {
            background: #1e405f;
            border-radius: 8px;
        }
        .block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
        h1, h2, h3 { color: var(--bf-ink); letter-spacing: -0.025em; }
        h1 { font-weight: 750; font-size: clamp(1.8rem, 3vw, 2.35rem); }
        h2 { font-weight: 700; font-size: 1.35rem; }
        h3 { font-weight: 650; font-size: 1.1rem; }
        [data-testid="stCaptionContainer"] { color: var(--bf-muted); }
        .bf-page-eyebrow {
            color: var(--bf-blue-dark);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .12em;
            margin-bottom: -.55rem;
        }
        div[data-testid="stMetric"] {
            background: var(--bf-surface);
            border: 1px solid var(--bf-border);
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 2px 7px rgba(16, 36, 64, .055);
            transition: border-color .15s ease, box-shadow .15s ease;
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] p,
        div[data-testid="stMetricLabel"] label {
            color: #52637a !important;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] div {
            color: var(--bf-ink) !important;
            font-weight: 700;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--bf-border);
            border-radius: 10px;
            overflow: hidden;
            background: var(--bf-surface);
        }
        [data-testid="stDataFrame"] [role="columnheader"] { font-weight: 700; }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTextArea"] textarea {
            border-color: #cbd5e1;
            border-radius: 8px;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--bf-blue);
            box-shadow: 0 0 0 1px var(--bf-blue);
        }
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stMarkdownContainer"] p {
            color: #334155;
        }
        [data-testid="stTabs"] button[role="tab"] {
            color: #42536a !important;
            font-weight: 600;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: var(--bf-blue-dark) !important;
        }
        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: var(--bf-blue);
            border-color: var(--bf-blue);
            color: #ffffff !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 650;
            min-height: 2.55rem;
            transition: background-color .15s ease, border-color .15s ease;
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background: var(--bf-blue-dark);
            border-color: var(--bf-blue-dark);
        }
        [data-testid="stForm"] {
            background: var(--bf-surface);
            border: 1px solid var(--bf-border);
            border-radius: 12px;
            padding: 1rem;
        }
        [data-testid="stExpander"] {
            background: var(--bf-surface);
            border: 1px solid var(--bf-border);
            border-radius: 10px;
        }
        [data-testid="stAlert"] {
            border-radius: 10px;
        }
        [data-testid="stAlert"] p {
            color: #24364b !important;
        }
        hr { border-color: var(--bf-border); }
        .bf-muted { color: var(--bf-muted); }
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
