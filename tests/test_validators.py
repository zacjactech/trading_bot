"""
Unit tests for bot/validators.py
"""
import pytest
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
    validate_order_inputs,
    ValidationError,
    VALID_SIDES,
    VALID_ORDER_TYPES,
)


class TestValidateSymbol:
    def test_valid_btcusdt(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_valid_lowercase_normalized(self):
        assert validate_symbol("btcusdt") == "BTCUSDT"

    def test_valid_with_spaces_stripped(self):
        assert validate_symbol("  ETHUSDT  ") == "ETHUSDT"

    def test_invalid_empty(self):
        with pytest.raises(ValidationError, match="Symbol is required"):
            validate_symbol("")

    def test_invalid_too_short(self):
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            validate_symbol("BTC")

    def test_invalid_special_chars(self):
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            validate_symbol("BTC-USDT")

    def test_valid_6_char_symbol(self):
        assert validate_symbol("XRPRLY") == "XRPRLY"


class TestValidateSide:
    def test_valid_buy(self):
        assert validate_side("BUY") == "BUY"
        assert validate_side("buy") == "BUY"

    def test_valid_sell(self):
        assert validate_side("SELL") == "SELL"
        assert validate_side("sell") == "SELL"

    def test_invalid_empty(self):
        with pytest.raises(ValidationError, match="Side is required"):
            validate_side("")

    def test_invalid_side(self):
        with pytest.raises(ValidationError, match="Invalid side"):
            validate_side("HOLD")


class TestValidateOrderType:
    def test_valid_market(self):
        assert validate_order_type("MARKET") == "MARKET"
        assert validate_order_type("market") == "MARKET"

    def test_valid_limit(self):
        assert validate_order_type("LIMIT") == "LIMIT"

    def test_valid_stop(self):
        assert validate_order_type("STOP") == "STOP"
        assert validate_order_type("STOP_LIMIT") == "STOP_LIMIT"

    def test_valid_others(self):
        for ot in VALID_ORDER_TYPES:
            assert validate_order_type(ot) == ot

    def test_invalid_empty(self):
        with pytest.raises(ValidationError, match="Order type is required"):
            validate_order_type("")

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="Invalid order type"):
            validate_order_type("FOK")


