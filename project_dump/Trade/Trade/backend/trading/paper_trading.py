import pandas as pd
from datetime import datetime
from backend.logger import logger
from backend.strategy import TradeSignal

class Position:
    """Represents an open trading position"""
    
    def __init__(self, symbol, entry_price, amount, entry_time, position_id):
        self.symbol = symbol
        self.entry_price = entry_price
        self.amount = amount
        self.entry_time = entry_time
        self.position_id = position_id
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0
        self.pnl_percent = 0
        self.is_open = True
    
    def close(self, exit_price, exit_time):
        """Close the position"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.pnl = (exit_price - self.entry_price) * self.amount
        self.pnl_percent = ((exit_price - self.entry_price) / self.entry_price) * 100
        self.is_open = False
    
    def get_unrealized_pnl(self, current_price):
        """Calculate unrealized P&L"""
        if self.is_open:
            pnl = (current_price - self.entry_price) * self.amount
            return pnl, (pnl / (self.entry_price * self.amount)) * 100
        return 0, 0
    
    def __repr__(self):
        status = "OPEN" if self.is_open else "CLOSED"
        return f"Position({self.symbol}, {self.amount}, Entry: ${self.entry_price:.2f}, {status})"

class PaperTradingEngine:
    """Simulate trading without real money"""
    
    def __init__(self, initial_balance=10000, symbol="BTC/USDT"):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.symbol = symbol
        self.positions = []
        self.trade_history = []
        self.position_counter = 0
        self.start_time = datetime.now()
        
        logger.info(f"Paper Trading Engine initialized: Balance=${self.balance:.2f}")
    
    def buy(self, price, amount, reason=""):
        """Execute buy order"""
        cost = price * amount
        
        if cost > self.balance:
            logger.warning(f"Insufficient balance. Need: ${cost:.2f}, Have: ${self.balance:.2f}")
            return None
        
        self.balance -= cost
        self.position_counter += 1
        
        position = Position(
            symbol=self.symbol,
            entry_price=price,
            amount=amount,
            entry_time=datetime.now(),
            position_id=self.position_counter
        )
        
        self.positions.append(position)
        
        trade = {
            'timestamp': datetime.now(),
            'type': 'BUY',
            'price': price,
            'amount': amount,
            'cost': cost,
            'reason': reason,
            'balance': self.balance
        }
        self.trade_history.append(trade)
        
        logger.info(f"BUY Order: {amount} {self.symbol.split('/')[0]} @ ${price:.2f} - {reason}")
        return position
    
    def sell(self, price, amount=None, reason=""):
        """Execute sell order"""
        # Sell first open position or specified amount
        open_positions = [p for p in self.positions if p.is_open]
        
        if not open_positions:
            logger.warning("No open positions to sell")
            return None
        
        if amount is None:
            amount = open_positions[0].amount
        
        # Close positions FIFO
        remaining = amount
        closed_positions = []
        
        for position in open_positions:
            if remaining <= 0:
                break
            
            amount_to_close = min(remaining, position.amount)
            close_amount = amount_to_close
            position.close(price, datetime.now())
            closed_positions.append(position)
            remaining -= amount_to_close
        
        revenue = price * amount
        self.balance += revenue
        
        trade = {
            'timestamp': datetime.now(),
            'type': 'SELL',
            'price': price,
            'amount': amount,
            'revenue': revenue,
            'reason': reason,
            'balance': self.balance,
            'positions_closed': closed_positions
        }
        self.trade_history.append(trade)
        
        total_pnl = sum(p.pnl for p in closed_positions)
        logger.info(f"SELL Order: {amount} {self.symbol.split('/')[0]} @ ${price:.2f} "
                   f"- P&L: ${total_pnl:.2f} - {reason}")
        
        return closed_positions
    
    def get_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        cash = self.balance
        holdings = sum(p.amount * current_price for p in self.positions if p.is_open)
        return cash + holdings
    
    def get_unrealized_pnl(self, current_price):
        """Get unrealized P&L from open positions"""
        total_pnl = 0
        for position in self.positions:
            if position.is_open:
                pnl, _ = position.get_unrealized_pnl(current_price)
                total_pnl += pnl
        return total_pnl
    
    def get_realized_pnl(self):
        """Get realized P&L from closed positions"""
        return sum(p.pnl for p in self.positions if not p.is_open)
    
    def get_stats(self, current_price):
        """Get trading statistics"""
        portfolio_value = self.get_portfolio_value(current_price)
        realized_pnl = self.get_realized_pnl()
        unrealized_pnl = self.get_unrealized_pnl(current_price)
        total_pnl = realized_pnl + unrealized_pnl
        
        open_positions = [p for p in self.positions if p.is_open]
        closed_positions = [p for p in self.positions if not p.is_open]
        
        win_count = sum(1 for p in closed_positions if p.pnl > 0)
        loss_count = sum(1 for p in closed_positions if p.pnl < 0)
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'portfolio_value': portfolio_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / self.initial_balance) * 100,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'wins': win_count,
            'losses': loss_count,
            'win_rate': (win_count / (win_count + loss_count) * 100) if (win_count + loss_count) > 0 else 0,
            'total_trades': len(self.trade_history)
        }
    
    def print_stats(self, current_price):
        """Print formatted statistics"""
        stats = self.get_stats(current_price)
        print("\n" + "="*50)
        print("PAPER TRADING STATISTICS")
        print("="*50)
        print(f"Initial Balance:    ${stats['initial_balance']:.2f}")
        print(f"Current Balance:    ${stats['current_balance']:.2f}")
        print(f"Portfolio Value:    ${stats['portfolio_value']:.2f}")
        print(f"Total P&L:          ${stats['total_pnl']:.2f} ({stats['total_pnl_percent']:.2f}%)")
        print(f"Realized P&L:       ${stats['realized_pnl']:.2f}")
        print(f"Unrealized P&L:     ${stats['unrealized_pnl']:.2f}")
        print(f"Open Positions:     {stats['open_positions']}")
        print(f"Closed Positions:   {stats['closed_positions']}")
        print(f"Win Rate:           {stats['win_rate']:.2f}% ({stats['wins']}W / {stats['losses']}L)")
        print(f"Total Trades:       {stats['total_trades']}")
        print("="*50 + "\n")
    
    def reset(self):
        """Reset the engine"""
        self.balance = self.initial_balance
        self.positions = []
        self.trade_history = []
        self.position_counter = 0
        logger.info("Paper Trading Engine reset")
