import pandas as pd
import numpy as np
from datetime import datetime
from backend.logger import logger
from backend.strategy import TradeSignal

class Backtester:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, initial_balance=10000, symbol="BTC/USDT"):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.symbol = symbol
        self.trades = []
        self.equity_curve = [initial_balance]
        self.timestamps = []
        self.positions = []
        
    def run(self, df, strategy):
        """
        Run backtest on historical data
        
        Args:
            df: DataFrame with OHLCV data
            strategy: Strategy object with generate_signal method
        
        Returns:
            dict: Backtest results
        """
        logger.info(f"Starting backtest on {len(df)} candles")
        
        self.balance = self.initial_balance
        self.trades = []
        self.equity_curve = [self.initial_balance]
        self.timestamps = []
        self.positions = []
        
        for i in range(1, len(df)):
            # Get data up to current candle
            current_df = df.iloc[:i+1].copy()
            current_price = current_df['close'].iloc[-1]
            timestamp = current_df['timestamp'].iloc[-1]
            
            # Generate signal
            signal = strategy.generate_signal(current_df)
            
            # Execute trade
            if signal == TradeSignal.BUY:
                self._buy(timestamp, current_price, strategy.name)
            elif signal == TradeSignal.SELL:
                self._sell(timestamp, current_price, strategy.name)
            
            # Calculate equity
            equity = self._calculate_equity(current_price)
            self.equity_curve.append(equity)
            self.timestamps.append(timestamp)
        
        logger.info(f"Backtest completed with {len(self.trades)} trades")
        return self._calculate_metrics()
    
    def _buy(self, timestamp, price, reason=""):
        """Record buy trade"""
        amount = self.balance / price  # Buy with all available balance
        
        if amount > 0:
            position = {
                'entry_time': timestamp,
                'entry_price': price,
                'amount': amount,
                'exit_time': None,
                'exit_price': None,
                'pnl': None,
                'reason': reason
            }
            self.positions.append(position)
            self.balance = 0
    
    def _sell(self, timestamp, price, reason=""):
        """Record sell trade"""
        if self.positions:
            position = self.positions[-1]
            if not position['exit_time']:  # Close the first open position
                position['exit_time'] = timestamp
                position['exit_price'] = price
                pnl = (price - position['entry_price']) * position['amount']
                position['pnl'] = pnl
                
                self.balance = position['amount'] * price
                
                trade = {
                    'entry_time': position['entry_time'],
                    'entry_price': position['entry_price'],
                    'exit_time': timestamp,
                    'exit_price': price,
                    'amount': position['amount'],
                    'pnl': pnl,
                    'pnl_percent': ((price - position['entry_price']) / position['entry_price']) * 100,
                    'reason': reason
                }
                self.trades.append(trade)
    
    def _calculate_equity(self, current_price):
        """Calculate current portfolio value"""
        # Cash balance + value of open positions
        open_position_value = 0
        for position in self.positions:
            if not position['exit_time']:
                open_position_value += position['amount'] * current_price
        
        return self.balance + open_position_value
    
    def _calculate_metrics(self):
        """Calculate backtest metrics"""
        if not self.trades:
            logger.warning("No trades executed during backtest")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'avg_trade_pnl': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'final_balance': self.balance
            }
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_pnl_percent = ((self.balance - self.initial_balance) / self.initial_balance) * 100
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        win_rate = (len(winning_trades) / len(self.trades) * 100) if self.trades else 0
        avg_trade_pnl = total_pnl / len(self.trades) if self.trades else 0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': self.balance,
            'trades': self.trades
        }
    
    def _calculate_max_drawdown(self):
        """Calculate maximum drawdown percentage"""
        if not self.equity_curve:
            return 0
        
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        
        return float(np.min(drawdown) * 100)
    
    def _calculate_sharpe_ratio(self, risk_free_rate=0.02):
        """Calculate Sharpe ratio"""
        if len(self.equity_curve) < 2:
            return 0
        
        returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        # Annualized Sharpe ratio (assuming hourly data -> 24*365 hours/year)
        sharpe = ((avg_return - risk_free_rate/8760) / std_return) * np.sqrt(8760)
        return float(sharpe)
    
    def print_results(self):
        """Print formatted backtest results"""
        metrics = self._calculate_metrics()
        
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Initial Balance:        ${self.initial_balance:.2f}")
        print(f"Final Balance:          ${metrics['final_balance']:.2f}")
        print(f"Total P&L:              ${metrics['total_pnl']:.2f} ({metrics['total_pnl_percent']:.2f}%)")
        print("-"*60)
        print(f"Total Trades:           {metrics['total_trades']}")
        print(f"Winning Trades:         {metrics['winning_trades']}")
        print(f"Losing Trades:          {metrics['losing_trades']}")
        print(f"Win Rate:               {metrics['win_rate']:.2f}%")
        print(f"Avg Trade P&L:          ${metrics['avg_trade_pnl']:.2f}")
        print("-"*60)
        print(f"Max Drawdown:           {metrics['max_drawdown']:.2f}%")
        print(f"Sharpe Ratio:           {metrics['sharpe_ratio']:.2f}")
        print("="*60 + "\n")
        
        return metrics
