#!/usr/bin/env python3
"""
Main entry point for the crypto trading bot
Run with: python main.py
"""

import sys
import time
import argparse
from backend.config import Config
from backend.logger import logger
from backend.data import DataFetcher
from backend.strategy import get_strategy
from backend.trading import TradingBot
from backend.backtest import Backtester

def run_paper_trading(symbol="BTC/USDT", strategy_type="ma_crossover", duration_hours=1):
    """Run bot in paper trading mode"""
    logger.info("="*60)
    logger.info("STARTING PAPER TRADING BOT")
    logger.info("="*60)
    
    try:
        # Initialize components
        data_fetcher = DataFetcher(exchange_name="binance")
        strategy = get_strategy(strategy_type)
        
        # Create bot
        bot = TradingBot(
            strategy=strategy,
            data_fetcher=data_fetcher,
            use_paper_trading=True,
            initial_balance=Config.INITIAL_BALANCE,
            symbol=symbol
        )
        
        logger.info(f"Bot running with {strategy_type} strategy on {symbol}")
        logger.info(f"Initial balance: ${Config.INITIAL_BALANCE:.2f}")
        
        # Run bot for specified duration
        start_time = time.time()
        iterations = 0
        
        while time.time() - start_time < duration_hours * 3600:
            iterations += 1
            logger.info(f"\n--- Iteration {iterations} ---")
            
            success = bot.run_iteration(amount_per_trade=Config.TRADE_AMOUNT)
            
            if success:
                stats = bot.get_stats()
                logger.info(f"Portfolio: ${stats['portfolio_value']:.2f} | "
                           f"P&L: ${stats['total_pnl']:.2f} ({stats['total_pnl_percent']:.2f}%)")
            
            # Wait before next iteration (1 hour)
            logger.info("Waiting 1 hour before next iteration...")
            time.sleep(3600)  # Sleep for 1 hour
        
        # Print final stats
        logger.info("\n" + "="*60)
        logger.info("BOT TRADING COMPLETED")
        logger.info("="*60)
        bot.engine.print_stats(data_fetcher.fetch_current_price(symbol)['price'])
        
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Error in bot: {e}")
        raise

def run_backtest(symbol="BTC/USDT", strategy_type="ma_crossover", timeframe="1h", candles=500):
    """Run strategy backtest on historical data"""
    logger.info("="*60)
    logger.info("STARTING STRATEGY BACKTEST")
    logger.info("="*60)
    
    try:
        # Fetch historical data
        logger.info(f"Fetching {candles} {timeframe} candles for {symbol}...")
        data_fetcher = DataFetcher(exchange_name="binance")
        df = data_fetcher.fetch_ohlcv(symbol, timeframe, limit=candles)
        
        if df.empty:
            logger.error("No data fetched")
            return
        
        logger.info(f"Fetched {len(df)} candles")
        
        # Create strategy
        strategy = get_strategy(strategy_type)
        
        # Run backtest
        backtester = Backtester(initial_balance=Config.INITIAL_BALANCE, symbol=symbol)
        results = backtester.run(df, strategy)
        
        # Print results
        backtester.print_results()
        
        # Print trades
        if results['trades']:
            logger.info("\nTrade Details:")
            logger.info("-"*80)
            for i, trade in enumerate(results['trades'][:10], 1):  # Show first 10 trades
                logger.info(f"{i}. Entry: ${trade['entry_price']:.2f} | "
                           f"Exit: ${trade['exit_price']:.2f} | "
                           f"P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
        
    except Exception as e:
        logger.error(f"Error in backtest: {e}")
        raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Crypto Trading Bot")
    parser.add_argument("--mode", choices=["trade", "backtest"], default="trade",
                       help="Bot mode: trade (paper trading) or backtest")
    parser.add_argument("--strategy", choices=["ma_crossover", "rsi", "ml"], 
                       default="ma_crossover", help="Trading strategy")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading symbol")
    parser.add_argument("--timeframe", default="1h", help="Candle timeframe (for backtest)")
    parser.add_argument("--candles", type=int, default=500, help="Number of candles (for backtest)")
    parser.add_argument("--duration", type=float, default=1, 
                       help="Trading duration in hours (for paper trading)")
    
    args = parser.parse_args()
    
    if args.mode == "trade":
        run_paper_trading(
            symbol=args.symbol,
            strategy_type=args.strategy,
            duration_hours=args.duration
        )
    else:
        run_backtest(
            symbol=args.symbol,
            strategy_type=args.strategy,
            timeframe=args.timeframe,
            candles=args.candles
        )

if __name__ == "__main__":
    main()
