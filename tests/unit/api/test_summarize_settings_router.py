import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status

from vulcanlab_api.main import app
from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.summarize_settings import SummarizeSettings

client = TestClient(app)

# Mock dependency
@pytest.fixture
def mock_db():
    mock = MagicMock(spec=Session)
    yield mock

@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db_session] = lambda: mock_db
    yield
    app.dependency_overrides.pop(get_db_session)

@pytest.mark.usefixtures("override_get_db")
class TestSummarizeSettingsRouter:

    def test_get_settings_default(self, mock_db):
        # Mock database returning nothing
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        response = client.get("/api/v1/settings/summarize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["h1_always_summarize"] is True
        assert data["h2_top_percent"] == 100
        assert data["h3_salience_threshold"] == 0.5

    def test_get_settings_existing(self, mock_db):
        # Mock database returning a record
        existing = SummarizeSettings(h2_top_percent=50, h3_salience_threshold=0.6)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result
        
        response = client.get("/api/v1/settings/summarize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["h2_top_percent"] == 50
        assert data["h3_salience_threshold"] == 0.6

    def test_update_settings_success(self, mock_db):
        # Mock existing settings
        existing = SummarizeSettings()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result
        
        update_data = {"h2_top_percent": 75, "h3_salience_threshold": 0.4}
        response = client.put("/api/v1/settings/summarize", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["h2_top_percent"] == 75
        assert data["h3_salience_threshold"] == 0.4
        mock_db.commit.assert_called_once()

    def test_update_settings_create_new(self, mock_db):
        # Mock no existing settings
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        update_data = {"h2_top_percent": 80}
        response = client.put("/api/v1/settings/summarize", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["h2_top_percent"] == 80
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_settings_validation_errors(self, mock_db):
        # Test h2_top_percent range
        response = client.put("/api/v1/settings/summarize", json={"h2_top_percent": 150})
        assert response.status_code == 400
        assert "h2_top_percent" in response.json()["detail"]
        
        # Test threshold range
        response = client.put("/api/v1/settings/summarize", json={"h3_salience_threshold": 1.5})
        assert response.status_code == 400
        assert "h3_salience_threshold" in response.json()["detail"]
        
        # Test negative value
        response = client.put("/api/v1/settings/summarize", json={"heading_depth_weight": -0.1})
        assert response.status_code == 400
        assert "heading_depth_weight" in response.json()["detail"]

    def test_update_settings_partial(self, mock_db):
        # Mock existing settings
        existing = SummarizeSettings(h1_always_summarize=False, h2_top_percent=30)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result
        
        # Update only one field
        response = client.put("/api/v1/settings/summarize", json={"h2_top_percent": 40})
        
        assert response.status_code == 200
        data = response.json()
        assert data["h2_top_percent"] == 40
        assert data["h1_always_summarize"] is False # Remained unchanged
