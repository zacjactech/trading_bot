"""
PrimeTrade Web UI — minimal, mobile-first Streamlit alternative to the CLI.

Run: streamlit run ui.py

Architecture
------------
This file is the *entrypoint*. It registers the page callables with
``st.navigation``. Each page lives in ``app_pages/<name>.py`` and exposes a
``render()`` function. Streamlit's multipage v2 API invokes those callables
directly (no file-path re-execution, no separate processes).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from app_pages.algo import render as render_algo
from app_pages.dashboard import render as render_dashboard
from app_pages.execution import render as render_execution
from app_pages.history import render as render_history
from app_pages.settings import render as render_settings
from pages_lib._shared import init_session_state

# Page config must come first — before any other st.* call.
st.set_page_config(
    page_title="PrimeTrade",
    page_icon=":material/candlestick_chart:",
    layout="centered",
    initial_sidebar_state="auto",
)

# Session-state bootstrap shared by all pages.
init_session_state()

# ── Donezo-style dashboard CSS ──────────────────────────────────────
st.html("""<style>
/* ── Global surfaces ────────────────────────────────────────────── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main .block-container {
    background: #F3F4F6;
}

/* ── Metric cards — white cards with subtle shadow ──────────────── */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 18px 22px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
[data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    color: #1A1D23 !important;
    font-weight: 700 !important;
    font-variant-numeric: tabular-nums;
}

/* ── Containers with borders — card panels ──────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* ── Sidebar ────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] {
    color: #374151;
}

/* ── Buttons — green primary ────────────────────────────────────── */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2D6A4F 0%, #40916C 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    border-radius: 10px !important;
    transition: box-shadow 0.2s ease, transform 0.1s ease;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(45, 106, 79, 0.3);
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active,
.stFormSubmitButton > button[kind="primary"]:active {
    transform: translateY(0);
}

/* Secondary / outline buttons */
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #374151 !important;
    border-radius: 10px !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #F9FAFB !important;
    border-color: #9CA3AF !important;
}

/* ── Selectbox, number input, text input ────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    color: #1A1D23 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2D6A4F !important;
    box-shadow: 0 0 0 2px rgba(45, 106, 79, 0.15) !important;
    background: #FFFFFF !important;
}

/* ── Slider ─────────────────────────────────────────────────────── */
.stSlider > div > div > div > div {
    background: #2D6A4F !important;
}

/* ── Tabs — green underline active ──────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 500;
    padding: 10px 16px;
}
.stTabs [aria-selected="true"] {
    color: #2D6A4F !important;
    border-bottom-color: #2D6A4F !important;
}

/* ── Segmented control ──────────────────────────────────────────── */
.stSegmentedControl [data-baseweb="tab"] {
    background: #F3F4F6 !important;
    border: 1px solid #E5E7EB !important;
    color: #6B7280 !important;
    font-weight: 500;
}
.stSegmentedControl [aria-selected="true"] {
    background: #2D6A4F !important;
    color: #fff !important;
    border-color: #2D6A4F !important;
}

/* ── Dataframes — clean table ───────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    overflow: hidden;
}

/* ── Expander ───────────────────────────────────────────────────── */
.stExpander {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* ── Progress bar ───────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #2D6A4F, #52B788) !important;
    border-radius: 6px;
}

/* ── Form ───────────────────────────────────────────────────────── */
.stForm {
    background: transparent;
}

/* ── Captions ───────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #6B7280 !important;
}

/* ── Scrollbar ──────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #D1D5DB;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #9CA3AF;
}

/* ── Callouts — soft tinted backgrounds ─────────────────────────── */
.stSuccess {
    background: #ECFDF5 !important;
    border: 1px solid #A7F3D0 !important;
}
.stError {
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
}
.stWarning {
    background: #FFFBEB !important;
    border: 1px solid #FDE68A !important;
}
.stInfo {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
}
</style>""")

# ── Page registry ────────────────────────────────────────────────────
pages = [
    st.Page(render_dashboard, title="Dashboard", icon=":material/dashboard:", url_path="app", default=True),
    st.Page(render_execution, title="Execution", icon=":material/bolt:", url_path="exec"),
    st.Page(render_algo, title="Algo", icon=":material/auto_graph:", url_path="algo"),
    st.Page(render_history, title="History", icon=":material/history:", url_path="hist"),
    st.Page(render_settings, title="Settings", icon=":material/settings:", url_path="settings"),
]

# Sidebar brand strip (small caption under the auto-generated nav).
with st.sidebar:
    st.caption("Testnet trading")

# Route to the selected page. This call must come last.
nav = st.navigation(pages, position="sidebar")
nav.run()
