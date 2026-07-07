"""
Order placement logic - separates API client from business logic
"""
from typing import Dict, Any, Optional
from .client import BinanceFuturesClient
from .validators import validate_order_inputs, ValidationError
from .logging_config import logger

__all__ = ["OrderManager", "print_order_request", "print_order_response"]

class OrderManager:
    """High-level order management with validation and logging"""
    
    def __init__(self, client: Optional[BinanceFuturesClient] = None):
        self.client = client or BinanceFuturesClient()
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a MARKET order"""
        logger.info(f"Market order requested: {side} {quantity} {symbol}")
        validated = validate_order_inputs(symbol, side, "MARKET", quantity)
        return self._execute_order(validated)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, time_in_force: str = "GTC") -> Dict[str, Any]:
        """Place a LIMIT order"""
        logger.info(f"Limit order requested: {side} {quantity} {symbol} @ {price}")
        validated = validate_order_inputs(symbol, side, "LIMIT", quantity, price)
        return self._execute_order(validated, time_in_force=time_in_force)
    
    def place_stop_limit_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float, 
        stop_price: float,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Place a STOP_LIMIT order
        """
        logger.info(f"Stop-Limit order requested: {side} {quantity} {symbol} stop={stop_price} limit={price}")
        validated = validate_order_inputs(symbol, side, "STOP_LIMIT", quantity, price, stop_price)
        return self._execute_order(validated, time_in_force=time_in_force)
    
    def place_stop_market_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict[str, Any]:
        """Stop Market"""
        validated = validate_order_inputs(symbol, side, "STOP_MARKET", quantity, price=None, stop_price=stop_price)
        return self._execute_order(validated)
    
    def place_twap_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        slices: int = 5,
        interval_seconds: int = 2,
        order_type: str = "MARKET"
    ) -> list:
        """
        TWAP - Time-Weighted Average Price
        Splits a large order into smaller chunks over time
        """
        import time as time_module
        logger.info(f"TWAP order start: {side} {total_quantity} {symbol} in {slices} slices")
        
        slice_qty = round(total_quantity / slices, 6)
        results = []
        
        for i in range(slices):
            # Adjust last slice for rounding
            qty = slice_qty if i < slices - 1 else round(total_quantity - slice_qty * (slices - 1), 6)
            logger.info(f"TWAP slice {i+1}/{slices}: {qty}")
            try:
                validated = validate_order_inputs(symbol, side, order_type, qty)
                result = self._execute_order(validated)
                results.append(result)
            except Exception as e:
                logger.error(f"TWAP slice {i+1} failed: {e}")
                results.append({"error": str(e), "slice": i+1})
            
            if i < slices - 1:
                time_module.sleep(interval_seconds)
        
        logger.info(f"TWAP completed: {len([r for r in results if 'orderId' in r])}/{slices} successful")
        return results
    
    def place_grid_orders(
        self,
        symbol: str,
        side: str,
        quantity_per_grid: float,
        lower_price: float,
        upper_price: float,
        grids: int = 5
    ) -> list:
        """
        Grid trading - place multiple limit orders at different price levels
        """
        logger.info(f"Grid order: {grids} levels between {lower_price} - {upper_price}")
        
        if lower_price >= upper_price:
            raise ValidationError("lower_price must be < upper_price")
        
        step = (upper_price - lower_price) / (grids - 1) if grids > 1 else 0
        results = []
        
        for i in range(grids):
            grid_price = round(lower_price + step * i, 2)
            try:
                validated = validate_order_inputs(symbol, side, "LIMIT", quantity_per_grid, grid_price)
                result = self._execute_order(validated)
                results.append(result)
            except Exception as e:
                logger.error(f"Grid level {i+1} @ {grid_price} failed: {e}")
                results.append({"error": str(e), "price": grid_price})
        
        return results
    
    def _execute_order(self, validated: dict, time_in_force: str = "GTC") -> Dict[str, Any]:
        """Execute validated order via client"""
        try:
            response = self.client.place_order(
                symbol=validated["symbol"],
                side=validated["side"],
                order_type=validated["type"],
                quantity=validated["quantity"],
                price=validated.get("price"),
                stop_price=validated.get("stopPrice"),
                time_in_force=time_in_force
            )
            return response
            
        except ValidationError as ve:
            logger.error(f"Validation failed: {ve}")
            raise
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            raise


def print_order_request(order: dict):
    """Print clear order request summary"""
    print("\n" + "="*56)
    print("📤 ORDER REQUEST SUMMARY")
    print("="*56)
    print(f"  Symbol     : {order['symbol']}")
    print(f"  Side       : {order['side']}")
    print(f"  Type       : {order['type']}")
    print(f"  Quantity   : {order['quantity']}")
    if order.get("price"):
        print(f"  Price      : {order['price']}")
    if order.get("stopPrice"):
        print(f"  Stop Price : {order['stopPrice']}")
    print("="*56 + "\n")

def print_order_response(resp: dict):
    """Print clear order response details"""
    print("\n" + "─"*56)
    print("📥 ORDER RESPONSE")
    print("─"*56)
    
    order_id = resp.get("orderId", "N/A")
    status = resp.get("status", "N/A")
    executed_qty = resp.get("executedQty", resp.get("origQty", "N/A"))
    avg_price = resp.get("avgPrice", "0")
    symbol = resp.get("symbol", "N/A")
    side = resp.get("side", "N/A")
    order_type = resp.get("type", "N/A")
    
    # Success / failure
    if status in ["NEW", "FILLED", "PARTIALLY_FILLED"]:
        print("  ✅ SUCCESS")
    else:
        print(f"  ⚠️  Status: {status}")
    
    print(f"\n  orderId      : {order_id}")
    print(f"  symbol       : {symbol}")
    print(f"  side         : {side}")
    print(f"  type         : {order_type}")
    print(f"  status       : {status}")
    print(f"  executedQty  : {executed_qty}")
    if avg_price and float(avg_price) != 0:
        print(f"  avgPrice     : {avg_price}")
    if "price" in resp:
        print(f"  price        : {resp['price']}")
    if "cumQuote" in resp:
        print(f"  cumQuote     : {resp['cumQuote']}")
    
    print("─"*56 + "\n")
