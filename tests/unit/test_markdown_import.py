"""
Unit tests for markdown import flow.

Tests import_sanitized_markdown() function.

Usage:
    pytest tests/unit/test_markdown_import.py -v
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch, MagicMock

from vulcanlab.markdown_import.import_flow import import_sanitized_markdown
from vulcanlab.markdown_import.metadata import Metadata
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.enums import FileType


class TestImportSanitizedMarkdown:
    """Tests for import_sanitized_markdown() function."""

    def test_import_creates_work_record(self):
        """Test import creates Work with correct metadata."""
        with TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test Book"
author: "John Doe"
year: 2023
---

# Chapter 1

Content here."""
            test_file.write_text(content, encoding='utf-8')

            # Mock metadata
            metadata = Metadata(title="Test Book", author="John Doe", year=2023)

            # Mock session
            mock_session = MagicMock()

            # Mock chunking functions
            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    # Mock return values
                    mock_heading.return_value = [Mock(vector_status="no_vec")]
                    mock_content_chunk = Mock(vector_status="to_vec")
                    mock_content.return_value = [mock_content_chunk]

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify Work was created
                    assert mock_session.add.called
                    added_work = mock_session.add.call_args_list[0][0][0]
                    assert isinstance(added_work, Work)
                    assert added_work.title == "Test Book"
                    assert added_work.authors == "John Doe"
                    assert added_work.year == 2023
                    assert added_work.work_type == "markdown"

    def test_import_stores_sanitized_markdown(self):
        """Test import stores content in sanitized_markdown table."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test"
---

# Content

Test content."""
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify ParsedMarkdown and SanitizedMarkdown were added
                    # call_count should be 3: Work, ParsedMarkdown, SanitizedMarkdown
                    assert mock_session.add.call_count == 3
                    sanitized = mock_session.add.call_args_list[2][0][0]
                    assert isinstance(sanitized, SanitizedMarkdown)
                    assert "# Content" in sanitized.content
                    assert "Test content." in sanitized.content
                    # Frontmatter should be stripped
                    assert "---" not in sanitized.content
                    assert "title:" not in sanitized.content

    def test_import_strips_frontmatter(self):
        """Test import strips frontmatter from content."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test"
author: "Author"
---

Clean content."""
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    sanitized = mock_session.add.call_args_list[1][0][0]
                    assert sanitized.content == "Clean content."

    def test_import_calls_chunking_functions(self):
        """Test import calls heading and content chunking."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify chunking functions were called
                    mock_heading.assert_called_once()
                    mock_content.assert_called_once()

                    # Verify they were called with work_id and session
                    call_args = mock_heading.call_args
                    assert isinstance(call_args[0][1], MagicMock)  # session

    def test_import_sets_chunks_to_vec_status(self):
        """Test import sets content chunks to TO_VEC status."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            # Create mock chunks
            chunk1 = Mock(vector_status="no_vec")  # Heading chunk
            chunk2 = Mock(vector_status="to_vec")  # Content chunk
            chunk3 = Mock(vector_status="tbl")  # Table chunk

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = [chunk1]
                    mock_content.return_value = [chunk2, chunk3]

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify heading chunk status unchanged
                    assert chunk1.vector_status == "no_vec"

                    # Verify content chunks set to to_vec
                    assert chunk2.vector_status == "to_vec"
                    assert chunk3.vector_status == "to_vec"

    def test_import_file_not_found(self):
        """Test import raises FileNotFoundError for nonexistent file."""
        metadata = Metadata(title="Test")
        mock_session = MagicMock()

        with pytest.raises(FileNotFoundError, match="File not found"):
            import_sanitized_markdown("/nonexistent/file.md", metadata, mock_session)

    def test_import_empty_content_after_stripping(self):
        """Test import raises ValueError when content empty after stripping frontmatter."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            # Only frontmatter, no content
            content = """---
title: "Test"
---"""
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with pytest.raises(ValueError, match="only frontmatter or whitespace"):
                import_sanitized_markdown(str(test_file), metadata, mock_session)

    def test_import_heading_chunking_failure(self):
        """Test import handles heading chunking failure."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                mock_heading.side_effect = Exception("Chunking failed")

                with pytest.raises(ValueError, match="Heading chunking failed"):
                    import_sanitized_markdown(str(test_file), metadata, mock_session)

                # Verify transaction was rolled back on failure
                mock_session.rollback.assert_called()

    def test_import_content_chunking_failure(self):
        """Test import handles content chunking failure."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.side_effect = Exception("Content chunking failed")

                    with pytest.raises(ValueError, match="Content chunking failed"):
                        import_sanitized_markdown(str(test_file), metadata, mock_session)

    def test_import_updates_processing_status(self):
        """Test import updates processing_status throughout."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = [Mock(vector_status="no_vec")]
                    mock_content.return_value = [Mock(vector_status="to_vec")]

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify final status
                    added_work = mock_session.add.call_args_list[0][0][0]
                    # Processing status should be updated multiple times
                    assert added_work.processing_status is not None

    def test_import_stores_file_info(self):
        """Test import stores file info in work.files."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    added_work = mock_session.add.call_args_list[0][0][0]
                    assert added_work.files is not None
                    assert "original_file" in added_work.files
                    assert added_work.files["original_file"]["path"] == "test.md"
                    assert added_work.files["original_file"]["type"] == "markdown"

    def test_import_calculates_content_hash(self):
        """Test import calculates content hash for deduplication."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    added_work = mock_session.add.call_args_list[0][0][0]
                    assert added_work.content_hash is not None
                    assert len(added_work.content_hash) == 64  # SHA-256 hex

    def test_import_commits_transaction(self):
        """Test import commits the transaction."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Content", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify commit was called
                    assert mock_session.commit.called

    def test_import_without_frontmatter(self):
        """Test import works with markdown without frontmatter."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "# Just Content\n\nNo frontmatter."
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                    mock_heading.return_value = []
                    mock_content.return_value = []

                    work = import_sanitized_markdown(str(test_file), metadata, mock_session)

                    # Content should be unchanged
                    sanitized = mock_session.add.call_args_list[1][0][0]
                    assert sanitized.content == content
