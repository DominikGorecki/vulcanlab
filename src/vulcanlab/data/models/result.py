"""
Result model for storing LLM responses to queries.

This module defines the Result model for storing LLM-generated responses
linked to Query objects (one-to-many relationship: one query can have many results).
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Result(Base):
    """
    Model representing an LLM response to a query.

    Attributes:
        id: Primary key.
        query_id: Foreign key to queries table.
        response_text: The full LLM response text.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
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
        response_preview = self.response_text[:50] + "..." if len(self.response_text) > 50 else self.response_text
        return f"<Result(id={self.id}, query_id={self.query_id}, response='{response_preview}')>"

