"""
API Routers package.

Each router handles a specific group of endpoints:
    - init: Initialization and setup
    - settings: Configuration management
    - conversion: Document conversion
    - sanitization: Content sanitization
    - chunking: Document chunking
    - vectorization: Embedding generation
    - corpus: Corpus management (read-only access to completed works)
    - rag: Retrieval and generation
"""

from vulcanlab_api.routers import (
    chunking,
    conversion,
    corpus,
    init,
    rag,
    sanitization,
    settings,
    simple_conversion,
    vectorization,
)

__all__ = [
    "init",
    "settings",
    "conversion",
    "sanitization",
    "chunking",
    "vectorization",
    "corpus",
    "rag",
    "simple_conversion",
]


