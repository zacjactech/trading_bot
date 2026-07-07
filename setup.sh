#!/usr/bin/env bash
# Binance Futures Trading Bot – Cross-Platform Setup
# PrimeTrade.ai – Python Developer Task
# Works: Linux (Ubuntu/Debian/Fedora/Arch/Zorin), macOS, WSL, Git Bash
set -e

DEMO=false
for arg in "$@"; do
  case "$arg" in
    --demo) DEMO=true ;;
  esac
done

echo "🚀 Binance Futures Testnet Bot – Setup"
echo ""

OS="$(uname -s)"
echo "Detected OS: $OS"

# --- Python check / install hints ---
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found."
  case "$OS" in
    Linux*) echo "  Try: sudo apt update && sudo apt install -y python3 python3-pip python3-venv" ;;
    Darwin*) echo "  Try: brew install python@3.11" ;;
    MINGW*|MSYS*|CYGWIN*) echo "  Download: https://www.python.org/downloads/windows/ – check 'Add to PATH'" ;;
  esac
  exit 1
fi

PYTHON=python3
PIP="$PYTHON -m pip"

# --- venv create ---
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv .venv || {
    echo "venv creation failed – installing venv tools…"
    if [[ "$OS" == "Linux"* ]]; then
      if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3-venv python3-pip
      elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-pip
      elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python-pip
      fi
      $PYTHON -m venv .venv
    else
      echo "Please install python3-venv manually, then re-run."
      exit 1
    fi
  }
fi

# activate
# shellcheck disable=SC1091
if [ -f ".venv/bin/activate" ]; then
  # Linux / macOS
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  # Windows Git Bash
  source .venv/Scripts/activate
else
  echo "⚠️  Could not auto-activate venv – activate manually:"
  echo "  Linux/Mac: source .venv/bin/activate"
  echo "  Windows: .venv\\Scripts\\activate"
fi

echo ""
echo "Installing requirements…"
python -m pip install --upgrade pip
pip install -r requirements.txt

# --- .env ---
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚙️  .env created – edit with your API keys, or leave MOCK_TRADING=true for offline demo"
  # default to mock safe mode for first run
  if [[ "$OS" != "MINGW"* ]] && [[ "$OS" != "MSYS"* ]]; then
    sed -i 's/^MOCK_TRADING=false/MOCK_TRADING=true/' .env || true
  fi
fi

echo ""
echo "=== Connectivity Test ==="
python cli.py test || true

if [ "$DEMO" = true ]; then
  echo ""
  echo "=== MARKET ORDER DEMO ==="
  python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001 || true

  echo ""
  echo "=== LIMIT ORDER DEMO ==="
  python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 65000 || true

  echo ""
  echo "=== STOP-LIMIT BONUS ==="
  python cli.py stop-limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 59000 --stop-price 59500 || true

  echo ""
  echo "=== TWAP BONUS ==="
  python cli.py twap --symbol BTCUSDT --side BUY --quantity 0.003 --slices 3 --interval 2 || true

  echo ""
  echo "=== GRID BONUS ==="
  python cli.py grid --symbol BTCUSDT --side BUY --quantity 0.001 --lower 60000 --upper 65000 --grids 5 || true
fi

echo ""
echo "✅ Setup complete – logs in ./logs/"
echo ""
echo "Next steps:"
echo "  Interactive CLI : python cli.py interactive"
echo "  Web UI          : streamlit run ui.py"
echo "  Place an order  : python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001"
echo "  Check balance   : python cli.py balance"
if [ "$DEMO" = false ]; then
  echo ""
  echo "  Run demo orders : bash setup.sh --demo"
fi
echo ""
echo "To use LIVE keys: edit .env"
echo "  BINANCE_API_KEY=..."
echo "  BINANCE_API_SECRET=..."
echo "  MOCK_TRADING=false"
echo "  BINANCE_BASE_URL=https://testnet.binancefuture.com"
