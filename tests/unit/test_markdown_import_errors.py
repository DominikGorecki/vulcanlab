"""
Unit tests for markdown import error handling.

Tests error scenarios including file I/O errors, empty files, encoding issues,
and transaction rollback.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from sqlalchemy.exc import SQLAlchemyError

from vulcanlab.markdown_import.import_flow import (
    import_sanitized_markdown,
    import_unsanitized_markdown
)
from vulcanlab.markdown_import.metadata import Metadata


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.add = Mock()
    session.flush = Mock()
    return session


@pytest.fixture
def sample_metadata():
    """Create sample metadata."""
    return Metadata(
        title="Test Work",
        author="Test Author",
        year=2023
    )


def test_import_sanitized_handles_file_not_found(mock_session, sample_metadata, tmp_path):
    """Test that import handles file not found errors."""
    # Setup - use a non-existent file path
    non_existent_file = tmp_path / "does_not_exist.md"

    # Test
    with pytest.raises(FileNotFoundError) as exc_info:
        import_sanitized_markdown(str(non_existent_file), sample_metadata, mock_session)

    # Verify
    assert "File not found" in str(exc_info.value)


def test_import_sanitized_handles_empty_file(mock_session, sample_metadata, tmp_path):
    """Test that import handles empty file (0 bytes) correctly."""
    # Setup - create an empty file
    empty_file = tmp_path / "empty.md"
    empty_file.touch()

    # Test
    with pytest.raises(ValueError) as exc_info:
        import_sanitized_markdown(str(empty_file), sample_metadata, mock_session)

    # Verify
    assert "empty" in str(exc_info.value).lower()
    assert "0 bytes" in str(exc_info.value)


def test_import_sanitized_handles_large_file_warning(mock_session, sample_metadata, tmp_path):
    """Test that import warns about very large files but proceeds."""
    # Setup - create a file larger than 10MB
    large_file = tmp_path / "large.md"
    content = "# Test\n" + ("A" * (11 * 1024 * 1024))  # 11MB
    large_file.write_text(content, encoding='utf-8')

    # Mock the chunking functions to avoid actual processing
    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading, \
         patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:

        mock_heading.return_value = []
        mock_content.return_value = []

        # Test - should not raise an error due to size, may fail for other reasons
        # The warning is logged, not emitted via warnings module
        try:
            import_sanitized_markdown(str(large_file), sample_metadata, mock_session)
        except Exception as e:
            # Should not be rejected due to size
            assert "empty" not in str(e).lower()
            assert "size" not in str(e).lower()


def test_import_sanitized_handles_invalid_utf8_encoding(mock_session, sample_metadata, tmp_path):
    """Test that import handles invalid UTF-8 encoding with fallback."""
    # Setup - create a file with latin-1 encoding
    latin1_file = tmp_path / "latin1.md"
    content = "# Test\n\nCafé résumé naïve"  # Characters that differ in latin-1
    latin1_file.write_bytes(content.encode('latin-1'))

    # Mock the chunking functions
    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading, \
         patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:

        mock_heading.return_value = []
        mock_content.return_value = []

        # Test - should succeed using fallback encoding
        work = import_sanitized_markdown(str(latin1_file), sample_metadata, mock_session)

        # Verify work was created
        assert mock_session.add.called


def test_import_sanitized_handles_permission_error(mock_session, sample_metadata):
    """Test that import handles permission errors when reading file."""
    # Setup
    with patch('vulcanlab.markdown_import.import_flow.Path') as mock_path_class:
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_size = 1000
        mock_path.read_text.side_effect = PermissionError("Access denied")

        mock_path_class.return_value = mock_path

        # Test
        with pytest.raises(ValueError) as exc_info:
            import_sanitized_markdown("/fake/path.md", sample_metadata, mock_session)

        # Verify
        assert "Permission denied" in str(exc_info.value)


def test_import_sanitized_handles_file_with_only_frontmatter(mock_session, sample_metadata, tmp_path):
    """Test that import rejects files with only frontmatter, no content."""
    # Setup - create file with only frontmatter
    frontmatter_only = tmp_path / "frontmatter_only.md"
    frontmatter_only.write_text("---\ntitle: Test\n---\n", encoding='utf-8')

    # Test
    with pytest.raises(ValueError) as exc_info:
        import_sanitized_markdown(str(frontmatter_only), sample_metadata, mock_session)

    # Verify
    assert "no content" in str(exc_info.value).lower() or "only frontmatter" in str(exc_info.value).lower()


def test_import_sanitized_rolls_back_on_chunking_failure(mock_session, sample_metadata, tmp_path):
    """Test that import rolls back transaction when chunking fails."""
    # Setup - create a valid file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here", encoding='utf-8')

    # Mock chunking to fail
    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
        mock_heading.side_effect = Exception("Chunking failed")

        # Test
        with pytest.raises(ValueError) as exc_info:
            import_sanitized_markdown(str(test_file), sample_metadata, mock_session)

        # Verify rollback was called
        assert mock_session.rollback.called
        assert "Heading chunking failed" in str(exc_info.value)


def test_import_sanitized_rolls_back_on_database_error(mock_session, sample_metadata, tmp_path):
    """Test that import rolls back transaction on database errors."""
    # Setup - create a valid file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here", encoding='utf-8')

    # Mock session.add to raise database error
    mock_session.add.side_effect = SQLAlchemyError("Database error")

    # Test
    with pytest.raises(Exception):
        import_sanitized_markdown(str(test_file), sample_metadata, mock_session)

    # Verify rollback was called
    assert mock_session.rollback.called


def test_import_unsanitized_handles_empty_file(mock_session, sample_metadata, tmp_path):
    """Test that unsanitized import handles empty file correctly."""
    # Setup - create an empty file
    empty_file = tmp_path / "empty.md"
    empty_file.touch()

    # Test
    with pytest.raises(ValueError) as exc_info:
        import_unsanitized_markdown(str(empty_file), sample_metadata, mock_session)

    # Verify
    assert "empty" in str(exc_info.value).lower()


def test_import_unsanitized_handles_sanitization_failure(mock_session, sample_metadata, tmp_path):
    """Test that unsanitized import rolls back when sanitization fails."""
    # Setup - create a valid file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here", encoding='utf-8')

    # Mock sanitization to fail
    with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
        mock_sanitize.side_effect = Exception("Sanitization failed")

        # Test
        with pytest.raises(ValueError) as exc_info:
            import_unsanitized_markdown(str(test_file), sample_metadata, mock_session)

        # Verify rollback was called
        assert mock_session.rollback.called
        assert "Sanitization failed" in str(exc_info.value)


def test_import_unsanitized_handles_invalid_encoding_with_fallback(mock_session, sample_metadata, tmp_path):
    """Test that unsanitized import handles encoding errors with fallback."""
    # Setup - create a file with latin-1 encoding
    latin1_file = tmp_path / "latin1.md"
    # Use actual latin-1 specific bytes
    content_bytes = b'# Test\n\nCaf\xe9 r\xe9sum\xe9 na\xefve'
    latin1_file.write_bytes(content_bytes)

    # Mock sanitization functions
    with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize, \
         patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading, \
         patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:

        mock_sanitize_obj = Mock()
        mock_sanitize_obj.token_count = 100
        mock_sanitize.return_value = mock_sanitize_obj
        mock_heading.return_value = []
        mock_content.return_value = []

        # Test - should succeed using fallback encoding
        work = import_unsanitized_markdown(str(latin1_file), sample_metadata, mock_session)

        # Verify work was created
        assert mock_session.add.called


def test_import_sanitized_handles_file_with_only_whitespace(mock_session, sample_metadata, tmp_path):
    """Test that import rejects files with only whitespace."""
    # Setup - create file with only whitespace
    whitespace_file = tmp_path / "whitespace.md"
    whitespace_file.write_text("   \n\n\t\n   ", encoding='utf-8')

    # Test
    with pytest.raises(ValueError) as exc_info:
        import_sanitized_markdown(str(whitespace_file), sample_metadata, mock_session)

    # Verify
    assert "no content" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()


def test_import_rolls_back_on_content_chunking_failure(mock_session, sample_metadata, tmp_path):
    """Test that import rolls back when content chunking fails."""
    # Setup - create a valid file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent here", encoding='utf-8')

    # Mock chunking - heading succeeds, content fails
    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading, \
         patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:

        mock_heading.return_value = []
        mock_content.side_effect = Exception("Content chunking failed")

        # Test
        with pytest.raises(ValueError) as exc_info:
            import_sanitized_markdown(str(test_file), sample_metadata, mock_session)

        # Verify rollback was called
        assert mock_session.rollback.called
        assert "Content chunking failed" in str(exc_info.value)
