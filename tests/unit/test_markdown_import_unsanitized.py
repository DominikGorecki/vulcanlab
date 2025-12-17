"""
Unit tests for unsanitized markdown import flow.

Tests import_unsanitized_markdown() and determine_sanitization_method() functions.

Usage:
    pytest tests/unit/test_markdown_import_unsanitized.py -v
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch, MagicMock

from vulcanlab.markdown_import.import_flow import (
    import_unsanitized_markdown,
    determine_sanitization_method,
    count_tokens
)
from vulcanlab.markdown_import.metadata import Metadata
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
from vulcanlab.data.models.enums import FileType, DocumentClassification


class TestDetermineSanitizationMethod:
    """Tests for determine_sanitization_method() function."""

    def test_returns_small_for_content_below_threshold(self):
        """Test returns 'small' for content with tokens < threshold."""
        # Short content that's definitely below threshold
        content = "# Short Document\n\nThis is a small document."

        with patch('vulcanlab.markdown_import.import_flow.get_token_threshold', return_value=15000):
            result = determine_sanitization_method(content)
            assert result == "small"

    def test_returns_large_for_content_above_threshold(self):
        """Test returns 'large' for content with tokens >= threshold."""
        # Generate large content that exceeds threshold
        content = "# Large Document\n\n" + ("This is a paragraph. " * 10000)

        with patch('vulcanlab.markdown_import.import_flow.get_token_threshold', return_value=100):
            result = determine_sanitization_method(content)
            assert result == "large"

    def test_uses_tiktoken_for_counting(self):
        """Test uses tiktoken for token counting."""
        content = "# Test\n\nContent here."

        with patch('vulcanlab.markdown_import.import_flow.count_tokens') as mock_count:
            with patch('vulcanlab.markdown_import.import_flow.get_token_threshold', return_value=15000):
                mock_count.return_value = 50
                result = determine_sanitization_method(content)

                # Verify count_tokens was called
                mock_count.assert_called_once_with(content)

    def test_compares_against_config_threshold(self):
        """Test compares token count against configured threshold."""
        content = "# Test"

        # Test with high threshold
        with patch('vulcanlab.markdown_import.import_flow.count_tokens', return_value=1000):
            with patch('vulcanlab.markdown_import.import_flow.get_token_threshold', return_value=2000):
                assert determine_sanitization_method(content) == "small"

        # Test with low threshold
        with patch('vulcanlab.markdown_import.import_flow.count_tokens', return_value=1000):
            with patch('vulcanlab.markdown_import.import_flow.get_token_threshold', return_value=500):
                assert determine_sanitization_method(content) == "large"


class TestCountTokens:
    """Tests for count_tokens() function."""

    def test_counts_tokens_with_tiktoken(self):
        """Test counts tokens using tiktoken encoding."""
        content = "Hello world"
        count = count_tokens(content)

        # Should return a positive integer
        assert isinstance(count, int)
        assert count > 0

    def test_handles_empty_string(self):
        """Test returns 0 for empty string."""
        assert count_tokens("") == 0

    def test_handles_none_gracefully(self):
        """Test handles None input gracefully."""
        with patch('vulcanlab.markdown_import.import_flow.ENCODING') as mock_encoding:
            mock_encoding.encode.side_effect = Exception("Error")
            # Should fallback to word-based estimate
            result = count_tokens("test content")
            assert result > 0


class TestImportUnsanitizedMarkdown:
    """Tests for import_unsanitized_markdown() function."""

    def test_creates_work_with_markdown_import_type(self):
        """Test creates Work record with FileType.MARKDOWN_IMPORT."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "# Test\n\nUnsanitized content."
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test Book", author="John Doe", year=2023)
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple'):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple'):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Verify Work was created
                            assert mock_session.add.called
                            # First add call is the Work
                            added_work = mock_session.add.call_args_list[0][0][0]
                            assert isinstance(added_work, Work)
                            assert added_work.title == "Test Book"

    def test_stores_original_content_in_parsed_markdown(self):
        """Test stores original markdown in ParsedMarkdown."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "# Original\n\nUnsanitized content."
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Second add call should be ParsedMarkdown
                            parsed = mock_session.add.call_args_list[1][0][0]
                            assert isinstance(parsed, ParsedMarkdown)
                            assert "# Original" in parsed.content

    def test_calls_sanitize_small_for_small_documents(self):
        """Test calls sanitize_small_document for documents below threshold."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Small doc", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize_small:
                    with patch('vulcanlab.markdown_import.import_flow.sanitize_large_document') as mock_sanitize_large:
                        with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                            with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                                mock_sanitize_small.return_value = Mock(token_count=100)

                                work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                                # Verify sanitize_small was called, not sanitize_large
                                mock_sanitize_small.assert_called_once()
                                mock_sanitize_large.assert_not_called()

    def test_calls_sanitize_large_for_large_documents(self):
        """Test calls sanitize_large_document for documents above threshold."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Large doc", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="large"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize_small:
                    with patch('vulcanlab.markdown_import.import_flow.sanitize_large_document') as mock_sanitize_large:
                        with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                            with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                                mock_sanitize_large.return_value = Mock(token_count=20000)

                                work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                                # Verify sanitize_large was called, not sanitize_small
                                mock_sanitize_large.assert_called_once()
                                mock_sanitize_small.assert_not_called()

    def test_stores_sanitized_content(self):
        """Test sanitized content is stored by sanitization function."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            mock_sanitized = Mock(token_count=150)

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document', return_value=mock_sanitized):
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Sanitization function returns SanitizedMarkdown with token_count
                            assert mock_sanitized.token_count == 150

    def test_calls_chunking_after_sanitization(self):
        """Test calls chunking functions after sanitization completes."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                            mock_sanitize.return_value = Mock(token_count=100)
                            mock_heading.return_value = []
                            mock_content.return_value = []

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Verify chunking functions were called
                            mock_heading.assert_called_once()
                            mock_content.assert_called_once()

    def test_sets_chunks_to_to_vec_status(self):
        """Test sets all content chunks to TO_VEC status."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            # Create mock chunks
            heading_chunk = Mock(vector_status="no_vec")
            content_chunk1 = Mock(vector_status="pending")
            content_chunk2 = Mock(vector_status="ready")

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple') as mock_heading:
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple') as mock_content:
                            mock_sanitize.return_value = Mock(token_count=100)
                            mock_heading.return_value = [heading_chunk]
                            mock_content.return_value = [content_chunk1, content_chunk2]

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Verify heading chunk unchanged
                            assert heading_chunk.vector_status == "no_vec"

                            # Verify content chunks set to to_vec
                            assert content_chunk1.vector_status == "to_vec"
                            assert content_chunk2.vector_status == "to_vec"

    def test_handles_sanitization_errors(self):
        """Test handles sanitization errors gracefully."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    mock_sanitize.side_effect = Exception("LLM API failure")

                    with pytest.raises(ValueError, match="Sanitization failed"):
                        import_unsanitized_markdown(str(test_file), metadata, mock_session)

                    # Verify commit was called (to save error status)
                    assert mock_session.commit.called

    def test_token_counting_matches_parse_classify_behavior(self):
        """Test token counting uses same method as parse_classify module."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = "# Test Document\n\nSome content here."
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.count_tokens') as mock_count:
                with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                    with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                        with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                            with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                                mock_count.return_value = 100
                                mock_sanitize.return_value = Mock(token_count=100)

                                work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                                # Verify count_tokens was called (uses tiktoken)
                                assert mock_count.called

    def test_file_not_found_raises_error(self):
        """Test raises FileNotFoundError for nonexistent file."""
        metadata = Metadata(title="Test")
        mock_session = MagicMock()

        with pytest.raises(FileNotFoundError, match="File not found"):
            import_unsanitized_markdown("/nonexistent/file.md", metadata, mock_session)

    def test_empty_content_after_stripping_raises_error(self):
        """Test raises ValueError when content empty after stripping frontmatter."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test"
---"""
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with pytest.raises(ValueError, match="no content after stripping frontmatter"):
                import_unsanitized_markdown(str(test_file), metadata, mock_session)

    def test_strips_frontmatter_before_processing(self):
        """Test strips frontmatter before sanitization."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            content = """---
