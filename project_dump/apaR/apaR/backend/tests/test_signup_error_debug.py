"""Test that signup errors include debug info in development."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

from sqlalchemy.exc import OperationalError

from app.main import app


def test_signup_error_shows_debug_in_dev():
    """Verify that signup errors include exception details in development mode."""
    with app.test_client() as client:
        # Get CSRF token
        csrf_resp = client.get("/api/auth/csrf")
        csrf_token = csrf_resp.json["csrf_token"]
        
        # Mock the actual commit call to fail after validation passes
        original_session = app.config["DB_SESSION"]
        
        with patch.object(original_session, "commit") as mock_commit:
            # Create a database error
            mock_commit.side_effect = OperationalError("Connection lost", "", "")
            
            # Try to sign up
            response = client.post(
                "/api/auth/signup",
                json={"email": "dev-test@example.com", "username": "devtest", "password": "password123"},
                headers={"X-CSRF-Token": csrf_token},
            )
        
        assert response.status_code == 500
        data = response.json
        assert data["ok"] is False
        assert data["error"]["code"] == "signup_failed"
        
        # In dev, should include debug info
        assert "debug" in data["error"], f"Expected debug in error, got: {data['error']}"
        debug = data["error"]["debug"]
        assert debug["exception_type"] == "OperationalError"
        assert "Connection lost" in debug["exception_message"]


def test_signup_error_generic_in_production():
    """Verify that signup errors hide details in production mode."""
    with app.app_context():
        app.config["ENV"] = "production"
        original_session = app.config["DB_SESSION"]
        
        with app.test_client() as client:
            # Get CSRF token
            csrf_resp = client.get("/api/auth/csrf")
            csrf_token = csrf_resp.json["csrf_token"]
            
            with patch.object(original_session, "commit") as mock_commit:
                # Create a database error
                mock_commit.side_effect = OperationalError("Connection lost", "", "")
                
                # Try to sign up
                response = client.post(
                    "/api/auth/signup",
                    json={"email": "prod-test@example.com", "username": "prodtest", "password": "password123"},
                    headers={"X-CSRF-Token": csrf_token},
                )
            
            assert response.status_code == 500
            data = response.json
            assert data["ok"] is False
            assert data["error"]["code"] == "signup_failed"
            
            # In production, should NOT include debug info
            assert "debug" not in data["error"], f"Debug should not be in production error: {data['error']}"
        
        # Reset to development
        app.config["ENV"] = "development"