class TestValidateQuantity:
    def test_valid_integer(self):
        assert validate_quantity(1) == 1.0

    def test_valid_float(self):
        assert validate_quantity(0.001) == 0.001

    def test_valid_string_number(self):
        assert validate_quantity("0.5") == 0.5

    def test_invalid_zero(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity(0)

    def test_invalid_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_quantity(-1)

    def test_invalid_non_numeric(self):
        with pytest.raises(ValidationError, match="must be numeric"):
            validate_quantity("abc")

    def test_invalid_too_large(self):
        with pytest.raises(ValidationError, match="unrealistically large"):
            validate_quantity(1_500_000)


class TestValidatePrice:
    def test_valid_positive(self):
        assert validate_price(50000.0) == 50000.0
        assert validate_price("60000") == 60000.0

    def test_optional_none_returns_none(self):
        assert validate_price(None, required=False) is None

    def test_required_none_raises(self):
        with pytest.raises(ValidationError, match="Price is required"):
            validate_price(None, required=True)

    def test_invalid_zero(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price(0)

    def test_invalid_negative(self):
        with pytest.raises(ValidationError, match="must be greater than 0"):
            validate_price(-100)

    def test_invalid_non_numeric(self):
        with pytest.raises(ValidationError, match="Price must be numeric"):
            validate_price("abc")


class TestValidateStopPrice:
    def test_valid_positive(self):
        assert validate_stop_price(59000.0) == 59000.0

    def test_required_none_raises(self):
        with pytest.raises(ValidationError, match="stopPrice is required"):
            validate_stop_price(None, required=True)

    def test_optional_none_returns_none(self):
        assert validate_stop_price(None, required=False) is None


class TestValidateOrderInputs:
    def test_market_order_minimal(self):
        result = validate_order_inputs("BTCUSDT", "BUY", "MARKET", 0.001)
        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"
        assert result["type"] == "MARKET"
        assert result["quantity"] == 0.001
        assert result["price"] is None
        assert result["stopPrice"] is None

    def test_limit_order_requires_price(self):
        result = validate_order_inputs("BTCUSDT", "SELL", "LIMIT", 0.001, price=65000.0)
        assert result["type"] == "LIMIT"
        assert result["price"] == 65000.0
        assert result["stopPrice"] is None

    def test_limit_order_missing_price_raises(self):
        with pytest.raises(ValidationError, match="Price is required for LIMIT"):
            validate_order_inputs("BTCUSDT", "SELL", "LIMIT", 0.001)

    def test_stop_limit_requires_price_and_stop(self):
        result = validate_order_inputs(
            "BTCUSDT", "BUY", "STOP_LIMIT", 0.001, price=59000.0, stop_price=59500.0
        )
        assert result["type"] == "STOP_LIMIT"
        assert result["price"] == 59000.0
        assert result["stopPrice"] == 59500.0

    def test_stop_limit_missing_stop_raises(self):
        with pytest.raises(ValidationError, match="stopPrice is required"):
            validate_order_inputs("BTCUSDT", "BUY", "STOP_LIMIT", 0.001, price=59000.0)

    def test_stop_order_requires_stop(self):
        result = validate_order_inputs(
            "BTCUSDT", "SELL", "STOP", 0.001, price=59000.0, stop_price=59500.0
        )
        assert result["stopPrice"] == 59500.0

    def test_symbol_case_normalized(self):
        result = validate_order_inputs("btcusdt", "buy", "market", 0.001)
        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"

    def test_stop_market_requires_stop_price(self):
        result = validate_order_inputs(
            "BTCUSDT", "BUY", "STOP_MARKET", 0.001, stop_price=59500.0
        )
        assert result["type"] == "STOP_MARKET"
        assert result["stopPrice"] == 59500.0
        assert result["price"] is None

    def test_stop_market_missing_stop_raises(self):
        with pytest.raises(ValidationError, match="stopPrice is required"):
            validate_order_inputs("BTCUSDT", "BUY", "STOP_MARKET", 0.001)

    def test_take_profit_requires_stop_price(self):
        result = validate_order_inputs(
            "BTCUSDT", "SELL", "TAKE_PROFIT", 0.001, stop_price=70000.0
        )
        assert result["type"] == "TAKE_PROFIT"
        assert result["stopPrice"] == 70000.0

    def test_take_profit_missing_stop_raises(self):
        with pytest.raises(ValidationError, match="stopPrice is required"):
            validate_order_inputs("BTCUSDT", "SELL", "TAKE_PROFIT", 0.001)

    def test_take_profit_market_requires_stop_price(self):
        result = validate_order_inputs(
            "ETHUSDT", "BUY", "TAKE_PROFIT_MARKET", 0.01, stop_price=4000.0
        )
        assert result["type"] == "TAKE_PROFIT_MARKET"
        assert result["stopPrice"] == 4000.0

    def test_take_profit_market_missing_stop_raises(self):
        with pytest.raises(ValidationError, match="stopPrice is required"):
            validate_order_inputs("ETHUSDT", "BUY", "TAKE_PROFIT_MARKET", 0.01)

    def test_market_order_with_optional_price(self):
        result = validate_order_inputs("BTCUSDT", "BUY", "MARKET", 0.001, price=60000.0)
        assert result["price"] == 60000.0

    def test_stop_limit_missing_price_raises(self):
        with pytest.raises(ValidationError, match="Price is required"):
            validate_order_inputs(
                "BTCUSDT", "BUY", "STOP_LIMIT", 0.001, stop_price=59500.0
            )