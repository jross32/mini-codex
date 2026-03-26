import pandas as pd
import numpy as np
from backend.logger import logger

class DataPreprocessor:
    """Preprocess market data for model training"""
    
    @staticmethod
    def add_technical_indicators(df):
        """Add technical indicators to OHLCV data"""
        df = df.copy()
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Average
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal']
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_sma'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_sma'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_sma'] - (df['bb_std'] * 2)
        
        # ATR (Average True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        
        # Price change
        df['price_change'] = df['close'].pct_change()
        df['price_change_5'] = df['close'].pct_change(5)
        
        logger.info("Technical indicators added to data")
        return df
    
    @staticmethod
    def normalize_data(df, columns=None):
        """Normalize features to 0-1 range"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        df_norm = df.copy()
        for col in columns:
            min_val = df_norm[col].min()
            max_val = df_norm[col].max()
            if max_val - min_val != 0:
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
        
        return df_norm
    
    @staticmethod
    def create_sequences(data, seq_length=24):
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length])
        return np.array(X), np.array(y)
    
    @staticmethod
    def prepare_training_data(df, target_col='close', seq_length=24, test_split=0.2):
        """Prepare complete training dataset"""
        # Add indicators
        df = DataPreprocessor.add_technical_indicators(df)
        
        # Remove NaN rows
        df = df.dropna()
        
        # Select features
        feature_cols = ['open', 'high', 'low', 'close', 'volume',
                       'sma_20', 'sma_50', 'ema_12', 'rsi', 'macd', 'atr']
        
        # Normalize
        df_norm = DataPreprocessor.normalize_data(df, columns=feature_cols)
        
        # Create sequences
        X, y = DataPreprocessor.create_sequences(
            df_norm[feature_cols].values, 
            seq_length=seq_length
        )
        
        # Split data
        split_idx = int(len(X) * (1 - test_split))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        logger.info(f"Training data: {X_train.shape}, Test data: {X_test.shape}")
        return X_train, X_test, y_train, y_test, df_norm
