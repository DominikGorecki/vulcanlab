"""ParsedMarkdown model for storing conversion output."""

from sqlalchemy import Column, Integer, Enum as SQLEnum, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.sql import func

from ..database import Base
from .enums import FileType, DocumentClassification
from ...utils.compression import compress_if_large, decompress_if_needed


class ParsedMarkdown(Base):
    """Stores markdown output from PDF/EPUB conversion."""

    __tablename__ = 'parsed_markdown'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    _content = Column('content', LargeBinary, nullable=False)  # Stored as bytes (compressed if >1MB)
    file_type = Column(SQLEnum(FileType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    classification = Column(SQLEnum(DocumentClassification, values_callable=lambda x: [e.value for e in x]), nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_parsed_markdown_work_id', 'work_id'),
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
        return f"<ParsedMarkdown(id={self.id}, work_id={self.work_id}, classification={self.classification.value})>"
