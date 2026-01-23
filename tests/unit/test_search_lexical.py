"""
Unit tests for search_lexical module.

Tests PostgreSQL full-text search with ts_vector/ts_query.
All tests use mocked sessions without database.
"""

import pytest
from unittest.mock import MagicMock, patch

from vulcanlab.search.search_lexical import search_lexical, truncate_content_words


class TestTruncateContentWords:
    """Test suite for truncate_content_words helper."""

    def test_short_content_no_truncation(self):
        """Test content shorter than limit is not truncated."""
        content = "This is a short sentence with only ten words here."
        result = truncate_content_words(content, word_limit=100)
        assert result == content
        assert not result.endswith("...")

    def test_exact_limit_no_truncation(self):
        """Test content exactly at limit is not truncated."""
        words = ["word"] * 100
        content = " ".join(words)
        result = truncate_content_words(content, word_limit=100)
        assert result == content
        assert not result.endswith("...")

    def test_long_content_truncated(self):
        """Test content longer than limit is truncated."""
        words = ["word"] * 150
        content = " ".join(words)
        result = truncate_content_words(content, word_limit=100)

        # Should have exactly 100 words plus ellipsis
        result_words = result.replace("...", "").split()
        assert len(result_words) == 100
        assert result.endswith("...")

    def test_truncation_at_word_boundary(self):
        """Test truncation happens at word boundaries, not mid-word."""
        content = "Memory systems in cognitive psychology include working memory and long-term memory."
        result = truncate_content_words(content, word_limit=5)

        assert result == "Memory systems in cognitive psychology..."
        # Verify no partial words
        assert not result[:-3].endswith(" psych")


class TestSearchLexical:
    """Test suite for search_lexical function."""

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_basic_search_returns_results(self, mock_breadcrumb):
        """Test basic search returns formatted results."""
        mock_session = MagicMock()
        mock_breadcrumb.return_value = "Chapter 1 > Introduction"

        # Mock count query
        mock_session.execute.return_value.scalar.return_value = 2

        # Mock search query
        mock_rows = [
            (1, "Memory systems in the brain...", "H2", 5, 100, 120,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.85, "Chapter 1 > Introduction"),
            (2, "Attention and perception...", "H3", 5, 150, 170,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.72, "Chapter 1 > Introduction")
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_rows

        results, total = search_lexical("memory", mock_session, page=1, page_size=20)

        assert total == 2
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[0]["breadcrumb"] == "Chapter 1 > Introduction"
        assert results[0]["work_title"] == "Cognitive Psychology"
        assert results[0]["rank_score"] == 0.85

    def test_empty_query_raises_error(self):
        """Test empty query raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_lexical("", mock_session)

    def test_whitespace_query_raises_error(self):
        """Test whitespace-only query raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_lexical("   ", mock_session)

    def test_none_session_raises_error(self):
        """Test None session raises ValueError."""
        with pytest.raises(ValueError, match="Session is required"):
            search_lexical("test", None)

    def test_invalid_page_raises_error(self):
        """Test page < 1 raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Page must be >= 1"):
            search_lexical("test", mock_session, page=0)

    def test_invalid_page_size_raises_error(self):
        """Test page_size < 1 raises ValueError."""
        mock_session = MagicMock()

        with pytest.raises(ValueError, match="Page size must be >= 1"):
            search_lexical("test", mock_session, page_size=0)

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_headings_only_filter(self, mock_breadcrumb):
        """Test headings_only filter excludes sentence/chunk levels."""
        mock_session = MagicMock()
        mock_breadcrumb.return_value = "Test"

        # Mock count
        mock_session.execute.return_value.scalar.return_value = 1

        # Mock results: only H2 chunk
        mock_rows = [
            (1, "Test content", "H2", 5, 100, 120,
             "Test Work", "Author", 2020, 0.90, "Breadcrumb")
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_rows

        results, total = search_lexical(
            "test", mock_session, headings_only=True
        )

        # Verify SQL contains level filter
        call_args = mock_session.execute.call_args_list
        # First call is count, second is search
        search_sql = str(call_args[1][0][0])
        assert "level IN ('H1', 'H2', 'H3', 'H4', 'H5')" in search_sql

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_pagination_offset_calculation(self, mock_breadcrumb):
        """Test pagination calculates correct offset."""
        mock_session = MagicMock()
        mock_breadcrumb.return_value = "Test"

        # Mock count
        mock_session.execute.return_value.scalar.return_value = 100
        mock_session.execute.return_value.fetchall.return_value = []

        # Page 3, page_size 20 → offset = (3-1)*20 = 40
        search_lexical("test", mock_session, page=3, page_size=20)

        # Verify OFFSET parameter in SQL call
        call_args = mock_session.execute.call_args_list
        params = call_args[1][0][1]  # Second call (search), second arg (params)
        assert params["offset"] == 40
        assert params["limit"] == 20

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_no_results_returns_empty_list(self, mock_breadcrumb):
        """Test search with no results returns empty list."""
        mock_session = MagicMock()

        # Mock count: 0
        mock_session.execute.return_value.scalar.return_value = 0
        mock_session.execute.return_value.fetchall.return_value = []

        results, total = search_lexical("nonexistent", mock_session)

        assert total == 0
        assert results == []

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_work_metadata_included(self, mock_breadcrumb):
        """Test results include work metadata from JOIN."""
        mock_session = MagicMock()
        mock_breadcrumb.return_value = "Test"

        # Mock count
        mock_session.execute.return_value.scalar.return_value = 1

        # Mock results with work metadata
        mock_rows = [
            (1, "Content", "H1", 5, 1, 10,
             "Test Work Title", "Test Author", 2023, 0.95, "Breadcrumb")
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_rows

        results, total = search_lexical("test", mock_session)

        assert results[0]["work_title"] == "Test Work Title"
        assert results[0]["work_authors"] == "Test Author"
        assert results[0]["work_year"] == 2023

    @patch('vulcanlab.search.search_lexical.build_breadcrumb')
    def test_content_preview_truncated(self, mock_breadcrumb):
        """Test content preview is truncated to 100 words."""
        mock_session = MagicMock()
        mock_breadcrumb.return_value = "Test"

        # Mock count
        mock_session.execute.return_value.scalar.return_value = 1

        # Create content with >100 words
        long_content = " ".join(["word"] * 150)
        mock_rows = [
            (1, long_content, "H1", 5, 1, 10,
             "Work", "Author", 2020, 0.80, "Breadcrumb")
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_rows

        results, total = search_lexical("test", mock_session)

        preview = results[0]["content_preview"]
        # Should be truncated
        assert preview.endswith("...")
        # Should have exactly 100 words (plus ellipsis)
        preview_words = preview.replace("...", "").split()
        assert len(preview_words) == 100

    def test_search_lexical_filters_dense_lexical_use(self):
        """Lexical search filters by dense_lexical_use=TRUE by default."""
        mock_session = MagicMock()
        mock_session.execute.return_value = MagicMock()

        search_lexical("query", mock_session, headings_only=False)

        # Check search query (second call to execute)
        call_args = mock_session.execute.call_args_list[1][0]
        sql_text = str(call_args[0])
        assert "c.dense_lexical_use = TRUE" in sql_text
