"""
Unit tests for markdown duplicate detection.

Tests check_duplicate_work() function.

Usage:
    pytest tests/unit/test_markdown_duplicate_check.py -v
"""

import pytest
from unittest.mock import MagicMock, Mock

from vulcanlab.markdown_import.duplicate_check import check_duplicate_work
from vulcanlab.data.models.work import Work


class TestCheckDuplicateWork:
    """Tests for check_duplicate_work() function."""

    def test_finds_exact_match(self):
        """Test finding exact title and author match."""
        # Mock session and query
        mock_session = MagicMock()
        mock_work = Mock(spec=Work)
        mock_work.id = 123
        mock_work.title = "The Psychology of Learning"
        mock_work.authors = "John Doe"

        # Set up query chain
        mock_query = mock_session.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter2.first.return_value = mock_work

        # Call function
        result = check_duplicate_work(
            "The Psychology of Learning",
            "John Doe",
            mock_session
        )

        # Verify result
        assert result == mock_work
        assert result.id == 123
        assert result.title == "The Psychology of Learning"

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching for title and author."""
        mock_session = MagicMock()
        mock_work = Mock(spec=Work)
        mock_work.id = 456
        mock_work.title = "The Psychology of Learning"
        mock_work.authors = "John Doe"

        # Set up query chain
        mock_query = mock_session.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter2.first.return_value = mock_work

        # Call with different case
        result = check_duplicate_work(
            "the psychology of learning",  # lowercase
            "john doe",  # lowercase
            mock_session
        )

        # Should still find the work
        assert result == mock_work
        assert result.id == 456

    def test_no_match_returns_none(self):
        """Test returns None when no match found."""
        mock_session = MagicMock()

        # Set up query to return None
        mock_query = mock_session.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter2.first.return_value = None

        result = check_duplicate_work(
            "Nonexistent Book",
            "Unknown Author",
            mock_session
        )

        assert result is None

    def test_empty_title_returns_none(self):
        """Test returns None for empty title."""
        mock_session = MagicMock()

        result = check_duplicate_work("", "John Doe", mock_session)

        assert result is None
        # Query should not be called
        mock_session.query.assert_not_called()

    def test_empty_author_returns_none(self):
        """Test returns None for empty author."""
        mock_session = MagicMock()

        result = check_duplicate_work("Test Title", "", mock_session)

        assert result is None
        # Query should not be called
        mock_session.query.assert_not_called()

    def test_partial_author_match(self):
        """Test matches partial author names in authors field."""
        mock_session = MagicMock()
        mock_work = Mock(spec=Work)
        mock_work.id = 789
        mock_work.title = "Cognitive Psychology"
        mock_work.authors = "John Doe, Jane Smith"  # Multiple authors

        # Set up query chain
        mock_query = mock_session.query.return_value
        mock_filter1 = mock_query.filter.return_value
        mock_filter2 = mock_filter1.filter.return_value
        mock_filter2.first.return_value = mock_work

        # Search for just one author
        result = check_duplicate_work(
            "Cognitive Psychology",
            "John Doe",  # Only one of the authors
            mock_session
        )

        # Should find the work
        assert result == mock_work
        assert result.id == 789

    def test_handles_database_error(self):
        """Test handles database errors by raising exception."""
        mock_session = MagicMock()

        # Make query raise an error
        mock_session.query.side_effect = Exception("Database connection error")

        with pytest.raises(Exception) as exc_info:
            check_duplicate_work("Test Title", "Test Author", mock_session)

        assert "Database connection error" in str(exc_info.value)

    def test_none_values_returns_none(self):
        """Test returns None for None values."""
        mock_session = MagicMock()

        result1 = check_duplicate_work(None, "John Doe", mock_session)
        result2 = check_duplicate_work("Test Title", None, mock_session)
        result3 = check_duplicate_work(None, None, mock_session)

        assert result1 is None
        assert result2 is None
        assert result3 is None
        mock_session.query.assert_not_called()

    def test_whitespace_only_returns_none(self):
        """Test returns None for whitespace-only strings."""
        mock_session = MagicMock()

        result1 = check_duplicate_work("   ", "John Doe", mock_session)
        result2 = check_duplicate_work("Test Title", "   ", mock_session)

        # Empty strings after strip should return None
        # Note: The function checks "not title" which is True for empty strings
        assert result1 is None
        assert result2 is None
