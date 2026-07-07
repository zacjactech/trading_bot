"""
Shared pytest fixtures
"""
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("BINANCE_API_KEY", "test_key_123")
os.environ.setdefault("BINANCE_API_SECRET", "test_secret_456")
os.environ.setdefault("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
os.environ.setdefault("MOCK_TRADING", "false")


@pytest.fixture
def mock_requests_session():
    """Patch requests.Session to avoid real HTTP calls"""
    with patch("requests.Session") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_balance_response():
    return [
        {
            "accountAlias": "test_user",
            "asset": "USDT",
            "balance": "15234.56789012",
            "crossWalletBalance": "15234.56789012",
            "crossUnPnl": "0.00000000",
            "availableBalance": "14850.12345678",
            "maxWithdrawAmount": "14850.12345678",
            "marginAvailable": True,
            "updateTime": 0,
        },
        {
            "accountAlias": "test_user",
            "asset": "BNB",
            "balance": "0.50000000",
            "crossWalletBalance": "0.50000000",
            "crossUnPnl": "0.00000000",
            "availableBalance": "0.50000000",
            "maxWithdrawAmount": "0.50000000",
            "marginAvailable": True,
            "updateTime": 0,
        },
    ]


@pytest.fixture
def sample_market_order_response():
    return {
        "clientOrderId": "mock_client_123",
        "cumQty": "0.001",
        "cumQuote": "60.50",
        "executedQty": "0.001",
        "orderId": 612345678,
        "avgPrice": "60500.00",
        "origQty": "0.001",
        "price": "0",
        "reduceOnly": False,
        "side": "BUY",
        "positionSide": "BOTH",
        "status": "FILLED",
        "stopPrice": "0",
        "closePosition": False,
        "symbol": "BTCUSDT",
        "time": 0,
        "timeInForce": "GTC",
        "type": "MARKET",
        "origType": "MARKET",
        "activatePrice": "0",
        "priceRate": "0",
        "updateTime": 0,
        "workingType": "CONTRACT_PRICE",
        "priceProtect": False,
        "priceMatch": "NONE",
        "selfTradePreventionMode": "EXPIRE_MAKER",
        "goodTillDate": 0,
    }


@pytest.fixture
def sample_limit_order_response():
    return {
        "clientOrderId": "mock_client_456",
        "cumQty": "0",
        "cumQuote": "0",
        "executedQty": "0",
        "orderId": 612345679,
        "avgPrice": "0",
        "origQty": "0.001",
        "price": "65000.00",
        "reduceOnly": False,
        "side": "SELL",
        "positionSide": "BOTH",
        "status": "NEW",
        "stopPrice": "0",
        "closePosition": False,
        "symbol": "BTCUSDT",
        "time": 0,
        "timeInForce": "GTC",
        "type": "LIMIT",
        "origType": "LIMIT",
        "activatePrice": "0",
        "priceRate": "0",
        "updateTime": 0,
        "workingType": "CONTRACT_PRICE",
        "priceProtect": False,
        "priceMatch": "NONE",
        "selfTradePreventionMode": "EXPIRE_MAKER",
        "goodTillDate": 0,
    }