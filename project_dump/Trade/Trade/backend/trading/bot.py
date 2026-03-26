from backend.logger import logger
from backend.config import Config
from backend.strategy import TradeSignal
import ccxt

class BrokerConnector:
    """Connect to real trading brokers"""
    
    def __init__(self, exchange_name="binance", api_key=None, api_secret=None):
        self.exchange_name = exchange_name
        self.api_key = api_key or Config.BINANCE_API_KEY
        self.api_secret = api_secret or Config.BINANCE_API_SECRET
        self.exchange = self._init_exchange()
    
    def _init_exchange(self):
        """Initialize exchange connection"""
        try:
            if self.exchange_name.lower() == "binance":
                exchange = ccxt.binanceus({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot'
                    }
                })
            elif self.exchange_name.lower() == "coinbase":
                exchange = ccxt.coinbase({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'password': Config.COINBASE_PASSPHRASE,
                    'enableRateLimit': True
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.exchange_name}")
            
            logger.info(f"Connected to {self.exchange_name}")
            return exchange
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            return None
    
    def check_balance(self):
        """Get account balance"""
        try:
            if not self.exchange:
                return None
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    def place_buy_order(self, symbol, amount, price=None):
        """Place buy order"""
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return None
            
            if price:
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            else:
                order = self.exchange.create_market_buy_order(symbol, amount)
            
            logger.info(f"Buy order placed: {amount} {symbol} @ ${price or 'market'}")
            return order
        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
            return None
    
    def place_sell_order(self, symbol, amount, price=None):
        """Place sell order"""
        try:
            if not self.exchange:
                logger.error("Exchange not initialized")
                return None
            
            if price:
                order = self.exchange.create_limit_sell_order(symbol, amount, price)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            logger.info(f"Sell order placed: {amount} {symbol} @ ${price or 'market'}")
            return order
        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return None
    
    def get_open_orders(self, symbol=None):
        """Get open orders"""
        try:
            if not self.exchange:
                return None
            return self.exchange.fetch_open_orders(symbol)
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return None
    
    def cancel_order(self, order_id, symbol=None):
        """Cancel an order"""
        try:
            if not self.exchange:
                return None
            return self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return None

class TradingBot:
    """Main bot controller"""
    
    def __init__(self, strategy, data_fetcher, use_paper_trading=True, 
                 initial_balance=10000, symbol="BTC/USDT"):
        self.strategy = strategy
        self.data_fetcher = data_fetcher
        self.symbol = symbol
        self.use_paper_trading = use_paper_trading
        
        if use_paper_trading:
            from backend.trading.paper_trading import PaperTradingEngine
            self.engine = PaperTradingEngine(initial_balance, symbol)
        else:
            self.engine = BrokerConnector()
        
        self.last_signal = TradeSignal.HOLD
        self.is_running = False
        logger.info(f"Trading Bot initialized with {strategy.name} strategy")
    
    def execute_trade(self, signal, current_price, amount):
        """Execute trade based on signal"""
        if signal == TradeSignal.BUY:
            if self.use_paper_trading:
                self.engine.buy(current_price, amount, reason=self.strategy.name)
            else:
                self.engine.place_buy_order(self.symbol, amount)
        
        elif signal == TradeSignal.SELL:
            if self.use_paper_trading:
                self.engine.sell(current_price, amount, reason=self.strategy.name)
            else:
                self.engine.place_sell_order(self.symbol, amount)
    
    def run_iteration(self, amount_per_trade=0.001):
        """Run one iteration of the bot"""
        try:
            # Fetch latest data
            df = self.data_fetcher.fetch_ohlcv(
                self.symbol, 
                timeframe="1h",
                limit=500
            )
            
            if df.empty:
                logger.error("Failed to fetch market data")
                return False
            
            # Generate signal
            signal = self.strategy.generate_signal(df)
            current_price = df['close'].iloc[-1]
            
            # Execute trade if signal
            if signal != TradeSignal.HOLD and signal != self.last_signal:
                self.execute_trade(signal, current_price, amount_per_trade)
                self.last_signal = signal
            
            # Print stats if using paper trading
            if self.use_paper_trading:
                stats = self.engine.get_stats(current_price)
                logger.info(f"Portfolio Value: ${stats['portfolio_value']:.2f}, "
                           f"P&L: ${stats['total_pnl']:.2f} ({stats['total_pnl_percent']:.2f}%)")
            
            return True
        
        except Exception as e:
            logger.error(f"Error in bot iteration: {e}")
            return False
    
    def get_stats(self):
        """Get bot statistics"""
        if self.use_paper_trading:
            return self.engine.get_stats(self.data_fetcher.fetch_current_price(self.symbol)['price'])
        return None
