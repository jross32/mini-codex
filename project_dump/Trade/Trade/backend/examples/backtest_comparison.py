#!/usr/bin/env python3
"""
Example: Backtest multiple strategies
Run with: python examples/backtest_comparison.py
"""

from backend.logger import logger
from backend.data import DataFetcher
from backend.strategy import (
    MovingAverageCrossoverStrategy,
    RSIStrategy
)
from backend.backtest import Backtester

def main():
    logger.info("Comparing Trading Strategies")
    
    # Fetch data once
    logger.info("\nFetching market data...")
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=500)
    logger.info(f"Fetched {len(df)} candles")
    
    # Test strategies
    strategies = [
        ("MA Crossover (12/26)", MovingAverageCrossoverStrategy(12, 26)),
        ("RSI (14)", RSIStrategy(14, 70, 30)),
    ]
    
    results_summary = []
    
    for name, strategy in strategies:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {name}")
        logger.info(f"{'='*60}")
        
        backtester = Backtester(initial_balance=10000, symbol="BTC/USDT")
        results = backtester.run(df, strategy)
        backtester.print_results()
        
        results_summary.append({
            'strategy': name,
            'total_trades': results['total_trades'],
            'win_rate': results['win_rate'],
            'total_pnl_percent': results['total_pnl_percent'],
            'max_drawdown': results['max_drawdown'],
            'sharpe_ratio': results['sharpe_ratio']
        })
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("STRATEGY COMPARISON SUMMARY")
    logger.info(f"{'='*60}")
    for res in results_summary:
        logger.info(f"\n{res['strategy']}")
        logger.info(f"  Trades: {res['total_trades']}")
        logger.info(f"  Win Rate: {res['win_rate']:.2f}%")
        logger.info(f"  P&L: {res['total_pnl_percent']:.2f}%")
        logger.info(f"  Max Drawdown: {res['max_drawdown']:.2f}%")
        logger.info(f"  Sharpe Ratio: {res['sharpe_ratio']:.2f}")

if __name__ == "__main__":
    main()
