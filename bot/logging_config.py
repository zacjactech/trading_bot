"""
Logging configuration for Binance Futures Trading Bot
Provides structured logging to both file and console
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str = "trading_bot", log_file: str = None, level=logging.INFO):
    """
    Setup structured logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Custom log file path (default: logs/bot.log)
        level: Logging level
    Returns:
        logging.Logger instance
    """
    if log_file is None:
        log_file = os.path.join(LOG_DIR, "bot.log")
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter - structured, useful not noisy
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler with rotation (5MB, 5 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

# Default logger instance
logger = setup_logger()
