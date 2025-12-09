"""
RAG configuration model for storing preset parameters.

This module defines the RagConfig model for storing and managing
RAG pipeline configuration presets (retrieval, consolidation, augmentation).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class RagConfig(Base):
    """
    Model representing a RAG configuration preset.

    Each preset contains parameters for retrieval, consolidation, and
    augmentation stages of the RAG pipeline.

    Attributes:
        id: Primary key.
        preset_name: Unique human-readable name for the preset.
        is_default: Whether this preset is the system default (only one can be true).
        description: Optional description of preset purpose and use cases.
        config: JSONB containing retrieval, consolidation, and augmentation parameters.
        created_at: Timestamp when preset was created.
        updated_at: Timestamp when preset was last updated (auto-updated by trigger).
    """

    __tablename__ = "rag_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    preset_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    def __repr__(self) -> str:
        """String representation of RagConfig."""
        default_marker = " (default)" if self.is_default else ""
        return f"<RagConfig(id={self.id}, preset_name='{self.preset_name}'{default_marker})>"
