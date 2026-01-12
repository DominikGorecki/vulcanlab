"""
Collection model for grouping related research items.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Collection(Base):
    """
    Model representing a collection of items.

    Attributes:
        id: Primary key.
        name: Name of the collection.
        description: Description of the collection.
        tags: List of tags for the collection (JSONB array).
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default='[]')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")
    research_sessions = relationship("ResearchSession", back_populates="collection", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name='{self.name}')>"

