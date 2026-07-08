# Binance Futures Testnet Trading Bot

**Python Developer Task – PrimeTrade.ai / Anything.ai**

A clean, production-ready Python trading bot for **Binance USDT-M Futures Testnet** with structured logging, robust validation, enhanced CLI, and a modern Streamlit web UI.

Testnet Base URL: `https://testnet.binancefuture.com`

---

## Features (Core Requirements)

- [x] **Python 3.x**
- [x] **Place MARKET and LIMIT orders** on Binance Futures Testnet (USDT-M)
- [x] **Support both BUY and SELL sides**
- [x] **CLI input validation** via Typer/Click:
  - `symbol` (e.g., BTCUSDT)
  - `side` (BUY/SELL)
  - `order_type` (MARKET/LIMIT)
  - `quantity`
  - `price` (required for LIMIT)
- [x] **Clear output:**
  - Order request summary
  - Order response details (orderId, status, executedQty, avgPrice)
  - Success/failure message
- [x] **Structured code:**
  - `bot/client.py` – Binance API wrapper (REST, HMAC-SHA256)
  - `bot/orders.py` – order placement logic
  - `bot/validators.py` – input validation
  - `cli.py` – CLI entry point
- [x] **Logging:** API requests, responses, errors → `logs/bot.log`
- [x] **Exception handling:** invalid input, API errors, network failures

---

## Bonus Features (ALL included)

### Order Types
- `STOP_LIMIT` – stop trigger + limit price
- `STOP_MARKET` – stop trigger at market price
- `TAKE_PROFIT` / `TAKE_PROFIT_MARKET` – profit-taking orders
- **TWAP** – Time-Weighted Average Price splitting
- **Grid Trading** – multiple limit orders across a price range

### Enhanced CLI UX
- Interactive menu (`python cli.py interactive`)
- Rich colored tables, prompts, validation messages
- Confirm dialogs, live price preview
- Typer + Rich

### Modern Streamlit Web UI
- **Donezo-style** light dashboard with green accents
- Live price ticker, order form, balance viewer
- TWAP & Grid strategy panels
- History page with session orders
- Settings page with connection status
- **Non-blocking fragments** — page skeleton renders instantly, data loads independently
- **Dynamic precision** — order qty/price truncated to symbol's `stepSize`/`tickSize` from exchange info
- **Smart min-notional** — minimum order value fetched per symbol ($5–$50) instead of hardcoded
- **User-friendly errors** — 60+ Binance error codes mapped to plain-English hints

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py           # Binance Futures REST client + precision truncation
│   ├── config.py           # .env config loader
│   ├── exceptions.py       # BotError, APIError, NetworkError hierarchy
│   ├── logging_config.py   # Structured logging
│   ├── orders.py           # OrderManager business logic
│   ├── types.py            # Type definitions
│   └── validators.py       # Input validation
├── app_pages/
│   ├── algo.py             # TWAP & Grid strategy UI
│   ├── dashboard.py        # Balances, watchlist, open orders
│   ├── execution.py        # Order form with live price
│   ├── history.py          # Session orders + live open orders
│   └── settings.py         # Environment inspection
├── pages_lib/
│   └── _shared.py          # Cached data loaders, error formatting, UI helpers
├── tests/
│   ├── conftest.py
│   ├── test_client.py      # 50 tests – client, precision, endpoint routing
│   ├── test_config.py      # 10 tests – config defaults, mock parsing
│   ├── test_orders.py      # 40 tests – order manager, TWAP, grid
│   └── test_validators.py  # 36 tests – symbol, side, quantity, price
├── cli.py                  # Typer CLI entry point
├── main.py                 # Quick-start entry
├── ui.py                   # Streamlit Web UI entry point
├── test_responsive.py      # Playwright responsive test
├── requirements.txt
├── setup.sh / setup.ps1 / setup.bat
├── .env.example
└── logs/
    └── bot.log             # Rotating log (5MB, 5 backups)
