"""Vectorization module for creating embeddings from chunks.

Uses lazy imports to avoid loading heavy AI dependencies until actually needed.
"""

from __future__ import annotations

__all__ = ["vectorize_chunks", "get_eligible_chunks_count", "VectorizationResult"]


def __getattr__(name: str):
    """Lazy import of vectorization components."""
    if name in ("vectorize_chunks", "get_eligible_chunks_count", "VectorizationResult"):
        from . import vect_chunks
        return getattr(vect_chunks, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
