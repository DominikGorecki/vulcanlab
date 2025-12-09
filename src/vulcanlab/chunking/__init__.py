"""Chunking utilities for processing markdown files.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.
"""

from __future__ import annotations

# Lightweight imports only
from .chunk_headings import chunk_headings

__all__ = [
    "BibliographicInfo",
    "chunk_headings",
    "ExtractedMetadata",
    "EXTRACT_CHARS",
    "extract_metadata",
    "suggest_chunks",
    "suggest_chunks_from_work",
    "build_prompt_for_vec_suggestions",
    "parse_vec_suggestions_response",
    "save_vec_suggestions_from_response",
    "TableOfContents",
    "TOCEntry",
]


def __getattr__(name: str):
    """Lazy import of components that depend on AI module."""
    if name in (
        "BibliographicInfo",
        "ExtractedMetadata",
        "EXTRACT_CHARS",
        "extract_metadata",
        "TableOfContents",
        "TOCEntry",
    ):
        from . import bib_extractor
        return getattr(bib_extractor, name)
    if name in (
        "suggest_chunks",
        "suggest_chunks_from_work",
        "build_prompt_for_vec_suggestions",
        "parse_vec_suggestions_response",
        "save_vec_suggestions_from_response",
    ):
        from . import suggested_chunks
        return getattr(suggested_chunks, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
