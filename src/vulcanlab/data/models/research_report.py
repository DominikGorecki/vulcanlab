"""
ResearchReport model for storing final research reports.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ResearchReport(Base):
    """
    Model representing a research report.

    Attributes:
        id: Primary key.
        session_id: Foreign key to research_sessions table.
        report_content: The full report content.
        executive_summary: Brief summary of the report.
        quality_evaluation: JSONB containing quality assessment data.
        report_metadata: JSONB containing additional metadata (mapped to 'metadata' column).
        version: Version number of the report.
        created_at: Timestamp when record was created.
    """

    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    report_content: Mapped[str] = mapped_column(Text, nullable=False)
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_evaluation: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    report_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default='1')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="reports")

    def __repr__(self) -> str:
        return f"<ResearchReport(id={self.id}, session_id={self.session_id}, version={self.version})>"
