"""
Dashboard page: balances, watchlist, open orders, recent activity.

Mobile-first: KPI tiles stack on mobile (use 2 columns max via st.columns(2)
inside a st.fragment), watchlist is a bordered list, recent orders shown as a
compact dataframe above the fold.
"""
import pandas as pd
import streamlit as st

from pages_lib._shared import (
    Config,
    format_error,
    format_money,
    get_account_balance,
    get_exchange_symbols,
    get_live_price,
    get_open_orders,
    get_recent_orders,
    init_session_state,
    render_status_badge,
)


def _kpi_grid(wallet: float, available: float, used: float, open_count: int) -> None:
    """2x2 grid on mobile / tablet, single row on wide screens."""
    if open_count == 0:
        orders_label = "All filled"
    elif open_count == 1:
        orders_label = "1 working order"
    else:
        orders_label = f"{open_count} working orders"

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.metric("Wallet", format_money(wallet, 0))
        st.metric("Used", format_money(used, 0))
    with c2:
        st.metric("Available", format_money(available, 0))
        st.metric("Open orders", open_count, help=orders_label)
    return None


def _watchlist(symbols: list[str]) -> None:
    """Compact mobile-friendly watchlist. Tap-through to Execution page."""
    with st.container(border=True):
        st.markdown("**Watchlist**")
        st.caption("Pin pairs to monitor live price.")
        fav: list[str] = st.session_state.setdefault("fav_symbols", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

        # Add control
        col_add, col_btn = st.columns([3, 1], gap="small", vertical_alignment="center")
        with col_add:
            new_sym = st.selectbox(
                "Add symbol",
                options=symbols,
                index=0,
                label_visibility="collapsed",
                key="wl_picker",
            )
        with col_btn:
            if st.button("Add", width="stretch", key="wl_add"):
                if new_sym not in fav:
                    fav.append(new_sym)
                    st.session_state["fav_symbols"] = fav
                    st.rerun()

        st.space("small")

        @st.fragment(run_every="10s")
        def _rows():
            for sym in list(fav):
                cols = st.columns([3, 1], gap="small", vertical_alignment="center")
                with cols[0]:
                    st.markdown(f"**{sym}**")
                with cols[1]:
                    p = get_live_price(sym)
                    st.markdown(f"`{('${:,.2f}'.format(p)) if p else '—'}`")
        _rows()


def _open_orders(symbol: str | None) -> None:
    with st.container(border=True):
        st.markdown("**Open orders**")
        try:
            orders = get_open_orders(symbol)
        except Exception as e:
            st.error(format_error(e), icon=":material/cloud_off:")
            return

        if not orders:
            st.caption("No open orders.")
            return

        df = pd.DataFrame(orders)
        display_cols = [c for c in ("orderId", "symbol", "side", "type", "price", "origQty", "status") if c in df.columns]
        st.dataframe(df[display_cols], hide_index=True, width="stretch")


def _balance_summary() -> tuple[float, float, float]:
    """Returns (wallet, available, used) for USDT, defaults to 0."""
    wallet = available = used = 0.0
    if not (Config.is_configured() or Config.MOCK_TRADING):
        return wallet, available, used
    try:
        bals = get_account_balance()
        usdt = next((b for b in bals if b["asset"] == "USDT"), None)
        if usdt:
            wallet = float(usdt.get("balance", 0))
            available = float(usdt.get("availableBalance", 0))
            used = max(wallet - available, 0.0)
    except Exception:
        pass  # silently default to 0 — dashboard shows zeros instead of crashing
    return wallet, available, used


def render() -> None:
    init_session_state()

    # ── Header — renders instantly, no data fetch ──────────────────
    cols = st.columns([2, 1], gap="small", vertical_alignment="center")
    with cols[0]:
        st.title("Dashboard")
        st.caption("Live balances, watchlist, and recent activity.")
    with cols[1]:
        render_status_badge()

    st.space("small")

    # ── KPIs — fragment, fetches balance + open orders independently ─
    @st.fragment(run_every="10s")
    def _kpis():
        wallet, avail, used = _balance_summary()
        try:
            open_count = len(get_open_orders())
        except Exception:
            open_count = 0
        _kpi_grid(wallet, avail, used, open_count)

    _kpis()
    st.space("medium")

    # ── Open orders — fragment, fetches independently ──────────────
    @st.fragment(run_every="10s")
    def _open_orders_fragment():
        selected = st.session_state.get("selected_symbol", "BTCUSDT")
        _open_orders(selected)

    _open_orders_fragment()
    st.space("small")

    # ── Watchlist — fragment, fetches symbols + prices independently ─
    @st.fragment(run_every="10s")
    def _watchlist_fragment():
        symbols = get_exchange_symbols() or ["BTCUSDT", "ETHUSDT"]
        _watchlist(symbols)

    _watchlist_fragment()

    st.space("medium")

    # ── Recent orders — session-only, no API call, renders instantly ─
    with st.expander("Recent activity (this session)", expanded=False):
        rows = get_recent_orders()
        if not rows:
            st.caption("No orders placed yet from this session.")
        else:
            df = pd.DataFrame(rows[:10])
            display_cols = [c for c in ("ts", "symbol", "side", "type", "quantity", "price", "status", "orderId") if c in df.columns]
            st.dataframe(df[display_cols], hide_index=True, width="stretch")
