"""
ResearchSession model for managing research workflows.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import SessionType, SessionStatus, ResearchPhase


class ResearchSession(Base):
    """
    Model representing a research session.

    Attributes:
        id: Primary key.
        collection_id: Foreign key to collections table.
        session_type: Type of session (manual or automated).
        thread_id: Unique identifier for the thread/conversation.
        current_phase: Current phase of the research process.
        research_plan: JSONB containing the research plan.
        state_data: JSONB containing session state data.
        status: Current status of the session.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
        completed_at: Timestamp when session was completed.
    """

    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_type: Mapped[SessionType] = mapped_column(
        SQLEnum(SessionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    current_phase: Mapped[Optional[ResearchPhase]] = mapped_column(
        SQLEnum(ResearchPhase, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True
    )
    research_plan: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    state_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SessionStatus.IN_PROGRESS,
        server_default='in_progress',
        index=True
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="research_sessions")
    sections: Mapped[List["ResearchSection"]] = relationship(
        "ResearchSection",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    reports: Mapped[List["ResearchReport"]] = relationship(
        "ResearchReport",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ResearchSession(id={self.id}, thread_id='{self.thread_id}', status='{self.status.value}')>"
