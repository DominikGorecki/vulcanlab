"""Module for retrieving active LLM configuration information.

This module provides functions to get the current active LLM provider and model
information without exposing sensitive API keys.
"""

from __future__ import annotations

from dataclasses import dataclass

from vulcanlab.ai.config import LLMSettings, ModelTier


@dataclass
class ActiveLLMInfo:
    """Container for active LLM configuration information.

    Attributes:
        provider: The active LLM provider (e.g., 'openai', 'gemini')
        light_model: The model name used for light/fast tasks
        full_model: The model name used for full/complex tasks
    """

    provider: str
    light_model: str
    full_model: str


def get_active_llm_info() -> ActiveLLMInfo:
    """Get current active LLM configuration information.

    Returns:
        ActiveLLMInfo object containing provider and model names.

    Examples:
        >>> info = get_active_llm_info()
        >>> print(f"Provider: {info.provider}")
        >>> print(f"Light Model: {info.light_model}")
        >>> print(f"Full Model: {info.full_model}")
    """
    settings = LLMSettings()

    return ActiveLLMInfo(
        provider=settings.provider.value,
        light_model=settings.get_model(ModelTier.LIGHT),
        full_model=settings.get_model(ModelTier.FULL),
    )
