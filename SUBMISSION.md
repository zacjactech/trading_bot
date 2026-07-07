# PrimeTrade.ai – Python Developer – Round-0 Submission

**Date:** July 7, 2026  
**Deadline:** July 8, 2026 – 11:50 PM IST  
**Position:** Python Developer – Trading Bot (Binance Futures Testnet)

---

## GitHub Repository

```
https://github.com/YOUR_USERNAME/binance-futures-trading-bot
```

Replace YOUR_USERNAME with your GitHub handle, then push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/binance-futures-trading-bot.git
git push -u origin main
```

---

## Live Testnet Orders – VERIFIED

**Base URL:** https://testnet.binancefuture.com  
**Account:** Demo API – HMAC SHA256

### 1. MARKET Order
- **orderId:** 19775137383
- **Time:** 2026-07-07 08:13:56 UTC
- **Symbol:** BTCUSDT
- **Side:** BUY
- **Type:** MARKET
- **Quantity:** 0.001
- **Status:** NEW
- **Signature:** 0512988da45510719ca5d70a309e8634854b2e44f41618a180c2c2f7c7b18be9
- **Timestamp:** 1783408436608
- **Log:** `logs/market_order.log`

### 2. LIMIT Order
- **orderId:** 19776538271
- **Time:** 2026-07-07 08:22:02 UTC
- **Symbol:** BTCUSDT
- **Side:** SELL
- **Type:** LIMIT
- **Quantity:** 0.001
- **Price:** 125000
- **Status:** NEW
- **TimeInForce:** GTC
- **Signature:** 57cc5802a7309a0ad07d2be06b455bbb8af273b179e2c0ba9ba99d9148a7a769
- **Timestamp:** 1783408920979
- **Log:** `logs/limit_order.log`

### 3. STOP_LIMIT (Bonus – LIVE)
- orderId: 1000000128653638
- Uses Binance Futures API mapping: STOP_LIMIT → STOP
- Routed to `/fapi/v1/algoOrder` with `algotype=conditional` + `triggerprice`
- Resolves API Error -1116 (Invalid orderType) and -4120 (Algo API migration)

### 4. STOP_MARKET (Bonus – LIVE)
- orderId: 1000000128653645
- Uses algo order endpoint with `triggerprice` parameter

### 5. TAKE_PROFIT_MARKET (Bonus – LIVE)
- orderId: 1000000128653652
- Uses algo order endpoint with `triggerprice` parameter

### 6. TWAP (Bonus – LIVE)
- **orderId:** 19778871654, 19778881480, 19778892256
- **Result:** 3/3 slices successful
- **Quantity:** 0.001 x 3 = 0.003 BTCUSDT

### 7. Grid Trading (Bonus)
- Fully implemented – see `OrderManager.place_grid_orders()`

---

## Google Form Submission Fields

Form URL: https://docs.google.com/forms/d/e/1FAIpQLScNGJdTAV4tMHxHR-vLuXbVR2vGk3IFdV_BPXa2KBysVLkSVg/viewform

| Field | Value |
|-------|-------|
| Full Name | **FILL ME** |
| Email | **FILL ME** |
| Position/Role | Python Developer |
| GitHub Link(Assignment) | https://github.com/YOUR_USERNAME/binance-futures-trading-bot |
| Resume Link | **FILL ME** |
| Phone Number | **FILL ME** |
| Experience(in months) | **FILL ME** |
| Year of Passout | **FILL ME – must be 2026 or earlier** |
| Branch | **FILL ME** |

> Replace **FILL ME** / YOUR_USERNAME before submitting.

---

## Deliverables Included

- [x] `bot/client.py` – REST HMAC-SHA256, auto-fallback URLs, MOCK_TRADING, STOP_LIMIT→STOP mapping, algo order endpoint with `algotype=conditional` + `triggerprice`
- [x] `bot/orders.py` – OrderManager (Market, Limit, Stop, Stop-Market, Take-Profit, TWAP, Grid)
- [x] `bot/validators.py` – full input validation
- [x] `bot/logging_config.py` – RotatingFileHandler structured logging
- [x] `cli.py` – Typer + Rich interactive CLI
- [x] `ui.py` – Streamlit Pro – modern dark trading terminal
- [x] `requirements.txt`
- [x] `README.md`
- [x] `logs/market_order.log` – LIVE order 19775137383
- [x] `logs/limit_order.log` – LIVE order 19776538271
- [x] `setup.sh` – Linux / macOS / WSL one-click (cross-platform)
- [x] `setup.ps1` – Windows PowerShell – native
- [x] `setup.bat` – Windows CMD – double-click
- [x] `fix_dns.sh` – Linux / macOS DNS fix
- [x] `fix_dns.ps1` – Windows DNS fix (admin)

---

## Run Instructions

**Linux / macOS:**
```bash
bash setup.sh
# or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python cli.py test
```

**Windows PowerShell (Admin recommended for DNS):**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
# then:
python cli.py interactive
streamlit run ui.py
```

**Windows CMD – double click:**
```
setup.bat
```

Then:
```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 65000
python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500
python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.003 --slices 3
streamlit run ui.py
```

---

Binance Futures Testnet Trading Bot
PrimeTrade.ai / Anything.ai – Python Developer Task
July 2026
