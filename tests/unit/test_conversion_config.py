"""Unit tests for conversion config loader."""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import json

from vulcanlab.config.conversion_config import (
    get_token_threshold,
    set_token_threshold,
    load_config,
    save_config,
    DEFAULT_TOKEN_THRESHOLD
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
