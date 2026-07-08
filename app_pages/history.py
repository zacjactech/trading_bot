"""
History page: read-only view of orders placed in this session, plus a manual
"open orders" lookup by symbol.

For full audit history across sessions, the logs/ directory is the source of
truth (logs/bot.log is rotated daily).
"""
import pandas as pd
import streamlit as st

from pages_lib._shared import (
    fmt_ts,
    format_error,
    get_exchange_symbols,
    get_open_orders,
    get_recent_orders,
    init_session_state,
)


def _format_history_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).copy()
    if "ts" in df.columns:
        df["Placed at"] = df["ts"].apply(fmt_ts)
        df = df.drop(columns=["ts"])
    rename = {
        "symbol": "Symbol",
        "side": "Side",
        "type": "Kind",
        "quantity": "Qty",
        "price": "Price",
        "stop_price": "Stop",
        "orderId": "Order ID",
        "status": "Status",
        "executedQty": "Filled",
    }
    df = df.rename(columns=rename)
    # Pretty status with badge-friendly text
    if "Status" in df.columns:
        df["Status"] = df["Status"].fillna("—").astype(str)
    return df


def render() -> None:
    init_session_state()

    st.title("History")
    st.caption("Orders placed from this session, and live open orders.")

    st.subheader("Open orders (live)")
    @st.fragment(run_every="15s")
    def _live_open_orders():
        symbols = get_exchange_symbols() or ["BTCUSDT", "ETHUSDT"]
        sym = st.selectbox("Filter by symbol", options=["(all)"] + symbols, label_visibility="collapsed")
        try:
            rows = get_open_orders(None if sym == "(all)" else sym)
        except Exception as e:
            st.error(format_error(e), icon=":material/cloud_off:")
            return
        if not rows:
            st.caption("No open orders.")
            return
        df = pd.DataFrame(rows)
        cols = [c for c in ("orderId", "symbol", "side", "type", "price", "origQty", "status", "updateTime") if c in df.columns]
        if "updateTime" in cols:
            df["updateTime"] = df["updateTime"].apply(fmt_ts)
        st.dataframe(df[cols], hide_index=True, width="stretch")
    _live_open_orders()

    st.space("medium")
    st.subheader("This session")
    rows = get_recent_orders()
    if not rows:
        st.caption("No orders placed yet from this session.")
        return
    df = _format_history_frame(rows)
    st.dataframe(df, hide_index=True, width="stretch")

    if st.button("Clear session history", width="content"):
        st.session_state["order_history"] = []
        st.rerun()
