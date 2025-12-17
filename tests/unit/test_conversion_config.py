"""Unit tests for conversion config loader."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import json

from vulcanlab.config.conversion_config import (
    get_token_threshold,
    set_token_threshold,
    get_advanced_mode_enabled,
    set_advanced_mode_enabled,
    get_use_full_model,
    set_use_full_model,
    load_config,
    save_config,
    DEFAULT_TOKEN_THRESHOLD,
    DEFAULT_ADVANCED_MODE_ENABLED,
    DEFAULT_USE_FULL_MODEL
)


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"token_threshold": 20000}}')
def test_get_token_threshold_from_config(mock_file, mock_path):
    """Test reading token threshold from config file."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == 20000


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{}')
def test_get_token_threshold_default(mock_file, mock_path):
    """Test default token threshold when not in config."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
def test_get_token_threshold_missing_file(mock_path):
    """Test default threshold when config file doesn't exist."""
    mock_path.return_value = MagicMock(exists=lambda: False)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"token_threshold": -100}}')
def test_get_token_threshold_invalid_value(mock_file, mock_path):
    """Test default threshold when config has invalid value."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    threshold = get_token_threshold()

    assert threshold == DEFAULT_TOKEN_THRESHOLD


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_token_threshold_success(mock_save, mock_load, mock_path):
    """Test setting token threshold successfully."""
    mock_load.return_value = {}

    set_token_threshold(25000)

    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['token_threshold'] == 25000


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_token_threshold_preserves_existing_config(mock_save, mock_load, mock_path):
    """Test that setting threshold preserves other config sections."""
    mock_load.return_value = {
        'database': {'host': 'localhost'},
        'llm': {'model': 'gpt-4'}
    }

    set_token_threshold(18000)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['database']['host'] == 'localhost'
    assert saved_config['llm']['model'] == 'gpt-4'
    assert saved_config['conversion']['token_threshold'] == 18000


def test_set_token_threshold_invalid_zero():
    """Test that zero threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold(0)


def test_set_token_threshold_invalid_negative():
    """Test that negative threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold(-5000)


def test_set_token_threshold_invalid_type():
    """Test that non-integer threshold raises ValueError."""
    with pytest.raises(ValueError, match="positive integer"):
        set_token_threshold("15000")  # String instead of int


# Tests for get_advanced_mode_enabled

@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"advanced_mode_enabled": true}}')
def test_get_advanced_mode_enabled_from_config(mock_file, mock_path):
    """Test reading advanced_mode_enabled from config file."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    enabled = get_advanced_mode_enabled()

    assert enabled is True


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{}')
def test_get_advanced_mode_enabled_default(mock_file, mock_path):
    """Test default advanced_mode_enabled when not in config."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    enabled = get_advanced_mode_enabled()

    assert enabled is False
    assert enabled == DEFAULT_ADVANCED_MODE_ENABLED


@patch('vulcanlab.config.conversion_config.get_config_path')
def test_get_advanced_mode_enabled_missing_file(mock_path):
    """Test default when config file doesn't exist."""
    mock_path.return_value = MagicMock(exists=lambda: False)

    enabled = get_advanced_mode_enabled()

    assert enabled is False


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"advanced_mode_enabled": "yes"}}')
def test_get_advanced_mode_enabled_invalid_value(mock_file, mock_path):
    """Test default when config has invalid value (string instead of bool)."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    enabled = get_advanced_mode_enabled()

    assert enabled is False  # Falls back to default


# Tests for set_advanced_mode_enabled

@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_advanced_mode_enabled_success(mock_save, mock_load, mock_path):
    """Test setting advanced_mode_enabled successfully."""
    mock_load.return_value = {}

    set_advanced_mode_enabled(True)

    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['advanced_mode_enabled'] is True


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_advanced_mode_enabled_false(mock_save, mock_load, mock_path):
    """Test setting advanced_mode_enabled to False."""
    mock_load.return_value = {}

    set_advanced_mode_enabled(False)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['advanced_mode_enabled'] is False


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_advanced_mode_enabled_preserves_existing_config(mock_save, mock_load, mock_path):
    """Test that setting advanced_mode_enabled preserves other config sections."""
    mock_load.return_value = {
        'database': {'host': 'localhost'},
        'conversion': {'token_threshold': 20000}
    }

    set_advanced_mode_enabled(True)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['database']['host'] == 'localhost'
    assert saved_config['conversion']['token_threshold'] == 20000
    assert saved_config['conversion']['advanced_mode_enabled'] is True


def test_set_advanced_mode_enabled_invalid_type_string():
    """Test that non-boolean value raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_advanced_mode_enabled("true")


