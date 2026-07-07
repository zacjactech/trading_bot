"""
Custom exception hierarchy for the Binance Futures Trading Bot.

All bot-specific errors inherit from ``BotError``, allowing callers to catch
either the base class or a specific subtype as needed.

Example::

    from bot.exceptions import APIError, NetworkError

    try:
        client.place_order(...)
    except APIError as exc:
        print(f"Binance rejected the order: {exc.code} – {exc.message}")
    except NetworkError:
        print("Could not reach Binance Testnet – check your VPN.")
"""

__all__ = ["BotError", "APIError", "NetworkError", "ConfigurationError"]


class BotError(Exception):
    """Base exception for all trading bot errors."""


class APIError(BotError):
    """Raised when the Binance API returns an error response.

    Attributes:
        code: Binance API error code (e.g. ``-1116``).
        message: Human-readable description from the API response.
    """

    def __init__(self, code: int | str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class NetworkError(BotError):
    """Raised when all configured base URLs fail to respond."""


class ConfigurationError(BotError):
    """Raised when required configuration values are missing or invalid."""
