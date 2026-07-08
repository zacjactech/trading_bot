"""
Settings page: read-only inspection of the current environment.

Intentionally no secret editing — secrets belong in `.env` (and gitignored).
"""
import streamlit as st

from pages_lib._shared import Config, probe_connection, render_status_badge


def render() -> None:
    st.title("Settings")
    st.caption("Environment inspection. Editing requires .env on the server.")

    # ── Connection status — fragment so probe_connection doesn't block ─
    @st.fragment(run_every="30s")
    def _status_section():
        with st.container(border=True):
            render_status_badge()
            ok, server_t = probe_connection()
            cols = st.columns(2, gap="small")
            with cols[0]:
                st.markdown("**Mode**")
                st.code("MOCK" if Config.MOCK_TRADING else ("LIVE" if Config.is_configured() else "OFFLINE"))
            with cols[1]:
                st.markdown("**Server time**")
                st.code(server_t if ok else "—")

    _status_section()

    # ── Configuration — static, renders instantly ─────────────────────
    with st.container(border=True):
        st.markdown("**Configuration**")
        st.caption("Sensitive values are masked.")
        rows = [
            ("Base URL", Config.BASE_URL),
            ("API key", "***" if Config.BINANCE_API_KEY else "(missing)"),
            ("API secret", "***" if Config.BINANCE_API_SECRET else "(missing)"),
        ]
        for k, v in rows:
            c1, c2 = st.columns([1, 2], gap="small")
            with c1:
                st.markdown(k)
            with c2:
                st.code(v)

    with st.container(border=True):
        st.markdown("**Quick links**")
        st.link_button("Binance Testnet faucet", "https://testnet.binancefuture.com")
        st.link_button("Demo trading portal", "https://demo.binance.com")
