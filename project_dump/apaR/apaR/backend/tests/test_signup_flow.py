"""Integration test for signup flow with CORS, CSRF, and session auth."""

import pytest
from app.config import Settings
from app.main import create_app
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create app with CORS enabled for Vite dev."""
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
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_signup_flow_complete(client):
    """Test full signup flow: preflight -> CSRF fetch -> signup POST."""
    # Step 1: Preflight for CSRF endpoint
    csrf_preflight = client.options(
        "/api/auth/csrf",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert csrf_preflight.status_code == 204
    assert csrf_preflight.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    print("✓ CSRF endpoint preflight works")
    
    # Step 2: Get CSRF token
    csrf_response = client.get(
        "/api/auth/csrf",
        headers={
            "Origin": "http://localhost:5173",
        },
    )
    assert csrf_response.status_code == 200
    csrf_data = csrf_response.get_json()
    assert "csrf_token" in csrf_data
    csrf_token = csrf_data["csrf_token"]
    print(f"✓ CSRF token obtained: {csrf_token[:20]}...")
    
    # Step 3: Preflight for signup
    signup_preflight = client.options(
        "/api/auth/signup",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-CSRF-Token",
        },
    )
    assert signup_preflight.status_code == 204
    assert signup_preflight.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "X-CSRF-Token" in signup_preflight.headers.get("Access-Control-Allow-Headers", "")
    print("✓ Signup endpoint preflight works")
    
    # Step 4: Perform signup
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "username": "newuser",
        },
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token,
        },
    )
    assert signup_response.status_code == 201, f"Signup failed: {signup_response.get_json()}"
    signup_data = signup_response.get_json()
    assert signup_data["ok"] is True
    assert "user" in signup_data
    assert signup_data["user"]["email"] == "newuser@example.com"
    print("✓ Signup successful")
    
    # Step 5: Verify CORS headers on response
    assert signup_response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert signup_response.headers.get("Access-Control-Allow-Credentials") == "true"
    print("✓ CORS headers present on signup response")
    
    # Step 6: Verify session is set (Set-Cookie header)
    set_cookie = signup_response.headers.get("Set-Cookie")
    assert set_cookie is not None, "No session cookie set"
    assert "apar_session" in set_cookie
    print(f"✓ Session cookie set: {set_cookie[:50]}...")
    
    # Step 7: Use the session cookie to verify auth
    me_response = client.get(
        "/api/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Cookie": set_cookie.split(";")[0],  # Get just the cookie, not attributes
        },
    )
    assert me_response.status_code == 200
    me_data = me_response.get_json()
    assert me_data.get("user") is not None
    assert me_data["user"]["email"] == "newuser@example.com"
    print("✓ Session authentication works")
    
    print("\n✅ All signup flow tests passed!")


def test_signup_with_wrong_origin_rejected(client):
    """Test that requests from wrong origin don't get CORS headers."""
    # Get CSRF token
    csrf_response = client.get(
        "/api/auth/csrf",
        headers={"Origin": "http://evil.com"},
    )
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.get_json()["csrf_token"]
    
    # Try signup from wrong origin
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "attacker@evil.com",
            "password": "malicious",
        },
        headers={
            "Origin": "http://evil.com",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token,
        },
    )
    # Signup itself works, but CORS header should be missing
    assert "Access-Control-Allow-Origin" not in signup_response.headers
    print("✓ Wrong origin correctly rejected for CORS")


def test_login_after_signup(client):
    """Test that we can login after signup."""
    # Get CSRF token
    csrf_response = client.get(
        "/api/auth/csrf",
        headers={"Origin": "http://localhost:5173"},
    )
    csrf_token = csrf_response.get_json()["csrf_token"]
    
    # Signup
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "password123",
            "username": "testuser",
        },
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token,
        },
    )
    assert signup_response.status_code == 201
    print("✓ User signed up")
    
    # Get new CSRF token for login
    csrf_response2 = client.get(
        "/api/auth/csrf",
        headers={"Origin": "http://localhost:5173"},
    )
    csrf_token2 = csrf_response2.get_json()["csrf_token"]
    
    # Try login with same credentials
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
        headers={
            "Origin": "http://localhost:5173",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token2,
        },
    )
    assert login_response.status_code == 200
    login_data = login_response.get_json()
    assert login_data["ok"] is True
    assert login_data["user"]["email"] == "testuser@example.com"
    print("✓ User logged in successfully")
