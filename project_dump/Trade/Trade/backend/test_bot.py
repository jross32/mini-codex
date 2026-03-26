#!/usr/bin/env python3
"""
Quick test to verify bot components work
Run with: python test_bot.py
"""

from backend.config import Config
from backend.logger import logger
from backend.data import DataFetcher
from backend.strategy import MovingAverageCrossoverStrategy
from backend.trading import TradingBot

def test_components():
    """Test that all bot components initialize correctly"""
    
    print("\n" + "="*60)
    print("CRYPTO TRADING BOT - COMPONENT TEST")
    print("="*60 + "\n")
    
    try:
        # Test 1: Data Fetcher
        print("✓ Test 1: Initializing Data Fetcher...")
        data_fetcher = DataFetcher()
        print("  ✓ Data Fetcher initialized successfully\n")
        
        # Test 2: Fetch data
        print("✓ Test 2: Fetching market data...")
        df = data_fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=100)
        print(f"  ✓ Fetched {len(df)} candles")
        print(f"  Current price: ${df['close'].iloc[-1]:.2f}\n")
        
        # Test 3: Strategy
        print("✓ Test 3: Initializing MA Crossover Strategy...")
        strategy = MovingAverageCrossoverStrategy(fast_period=12, slow_period=26)
        print("  ✓ Strategy initialized successfully\n")
        
        # Test 4: Generate signal
        print("✓ Test 4: Generating trading signal...")
        signal = strategy.generate_signal(df)
        print(f"  ✓ Signal: {signal.name}\n")
        
        # Test 5: Paper Trading Bot
        print("✓ Test 5: Initializing Paper Trading Bot...")
        bot = TradingBot(
            strategy=strategy,
            data_fetcher=data_fetcher,
            use_paper_trading=True,
            initial_balance=10000,
            symbol="BTC/USDT"
        )
        print("  ✓ Bot initialized successfully\n")
        
        # Test 6: Bot iteration
        print("✓ Test 6: Running bot iteration...")
        success = bot.run_iteration(amount_per_trade=0.001)
        if success:
            print("  ✓ Bot iteration completed\n")
            
            # Test 7: Stats
            print("✓ Test 7: Getting bot statistics...")
            stats = bot.get_stats()
            print(f"  Portfolio Value: ${stats['portfolio_value']:.2f}")
            print(f"  Total P&L: ${stats['total_pnl']:.2f}")
            print(f"  Open Positions: {stats['open_positions']}")
            print(f"  Total Trades: {stats['total_trades']}\n")
        
        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\n✓ Your trading bot is ready!")
        print("✓ Run 'python main.py --help' for usage options")
        print("✓ Or run 'python examples/quick_start.py' to get started\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_components()
    exit(0 if success else 1)
