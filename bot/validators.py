"""
Input validation for trading orders
"""
from typing import Optional
import re
from bot.types import OrderParams

__all__ = [
    "ValidationError",
    "validate_symbol",
    "validate_side",
    "validate_order_type",
    "validate_quantity",
    "validate_price",
    "validate_stop_price",
    "validate_order_inputs",
]
VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET", "STOP_LIMIT"]
# Core required: MARKET, LIMIT - bonus adds STOP_LIMIT etc.
CORE_ORDER_TYPES = ["MARKET", "LIMIT"]

VALID_SYMBOLS_PATTERN = re.compile(r"^[A-Z0-9]{6,20}$")  # e.g., BTCUSDT

class ValidationError(Exception):
    """Custom validation exception"""
    pass

def validate_symbol(symbol: str) -> str:
    """Validate trading symbol"""
    if not symbol:
        raise ValidationError("Symbol is required")
    symbol = symbol.upper().strip()
    if not VALID_SYMBOLS_PATTERN.match(symbol):
        raise ValidationError(f"Invalid symbol format: {symbol}. Expected e.g., BTCUSDT")
    # Non-USDT quote assets are allowed on Binance Futures (e.g., BTCBUSD)
    return symbol

def validate_side(side: str) -> str:
    """Validate order side"""
    if not side:
        raise ValidationError("Side is required")
    side = side.upper().strip()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be BUY or SELL")
    return side

def validate_order_type(order_type: str) -> str:
    """Validate order type"""
    if not order_type:
        raise ValidationError("Order type is required")
    order_type = order_type.upper().strip()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Invalid order type '{order_type}'. Valid: {', '.join(VALID_ORDER_TYPES)}")
    return order_type

def validate_quantity(quantity) -> float:
    """Validate quantity"""
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be numeric, got: {quantity}")
    
    if qty <= 0:
        raise ValidationError("Quantity must be greater than 0")
    
    # Binance futures minimums vary, but basic sanity check
    if qty > 1000000:
        raise ValidationError("Quantity unrealistically large")
    
    return qty

def validate_price(price, required: bool = False) -> Optional[float]:
    """Validate price"""
    if price is None or price == "":
        if required:
            raise ValidationError("Price is required for LIMIT orders")
        return None
    
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValidationError(f"Price must be numeric, got: {price}")
    
    if p <= 0:
        raise ValidationError("Price must be greater than 0")
    
    return p

def validate_stop_price(stop_price, required: bool = False) -> Optional[float]:
    """Validate stop price for stop orders"""
    if stop_price is None or stop_price == "":
        if required:
            raise ValidationError("stopPrice is required for STOP/STOP_LIMIT orders")
        return None
    return validate_price(stop_price, required=True)

def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None
) -> OrderParams:
    """
    Comprehensive order validation
    Returns cleaned dict or raises ValidationError
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    
    clean_price = None
    clean_stop = None
    
    # Price required for LIMIT orders
    if clean_type == "LIMIT":
        clean_price = validate_price(price, required=True)
    elif clean_type in ["STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]:
        clean_stop = validate_stop_price(stop_price, required=True)
    elif clean_type == "STOP_LIMIT":
        clean_price = validate_price(price, required=True)
        clean_stop = validate_stop_price(stop_price, required=True)
    else:  # MARKET
        # Price optional / ignored
        if price:
            clean_price = validate_price(price, required=False)
    
    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "type": clean_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stopPrice": clean_stop
    }
