"""
Unit tests for dense search functionality.

Tests dense search with mock embeddings and database queries.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from vulcanlab.search.search_dense import (
    search_dense,
    generate_query_embedding,
    truncate_content_words
)


class TestTruncateContentWords:
    """Tests for content truncation utility."""

    def test_truncate_short_content(self):
        """Content shorter than limit should not be truncated."""
        content = "This is a short sentence."
        result = truncate_content_words(content, word_limit=100)
        assert result == content
        assert "..." not in result

    def test_truncate_long_content(self):
        """Content longer than limit should be truncated with ellipsis."""
        words = ["word"] * 150
        content = " ".join(words)
        result = truncate_content_words(content, word_limit=100)

        result_words = result.replace("...", "").split()
        assert len(result_words) == 100
        assert result.endswith("...")

    def test_truncate_exact_limit(self):
        """Content exactly at limit should not be truncated."""
        words = ["word"] * 100
        content = " ".join(words)
        result = truncate_content_words(content, word_limit=100)
        assert result == content
        assert "..." not in result


class TestGenerateQueryEmbedding:
    """Tests for query embedding generation."""

    @patch('vulcanlab.ai.llm_factory.create_embeddings')
    def test_generate_embedding_success(self, mock_create_embeddings):
        """Successfully generate embedding for query."""
        mock_embeddings = Mock()
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_create_embeddings.return_value = mock_embeddings

        result = generate_query_embedding("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_embeddings.embed_query.assert_called_once_with("test query")

    @patch('vulcanlab.ai.llm_factory.create_embeddings')
    def test_generate_embedding_failure(self, mock_create_embeddings):
        """Raise RuntimeError when embedding generation fails."""
        mock_embeddings = Mock()
        mock_embeddings.embed_query.side_effect = Exception("API error")
        mock_create_embeddings.return_value = mock_embeddings

        with pytest.raises(RuntimeError, match="Failed to generate query embedding"):
            generate_query_embedding("test query")


class TestSearchDense:
    """Tests for dense search function."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def mock_embedding(self):
        """Mock embedding vector."""
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_search_dense_validates_page(self, mock_session):
        """Validate page parameter must be >= 1."""
        with pytest.raises(ValueError, match="Page must be >= 1"):
            search_dense("query", mock_session, page=0)

    def test_search_dense_validates_page_size(self, mock_session):
        """Validate page_size parameter must be >= 1."""
        with pytest.raises(ValueError, match="Page size must be >= 1"):
            search_dense("query", mock_session, page_size=0)

    def test_search_dense_validates_session(self):
        """Validate session is required."""
        with pytest.raises(ValueError, match="Session is required"):
            search_dense("query", None)

    def test_search_dense_validates_query(self, mock_session):
        """Validate query cannot be empty."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_dense("", mock_session)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_dense("   ", mock_session)

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_returns_results(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search returns results ordered by similarity."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1 > Section 1.1"

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 3

        # Mock search query
        mock_search_rows = [
            (1, "Content about memory systems...", "H2", 5, 10, 20,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.95),
            (2, "More about memory...", "H3", 5, 25, 35,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.87),
            (3, "Discussion of memory...", "sentence", 5, 40, 45,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.75),
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        # Configure session to return appropriate results
        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search
        results, total_count = search_dense(
            "memory systems",
            mock_session,
            page=1,
            page_size=20,
            headings_only=False
        )

        # Assertions
        assert total_count == 3
        assert len(results) == 3

        # Check first result
        assert results[0]["id"] == 1
        assert results[0]["level"] == "H2"
        assert results[0]["work_title"] == "Cognitive Psychology"
        assert results[0]["similarity_score"] == 0.95
        assert results[0]["breadcrumb"] == "Chapter 1 > Section 1.1"
        assert "memory systems" in results[0]["content_preview"].lower()

        # Verify embedding was generated
        mock_generate_embedding.assert_called_once_with("memory systems")

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_headings_only(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search with headings_only filters to H1-H5."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1 > Section 1.1"

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        # Mock search query - only headings
        mock_search_rows = [
            (1, "Content about memory systems...", "H2", 5, 10, 20,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.95),
            (2, "More about memory...", "H3", 5, 25, 35,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.87),
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search with headings_only
        results, total_count = search_dense(
            "memory systems",
            mock_session,
            page=1,
            page_size=20,
            headings_only=True
        )

        # Assertions
        assert total_count == 2
        assert len(results) == 2

        # All results should be headings
        for result in results:
            assert result["level"] in ["H1", "H2", "H3", "H4", "H5"]

        # Verify SQL WHERE clause included level filter
        call_args = mock_session.execute.call_args_list[1][0]
        sql_text = str(call_args[0])
        assert "c.level IN ('H1', 'H2', 'H3', 'H4', 'H5')" in sql_text

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_skips_missing_embeddings(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search skips chunks without embeddings."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1"

        # Mock results (WHERE clause already filters out NULL embeddings)
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_search_rows = [
            (1, "Content with embedding...", "H2", 5, 10, 20,
             "Cognitive Psychology", "Eysenck & Keane", 2015, 0.95),
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search
        results, total_count = search_dense("query", mock_session)

        # Verify WHERE clause filters NULL embeddings
        call_args = mock_session.execute.call_args_list[0][0]
        sql_text = str(call_args[0])
        assert "c.embedding IS NOT NULL" in sql_text

        assert len(results) == 1

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_pagination(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search respects pagination parameters."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1"

        # Mock total count of 50 results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 50

        # Mock page 2 results (items 21-40)
        mock_search_rows = [
            (21 + i, f"Content {i}...", "H2", 5, 10 + i * 10, 20 + i * 10,
             "Book", "Author", 2020, 0.8 - i * 0.01)
            for i in range(20)
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search for page 2
        results, total_count = search_dense(
            "query",
            mock_session,
            page=2,
            page_size=20
        )

        # Verify pagination
        assert total_count == 50
        assert len(results) == 20

        # Verify OFFSET was calculated correctly (page 2, offset = 20)
        call_args = mock_session.execute.call_args_list[1][0]
        params = call_args[1]
        assert params["offset"] == 20
        assert params["limit"] == 20

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    def test_search_dense_embedding_failure(
        self,
        mock_generate_embedding,
        mock_session
    ):
        """Dense search raises RuntimeError when embedding fails."""
        mock_generate_embedding.side_effect = RuntimeError("Embedding failed")

        with pytest.raises(RuntimeError, match="Dense search failed"):
            search_dense("query", mock_session)

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_similarity_score_calculation(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search calculates similarity as 1 - distance."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1"

        # Mock results with distance values
        # Similarity = 1 - distance
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        mock_search_rows = [
            (1, "High similarity content", "H2", 5, 10, 20,
             "Book", "Author", 2020, 0.95),  # distance = 0.05
            (2, "Lower similarity content", "H3", 5, 30, 40,
             "Book", "Author", 2020, 0.65),  # distance = 0.35
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search
        results, total_count = search_dense("query", mock_session)

        # Verify similarity scores
        assert results[0]["similarity_score"] == 0.95
        assert results[1]["similarity_score"] == 0.65

        # Verify SQL calculates as 1 - distance
        call_args = mock_session.execute.call_args_list[1][0]
        sql_text = str(call_args[0])
        assert "1 - (c.embedding <=> :embedding)" in sql_text

    @patch('vulcanlab.search.search_dense.generate_query_embedding')
    @patch('vulcanlab.search.search_dense.build_breadcrumb')
    def test_search_dense_top_k_limit(
        self,
        mock_breadcrumb,
        mock_generate_embedding,
        mock_session,
        mock_embedding
    ):
        """Dense search respects top_k parameter."""
        # Setup mocks
        mock_generate_embedding.return_value = mock_embedding
        mock_breadcrumb.return_value = "Chapter 1"

        # Mock count limited by top_k
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 10  # Limited by top_k=10

        mock_search_rows = [
            (i, f"Content {i}", "H2", 5, 10, 20, "Book", "Author", 2020, 0.9 - i * 0.05)
            for i in range(10)
        ]
        mock_search_result = Mock()
        mock_search_result.fetchall.return_value = mock_search_rows

        mock_session.execute.side_effect = [mock_count_result, mock_search_result]

        # Execute search with top_k=10
        results, total_count = search_dense(
            "query",
            mock_session,
            top_k=10
        )

        # Verify top_k was used in query
        call_args = mock_session.execute.call_args_list[0][0]
        params = call_args[1]
        assert params["top_k"] == 10
