#!/usr/bin/env python3
"""
Binance Futures Testnet Trading Bot - CLI Entry Point

Enhanced CLI UX with Typer + Rich
Supports: MARKET, LIMIT, STOP_LIMIT, TWAP, Grid
"""
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, FloatPrompt, IntPrompt
from rich import box

from bot.orders import OrderManager, print_order_request, print_order_response
from bot.client import BinanceFuturesClient
from bot.config import Config
from bot.logging_config import logger, setup_logger

app = typer.Typer(
    help="🚀 Binance Futures Testnet Trading Bot",
    rich_markup_mode="rich",
    add_completion=False
)
console = Console()

# Setup dedicated CLI logger
cli_logger = setup_logger("cli", level=20)


def check_config():
    """Check API configuration"""
    errors = Config.validate()
    if errors:
        console.print(Panel(
            "\n".join([f"• {e}" for e in errors]) + 
            "\n\n[bold]Setup:[/bold]\n1. Copy .env.example to .env\n2. Add your Testnet API Key/Secret\n3. Get keys from: https://testnet.binancefuture.com",
            title="⚠️  API Configuration Missing",
            border_style="red"
        ))
        raise typer.Exit(code=1)


@app.command()
def market(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair e.g., BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive prompt mode")
):
    """Place a MARKET order"""
    check_config()
    
    if interactive:
        symbol, side, quantity = interactive_market_prompt()
    
    try:
        manager = OrderManager()
        result = manager.place_market_order(symbol, side, quantity)
        console.print(f"[green]✓ Market order completed: {result.get('orderId')}[/green]")
    except Exception as e:
        console.print(f"[bold red]Order failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def limit(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: float = typer.Option(..., "--price", "-p", help="Limit price"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode")
):
    """Place a LIMIT order"""
    check_config()
    
    if interactive:
        symbol, side, quantity, price = interactive_limit_prompt()
    
    try:
        manager = OrderManager()
        result = manager.place_limit_order(symbol, side, quantity, price)
        console.print(f"[green]✓ Limit order placed: {result.get('orderId')} | Status: {result.get('status')}[/green]")
    except Exception as e:
        console.print(f"[bold red]Order failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command(name="stop-limit")
def stop_limit(
    symbol: str = typer.Option(..., "--symbol", "-s"),
    side: str = typer.Option(..., "--side"),
    quantity: float = typer.Option(..., "--quantity", "-q"),
    price: float = typer.Option(..., "--price", "-p", help="Limit price"),
    stop_price: float = typer.Option(..., "--stop-price", help="Stop trigger price"),
):
    """BONUS: Place a STOP_LIMIT order"""
    check_config()
    try:
        manager = OrderManager()
        result = manager.place_stop_limit_order(symbol, side, quantity, price, stop_price)
        console.print(f"[green]✓ Stop-Limit order: {result.get('orderId')}[/green]")
    except Exception as e:
        console.print(f"[bold red]Failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def twap(
    symbol: str = typer.Option(..., "--symbol", "-s"),
    side: str = typer.Option(..., "--side"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Total quantity"),
    slices: int = typer.Option(5, "--slices", help="Number of slices"),
    interval: int = typer.Option(2, "--interval", help="Seconds between slices"),
):
    """BONUS: TWAP - split order over time"""
    check_config()
    console.print(f"[cyan]Starting TWAP: {slices} slices, {interval}s interval[/cyan]")
    manager = OrderManager()
    results = manager.place_twap_order(symbol, side, quantity, slices, interval)
    
    success = len([r for r in results if "orderId" in r])
    table = Table(title=f"TWAP Results {success}/{slices} successful", box=box.ROUNDED)
    table.add_column("Slice", justify="right")
    table.add_column("OrderId")
    table.add_column("Status")
    for i, r in enumerate(results, 1):
        if "orderId" in r:
            table.add_row(str(i), str(r["orderId"]), f"[green]{r.get('status')}[/green]")
        else:
            table.add_row(str(i), "-", f"[red]{r.get('error', 'failed')}[/red]")
    console.print(table)


@app.command()
def grid(
    symbol: str = typer.Option(...),
    side: str = typer.Option(...),
    quantity: float = typer.Option(..., help="Quantity per grid level"),
    lower: float = typer.Option(..., help="Lower price"),
    upper: float = typer.Option(..., help="Upper price"),
    grids: int = typer.Option(5, help="Number of grid levels"),
):
    """BONUS: Grid trading - multiple limit orders"""
    check_config()
    manager = OrderManager()
    results = manager.place_grid_orders(symbol, side, quantity, lower, upper, grids)
    success = len([r for r in results if "orderId" in r])
    console.print(f"[green]Grid completed: {success}/{grids} orders placed[/green]")


@app.command()
def balance():
    """Show Futures account balance"""
    check_config()
    client = BinanceFuturesClient()
    try:
        balances = client.get_account_balance()
        table = Table(title="Futures Testnet Balance", box=box.SIMPLE_HEAVY)
        table.add_column("Asset")
        table.add_column("Balance", justify="right")
        table.add_column("Available", justify="right")
        for b in balances:
            bal = float(b["balance"])
            if bal != 0:
                table.add_row(b["asset"], f"{bal:.4f}", b.get("availableBalance", b.get("withdrawAvailable", "0")))
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def price(
    symbol: str = typer.Argument(..., help="e.g., BTCUSDT")
):
    """Get current symbol price"""
    check_config()
    client = BinanceFuturesClient()
    try:
        p = client.get_symbol_price(symbol.upper())
        console.print(f"[bold cyan]{symbol.upper()}: ${p:,.2f}[/bold cyan]")
    except Exception as e:
        console.print(f"[red]{e}[/red]")


@app.command()
def interactive():
    """
    BONUS: Enhanced interactive CLI menu
    """
    check_config()
    console.print(Panel.fit("[bold cyan]Binance Futures Testnet – Interactive Trader[/bold cyan]", border_style="cyan"))
    
    while True:
        console.print("\n[bold]Choose action:[/bold]")
        console.print("  1) Market order")
        console.print("  2) Limit order")
        console.print("  3) Stop-Limit order  [bonus]")
        console.print("  4) TWAP order  [bonus]")
        console.print("  5) Grid orders  [bonus]")
        console.print("  6) Check balance")
        console.print("  7) Check price")
        console.print("  0) Exit")
        
        choice = Prompt.ask("Select", choices=["0","1","2","3","4","5","6","7"], default="1")
        
        try:
            if choice == "0":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif choice == "1":
                s, sd, q = interactive_market_prompt()
                OrderManager().place_market_order(s, sd, q)
            elif choice == "2":
                s, sd, q, p = interactive_limit_prompt()
                OrderManager().place_limit_order(s, sd, q, p)
            elif choice == "3":
                s, sd, q, p, sp = interactive_stop_limit_prompt()
                OrderManager().place_stop_limit_order(s, sd, q, p, sp)
            elif choice == "4":
                s = Prompt.ask("Symbol", default="BTCUSDT").upper()
                sd = Prompt.ask("Side", choices=["BUY","SELL"], default="BUY")
                q = FloatPrompt.ask("Total quantity")
                slices = IntPrompt.ask("Slices", default=5)
                interval = IntPrompt.ask("Interval seconds", default=2)
                OrderManager().place_twap_order(s, sd, q, slices, interval)
            elif choice == "5":
                s = Prompt.ask("Symbol", default="BTCUSDT").upper()
                sd = Prompt.ask("Side", choices=["BUY","SELL"], default="BUY")
                q = FloatPrompt.ask("Qty per grid")
                low = FloatPrompt.ask("Lower price")
                high = FloatPrompt.ask("Upper price")
                grids = IntPrompt.ask("Grid count", default=5)
                OrderManager().place_grid_orders(s, sd, q, low, high, grids)
            elif choice == "6":
                balance()
            elif choice == "7":
                sym = Prompt.ask("Symbol", default="BTCUSDT")
                price(sym)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        
        if not Confirm.ask("\nContinue?", default=True):
            break


# --- Interactive prompt helpers ---
def interactive_market_prompt():
    console.print(Panel("Market Order", style="green"))
    symbol = Prompt.ask("Symbol", default="BTCUSDT").upper()
    side = Prompt.ask("Side", choices=["BUY", "SELL"], default="BUY")
    # Show current price
    try:
        p = BinanceFuturesClient().get_symbol_price(symbol)
        console.print(f"[dim]Current {symbol} price: ${p:,.2f}[/dim]")
    except Exception:
        pass
    quantity = FloatPrompt.ask("Quantity")
    console.print(f"\n[bold]Confirm:[/bold] {side} {quantity} {symbol} MARKET")
    if not Confirm.ask("Execute?", default=True):
        raise typer.Abort()
    return symbol, side, quantity

def interactive_limit_prompt():
    console.print(Panel("Limit Order", style="blue"))
    symbol = Prompt.ask("Symbol", default="BTCUSDT").upper()
    side = Prompt.ask("Side", choices=["BUY", "SELL"], default="BUY")
    try:
        p = BinanceFuturesClient().get_symbol_price(symbol)
        console.print(f"[dim]Current {symbol} price: ${p:,.2f}[/dim]")
    except Exception:
        p = None
    quantity = FloatPrompt.ask("Quantity")
    default_price = str(p) if p else ""
    price_val = FloatPrompt.ask("Limit price", default=p if p else ...)
    console.print(f"\n[bold]Confirm:[/bold] {side} {quantity} {symbol} @ {price_val} LIMIT")
    if not Confirm.ask("Execute?", default=True):
        raise typer.Abort()
    return symbol, side, quantity, price_val

def interactive_stop_limit_prompt():
    console.print(Panel("Stop-Limit Order [BONUS]", style="magenta"))
    symbol = Prompt.ask("Symbol", default="BTCUSDT").upper()
    side = Prompt.ask("Side", choices=["BUY", "SELL"], default="BUY")
    quantity = FloatPrompt.ask("Quantity")
    stop_price = FloatPrompt.ask("Stop trigger price")
    limit_price = FloatPrompt.ask("Limit price")
    console.print(f"\n[bold]Confirm:[/bold] {side} {quantity} {symbol} STOP {stop_price} → LIMIT {limit_price}")
    if not Confirm.ask("Execute?", default=True):
        raise typer.Abort()
    return symbol, side, quantity, limit_price, stop_price


@app.command()
def test():
    """Test API connectivity"""
    check_config()
    client = BinanceFuturesClient()
    try:
        console.print("[cyan]Pinging testnet...[/cyan]")
        client.ping()
        t = client.get_server_time()
        console.print(f"[green]✓ Connected! Server time: {t.get('serverTime')}[/green]")
        console.print(f"[dim]Base URL: {client.base_url}[/dim]")
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
