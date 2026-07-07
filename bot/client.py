"""
Binance Futures Testnet API Client
Direct REST implementation with HMAC-SHA256 signing
Base URL: https://testnet.binancefuture.com

Also includes optional python-binance wrapper fallback.
"""
import time
import hmac
import hashlib
import random
import re
import requests
from urllib.parse import urlencode
from typing import Dict, Any, Optional

from .logging_config import logger
from .config import Config


class BinanceFuturesClient:
    """
    Binance USDT-M Futures Testnet Client
    Handles signing, requests, error handling, logging
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, base_url: str = None):
        self.api_key = api_key or Config.BINANCE_API_KEY
        self.api_secret = api_secret or Config.BINANCE_API_SECRET
        self.base_url = (base_url or Config.BASE_URL).rstrip("/")
        self.mock_mode = Config.MOCK_TRADING
        
        if self.mock_mode:
            logger.warning("⚠️  MOCK_TRADING mode enabled – orders will be simulated, not sent to Binance")
        
        if not self.api_key or not self.api_secret:
            if not self.mock_mode:
                logger.warning("API credentials missing - client will fail on signed endpoints. Enable MOCK_TRADING=true for offline demo")
            else:
                # inject dummy keys for mock mode
                self.api_key = self.api_key or "MOCK_API_KEY"
                self.api_secret = self.api_secret or "MOCK_API_SECRET"
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        logger.info(f"BinanceFuturesClient initialized | base_url={self.base_url} | mock={self.mock_mode}")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict[str, Any]:
        """
        Make API request with logging and error handling
        Supports mock mode + automatic URL fallback for testnet migration
        """
        if params is None:
            params = {}
        
        # MOCK MODE – return simulated data for offline demo
        if self.mock_mode:
            return self._mock_response(method, endpoint, params, signed)
        
        # Add timestamp for signed requests
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = Config.DEFAULT_RECV_WINDOW
            query_string = urlencode(params)
            signature = self._generate_signature(query_string)
            params["signature"] = signature
        
        # Try primary URL, then fallbacks (Binance testnet migration 2025)
        urls_to_try = [self.base_url] + [u for u in Config.FALLBACK_URLS if u != self.base_url]
        last_error = None
        
        for attempt_url in urls_to_try:
            url = f"{attempt_url}{endpoint}"
            logger.info(f"API REQUEST | {method} {endpoint} | base={attempt_url} | params={ {k:v for k,v in params.items() if k != 'signature'} }")
            
            try:
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=10)
                elif method == "POST":
                    response = self.session.post(url, params=params, timeout=10)
                elif method == "DELETE":
                    response = self.session.delete(url, params=params, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                safe_url = re.sub(r'&signature=[^&]+', '', response.url)
                logger.info(f"API RESPONSE | status={response.status_code} | url={safe_url}")
                
                data = response.json()
                
                # Binance error handling
                if response.status_code >= 400 or "code" in data and data.get("code", 0) < 0:
                    error_msg = data.get("msg", "Unknown API error")
                    error_code = data.get("code", response.status_code)
                    logger.error(f"API ERROR | code={error_code} | msg={error_msg} | response={data}")
                    raise Exception(f"Binance API Error {error_code}: {error_msg}")
                
                # Success – update base_url if fallback worked
                if attempt_url != self.base_url:
                    logger.warning(f"Primary URL failed, succeeded with fallback: {attempt_url} – switching base_url")
                    self.base_url = attempt_url
                
                logger.info(f"API SUCCESS | endpoint={endpoint} | keys={list(data.keys()) if isinstance(data, dict) else 'list'}")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error on {attempt_url}: {e} – trying next fallback...")
                last_error = e
                continue
            except ValueError as e:
                logger.exception(f"JSON decode error: {e}")
                raise
        
        # All URLs failed
        logger.exception(f"All testnet URLs failed. Last error: {last_error}")
        # Provide helpful error with Nigeria-specific advice
        raise Exception(
            f"Network failure: Could not reach Binance Testnet. Tried: {', '.join(urls_to_try)}. "
            f"Last error: {last_error}. "
            f"Tip: Binance Testnet (testnet.binancefuture.com / demo.binance.com) may be geo-blocked in some regions including Nigeria. "
            f"Try: 1) VPN (US/SG/EU), 2) Change DNS to 8.8.8.8 / 1.1.1.1, 3) Mobile hotspot, 4) Enable MOCK_TRADING=true in .env for offline demo."
        )

    def _mock_response(self, method: str, endpoint: str, params: Dict, signed: bool) -> Dict[str, Any]:
        """Generate realistic mock responses for offline demo / blocked regions"""
        import random
        logger.info(f"MOCK API | {method} {endpoint} | params={params}")
        time.sleep(0.3)  # simulate latency
        
        # ping
        if endpoint == "/fapi/v1/ping":
            return {}
        if endpoint == "/fapi/v1/time":
            return {"serverTime": int(time.time() * 1000)}
        if endpoint == "/fapi/v1/ticker/price":
            symbol = params.get("symbol", "BTCUSDT")
            # realistic mock prices July 2026
            mock_prices = {"BTCUSDT": 116480.5, "ETHUSDT": 3420.0, "SOLUSDT": 148.5, "BNBUSDT": 610.0}
            price = mock_prices.get(symbol, 100.0)
            # add small jitter
            price = round(price * random.uniform(0.999, 1.001), 2)
            return {"symbol": symbol, "price": str(price), "time": int(time.time()*1000)}
        if endpoint == "/fapi/v2/balance":
            return [
                {"accountAlias": "test_user", "asset": "USDT", "balance": "15234.56789012", "crossWalletBalance": "15234.56789012", "crossUnPnl": "0.00000000", "availableBalance": "14850.12345678", "maxWithdrawAmount": "14850.12345678", "marginAvailable": True, "updateTime": int(time.time()*1000)},
                {"accountAlias": "test_user", "asset": "BNB", "balance": "0.50000000", "crossWalletBalance": "0.50000000", "crossUnPnl": "0.00000000", "availableBalance": "0.50000000", "maxWithdrawAmount": "0.50000000", "marginAvailable": True, "updateTime": int(time.time()*1000)}
            ]
        if endpoint == "/fapi/v1/openOrders":
            return []  # empty for mock
        if endpoint in ["/fapi/v1/order", "/fapi/v1/algoOrder"] and method == "POST":
            # Simulate order placement
            symbol = params.get("symbol", "BTCUSDT")
            side = params.get("side", "BUY")
            order_type = params.get("type", "MARKET")
            quantity = str(params.get("quantity", "0.001"))
            price = params.get("price", "0")
            
            # Get mock market price
            mock_price_map = {"BTCUSDT": 116482.5, "ETHUSDT": 3420.0}
            market_price = mock_price_map.get(symbol, 100.0)
            
            order_id = random.randint(610000000, 619999999)
            now_ms = int(time.time() * 1000)
            
            if order_type == "MARKET":
                status = "FILLED"
                executed_qty = quantity
                avg_price = str(market_price)
                cum_quote = str(float(quantity) * market_price)
            else:  # LIMIT etc
                status = "NEW"
                executed_qty = "0"
                avg_price = "0"
                cum_quote = "0"
            
            return {
                "clientOrderId": f"mock_{random.randint(100000,999999)}",
                "cumQty": executed_qty,
                "cumQuote": cum_quote,
                "executedQty": executed_qty,
                "orderId": order_id,
                "avgPrice": avg_price,
                "origQty": quantity,
                "price": str(price) if price != "0" else "0",
                "reduceOnly": False,
                "side": side,
                "positionSide": "BOTH",
                "status": status,
                "stopPrice": params.get("stopPrice", "0"),
                "closePosition": False,
                "symbol": symbol,
                "time": now_ms,
                "timeInForce": params.get("timeInForce", "GTC"),
                "type": order_type,
                "origType": order_type,
                "activatePrice": "0",
                "priceRate": "0",
                "updateTime": now_ms,
                "workingType": "CONTRACT_PRICE",
                "priceProtect": False,
                "priceMatch": "NONE",
                "selfTradePreventionMode": "EXPIRE_MAKER",
                "goodTillDate": 0
            }
        
        # default empty success
        return {}
    
    # Public endpoints
    def ping(self) -> Dict:
        """Test connectivity"""
        return self._request("GET", "/fapi/v1/ping")
    
    def get_server_time(self) -> Dict:
        return self._request("GET", "/fapi/v1/time")
    
    def get_exchange_info(self) -> Dict:
        return self._request("GET", "/fapi/v1/exchangeInfo")
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current mark price"""
        data = self._request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
        return float(data["price"])
    
    # Account endpoints (signed)
    def get_account_balance(self) -> Dict:
        return self._request("GET", "/fapi/v2/balance", signed=True)
    
    def get_account_info(self) -> Dict:
        return self._request("GET", "/fapi/v2/account", signed=True)
    
    # Order endpoints
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        stop_price: Optional[float] = None,
        reduce_only: bool = False,
        **extra_params
    ) -> Dict[str, Any]:
        """
        Place a futures order
        
        Args:
            symbol: e.g., BTCUSDT
            side: BUY or SELL
            order_type: MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, STOP_LIMIT
            quantity: order quantity
            price: limit price (required for LIMIT)
            time_in_force: GTC, IOC, FOK
            stop_price: trigger price for stop orders
        """
        # Binance Futures API type mapping
        # User-friendly / common names -> actual Binance Futures API type
        # STOP_LIMIT (standard across exchanges) is called STOP in Binance Futures USDT-M
        # STOP_MARKET stays STOP_MARKET, etc.
        api_type_map = {
            "STOP_LIMIT": "STOP",  # key fix for -1116 Invalid orderType
            "STOP_LOSS": "STOP",
            "STOP_LOSS_LIMIT": "STOP",
            "TAKE_PROFIT_LIMIT": "TAKE_PROFIT",
        }
        api_order_type = api_type_map.get(order_type, order_type)
        
        # Log mapping if translated
        if api_order_type != order_type:
            logger.info(f"Order type mapped: {order_type} -> {api_order_type} (Binance Futures API compatibility)")
        
        params = {
            "symbol": symbol,
            "side": side,
            "type": api_order_type,
            "quantity": quantity,
        }
        
        # Order type specific params
        # Use original order_type for logic branching, but api_order_type is sent
        if order_type == "LIMIT" or api_order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders")
            params["price"] = f"{price:.8f}".rstrip('0').rstrip('.') if '.' in f"{price:.8f}" else price
            params["timeInForce"] = time_in_force
        
        elif order_type in ["STOP_LIMIT", "STOP", "STOP_LOSS", "STOP_LOSS_LIMIT"]:
            # Binance Futures STOP = stop-limit order
            if price is None or stop_price is None:
                raise ValueError("price and stopPrice required for STOP / STOP_LIMIT orders")
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force
            # Ensure api type is STOP
            params["type"] = "STOP"
        
        elif order_type in ["STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET", "TAKE_PROFIT_LIMIT"]:
            if stop_price is None:
                raise ValueError(f"stopPrice required for {order_type}")
            params["stopPrice"] = stop_price
            # STOP_MARKET does NOT need price, timeInForce
            if api_order_type in ["TAKE_PROFIT", "STOP"] and price:
                # If price provided with STOP/TAKE_PROFIT, treat as limit version
                params["price"] = price
                params["timeInForce"] = time_in_force
        
        # MARKET orders need no price
        # reduceOnly
        if reduce_only:
            params["reduceOnly"] = "true"
        
        # merge extras
        params.update(extra_params)
        
        logger.info(f"Placing order | {side} {quantity} {symbol} | type={order_type} (api:{api_order_type}) | price={price} | stop={stop_price}")
        
        # Algo order types (Binance Dec 2025 migration)
        # STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
        # now require /fapi/v1/algoOrder endpoint, otherwise -4120
        algo_order_types = ["STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET", "TRAILING_STOP_MARKET"]
        is_algo = api_order_type in algo_order_types
        
        # First try standard order endpoint, fallback to algo if -4120
        endpoints_to_try = []
        if is_algo:
            # Try algo first for conditional orders (new Binance standard)
            endpoints_to_try = ["/fapi/v1/algoOrder", "/fapi/v1/order"]
        else:
            endpoints_to_try = ["/fapi/v1/order"]
        
        last_err = None
        for ep in endpoints_to_try:
            try:
                algo_params = params.copy()
                if ep == "/fapi/v1/algoOrder":
                    algo_params.setdefault("workingType", "CONTRACT_PRICE")
                    algo_params.setdefault("algotype", "conditional")
                    # Binance algo API uses triggerprice instead of stopPrice
                    if "stopPrice" in algo_params:
                        algo_params["triggerprice"] = algo_params.pop("stopPrice")
                    logger.info(f"Using Algo Order endpoint: {ep} for type {api_order_type}")

                result = self._request("POST", ep, algo_params, signed=True)

                if ep == "/fapi/v1/algoOrder" and "algoId" in result and "orderId" not in result:
                    result["orderId"] = result.get("algoId")
                    result.setdefault("status", "NEW")
                    result.setdefault("symbol", symbol)
                    result.setdefault("side", side)
                    result.setdefault("type", order_type)
                    result.setdefault("origQty", str(quantity))
                    result.setdefault("executedQty", "0")
                    result.setdefault("price", str(price or 0))

                logger.info(f"Order placed successfully | orderId={result.get('orderId')} | status={result.get('status')} | endpoint={ep}")
                return result

            except Exception as e:
                err_str = str(e)
                last_err = e
                if "-4120" in err_str and ep == "/fapi/v1/order" and "/fapi/v1/algoOrder" not in endpoints_to_try:
                    logger.warning("Order type -4120 – retrying via /fapi/v1/algoOrder (Binance Algo API migration)")
                    try:
                        algo_params = params.copy()
                        algo_params.setdefault("workingType", "CONTRACT_PRICE")
                        algo_params.setdefault("algotype", "conditional")
                        if "stopPrice" in algo_params:
                            algo_params["triggerprice"] = algo_params.pop("stopPrice")
                        result = self._request("POST", "/fapi/v1/algoOrder", algo_params, signed=True)
                        if "algoId" in result and "orderId" not in result:
                            result["orderId"] = result.get("algoId")
                            result.setdefault("status", "NEW")
                            result.setdefault("symbol", symbol)
                            result.setdefault("side", side)
                            result.setdefault("type", order_type)
                        logger.info(f"Algo order placed successfully | orderId={result.get('orderId')} | via /fapi/v1/algoOrder")
                        return result
                    except Exception as e2:
                        last_err = e2
                        logger.error(f"Algo fallback also failed: {e2}")
                        raise e2 from None

                if ep == endpoints_to_try[-1]:
                    raise
                logger.warning(f"Endpoint {ep} failed: {e} – trying next")
                continue

        raise last_err if last_err else Exception("Order placement failed – unknown error")
    
    def get_order(self, symbol: str, order_id: int) -> Dict:
        return self._request("GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        return self._request("DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> Dict:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params, signed=True)


# Optional: python-binance wrapper for users who prefer library
try:
    from binance.client import Client as BinanceLibraryClient
    from binance.exceptions import BinanceAPIException
    
    class BinanceLibraryWrapper:
        """Thin wrapper around python-binance for compatibility"""
        def __init__(self, api_key=None, api_secret=None):
            api_key = api_key or Config.BINANCE_API_KEY
            api_secret = api_secret or Config.BINANCE_API_SECRET
            self.client = BinanceLibraryClient(api_key, api_secret, testnet=True)
            # Force correct futures testnet URL
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
            logger.info("python-binance library client initialized")
        
        def place_order(self, **kwargs):
            return self.client.futures_create_order(**kwargs)

    LIBRARY_AVAILABLE = True
except ImportError:
    LIBRARY_AVAILABLE = False
    BinanceLibraryWrapper = None
    logger.warning("python-binance library not installed - using REST client only")
