"""
PrimeTrade.ai – Dashboard
Run: streamlit run ui.py --server.port 8501
"""
import sys
import os
import pandas as pd
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from bot.orders import OrderManager
from bot.client import BinanceFuturesClient
from bot.config import Config
from bot.validators import ValidationError

# ─────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PrimeTrade Dashboard",
    page_icon=":material/space_dashboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS — Donezo-inspired Light Dashboard
# ─────────────────────────────────────────────────────────────
st.html("""
<style>
/* ── Google Fonts preload ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Main background styling */
.stApp {
    background-color: #F4F7F6;
}

/* Card styling overrides for a softer look */
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 16px !important;
    border: 1px solid #E5E7EB !important;
    background-color: #FFFFFF;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
    padding: 1rem;
}

/* ── Sidebar Menu Styling ── */
.sidebar-menu-category {
    font-size: 11px;
    font-weight: 600;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 24px;
    margin-bottom: 12px;
}
.sidebar-menu-item {
    padding: 10px 12px;
    border-radius: 8px;
    color: #4B5563;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 4px;
    cursor: pointer;
}
.sidebar-menu-item:hover {
    background-color: #F3F4F6;
}
.sidebar-menu-item.active {
    background-color: #ECFDF5;
    color: #1B5E20;
    font-weight: 600;
}

/* ── Status Card (Sidebar) ── */
.status-card {
    background: linear-gradient(135deg, #064E3B 0%, #065F46 100%);
    border-radius: 16px;
    padding: 20px;
    color: #FFFFFF;
    margin-top: 20px;
    text-align: left;
    box-shadow: 0 10px 15px -3px rgba(6, 78, 59, 0.3);
}
.status-card-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 4px;
}
.status-card-text {
    font-size: 12px;
    color: #A7F3D0;
    margin-bottom: 20px;
}
.status-card-btn {
    background: #10B981;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    color: white;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    width: 100%;
}

/* ── Primary KPI Card (Solid Green) ── */
.kpi-primary {
    background: linear-gradient(135deg, #1B5E20 0%, #15803D 100%);
    border-radius: 16px;
    padding: 20px;
    color: #FFFFFF;
    height: 100%;
    position: relative;
}
.kpi-primary .kpi-icon-top {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}
.kpi-primary .kpi-title {
    font-size: 15px;
    font-weight: 500;
    color: #E6F4EA;
}
.kpi-primary .kpi-value {
    font-size: 36px;
    font-weight: 700;
    margin: 12px 0;
    font-family: 'Inter', sans-serif;
}
.kpi-primary .kpi-trend {
    font-size: 12px;
    color: #86EFAC;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── Secondary KPI Cards (White) ── */
.kpi-secondary {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px;
    height: 100%;
    position: relative;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.kpi-secondary .kpi-icon-top {
    position: absolute;
    top: 20px;
    right: 20px;
    background: #F3F4F6;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    color: #4B5563;
}
.kpi-secondary .kpi-title {
    font-size: 15px;
    font-weight: 500;
    color: #1F2937;
}
.kpi-secondary .kpi-value {
    font-size: 36px;
    font-weight: 700;
    margin: 12px 0;
    color: #111827;
    font-family: 'Inter', sans-serif;
}
.kpi-secondary .kpi-trend {
    font-size: 12px;
    color: #9CA3AF;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── Form buttons ── */
.st-key-btn_buy button {
    background-color: #10B981 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.st-key-btn_sell button {
    background-color: #EF4444 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""")

# ─────────────────────────────────────────────────────────────
# Cached helpers
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def get_live_price(symbol: str) -> float | None:
    try:
        return BinanceFuturesClient().get_symbol_price(symbol)
    except Exception:
        return None

@st.cache_data(ttl=60)
def get_exchange_symbols() -> list[str]:
    try:
        info = BinanceFuturesClient().get_exchange_info()
        return sorted([
            s["symbol"] for s in info.get("symbols", [])
            if s.get("contractType") == "PERPETUAL" and s["symbol"].endswith("USDT")
        ])[:60]
    except Exception:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

@st.cache_data(ttl=10)
def get_account_balance() -> list[dict]:
    return BinanceFuturesClient().get_account_balance()

