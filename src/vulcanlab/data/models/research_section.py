"""
ResearchSection model for storing research section data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import QualityStatus


class ResearchSection(Base):
    """
    Model representing a research section.

    Attributes:
        id: Primary key.
        session_id: Foreign key to research_sessions table.
        question_id: Identifier for the question being researched.
        question_text: The actual question text.
        section_content: The research content for this section.
        context_data: JSONB containing context information.
        matching_results: JSONB containing matching results from searches.
        section_metadata: JSONB containing additional metadata (mapped to 'metadata' column).
        reuse_info: JSONB containing information about content reuse.
        quality_status: Quality assessment status.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "research_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    question_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    matching_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    section_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    reuse_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    quality_status: Mapped[Optional[QualityStatus]] = mapped_column(
        SQLEnum(QualityStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        index=True,
        default=QualityStatus.PENDING
    )
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
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="sections")

    def __repr__(self) -> str:
        return f"<ResearchSection(id={self.id}, session_id={self.session_id}, question_id='{self.question_id}')>"
