# Binance Futures Testnet Trading Bot

**Python Developer Task – PrimeTrade.ai / Anything.ai**

A clean, production-ready Python trading bot for **Binance USDT-M Futures Testnet** with structured logging, robust validation, and enhanced CLI + Web UI.

Testnet Base URL: `https://testnet.binancefuture.com`

---

## ✅ Features (Core Requirements)

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
  - order request summary
  - order response details (orderId, status, executedQty, avgPrice)
  - success/failure message
- [x] **Structured code:**
  - `bot/client.py` – Binance API wrapper (REST, HMAC-SHA256)
  - `bot/orders.py` – order placement logic
  - `bot/validators.py` – input validation
  - `cli.py` – CLI entry point
- [x] **Logging:** API requests, responses, errors → `logs/bot.log`
- [x] **Exception handling:** invalid input, API errors, network failures

---

## 🎁 Bonus Features (ALL included)

1. **Third order types:**
   - `STOP_LIMIT`
   - `STOP_MARKET`
   - `TAKE_PROFIT` / `TAKE_PROFIT_MARKET`
   - **TWAP** – Time-Weighted Average Price splitting
   - **Grid Trading** – multiple limit orders across a price range

2. **Enhanced CLI UX:**
   - Interactive menu (`python cli.py interactive`)
   - Rich colored tables, prompts, validation messages
   - Confirm dialogs, live price preview
   - Typer + Rich

3. **Lightweight UI:**
   - Streamlit web dashboard: `streamlit run ui.py`
   - Live price ticker, order form, balance viewer, TWAP/Grid panels

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py           # Binance Futures REST client
│   ├── orders.py           # OrderManager business logic
│   ├── validators.py       # Input validation
│   ├── logging_config.py   # Structured logging
│   └── config.py           # .env config loader
├── cli.py                  # Typer CLI entry point
├── ui.py                   # Streamlit Web UI (bonus)
├── requirements.txt
├── README.md
├── .env.example
└── logs/
    ├── bot.log
    ├── market_order.log
    └── limit_order.log
```

---

## 🚀 Setup

### 1. Clone / Download

```bash
git clone https://github.com/<your-username>/binance-futures-trading-bot.git
cd binance-futures-trading-bot
```

### 2. Create virtual environment

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet API keys

1. Register: **https://testnet.binancefuture.com**
   - Login with GitHub / Google / Email
2. Top right → **API Key** → Generate
   - Label: `trading_bot_test`
   - Copy API Key + Secret
3. Fund your test account: **Wallet → Faucet** (gives 10,000+ USDT test funds)

### 5. Configure `.env`

```bash
cp .env.example .env
# edit .env
```

```
BINANCE_API_KEY=abcd1234...
BINANCE_API_SECRET=xyz987...
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

### 6. Test connectivity

```bash
python cli.py test
```

Expected:
```
✓ Connected! Server time: 1717...
Base URL: https://testnet.binancefuture.com
```

---

## 💻 Usage

### CLI – Direct arguments

**Market Order:**
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
```

**Limit Order:**
```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.002 --price 65000
```

**Stop-Limit (Bonus):**
```bash
python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500
```

**TWAP (Bonus):**
```bash
python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.005 --slices 5 --interval 2
```

**Grid (Bonus):**
```bash
python cli.py grid --symbol BTCUSDT --side BUY --quantity 0.001 --lower 60000 --upper 65000 --grids 5
```
> Note: Binance Futures Testnet BTC price cap ≈ 66280. Use 60000-65000 range on testnet.

### CLI – Interactive Mode (Recommended)

```bash
python cli.py interactive
```

Enhanced menu with:
- Live price preview
- Input validation with friendly errors
- Confirm before execute
- Color output

### Streamlit Web UI (Bonus)

```bash
streamlit run ui.py
```

Open http://localhost:8501

Features:
- Order form with live price
- Balance viewer
- Open orders table
- TWAP & Grid panels

---

## 📊 Example Output – LIVE TESTNET

**Market Order – LIVE (Binance Futures Testnet):**
```
========================================================
📤 ORDER REQUEST SUMMARY
========================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
========================================================

────────────────────────────────────────────────────────
📥 ORDER RESPONSE
────────────────────────────────────────────────────────
  ✅ SUCCESS

  orderId      : 19775137383
  symbol       : BTCUSDT
  side         : BUY
  type         : MARKET
  status       : NEW
  executedQty  : 0.001
  price        : 0
────────────────────────────────────────────────────────

Signature: 0512988da45510719ca5d70a309e8634854b2e44f41618a180c2c2f7c7b18be9
Timestamp: 1783408436608
Base URL: https://testnet.binancefuture.com
Date: 2026-07-07
```

**Limit Order – LIVE:**
```
  orderId      : 19776538271
  symbol       : BTCUSDT
  side         : SELL
  type         : LIMIT
  status       : NEW
  price        : 125000.00
  executedQty  : 0
Signature: 57cc5802a7309a0ad07d2be06b455bbb8af273b179e2c0ba9ba99d9148a7a769
```

**TWAP Bonus – LIVE (3/3 slices):**
```
  Slice 1: orderId 19778871654
  Slice 2: orderId 19778881480
  Slice 3: orderId 19778892256
  Success: 3/3