```

---

## Setup

### One-Click Setup (Recommended)

**Linux / macOS / WSL:**
```bash
git clone https://github.com/zacjactech/trading_bot.git
cd trading_bot
bash setup.sh
```

**Windows PowerShell:**
```powershell
.\setup.ps1
```

**Windows CMD (double-click):**
```
setup.bat
```

All setup scripts install dependencies and run a connectivity test. No orders are placed by default.

**To run demo orders after setup:**
```bash
bash setup.sh --demo        # Linux/Mac
.\setup.ps1 -Demo           # PowerShell
setup.bat --demo            # CMD
```

### Manual Setup

```bash
git clone https://github.com/zacjactech/trading_bot.git
cd trading_bot
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
```

### Get Binance Futures Testnet API Keys

1. Register: **https://testnet.binancefuture.com**
   - Login with GitHub / Google / Email
2. Top right → **API Key** → Generate
   - Label: `trading_bot_test`
   - Copy API Key + Secret
3. Fund your test account: **Wallet → Faucet** (gives 10,000+ USDT test funds)

### Configure `.env`

```bash
cp .env.example .env
# edit .env
```

```
BINANCE_API_KEY=abcd1234...
BINANCE_API_SECRET=xyz987...
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

### Test Connectivity

```bash
python cli.py test
```

Expected:
```
✓ Connected! Server time: 1783...
Base URL: https://testnet.binancefuture.com
```

---

## Usage

### CLI – Direct Arguments

**Market Order:**
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

**Limit Order:**
```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.002 --price 65000
```

**Stop-Limit:**
```bash
python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500
```

**TWAP:**
```bash
python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.005 --slices 5 --interval 2
```

**Grid:**
```bash
python cli.py grid --symbol BTCUSDT --side BUY --quantity 0.001 --lower 60000 --upper 65000 --grids 5
```

> Note: Binance Futures Testnet BTC price cap is around 66,280. Use 60,000–65,000 range on testnet.

**Check Balance:**
```bash
python cli.py balance
```

**Check Price:**
```bash
python cli.py price BTCUSDT
```

### CLI – Interactive Mode

```bash
python cli.py interactive
```

Enhanced menu with:
- Live price preview
- Input validation with friendly errors
- Confirm before execute
- Color output

### Streamlit Web UI

```bash
streamlit run ui.py
```

Open http://localhost:8501

**Pages:**
- **Dashboard** – balances, watchlist, open orders, recent activity
- **Execution** – order form with live price, validation, notional check
- **Algo** – TWAP and Grid strategy panels
- **History** – session orders + live open orders
- **Settings** – environment inspection, connection status

---

## Technical Details

### Order Precision

The bot automatically truncates order quantities and prices to match each symbol's allowed precision from Binance's exchange info:

| Symbol | Qty Precision | Price Precision | Min Notional |
|--------|--------------|-----------------|--------------|
| BTCUSDT | 4 decimals (step 0.0001) | 2 decimals (tick 0.10) | $50 |
| ETHUSDT | 3 decimals (step 0.001) | 2 decimals (tick 0.01) | $20 |
| SOLUSDT | 2 decimals (step 0.01) | 4 decimals (tick 0.01) | $5 |
| XRPUSDT | 1 decimal (step 0.1) | 4 decimals (tick 0.0001) | $5 |

This prevents the common `Binance API Error -1111: Precision is over the maximum` error.

### Min-Notional Enforcement

Each symbol has a minimum order value (notional). The bot enforces this before placing orders:
- BTCUSDT: $50 minimum
- ETHUSDT: $20 minimum
- Other USDT pairs: typically $5

The UI shows a warning when the order value is below the minimum and suggests the exact quantity needed.

### Error Handling

All errors are mapped to user-friendly messages:
- `APIError` – shows the Binance error message + a plain-English hint
- `NetworkError` – connection troubleshooting steps
- `ValidationError` – input-specific guidance
- `Exception` – truncated to 200 chars for readability

