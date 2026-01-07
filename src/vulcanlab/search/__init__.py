"""
Search module for lexical and dense document retrieval.

This module provides search functionality across document chunks:
- Lexical search using PostgreSQL full-text search (ts_vector/ts_query)
- Dense search using vector similarity (T02)
- Hybrid search with RRF fusion (T03)
"""

from .breadcrumb_builder import build_breadcrumb
from .search_lexical import search_lexical

__all__ = ["build_breadcrumb", "search_lexical"]
