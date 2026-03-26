# Crypto Trading Bot

A comprehensive Python-based AI trading bot for cryptocurrency markets with paper trading, backtesting, and live trading capabilities.

## Features

- **Multiple Trading Strategies**
  - Moving Average Crossover
  - RSI (Relative Strength Index)
  - ML-based predictions with LSTM
  - Hybrid strategies combining multiple approaches

- **Paper Trading** - Test strategies with virtual money before risking real funds

- **Backtesting** - Validate strategies on historical data with detailed metrics (Win Rate, Sharpe Ratio, Max Drawdown)

- **Live Trading Support** - Ready for Binance.US and Coinbase integration

- **REST API** - FastAPI-based API for remote bot control and monitoring

- **Data Fetching** - Real-time market data via CCXT exchange library

- **Technical Indicators** - SMA, EMA, MACD, RSI, Bollinger Bands, ATR, Volume indicators

- **Risk Management** - Position sizing, drawdown tracking, win rate monitoring

## Project Structure

```
crypto_bot/
├── data/
│   ├── fetcher.py          # Market data fetching
│   └── preprocessor.py     # Data preprocessing & indicators
├── models/
│   └── model.py            # LSTM, Random Forest, Simple MA models
├── strategy/
│   └── strategy.py         # Trading strategy implementations
├── trading/
│   ├── paper_trading.py    # Paper trading simulator
│   └── bot.py              # Main bot controller
├── broker/
│   └── ...                 # (Future: real broker integration)
├── backtest/
│   └── backtester.py       # Historical backtesting
├── api/
│   └── main.py             # FastAPI REST endpoints
├── logs/                   # Trading logs
└── config.py               # Configuration management

examples/
├── quick_start.py          # Quick example
├── backtest_comparison.py  # Compare strategies
└── api_server.py           # Run API server

main.py                     # Main entry point
```

## Installation

### 1. Clone/Download the project
```bash
cd Trade
```

### 2. Create a virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Configuration

Edit `.env` file to customize:
- Bot mode (paper_trading or live_trading)
- Exchange settings
- Trading parameters
- API keys (for live trading)

```env
BOT_MODE=paper_trading
INITIAL_BALANCE=10000
TARGET_CRYPTO=BTC/USDT
MODEL_TYPE=lstm
```

## Quick Start

### Option 1: Run Paper Trading
```bash
# Run MA Crossover strategy for 1 hour (paper trading)
python main.py --mode trade --strategy ma_crossover --symbol BTC/USDT --duration 1
```

### Option 2: Backtest a Strategy
```bash
# Backtest RSI strategy on 500 hourly candles
python main.py --mode backtest --strategy rsi --symbol BTC/USDT --timeframe 1h --candles 500
```

### Option 3: Quick Start Example
```bash
python examples/quick_start.py
```

### Option 4: Run REST API Server
```bash
python examples/api_server.py
# API docs: http://localhost:8000/docs
```

### Option 5: Compare Strategies
```bash
python examples/backtest_comparison.py
```

## API Endpoints

### Bot Control
- `POST /bot/start` - Start bot with config
- `POST /bot/stop` - Stop running bot
- `POST /bot/run-iteration` - Run single bot iteration
- `GET /bot/stats` - Get current stats

### Market Data
- `GET /market/price/{symbol}` - Get current price
- `GET /market/data/{symbol}` - Get OHLCV data

### Backtesting
- `POST /backtest` - Run strategy backtest

### Info
- `GET /strategies` - List available strategies
- `GET /health` - Health check

**Example API calls:**
```bash
# Start bot
curl -X POST http://localhost:8000/bot/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "ma_crossover", "symbol": "BTC/USDT"}'

# Get bot stats
curl http://localhost:8000/bot/stats

# Get BTC price
curl http://localhost:8000/market/price/BTC/USDT

# Run backtest
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{"strategy": "ma_crossover", "candles": 500}'
```

## Trading Strategies

### 1. Moving Average Crossover
- Buy when Fast MA > Slow MA
- Sell when Fast MA < Slow MA
- Good for trending markets

**Run:** `python main.py --strategy ma_crossover`

