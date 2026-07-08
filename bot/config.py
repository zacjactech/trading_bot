"""
Configuration loader for Binance Futures Testnet
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

__all__ = ["Config"]

class Config:
    """Trading bot configuration"""
    
    # Binance Futures Testnet
    # Historically: https://testnet.binancefuture.com
    # NEW Demo Trading (Sept 2025+): https://demo-fapi.binance.com
    # See: https://www.binance.com/en/support/announcement/futures-testnet-upgrade
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    if not BASE_URL.startswith("https://"):
        raise ValueError("BINANCE_BASE_URL must use HTTPS for secure API communication")
    
    # Fallback URLs to try if primary fails (Binance Testnet migration 2025)
    FALLBACK_URLS = [
        "https://testnet.binancefuture.com",
        "https://demo-fapi.binance.com",
        "https://testnet.binance.vision",
    ]
    
    # Mock mode – allows offline demonstration when testnet is unreachable
    # Set MOCK_TRADING=true in .env to enable
    MOCK_TRADING = os.getenv("MOCK_TRADING", "false").lower() in ("true", "1", "yes")
    
    # Trading defaults
    DEFAULT_RECV_WINDOW = 10000
    DEFAULT_TIME_IN_FORCE = "GTC"
    
    @classmethod
    def validate(cls):
        """Validate that required config is present"""
        errors = []
        if not cls.BINANCE_API_KEY:
            errors.append("BINANCE_API_KEY is missing - set in .env file")
        if not cls.BINANCE_API_SECRET:
            errors.append("BINANCE_API_SECRET is missing - set in .env file")
        return errors
    
    @classmethod
    def is_configured(cls):
        return bool(cls.BINANCE_API_KEY and cls.BINANCE_API_SECRET)

    @classmethod
    def reload(cls):
        """Re-read all config values from environment variables.
        
        Useful in tests or when env vars may change after initial import.
        Call after os.environ changes or a second load_dotenv() to pick up new values.
        """
        cls.BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
        cls.BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
        cls.BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
        cls.MOCK_TRADING = os.getenv("MOCK_TRADING", "false").lower() in ("true", "1", "yes")

    @classmethod
    def summary(cls) -> dict:
        """Return a safe dictionary representation of the config (secrets masked)."""
        return {
            "BASE_URL": cls.BASE_URL,
            "MOCK_TRADING": cls.MOCK_TRADING,
            "BINANCE_API_KEY": "***" if cls.BINANCE_API_KEY else None,
            "BINANCE_API_SECRET": "***" if cls.BINANCE_API_SECRET else None,
        }
