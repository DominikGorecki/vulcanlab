"""
ResultModel for tracking LLM models used to generate results.

This module defines the ResultModel for storing unique model names
(e.g., "gpt-4", "claude-sonnet-3.5") that are referenced by Result records.
"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ResultModel(Base):
    """
    Model representing an LLM model used to generate results.

    Attributes:
        id: Primary key.
        name: Unique model name (e.g., "gpt-4", "claude-sonnet-3.5").
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "result_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
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
        return f"<ResultModel(id={self.id}, name='{self.name}')>"
