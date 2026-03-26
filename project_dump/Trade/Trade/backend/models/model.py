import numpy as np
import joblib
import os
from backend.logger import logger
from backend.config import Config

# Optional TensorFlow imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not installed. LSTM model will not be available.")

if TENSORFLOW_AVAILABLE:
    class LSTMModel:
        """LSTM model for price prediction"""
        
        def __init__(self, input_shape=(24, 11), output_shape=1):
            """
            Initialize LSTM model
            Args:
                input_shape: (sequence_length, num_features)
                output_shape: Number of output predictions
            """
            self.input_shape = input_shape
            self.output_shape = output_shape
            self.model = self._build_model()
            
        def _build_model(self):
            """Build LSTM neural network"""
            model = keras.Sequential([
                # First LSTM layer
                layers.LSTM(64, activation='relu', return_sequences=True, 
                           input_shape=self.input_shape),
                layers.Dropout(0.2),
                
                # Second LSTM layer
                layers.LSTM(32, activation='relu', return_sequences=False),
                layers.Dropout(0.2),
                
                # Dense layers
                layers.Dense(16, activation='relu'),
                layers.Dropout(0.1),
                layers.Dense(self.output_shape, activation='linear')
            ])
            
            model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("LSTM model built successfully")
            return model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """Train the model"""
        logger.info(f"Training LSTM model for {epochs} epochs")
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        logger.info("Model training completed")
        return history
    
    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)
    
    def save(self, filepath):
        """Save model to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load model from file"""
        self.model = keras.models.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")
else:
    # Placeholder when TensorFlow is not available
    class LSTMModel:
        def __init__(self, *args, **kwargs):
            raise ImportError("TensorFlow is not installed. Cannot use LSTM model.")

class RandomForestModel:
    """Random Forest model for price prediction (alternative to LSTM)"""
    
    def __init__(self):
        from sklearn.ensemble import RandomForestRegressor
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
    
    def train(self, X_train, y_train):
        """Train the model"""
        logger.info("Training Random Forest model")
        self.model.fit(X_train, y_train)
        logger.info("Random Forest training completed")
    
    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)
    
    def save(self, filepath):
        """Save model"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load model"""
        self.model = joblib.load(filepath)
        logger.info(f"Model loaded from {filepath}")

class SimpleMAModel:
    """Simple Moving Average model (baseline strategy)"""
    
    def __init__(self, fast_period=12, slow_period=26):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def predict(self, close_prices):
        """Generate buy/sell signals based on MA crossover"""
        import pandas as pd
        
        prices = pd.Series(close_prices)
        fast_ma = prices.rolling(window=self.fast_period).mean()
        slow_ma = prices.rolling(window=self.slow_period).mean()
        
        signal = np.zeros(len(prices))
        signal[self.slow_period:] = np.where(
            fast_ma[self.slow_period:] > slow_ma[self.slow_period:],
            1, -1
        )
        
        return signal
    
    def save(self, filepath):
        """Save model params"""
        joblib.dump(
            {'fast': self.fast_period, 'slow': self.slow_period},
            filepath
        )
    
    def load(self, filepath):
        """Load model params"""
        params = joblib.load(filepath)
        self.fast_period = params['fast']
        self.slow_period = params['slow']

def get_model(model_type='lstm'):
    """Factory function to get model based on config"""
    if model_type == 'lstm':
        return LSTMModel()
    elif model_type == 'random_forest':
        return RandomForestModel()
    elif model_type == 'simple_ma':
        return SimpleMAModel()
    else:
        logger.warning(f"Unknown model type: {model_type}, using LSTM")
        return LSTMModel()
