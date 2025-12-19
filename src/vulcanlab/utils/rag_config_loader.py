"""
RAG configuration loader utility.

Provides functions to load RAG configuration presets from the database.
Used by retrieval, consolidation, and augmentation modules to get
runtime parameters.

Example:
    >>> from vulcanlab.utils.rag_config_loader import get_default_config
    >>> config = get_default_config()
    >>> dense_limit = config["retrieval"]["dense_limit"]
"""

import logging
from typing import Optional, Any

from sqlalchemy.orm import Session

from vulcanlab.data.database import get_session
from vulcanlab.data.models.rag_config import RagConfig

logger = logging.getLogger(__name__)


def get_config_value(config: dict, section: str, key: str, fallback: Any) -> Any:
    """
    Get config value from current or deprecated location.

    Checks:
    1. config[section][key]
    2. config[section]['_deprecated'][key]
    3. fallback

    Args:
        config: The configuration dictionary.
        section: The section name (e.g., 'retrieval').
        key: The parameter key (e.g., 'min_word_count').
        fallback: The value to return if not found.

    Returns:
        The configuration value.
    """
    section_config = config.get(section, {})

    # Check current location
    if key in section_config:
        return section_config[key]

    # Check deprecated location
    deprecated = section_config.get('_deprecated', {})
    if key in deprecated:
        logger.warning(f"Using deprecated config key: {section}.{key}. Please update your RAG config preset.")
        return deprecated[key]

    return fallback


def get_default_config() -> dict:
    """
    Get default RAG configuration from database.

    Returns the configuration dict for the preset marked as default.
    This is the primary function used by RAG pipeline modules.

    Returns:
        Dict with keys: "retrieval", "consolidation", "augmentation".
        Each key contains a dict of parameters for that stage.

    Raises:
        RuntimeError: If no default configuration exists in database.

    Example:
        >>> config = get_default_config()
        >>> config["retrieval"]["dense_limit"]
        19
        >>> config["consolidation"]["coverage_threshold"]
        0.5
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.is_default == True).first()
        if not config:
            raise RuntimeError(
                "No default RAG configuration found in database. "
                "Run database initialization to create default preset."
            )
        return config.config


def get_config_by_name(preset_name: str) -> dict:
    """
    Get RAG configuration by preset name.

    Loads a specific preset by name. Use this when you want to override
    the default configuration for a specific query or experiment.

    Args:
        preset_name: Name of the preset to load (case-sensitive).

    Returns:
        Dict with keys: "retrieval", "consolidation", "augmentation".
        Each key contains a dict of parameters for that stage.

    Raises:
        ValueError: If preset with given name not found.

    Example:
        >>> config = get_config_by_name("Fast")
        >>> config["retrieval"]["top_n_final"]
        10
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.preset_name == preset_name).first()
        if not config:
            raise ValueError(
                f"RAG config preset '{preset_name}' not found. "
                f"Use get_default_config() or verify preset name."
            )
        return config.config


def get_all_preset_names() -> list[str]:
    """
    Get list of all available preset names.

    Useful for CLI tools, logging, or UI dropdown population.

    Returns:
        List of preset names sorted alphabetically.

    Example:
        >>> get_all_preset_names()
        ['Default', 'Fast', 'Thorough']
    """
    with get_session() as session:
        presets = session.query(RagConfig.preset_name).order_by(RagConfig.preset_name).all()
        return [preset[0] for preset in presets]
