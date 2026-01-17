"""
SummaryResult model for final generated summaries.
"""

from datetime import datetime

from sqlalchemy import Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SummaryResult(Base):
    """
    Model representing final generated summaries for specific headings.

    Attributes:
        id: Primary key.
        work_id: Foreign key to the work this summary belongs to.
        chunk_id: Foreign key to the heading chunk being summarized (unique).
        summary_content: The generated summary text.
        prompt_index: Index of the prompt template used.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "summary_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    summary_content: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_index: Mapped[int] = mapped_column(Integer, nullable=True)
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

    # Relationships
    work = relationship("Work", passive_deletes=True)
    chunk = relationship("Chunk", foreign_keys=[chunk_id], passive_deletes=True)

    def __repr__(self) -> str:
        return f"<SummaryResult(id={self.id}, work_id={self.work_id}, chunk_id={self.chunk_id})>"