### Non-Blocking UI

All data fetches (prices, balances, orders, exchange info) run inside Streamlit fragments. The page skeleton renders instantly, and each section loads independently as API calls complete. No single slow API call blocks the entire page.

### API Configuration

- **Base URLs:** Auto-fallback tries 3 endpoints
  - `https://testnet.binancefuture.com`
  - `https://demo-fapi.binance.com`
  - `https://testnet.binance.vision`
- **Signing:** `timestamp + recvWindow=10000` → HMAC-SHA256
- **Mock mode:** `MOCK_TRADING=true` in `.env` for offline demo
- **Algo Orders:** Conditional orders use `/fapi/v1/algoOrder` with `algotype=conditional` + `triggerprice`

### Endpoints Used

- `POST /fapi/v1/order` – standard orders (MARKET, LIMIT)
- `POST /fapi/v1/algoOrder` – conditional orders (STOP, STOP_MARKET, TAKE_PROFIT)
- `GET /fapi/v1/ticker/price` – live prices
- `GET /fapi/v1/exchangeInfo` – symbol filters (precision, min-notional)
- `GET /fapi/v1/openOrders` – open orders
- `DELETE /fapi/v1/order` – cancel orders
- `GET /fapi/v2/balance` – account balance
- `GET /fapi/v1/ping` – connectivity test

---

## Test Suite

```bash
python -m pytest tests/ -v
```

136 tests covering:
- Client: signature generation, mock mode, endpoint routing, URL fallback, error handling
- Config: defaults, mock trading parsing, validation
- Orders: market, limit, stop-limit, TWAP, grid, edge cases
- Validators: symbol, side, order type, quantity, price, stop price

---

## Troubleshooting

### Can't reach testnet?

1. **VPN** – US / Singapore / EU – Binance Demo is geo-restricted in some regions
2. **Change DNS:**
   - Windows: Network → Adapter → IPv4 → 8.8.8.8 / 1.1.1.1 → `ipconfig /flushdns`
   - Linux: `sudo resolvectl dns eth0 8.8.8.8 1.1.1.1`
3. **Try mobile hotspot** – sometimes routes differently
4. **Try all 3 URLs** in browser:
   - https://testnet.binancefuture.com
   - https://demo.binance.com
   - https://www.binance.com/en/futures/mock-trading
5. **Mock mode** – set `MOCK_TRADING=true` in `.env`

### Precision errors?

The bot now auto-truncates to the correct precision. If you still see `-1111` errors, restart the Streamlit server to clear bytecode cache.

### Notional errors?

Each symbol has a different minimum order value ($5–$50). The bot enforces this automatically and shows a warning with the exact minimum quantity needed.

---

## Assumptions

- USDT-M Futures (not COIN-M)
- One-way position mode (default testnet)
- Testnet faucet funds used (no real money)
- Quantity precision auto-handled via exchange info filters
- TimeInForce default: GTC
- Mock mode available for regions where Binance testnet is geo-blocked

---

## Deliverables Checklist

- [x] Source code – structured, commented
- [x] README.md – setup + run examples
- [x] requirements.txt
- [x] Bonus: Stop-Limit, TWAP, Grid
- [x] Bonus: Enhanced CLI (Typer + Rich)
- [x] Bonus: Streamlit Web UI (Donezo-style theme)
- [x] Live testnet orders verified
- [x] Setup scripts (Linux, PowerShell, CMD)
- [x] Auto-fallback URLs + MOCK_TRADING mode
- [x] Dynamic precision truncation per symbol
- [x] Smart min-notional enforcement
- [x] User-friendly error messages (60+ Binance codes)
- [x] Non-blocking UI with fragments
- [x] 136 passing tests

---

## Author

Built for **PrimeTrade.ai / Anything.ai – Python Developer Round-0 Task**

Submission date: July 8, 2026

GitHub: https://github.com/zacjactech/trading_bot

---

## License

MIT – educational / interview task use
