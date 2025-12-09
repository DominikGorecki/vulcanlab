"""
Prompt Template model for storing versioned LangChain PromptTemplate strings.

This model supports versioned prompt templates for different AI functions,
allowing users to manage and customize prompts via the UI while maintaining
backward compatibility with hardcoded fallbacks.
"""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import validates

from ..database import Base


class PromptTemplate(Base):
    """Versioned prompt template for AI functions.

    Stores LangChain PromptTemplate strings with version management and
    active template selection per function tag.

    Attributes:
        id: Primary key
        function_tag: Identifier for the function (e.g., 'query_expansion')
        version: Version number (starts at 1, auto-incremented)
        title: Human-readable title for this template version
        template_content: The template string with {variable} placeholders
        is_active: Whether this version is currently active for its function
        created_at: Timestamp when created
        updated_at: Timestamp when last modified
    """

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    function_tag = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    template_content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('function_tag', 'version', name='uq_function_tag_version'),
        CheckConstraint('version > 0', name='chk_version_positive'),
        Index('idx_prompt_templates_function_tag', 'function_tag'),
        Index('idx_prompt_templates_active', 'function_tag', 'is_active'),
    )

    @validates('version')
    def validate_version(self, key, value):
        """Validate that version is positive."""
        if value <= 0:
            raise ValueError("Version must be greater than 0")
        return value

    def __repr__(self):
        return (
            f"<PromptTemplate(id={self.id}, function_tag='{self.function_tag}', "
            f"version={self.version}, active={self.is_active})>"
        )
