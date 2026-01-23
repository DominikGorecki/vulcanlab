"""
Unit tests for embedding vector column dimensions.

Tests that SQLAlchemy model Vector column definitions use 1536 dimensions
for text-embedding-005 compatibility.
"""

import pytest
from pgvector.sqlalchemy import Vector

from vulcanlab.data.models.chunk import Chunk
from vulcanlab.data.models.query import Query


class TestEmbeddingDimensions:
    """Test vector column dimensions are set to 1536."""

    def test_chunk_embedding_column_dimension(self):
        """Verify Chunk.embedding is Vector(1536)."""
        embedding_column = Chunk.__table__.c.embedding
        assert isinstance(embedding_column.type, Vector)
        assert embedding_column.type.dim == 1536

    def test_query_embedding_original_column_dimension(self):
        """Verify Query.embedding_original is Vector(1536)."""
        embedding_column = Query.__table__.c.embedding_original
        assert isinstance(embedding_column.type, Vector)
        assert embedding_column.type.dim == 1536

    def test_query_embedding_hyde_column_dimension(self):
        """Verify Query.embedding_hyde is Vector(1536)."""
        embedding_column = Query.__table__.c.embedding_hyde
        assert isinstance(embedding_column.type, Vector)
        assert embedding_column.type.dim == 1536
