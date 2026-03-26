#!/usr/bin/env python3
"""
Example: Quick start with paper trading
Run with: python examples/quick_start.py
"""

from backend.config import Config
from backend.logger import logger
from backend.data import DataFetcher, DataPreprocessor
from backend.strategy import MovingAverageCrossoverStrategy
from backend.trading import TradingBot

def main():
    logger.info("Starting Quick Start Example")
    
    # 1. Fetch market data
    logger.info("\n1. Fetching market data...")
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=100)
    logger.info(f"Fetched {len(df)} candles")
    
    # 2. Add technical indicators
    logger.info("\n2. Adding technical indicators...")
    df = DataPreprocessor.add_technical_indicators(df)
    
    # 3. Create strategy
    logger.info("\n3. Creating strategy...")
    strategy = MovingAverageCrossoverStrategy(fast_period=12, slow_period=26)
    
    # 4. Create trading bot
    logger.info("\n4. Initializing trading bot...")
    bot = TradingBot(
        strategy=strategy,
        data_fetcher=data_fetcher,
        use_paper_trading=True,
        initial_balance=10000,
        symbol="BTC/USDT"
    )
    
    # 5. Run a single iteration
    logger.info("\n5. Running bot iteration...")
    bot.run_iteration(amount_per_trade=0.001)
    
    # 6. Print statistics
    logger.info("\n6. Current Statistics:")
    bot.engine.print_stats(df['close'].iloc[-1])

if __name__ == "__main__":
    main()
