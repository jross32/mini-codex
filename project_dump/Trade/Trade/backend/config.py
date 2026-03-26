import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    BOT_MODE = os.getenv("BOT_MODE", "paper_trading")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Exchange
    PRIMARY_EXCHANGE = os.getenv("PRIMARY_EXCHANGE", "binance")
    LIVE_EXCHANGE = os.getenv("LIVE_EXCHANGE", "binance")
    
    # API Keys
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
    COINBASE_PASSPHRASE = os.getenv("COINBASE_PASSPHRASE")
    
    # Trading
    INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "10000"))
    TARGET_CRYPTO = os.getenv("TARGET_CRYPTO", "BTC/USDT")
    TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "0.01"))
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
    
    # Model
    MODEL_TYPE = os.getenv("MODEL_TYPE", "lstm")
    PREDICTION_HORIZON = int(os.getenv("PREDICTION_HORIZON", "24"))
    
    # Data
    DATA_DIR = "crypto_bot/data"
    MODELS_DIR = "crypto_bot/models"
    LOGS_DIR = "crypto_bot/logs"
