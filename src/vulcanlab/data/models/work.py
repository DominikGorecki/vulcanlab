"""
Work model for bibliographic information.

This module defines the Work model for storing bibliographic metadata
about psychology literature.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Work(Base):
    """
    Model representing a bibliographic work (book, article, etc.).

    Attributes:
        id: Primary key.
        title: Title of the work.
        authors: Author(s) of the work.
        year: Year of publication.
        publisher: Publisher name.
        isbn: ISBN for books.
        doi: Digital Object Identifier for articles.
        abstract: Abstract or summary.
        source_path: Path to the original source file.
        markdown_path: Path to the converted markdown file.
        work_type: Type of work (book, article, chapter, etc.).
        toc: Table of contents as JSON array of {level, title} entries.
        files: JSON object tracking all processing pipeline files with their paths and hashes.
               Structure: {"original_file": {"path": "...", "hash": "..."},
                          "hier_markdown": {"path": "...", "hash": "..."},
                          "style_markdown": {"path": "...", "hash": "..."},
                          "original_markdown": {"path": "...", "hash": "..."},
                          "toc_titles": {"path": "...", "hash": "..."},
                          "titles": {"path": "...", "hash": "..."},
                          "san_mapping": {"path": "...", "hash": "..."},
                          "sanitized": {"path": "...", "hash": "..."},
                          "sanitized_titles": {"path": "...", "hash": "..."},
                          "vec_suggestions": {"path": "...", "hash": "..."}}
        processing_status: JSON object tracking processing operation statuses.
                          Structure: {"heading_chunks": "completed"|"pending"|"failed",
                                     "content_chunks": "completed"|"pending"|"failed"}
        content_hash: SHA-256 hash of source content for deduplication.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    __tablename__ = "works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    authors: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    volume: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    issue: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pages: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    editor: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    markdown_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    work_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    toc: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    files: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    processing_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
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
    chunks = relationship("Chunk", back_populates="work", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Work(id={self.id}, title='{self.title[:50]}...')>"
