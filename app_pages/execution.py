"""
Execution page: place MARKET / LIMIT / STOP_LIMIT orders.

Features:
- Symbol picker (with current price preview, auto-refreshing)
- Order type segmented control
- Mobile-first form: full-width inputs, BUY/SELL as a segmented control
- Live validation; errors surface above the form
- Confirmation toast on success; optimistic fail-fast on errors
"""
import time

import streamlit as st

from pages_lib._shared import (
    Config,
    format_error,
    get_exchange_symbols,
    get_live_price,
    get_min_notional,
    get_order_manager,
    init_session_state,
    record_order,
    ValidationError,
    APIError,
    NetworkError,
)


def _render_order_preview(symbol: str, side: str, order_type: str, qty: str, price: str, stop: str) -> None:
    """Small confirmation panel above the submit button."""
    rows = [("Symbol", symbol), ("Side", side), ("Type", order_type), ("Quantity", qty)]
    if order_type in ("LIMIT", "STOP_LIMIT"):
        rows.append(("Limit price", price))
    if order_type in ("STOP_LIMIT",):
        rows.append(("Stop trigger", stop))
    st.dataframe(
        {k: v for k, v in rows},
        hide_index=True,
        width="stretch",
    )


def _submit_order(symbol, side, order_type, qty, price=None, stop_price=None):
    mgr = get_order_manager()
    if order_type == "MARKET":
        return mgr.place_market_order(symbol, side, qty)
    if order_type == "LIMIT":
        return mgr.place_limit_order(symbol, side, qty, price)
    if order_type == "STOP_LIMIT":
        return mgr.place_stop_limit_order(symbol, side, qty, price, stop_price)
    raise ValidationError(f"Unsupported order type: {order_type}")