### 2. RSI Strategy
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Good for range-bound markets

**Run:** `python main.py --strategy rsi`

### 3. ML-Based (LSTM)
- Uses LSTM neural network for price prediction
- Trained on technical indicators
- More complex, needs data preparation

**Run:** `python main.py --strategy ml`

## Backtesting Metrics

After running backtest, you'll see:
- **Total Trades**: Number of completed trades
- **Win Rate**: % of profitable trades
- **Total P&L**: Profit/Loss in dollars and %
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns (higher is better)

## Paper Trading

Trade with virtual money to test strategies:
1. Initial balance: $10,000 (configurable)
2. Each iteration fetches latest market data
3. Strategy generates buy/sell signals
4. Orders execute at current market price
5. Portfolio value updated in real-time

## Next Steps: Live Trading

To enable live trading with Binance.US or Coinbase:

1. **Get API Keys**
   - Binance.US: https://www.binance.us/en/account/api-management
   - Coinbase: https://www.coinbase.com/settings/api

2. **Add credentials to `.env`**
   ```env
   BINANCE_API_KEY=your_key
   BINANCE_API_SECRET=your_secret
   BOT_MODE=live_trading
   ```

3. **Test with small amount first**
   ```python
   bot = TradingBot(..., use_paper_trading=False)
   ```

⚠️ **WARNING**: Live trading risks real money. Always backtest and paper trade first!

## Common Issues

### No data fetched
- Check internet connection
- Verify symbol format (e.g., BTC/USDT)
- Rate limits from exchange (wait a moment and retry)

### API key errors
- Verify API key format in `.env`
- Check key has trading permissions
- Ensure IP whitelisting on exchange

### Memory issues with large datasets
- Reduce `limit` in `fetch_ohlcv()` calls
- Use shorter timeframes initially

## Performance Tips

1. **Start with paper trading** - Test strategy without risk
2. **Backtest on historical data** - Validate before deployment
3. **Use appropriate timeframes** - 1h or 4h for crypto
4. **Monitor for overfitting** - Good backtest ≠ good live performance
5. **Adjust position size** - Risk only 1-2% per trade
6. **Diversify strategies** - Use hybrid approach

## File Structure Summary

```
main.py                    # CLI entry point
requirements.txt           # Python dependencies
.env                      # Configuration (create from template)

crypto_bot/
├── config.py             # Settings management
├── logger.py             # Logging setup
├── data/
│   ├── fetcher.py        # OHLCV data from exchanges
│   └── preprocessor.py   # Indicators & normalization
├── models/
│   └── model.py          # LSTM, RF, MA models
├── strategy/
│   └── strategy.py       # 4+ strategy implementations
├── trading/
│   ├── paper_trading.py  # Virtual trading
│   └── bot.py            # Main bot orchestration
├── backtest/
│   └── backtester.py     # Historical testing
└── api/
    └── main.py           # FastAPI endpoints

examples/
├── quick_start.py        # Simple example
├── backtest_comparison.py # Compare strategies
└── api_server.py         # Run API
```

## Development & Customization

### Add New Strategy
Create a new class inheriting from `StrategyEngine`:
```python
from crypto_bot.strategy import StrategyEngine, TradeSignal

class MyStrategy(StrategyEngine):
    def generate_signal(self, df):
        # Your logic here
        if condition:
            return TradeSignal.BUY
        return TradeSignal.HOLD
```

### Add New Model
Implement model in `crypto_bot/models/model.py`:
```python
class MyModel:
    def train(self, X, y):
        # Training logic
        pass
    
    def predict(self, X):
        # Prediction logic
        pass
```

## Contributing

Improvements welcome:
- New strategies
- Better prediction models
- Performance optimizations
- Additional indicators

## Disclaimer

This bot is for educational purposes. Trading cryptocurrencies involves substantial risk of loss. Paper trading results do not guarantee live trading performance. Always do your own research and test thoroughly before using real money.

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check logs in `crypto_bot/logs/`
2. Review `.env` configuration
3. Test with paper trading first
4. Check exchange API documentation

---

**Happy Trading! 🚀📈**
