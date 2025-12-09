"""Augmentation module for VulcanLab."""

from .consolidate_context import consolidate_context, ConsolidationResult, ConsolidatedGroup
from .augment import (
    generate_augmented_prompt,
    get_query_with_context,
    format_context_blocks,
)

__all__ = [
    "consolidate_context",
    "ConsolidationResult",
    "ConsolidatedGroup",
    "generate_augmented_prompt",
    "get_query_with_context",
    "format_context_blocks",
]
