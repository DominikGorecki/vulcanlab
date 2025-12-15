"""
Configuration loader for simple conversion pipeline settings.

Provides functions to read and write conversion-related configuration values
from vulcanlab.config.json.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_THRESHOLD = 15000
DEFAULT_ADVANCED_MODE_ENABLED = False

def get_config_path() -> Path:
    """Get path to vulcanlab.config.json."""
    # Look for config in standard locations
    candidates = [
        Path.cwd() / "vulcanlab.config.json",
        Path.home() / ".vulcanlab" / "vulcanlab.config.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    # Return default location if none exist
    return Path.cwd() / "vulcanlab.config.json"


def load_config() -> dict:
    """Load configuration from JSON file."""
    config_path = get_config_path()

    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {}

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def save_config(config: dict) -> None:
    """Save configuration to JSON file."""
    config_path = get_config_path()

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        raise


def get_token_threshold() -> int:
    """
    Get the token threshold for document classification.

    Returns:
        Token threshold value (defaults to 15000)
    """
    config = load_config()

    # Navigate nested structure: conversion.token_threshold
    conversion = config.get('conversion', {})
    threshold = conversion.get('token_threshold', DEFAULT_TOKEN_THRESHOLD)

    if not isinstance(threshold, int) or threshold <= 0:
        logger.warning(
            f"Invalid token threshold value: {threshold}, using default {DEFAULT_TOKEN_THRESHOLD}"
        )
        return DEFAULT_TOKEN_THRESHOLD

    return threshold


def set_token_threshold(threshold: int) -> None:
    """
    Set the token threshold for document classification.

    Args:
        threshold: New threshold value (must be positive integer)

    Raises:
        ValueError: If threshold is not a positive integer
    """
    if not isinstance(threshold, int) or threshold <= 0:
        raise ValueError("Token threshold must be a positive integer")

    config = load_config()

    # Ensure conversion section exists
    if 'conversion' not in config:
        config['conversion'] = {}

    config['conversion']['token_threshold'] = threshold
    save_config(config)
    logger.info(f"Token threshold updated to {threshold}")


def get_advanced_mode_enabled() -> bool:
    """
    Get the advanced mode enabled setting.

    Returns:
        Boolean indicating if advanced mode is enabled (defaults to False)
    """
    config = load_config()

    # Navigate nested structure: conversion.advanced_mode_enabled
    conversion = config.get('conversion', {})
    enabled = conversion.get('advanced_mode_enabled', DEFAULT_ADVANCED_MODE_ENABLED)

    if not isinstance(enabled, bool):
        logger.warning(
            f"Invalid advanced_mode_enabled value: {enabled}, using default {DEFAULT_ADVANCED_MODE_ENABLED}"
        )
        return DEFAULT_ADVANCED_MODE_ENABLED

    return enabled


def set_advanced_mode_enabled(enabled: bool) -> None:
    """
    Set the advanced mode enabled setting.

    Args:
        enabled: Boolean indicating if advanced mode should be enabled

    Raises:
        ValueError: If enabled is not a boolean
    """
    if not isinstance(enabled, bool):
        raise ValueError("advanced_mode_enabled must be a boolean")

    config = load_config()

    # Ensure conversion section exists
    if 'conversion' not in config:
        config['conversion'] = {}

    config['conversion']['advanced_mode_enabled'] = enabled
    save_config(config)
    logger.info(f"Advanced mode enabled updated to {enabled}")