def render() -> None:
    init_session_state()

    st.title("Execution")
    st.caption("Place orders on Binance Futures Testnet.")

    # Configuration banner — shown but does NOT halt rendering.
    # Submission below is blocked separately when keys are missing.
    keys_missing = not Config.is_configured() and not Config.MOCK_TRADING
    if keys_missing:
        st.warning(
            "API keys not configured. Add `BINANCE_API_KEY` and "
            "`BINANCE_API_SECRET` to your `.env` file, or set "
            "`MOCK_TRADING=true` for offline paper trading. "
            "You can still preview the form below.",
            icon=":material/info:",
        )

    # ── Symbol + price preview — fragment, fetches symbols independently ─
    @st.fragment(run_every="10s")
    def _symbol_picker():
        symbols = get_exchange_symbols()
        if not symbols:
            symbols = ["BTCUSDT"]

        with st.container(border=True):
            st.markdown("**Symbol**")
            cols = st.columns([2, 1], gap="small", vertical_alignment="center")
            with cols[0]:
                symbol = st.selectbox(
                    "Symbol",
                    options=symbols,
                    index=symbols.index(st.session_state["selected_symbol"])
                    if st.session_state["selected_symbol"] in symbols
                    else 0,
                    label_visibility="collapsed",
                )
                st.session_state["selected_symbol"] = symbol
            with cols[1]:
                p = get_live_price(symbol)
                if p is not None:
                    st.metric("Price", f"${p:,.2f}", label_visibility="collapsed")
                else:
                    st.caption("—")

    _symbol_picker()
    st.space("small")

    # ── Order form — fragment so get_live_price doesn't block page ─────
    @st.fragment
    def _order_form():
        symbol = st.session_state.get("selected_symbol", "BTCUSDT")

        with st.form("order_form", clear_on_submit=False, border=False):
            st.markdown("**Order type**")
            order_type = st.segmented_control(
                "Order type",
                options=["MARKET", "LIMIT", "STOP_LIMIT"],
                default="MARKET",
                label_visibility="collapsed",
            )

            st.space("small")

            st.markdown("**Side**")
            side = st.segmented_control(
                "Side",
                options=["BUY", "SELL"],
                default="BUY",
                label_visibility="collapsed",
            )

            st.space("small")

            st.markdown("**Quantity**")
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=0.001,
                step=0.001,
                format="%.6f",
                label_visibility="collapsed",
            )

            # Price / stop appear contextually
            price: float | None = None
            stop_price: float | None = None
            if order_type in ("LIMIT", "STOP_LIMIT"):
                st.markdown("**Limit price**")
                price = st.number_input(
                    "Limit price",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                )
            if order_type == "STOP_LIMIT":
                st.markdown("**Stop trigger**")
                stop_price = st.number_input(
                    "Stop trigger",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                )

            st.space("medium")

            # Compute live context for preview & warnings
            live_px = get_live_price(symbol)

            # Soft warning when limit price is far from market
            if order_type == "LIMIT" and price and live_px:
                diff_pct = abs(price - live_px) / live_px * 100
                if diff_pct > 5:
                    st.caption(
                        f":material/warning: Limit price is {diff_pct:.1f}% away from market "
                        f"(${live_px:,.2f}). Will likely sit open."
                    )

            # Notional check — warn if order value is below symbol's minimum
            eff_price = price if order_type in ("LIMIT", "STOP_LIMIT") else live_px
            min_not = get_min_notional(symbol)
            if quantity and eff_price and quantity * eff_price < min_not:
                notional = quantity * eff_price
                st.warning(
                    f":material/warning: Order value is **${notional:,.2f}** — below the ${min_not:,.0f} minimum for {symbol}. "
                    f"Increase quantity to at least **{min_not / eff_price:.4g}**.",
                )

            # Preview block
            with st.expander("Preview", expanded=False):
                _render_order_preview(
                    symbol,
                    side or "BUY",
                    order_type or "MARKET",
                    f"{quantity:g}",
                    f"{price:,.2f}" if price else "—",
                    f"{stop_price:,.2f}" if stop_price else "—",
                )

            submit_label = f"{side or 'BUY'} {order_type or 'MARKET'} · {symbol}"
            submitted = st.form_submit_button(
                submit_label,
                type="primary",
                width="stretch",
                disabled=keys_missing,
            )

        # ── Submission handling (inside fragment) ───────────────────────
        if submitted:
            if not side or not order_type:
                st.error("Please choose a side and order type.", icon=":material/error:")
                return

            if keys_missing:
                st.error(
                    "Cannot place orders: API keys are not configured.",
                    icon=":material/lock:",
                )
                return

            try:
                if order_type != "MARKET" and (price is None or price <= 0):
                    raise ValidationError("Limit price required.")
                if order_type == "STOP_LIMIT" and (stop_price is None or stop_price <= 0):
                    raise ValidationError("Stop trigger price required.")
                if quantity <= 0:
                    raise ValidationError("Quantity must be greater than zero.")
                eff_px = price if order_type in ("LIMIT", "STOP_LIMIT") else live_px
                min_not = get_min_notional(symbol)
                if eff_px and quantity * eff_px < min_not:
                    min_qty = min_not / eff_px
                    raise ValidationError(
                        f"Order value ${quantity * eff_px:,.2f} is below the ${min_not:,.0f} minimum for {symbol}. "
                        f"Raise quantity to at least {min_qty:.4g}."
                    )
            except ValidationError as e:
                st.error(str(e), icon=":material/error:")
                return

            try:
                with st.spinner(f"Placing {order_type} order…", show_time=False):
                    result = _submit_order(symbol, side, order_type, quantity, price, stop_price)
                record_order({
                    "ts": time.time(),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price,
                    "stop_price": stop_price,
                    "orderId": result.get("orderId"),
                    "status": result.get("status", "UNKNOWN"),
                    "executedQty": result.get("executedQty", "0"),
                })
                st.toast(
                    f"Order #{result.get('orderId', '?')} {result.get('status', 'placed')}",
                    icon=":material/check_circle:",
                )
                st.success(
                    f"**{side} {order_type}** placed. "
                    f"ID `{result.get('orderId', '?')}` · "
                    f"status `{result.get('status', '—')}`.",
                    icon=":material/check_circle:",
                )
            except ValidationError as e:
                st.error(format_error(e), icon=":material/error:")
            except APIError as e:
                st.error(format_error(e), icon=":material/error:")
            except NetworkError as e:
                st.error(format_error(e), icon=":material/cloud_off:")
            except Exception as e:
                st.error(format_error(e), icon=":material/error:")

    _order_form()
