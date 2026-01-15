"""
Summary node model for granular chunk-level summaries.

This module defines the SummaryNode model for storing structured summary data
for individual heading-level chunks.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SummaryNode(Base):
    """
    Model representing a structured summary for a document chunk.

    Attributes:
        id: Primary key.
        chunk_id: Foreign key to the source chunk.
        work_id: Foreign key to the work this summary belongs to.
        gist: 1-2 sentence high-level summary.
        key_points: JSONB array of {text, start_line, end_line}.
        definitions: JSONB array of {term, definition, start_line, end_line}.
        key_terms: JSONB array of {term, start_line, end_line}.
        examples: JSONB array of {text, start_line, end_line}.
        start_line: Start line in source markdown.
        end_line: End line in source markdown.
        salience_score: Computed salience score for this node.
        created_at: Timestamp when record was created.
    """

    __tablename__ = "summary_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    work_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    gist: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    definitions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    key_terms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    examples: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    salience_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize with defaults for Python-side usage."""
        kwargs.setdefault('key_points', [])
        kwargs.setdefault('definitions', [])
        kwargs.setdefault('key_terms', [])
        kwargs.setdefault('examples', [])
        super().__init__(**kwargs)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    chunk = relationship("Chunk", passive_deletes=True)
    work = relationship("Work", passive_deletes=True)

    @property
    def heading_breadcrumbs(self) -> Optional[str]:
        return self.chunk.heading_breadcrumbs if self.chunk else None

    @property
    def level(self) -> Optional[str]:
        return self.chunk.level if self.chunk else None

    @property
    def parent_id(self) -> Optional[int]:
        return self.chunk.parent_id if self.chunk else None

    def __repr__(self) -> str:
        return f"<SummaryNode(id={self.id}, work_id={self.work_id}, chunk_id={self.chunk_id})>"
