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
@patch('vulcanlab_api.routers.conversion_settings.get_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.get_use_full_model')
def test_get_conversion_settings_success(mock_get_use_full, mock_get_advanced, mock_get_threshold):
    """Test GET /api/conversion/settings returns current threshold, advanced mode, and use_full_model."""
    mock_get_threshold.return_value = 20000
    mock_get_advanced.return_value = True
    mock_get_use_full.return_value = False

    response = client.get('/api/conversion/settings')

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 20000
    assert data['advanced_mode_enabled'] is True
    assert data['use_full_model'] is False


@patch('vulcanlab_api.routers.conversion_settings.get_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.get_advanced_mode_enabled')
def test_get_conversion_settings_error(mock_get_advanced, mock_get_threshold):
    """Test GET /api/conversion/settings handles errors."""
    mock_get_threshold.side_effect = Exception("Config error")

    response = client.get('/api/conversion/settings')

    assert response.status_code == 500


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.set_use_full_model')
def test_update_conversion_settings_success(mock_set_use_full, mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings updates threshold, advanced mode, and use_full_model."""
    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 18000,
            'advanced_mode_enabled': True,
            'use_full_model': True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 18000
    assert data['advanced_mode_enabled'] is True
    assert data['use_full_model'] is True
    mock_set_threshold.assert_called_once_with(18000)
    mock_set_advanced.assert_called_once_with(True)
    mock_set_use_full.assert_called_once_with(True)


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
def test_update_conversion_settings_invalid_value(mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings rejects invalid values via Pydantic."""
    # Pydantic catches negative values before our endpoint code runs
    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': -100}
    )

    assert response.status_code == 422  # Pydantic validation error


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
def test_update_conversion_settings_without_advanced_mode(mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings with only token_threshold (backward compatibility)."""
    response = client.put(
        '/api/conversion/settings',
        json={'token_threshold': 18000}
        # Note: advanced_mode_enabled is omitted, should default to False
    )

    assert response.status_code == 200
    data = response.json()
    assert data['token_threshold'] == 18000
    assert data['advanced_mode_enabled'] is False  # Should use default
    mock_set_threshold.assert_called_once_with(18000)
    mock_set_advanced.assert_called_once_with(False)  # Should be called with default


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
def test_update_conversion_settings_invalid_boolean(mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings rejects invalid boolean values."""
    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 15000,
            'advanced_mode_enabled': 123  # Integer instead of boolean
        }
    )

    assert response.status_code == 422  # Pydantic validation error


def test_update_conversion_settings_missing_field():
    """Test PUT /api/conversion/settings rejects missing required fields."""
    # token_threshold is required, advanced_mode_enabled has default
    response = client.put(
        '/api/conversion/settings',
        json={'advanced_mode_enabled': True}  # Only optional field
    )

    assert response.status_code == 422  # Pydantic validation error - token_threshold required


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.set_use_full_model')
def test_update_conversion_settings_save_error(mock_set_use_full, mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings handles save errors."""
    mock_set_threshold.side_effect = Exception("Disk full")

    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 15000,
            'advanced_mode_enabled': False,
            'use_full_model': False
        }
    )

    assert response.status_code == 500


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.set_use_full_model')
def test_update_conversion_settings_advanced_mode_save_error(mock_set_use_full, mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings handles advanced_mode save errors."""
    mock_set_advanced.side_effect = Exception("Permission denied")

    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 15000,
            'advanced_mode_enabled': True,
            'use_full_model': False
        }
    )

    assert response.status_code == 500


@patch('vulcanlab_api.routers.conversion_settings.get_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.get_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.get_use_full_model')
def test_get_conversion_settings_with_use_full_model_true(mock_get_use_full, mock_get_advanced, mock_get_threshold):
    """Test GET /api/conversion/settings returns use_full_model=True when configured."""
    mock_get_threshold.return_value = 15000
    mock_get_advanced.return_value = False
    mock_get_use_full.return_value = True

    response = client.get('/api/conversion/settings')

    assert response.status_code == 200
    data = response.json()
    assert data['use_full_model'] is True


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.set_use_full_model')
def test_update_conversion_settings_only_use_full_model(mock_set_use_full, mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings with only use_full_model changed."""
    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 15000,
            'advanced_mode_enabled': False,
            'use_full_model': True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['use_full_model'] is True
    mock_set_use_full.assert_called_once_with(True)


@patch('vulcanlab_api.routers.conversion_settings.set_token_threshold')
@patch('vulcanlab_api.routers.conversion_settings.set_advanced_mode_enabled')
@patch('vulcanlab_api.routers.conversion_settings.set_use_full_model')
def test_update_conversion_settings_use_full_model_default(mock_set_use_full, mock_set_advanced, mock_set_threshold):
    """Test PUT /api/conversion/settings defaults use_full_model to False if omitted."""
    response = client.put(
        '/api/conversion/settings',
        json={
            'token_threshold': 15000,
            'advanced_mode_enabled': True
            # use_full_model omitted - should default to False
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['use_full_model'] is False
    mock_set_use_full.assert_called_once_with(False)
