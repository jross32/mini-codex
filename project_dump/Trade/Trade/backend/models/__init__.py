try:
    from backend.models.model import LSTMModel, RandomForestModel, SimpleMAModel, get_model
    __all__ = ['LSTMModel', 'RandomForestModel', 'SimpleMAModel', 'get_model']
except ImportError:
    # TensorFlow not installed, use only RandomForest and SimpleMA
    from backend.models.model import RandomForestModel, SimpleMAModel, get_model
    __all__ = ['RandomForestModel', 'SimpleMAModel', 'get_model']
