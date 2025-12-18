"""
Unit tests for enums module.

Tests FileType, DocumentClassification, and ModificationAction enums.

Usage:
    pytest tests/unit/test_enums.py -v
"""

import pytest

from vulcanlab.data.models.enums import (
    FileType,
    DocumentClassification,
    ModificationAction,
)


class TestFileType:
    """Tests for FileType enum."""

    def test_pdf_value(self):
        """Test PDF enum value."""
        assert FileType.PDF == 'pdf'
        assert FileType.PDF.value == 'pdf'

    def test_epub_value(self):
        """Test EPUB enum value."""
        assert FileType.EPUB == 'epub'
        assert FileType.EPUB.value == 'epub'

    def test_markdown_import_value(self):
        """Test MARKDOWN_IMPORT enum value."""
        assert FileType.MARKDOWN_IMPORT == 'markdown_import'
        assert FileType.MARKDOWN_IMPORT.value == 'markdown_import'

    def test_markdown_import_exists(self):
        """Test MARKDOWN_IMPORT enum member exists."""
        assert hasattr(FileType, 'MARKDOWN_IMPORT')
        assert FileType.MARKDOWN_IMPORT in FileType

    def test_all_file_types(self):
        """Test all FileType values."""
        file_types = list(FileType)
        assert FileType.PDF in file_types
        assert FileType.EPUB in file_types
        assert FileType.MARKDOWN_IMPORT in file_types
        assert len(file_types) == 3


class TestDocumentClassification:
    """Tests for DocumentClassification enum."""

    def test_small_value(self):
        """Test SMALL enum value."""
        assert DocumentClassification.SMALL == 'small'
        assert DocumentClassification.SMALL.value == 'small'

    def test_large_value(self):
        """Test LARGE enum value."""
        assert DocumentClassification.LARGE == 'large'
        assert DocumentClassification.LARGE.value == 'large'


class TestModificationAction:
    """Tests for ModificationAction enum."""

    def test_remove_value(self):
        """Test REMOVE enum value."""
        assert ModificationAction.REMOVE == 'remove'
        assert ModificationAction.REMOVE.value == 'remove'

    def test_change_value(self):
        """Test CHANGE enum value."""
        assert ModificationAction.CHANGE == 'change'
        assert ModificationAction.CHANGE.value == 'change'

    def test_keep_value(self):
        """Test KEEP enum value."""
        assert ModificationAction.KEEP == 'keep'
        assert ModificationAction.KEEP.value == 'keep'
