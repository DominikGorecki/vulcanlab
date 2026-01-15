"""
Work summary model for high-level derived summaries.

This module defines the WorkSummary model and its type enum for storing
derived high-level summaries (abstract, outline, etc.) for works.
"""

import enum
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class WorkSummaryType(str, enum.Enum):
    """
    Enum representing types of derived high-level summaries.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (type IN ('abstract', 'outline', 'key_concepts', 'chapter_summaries'))
    """
    ABSTRACT = 'abstract'
    OUTLINE = 'outline'
    KEY_CONCEPTS = 'key_concepts'
    CHAPTER_SUMMARIES = 'chapter_summaries'


class WorkSummary(Base):
    """
    Model representing a high-level derived summary for a work.

    Attributes:
        id: Primary key.
        work_id: Foreign key to the work this summary belongs to.
        type: The type of summary (abstract, outline, etc.).
        content: JSONB blob containing type-specific content structure.
        line_references: JSONB array of {start_line, end_line} for source attribution.
        created_at: Timestamp when record was created.
    """

    __tablename__ = "work_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("works.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[WorkSummaryType] = mapped_column(
        String(30),
        nullable=False
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    line_references: Mapped[list] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    work = relationship("Work", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint('work_id', 'type', name='unq_work_summary_work_type'),
    )

    def __repr__(self) -> str:
        # Use value if it's an enum, otherwise the string
        type_val = self.type.value if hasattr(self.type, 'value') else self.type
        return f"<WorkSummary(id={self.id}, work_id={self.work_id}, type='{type_val}')>"
