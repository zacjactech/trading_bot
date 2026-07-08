"""
Algo page: TWAP (Time-Weighted Average Price) and Grid strategies.

Both strategies run synchronously inside a Streamlit fragment with a progress
indicator. For long-running TWAPs, use the CLI; this UI is meant as a quick
sandbox for low slice counts (<= 20).
"""
import time as time_mod

import streamlit as st

from pages_lib._shared import (
    Config,
    APIError,
    NetworkError,
    format_error,
    get_exchange_symbols,
    get_live_price,
    get_min_notional,
    get_order_manager,
    init_session_state,
    record_order,
)


def _render_twap() -> None:
    st.subheader("TWAP order")
    st.caption("Split a large order into N slices spaced over time. Useful for reducing market impact.")

    with st.form("twap_form", border=False):
        symbols = get_exchange_symbols() or ["BTCUSDT"]
        c1, c2 = st.columns(2, gap="small")
        with c1:
            symbol = st.selectbox("Symbol", options=symbols, label_visibility="visible", key="twap_sym")
        with c2:
            side = st.segmented_control("Side", options=["BUY", "SELL"], default="BUY", label_visibility="visible")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            total_qty = st.number_input("Total quantity", min_value=0.0, value=0.003, step=0.001, format="%.6f")
        with c2:
            order_type = st.segmented_control("Order type", options=["MARKET", "LIMIT"], default="MARKET", label_visibility="visible")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            slices = st.slider("Slices", min_value=1, max_value=20, value=3, step=1)
        with c2:
            interval_s = st.slider("Interval (s)", min_value=0, max_value=10, value=2, step=1)

        live_px = get_live_price(symbol) if order_type == "LIMIT" else None
        price: float | None = None
        if order_type == "LIMIT":
            default_price = float(live_px) if live_px else 0.0
            price = st.number_input("Limit price", min_value=0.0, value=default_price, step=0.01, format="%.2f")

        submitted = st.form_submit_button("Run TWAP", type="primary", width="stretch")

    if submitted:
        if not side:
            st.error("Choose a side.", icon=":material/error:")
            return
        if total_qty <= 0:
            st.error("Quantity must be > 0.", icon=":material/error:")
            return
        if order_type == "LIMIT" and (price is None or price <= 0):
            st.error("Limit price required.", icon=":material/error:")
            return

        # Notional check — each slice must meet symbol's minimum
        eff_price = price if order_type == "LIMIT" else get_live_price(symbol)
        slice_qty = round(total_qty / slices, 6)
        min_not = get_min_notional(symbol)
        if eff_price and slice_qty * eff_price < min_not:
            min_slice = min_not / eff_price
            st.error(
                f"Each slice (${slice_qty * eff_price:,.2f}) is below the ${min_not:,.0f} minimum for {symbol}. "
                f"Raise total quantity to at least **{min_slice * slices:.4g}**.",
                icon=":material/error:",
            )
            return

        mgr = get_order_manager()
        progress = st.progress(0.0, text="Starting…")
        statuses: list[dict] = []

        try:
            for i in range(slices):
                qty = slice_qty if i < slices - 1 else round(total_qty - slice_qty * (slices - 1), 6)
                progress.progress((i + 1) / slices, text=f"Slice {i + 1}/{slices} · {qty:g} {symbol}")
                if order_type == "MARKET":
                    res = mgr.place_market_order(symbol, side, qty)
                else:
                    res = mgr.place_limit_order(symbol, side, qty, price)
                statuses.append({"slice": i + 1, "qty": qty, **res})
                record_order({
                    "type": f"TWAP/{order_type}",
                    "ts": time_mod.time(),
                    "symbol": symbol,
                    "side": side,
                    "quantity": qty,
                    "price": price,
                    "orderId": res.get("orderId"),
                    "status": res.get("status", "—"),
                    "executedQty": res.get("executedQty", "0"),
                })
                if i < slices - 1 and interval_s > 0:
                    time_mod.sleep(interval_s)
            progress.empty()
            ok = sum(1 for s in statuses if "orderId" in s and not s.get("error"))
            st.toast(f"TWAP complete · {ok}/{slices} ok", icon=":material/check_circle:")
            st.success(f"TWAP finished: {ok}/{slices} slices succeeded.", icon=":material/check_circle:")
        except (APIError, NetworkError, ValueError) as e:
            progress.empty()
            st.error(format_error(e), icon=":material/error:")


