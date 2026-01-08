"""Enums for simple conversion pipeline models."""

import enum


class FileType(str, enum.Enum):
    """File type for parsed markdown."""
    PDF = 'pdf'
    EPUB = 'epub'
    MARKDOWN_IMPORT = 'markdown_import'


class DocumentClassification(str, enum.Enum):
    """Document size classification."""
    SMALL = 'small'
    LARGE = 'large'


class ModificationAction(str, enum.Enum):
    """Heading modification action."""
    REMOVE = 'remove'
    CHANGE = 'change'
    KEEP = 'keep'


class CollectionItemType(str, enum.Enum):
    """Item type for collection items."""
    EXCERPT = 'excerpt'
    RESEARCH_RESULT = 'research_result'
    RESEARCH_QUERY = 'research_query'
