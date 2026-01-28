"""
AnswerExpansion and ExpansionSection models for the expand answer feature.

This module defines models for breaking down RAG answers into multiple sections,
processing each through the RAG pipeline independently, and combining them
into a comprehensive report.
"""

import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .result import Result
    from .query import Query


class ExpansionMode(str, enum.Enum):
    """
    Expansion mode for answer expansions.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (mode IN ('automatic', 'manual'))
    """
    AUTOMATIC = 'automatic'
    MANUAL = 'manual'


class ExpansionStatus(str, enum.Enum):
    """
    Status for answer expansions.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (status IN ('created', 'breakdown_pending', 'breakdown_complete',
                      'sections_in_progress', 'combining', 'completed', 'failed'))
    """
    CREATED = 'created'
    BREAKDOWN_PENDING = 'breakdown_pending'
    BREAKDOWN_COMPLETE = 'breakdown_complete'
    SECTIONS_IN_PROGRESS = 'sections_in_progress'
    COMBINING = 'combining'
    COMPLETED = 'completed'
    FAILED = 'failed'


class SectionStatus(str, enum.Enum):
    """
    Status for expansion sections.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (status IN ('pending', 'expanding', 'ready', 'generating', 'completed', 'failed'))
    """
    PENDING = 'pending'
    EXPANDING = 'expanding'
    READY = 'ready'
    GENERATING = 'generating'
    COMPLETED = 'completed'
    FAILED = 'failed'


class AnswerExpansion(Base):
    """
    Model representing an expansion of a RAG answer into multiple sections.

    Each expansion is linked to a single Result and breaks down the answer
    into 3-7 sections, each processed through the full RAG pipeline.

    Attributes:
        id: Primary key.
        result_id: Foreign key to results table (unique - one expansion per result).
        query_id: Foreign key to queries table (denormalized for URL generation).
        mode: Expansion mode (automatic or manual).
        status: Current status of the expansion.
        combined_report: Final combined report after all sections complete.
        expansion_metadata: JSONB for additional expansion metadata.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "answer_expansions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    query_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mode: Mapped[ExpansionMode] = mapped_column(
        SQLEnum(ExpansionMode, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    status: Mapped[ExpansionStatus] = mapped_column(
        SQLEnum(ExpansionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ExpansionStatus.CREATED,
        server_default='created',
        index=True
    )
    combined_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expansion_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
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
    result: Mapped["Result"] = relationship("Result", backref="expansion")
    query: Mapped["Query"] = relationship("Query")
    sections: Mapped[List["ExpansionSection"]] = relationship(
        "ExpansionSection",
        back_populates="expansion",
        cascade="all, delete-orphan",
        order_by="ExpansionSection.order"
    )

    def __repr__(self) -> str:
        return f"<AnswerExpansion(id={self.id}, result_id={self.result_id}, status='{self.status.value}')>"


class ExpansionSection(Base):
    """
    Model representing a single section of an expanded answer.

    Each section contains a heading, summary, and expansion prompt generated
    by the initial breakdown. The section then goes through the full RAG
    pipeline to generate a comprehensive response.

    Attributes:
        id: Primary key.
        expansion_id: Foreign key to answer_expansions table.
        order: Section order (1-based).
        heading: Section heading from breakdown.
        summary: Brief summary from breakdown.
        expansion_prompt: The prompt to use for RAG expansion.
        expanded_queries: JSONB of expanded queries from MQE.
        hyde_answer: HyDE-generated hypothetical answer.
        intent: Detected query intent.
        entities: JSONB of extracted entities.
        retrieved_context: JSONB of raw retrieved chunks.
        clean_retrieval_context: JSONB of cleaned/consolidated context.
        augmented_prompt: Final prompt after context augmentation.
        response_text: LLM-generated response for this section.
        status: Current status of the section.
        error_message: Error message if section failed.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "expansion_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expansion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("answer_expansions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    expansion_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expanded_queries: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    hyde_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    retrieved_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    clean_retrieval_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    augmented_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[SectionStatus] = mapped_column(
        SQLEnum(SectionStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SectionStatus.PENDING,
        server_default='pending',
        index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    expansion: Mapped["AnswerExpansion"] = relationship(
        "AnswerExpansion",
        back_populates="sections"
    )

    def __repr__(self) -> str:
        return f"<ExpansionSection(id={self.id}, expansion_id={self.expansion_id}, order={self.order}, status='{self.status.value}')>"
