"""Test CORS configuration and auth endpoints."""

import pytest
from app.config import Settings
from app.main import create_app


@pytest.fixture
def app():
    """Create app with CORS enabled for localhost:5173."""
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
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_cors_preflight_csrf_endpoint(client):
    """Test that CORS preflight works for /api/auth/csrf."""
    response = client.options(
        "/api/auth/csrf",
        headers={
            "Origin": "http://localhost:5173",
        },
    )
    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "X-CSRF-Token" in response.headers.get("Access-Control-Allow-Headers", "")


def test_cors_csrf_token_endpoint(client):
    """Test that CSRF token endpoint returns proper CORS headers."""
    response = client.get(
        "/api/auth/csrf",
        headers={
            "Origin": "http://localhost:5173",
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "csrf_token" in data
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_preflight_login_endpoint(client):
    """Test that CORS preflight works for /api/auth/login."""
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5173",
        },
    )
    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "Content-Type" in response.headers.get("Access-Control-Allow-Headers", "")


def test_cors_wrong_origin(client):
    """Test that CORS is rejected for wrong origin."""
    response = client.get(
        "/api/auth/csrf",
        headers={
            "Origin": "http://evil.com",
        },
    )
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_csrf_token_fetch_works(client):
    """Test the actual CSRF token fetch flow."""
    response = client.get(
        "/api/auth/csrf",
        headers={
            "Origin": "http://localhost:5173",
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "csrf_token" in data
    assert data["ok"] is True
    assert len(data["csrf_token"]) > 0
