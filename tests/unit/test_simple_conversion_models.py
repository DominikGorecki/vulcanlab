"""Unit tests for simple conversion models and utilities.

All tests use mocks - NEVER hit the database.
"""

import gzip
import pytest
from unittest.mock import MagicMock

from vulcanlab.data.models.enums import FileType, DocumentClassification, ModificationAction
from vulcanlab.utils.compression import compress_if_large, decompress_if_needed, COMPRESSION_THRESHOLD
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.heading_modifications import HeadingModification


# ENUM Tests

def test_file_type_enum_values():
    """Test FileType enum has correct values."""
    assert FileType.PDF.value == 'pdf'
    assert FileType.EPUB.value == 'epub'


def test_document_classification_enum_values():
    """Test DocumentClassification enum has correct values."""
    assert DocumentClassification.SMALL.value == 'small'
    assert DocumentClassification.LARGE.value == 'large'


def test_modification_action_enum_values():
    """Test ModificationAction enum has correct values."""
    assert ModificationAction.REMOVE.value == 'remove'
    assert ModificationAction.CHANGE.value == 'change'
    assert ModificationAction.KEEP.value == 'keep'


# Compression Tests

def test_compress_small_content():
    """Test compression with content < 1MB (should not compress)."""
    content = "small text"
    result = compress_if_large(content)

    assert isinstance(result, bytes)
    assert len(result) < COMPRESSION_THRESHOLD
    # Should be uncompressed UTF-8 bytes
    assert result == content.encode('utf-8')


def test_compress_large_content():
    """Test compression with content > 1MB (should compress)."""
    # Create 2MB of content
    content = "x" * (2 * 1024 * 1024)
    result = compress_if_large(content)

    assert isinstance(result, bytes)
    # Compressed should be smaller than original
    assert len(result) < len(content.encode('utf-8'))

    # Verify it's actually gzip compressed
    decompressed = gzip.decompress(result)
    assert decompressed.decode('utf-8') == content


def test_compress_none_content():
    """Test compression with None content."""
    result = compress_if_large(None)
    assert result == b''


def test_compress_bytes_input():
    """Test compression accepts bytes input."""
    content_bytes = b"test bytes content"
    result = compress_if_large(content_bytes)

    assert isinstance(result, bytes)
    assert result == content_bytes


def test_decompress_compressed_data():
    """Test decompression of gzip compressed data."""
    original = "test content for compression"
    compressed = gzip.compress(original.encode('utf-8'))

    result = decompress_if_needed(compressed)

    assert result == original


def test_decompress_uncompressed_data():
    """Test decompression of uncompressed UTF-8 bytes."""
    original = "uncompressed text"
    data = original.encode('utf-8')

    result = decompress_if_needed(data)

    assert result == original


def test_decompress_string_input():
    """Test decompression with string input (should return as-is)."""
    original = "already a string"

    result = decompress_if_needed(original)

    assert result == original


def test_decompress_none_data():
    """Test decompression with None data."""
    result = decompress_if_needed(None)
    assert result == ''


def test_decompress_invalid_gzip():
    """Test decompression gracefully handles invalid gzip data."""
    # Create invalid gzip data (just random bytes)
    invalid_data = b"not gzip data at all"

    # Should fallback to UTF-8 decode
    result = decompress_if_needed(invalid_data)
    assert result == "not gzip data at all"


# Model Property Tests

def test_parsed_markdown_content_property_decompresses():
    """Test ParsedMarkdown.content property decompresses data."""
    original_content = "test markdown content"
    compressed = gzip.compress(original_content.encode('utf-8'))

    # Create mock instance
    instance = ParsedMarkdown()
    instance._content = compressed

    # Access property should decompress
    result = instance.content
    assert result == original_content


def test_parsed_markdown_content_setter_compresses():
    """Test ParsedMarkdown.content setter compresses large content."""
    # Create large content (>1MB)
    large_content = "x" * (2 * 1024 * 1024)

    instance = ParsedMarkdown()
    instance.content = large_content

    # Should be compressed
    assert len(instance._content) < len(large_content.encode('utf-8'))

    # Should decompress back to original
    assert instance.content == large_content


