# Binance Futures Trading Bot – Windows PowerShell Setup
# PrimeTrade.ai – Python Developer Task
# Run: Right-click → Run with PowerShell
#  or: powershell -ExecutionPolicy Bypass -File .\setup.ps1
#  or: powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Demo

param(
    [switch]$Demo
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "PrimeTrade – Binance Futures Bot Setup"

Write-Host ""
Write-Host "🚀 Binance Futures Testnet Bot – Windows Setup" -ForegroundColor Cyan
Write-Host "   PrimeTrade.ai – Python Developer" -ForegroundColor DarkGray
Write-Host ""

# --- Check Python ---
try {
    $pyVersion = & python --version 2>&1
    Write-Host "✓ Found: $pyVersion" -ForegroundColor Green
    $PYTHON = "python"
} catch {
    try {
        $pyVersion = & py -3 --version 2>&1
        Write-Host "✓ Found: $pyVersion"
        $PYTHON = "py -3"
    } catch {
        Write-Host "❌ Python 3 not found in PATH" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install Python 3.10+ from:"
        Write-Host "  https://www.python.org/downloads/windows/"
        Write-Host "  ⚠️  CHECK 'Add Python to PATH' during install"
        Write-Host ""
        pause
        exit 1
    }
}

# --- venv ---
if (-Not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    Invoke-Expression "$PYTHON -m venv .venv"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "venv failed – trying pip install virtualenv fallback…" -ForegroundColor Yellow
        Invoke-Expression "$PYTHON -m pip install virtualenv"
        Invoke-Expression "$PYTHON -m virtualenv .venv"
    }
} else {
    Write-Host "✓ venv already exists" -ForegroundColor Green
}

# --- activate ---
$activatePath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
    Write-Host "Activating venv…"
    & $activatePath
} else {
    Write-Host "⚠️ Could not find .venv\Scripts\Activate.ps1 – activating manually may be needed" -ForegroundColor Yellow
}

# ensure pip
Write-Host ""
Write-Host "Installing dependencies…" -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ pip install failed" -ForegroundColor Red
    pause
    exit 1
}

# --- .env ---
if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "⚙️  .env created" -ForegroundColor Yellow
    Write-Host "   Edit .env to add your API keys, OR"
    Write-Host "   Leave MOCK_TRADING=true for offline demo"
    # enable mock by default
    (Get-Content ".env") -replace "^MOCK_TRADING=false", "MOCK_TRADING=true" | Set-Content ".env"
    Write-Host "   → MOCK_TRADING enabled by default (safe)"
}

Write-Host ""
Write-Host "=== Test connectivity ===" -ForegroundColor Cyan
python cli.py test
if ($LASTEXITCODE -ne 0) { Write-Host "test failed – continuing anyway (may need API keys)" -ForegroundColor Yellow }

if ($Demo) {
    Write-Host ""
    Write-Host "=== MARKET ORDER DEMO ===" -ForegroundColor Cyan
    python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001

    Write-Host ""
    Write-Host "=== LIMIT ORDER DEMO ===" -ForegroundColor Cyan
    python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 65000

    Write-Host ""
    Write-Host "=== STOP-LIMIT BONUS ===" -ForegroundColor Magenta
    python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500

    Write-Host ""
    Write-Host "=== TWAP BONUS ===" -ForegroundColor Magenta
    python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.003 --slices 3 --interval 2

    Write-Host ""
    Write-Host "=== GRID BONUS ===" -ForegroundColor Magenta
    python cli.py grid --symbol BTCUSDT --side BUY --quantity 0.001 --lower 60000 --upper 65000 --grids 3
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  Interactive CLI :  python cli.py interactive" -ForegroundColor White
Write-Host "  Web UI          :  streamlit run ui.py" -ForegroundColor White
Write-Host "  Place an order  :  python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001" -ForegroundColor White
Write-Host "  Balance         :  python cli.py balance" -ForegroundColor White
if (-not $Demo) {
    Write-Host ""
    Write-Host "  Run demo orders :  .\setup.ps1 -Demo" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "To use LIVE keys, edit .env:"
Write-Host "  BINANCE_API_KEY=..."
Write-Host "  BINANCE_API_SECRET=..."
Write-Host "  MOCK_TRADING=false"
Write-Host "  BINANCE_BASE_URL=https://testnet.binancefuture.com"
Write-Host ""
Write-Host "PrimeTrade.ai – Python Developer Task – July 2026"
Write-Host ""
pause
