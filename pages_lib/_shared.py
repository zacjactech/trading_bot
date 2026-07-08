"""
Shared helpers for the Streamlit web UI.

Importable from any page file. Centralizes:
- Cached data loaders (balances, prices, symbols)
- API client singleton
- Order history persistence (session-state-backed)
- Connection probe
"""
import hashlib
import sys
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

# Make the `bot/` package importable when run from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.client import BinanceFuturesClient  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.exceptions import APIError, NetworkError  # noqa: E402
from bot.orders import OrderManager  # noqa: E402
from bot.validators import ValidationError  # noqa: E402

__all__ = [
    "Config",
    "BinanceFuturesClient",
    "OrderManager",
    "ValidationError",
    "APIError",
    "NetworkError",
    "init_session_state",
    "get_client",
    "get_order_manager",
    "probe_connection",
    "get_live_price",
    "get_account_balance",
    "get_exchange_symbols",
    "get_min_notional",
    "render_status_badge",
    "format_money",
    "record_order",
    "get_recent_orders",
    "fmt_ts",
    "format_error",
]


# ── Session-state initialization ─────────────────────────────────────
def init_session_state() -> None:
    """Set up per-user session state. Idempotent."""
    st.session_state.setdefault("order_history", [])  # type: list[dict[str, Any]]
    st.session_state.setdefault("selected_symbol", "BTCUSDT")
    st.session_state.setdefault("fav_symbols", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])


# ── Cached resource (singleton client per browser session) ────────────
@st.cache_resource(show_spinner=False)
def get_client() -> BinanceFuturesClient:
    return BinanceFuturesClient()


def get_order_manager() -> OrderManager:
    return OrderManager(client=get_client())


# ── Lightweight cached data loaders ──────────────────────────────────
@st.cache_data(ttl=5, show_spinner=False)
def get_live_price(symbol: str) -> float | None:
    try:
        return get_client().get_symbol_price(symbol)
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def get_exchange_symbols() -> list[str]:
    try:
        info = get_client().get_exchange_info()
        return sorted(
            s["symbol"]
            for s in info.get("symbols", [])
            if s.get("contractType") == "PERPETUAL" and s["symbol"].endswith("USDT")
        )
    except Exception:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


@st.cache_data(ttl=60, show_spinner=False)
def get_min_notional(symbol: str) -> float:
    """Return the minimum notional (order value) for a symbol from exchange info."""
    try:
        info = get_client().get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                for f in s.get("filters", []):
                    if f["filterType"] == "MIN_NOTIONAL":
                        return float(f.get("notional", 5.0))
    except Exception:
        pass
    return 5.0


@st.cache_data(ttl=8, show_spinner=False)
def get_account_balance() -> list[dict]:
    return get_client().get_account_balance()


@st.cache_data(ttl=10, show_spinner=False)
def get_open_orders(symbol: str | None = None) -> list[dict]:
    data = get_client().get_open_orders(symbol)
    return data if isinstance(data, list) else data.get("orders", []) if isinstance(data, dict) else []


@st.cache_data(ttl=30, show_spinner=False)
def probe_connection() -> tuple[bool, str]:
    """Return (connected, server_time_str). Cached for 30s to avoid blocking every page load."""
    try:
        c = get_client()
        c.ping()
        ts = c.get_server_time().get("serverTime", 0)
        if ts:
            t = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%H:%M:%S UTC")
            return True, t
        return True, "—"
    except Exception:
        return False, "offline"


# ── UI helpers ───────────────────────────────────────────────────────
def render_status_badge() -> None:
    """Single-row connection status badge for the sidebar footer."""
    if Config.MOCK_TRADING:
        st.markdown(":orange-badge[Mock mode · paper trading]")
        return
    ok, server_t = probe_connection()
    if ok and Config.is_configured():
        st.markdown(f":green-badge[Live testnet · {server_t}]")
    elif Config.is_configured():
        st.markdown(":red-badge[Testnet unreachable]")
    else:
        st.markdown(":gray-badge[API keys missing]")


def format_money(value: float, decimals: int = 2) -> str:
    return f"${value:,.{decimals}f}"


def fmt_ts(ms: int | float | None) -> str:
    if not ms:
        return "—"
    try:
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "—"


