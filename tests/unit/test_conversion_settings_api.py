"""Unit tests for conversion settings API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from vulcanlab_api.routers.conversion_settings import router


# Mock app for testing
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch('vulcanlab_api.routers.conversion_settings.get_token_threshold')
def test_get_conversion_settings_success(mock_get):
    """Test GET /api/conversion/settings returns current threshold."""
    mock_get.return_value = 20000

    response = client.get('/api/conversion/settings')

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 20000


@patch('vulcanlab_api.routers.conversion_settings.get_token_threshold')
def test_get_conversion_settings_error(mock_get):
    """Test GET /api/conversion/settings handles errors."""
    mock_get.side_effect = Exception("Config error")

    response = client.get('/api/conversion/settings')

    assert response.status_code == 500


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
def test_update_conversion_settings_success(mock_set):
    """Test PUT /api/conversion/settings updates threshold."""
    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': 18000}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 18000
    mock_set.assert_called_once_with(18000)


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
def test_update_conversion_settings_invalid_value(mock_set):
    """Test PUT /api/conversion/settings rejects invalid values via Pydantic."""
    # Pydantic catches negative values before our endpoint code runs
    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': -100}
    )

    assert response.status_code == 422  # Pydantic validation error


def test_update_conversion_settings_missing_field():
    """Test PUT /api/conversion/settings rejects missing fields."""
    response = client.put(
        '/api/conversion/settings',
        json={}
    )

    assert response.status_code == 422  # Pydantic validation error


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
def test_update_conversion_settings_save_error(mock_set):
    """Test PUT /api/conversion/settings handles save errors."""
    mock_set.side_effect = Exception("Disk full")

    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': 15000}
    )

    assert response.status_code == 500
