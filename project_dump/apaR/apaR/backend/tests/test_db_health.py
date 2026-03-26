"""Test database health check endpoint."""
from __future__ import annotations

from app.main import app


def test_db_health_check_sqlite():
    """Verify database health check works and returns correct info."""
    with app.test_client() as client:
        response = client.get("/api/db-health")
        
        assert response.status_code == 200
        data = response.json
        
        assert data["ok"] is True
        assert data["db_kind"] == "sqlite"
        assert data["db_connected"] is True
        assert "users" in data["tables_present"]
        assert "user_contexts" in data["tables_present"]
        assert data["required_tables"] == ["user_contexts", "users"]
        assert data["tables_ok"] is True
        assert data["last_error"] is None


def test_db_health_check_no_secrets():
    """Verify health check doesn't expose database credentials."""
    with app.test_client() as client:
        response = client.get("/api/db-health")
        
        data = response.json
        response_str = str(response.json)
        
        # Make sure no connection strings or secrets leak
        assert "sqlite:///" not in response_str
        assert "postgres://" not in response_str
        assert "password" not in response_str.lower()
        assert "@" not in response_str  # No user:pass@host patterns
