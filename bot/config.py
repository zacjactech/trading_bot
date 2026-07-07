"""
Configuration loader for Binance Futures Testnet
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv optional – fallback to system env only
    def load_dotenv():
        pass

class Config:
    """Trading bot configuration"""
    
    # Binance Futures Testnet
    # Historically: https://testnet.binancefuture.com
    # NEW Demo Trading (Sept 2025+): https://demo-fapi.binance.com
    # See: https://www.binance.com/en/support/announcement/futures-testnet-upgrade
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    
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
    DEFAULT_RECV_WINDOW = 5000
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
