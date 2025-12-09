"""AI module for LLM provider configuration and factory functions.

Uses lazy imports to avoid loading heavy ML libraries until actually needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Config is lightweight - import eagerly
from .config import LLMProvider, LLMSettings, ModelTier

__all__ = [
    "LLMProvider",
    "LLMSettings",
    "ModelTier",
    "PydanticAIStack",
    "LangChainStack",
    "LLMStack",
    "create_pydantic_agent",
    "create_langchain_chat",
    "create_llm_stack",
    "create_embeddings",
]


def __getattr__(name: str):
    """Lazy import of heavy llm_factory components."""
    if name in (
        "PydanticAIStack",
        "LangChainStack",
        "LLMStack",
        "create_pydantic_agent",
        "create_langchain_chat",
        "create_llm_stack",
        "create_embeddings",
    ):
        from . import llm_factory
        return getattr(llm_factory, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
