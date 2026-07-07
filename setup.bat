@echo off
REM Binance Futures Trading Bot – Windows One-Click Setup
REM PrimeTrade.ai – Python Developer Task
REM Double-click to run
REM
REM Options:
REM   setup.bat           – setup only (no orders placed)
REM   setup.bat --demo    – setup + demo orders

title PrimeTrade – Binance Futures Bot Setup
color 0B
echo.
echo  ===============================
echo   PrimeTrade – Futures Bot
echo   Binance Testnet – Windows
echo  ===============================
echo.

SET DEMO=0
if "%1"=="--demo" SET DEMO=1

REM --- Check Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
  py -3 --version >nul 2>&1
  if %errorlevel% neq 0 (
    echo [ERROR] Python 3 not found
    echo.
    echo Install from: https://www.python.org/downloads/windows/
    echo CHECK "Add Python to PATH"
    echo.
    pause
    exit /b 1
  ) else (
    set PYTHON=py -3
    goto :foundpy
  )
)
set PYTHON=python
:foundpy

%PYTHON% --version

REM --- venv ---
if not exist .venv (
  echo [*] Creating virtual environment…
  %PYTHON% -m venv .venv
  if %errorlevel% neq 0 (
    echo [!] venv failed, installing virtualenv…
    %PYTHON% -m pip install virtualenv
    %PYTHON% -m virtualenv .venv
  )
)

REM --- activate ---
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
  echo [!] Could not auto-activate venv
  echo     Run manually: .venv\Scripts\activate
)

echo.
echo [*] Installing requirements…
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
  echo [ERROR] pip install failed
  pause
  exit /b 1
)

REM --- .env ---
if not exist .env (
  copy .env.example .env >nul
  echo.
  echo [*] .env created – MOCK_TRADING enabled by default
  powershell -Command "(Get-Content .env) -replace 'MOCK_TRADING=false','MOCK_TRADING=true' | Set-Content .env"
)

echo.
echo === Test connectivity ===
python cli.py test

if %DEMO%==1 (
  echo.
  echo === MARKET ORDER DEMO ===
  python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001

  echo.
  echo === LIMIT ORDER DEMO ===
  python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 65000

  echo.
  echo === STOP-LIMIT BONUS ===
  python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500

  echo.
  echo === TWAP BONUS ===
  python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.003 --slices 3 --interval 2

  echo.
  echo === GRID BONUS ===
  python cli.py grid --symbol BTCUSDT --side BUY --quantity 0.001 --lower 60000 --upper 65000 --grids 3
)

echo.
echo ===============================
echo  [OK] Setup complete!
echo ===============================
echo.
echo Next:
echo   python cli.py interactive
echo   streamlit run ui.py
echo   python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001
if %DEMO%==0 (
  echo.
  echo   Run demo: setup.bat --demo
)
echo.
echo Edit .env to add LIVE API keys:
echo   BINANCE_API_KEY=...
echo   BINANCE_API_SECRET=...
echo   MOCK_TRADING=false
echo.
pause
