#!/usr/bin/env python3
"""
Test bot components without external API calls
Run with: python test_bot_offline.py
"""

import pandas as pd
import numpy as np
from backend.config import Config
from backend.logger import logger
from backend.strategy import MovingAverageCrossoverStrategy
from backend.trading import PaperTradingEngine
from backend.backtest import Backtester

def create_mock_data():
    """Create mock OHLCV data for testing"""
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    
    # Generate realistic price movement
    prices = 40000 + np.cumsum(np.random.randn(100) * 200)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices - np.abs(np.random.randn(100) * 50),
        'high': prices + np.abs(np.random.randn(100) * 100),
        'low': prices - np.abs(np.random.randn(100) * 100),
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })
    
    return df

def test_components():
    """Test all bot components"""
    
    print("\n" + "="*60)
    print("CRYPTO TRADING BOT - OFFLINE COMPONENT TEST")
    print("="*60 + "\n")
    
    try:
        # Test 1: Create mock data
        print("✓ Test 1: Creating mock market data...")
        df = create_mock_data()
        print(f"  ✓ Created {len(df)} candles")
        print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}\n")
        
        # Test 2: Strategy
        print("✓ Test 2: Initializing MA Crossover Strategy...")
        strategy = MovingAverageCrossoverStrategy(fast_period=12, slow_period=26)
        print("  ✓ Strategy initialized successfully\n")
        
        # Test 3: Generate signal
        print("✓ Test 3: Generating trading signal...")
        signal = strategy.generate_signal(df)
        print(f"  ✓ Signal: {signal.name}\n")
        
        # Test 4: Paper Trading Engine
        print("✓ Test 4: Initializing Paper Trading Engine...")
        engine = PaperTradingEngine(initial_balance=10000, symbol="BTC/USDT")
        print("  ✓ Engine initialized\n")
        
        # Test 5: Execute trades
        print("✓ Test 5: Simulating paper trades...")
        price1 = df['close'].iloc[30]
        engine.buy(price1, 0.1, "Test buy")
        print(f"  ✓ Buy executed at ${price1:.2f}\n")
        
        price2 = df['close'].iloc[60]
        engine.sell(price2, 0.1, "Test sell")
        print(f"  ✓ Sell executed at ${price2:.2f}\n")
        
        # Test 6: Get stats
        print("✓ Test 6: Getting trading statistics...")
        stats = engine.get_stats(df['close'].iloc[-1])
        print(f"  Initial Balance:    ${stats['initial_balance']:.2f}")
        print(f"  Current Balance:    ${stats['current_balance']:.2f}")
        print(f"  Total P&L:          ${stats['total_pnl']:.2f}")
        print(f"  Total Trades:       {stats['total_trades']}\n")
        
        # Test 7: Backtester
        print("✓ Test 7: Running backtest...")
        backtester = Backtester(initial_balance=10000, symbol="BTC/USDT")
        results = backtester.run(df, strategy)
        print(f"  ✓ Backtest completed")
        print(f"  Total Trades:       {results['total_trades']}")
        print(f"  Win Rate:           {results['win_rate']:.2f}%")
        print(f"  Total P&L:          ${results['total_pnl']:.2f} ({results['total_pnl_percent']:.2f}%)")
        print(f"  Max Drawdown:       {results['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio:       {results['sharpe_ratio']:.2f}\n")
        
        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\n✓ Your trading bot is ready!")
        print("✓ Bot components tested successfully")
        print("\n✓ Next steps:")
        print("  1. Run 'python main.py --mode backtest' to test strategies on historical data")
        print("  2. Run 'python main.py --mode trade' to run paper trading simulation")
        print("  3. Run 'python examples/api_server.py' to start the REST API server\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_components()
    exit(0 if success else 1)
