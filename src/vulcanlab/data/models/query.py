"""
Query model for storing expanded queries and their embeddings.

This module defines the Query model for storing query expansion results
including MQE queries, HyDE answers, intent, entities, and embeddings.
"""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Query(Base):
    """
    Model representing an expanded query with embeddings.

    Attributes:
        id: Primary key.
        original_query: The original user query.
        expanded_queries: List of MQE expanded queries (JSON array).
        hyde_answer: Hypothetical document embedding answer.
        intent: Query intent (DEFINITION, MECHANISM, COMPARISON, APPLICATION, STUDY_DETAIL, CRITIQUE).
        entities: Extracted entities (JSON array of names, theories, keywords).
        embedding_original: Vector embedding for original query (768 dimensions).
        embeddings_mqe: JSON array of MQE query embeddings.
        embedding_hyde: Vector embedding for HyDE answer.
        vector_status: Vectorization status (no_vec, to_vec, vec, vec_err).
        retrieved_context: JSON array of retrieved chunks with metadata and scores.
        clean_retrieval_context: JSON array of consolidated chunks after grouping.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    expanded_queries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    hyde_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Embeddings (768 dimensions for text-embedding-004)
    embedding_original: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)
    embeddings_mqe: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Array of embeddings
    embedding_hyde: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)

    vector_status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="no_vec",
        index=True
    )
    retrieved_context: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    clean_retrieval_context: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        query_preview = self.original_query[:50] + "..." if len(self.original_query) > 50 else self.original_query
        return f"<Query(id={self.id}, query='{query_preview}')>"
