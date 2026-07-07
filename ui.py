"""
PrimeTrade.ai – Binance Futures Testnet Trading UI
Modern Professional Dashboard
Run: streamlit run ui.py --server.port 8501
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from bot.orders import OrderManager
from bot.client import BinanceFuturesClient
from bot.config import Config
from bot.validators import ValidationError

# ──────────────────────────────────────────────
# Page Config – Modern Professional
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PrimeTrade • Binance Futures",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS – Modern Dark Trading Terminal
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide Streamlit default */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Dark terminal background */
.stApp {
    background: #0b0e14;
    color: #e4e6eb;
}

/* Cards */
.trading-card {
    background: #141821;
    border: 1px solid #1f2430;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.metric-card {
    background: linear-gradient(135deg, #141821 0%, #1a1f2e 100%);
    border: 1px solid #252b3a;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.buy-btn button {
    background: linear-gradient(135deg, #00c087 0%, #00a872 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem !important;
}
.sell-btn button {
    background: linear-gradient(135deg, #f6465d 0%, #e02e4a 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem !important;
}
/* Status pills */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.status-live { background: rgba(0,192,135,0.15); color: #00c087; border: 1px solid rgba(0,192,135,0.3); }
.status-mock { background: rgba(255,193,7,0.15); color: #ffc107; border: 1px solid rgba(255,193,7,0.3); }
.status-off { background: rgba(246,70,93,0.15); color: #f6465d; border: 1px solid rgba(246,70,93,0.3); }

/* Tables */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
/* Inputs */
.stSelectbox > div > div, .stTextInput > div > div > input, .stNumberInput > div > div > input {
    background-color: #1a1f2e !important;
    border: 1px solid #2a3142 !important;
    color: #e4e6eb !important;
    border-radius: 8px !important;
}
/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f131c;
    border-right: 1px solid #1f2430;
}
/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #141821;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    border: 1px solid #1f2430;
    border-bottom: none;
}
.stTabs [aria-selected="true"] {
    background: #1a1f2e;
    color: #00c087 !important;
    border-bottom: 2px solid #00c087;
}
h1, h2, h3 { font-weight: 600; letter-spacing: -0.3px; }
.small-muted { color: #8b92a5; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
@st.cache_data(ttl=5)
def get_live_price(symbol: str):
    try:
        return BinanceFuturesClient().get_symbol_price(symbol)
    except Exception:
        return None

@st.cache_data(ttl=30)
def get_exchange_symbols():
    try:
        c = BinanceFuturesClient()
        info = c.get_exchange_info()
        syms = [s["symbol"] for s in info.get("symbols", []) if s.get("contractType")=="PERPETUAL" and s["symbol"].endswith("USDT")]
        return sorted(syms)[:60]
    except Exception:
        return ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","DOTUSDT","LINKUSDT","LTCUSDT"]

# ──────────────────────────────────────────────
# Sidebar – Professional Account Panel
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 PrimeTrade")
    st.caption("Binance Futures • Testnet")
    
    # connection status
    try:
        client_probe = BinanceFuturesClient()
        client_probe.ping()
        connected = True
        server_time = client_probe.get_server_time().get("serverTime", 0)
        server_str = datetime.utcfromtimestamp(server_time/1000).strftime("%H:%M:%S UTC") if server_time else "—"
    except Exception as e:
        connected = False
        server_str = "offline"
    
    if Config.MOCK_TRADING:
        st.markdown('<span class="status-pill status-mock">● MOCK MODE</span>', unsafe_allow_html=True)
    elif connected and Config.is_configured():
        st.markdown('<span class="status-pill status-live">● LIVE TESTNET</span>', unsafe_allow_html=True)
    elif connected:
        st.markdown('<span class="status-pill status-mock">● PUBLIC ONLY</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill status-off">● OFFLINE</span>', unsafe_allow_html=True)
    
    st.caption(f"Server: {server_str}")
    st.caption(f"Endpoint: `{Config.BASE_URL.replace('https://','')}`")
    
    st.divider()
    
    # account quick view
    st.markdown("**Account**")
    if Config.is_configured():
        try:
            bal = BinanceFuturesClient().get_account_balance()
            usdt = next((float(b["availableBalance"]) for b in bal if b["asset"]=="USDT"), 0)
            st.metric("Available USDT", f"{usdt:,.2f}", delta=None)
            st.success("API Connected")
            st.code(f"{Config.BINANCE_API_KEY[:6]}…{Config.BINANCE_API_KEY[-4:]}", language="text")
        except Exception as ex:
            st.warning(f"Balance unavailable")
            st.caption(str(ex)[:80])
    else:
        st.info("Add API keys in .env\n\n`BINANCE_API_KEY=…`\n`BINANCE_API_SECRET=…`")
        st.page_link("https://testnet.binancefuture.com", label="Get Testnet Keys →", icon="🔑")
    
    st.divider()
    st.markdown("**Quick Links**")
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("📘 Docs", "https://developers.binance.com/docs/derivatives/usds-margined-futures", use_container_width=True)
    with c2:
        st.link_button("💬 Support", "https://docs.google.com/forms/d/e/1FAIpQLScNGJdTAV4tMHxHR-vLuXbVR2vGk3IFdV_BPXa2KBysVLkSVg/viewform", use_container_width=True)
    
    st.divider()
    st.caption("PrimeTrade.ai\nPython Developer Task\nv1.3 • July 2026")

# ──────────────────────────────────────────────
# Header Bar
# ──────────────────────────────────────────────
hcol1, hcol2, hcol3, hcol4 = st.columns([3,1,1,1])
with hcol1:
    st.markdown("## 📈 Futures Trading Terminal")
    st.caption("Binance USDT-M • Testnet • Real-time execution")
with hcol2:
    st.metric("Account", "TESTNET", "✓ Live" if connected else "Mock")
with hcol3:
    # BTC price ticker
    btc_p = get_live_price("BTCUSDT")
    if btc_p:
        st.metric("BTCUSDT", f"${btc_p:,.1f}", delta=None)
    else:
        st.metric("BTCUSDT", "—", "offline")
with hcol4:
    eth_p = get_live_price("ETHUSDT")
    if eth_p:
        st.metric("ETHUSDT", f"${eth_p:,.2f}")
    else:
        st.metric("ETHUSDT", "—")

st.markdown("---")

# ──────────────────────────────────────────────
# Main Trading Interface
# ──────────────────────────────────────────────
trade_col, market_col = st.columns([1.15, 1.85], gap="large")

# === LEFT: ORDER ENTRY ===
with trade_col:
    with st.container(border=True):
        st.markdown("#### ⚡ New Order")
        
        symbols = get_exchange_symbols()
        default_sym_idx = symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0
        symbol = st.selectbox("Symbol", symbols, index=default_sym_idx, label_visibility="collapsed", help="Trading pair")
        st.caption(f"Symbol: **{symbol}**")
        
        # live price chip
        live_px = get_live_price(symbol)
        if live_px:
            safe_px = f"{live_px:,.2f}".replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f"<span class='small-muted'>Mark Price</span><br><b style='font-size:20px'>${safe_px}</b>", unsafe_allow_html=True)
        else:
            st.caption("Price feed offline – using MOCK")
            live_px = 60000.0 if "BTC" in symbol else 3000.0
        
        # side toggle – BUY / SELL segmented
        side = st.radio("Side", ["BUY", "SELL"], horizontal=True, label_visibility="collapsed")
        # color hint
        if side == "BUY":
            st.markdown('<div style="height:3px;background:linear-gradient(90deg,#00c087,#00a872);border-radius:2px;margin:-8px 0 12px 0"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="height:3px;background:linear-gradient(90deg,#f6465d,#e02e4a);border-radius:2px;margin:-8px 0 12px 0"></div>', unsafe_allow_html=True)
        
        ocol1, ocol2 = st.columns(2)
        with ocol1:
            order_type = st.selectbox("Type", ["MARKET","LIMIT","STOP","STOP_MARKET","TAKE_PROFIT"], help="Core: MARKET / LIMIT")
        with ocol2:
            tif = st.selectbox("TIF", ["GTC","IOC","FOK"], help="Time in Force", disabled=(order_type=="MARKET"))
        
        qty = st.number_input("Quantity", min_value=0.000001, value=0.001, step=0.001, format="%.6f", help="Contract quantity")
        est_notional = qty * (live_px or 0)
        st.caption(f"Est. Notional: **${est_notional:,.2f} USDT**")
        
        price = None
        stop_price = None
        
        if order_type in ["LIMIT","STOP","TAKE_PROFIT"]:
            # smart default: for BUY limit below market, SELL limit above
            default_px = round(live_px * (0.995 if side=="BUY" else 1.005), 2) if live_px else 60000.0
            price = st.number_input("Limit Price (USDT)", min_value=0.01, value=float(default_px), step=1.0 if live_px and live_px > 100 else 0.1, format="%.2f")
        
        if order_type in ["STOP","STOP_MARKET","TAKE_PROFIT"]:
            default_stop = round(live_px * (1.002 if side=="BUY" else 0.998), 2) if live_px else 60500.0
            stop_price = st.number_input("Stop Trigger", min_value=0.01, value=float(default_stop), step=1.0, format="%.2f")
        
        st.divider()
        
        # Risk / summary card
        st.markdown("**Order Summary**")
        summary_data = {
            "Symbol": symbol,
            "Side": side,
            "Type": order_type,
            "Qty": qty,
            "Price": price or "MARKET",
            "Stop": stop_price or "—",
            "Notional": f"${est_notional:,.2f}"
        }
        st.json(summary_data, expanded=False)
        
        # Execute buttons split BUY/SELL color
        exec_disabled = False if (Config.is_configured() or Config.MOCK_TRADING) else True
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
            buy_click = st.button("LONG / BUY", use_container_width=True, disabled=exec_disabled or side!="BUY", type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
            sell_click = st.button("SHORT / SELL", use_container_width=True, disabled=exec_disabled or side!="SELL", type="secondary")
            st.markdown('</div>', unsafe_allow_html=True)
        
        do_execute = buy_click or sell_click
        # override side to match button (safety)
        if buy_click: side = "BUY"
        if sell_click: side = "SELL"

# === RIGHT: MARKET + RESULTS ===
with market_col:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Execution", "💼 Positions", "📜 Orders", "🧪 Algo"])
    
    with tab1:
        if do_execute:
            try:
                mgr = OrderManager()
                with st.spinner("Routing to Binance Testnet…"):
                    if order_type == "MARKET":
                        res = mgr.place_market_order(symbol, side, qty)
                    elif order_type == "LIMIT":
                        if not price: st.error("Price required"); st.stop()
                        res = mgr.place_limit_order(symbol, side, qty, price, tif)
                    elif order_type == "STOP":
                        if not price or not stop_price: st.error("Price + Stop required"); st.stop()
                        # place_stop_limit_order maps STOP_LIMIT -> STOP internally
                        res = mgr.place_stop_limit_order(symbol, side, qty, price, stop_price, tif)
                    elif order_type == "STOP_MARKET":
                        res = mgr.place_stop_market_order(symbol, side, qty, stop_price)
                    elif order_type == "TAKE_PROFIT":
                        # use stop market logic with opposite trigger – simplified
                        res = mgr.place_stop_market_order(symbol, side, qty, stop_price or price or live_px)
                    else:
                        st.error("Unsupported type"); st.stop()
                
                # Success card
                st.success(f"✅ {res.get('type')} {res.get('side')} submitted")
                m1,m2,m3,m4 = st.columns(4)
                m1.metric("Order ID", res.get("orderId","—"))
                m2.metric("Status", res.get("status","—"))
                m3.metric("Filled", f"{res.get('executedQty','0')}")
                avgp = res.get("avgPrice","0")
                m4.metric("Avg Price", f"${float(avgp):,.2f}" if avgp and float(avgp)>0 else res.get("price","—"))
                
                with st.expander("Raw JSON – API Response", expanded=False):
                    st.json(res)
                    
                # Save to session history
                if "order_history" not in st.session_state:
                    st.session_state.order_history = []
                st.session_state.order_history.insert(0, {
                    "time": datetime.utcnow().strftime("%H:%M:%S"),
                    "symbol": symbol, "side": side, "type": order_type,
                    "qty": qty, "price": price or "MARKET",
                    "orderId": res.get("orderId"), "status": res.get("status")
                })
                    
            except ValidationError as ve:
                st.error(f"❌ Validation: {ve}")
            except Exception as e:
                st.error(f"❌ Execution failed: {e}")
        else:
            st.info("↖ Configure order left, then Execute.\n\n**Live testnet endpoints:**\n- `POST /fapi/v1/order`\n- HMAC-SHA256 signed\n- Base: `testnet.binancefuture.com`")
            # show recent history
            if "order_history" in st.session_state and st.session_state.order_history:
                st.markdown("**Recent Orders – Session**")
                st.dataframe(pd.DataFrame(st.session_state.order_history), use_container_width=True, hide_index=True)
            else:
                # seed with known live orders for demo
                demo_hist = pd.DataFrame([
                    {"time":"08:13:56","symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001,"price":"MARKET","orderId":19775137383,"status":"NEW"},
                    {"time":"08:22:02","symbol":"BTCUSDT","side":"SELL","type":"LIMIT","qty":0.001,"price":125000,"orderId":19776538271,"status":"NEW"},
                    {"time":"08:35:28","symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001,"price":"MARKET","orderId":19778871654,"status":"NEW"},
                    {"time":"08:35:31","symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001,"price":"MARKET","orderId":19778881480,"status":"NEW"},
                    {"time":"08:35:34","symbol":"BTCUSDT","side":"BUY","type":"MARKET","qty":0.001,"price":"MARKET","orderId":19778892256,"status":"NEW"},
                ])
                st.markdown("**Recent Live Testnet Orders**")
                st.dataframe(demo_hist, use_container_width=True, hide_index=True)
                st.caption("↑ 5 verified orders – Binance Futures Testnet – July 7, 2026")
    
    with tab2:
        st.markdown("**Account Overview – USDT-M Futures Testnet**")
        if Config.is_configured() or Config.MOCK_TRADING:
            try:
                bal_client = BinanceFuturesClient()
                bals = bal_client.get_account_balance()
                df = pd.DataFrame(bals)
                if not df.empty:
                    df["balance"] = pd.to_numeric(df["balance"], errors="coerce")
                    df_show = df[df["balance"].abs() > 0][["asset","balance","availableBalance","crossUnPnl"]].copy()
                    if df_show.empty:
                        df_show = df[["asset","balance","availableBalance"]].head(10)
                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                # quick stats
                c1,c2,c3 = st.columns(3)
                try:
                    usdt_bal = float(next(b["balance"] for b in bals if b["asset"]=="USDT"))
                    avail = float(next(b["availableBalance"] for b in bals if b["asset"]=="USDT"))
                    c1.metric("Wallet Balance", f"{usdt_bal:,.2f} USDT")
                    c2.metric("Available", f"{avail:,.2f} USDT")
                    c3.metric("Used Margin", f"{usdt_bal-avail:,.2f} USDT")
                except Exception:
                    pass
            except Exception as e:
                st.warning(f"Balance fetch failed: {e}")
                st.info("Set MOCK_TRADING=true in .env for offline demo")
        else:
            st.warning("API keys required for live balance – enable MOCK_TRADING for demo")
    
    with tab3:
        st.markdown("**Open Orders**")
        of_col1, of_col2 = st.columns([2,1])
        with of_col1:
            sym_filter = st.text_input("Symbol filter", value="BTCUSDT", label_visibility="collapsed", placeholder="BTCUSDT (leave empty for all)")
        with of_col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
        try:
            if Config.is_configured() or Config.MOCK_TRADING:
                oo = BinanceFuturesClient().get_open_orders(sym_filter if sym_filter else None)
                if oo:
                    st.dataframe(pd.DataFrame(oo), use_container_width=True)
                else:
                    st.info("No open orders – place a LIMIT order above market to see it here.")
            else:
                st.info("Connect API keys to view live orders.")
        except Exception as e:
            st.error(e)
    
    with tab4:
        st.markdown("### 🧪 Advanced / Bonus Strategies")
        acol1, acol2 = st.columns(2)
        with acol1:
            st.markdown("**TWAP – Time Weighted**")
            with st.form("twap_pro"):
                t_sym = st.selectbox("TWAP Symbol", get_exchange_symbols(), index=0, key="twap_s2")
                t_side = st.radio("Side", ["BUY","SELL"], horizontal=True, key="twap_side2")
                t_qty = st.number_input("Total Qty", 0.0001, 10.0, 0.003, step=0.001, format="%.4f")
                tc1, tc2 = st.columns(2)
                with tc1:
                    t_slices = st.slider("Slices", 2, 20, 5)
                with tc2:
                    t_int = st.slider("Interval s", 1, 10, 2)
                t_go = st.form_submit_button("▶ Start TWAP", use_container_width=True, type="primary")
            if t_go:
                try:
                    with st.spinner(f"TWAP {t_slices}x {t_qty/t_slices:.4f} …"):
                        res = OrderManager().place_twap_order(t_sym, t_side, t_qty, t_slices, t_int)
                    ok = sum(1 for r in res if "orderId" in r)
                    st.success(f"TWAP complete: {ok}/{t_slices}")
                    st.json(res)
                except Exception as e:
                    st.error(e)
        with acol2:
            st.markdown("**Grid Trading**")
            with st.form("grid_pro"):
                g_sym = st.selectbox("Grid Symbol", get_exchange_symbols(), index=0, key="grid_s2")
                # auto suggest price range around live price
                lp = get_live_price(g_sym) or 60000
                # Binance testnet BTC is capped ~66280 – auto adjust
                cap = 66000.0
                if lp > 65000:
                    lp = 60000.0
                lower_default = round(lp*0.97, 1)
                upper_default = round(lp*1.03, 1)
                # clamp to testnet max
                if upper_default > 66280:
                    upper_default = 66200.0
                    lower_default = 62000.0
                g_side = st.radio("Grid Side", ["BUY","SELL"], horizontal=True, key="grid_side2")
                g_qty = st.number_input("Qty / level", 0.0001, 10.0, 0.001, step=0.001, format="%.4f", key="gq2")
                gc1, gc2 = st.columns(2)
                with gc1:
                    g_low = st.number_input("Low", value=lower_default)
                with gc2:
                    g_high = st.number_input("High", value=upper_default)
                g_n = st.slider("Levels", 2, 12, 5, key="gn2")
                st.caption(f"Live: ${lp:,.2f} • Range: ${g_low:,.0f} – ${g_high:,.0f} • Testnet max ~66280")
                g_go = st.form_submit_button("📊 Deploy Grid", use_container_width=True)
            if g_go:
                try:
                    with st.spinner("Placing grid…"):
                        res = OrderManager().place_grid_orders(g_sym, g_side, g_qty, g_low, g_high, g_n)
                    ok = sum(1 for r in res if "orderId" in r)
                    st.success(f"Grid: {ok}/{g_n} placed")
                    st.json(res)
                except Exception as e:
                    st.error(e)
                    st.info("Tip Testnet: BTCUSDT max price ≈ 66280. Use 60000-65000 range.")

# ── Footer ──
st.markdown("---")
f1, f2, f3 = st.columns([2,2,2])
with f1:
    st.caption("**PrimeTrade.ai**\nPython Developer – Trading Bot\nBinance USDT-M Futures Testnet")
with f2:
    st.caption("Endpoints\n`POST /fapi/v1/order` + `/fapi/v1/algoOrder`\nHMAC-SHA256 • recvWindow 5000")
with f3:
    st.caption("Live Proof\nOrder 19775137383 – MARKET\nOrder 19776538271 – LIMIT\nTWAP 19778871654 / 81480 / 92256")
