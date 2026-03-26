import logging
import os
from datetime import datetime
from backend.config import Config

def setup_logger(name, log_file=None):
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)
    
    # Create logs directory if not exists
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.LOG_LEVEL)
    
    # File handler
    if not log_file:
        log_file = os.path.join(Config.LOGS_DIR, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(Config.LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Global logger
logger = setup_logger("CryptoBot")
