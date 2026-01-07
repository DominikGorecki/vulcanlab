"""
Unit tests for breadcrumb_builder module.

Tests breadcrumb generation by traversing chunk hierarchy upward to H1 or root.
All tests use mocked sessions without database.
"""

import pytest
from unittest.mock import MagicMock

from vulcanlab.search.breadcrumb_builder import build_breadcrumb


class TestBuildBreadcrumb:
    """Test suite for build_breadcrumb function."""

    def test_simple_hierarchy(self):
        """Test breadcrumb for simple H1 > H2 > H3 hierarchy."""
        mock_session = MagicMock()

        # Mock recursive CTE result: [H1, H2, H3] in root-to-leaf order
        mock_result = [
            ("Introduction", "H1", 2),
            ("Background", "H2", 1),
            ("Literature Review", "H3", 0)
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(123, mock_session)

        assert breadcrumb == "Introduction > Background > Literature Review"
        mock_session.execute.assert_called_once()

    def test_root_chunk_h1(self):
        """Test breadcrumb for root H1 chunk with no parent."""
        mock_session = MagicMock()

        # Mock result: just H1
        mock_result = [("Chapter 1", "H1", 0)]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(1, mock_session)

        assert breadcrumb == "Chapter 1"

    def test_orphaned_chunk(self):
        """Test breadcrumb for orphaned chunk (broken parent chain)."""
        mock_session = MagicMock()

        # Mock result: empty (no heading ancestors found)
        mock_result = []
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(999, mock_session)

        assert breadcrumb == "[No heading]"

    def test_chunk_not_found(self):
        """Test breadcrumb for non-existent chunk ID."""
        mock_session = MagicMock()

        # Mock result: empty
        mock_result = []
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(99999, mock_session)

        assert breadcrumb == "[No heading]"

    def test_deep_hierarchy(self):
        """Test breadcrumb for deep hierarchy (H1 > H2 > H3 > H4 > H5)."""
        mock_session = MagicMock()

        # Mock result: 5 levels deep
        mock_result = [
            ("Part I", "H1", 4),
            ("Chapter 1", "H2", 3),
            ("Section 1.1", "H3", 2),
            ("Subsection 1.1.1", "H4", 1),
            ("Detail", "H5", 0)
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(500, mock_session)

        assert breadcrumb == "Part I > Chapter 1 > Section 1.1 > Subsection 1.1.1 > Detail"

    def test_empty_heading_content(self):
        """Test breadcrumb when heading has empty content."""
        mock_session = MagicMock()

        # Mock result: H2 has empty content
        mock_result = [
            ("Chapter 1", "H1", 1),
            ("", "H2", 0)  # Empty content
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(200, mock_session)

        # Should filter out empty content
        assert breadcrumb == "Chapter 1"

    def test_all_empty_headings(self):
        """Test breadcrumb when all headings have empty content."""
        mock_session = MagicMock()

        # Mock result: all empty
        mock_result = [
            ("", "H1", 1),
            ("", "H2", 0)
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(300, mock_session)

        assert breadcrumb == "[No heading]"

    def test_whitespace_only_heading(self):
        """Test breadcrumb with whitespace-only heading content."""
        mock_session = MagicMock()

        # Mock result: H2 has only whitespace
        mock_result = [
            ("Chapter 1", "H1", 1),
            ("   ", "H2", 0)  # Whitespace only
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result

        breadcrumb = build_breadcrumb(400, mock_session)

        # Should filter out whitespace-only content
        assert breadcrumb == "Chapter 1"

    def test_session_none_raises_error(self):
        """Test that None session raises ValueError."""
        with pytest.raises(ValueError, match="Session is required"):
            build_breadcrumb(123, None)

    def test_database_error_returns_no_heading(self):
        """Test that database error returns [No heading]."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database connection lost")

        breadcrumb = build_breadcrumb(123, mock_session)

        assert breadcrumb == "[No heading]"
