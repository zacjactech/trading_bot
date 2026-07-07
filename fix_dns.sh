#!/usr/bin/env bash
# Binance Testnet – Cross-Platform DNS Fix
# Supports: Linux (systemd-resolved, NetworkManager, /etc/resolv.conf),
#           macOS, WSL, Windows (Git Bash – prints manual steps)
# Usage: sudo bash fix_dns.sh  (Linux/macOS – needs root)
#        bash fix_dns.sh       (Windows – informational)

set -e
OS="$(uname -s)"
echo "🔧 Binance Testnet DNS Helper"
echo "Detected: $OS"
echo ""

TEST_HOSTS="testnet.binancefuture.com demo.binance.com demo-fapi.binance.com fapi.binance.com"

test_dns() {
  echo "— DNS resolution test —"
  for h in $TEST_HOSTS; do
    printf "%-30s → " "$h"
    if command -v getent >/dev/null 2>&1; then
      getent hosts "$h" | awk '{print $1}' | head -1 || echo "FAILED"
    elif command -v dscacheutil >/dev/null 2>&1; then
      dscacheutil -q host -a name "$h" | awk '/ip_address/ {print $2; exit}' || echo "FAILED"
    elif command -v nslookup >/dev/null 2>&1; then
      nslookup "$h" 2>/dev/null | awk '/Address: / {print $2}' | tail -1 || echo "FAILED"
    else
      ping -c1 -W1 "$h" >/dev/null 2>&1 && echo "OK" || echo "FAILED"
    fi
  done
  echo ""
}

test_https() {
  echo "— HTTPS connectivity —"
  for url in \
    "https://testnet.binancefuture.com/fapi/v1/ping" \
    "https://demo-fapi.binance.com/fapi/v1/ping" \
    "https://fapi.binance.com/fapi/v1/ping"
  do
    echo -n "$url → "
    if command -v curl >/dev/null 2>&1; then
      curl -s -m 5 -o /dev/null -w "%{http_code}\n" "$url" || echo "fail"
    else
      echo "curl not found"
    fi
  done
  echo ""
}

case "$OS" in
  Linux*)
    echo "→ Linux detected"
    # Backup
    [ -w /etc/resolv.conf ] && sudo cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%s) 2>/dev/null || true

    # systemd-resolved ?
    if command -v resolvectl >/dev/null 2>&1 && systemctl is-active --quiet systemd-resolved 2>/dev/null; then
      echo "→ systemd-resolved active – setting global DNS to 8.8.8.8,1.1.1.1,9.9.9.9"
      sudo mkdir -p /etc/systemd/resolved.conf.d
      sudo tee /etc/systemd/resolved.conf.d/99-binance-dns.conf >/dev/null <<'EOC'
[Resolve]
DNS=8.8.8.8 1.1.1.1 9.9.9.9
FallbackDNS=8.8.4.4 1.0.0.1
Domains=~.
DNSOverTLS=no
EOC
      sudo systemctl restart systemd-resolved || true
      sudo resolvectl flush-caches || true
    fi

    # NetworkManager – try to set DNS on active connections
    if command -v nmcli >/dev/null 2>&1; then
      echo "→ NetworkManager detected – updating active connections"
      for CONN in $(nmcli -t -f NAME,TYPE,DEVICE con show --active | cut -d: -f1); do
        echo "  Setting DNS for: $CONN"
        sudo nmcli con mod "$CONN" ipv4.dns "8.8.8.8,1.1.1.1" || true
        sudo nmcli con mod "$CONN" ipv4.ignore-auto-dns yes || true
        sudo nmcli con down "$CONN" >/dev/null 2>&1 || true
        sudo nmcli con up "$CONN" >/dev/null 2>&1 || true
      done
    fi

    # Fallback direct resolv.conf
    if [ -w /etc/resolv.conf ] || [ "$EUID" -eq 0 ]; then
      echo "→ Updating /etc/resolv.conf fallback"
      printf "nameserver 8.8.8.8\nnameserver 1.1.1.1\nnameserver 9.9.9.9\n" | sudo tee /etc/resolv.conf >/dev/null || true
    fi
    ;;

  Darwin*)
    echo "→ macOS detected"
    echo "Setting DNS to 8.8.8.8 / 1.1.1.1 on all active services…"
    # List network services
    SERVICES=$(networksetup -listallnetworkservices | tail -n +2 | grep -v "^\*")
    echo "$SERVICES" | while read -r SVC; do
      [ -z "$SVC" ] && continue
      echo "  $SVC → 8.8.8.8 1.1.1.1 9.9.9.9"
      sudo networksetup -setdnsservers "$SVC" 8.8.8.8 1.1.1.1 9.9.9.9 2>/dev/null || true
    done
    echo "Flushing DNS cache…"
    sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder 2>/dev/null || true
    ;;

  MINGW*|MSYS*|CYGWIN*)
    echo "→ Windows (Git Bash) detected"
    echo ""
    echo "Manual steps – run in Administrator PowerShell:"
    echo "  1. Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ServerAddresses '8.8.8.8','1.1.1.1'"
    echo "  2. Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses '8.8.8.8','1.1.1.1'"
    echo "  3. ipconfig /flushdns"
    echo ""
    echo "Or GUI: Settings → Network → Adapter → IPv4 → DNS: 8.8.8.8 , 1.1.1.1"
    echo ""
    ;;
  *)
    echo "Unknown OS: $OS – printing generic advice"
    ;;
esac

echo ""
test_dns
test_https

cat << 'ENDMSG'

If still blocked:
  • VPN recommended – ProtonVPN / Windscribe (free tier)
    Linux: protonvpn-cli connect --sc
    macOS: use ProtonVPN app
    Windows: ProtonVPN / Windscribe GUI
  • Mobile hotspot test – carrier DNS often differs
  • Testnet endpoints tried by the bot (auto-fallback):
    1) https://testnet.binancefuture.com
    2) https://demo-fapi.binance.com
    3) https://testnet.binance.vision

Offline demo (always works):
  MOCK_TRADING=true python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001

ENDMSG