def test_set_advanced_mode_enabled_invalid_type_int():
    """Test that integer instead of boolean raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_advanced_mode_enabled(1)


def test_set_advanced_mode_enabled_invalid_type_none():
    """Test that None instead of boolean raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_advanced_mode_enabled(None)


# Tests for get_use_full_model

@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"use_full_model": true}}')
def test_get_use_full_model_from_config(mock_file, mock_path):
    """Test reading use_full_model from config file."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    use_full = get_use_full_model()

    assert use_full is True


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{}')
def test_get_use_full_model_default(mock_file, mock_path):
    """Test default use_full_model when not in config."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    use_full = get_use_full_model()

    assert use_full is False
    assert use_full == DEFAULT_USE_FULL_MODEL


@patch('vulcanlab.config.conversion_config.get_config_path')
def test_get_use_full_model_missing_file(mock_path):
    """Test default when config file doesn't exist."""
    mock_path.return_value = MagicMock(exists=lambda: False)

    use_full = get_use_full_model()

    assert use_full is False


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('builtins.open', new_callable=mock_open, read_data='{"conversion": {"use_full_model": "yes"}}')
def test_get_use_full_model_invalid_value(mock_file, mock_path):
    """Test default when config has invalid value (string instead of bool)."""
    mock_path.return_value = MagicMock(exists=lambda: True)

    use_full = get_use_full_model()

    assert use_full is False  # Falls back to default


# Tests for set_use_full_model

@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_use_full_model_success(mock_save, mock_load, mock_path):
    """Test setting use_full_model successfully."""
    mock_load.return_value = {}

    set_use_full_model(True)

    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['use_full_model'] is True


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_use_full_model_false(mock_save, mock_load, mock_path):
    """Test setting use_full_model to False."""
    mock_load.return_value = {}

    set_use_full_model(False)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['conversion']['use_full_model'] is False


@patch('vulcanlab.config.conversion_config.get_config_path')
@patch('vulcanlab.config.conversion_config.load_config')
@patch('vulcanlab.config.conversion_config.save_config')
def test_set_use_full_model_preserves_existing_config(mock_save, mock_load, mock_path):
    """Test that setting use_full_model preserves other config sections."""
    mock_load.return_value = {
        'database': {'host': 'localhost'},
        'conversion': {'token_threshold': 20000, 'advanced_mode_enabled': True}
    }

    set_use_full_model(True)

    saved_config = mock_save.call_args[0][0]
    assert saved_config['database']['host'] == 'localhost'
    assert saved_config['conversion']['token_threshold'] == 20000
    assert saved_config['conversion']['advanced_mode_enabled'] is True
    assert saved_config['conversion']['use_full_model'] is True


def test_set_use_full_model_invalid_type_string():
    """Test that non-boolean value raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_use_full_model("true")


def test_set_use_full_model_invalid_type_int():
    """Test that integer instead of boolean raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_use_full_model(1)


def test_set_use_full_model_invalid_type_none():
    """Test that None instead of boolean raises ValueError."""
    with pytest.raises(ValueError, match="must be a boolean"):
        set_use_full_model(None)
