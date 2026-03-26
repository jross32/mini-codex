"""Test fixtures and utilities."""
import os
import pytest
import tempfile
import sqlite3
from contextlib import contextmanager
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    # Use NamedTemporaryFile with delete=True for automatic cleanup
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        path = tmp.name
    
    # Override DB path for testing
    import database
    database.DB_NAME = path
    
    yield path
    
    try:
        os.unlink(path)
    except OSError:
        pass  # File might be locked or already deleted
    
@contextmanager
def temp_db_connection():
    """Get a connection to the test database."""
    import database
    conn = database.connect()
    try:
        yield conn
    finally:
        conn.close()
        
@pytest.fixture
def app_client():
    """Create a test Flask client."""
    import app
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False  # disable CSRF for testing
    return app.app.test_client()