def _render_grid() -> None:
    st.subheader("Grid order")
    st.caption("Place `grids` limit orders between `lower` and `upper` price levels.")

    with st.form("grid_form", border=False):
        symbols = get_exchange_symbols() or ["BTCUSDT"]
        c1, c2 = st.columns(2, gap="small")
        with c1:
            symbol = st.selectbox("Symbol", options=symbols, label_visibility="visible", key="grid_sym")
        with c2:
            side = st.segmented_control("Side", options=["BUY", "SELL"], default="BUY", label_visibility="visible")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            qty_per_grid = st.number_input("Qty per grid", min_value=0.0, value=0.001, step=0.001, format="%.6f")
        with c2:
            grids = st.slider("Grids", min_value=2, max_value=12, value=5, step=1)

        c1, c2 = st.columns(2, gap="small")
        with c1:
            lower = st.number_input("Lower price", min_value=0.0, value=60000.0, step=100.0, format="%.2f")
        with c2:
            upper = st.number_input("Upper price", min_value=0.0, value=65000.0, step=100.0, format="%.2f")

        submitted = st.form_submit_button("Place grid", type="primary", width="stretch")

    if submitted:
        if not side:
            st.error("Choose a side.", icon=":material/error:")
            return
        if lower >= upper:
            st.error("Lower must be strictly less than upper.", icon=":material/error:")
            return
        if qty_per_grid <= 0:
            st.error("Quantity must be > 0.", icon=":material/error:")
            return
        if lower <= 0 or upper <= 0:
            st.error("Prices must be > 0.", icon=":material/error:")
            return

        # Notional check — lowest grid level must meet symbol's minimum
        min_not = get_min_notional(symbol)
        if qty_per_grid * lower < min_not:
            min_qty = min_not / lower
            st.error(
                f"Lowest grid level (${qty_per_grid * lower:,.2f}) is below the ${min_not:,.0f} minimum for {symbol}. "
                f"Raise qty per grid to at least **{min_qty:.4g}**.",
                icon=":material/error:",
            )
            return

        mgr = get_order_manager()
        step = (upper - lower) / (grids - 1)
        try:
            results = []
            progress = st.progress(0.0, text="Placing grid…")
            for i in range(grids):
                p = round(lower + step * i, 2)
                res = mgr.place_limit_order(symbol, side, qty_per_grid, p)
                results.append((p, res))
                record_order({
                    "type": "GRID/LIMIT",
                    "ts": time_mod.time(),
                    "symbol": symbol,
                    "side": side,
                    "quantity": qty_per_grid,
                    "price": p,
                    "orderId": res.get("orderId"),
                    "status": res.get("status", "—"),
                    "executedQty": res.get("executedQty", "0"),
                })
                progress.progress((i + 1) / grids, text=f"Level {i + 1}/{grids} · @ {p:,.2f}")
            progress.empty()
            ok = sum(1 for _, r in results if r.get("orderId"))
            st.toast(f"Grid complete · {ok}/{grids} placed", icon=":material/check_circle:")
            st.success(f"Grid placed: {ok}/{grids} levels succeeded.", icon=":material/check_circle:")
        except (APIError, NetworkError, ValueError) as e:
            st.error(format_error(e), icon=":material/error:")


def render() -> None:
    init_session_state()

    if not Config.is_configured() and not Config.MOCK_TRADING:
        st.warning(
            "API keys not configured. Add keys to `.env` or set `MOCK_TRADING=true`.",
            icon=":material/info:",
        )

    st.title("Algo strategies")
    st.caption("TWAP and grid trading. For long-running orders, prefer the CLI.")

    tabs = st.tabs(["TWAP", "Grid"])

    # Each strategy renders in a fragment so get_exchange_symbols() doesn't block the page
    @st.fragment
    def _twap_tab():
        _render_twap()

    @st.fragment
    def _grid_tab():
        _render_grid()

    with tabs[0]:
        _twap_tab()
    with tabs[1]:
        _grid_tab()
