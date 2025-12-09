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

from typing import Optional

from sqlalchemy.orm import Session

from vulcanlab.data.database import get_session
from vulcanlab.data.models.rag_config import RagConfig


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
