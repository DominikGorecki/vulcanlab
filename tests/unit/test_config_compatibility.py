import logging
import pytest
from vulcanlab.utils.rag_config_loader import get_config_value

def test_get_config_value_current_location():
    config = {
        "retrieval": {
            "dense_limit": 20
        }
    }
    assert get_config_value(config, "retrieval", "dense_limit", 10) == 20

def test_get_config_value_deprecated_location(caplog):
    config = {
        "retrieval": {
            "_deprecated": {
                "dense_limit": 15
            }
        }
    }
    with caplog.at_level(logging.WARNING):
        assert get_config_value(config, "retrieval", "dense_limit", 10) == 15
    assert "Using deprecated config key: retrieval.dense_limit" in caplog.text

def test_get_config_value_fallback():
    config = {
        "retrieval": {}
    }
    assert get_config_value(config, "retrieval", "dense_limit", 10) == 10

def test_get_config_value_missing_section():
    config = {}
    assert get_config_value(config, "retrieval", "dense_limit", 10) == 10

def test_get_config_value_precedence():
    # Current should take precedence over deprecated
    config = {
        "retrieval": {
            "dense_limit": 25,
            "_deprecated": {
                "dense_limit": 15
            }
        }
    }
    assert get_config_value(config, "retrieval", "dense_limit", 10) == 25
