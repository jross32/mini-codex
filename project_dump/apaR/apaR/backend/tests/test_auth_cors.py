"""Test auth with CORS."""

import pytest
from app.config import Settings
from app.main import create_app
from werkzeug.security import generate_password_hash
from app.models import User


@pytest.fixture
def app():
    """Create app with CORS enabled."""
    settings = Settings(
        environment="development",
        secret_key="test-secret",
        database_url="sqlite:///:memory:",
        api_host="127.0.0.1",
        api_port=5000,
        data_dir="/tmp",
        cors_allow_origin="http://localhost:5173",
    )
    app = create_app(settings)
    
    # Create tables
    with app.app_context():
        from app.models import Base
        
        engine = app.config["DB_ENGINE"]
        Base.metadata.create_all(engine)
        
        # Create a test user
        db_session = app.config["DB_SESSION"]
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash=generate_password_hash("password123"),
        )
        db_session.add(user)
        db_session.commit()
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_login_with_cors_headers(client):
    """Test that login works with CORS headers."""
    # First get CSRF token
    csrf_response = client.get(
        "/api/auth/csrf",
        headers={"Origin": "http://localhost:5173"},
    )
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.get_json()["csrf_token"]
    
    # Then login with CSRF token
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"},
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token,
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert "user" in data
    # Check CORS header is present
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_login_preflight(client):
    """Test that login preflight request works."""
    # First get CSRF token
    csrf_response = client.get(
        "/api/auth/csrf",
        headers={"Origin": "http://localhost:5173"},
    )
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.get_json()["csrf_token"]
    
    # Then do preflight
    preflight_response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-CSRF-Token",
        },
    )
    assert preflight_response.status_code == 204
    assert preflight_response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    
    # Then actual login with CSRF token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"},
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token,
        },
    )
    assert login_response.status_code == 200
    assert login_response.get_json()["ok"] is True
