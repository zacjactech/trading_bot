#Requires -RunAsAdministrator
# Binance Testnet – Windows DNS Fix
# PrimeTrade.ai
# Run: Right-click → Run with PowerShell (Admin)
#  or: powershell -ExecutionPolicy Bypass -File .\fix_dns.ps1

Write-Host ""
Write-Host "🔧 Binance Testnet – DNS Fix – Windows" -ForegroundColor Cyan
Write-Host ""

function Test-HostRes {
    param([string]$Hostname)
    try {
        $r = Resolve-DnsName -Name $Hostname -Server 8.8.8.8 -ErrorAction Stop | Select-Object -First 1
        return $r.IPAddress
    } catch {
        return $null
    }
}

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  Not running as Administrator – DNS change requires admin" -ForegroundColor Yellow
    Write-Host "  Right-click PowerShell → Run as Administrator, then:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\fix_dns.ps1"
    Write-Host ""
    # still run tests read-only
} else {
    Write-Host "✓ Administrator – will apply DNS changes" -ForegroundColor Green
}

Write-Host ""
Write-Host "Active network adapters:"
Get-NetAdapter | Where-Object Status -eq "Up" | Format-Table Name, InterfaceDescription, Status -AutoSize

$adapters = Get-NetAdapter | Where-Object Status -eq "Up"
foreach ($ad in $adapters) {
    $ifAlias = $ad.Name
    Write-Host ""
    Write-Host "→ Configuring: $ifAlias" -ForegroundColor Yellow
    try {
        if ($isAdmin) {
            Set-DnsClientServerAddress -InterfaceAlias $ifAlias -ServerAddresses ("8.8.8.8","1.1.1.1","9.9.9.9") -ErrorAction Stop
            Write-Host "  ✓ DNS set to 8.8.8.8, 1.1.1.1, 9.9.9.9" -ForegroundColor Green
        } else {
            Write-Host "  Skipped (needs admin)" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "  ⚠ Failed: $_" -ForegroundColor Red
    }
}

if ($isAdmin) {
    Write-Host ""
    Write-Host "Flushing DNS cache…"
    Clear-DnsClientCache
    ipconfig /flushdns | Out-Null
    Write-Host "✓ Done" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== DNS Test ===" -ForegroundColor Cyan
$hosts = @("testnet.binancefuture.com","demo.binance.com","demo-fapi.binance.com","fapi.binance.com","api.binance.com")
foreach ($h in $hosts) {
    $ip = Test-HostRes $h
    if ($ip) {
        Write-Host ("{0,-30} → {1}" -f $h, $ip) -ForegroundColor Green
    } else {
        Write-Host ("{0,-30} → FAILED" -f $h) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== HTTPS Test ===" -ForegroundColor Cyan
$urls = @(
    "https://testnet.binancefuture.com/fapi/v1/ping",
    "https://testnet.binancefuture.com/fapi/v1/time",
    "https://demo-fapi.binance.com/fapi/v1/ping"
)
foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -Uri $u -Method Get -TimeoutSec 5 -UseBasicParsing
        Write-Host "$u → $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "$u → $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Get-DnsClientServerAddress | Where-Object {$_.ServerAddresses -ne @()} | Select-Object InterfaceAlias, ServerAddresses | Format-Table -AutoSize

Write-Host ""
Write-Host "If still blocked:"
Write-Host "  • Use VPN – ProtonVPN / Windsurf – connect SG / US / EU" -ForegroundColor Yellow
Write-Host "  • Or run bot in MOCK mode:"
Write-Host "    set MOCK_TRADING=true"
Write-Host "    python cli.py market --symbol BTCUSDT --side BUY --quantity 0.001"
Write-Host ""
Write-Host "Testnet endpoints:"
Write-Host "  https://testnet.binancefuture.com"
Write-Host "  https://demo-fapi.binance.com"
Write-Host ""
pause
