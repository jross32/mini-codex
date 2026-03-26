import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.logger import logger
from backend.config import Config
import json
import os

class DataFetcher:
    """Fetch historical and real-time crypto market data"""
    
    def __init__(self, exchange_name="binance"):
        """Initialize exchange connection"""
        self.exchange_name = exchange_name
        self.exchange = self._get_exchange()
        self.cache_dir = os.path.join(Config.DATA_DIR, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_exchange(self):
        """Get CCXT exchange instance"""
        try:
            if self.exchange_name.lower() == "binance":
                exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'rateLimit': 200,
                })
            elif self.exchange_name.lower() == "coinbase":
                exchange = ccxt.coinbase({
                    'enableRateLimit': True,
                    'rateLimit': 300,
                })
            else:
                exchange = ccxt.binance()
            
            logger.info(f"Connected to {self.exchange_name}")
            return exchange
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            raise
    
    def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1h", limit=500):
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching {symbol} {timeframe} candles (limit: {limit})")
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            logger.info(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return pd.DataFrame()
    
    def fetch_current_price(self, symbol="BTC/USDT"):
        """Fetch current price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def fetch_order_book(self, symbol="BTC/USDT", limit=20):
        """Fetch order book data"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit],
                'timestamp': datetime.fromtimestamp(orderbook['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None
    
    def fetch_multiple_symbols(self, symbols, timeframe="1h", limit=500):
        """Fetch data for multiple symbols at once"""
        data = {}
        for symbol in symbols:
            try:
                df = self.fetch_ohlcv(symbol, timeframe, limit)
                data[symbol] = df
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
        return data
    
    def save_data_to_csv(self, df, filename):
        """Save DataFrame to CSV"""
        filepath = os.path.join(Config.DATA_DIR, filename)
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        df.to_csv(filepath, index=False)
        logger.info(f"Data saved to {filepath}")
        return filepath
    
    def load_data_from_csv(self, filename):
        """Load data from CSV"""
        filepath = os.path.join(Config.DATA_DIR, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()