def _probe() -> tuple[bool, str]:
    try:
        c = BinanceFuturesClient()
        c.ping()
        ts = c.get_server_time().get("serverTime", 0)
        t = datetime.utcfromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else "—"
        return True, f"{t} UTC"
    except Exception:
        return False, "offline"

# ─────────────────────────────────────────────────────────────
# Bootstrap
# ─────────────────────────────────────────────────────────────
st.session_state.setdefault("order_history", [])
connected, server_time_str = _probe()

# ─────────────────────────────────────────────────────────────
# Sidebar (Navigation & Status)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🟢 PrimeTrade")
    
    # Styled Mock Navigation
    st.html("""
    <div class="sidebar-menu-category">MENU</div>
    <div class="sidebar-menu-item active">
        <span>📊</span> Dashboard
    </div>
    <div class="sidebar-menu-item">
        <span>⚡</span> Execution
    </div>
    <div class="sidebar-menu-item">
        <span>💼</span> Positions
    </div>
    <div class="sidebar-menu-item">
        <span>🤖</span> Algo Strategies
    </div>
    <div class="sidebar-menu-category">GENERAL</div>
    <div class="sidebar-menu-item">
        <span>⚙️</span> Settings
    </div>
    <div class="sidebar-menu-item">
        <span>❓</span> Help
    </div>
    """)
    
    st.space(120)
    
    # Status Card (like the "Download App" card in Donezo)
    if Config.MOCK_TRADING:
        status_title = "Mock Trading"
        status_text = "Paper trading active."
    elif connected and Config.is_configured():
        status_title = "Live Testnet"
        status_text = f"Connected • {server_time_str}"
    else:
        status_title = "Offline"
        status_text = "Check API keys."

    st.html(f"""
    <div class="status-card">
        <div class="status-card-title">{status_title}</div>
        <div class="status-card-text">{status_text}</div>
        <button class="status-card-btn">Manage Keys</button>
    </div>
    """)

# ─────────────────────────────────────────────────────────────
# Top Navigation Bar
# ─────────────────────────────────────────────────────────────
header_col1, header_col2 = st.columns([1, 1], vertical_alignment="center")
with header_col1:
    st.markdown("### Dashboard")
    st.caption("Plan, prioritize, and execute trades with ease.")
with header_col2:
    with st.container(horizontal_alignment="right"):
        c1, c2 = st.columns([1, 1], vertical_alignment="center")
        with c1:
            st.button("+ Add Order", type="primary", use_container_width=True)
        with c2:
            st.button("Import Data", use_container_width=True)

st.space("small")

# ─────────────────────────────────────────────────────────────
# KPI Cards Row (Donezo Style)
# ─────────────────────────────────────────────────────────────
wallet_bal = 0.0
avail_bal = 0.0
used_bal = 0.0
if Config.is_configured() or Config.MOCK_TRADING:
    try:
        bals = get_account_balance()
        usdt_row = next((b for b in bals if b["asset"] == "USDT"), None)
        if usdt_row:
            wallet_bal = float(usdt_row["balance"])
            avail_bal = float(usdt_row["availableBalance"])
            used_bal = wallet_bal - avail_bal
    except Exception:
        pass

kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.html(f"""
    <div class="kpi-primary">
        <div class="kpi-icon-top">↗</div>
        <div class="kpi-title">Wallet Balance</div>
        <div class="kpi-value">${wallet_bal:,.0f}</div>
        <div class="kpi-trend">📈 Increased from last week</div>
    </div>
    """)

with kpi_cols[1]:
    st.html(f"""
    <div class="kpi-secondary">
        <div class="kpi-icon-top">↗</div>
        <div class="kpi-title">Available Margin</div>
        <div class="kpi-value">${avail_bal:,.0f}</div>
        <div class="kpi-trend">☁️ Ready to deploy</div>
    </div>
    """)

with kpi_cols[2]:
    st.html(f"""
    <div class="kpi-secondary">
        <div class="kpi-icon-top">↗</div>
        <div class="kpi-title">Used Margin</div>
        <div class="kpi-value">${used_bal:,.0f}</div>
        <div class="kpi-trend">☁️ In active positions</div>
    </div>
    """)

