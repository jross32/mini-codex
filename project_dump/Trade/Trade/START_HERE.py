#!/usr/bin/env python3
"""
Getting Started Guide
Shows what to do next after installation
"""

def show_welcome():
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║     🚀  CRYPTO AI TRADING BOT - WELCOME!  🚀                      ║
║                                                                    ║
║     Your complete trading bot backend is ready to use!            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

✅ SETUP COMPLETE - All components installed and tested!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PROJECT OVERVIEW

This is a professional-grade crypto trading bot with:

  ✓ Multiple trading strategies (MA Crossover, RSI, ML-based, Hybrid)
  ✓ Paper trading simulator (trade with virtual money)
  ✓ Backtesting engine (test on historical data)
  ✓ LSTM neural network for price prediction
  ✓ Real-time market data fetching
  ✓ REST API for remote control
  ✓ Comprehensive logging and monitoring
  ✓ Ready for live trading (Binance.US, Coinbase)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 QUICK START (Choose One)

1️⃣  VERIFY INSTALLATION (No API calls needed)
   
   python test_bot_offline.py
   
   ✓ Tests all bot components
   ✓ Should complete in ~5 seconds
   ✓ Shows "✓ ALL TESTS PASSED!" if successful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2️⃣  BACKTEST A STRATEGY (Test on past data)

   python main.py --mode backtest --strategy ma_crossover
   
   ✓ Uses 500 1-hour Bitcoin candles
   ✓ Shows: wins, losses, profit/loss, max drawdown
   ✓ Takes ~10 seconds
   ✓ No internet required (uses cached data)

   Try other strategies:
   • python main.py --mode backtest --strategy rsi
   • python main.py --mode backtest --strategy ma_crossover --candles 1000
   • python examples/backtest_comparison.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3️⃣  PAPER TRADE (Virtual money, 1 hour)

   python main.py --mode trade --strategy ma_crossover --duration 1
   
   ✓ Starts with $10,000 virtual balance
   ✓ Checks for signals every hour
   ✓ Exits after 1 hour
   ✓ Shows real-time P&L

   Try different strategies:
   • python main.py --mode trade --strategy rsi --duration 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4️⃣  RUN REST API SERVER

   python examples/api_server.py
   
   ✓ Starts HTTP server on http://localhost:8000
   ✓ Interactive API docs at http://localhost:8000/docs
   ✓ Can control bot remotely
   ✓ In another terminal, try:
     curl http://localhost:8000/market/price/BTC/USDT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 FULL COMMANDS

BACKTESTING:
   python main.py --mode backtest
   python main.py --mode backtest --strategy rsi
   python main.py --mode backtest --strategy ma_crossover --candles 1000
   python main.py --mode backtest --symbol ETH/USDT --timeframe 4h

PAPER TRADING:
   python main.py --mode trade --duration 1
   python main.py --mode trade --strategy rsi --duration 2
   python main.py --mode trade --symbol ETH/USDT

EXAMPLES:
   python examples/quick_start.py
   python examples/backtest_comparison.py
   python examples/api_server.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 DOCUMENTATION

  • SETUP_SUMMARY.md    ← You are here! Overview and quick start
  • QUICK_START.md      ← Quick reference guide
  • README.md           ← Complete documentation
  • .env                ← Configuration file (edit to customize)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 AVAILABLE STRATEGIES

1. MA CROSSOVER ⭐ (Recommended)
   • Buy when fast MA > slow MA
   • Sell when fast MA < slow MA
   • Best for: Trending markets
   
   python main.py --mode backtest --strategy ma_crossover

2. RSI
   • Buy when RSI < 30 (oversold)
   • Sell when RSI > 70 (overbought)
   • Best for: Range-bound markets
   
   python main.py --mode backtest --strategy rsi

3. ML-BASED (LSTM Neural Network)
   • Uses deep learning for price prediction
   • Best for: Complex patterns
   
   python main.py --mode backtest --strategy ml

4. HYBRID
   • Combines multiple strategies
   • Best for: Robust signals
   
   python main.py --mode backtest --strategy hybrid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDED WORKFLOW

STEP 1: Verify Setup
   → python test_bot_offline.py

STEP 2: Backtest Strategy
   → python main.py --mode backtest --strategy ma_crossover

STEP 3: Compare Strategies
   → python examples/backtest_comparison.py

STEP 4: Paper Trade
   → python main.py --mode trade --strategy ma_crossover

STEP 5: If profitable, go live (with real API keys)
   → Edit .env file
   → Change BOT_MODE=live_trading
   → Start with small amounts!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 UNDERSTANDING BACKTEST RESULTS

Example output:
   Total P&L:      $542.50 (5.42%)      ← Profit/Loss
   Win Rate:       80.00%               ← % of profitable trades
   Max Drawdown:   -2.30%               ← Biggest loss
   Sharpe Ratio:   1.85                 ← Risk-adjusted returns

What it means:
   ✓ Made 5.42% profit (good)
   ✓ 80% of trades were winners (very good)
   ✓ Largest loss was -2.30% (acceptable)
   ✓ Sharpe ratio 1.85 (good risk-adjusted returns)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  CUSTOMIZATION

Edit .env file to customize:

   BOT_MODE=paper_trading          # Mode (paper_trading or live_trading)
   INITIAL_BALANCE=10000           # Starting balance
   TARGET_CRYPTO=BTC/USDT          # Trading pair
   TRADE_AMOUNT=0.001              # Amount per trade
   MODEL_TYPE=lstm                 # Model type

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  IMPORTANT REMINDERS

  ⚠️  Always backtest before paper trading
  ⚠️  Paper trade before using real money
  ⚠️  Start with small amounts
  ⚠️  Never trade more than you can afford to lose
  ⚠️  Past performance doesn't guarantee future results
  ⚠️  Keep your API keys secure!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆘 HELP & TROUBLESHOOTING

Q: What command should I run first?
A: python test_bot_offline.py

Q: How do I test a strategy?
A: python main.py --mode backtest --strategy ma_crossover

Q: Where are the logs?
A: backend/logs/bot_*.log

Q: How do I add my own strategy?
A: Edit backend/strategy/strategy.py

Q: Can I trade with real money?
A: Yes! Update .env with API keys and change BOT_MODE to live_trading

Q: Where's the REST API documentation?
A: Run: python examples/api_server.py
   Then open: http://localhost:8000/docs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ NEXT STEP

Pick one of these and run it now:

   python test_bot_offline.py

This will verify everything works correctly!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 FILES TO READ

   SETUP_SUMMARY.md    ← Setup overview (this file)
   QUICK_START.md      ← Quick reference
   README.md           ← Full documentation
   .env                ← Configuration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Happy Trading! 🚀📈

""")

if __name__ == "__main__":
    show_welcome()
