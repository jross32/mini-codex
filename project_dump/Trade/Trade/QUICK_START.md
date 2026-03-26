# Crypto AI Trading Bot - Quick Start Guide

## ✅ Installation Complete!

Your crypto trading bot is fully set up and ready to use. All components have been tested and verified working.

## 🚀 Getting Started (5 Minutes)

### 1. **Verify Installation**
```bash
python test_bot_offline.py
```
You should see "✓ ALL TESTS PASSED!"

### 2. **Run Your First Backtest**

Test a trading strategy on historical data:
```bash
python main.py --mode backtest --strategy ma_crossover --candles 500
```

You'll see:
- Number of trades executed
- Win rate percentage
- Total profit/loss
- Max drawdown
- Sharpe ratio

### 3. **Run Paper Trading Simulation**

Trade with virtual money (doesn't affect real balance):
```bash
python main.py --mode trade --strategy ma_crossover --duration 1
```

This runs the bot for 1 hour, checking every hour for signals.

### 4. **Try Different Strategies**

```bash
# RSI Strategy
python main.py --mode backtest --strategy rsi

# Compare all strategies
python examples/backtest_comparison.py

# Quick start with one trade
python examples/quick_start.py
```

## 📊 Available Commands

### Backtesting
```bash
# Default: MA Crossover on 500 1-hour candles
python main.py --mode backtest

# With options
python main.py --mode backtest \
  --strategy rsi \
  --symbol BTC/USDT \
  --timeframe 4h \
  --candles 1000

# Options for --strategy:
#   ma_crossover (recommended for beginners)
#   rsi
#   ml (requires trained model)
```

### Paper Trading
```bash
# Run for 1 hour
python main.py --mode trade --duration 1

# Change strategy
python main.py --mode trade --strategy rsi --duration 2

# Use different symbol
python main.py --mode trade --symbol ETH/USDT
```

### REST API Server
```bash
# Start API server (runs on http://localhost:8000)
python examples/api_server.py

# In another terminal, test the API:
curl http://localhost:8000/market/price/BTC/USDT
```

## 📁 Project Files

```
Trade/
├── main.py                 ← Main entry point
├── test_bot_offline.py     ← Run tests
├── requirements.txt        ← Dependencies
├── .env                    ← Configuration
├── README.md               ← Full documentation
│
├── crypto_bot/
│   ├── config.py          ← Settings
│   ├── logger.py          ← Logging
│   │
│   ├── data/              ← Market data
│   │   ├── fetcher.py     ← Get prices from exchange
│   │   └── preprocessor.py ← Add indicators
│   │
│   ├── models/            ← Price prediction
│   │   └── model.py       ← LSTM, RF, MA models
│   │
│   ├── strategy/          ← Trading logic
│   │   └── strategy.py    ← 4+ strategies
│   │
│   ├── trading/           ← Order execution
│   │   ├── paper_trading.py ← Virtual trading
│   │   └── bot.py         ← Main bot
│   │
│   ├── backtest/          ← Historical testing
│   │   └── backtester.py
│   │
│   └── api/               ← REST API
│       └── main.py
│
└── examples/
    ├── quick_start.py
    ├── backtest_comparison.py
    └── api_server.py
```

## 🎯 Key Features Explained

### **Paper Trading**
- Start with $10,000 virtual balance
- Trade without risking real money
- Perfect for testing strategies
- See real-time P&L, win rates, drawdown

### **Backtesting**
- Test strategies on past data
- See how profitable they would have been
- Avoid overfitting (good backtest ≠ live profits)
- Compare different strategies

### **Multiple Strategies**

#### **1. MA Crossover (Best for beginners)**
- Buy when fast moving average > slow moving average
- Sell when fast MA < slow MA
- Great for trending markets
```bash
python main.py --mode backtest --strategy ma_crossover
```

#### **2. RSI Strategy**
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Good for range-bound markets
```bash
python main.py --mode backtest --strategy rsi
```

#### **3. ML-Based (Advanced)**
- Uses LSTM neural network
- Learns from historical patterns
- More complex setup
```bash
python main.py --mode backtest --strategy ml
```

## ⚙️ Configuration

Edit `.env` file to customize:

```env
# Trading mode
BOT_MODE=paper_trading        # or live_trading

# Account setup
INITIAL_BALANCE=10000         # Starting balance
TARGET_CRYPTO=BTC/USDT        # Trading pair
TRADE_AMOUNT=0.001            # Amount per trade

# Strategy
MODEL_TYPE=lstm               # or simple_ma, random_forest

# For live trading (optional, don't share!)
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

## 📈 Understanding Backtest Results

```
Initial Balance:        $10,000.00
Final Balance:          $10,542.50
Total P&L:              $542.50 (5.42%)
├─ Winning Trades:      12
├─ Losing Trades:       3
└─ Win Rate:            80%
Max Drawdown:           -2.3%      (Biggest loss during backtest)
Sharpe Ratio:           1.85       (Higher = better risk-adjusted returns)
```

## 🔄 Complete Trading Workflow

1. **Backtest Strategy**
   ```bash
   python main.py --mode backtest --strategy ma_crossover --candles 1000
   ```

2. **If backtest looks good, paper trade**
   ```bash
   python main.py --mode trade --strategy ma_crossover
   ```

3. **Monitor results** (check logs in `crypto_bot/logs/`)

4. **Once confident, enable live trading**
   - Update `.env` with real API keys
   - Change `BOT_MODE=live_trading`
   - Start with small amounts!

## ⚠️ Risk Management Tips

1. **Always backtest first** - No backtest ≠ no live trade
2. **Paper trade before real money** - Verify strategy works live
3. **Start small** - Use `TRADE_AMOUNT=0.0001` initially
4. **Monitor drawdowns** - Close bot if losses exceed 10%
5. **Diversify** - Don't use all capital on one strategy
6. **Test on different timeframes** - What works on 1h might not work on 4h

## 🐛 Troubleshooting

### "No data fetched"
- Check internet connection
- Try with different symbol (e.g., ETH/USDT)
- Check exchange API status

### "Module not found errors"
```bash
pip install -r requirements.txt
```

### "Permission denied"
```bash
# Make scripts executable (Linux/Mac)
chmod +x main.py
chmod +x test_bot_offline.py
```

### "API rate limit"
- Bot waits automatically (CCXT handles this)
- Or reduce number of candles in backtest

## 📚 Next Steps

1. **Explore strategies**: Modify strategy code in `crypto_bot/strategy/strategy.py`
2. **Add indicators**: Customize in `crypto_bot/data/preprocessor.py`
3. **Train ML model**: Use `crypto_bot/models/model.py` with your data
4. **Build frontend**: Use the REST API to create a web dashboard
5. **Deploy**: Run on VPS or cloud for 24/7 trading

## 🤝 Useful Resources

- **CCXT Library**: https://github.com/ccxt/ccxt - Exchange API wrapper
- **Crypto Trading Indicators**: Technical analysis library
- **Backtesting Best Practices**: https://www.investopedia.com/
- **Live Trading Safety**: Always use small position sizes first

## 📞 Support

- Check logs: `cat crypto_bot/logs/bot_*.log`
- Read docs: `README.md` (comprehensive guide)
- Try examples: `python examples/quick_start.py`
- Review code: All files well-commented

## ✨ What's Included

✅ 4+ trading strategies (MA, RSI, ML, Hybrid)
✅ Paper trading simulator (virtual money)
✅ Backtesting engine with detailed metrics
✅ LSTM neural network for price prediction
✅ Real-time market data fetching
✅ REST API for remote control
✅ Comprehensive logging
✅ Risk management tools
✅ Ready for Binance.US and Coinbase integration

## 🎓 Example Usage

### Quick backtest
```bash
python main.py --mode backtest --strategy ma_crossover --candles 300
```

### Compare strategies
```bash
python examples/backtest_comparison.py
```

### Run bot for 2 hours with RSI strategy
```bash
python main.py --mode trade --strategy rsi --duration 2
```

### Start API server
```bash
python examples/api_server.py
```

---

**You're all set! 🚀** 

Start with backtesting, then move to paper trading, and finally go live when you're confident.

Happy trading! 📈
