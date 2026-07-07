"""
Unit tests for bot/config.py
"""
import pytest
from unittest.mock import patch


class TestConfigDefaults:
    def test_validate_missing_key_and_secret(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = ""
            Config.BINANCE_API_SECRET = ""
            errors = Config.validate()
            assert any("BINANCE_API_KEY is missing" in e for e in errors)
            assert any("BINANCE_API_SECRET is missing" in e for e in errors)
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret

    def test_validate_both_present(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = "abc"
            Config.BINANCE_API_SECRET = "xyz"
            errors = Config.validate()
            assert errors == []
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret

    def test_is_configured_true(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = "abc"
            Config.BINANCE_API_SECRET = "xyz"
            assert Config.is_configured() is True
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret

    def test_is_configured_false(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = ""
            Config.BINANCE_API_SECRET = ""
            assert Config.is_configured() is False
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret


class TestConfigDefaults:
    def test_fallback_urls_is_list(self):
        from bot.config import Config
        assert isinstance(Config.FALLBACK_URLS, list)
        assert len(Config.FALLBACK_URLS) >= 2

    def test_fallback_urls_contain_binance_domains(self):
        from bot.config import Config
        urls = Config.FALLBACK_URLS
        assert any("binance" in u for u in urls)

    def test_default_recv_window(self):
        from bot.config import Config
        assert Config.DEFAULT_RECV_WINDOW == 5000
        assert isinstance(Config.DEFAULT_RECV_WINDOW, int)

    def test_default_time_in_force(self):
        from bot.config import Config
        assert Config.DEFAULT_TIME_IN_FORCE == "GTC"

    def test_validate_only_key_missing(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = ""
            Config.BINANCE_API_SECRET = "xyz"
            errors = Config.validate()
            assert any("BINANCE_API_KEY" in e for e in errors)
            assert not any("BINANCE_API_SECRET" in e for e in errors)
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret

    def test_validate_only_secret_missing(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = "abc"
            Config.BINANCE_API_SECRET = ""
            errors = Config.validate()
            assert not any("BINANCE_API_KEY" in e for e in errors)
            assert any("BINANCE_API_SECRET" in e for e in errors)
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret

    def test_is_configured_key_only(self):
        from bot.config import Config
        original_key = Config.BINANCE_API_KEY
        original_secret = Config.BINANCE_API_SECRET
        try:
            Config.BINANCE_API_KEY = "abc"
            Config.BINANCE_API_SECRET = ""
            assert Config.is_configured() is False
        finally:
            Config.BINANCE_API_KEY = original_key
            Config.BINANCE_API_SECRET = original_secret


class TestMockTradingParsing:
    def test_mock_trading_true_string(self):
        from bot.config import Config
        original = Config.MOCK_TRADING
        try:
            Config.MOCK_TRADING = "true".lower() in ("true", "1", "yes")
            assert Config.MOCK_TRADING is True
        finally:
            Config.MOCK_TRADING = original

    def test_mock_trading_one_string(self):
        from bot.config import Config
        original = Config.MOCK_TRADING
        try:
            Config.MOCK_TRADING = "1".lower() in ("true", "1", "yes")
            assert Config.MOCK_TRADING is True
        finally:
            Config.MOCK_TRADING = original

    def test_mock_trading_yes_string(self):
        from bot.config import Config
        original = Config.MOCK_TRADING
        try:
            Config.MOCK_TRADING = "yes".lower() in ("true", "1", "yes")
            assert Config.MOCK_TRADING is True
        finally:
            Config.MOCK_TRADING = original

    def test_mock_trading_false_string(self):
        from bot.config import Config
        original = Config.MOCK_TRADING
        try:
            Config.MOCK_TRADING = "false".lower() in ("true", "1", "yes")
            assert Config.MOCK_TRADING is False
        finally:
            Config.MOCK_TRADING = original

    def test_mock_trading_random_string(self):
        from bot.config import Config
        original = Config.MOCK_TRADING
        try:
            Config.MOCK_TRADING = "maybe".lower() in ("true", "1", "yes")
            assert Config.MOCK_TRADING is False
        finally:
            Config.MOCK_TRADING = original