# ── Error formatting ─────────────────────────────────────────────────
_API_ERROR_MAP: dict[int, str] = {
    -1000: "Unknown error — try again.",
    -1001: "Internal server error — Binance is having issues.",
    -1002: "Request rejected — you may be accessing the API too fast.",
    -1003: "Too many requests — slow down.",
    -1013: "Request weight too high — reduce request frequency.",
    -1015: "Too many orders — wait for existing orders to fill.",
    -1016: "Service unavailable — Binance is under maintenance.",
    -1100: "Illegal characters in the request.",
    -1101: "Too many parameters.",
    -1102: "Mandatory parameter missing.",
    -1103: "Unknown parameter.",
    -1104: "Not all sent parameters were read.",
    -1105: "Empty parameter.",
    -1106: "Parameter was expected to be sent but was not.",
    -1111: "Precision exceeds the maximum allowed for this asset. Reduce decimal places.",
    -1112: "No depth for this price level.",
    -1113: "Withdrawal amount is less than the minimum.",
    -1114: "TimeInForce parameter was unexpected.",
    -1115: "Invalid stopPrice time in force.",
    -1116: "Invalid order type.",
    -1117: "Invalid side.",
    -1118: "Invalid new order response type.",
    -1119: "Invalid quantity.",
    -1120: "Invalid price.",
    -1121: "Invalid stopPrice.",
    -1122: "Invalid iceberg quantity.",
    -1123: "Invalid order book type.",
    -1124: "Invalid data type for this request.",
    -1125: "Invalid timestamp.",
    -1126: "Invalid parameter.",
    -1127: "Query window too large.",
    -1128: "Invalid depth.",
    -1130: "Invalid data sent.",
    -2010: "Order rejected — check balance, quantity, or price.",
    -2011: "Unknown order — it may have already been filled or cancelled.",
    -2013: "Order does not exist.",
    -2014: "Invalid API key, IP, or permissions.",
    -2015: "Invalid API-key, IP, or permissions for action.",
    -2016: "No trading window — too many open orders.",
    -2018: "Balance insufficient — add funds or reduce quantity.",
    -2019: "Margin insufficient.",
    -4000: "Invalid contract type.",
    -4001: "Invalid side for this symbol.",
    -4003: "Invalid quantity.",
    -4004: "Invalid price.",
    -4005: "Invalid new order resp type.",
    -4006: "Invalid depth limit.",
    -4007: "Invalid symbol.",
    -4008: "Invalid listen key.",
    -4009: "Invalid limit.",
    -4010: "Invalid time range.",
    -4011: "Invalid interval.",
    -4012: "Invalid parameter.",
    -4013: "Invalid data type.",
    -4014: "Invalid rate limit.",
    -4015: "Invalid issue time.",
    -4016: "Invalid issue time range.",
    -4017: "Invalid issue time.",
    -4018: "Invalid asset.",
    -4019: "Invalid product type.",
    -4020: "Invalid data type.",
    -4021: "Invalid start time.",
    -4022: "Invalid end time.",
    -4023: "Invalid time range.",
    -4024: "Invalid interval.",
    -4025: "Invalid limit.",
    -4026: "Invalid data type.",
    -4027: "Invalid rate limit.",
    -4028: "Invalid symbol.",
    -4029: "Invalid margin asset.",
    -4030: "Invalid pair.",
    -4031: "Invalid transaction type.",
    -4032: "Invalid amount.",
    -4033: "Invalid account type.",
    -4034: "Invalid asset.",
    -4035: "Invalid position side.",
    -4036: "Invalid leverage.",
    -4037: "Invalid notional limit.",
    -4038: "Invalid margin type.",
    -4039: "Invalid amount.",
    -4040: "Invalid period.",
    -4041: "Invalid symbol.",
    -4042: "Invalid symbol.",
    -4043: "Invalid pair.",
    -4044: "Invalid data.",
    -4045: "Invalid type.",
    -4046: "Invalid side.",
    -4047: "Invalid position side.",
    -4048: "Invalid time.",
    -4049: "Invalid interval.",
    -4050: "Invalid limit.",
    -4051: "Invalid period.",
    -4052: "Invalid amount.",
    -4053: "Invalid asset.",
    -4054: "Invalid transaction type.",
    -4055: "Invalid account type.",
    -4056: "Invalid margin type.",
    -4057: "Invalid leverage.",
    -4058: "Invalid notional limit.",
    -4059: "Invalid side.",
    -4060: "Invalid position side.",
    -4061: "Invalid amount.",
    -4062: "Invalid period.",
    -4063: "Invalid symbol.",
    -4064: "Invalid pair.",
    -4065: "Invalid data.",
    -4066: "Invalid type.",
    -4067: "Invalid side.",
    -4068: "Invalid position side.",
    -4069: "Invalid time.",
    -4070: "Invalid interval.",
    -4071: "Invalid limit.",
    -4072: "Invalid period.",
    -4073: "Invalid amount.",
    -4074: "Invalid asset.",
    -4075: "Invalid transaction type.",
    -4076: "Invalid account type.",
    -4077: "Invalid margin type.",
    -4078: "Invalid leverage.",
    -4079: "Invalid notional limit.",
}


def format_error(exc: Exception) -> str:
    """Return a user-friendly error message for any exception type."""
    if isinstance(exc, APIError):
        code = exc.code if isinstance(exc.code, int) else int(exc.code) if str(exc.code).lstrip('-').isdigit() else 0
        hint = _API_ERROR_MAP.get(code)
        if hint:
            return f"**{exc.message}** — {hint}"
        return f"**Exchange error `{exc.code}`**: {exc.message}"
    if isinstance(exc, NetworkError):
        return (
            "Could not reach the exchange. Check your internet connection, "
            "VPN, or DNS settings. You can also enable `MOCK_TRADING=true` "
            "in `.env` for offline paper trading."
        )
    if isinstance(exc, ValidationError):
        return str(exc)
    msg = str(exc).strip()
    if not msg:
        return "An unexpected error occurred. Please try again."
    if len(msg) > 200:
        msg = msg[:200] + "…"
    return f"Unexpected error: {msg}"


# ── Order history (session-only) ──────────────────────────────────────
def record_order(entry: dict[str, Any]) -> None:
    """Append an order to session-state history (newest first, max 100)."""
    history: list[dict[str, Any]] = st.session_state.setdefault("order_history", [])
    history.insert(0, entry)
    st.session_state["order_history"] = history[:100]


def get_recent_orders() -> list[dict[str, Any]]:
    return st.session_state.get("order_history", [])
