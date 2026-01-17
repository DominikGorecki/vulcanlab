"""
SummaryChunk model for intermediate summarization storage.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SummaryChunk(Base):
    """
    Model representing an intermediate chunk selected for summarization.

    Attributes:
        id: Primary key.
        work_id: Foreign key to the work this summary chunk belongs to.
        heading_chunk_id: Foreign key to the heading chunk being summarized.
        content_chunk_id: Foreign key to the specific content chunk included.
        word_count: Number of words in the content chunk.
        dense_score: Score from dense vector retrieval.
        lexical_score: Score from lexical (BM25) retrieval.
        rrf_score: Reciprocal Rank Fusion score.
        mmr_score: Maximal Marginal Relevance score.
        rank_position: Position in the final selection for this heading.
        created_at: Timestamp when record was created.
    """

    __tablename__ = "summary_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    heading_chunk_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content_chunk_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False
    )
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dense_score: Mapped[float] = mapped_column(Float, nullable=True)
    lexical_score: Mapped[float] = mapped_column(Float, nullable=True)
    rrf_score: Mapped[float] = mapped_column(Float, nullable=True)
    mmr_score: Mapped[float] = mapped_column(Float, nullable=True)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_index: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    work = relationship("Work", passive_deletes=True)
    heading_chunk = relationship("Chunk", foreign_keys=[heading_chunk_id], passive_deletes=True)
    content_chunk = relationship("Chunk", foreign_keys=[content_chunk_id], passive_deletes=True)

    def __repr__(self) -> str:
        return (
            f"<SummaryChunk(id={self.id}, work_id={self.work_id}, "
            f"heading_id={self.heading_chunk_id}, rank={self.rank_position})>"
        )
