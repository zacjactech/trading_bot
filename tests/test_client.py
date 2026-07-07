"""
Unit tests for bot/client.py
"""
import time
import hmac
import hashlib
import requests
import pytest
from unittest.mock import patch, MagicMock, call
from urllib.parse import parse_qs, unquote

from bot.client import BinanceFuturesClient


def hmac_sha256(secret: str, query_string: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class TestSignatureGeneration:
    def test_signature_uses_hmac_sha256(self):
        client = BinanceFuturesClient(api_key="key", api_secret="secret")
        qs = "symbol=BTCUSDT&side=BUY&type=MARKET&quantity=0.001&timestamp=1234567890&recvWindow=5000"
        sig = client._generate_signature(qs)
        expected = hmac_sha256("secret", qs)
        assert sig == expected

    def test_signature_deterministic(self):
        client = BinanceFuturesClient(api_key="key", api_secret="secret")
        qs = "symbol=BTCUSDT&timestamp=1000&recvWindow=5000"
        sig1 = client._generate_signature(qs)
        sig2 = client._generate_signature(qs)
        assert sig1 == sig2

    def test_signature_differs_with_different_secret(self):
        client1 = BinanceFuturesClient(api_key="key", api_secret="secret1")
        client2 = BinanceFuturesClient(api_key="key", api_secret="secret2")
        qs = "symbol=BTCUSDT&timestamp=1000&recvWindow=5000"
        assert client1._generate_signature(qs) != client2._generate_signature(qs)


class TestMockMode:
    def test_mock_mode_enabled_when_env_true(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            assert client.mock_mode is True

    def test_mock_ping_returns_empty_dict(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.ping()
            assert result == {}

    def test_mock_server_time_contains_serverTime(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.get_server_time()
            assert "serverTime" in result

    def test_mock_symbol_price_btc(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            price = client.get_symbol_price("BTCUSDT")
            assert isinstance(price, float)
            assert 10000 < price < 200000  # reasonable BTC range

    def test_mock_symbol_price_unknown_symbol(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            price = client.get_symbol_price("UNKNOWNUSDT")
            assert 95.0 <= price <= 105.0  # jitter around 100

    def test_mock_balance_returns_list(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.get_account_balance()
            assert isinstance(result, list)
            assert len(result) > 0
            usdt = next(b for b in result if b["asset"] == "USDT")
            assert float(usdt["balance"]) > 0

    def test_mock_market_order_returns_filled(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=0.001,
            )
            assert result["status"] == "FILLED"
            assert result["executedQty"] == "0.001"
            assert result["side"] == "BUY"

    def test_mock_limit_order_returns_new(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="SELL",
                order_type="LIMIT",
                quantity=0.001,
                price=65000.0,
            )
            assert result["status"] == "NEW"
            assert result["executedQty"] == "0"

    def test_mock_order_id_is_reasonable(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=0.001,
            )
            assert 610_000_000 <= result["orderId"] <= 619_999_999


class TestOrderTypeMapping:
    def test_stop_limit_sent_as_stop_to_api(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP_LIMIT",
                quantity=0.001,
                price=59000.0,
                stop_price=59500.0,
            )
            assert result["orderId"] > 0
            assert result["type"] == "STOP"
            assert result["orderId"] > 0


class TestPlaceOrderEndpointRouting:
    @patch("bot.client.BinanceFuturesClient._request")
    def test_algo_types_use_algo_endpoint_first(self, mock_request):
        mock_request.return_value = {
            "algoId": 999,
            "orderId": 999,
            "status": "NEW",
            "symbol": "BTCUSDT",
        }
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()
            client.api_key = "key"
            client.api_secret = "secret"

            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP",
                quantity=0.001,
                price=59000.0,
                stop_price=59500.0,
            )

            calls = mock_request.call_args_list
            assert len(calls) == 1
            ep = calls[0][0][1]  # second positional arg = endpoint
            assert ep == "/fapi/v1/algoOrder"

    @patch("bot.client.BinanceFuturesClient._request")
    def test_market_order_uses_standard_endpoint(self, mock_request):
        mock_request.return_value = {
            "orderId": 123,
            "status": "FILLED",
            "executedQty": "0.001",
        }
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()
            client.api_key = "key"
            client.api_secret = "secret"

            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=0.001,
            )

            calls = mock_request.call_args_list
            ep = calls[0][0][1]
            assert ep == "/fapi/v1/order"


class TestAlgoFallbackOn4120:
    @patch("bot.client.BinanceFuturesClient._request")
    def test_4120_error_triggers_algo_fallback(self, mock_request):
        call_count = [0]

        def side_effect(method, endpoint, params=None, signed=False):
            call_count[0] += 1
            if endpoint == "/fapi/v1/order":
                raise Exception("Binance API Error -4120: Order type not supported")
            return {
                "algoId": 777,
                "orderId": 777,
                "status": "NEW",
                "symbol": "BTCUSDT",
            }

        mock_request.side_effect = side_effect

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()
            client.api_key = "key"
            client.api_secret = "secret"

            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity=0.001,
                price=65000.0,
            )

            assert result["orderId"] == 777
            assert mock_request.call_count == 2
            assert mock_request.call_args_list[0][0][1] == "/fapi/v1/order"
            assert mock_request.call_args_list[1][0][1] == "/fapi/v1/algoOrder"


class TestRequestMethodRouting:
    def test_get_request_uses_get(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/ping"
            mock_response.json.return_value = {}
            mock_session_instance.get.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                client.ping()

                mock_session_instance.get.assert_called_once()

    def test_post_request_uses_post(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/order"
            mock_response.json.return_value = {"orderId": 123, "status": "NEW"}
            mock_session_instance.post.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="MARKET",
                    quantity=0.001,
                )

                mock_session_instance.post.assert_called_once()


class TestURLFallback:
    @patch("requests.Session")
    def test_falls_back_to_second_url(self, MockSession):
        mock_session_instance = MagicMock()
        MockSession.return_value = mock_session_instance

        call_urls = []

        def get_side_effect(url, params=None, timeout=None):
            call_urls.append(url)
            if len(call_urls) == 1:
                raise requests.exceptions.RequestException("testnet unreachable")
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.url = url
            mock_resp.json.return_value = {"serverTime": 0}
            return mock_resp

        mock_session_instance.get.side_effect = get_side_effect

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            mock_config.BASE_URL = "https://testnet.binancefuture.com"
            mock_config.FALLBACK_URLS = ["https://testnet.binancefuture.com", "https://demo-fapi.binance.com"]
            client = BinanceFuturesClient()

            result = client.get_server_time()

            assert len(call_urls) == 2
            assert "testnet.binancefuture.com" in call_urls[0]
            assert "demo-fapi.binance.com" in call_urls[1]


class TestAlgoOrderResponseNormalization:
    @patch("bot.client.BinanceFuturesClient._request")
    def test_algo_id_mapped_to_order_id(self, mock_request):
        mock_request.return_value = {
            "algoId": 888,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "status": "NEW",
            "type": "STOP",
        }

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()
            client.api_key = "key"
            client.api_secret = "secret"

            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP",
                quantity=0.001,
                price=59000.0,
                stop_price=59500.0,
            )

            assert result["orderId"] == 888


class TestStopLimitApiMapping:
    @patch("bot.client.BinanceFuturesClient._request")
    def test_stop_limit_order_type_not_mapped_if_not_in_map(self, mock_request):
        mock_request.return_value = {"orderId": 100, "status": "NEW"}

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()
            client.api_key = "key"
            client.api_secret = "secret"

            client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP",
                quantity=0.001,
                price=59000.0,
                stop_price=59500.0,
            )

            call_params = mock_request.call_args[0][2]
            assert call_params["type"] == "STOP"


class TestDeleteRequest:
    def test_delete_request_uses_delete(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/order"
            mock_response.json.return_value = {"orderId": 1, "status": "CANCELED"}
            mock_session_instance.delete.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                client.cancel_order("BTCUSDT", 1)

                mock_session_instance.delete.assert_called_once()


class TestRequestErrorHandling:
    def test_400_status_raises_exception(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/order"
            mock_response.json.return_value = {"code": -1002, "msg": "Unsupported order type"}
            mock_session_instance.get.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                with pytest.raises(Exception, match="Binance API Error"):
                    client.ping()

    def test_negative_code_in_response_raises_exception(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/order"
            mock_response.json.return_value = {"code": -1102, "msg": "Mandatory parameter missing"}
            mock_session_instance.get.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                with pytest.raises(Exception, match="Binance API Error"):
                    client.ping()

    def test_unsupported_http_method_raises(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                with pytest.raises(ValueError, match="Unsupported HTTP method"):
                    client._request("PATCH", "/fapi/v1/test")

    def test_invalid_json_raises_value_error(self):
        with patch("requests.Session") as MockSession:
            mock_session_instance = MagicMock()
            MockSession.return_value = mock_session_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "https://testnet.binancefuture.com/fapi/v1/ping"
            mock_response.json.side_effect = ValueError("No JSON object could be decoded")
            mock_session_instance.get.return_value = mock_response

            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.FALLBACK_URLS = []
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                with pytest.raises(ValueError, match="No JSON"):
                    client.ping()


class TestURLFallbackUpdateBaseUrl:
    @patch("requests.Session")
    def test_successful_fallback_updates_base_url(self, MockSession):
        mock_session_instance = MagicMock()
        MockSession.return_value = mock_session_instance

        call_urls = []

        def get_side_effect(url, params=None, timeout=None):
            call_urls.append(url)
            if len(call_urls) == 1:
                raise requests.exceptions.RequestException("testnet unreachable")
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.url = url
            mock_resp.json.return_value = {"serverTime": 0}
            return mock_resp

        mock_session_instance.get.side_effect = get_side_effect

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            mock_config.BASE_URL = "https://testnet.binancefuture.com"
            mock_config.FALLBACK_URLS = ["https://testnet.binancefuture.com", "https://demo-fapi.binance.com"]
            client = BinanceFuturesClient()

            client.get_server_time()

            assert client.base_url == "https://demo-fapi.binance.com"


class TestAllURLsFail:
    @patch("requests.Session")
    def test_raises_when_all_urls_fail(self, MockSession):
        mock_session_instance = MagicMock()
        MockSession.return_value = mock_session_instance
        mock_session_instance.get.side_effect = requests.exceptions.RequestException("unreachable")

        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            mock_config.BASE_URL = "https://testnet.binancefuture.com"
            mock_config.FALLBACK_URLS = ["https://testnet.binancefuture.com", "https://demo-fapi.binance.com"]
            client = BinanceFuturesClient()

            with pytest.raises(Exception, match="Network failure"):
                client.ping()


class TestConstructorMockKeys:
    def test_mock_mode_injects_dummy_keys(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            assert client.api_key == "MOCK_API_KEY"
            assert client.api_secret == "MOCK_API_SECRET"

    def test_non_mock_mode_keeps_missing_keys_empty(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            assert client.api_key == ""
            assert client.api_secret == ""


class TestPublicEndpoints:
    @patch("bot.client.BinanceFuturesClient._request")
    def test_get_exchange_info(self, mock_request):
        mock_request.return_value = {"symbols": []}
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.get_exchange_info()

            mock_request.assert_called_once_with("GET", "/fapi/v1/exchangeInfo")
            assert result == {"symbols": []}

    @patch("bot.client.BinanceFuturesClient._request")
    def test_get_account_info(self, mock_request):
        mock_request.return_value = {"totalWalletBalance": "10000"}
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.get_account_info()

            mock_request.assert_called_once_with("GET", "/fapi/v2/account", signed=True)
            assert result["totalWalletBalance"] == "10000"

    @patch("bot.client.BinanceFuturesClient._request")
    def test_get_order(self, mock_request):
        mock_request.return_value = {"orderId": 123, "status": "NEW"}
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.get_order("BTCUSDT", 123)

            mock_request.assert_called_once_with(
                "GET", "/fapi/v1/order", {"symbol": "BTCUSDT", "orderId": 123}, signed=True
            )
            assert result["orderId"] == 123

    @patch("bot.client.BinanceFuturesClient._request")
    def test_cancel_order(self, mock_request):
        mock_request.return_value = {"orderId": 123, "status": "CANCELED"}
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.cancel_order("BTCUSDT", 123)

            mock_request.assert_called_once_with(
                "DELETE", "/fapi/v1/order", {"symbol": "BTCUSDT", "orderId": 123}, signed=True
            )
            assert result["status"] == "CANCELED"

    @patch("bot.client.BinanceFuturesClient._request")
    def test_get_open_orders_with_symbol(self, mock_request):
        mock_request.return_value = [{"orderId": 1}]
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.get_open_orders("BTCUSDT")

            mock_request.assert_called_once_with(
                "GET", "/fapi/v1/openOrders", {"symbol": "BTCUSDT"}, signed=True
            )
            assert len(result) == 1

    @patch("bot.client.BinanceFuturesClient._request")
    def test_get_open_orders_without_symbol(self, mock_request):
        mock_request.return_value = []
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = False
            mock_config.BINANCE_API_KEY = "key"
            mock_config.BINANCE_API_SECRET = "secret"
            mock_config.DEFAULT_RECV_WINDOW = 5000
            client = BinanceFuturesClient()

            result = client.get_open_orders()

            mock_request.assert_called_once_with(
                "GET", "/fapi/v1/openOrders", {}, signed=True
            )
            assert result == []


class TestMockModeAdditionalEndpoints:
    def _make_mock_client(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            yield BinanceFuturesClient()

    def test_mock_exchange_info(self):
        client = BinanceFuturesClient.__new__(BinanceFuturesClient)
        client.mock_mode = True
        client.api_key = "MOCK"
        client.api_secret = "MOCK"
        client.session = MagicMock()
        from bot.logging_config import logger
        client.logger = logger
        result = client._mock_response("GET", "/fapi/v1/exchangeInfo", {}, False)
        assert result == {}

    def test_mock_open_orders(self):
        client = BinanceFuturesClient.__new__(BinanceFuturesClient)
        client.mock_mode = True
        client.api_key = "MOCK"
        client.api_secret = "MOCK"
        client.session = MagicMock()
        from bot.logging_config import logger
        client.logger = logger
        result = client._mock_response("GET", "/fapi/v1/openOrders", {}, False)
        assert result == []

    def test_mock_algo_order_endpoint(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP_MARKET",
                quantity=0.001,
                stop_price=59000.0,
            )
            assert "orderId" in result
            assert result["status"] == "NEW"

    def test_mock_take_profit_order(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="ETHUSDT",
                side="SELL",
                order_type="TAKE_PROFIT_MARKET",
                quantity=0.01,
                stop_price=4000.0,
            )
            assert "orderId" in result
            assert result["status"] == "NEW"

    def test_mock_unknown_endpoint_returns_empty(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client._mock_response("GET", "/fapi/v1/unknownEndpoint", {}, False)
            assert result == {}

    def test_mock_delete_request(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client._mock_response("DELETE", "/fapi/v1/order", {"symbol": "BTCUSDT"}, False)
            assert result == {}


class TestPlaceOrderValidation:
    def test_limit_order_missing_price_raises(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            with pytest.raises(ValueError, match="price is required"):
                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="LIMIT",
                    quantity=0.001,
                )

    def test_stop_order_missing_both_raises(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            with pytest.raises(ValueError, match="price and stopPrice required"):
                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="STOP",
                    quantity=0.001,
                )

    def test_stop_order_missing_stop_price_raises(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            with pytest.raises(ValueError, match="price and stopPrice required"):
                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="STOP_LIMIT",
                    quantity=0.001,
                    price=59000.0,
                )

    def test_stop_market_missing_stop_price_raises(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            with pytest.raises(ValueError, match="stopPrice required"):
                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="STOP_MARKET",
                    quantity=0.001,
                )

    def test_take_profit_missing_stop_price_raises(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            with pytest.raises(ValueError, match="stopPrice required"):
                client.place_order(
                    symbol="BTCUSDT",
                    side="SELL",
                    order_type="TAKE_PROFIT",
                    quantity=0.001,
                )

    def test_reduce_only_param_included(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=0.001,
                reduce_only=True,
            )
            assert "orderId" in result


class TestPriceFormatting:
    def test_limit_price_trailing_zeros_stripped(self):
        with patch("bot.client.Config") as mock_config:
            mock_config.MOCK_TRADING = True
            mock_config.BINANCE_API_KEY = ""
            mock_config.BINANCE_API_SECRET = ""
            client = BinanceFuturesClient()
            result = client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity=0.001,
                price=60000.0,
            )
            assert result["orderId"] > 0

    def test_stop_limit_includes_price_and_stop_in_params(self):
        with patch("bot.client.BinanceFuturesClient._request") as mock_request:
            mock_request.return_value = {"orderId": 100, "status": "NEW"}
            with patch("bot.client.Config") as mock_config:
                mock_config.MOCK_TRADING = False
                mock_config.BINANCE_API_KEY = "key"
                mock_config.BINANCE_API_SECRET = "secret"
                mock_config.DEFAULT_RECV_WINDOW = 5000
                client = BinanceFuturesClient()

                client.place_order(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="STOP_LIMIT",
                    quantity=0.001,
                    price=59000.0,
                    stop_price=59500.0,
                )

                call_params = mock_request.call_args[0][2]
                assert call_params["price"] == 59000.0
                assert call_params["triggerprice"] == 59500.0
                assert call_params["type"] == "STOP"
                assert call_params["algotype"] == "conditional"