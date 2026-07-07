# Binance Futures Trading Bot Package
__version__ = "1.0.0"

from .client import BinanceFuturesClient
from .orders import OrderManager
from .config import Config

__all__ = ["BinanceFuturesClient", "OrderManager", "Config", "__version__"]