with kpi_cols[3]:
    open_orders_cnt = 0
    try:
        if Config.is_configured():
            orders = BinanceFuturesClient().get_open_orders()
            open_orders_cnt = len(orders) if orders else 0
    except:
        pass
    st.html(f"""
    <div class="kpi-secondary">
        <div class="kpi-icon-top">↗</div>
        <div class="kpi-title">Open Orders</div>
        <div class="kpi-value">{open_orders_cnt}</div>
        <div class="kpi-trend">On Discuss</div>
    </div>
    """)

st.space("medium")

# ─────────────────────────────────────────────────────────────
# Main Content Grid (Row 1)
# ─────────────────────────────────────────────────────────────
r1_c1, r1_c2, r1_c3 = st.columns([2, 1, 1], gap="large")

with r1_c1:
    with st.container(border=True):
        st.subheader("Market Analytics")
        symbols = get_exchange_symbols()
        selected_symbol = st.selectbox("Symbol", symbols, index=symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0, label_visibility="collapsed")
        live_px = get_live_price(selected_symbol)
        display_px = live_px if live_px is not None else 60000.0
        
        # Fake chart data mapped to Donezo bar chart style
        chart_data = pd.DataFrame({"Volume": [40, 70, 45, 90, 30, 40, 50]})
        st.bar_chart(chart_data, y="Volume", height=150, color="#1B5E20")

with r1_c2:
    with st.container(border=True):
        st.subheader("Quick Execution")
        st.caption("Target: $64,200.00")
        
        st.button("Start Meeting", type="primary", use_container_width=True) # Matching "Start Meeting" button shape
        
        side = st.selectbox("Side", ["BUY", "SELL"], label_visibility="collapsed")
        qty = st.number_input("Qty", value=0.01)
        st.button("Submit Trade", use_container_width=True)

with r1_c3:
    with st.container(border=True):
        st.subheader("Watchlist")
        st.button("+ New")
        st.markdown("""
        - 🚀 **BTC/USDT**  
          <small style="color:gray;">Due date: Nov 26, 2024</small>
        - 🔹 **ETH/USDT**  
          <small style="color:gray;">Due date: Nov 29, 2024</small>
        - ☀️ **SOL/USDT**  
          <small style="color:gray;">Due date: Dec 5, 2024</small>
        """, unsafe_allow_html=True)

st.space("medium")

# ─────────────────────────────────────────────────────────────
# Main Content Grid (Row 2)
# ─────────────────────────────────────────────────────────────
r2_c1, r2_c2, r2_c3 = st.columns([2, 1, 1], gap="large")

with r2_c1:
    with st.container(border=True):
        st.subheader("Active Positions")
        st.button("+ Add Margin")
        st.markdown("""
        **Long BTC/USDT**  
        <small style="color:gray;">Working on GitHub Project Repository</small>  
        <span style="color:#10B981; background:#D1FAE5; padding:2px 6px; border-radius:4px; font-size:10px;">In Progress</span>
        """, unsafe_allow_html=True)

with r2_c2:
    with st.container(border=True):
        st.subheader("Margin Usage")
        # Fake donut chart representation
        st.html("""
        <div style="text-align:center; padding: 20px 0;">
            <div style="font-size:36px; font-weight:700; color:#111827;">41%</div>
            <div style="font-size:12px; color:#6B7280;">Margin Allocated</div>
        </div>
        """)

with r2_c3:
    with st.container(border=True):
        st.html("""
        <div style="background: linear-gradient(135deg, #064E3B 0%, #065F46 100%); border-radius:12px; padding:20px; color:white; text-align:center; height:100%;">
            <div style="font-size:14px; text-align:left; margin-bottom:10px;">Time Tracker</div>
            <div style="font-size:32px; font-family:'JetBrains Mono', monospace; font-weight:700; margin-bottom:20px;">01:24:08</div>
            <div style="display:flex; justify-content:center; gap:10px;">
                <button style="border-radius:50%; width:30px; height:30px; border:none; background:white; color:#064E3B; font-weight:bold;">⏸</button>
                <button style="border-radius:50%; width:30px; height:30px; border:none; background:#EF4444; color:white; font-weight:bold;">⏹</button>
            </div>
        </div>
        """)
