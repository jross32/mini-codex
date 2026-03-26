import pandas as pd
import numpy as np
from datetime import datetime
from backend.logger import logger
from enum import Enum

class TradeSignal(Enum):
    """Trade signal types"""
    BUY = 1
    SELL = -1
    HOLD = 0

class StrategyEngine:
    """Base strategy engine for generating trading signals"""
    
    def __init__(self, name="DefaultStrategy"):
        self.name = name
        self.trades = []
        self.last_signal = TradeSignal.HOLD
        
    def generate_signal(self, df):
        """Generate trading signal from data"""
        raise NotImplementedError("Subclasses must implement generate_signal")
    
    def log_trade(self, signal, price, reason=""):
        """Log trade signal"""
        trade = {
            'timestamp': datetime.now(),
            'signal': signal.name,
            'price': price,
            'reason': reason
        }
        self.trades.append(trade)
        logger.info(f"[{self.name}] Signal: {signal.name} @ ${price:.2f} - {reason}")

class MovingAverageCrossoverStrategy(StrategyEngine):
    """
    Simple but effective strategy using moving average crossover
    Buy when fast MA > slow MA, Sell when fast MA < slow MA
    """
    
    def __init__(self, fast_period=12, slow_period=26):
        super().__init__("MA_Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def generate_signal(self, df):
        """Generate signal based on MA crossover"""
        if len(df) < self.slow_period:
            return TradeSignal.HOLD
        
        df = df.copy()
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
        current_fast = df['fast_ma'].iloc[-1]
        current_slow = df['slow_ma'].iloc[-1]
        prev_fast = df['fast_ma'].iloc[-2]
        prev_slow = df['slow_ma'].iloc[-2]
        
        # Crossover logic
        if pd.isna(current_fast) or pd.isna(current_slow):
            return TradeSignal.HOLD
        
        current_price = df['close'].iloc[-1]
        
        # Buy signal: fast MA crosses above slow MA
        if prev_fast <= prev_slow and current_fast > current_slow:
            self.last_signal = TradeSignal.BUY
            self.log_trade(TradeSignal.BUY, current_price, 
                          f"Fast MA({self.fast_period}) > Slow MA({self.slow_period})")
            return TradeSignal.BUY
        
        # Sell signal: fast MA crosses below slow MA
        elif prev_fast >= prev_slow and current_fast < current_slow:
            self.last_signal = TradeSignal.SELL
            self.log_trade(TradeSignal.SELL, current_price,
                          f"Fast MA({self.fast_period}) < Slow MA({self.slow_period})")
            return TradeSignal.SELL
        
        return TradeSignal.HOLD

class RSIStrategy(StrategyEngine):
    """RSI (Relative Strength Index) based strategy"""
    
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__("RSI_Strategy")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signal(self, df):
        """Generate signal based on RSI"""
        if len(df) < self.period:
            return TradeSignal.HOLD
        
        df = df.copy()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if pd.isna(current_rsi):
            return TradeSignal.HOLD
        
        # Oversold = Buy opportunity
        if current_rsi < self.oversold:
            self.last_signal = TradeSignal.BUY
            self.log_trade(TradeSignal.BUY, current_price,
                          f"RSI oversold: {current_rsi:.2f}")
            return TradeSignal.BUY
        
        # Overbought = Sell opportunity
        elif current_rsi > self.overbought:
            self.last_signal = TradeSignal.SELL
            self.log_trade(TradeSignal.SELL, current_price,
                          f"RSI overbought: {current_rsi:.2f}")
            return TradeSignal.SELL
        
        return TradeSignal.HOLD

class MLBasedStrategy(StrategyEngine):
    """Strategy using machine learning model predictions"""
    
    def __init__(self, model, threshold=0.02):
        super().__init__("ML_Strategy")
        self.model = model
        self.threshold = threshold  # Price change threshold for signals
        
    def generate_signal(self, df):
        """Generate signal based on ML model prediction"""
        if len(df) < 24:  # Minimum sequence length
            return TradeSignal.HOLD
        
        # Prepare data for model
        from backend.data.preprocessor import DataPreprocessor
        
        df_processed = DataPreprocessor.add_technical_indicators(df.copy())
        df_processed = DataPreprocessor.normalize_data(df_processed)
        
        feature_cols = ['open', 'high', 'low', 'close', 'volume',
                       'sma_20', 'sma_50', 'ema_12', 'rsi', 'macd', 'atr']
        
        X = df_processed[feature_cols].tail(24).values.reshape(1, 24, -1)
        
        try:
            prediction = self.model.predict(X, verbose=0)[0][0]
            
            current_price = df['close'].iloc[-1]
            current_rsi = self._calculate_rsi(df)
            
            # Generate signal based on prediction and RSI
            if prediction > self.threshold and current_rsi < 70:
                self.last_signal = TradeSignal.BUY
                self.log_trade(TradeSignal.BUY, current_price,
                              f"ML prediction: {prediction:.4f}")
                return TradeSignal.BUY
            
            elif prediction < -self.threshold and current_rsi > 30:
                self.last_signal = TradeSignal.SELL
                self.log_trade(TradeSignal.SELL, current_price,
                              f"ML prediction: {prediction:.4f}")
                return TradeSignal.SELL
            
            return TradeSignal.HOLD
        
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return TradeSignal.HOLD
    
    @staticmethod
    def _calculate_rsi(df, period=14):
        """Calculate RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return (100 - (100 / (1 + rs))).iloc[-1]

class HybridStrategy(StrategyEngine):
    """Combine multiple strategies for robust signals"""
    
    def __init__(self, strategies):
        super().__init__("Hybrid_Strategy")
        self.strategies = strategies
        
    def generate_signal(self, df):
        """Generate signal by combining multiple strategies"""
        signals = []
        
        for strategy in self.strategies:
            signal = strategy.generate_signal(df)
            if signal != TradeSignal.HOLD:
                signals.append(signal.value)
        
        if not signals:
            return TradeSignal.HOLD
        
        # Buy if majority of strategies agree
        signal_sum = sum(signals)
        current_price = df['close'].iloc[-1]
        
        if signal_sum > 0:
            self.last_signal = TradeSignal.BUY
            self.log_trade(TradeSignal.BUY, current_price,
                          f"Consensus: {len(signals)} strategies agree")
            return TradeSignal.BUY
        elif signal_sum < 0:
            self.last_signal = TradeSignal.SELL
            self.log_trade(TradeSignal.SELL, current_price,
                          f"Consensus: {len(signals)} strategies agree")
            return TradeSignal.SELL
        
        return TradeSignal.HOLD

def get_strategy(strategy_type='ma_crossover', **kwargs):
    """Factory function to get strategy"""
    if strategy_type == 'ma_crossover':
        return MovingAverageCrossoverStrategy(
            kwargs.get('fast_period', 12),
            kwargs.get('slow_period', 26)
        )
    elif strategy_type == 'rsi':
        return RSIStrategy(
            kwargs.get('period', 14),
            kwargs.get('overbought', 70),
            kwargs.get('oversold', 30)
        )
    elif strategy_type == 'ml':
        return MLBasedStrategy(kwargs.get('model'), kwargs.get('threshold', 0.02))
    else:
        logger.warning(f"Unknown strategy: {strategy_type}, using MA_Crossover")
        return MovingAverageCrossoverStrategy()