def test_sanitized_markdown_compression_roundtrip():
    """Test SanitizedMarkdown compression roundtrip."""
    # Create large markdown
    large_markdown = "# Heading\n\n" + ("Content paragraph. " * 100000)

    instance = SanitizedMarkdown()
    instance.content = large_markdown

    # Get it back
    result = instance.content

    # Should match original (compression is transparent)
    assert result == large_markdown


def test_parsed_markdown_small_content_not_compressed():
    """Test ParsedMarkdown doesn't compress small content."""
    small_content = "small markdown"

    instance = ParsedMarkdown()
    instance.content = small_content

    # Should be stored as uncompressed bytes
    assert instance._content == small_content.encode('utf-8')

    # Should decompress correctly anyway
    assert instance.content == small_content


# Table Structure Tests (inspect model metadata, don't hit DB)

def test_parsed_markdown_table_structure():
    """Test ParsedMarkdown table has correct structure."""
    table = ParsedMarkdown.__table__

    # Check table name
    assert table.name == 'parsed_markdown'

    # Check columns exist
    column_names = [col.name for col in table.columns]
    assert 'id' in column_names
    assert 'work_id' in column_names
    assert 'content' in column_names
    assert 'file_type' in column_names
    assert 'classification' in column_names
    assert 'token_count' in column_names
    assert 'created_at' in column_names

    # Check foreign key
    work_id_col = table.columns['work_id']
    assert len(work_id_col.foreign_keys) == 1
    fk = list(work_id_col.foreign_keys)[0]
    assert 'works.id' in str(fk.target_fullname)
    assert fk.ondelete == 'CASCADE'


def test_sanitized_markdown_table_structure():
    """Test SanitizedMarkdown table has correct structure."""
    table = SanitizedMarkdown.__table__

    assert table.name == 'sanitized_markdown'

    column_names = [col.name for col in table.columns]
    assert 'id' in column_names
    assert 'work_id' in column_names
    assert 'content' in column_names
    assert 'token_count' in column_names
    assert 'created_at' in column_names

    # Check CASCADE delete
    work_id_col = table.columns['work_id']
    fk = list(work_id_col.foreign_keys)[0]
    assert fk.ondelete == 'CASCADE'


def test_heading_modifications_table_structure():
    """Test HeadingModification table has correct structure."""
    table = HeadingModification.__table__

    assert table.name == 'heading_modifications'

    column_names = [col.name for col in table.columns]
    assert 'id' in column_names
    assert 'work_id' in column_names
    assert 'line_number' in column_names
    assert 'original_heading' in column_names
    assert 'modified_heading' in column_names
    assert 'action' in column_names
    assert 'vectorize_flag' in column_names
    assert 'created_at' in column_names

    # Check CASCADE delete
    work_id_col = table.columns['work_id']
    fk = list(work_id_col.foreign_keys)[0]
    assert fk.ondelete == 'CASCADE'


def test_parsed_markdown_indexes():
    """Test ParsedMarkdown has index on work_id."""
    table = ParsedMarkdown.__table__

    # Check for work_id index
    index_names = [idx.name for idx in table.indexes]
    assert 'ix_parsed_markdown_work_id' in index_names

    # Verify it's on the right column
    work_id_index = [idx for idx in table.indexes if idx.name == 'ix_parsed_markdown_work_id'][0]
    indexed_columns = [col.name for col in work_id_index.columns]
    assert 'work_id' in indexed_columns


def test_heading_modifications_composite_index():
    """Test HeadingModification has composite index on (work_id, line_number)."""
    table = HeadingModification.__table__

    index_names = [idx.name for idx in table.indexes]
    assert 'ix_heading_modifications_work_id' in index_names
    assert 'ix_heading_modifications_work_line' in index_names

    # Verify composite index
    composite_index = [idx for idx in table.indexes if idx.name == 'ix_heading_modifications_work_line'][0]
    indexed_columns = [col.name for col in composite_index.columns]
    assert 'work_id' in indexed_columns
    assert 'line_number' in indexed_columns
