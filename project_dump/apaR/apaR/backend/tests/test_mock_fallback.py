"""Tests for mock data fallback when no real dataset exists."""
import pytest
from pathlib import Path
from app.config import Settings
from app.main import create_app
from app.data_store import DataStore


@pytest.fixture
def app():
    """Create app that will fallback to mock data."""
    settings = Settings(
        environment="development",
        secret_key="test-secret",
        database_url="sqlite:///:memory:",
        api_host="127.0.0.1",
        api_port=5000,
        data_dir="/tmp/nonexistent-data-dir",  # Non-existent dir forces mock fallback
        cors_allow_origin="http://localhost:5173",
    )
    app = create_app(settings)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_mock_data_fallback_when_no_data_dir(tmp_path):
    """When data_dir doesn't exist and no active_dataset.json, load mock data."""
    nonexistent_dir = tmp_path / "nonexistent"
    
    ds = DataStore(str(nonexistent_dir))
    dataset = ds.load()
    
    # Should have loaded mock data
    assert ds.is_mock_data is True
    assert dataset["meta"]["source"] == "mock"
    assert dataset["league"]["name"] == "APA Rio Grande Valley"
    assert len(dataset["players"]) == 51


def test_meta_endpoint_shows_mock_data_flag(client):
    """GET /api/meta includes source, meta_banner, and counts for UI."""
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify source field
    assert "source" in data
    assert data["source"] == "mock"
    
    # Verify meta_banner for frontend display
    assert "meta_banner" in data
    assert "Using mock data" in data["meta_banner"]
    
    # Verify active_file
    assert "active_file" in data
    assert data["active_file"] == "leagueData.json"
    
    # Verify counts for tooltip
    assert "counts" in data
    assert data["counts"]["players"] == 51
    assert data["counts"]["teams"] == 10
    assert data["counts"]["divisions"] == 3
    assert data["counts"]["matches"] == 13
    assert data["counts"]["locations"] == 5
    
    # Verify generated_at
    assert "generated_at" in data
    assert data["generated_at"] is not None


def test_health_endpoint_shows_data_source(client):
    """GET /api/health shows data status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["data"]["status"] == "loaded"
    assert "last_loaded_at" in data["data"]
    assert "source" in data["data"]
