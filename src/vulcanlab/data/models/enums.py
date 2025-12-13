"""Enums for simple conversion pipeline models."""

import enum


class FileType(str, enum.Enum):
    """File type for parsed markdown."""
    PDF = 'pdf'
    EPUB = 'epub'


class DocumentClassification(str, enum.Enum):
    """Document size classification."""
    SMALL = 'small'
    LARGE = 'large'


class ModificationAction(str, enum.Enum):
    """Heading modification action."""
    REMOVE = 'remove'
    CHANGE = 'change'
    KEEP = 'keep'
