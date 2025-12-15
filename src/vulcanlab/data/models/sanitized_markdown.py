"""SanitizedMarkdown model for storing LLM-cleaned markdown."""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.sql import func

from ..database import Base
from ...utils.compression import compress_if_large, decompress_if_needed


class SanitizedMarkdown(Base):
    """Stores sanitized markdown from Step 2A or 2B."""

    __tablename__ = 'sanitized_markdown'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    _content = Column('content', LargeBinary, nullable=False)  # Stored as bytes (compressed if >1MB)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_sanitized_markdown_work_id', 'work_id'),
    )

    @property
    def content(self) -> str:
        """Get decompressed content."""
        return decompress_if_needed(self._content)

    @content.setter
    def content(self, value: str):
        """Set content with automatic compression."""
        self._content = compress_if_large(value)

    def __repr__(self):
        return f"<SanitizedMarkdown(id={self.id}, work_id={self.work_id}, token_count={self.token_count})>"