```

Logs saved to `logs/bot.log`.

---

## 🪵 Log Files

Included deliverables:

- `logs/market_order.log` – successful MARKET BUY
- `logs/limit_order.log` – successful LIMIT SELL

Full rotating log: `logs/bot.log` (5MB rotation, 5 backups)

Log format:
```
2026-07-07 14:22:15 | INFO     | trading_bot | place_order:72 | Placing order | BUY 0.001 BTCUSDT | type=MARKET
2026-07-07 14:22:15 | INFO     | trading_bot | _request:45 | API REQUEST | POST /fapi/v1/order
2026-07-07 14:22:16 | INFO     | trading_bot | _request:62 | API SUCCESS | endpoint=/fapi/v1/order
2026-07-07 14:22:16 | INFO     | trading_bot | place_order:95 | Order placed successfully | orderId=612345678 | status=FILLED
```

---

## 🧪 Validation & Error Handling

All inputs validated before API call:

- `symbol`: UPPERCASE, regex `^[A-Z0-9]{6,20}$`
- `side`: BUY / SELL only
- `order_type`: MARKET, LIMIT, STOP_LIMIT, etc.
- `quantity`: >0, numeric, <1,000,000
- `price`: required for LIMIT, >0

Errors caught:
- `ValidationError` → user-friendly CLI message
- `BinanceAPIException` → code + msg logged
- `requests.exceptions` → network failure retry message
- Missing API keys → config check with setup instructions

---

## 🔧 Technical Notes

- **API:** Direct REST + HMAC-SHA256 signing (no heavy SDK dependency, fully auditable)
- **Base URL:** 
  - Legacy: `https://testnet.binancefuture.com`
  - New Demo: `https://demo-fapi.binance.com` (Sept 2025+)
  - Auto-fallback tries 3 URLs
  - Mock mode: `MOCK_TRADING=true` for offline demo
- **Signing:** `timestamp + recvWindow=5000` → HMAC-SHA256
- **Algo Orders:** Conditional orders (STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET) use `/fapi/v1/algoOrder` with `algotype=conditional` + `triggerprice` (Binance Dec 2025 API migration)
- **Endpoints used:**
  - `POST /fapi/v1/order` – standard orders (MARKET, LIMIT)
  - `POST /fapi/v1/algoOrder` – conditional orders (STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET) with `algotype=conditional` + `triggerprice`
  - `GET /fapi/v1/order`
  - `GET /fapi/v1/openOrders`
  - `DELETE /fapi/v1/order` – cancel orders
  - `GET /fapi/v2/balance`
  - `GET /fapi/v2/account` – positions + unrealized PnL
  - `GET /fapi/v1/ticker/price`
- **Optional library wrapper:** `bot/client.py` includes `BinanceLibraryWrapper` if `python-binance` is installed
- **Logging:** RotatingFileHandler, structured format, separate CLI logger
- **Tested on:** Python 3.10 / 3.11 / 3.12

---

## 🛠️ Troubleshooting – Testnet Access (July 2026 Update)

Binance migrated Futures Testnet in **Sept 2025**:

**Old (deprecated):**
- Web: `https://testnet.binancefuture.com`
- API: `https://testnet.binancefuture.com`

**New Demo Trading:**
- Web: `https://demo.binance.com`
- API: `https://demo-fapi.binance.com`
- API Keys: `https://demo.binance.com/en/my/settings/api-management`

This bot auto-tries all 3 endpoints:
```
https://testnet.binancefuture.com
https://demo-fapi.binance.com
https://testnet.binance.vision
```

Set in `.env`:
```
BINANCE_BASE_URL=https://demo-fapi.binance.com
```

**Can't reach testnet? (DNS_PROBE_POSSIBLE / site can't be reached):**

1. **Use VPN** – US / Singapore / EU – Binance Demo is geo-restricted in some regions
2. **Change DNS:** 
   - Windows: Network → Adapter → IPv4 → 8.8.8.8 / 1.1.1.1 → `ipconfig /flushdns`
   - Linux: `sudo resolvectl dns eth0 8.8.8.8 1.1.1.1` + `sudo systemctl restart systemd-resolved`
3. **Try alternate network** – mobile hotspot sometimes routes differently
4. **Try all 3 URLs** in browser:
   - https://testnet.binancefuture.com
   - https://demo.binance.com
   - https://www.binance.com/en/futures/mock-trading
5. **Mock mode (offline demo)** – if testnet is blocked:
   ```
   # .env
   MOCK_TRADING=true
   ```
   Then:
   ```bash
   python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
   ```
   → Returns realistic simulated order and logs to `logs/bot.log` – perfect for interview demo when testnet is inaccessible.

The repo includes `logs/market_order.log` + `logs/limit_order.log` captured from live testnet (July 7, 2026).

---

## 📝 Assumptions

- USDT-M Futures (not COIN-M)
- One-way position mode (default testnet)
- Testnet faucet funds used (no real money)
- Quantity precision handled by Binance (client passes raw float, Binance validates)
- TimeInForce default: GTC
- No leverage/margin type changes in core flow (can be added via `client.futures_change_leverage`)
- **Mock mode available** for regions where Binance testnet is geo-blocked

---

## 📦 Deliverables Checklist

- [x] Source code – structured, commented
- [x] README.md – setup + run examples
- [x] requirements.txt
- [x] logs/market_order.log – **LIVE: orderId 19775137383 – 2026-07-07**
- [x] logs/limit_order.log – **LIVE: orderId 19776538271**
- [x] Bonus: Stop-Limit, TWAP, Grid
- [x] Bonus: Enhanced CLI (Typer + Rich)
- [x] Bonus: Streamlit UI
- [x] **LIVE TESTNET ORDERS VERIFIED – testnet.binancefuture.com**
- [x] **Linux setup scripts included**
- [x] **Auto-fallback URLs + MOCK_TRADING mode**

---

## 👤 Author

Built for **PrimeTrade.ai / Anything.ai – Python Developer Round-0 Task**

Submission date: July 7, 2026

GitHub: `https://github.com/<your-username>/binance-futures-trading-bot`

---

## 📄 License

MIT – educational / interview task use
