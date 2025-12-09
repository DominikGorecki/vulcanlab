"""
Chunk model for storing document sections and their embeddings.

This module defines the Chunk model for storing hierarchical document
sections (H1-H5, sentences, chunks) with their vector embeddings.
"""

from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Chunk(Base):
    """
    Model representing a document chunk with embedding.

    Attributes:
        id: Primary key.
        parent_id: Reference to parent chunk (NULL for H1/top-level).
        work_id: Foreign key to the work this chunk belongs to.
        level: Hierarchy level (H1, H2, H3, H4, H5, sentence, chunk).
        content: The actual text content of the chunk (without breadcrumb prefix).
        heading_breadcrumbs: Breadcrumb trail of section headings (e.g., "H1 > H2 > H3").
        embedding: Vector embedding (768 dimensions).
        start_line: Line number where chunk begins in markdown.
        end_line: Line number where chunk ends in markdown.
        vector_status: Vectorization status (no_vec, to_vec, vec, vec_err).
    """

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    work_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    heading_breadcrumbs: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="no_vec",
        index=True
    )

    # Relationships
    parent = relationship("Chunk", remote_side=[id], backref="children", passive_deletes=True)
    work = relationship("Work", back_populates="chunks", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, level='{self.level}', work_id={self.work_id})>"