title: "Test"
author: "Author"
---

# Clean Content"""
            test_file.write_text(content, encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Check ParsedMarkdown has clean content without frontmatter
                            parsed = mock_session.add.call_args_list[1][0][0]
                            assert "---" not in parsed.content
                            assert "title:" not in parsed.content
                            assert "# Clean Content" in parsed.content

    def test_creates_parsed_markdown_with_correct_classification(self):
        """Test creates ParsedMarkdown with correct classification."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            # Test small classification
            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            parsed = mock_session.add.call_args_list[1][0][0]
                            assert parsed.classification == DocumentClassification.SMALL

    def test_updates_processing_status_throughout(self):
        """Test updates processing_status at each step."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[Mock()]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[Mock()]):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Final processing status should be 'complete'
                            added_work = mock_session.add.call_args_list[0][0][0]
                            assert added_work.processing_status["simple_conversion_step"] == "complete"
                            assert "simple_conversion_classification" in added_work.processing_status

    def test_logs_sanitization_operations(self):
        """Test logs important sanitization operations."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.logger') as mock_logger:
                with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                    with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                        with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                            with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                                mock_sanitize.return_value = Mock(token_count=100)

                                work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                                # Verify logging calls were made
                                assert mock_logger.info.called

    def test_commits_transaction_on_success(self):
        """Test commits transaction when import succeeds."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test", encoding='utf-8')

            metadata = Metadata(title="Test")
            mock_session = MagicMock()

            with patch('vulcanlab.markdown_import.import_flow.determine_sanitization_method', return_value="small"):
                with patch('vulcanlab.markdown_import.import_flow.sanitize_small_document') as mock_sanitize:
                    with patch('vulcanlab.markdown_import.import_flow.create_heading_chunks_simple', return_value=[]):
                        with patch('vulcanlab.markdown_import.import_flow.create_content_chunks_simple', return_value=[]):
                            mock_sanitize.return_value = Mock(token_count=100)

                            work = import_unsanitized_markdown(str(test_file), metadata, mock_session)

                            # Verify final commit was called
                            assert mock_session.commit.called
