"""
Unit tests for bot/orders.py
"""
import pytest
from unittest.mock import patch, MagicMock
from bot.orders import OrderManager, print_order_request, print_order_response, ValidationError


class TestOrderManagerMarket:
    def test_place_market_order_success(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = sample_market_order_response

            manager = OrderManager(client=mock_instance)
            result = manager.place_market_order("BTCUSDT", "BUY", 0.001)

            mock_instance.place_order.assert_called_once_with(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=0.001,
                price=None,
                stop_price=None,
                time_in_force="GTC",
            )
            assert result["orderId"] == 612345678
            assert result["status"] == "FILLED"

    def test_place_market_order_validation_error(self):
        manager = OrderManager(client=MagicMock())
        with pytest.raises(ValidationError):
            manager.place_market_order("", "BUY", 0.001)


class TestOrderManagerLimit:
    def test_place_limit_order_success(self, sample_limit_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = sample_limit_order_response

            manager = OrderManager(client=mock_instance)
            result = manager.place_limit_order("BTCUSDT", "SELL", 0.001, 65000.0)

            mock_instance.place_order.assert_called_once()
            call_kwargs = mock_instance.place_order.call_args.kwargs
            assert call_kwargs["symbol"] == "BTCUSDT"
            assert call_kwargs["order_type"] == "LIMIT"
            assert call_kwargs["price"] == 65000.0
            assert result["status"] == "NEW"


class TestOrderManagerStopLimit:
    def test_place_stop_limit_order_success(self, sample_limit_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            sample_limit_order_response["type"] = "STOP"
            mock_instance.place_order.return_value = sample_limit_order_response

            manager = OrderManager(client=mock_instance)
            result = manager.place_stop_limit_order(
                "BTCUSDT", "BUY", 0.001, 59000.0, 59500.0
            )
            call_kwargs = mock_instance.place_order.call_args.kwargs
            assert call_kwargs["stop_price"] == 59500.0
            assert call_kwargs["price"] == 59000.0


class TestOrderManagerTwap:
    def test_place_twap_splits_into_slices(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = sample_market_order_response

            manager = OrderManager(client=mock_instance)
            results = manager.place_twap_order("BTCUSDT", "BUY", 0.003, slices=3, interval_seconds=2)

            assert len(results) == 3
            assert mock_instance.place_order.call_count == 3

    def test_place_twap_last_slice_adjusts_rounding(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            sample_market_order_response["executedQty"] = "0.002"
            mock_instance.place_order.return_value = sample_market_order_response

            manager = OrderManager(client=mock_instance)
            results = manager.place_twap_order("BTCUSDT", "BUY", 0.006, slices=3)

            calls = mock_instance.place_order.call_args_list
            last_qty = calls[2][1]["quantity"]
            assert last_qty == 0.002

    def test_place_twap_continues_on_slice_failure(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.side_effect = [
                sample_market_order_response,
                Exception("API Error"),
                sample_market_order_response,
            ]

            manager = OrderManager(client=mock_instance)
            results = manager.place_twap_order("BTCUSDT", "BUY", 0.003, slices=3)

            assert len(results) == 3
            assert "orderId" in results[0]
            assert "error" in results[1]
            assert "orderId" in results[2]


class TestOrderManagerGrid:
    def test_place_grid_orders_price_step(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = {"orderId": 123}

            manager = OrderManager(client=mock_instance)
            results = manager.place_grid_orders(
                "BTCUSDT", "BUY", 0.001, lower_price=60000.0, upper_price=62000.0, grids=5
            )

            assert len(results) == 5
            assert mock_instance.place_order.call_count == 5

            calls = mock_instance.place_order.call_args_list
            # Grid prices: 60000, 60500, 61000, 61500, 62000
            prices = [call[1]["price"] for call in calls]
            assert prices[0] == 60000.0
            assert prices[2] == 61000.0
            assert prices[4] == 62000.0

    def test_place_grid_lower_equal_upper_raises(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            manager = OrderManager(client=MockClient.return_value)
            with pytest.raises(ValidationError, match="lower_price must be < upper_price"):
                manager.place_grid_orders("BTCUSDT", "BUY", 0.001, 62000.0, 60000.0, grids=5)

    def test_place_grid_continues_on_failure(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.side_effect = [
                {"orderId": 1},
                Exception("fail"),
                {"orderId": 3},
            ]

            manager = OrderManager(client=mock_instance)
            results = manager.place_grid_orders(
                "BTCUSDT", "BUY", 0.001, lower_price=60000.0, upper_price=62000.0, grids=3
            )

            assert len(results) == 3
            assert results[1]["error"] == "fail"


class TestPrintFunctions:
    def test_print_order_request_does_not_raise(self):
        order = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": 0.001,
            "price": None,
            "stopPrice": None,
        }
        print_order_request(order)  # should not raise

    def test_print_order_request_with_price_and_stop(self):
        order = {
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "STOP_LIMIT",
            "quantity": 0.001,
            "price": 59000.0,
            "stopPrice": 59500.0,
        }
        print_order_request(order)  # should not raise

    def test_print_order_response_filled(self):
        resp = {
            "orderId": 123,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "status": "FILLED",
            "executedQty": "0.001",
            "avgPrice": "60500.0",
        }
        print_order_response(resp)  # should not raise

    def test_print_order_response_new_no_price(self):
        resp = {
            "orderId": 456,
            "symbol": "BTCUSDT",
            "side": "SELL",
            "type": "LIMIT",
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
            "price": "65000",
        }
        print_order_response(resp)  # should not raise

    def test_print_order_response_partially_filled(self):
        resp = {
            "orderId": 789,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "status": "PARTIALLY_FILLED",
            "executedQty": "0.0005",
            "avgPrice": "60000.0",
            "price": "60000.0",
            "cumQuote": "30.0",
        }
        print_order_response(resp)

    def test_print_order_response_missing_optional_fields(self):
        resp = {
            "orderId": 101,
            "symbol": "ETHUSDT",
            "side": "SELL",
            "type": "MARKET",
            "status": "FILLED",
            "executedQty": "0.01",
            "avgPrice": "3400.0",
        }
        print_order_response(resp)

    def test_print_order_response_no_order_id(self):
        resp = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "status": "REJECTED",
            "executedQty": "0",
        }
        print_order_response(resp)

    def test_print_order_response_with_cum_quote(self):
        resp = {
            "orderId": 202,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "status": "FILLED",
            "executedQty": "0.001",
            "avgPrice": "60500.0",
            "price": "0",
            "cumQuote": "60.50",
        }
        print_order_response(resp)


class TestOrderManagerStopMarket:
    def test_place_stop_market_order_success(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = {
                "orderId": 301,
                "status": "NEW",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "STOP_MARKET",
            }

            manager = OrderManager(client=mock_instance)
            result = manager.place_stop_market_order("BTCUSDT", "BUY", 0.001, 59500.0)

            call_kwargs = mock_instance.place_order.call_args.kwargs
            assert call_kwargs["stop_price"] == 59500.0
            assert result["orderId"] == 301

    def test_place_stop_market_order_validation_error(self):
        manager = OrderManager(client=MagicMock())
        with pytest.raises(ValidationError):
            manager.place_stop_market_order("BTCUSDT", "BUY", 0.001, stop_price=None)


class TestOrderManagerGridEdgeCases:
    def test_place_grid_one_grid(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = {"orderId": 400}

            manager = OrderManager(client=mock_instance)
            results = manager.place_grid_orders(
                "BTCUSDT", "BUY", 0.001, lower_price=60000.0, upper_price=62000.0, grids=1
            )

            assert len(results) == 1
            assert mock_instance.place_order.call_count == 1

    def test_place_grid_two_grids(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = {"orderId": 401}

            manager = OrderManager(client=mock_instance)
            results = manager.place_grid_orders(
                "BTCUSDT", "BUY", 0.001, lower_price=60000.0, upper_price=62000.0, grids=2
            )

            assert len(results) == 2
            calls = mock_instance.place_order.call_args_list
            prices = [call[1]["price"] for call in calls]
            assert prices[0] == 60000.0
            assert prices[1] == 62000.0


class TestOrderManagerExecuteOrderException:
    def test_execute_order_client_exception_propagates(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.side_effect = Exception("Connection timeout")

            manager = OrderManager(client=mock_instance)
            with pytest.raises(Exception, match="Connection timeout"):
                manager.place_market_order("BTCUSDT", "BUY", 0.001)

    def test_execute_order_validation_error_propagates(self):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value

            manager = OrderManager(client=mock_instance)
            with pytest.raises(ValidationError):
                manager.place_limit_order("BTCUSDT", "SELL", 0.001, price=None)


class TestOrderManagerTwapEdgeCases:
    def test_place_twap_single_slice(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.return_value = sample_market_order_response

            manager = OrderManager(client=mock_instance)
            results = manager.place_twap_order("BTCUSDT", "BUY", 0.001, slices=1)

            assert len(results) == 1
            assert mock_instance.place_order.call_count == 1

    def test_place_twap_validation_error_continues(self, sample_market_order_response):
        with patch("bot.orders.BinanceFuturesClient") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.place_order.side_effect = [
                sample_market_order_response,
                ValidationError("Invalid symbol"),
                sample_market_order_response,
            ]

            manager = OrderManager(client=mock_instance)
            results = manager.place_twap_order("BTCUSDT", "BUY", 0.003, slices=3)

            assert len(results) == 3
            assert "orderId" in results[0]
            assert "error" in results[1]
            assert "orderId" in results[2]