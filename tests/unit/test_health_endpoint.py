import pytest
from fastapi.testclient import TestClient
from vulcanlab_api.main import app

client = TestClient(app)

def test_health_endpoint_exists():
    """Test that /health endpoint exists."""
    response = client.get("/health")
    assert response.status_code in [200, 503]  # Either healthy or unhealthy

def test_health_endpoint_returns_json():
    """Test that /health returns JSON."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"

def test_health_endpoint_has_status():
    """Test that /health response includes status field."""
    response = client.get("/health")
    data = response.json()

    # For 200 response
    if response.status_code == 200:
        assert "status" in data
    # For 503 response, status is in detail
    elif response.status_code == 503:
        assert "detail" in data
        assert "status" in data["detail"]

def test_health_endpoint_has_service_name():
    """Test that /health response includes service identifier."""
    response = client.get("/health")
    data = response.json()

    # For 200 response
    if response.status_code == 200:
        assert "service" in data
        assert data["service"] == "vulcanlab-api"
    # For 503 response, service is in detail
    elif response.status_code == 503:
        assert "detail" in data
        assert "service" in data["detail"]
        assert data["detail"]["service"] == "vulcanlab-api"

def test_health_endpoint_has_timestamp():
    """Test that /health response includes timestamp."""
    response = client.get("/health")
    data = response.json()

    # For 200 response
    if response.status_code == 200:
        assert "timestamp" in data
    # For 503 response, timestamp is in detail
    elif response.status_code == 503:
        assert "detail" in data
        assert "timestamp" in data["detail"]

def test_health_endpoint_has_database_status():
    """Test that /health response includes database status."""
    response = client.get("/health")
    data = response.json()

    # For 200 response
    if response.status_code == 200:
        assert "database" in data
        assert data["database"] in ["connected", "disconnected", "not_configured"]
    # For 503 response, database is in detail
    elif response.status_code == 503:
        assert "detail" in data
        assert "database" in data["detail"]
