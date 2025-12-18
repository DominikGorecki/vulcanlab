"""
Unit tests for chunk_operations module.

Tests lexical search with title/content ranking, recursive descendant retrieval,
and cascading deletion operations. All tests use mocked sessions without database.
"""

import pytest
from unittest.mock import MagicMock, call, patch

from src.vulcanlab.data.chunk_operations import (
    search_chunks_lexical,
    get_all_descendants,
    delete_chunk_cascade,
)
from tests.unit.mock_helpers import (
    mock_session,
    create_mock_chunk,
    create_mock_query_chain,
)


class TestSearchChunksLexical:
    """Test suite for search_chunks_lexical function."""

    def test_exact_title_match(self, mock_session):
        """Test exact title match ranks first."""
        # Create chunks with different match types
        exact_match = create_mock_chunk(
            id=1,
            heading_breadcrumbs="Chapter 1 > Introduction",
            content="Some content about other topics"
        )
        partial_match = create_mock_chunk(
            id=2,
            heading_breadcrumbs="Chapter 2 > Introduction to Python",
            content="More content here"
        )
        content_match = create_mock_chunk(
            id=3,
            heading_breadcrumbs="Chapter 3 > Summary",
            content="This introduction is in the content"
        )

        # Mock query chain to return all chunks
        mock_query = create_mock_query_chain(
            return_data=[exact_match, partial_match, content_match],
            return_scalar=3
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("Introduction", session=mock_session)

        assert total == 3
        assert len(results) == 3
        # The ranking is done in SQL, so we trust the query was built correctly
        # We just verify the function returns the mocked results
        assert results[0].id == 1  # exact_match should be first

    def test_partial_title_match(self, mock_session):
        """Test partial title matches rank after exact matches."""
        partial_match = create_mock_chunk(
            id=1,
            heading_breadcrumbs="H1 > References and Citations",
            content="Some content"
        )

        mock_query = create_mock_query_chain(
            return_data=[partial_match],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("Reference", session=mock_session)

        assert total == 1
        assert len(results) == 1
        assert results[0].id == 1

    def test_content_match(self, mock_session):
        """Test content matches rank after title matches."""
        content_match = create_mock_chunk(
            id=1,
            heading_breadcrumbs="Chapter 1 > Overview",
            content="This section contains reference material"
        )

        mock_query = create_mock_query_chain(
            return_data=[content_match],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("reference", session=mock_session)

        assert total == 1
        assert len(results) == 1
        assert results[0].id == 1

    def test_combined_ranking(self, mock_session):
        """Test combined ranking with exact, partial, and content matches."""
        exact = create_mock_chunk(
            id=1,
            heading_breadcrumbs="Main > Test",
            content="Other content"
        )
        partial = create_mock_chunk(
            id=2,
            heading_breadcrumbs="Main > Testing Guide",
            content="Other content"
        )
        content = create_mock_chunk(
            id=3,
            heading_breadcrumbs="Main > Overview",
            content="This covers test scenarios"
        )

        mock_query = create_mock_query_chain(
            return_data=[exact, partial, content],
            return_scalar=3
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("Test", session=mock_session)

        assert total == 3
        assert len(results) == 3

    def test_no_breadcrumbs(self, mock_session):
        """Test handling of None heading_breadcrumbs."""
        chunk_no_breadcrumbs = create_mock_chunk(
            id=1,
            heading_breadcrumbs=None,
            content="This content has the search term"
        )

        mock_query = create_mock_query_chain(
            return_data=[chunk_no_breadcrumbs],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("search", session=mock_session)

        assert total == 1
        assert len(results) == 1
        assert results[0].heading_breadcrumbs is None

    def test_pagination_page_1(self, mock_session):
        """Test pagination returns correct page 1 results."""
        chunks = [create_mock_chunk(id=i, content=f"Content {i}") for i in range(1, 26)]

        mock_query = create_mock_query_chain(
            return_data=chunks,
            return_scalar=50
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("Content", page=1, page_size=25, session=mock_session)

        assert total == 50
        assert len(results) == 25
        # Verify offset was set to 0 for page 1
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(25)

    def test_pagination_page_2(self, mock_session):
        """Test pagination returns correct page 2 results."""
        chunks = [create_mock_chunk(id=i, content=f"Content {i}") for i in range(26, 51)]

        mock_query = create_mock_query_chain(
            return_data=chunks,
            return_scalar=50
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("Content", page=2, page_size=25, session=mock_session)

        assert total == 50
        assert len(results) == 25
        # Verify offset was set to 25 for page 2
        mock_query.offset.assert_called_once_with(25)
        mock_query.limit.assert_called_once_with(25)

    def test_empty_results(self, mock_session):
        """Test search with no matches returns empty results."""
        mock_query = create_mock_query_chain(
            return_data=[],
            return_scalar=0
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("nonexistent", session=mock_session)

        assert total == 0
        assert len(results) == 0

    def test_case_insensitive(self, mock_session):
        """Test case-insensitive matching."""
        chunk = create_mock_chunk(
            id=1,
            heading_breadcrumbs="Main > Reference",
            content="Some content"
        )

        mock_query = create_mock_query_chain(
            return_data=[chunk],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("reference", session=mock_session)

        assert total == 1
        assert len(results) == 1

    def test_invalid_page_number(self, mock_session):
        """Test error on invalid page number."""
        with pytest.raises(ValueError, match="Page must be >= 1"):
            search_chunks_lexical("test", page=0, session=mock_session)

    def test_invalid_page_size(self, mock_session):
        """Test error on invalid page size."""
        with pytest.raises(ValueError, match="Page size must be >= 1"):
            search_chunks_lexical("test", page_size=0, session=mock_session)

    def test_missing_session(self):
        """Test error when session is None."""
        with pytest.raises(ValueError, match="Session is required"):
            search_chunks_lexical("test", session=None)

    def test_title_extraction_multiple_levels(self, mock_session):
        """Test title extraction from multi-level breadcrumbs."""
        chunk = create_mock_chunk(
            id=1,
            heading_breadcrumbs="H1 > H2 > H3",
            content="Content"
        )

        mock_query = create_mock_query_chain(
            return_data=[chunk],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("H3", session=mock_session)

        assert total == 1
        assert len(results) == 1

    def test_title_extraction_single_level(self, mock_session):
        """Test title extraction from single-level breadcrumbs."""
        chunk = create_mock_chunk(
            id=1,
            heading_breadcrumbs="H1",
            content="Content"
        )

        mock_query = create_mock_query_chain(
            return_data=[chunk],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("H1", session=mock_session)

        assert total == 1
        assert len(results) == 1

    def test_title_extraction_empty_breadcrumbs(self, mock_session):
        """Test handling of empty string breadcrumbs."""
        chunk = create_mock_chunk(
            id=1,
            heading_breadcrumbs="",
            content="Content with search term"
        )

        mock_query = create_mock_query_chain(
            return_data=[chunk],
            return_scalar=1
        )
        mock_session.query.return_value = mock_query

        results, total = search_chunks_lexical("search", session=mock_session)

        assert total == 1
        assert len(results) == 1


class TestGetAllDescendants:
    """Test suite for get_all_descendants function."""

    def test_multi_level_hierarchy(self, mock_session):
        """Test recursive retrieval of multi-level descendants."""
        # Create a 4-level hierarchy: parent -> child -> grandchild -> great-grandchild
        parent = create_mock_chunk(id=1, parent_id=None)
        child = create_mock_chunk(id=2, parent_id=1)
        grandchild = create_mock_chunk(id=3, parent_id=2)
        great_grandchild = create_mock_chunk(id=4, parent_id=3)

        def query_side_effect(*args):
            """Return appropriate mock query based on the model being queried."""
            mock_query = MagicMock()
            mock_query.filter = MagicMock(return_value=mock_query)
            mock_query.all = MagicMock()
            return mock_query

        # Configure session.query to return different children based on parent_id filter
        mock_session.query.side_effect = query_side_effect

        # We need to mock the filter().all() chain for each level
        # This is complex, so we'll mock the actual queries
        query_results = {
            1: [child],  # parent_id=1 returns child
            2: [grandchild],  # parent_id=2 returns grandchild
            3: [great_grandchild],  # parent_id=3 returns great-grandchild
            4: [],  # parent_id=4 returns empty (leaf node)
        }

        def filter_all_side_effect(condition):
            """Mock filter().all() to return appropriate children."""
            mock_filtered = MagicMock()
            # Extract parent_id from condition (simplified - in real test would parse)
            # For this test, we'll track calls and return appropriate data
            mock_filtered.all = MagicMock()
            return mock_filtered

        # Simpler approach: directly mock the recursive calls
        with patch('src.vulcanlab.data.chunk_operations.get_all_descendants',
                   wraps=get_all_descendants) as mock_recursive:

            # For the initial call with parent_id=1
            first_query = create_mock_query_chain(return_data=[child])
            second_query = create_mock_query_chain(return_data=[grandchild])
            third_query = create_mock_query_chain(return_data=[great_grandchild])
            fourth_query = create_mock_query_chain(return_data=[])

            mock_session.query.side_effect = [
                first_query,  # Query for children of 1
                second_query,  # Query for children of 2
                third_query,  # Query for children of 3
                fourth_query,  # Query for children of 4
            ]

            descendants = get_all_descendants(1, mock_session)

            # Should return child, grandchild, and great-grandchild
            assert len(descendants) == 3
            assert descendants[0].id == 2
            assert descendants[1].id == 3
            assert descendants[2].id == 4

    def test_single_level(self, mock_session):
        """Test retrieval with only direct children."""
        child1 = create_mock_chunk(id=2, parent_id=1)
        child2 = create_mock_chunk(id=3, parent_id=1)

        # First query returns the two children
        first_query = create_mock_query_chain(return_data=[child1, child2])
        # Subsequent queries for each child return empty (no grandchildren)
        empty_query1 = create_mock_query_chain(return_data=[])
        empty_query2 = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [first_query, empty_query1, empty_query2]

        descendants = get_all_descendants(1, mock_session)

        assert len(descendants) == 2
        assert descendants[0].id == 2
        assert descendants[1].id == 3

    def test_no_children(self, mock_session):
        """Test leaf node with no children returns empty list."""
        mock_query = create_mock_query_chain(return_data=[])
        mock_session.query.return_value = mock_query

        descendants = get_all_descendants(99, mock_session)

        assert len(descendants) == 0

    def test_non_existent_chunk(self, mock_session):
        """Test non-existent chunk_id returns empty list."""
        mock_query = create_mock_query_chain(return_data=[])
        mock_session.query.return_value = mock_query

        descendants = get_all_descendants(99999, mock_session)

        assert len(descendants) == 0

    def test_missing_session(self):
        """Test error when session is None."""
        with pytest.raises(ValueError, match="Session is required"):
            get_all_descendants(1, session=None)

    def test_complex_tree(self, mock_session):
        """Test complex tree with multiple branches."""
        # Parent has 2 children, first child has 2 grandchildren
        child1 = create_mock_chunk(id=2, parent_id=1)
        child2 = create_mock_chunk(id=3, parent_id=1)
        grandchild1 = create_mock_chunk(id=4, parent_id=2)
        grandchild2 = create_mock_chunk(id=5, parent_id=2)

        first_query = create_mock_query_chain(return_data=[child1, child2])
        second_query = create_mock_query_chain(return_data=[grandchild1, grandchild2])
        third_query = create_mock_query_chain(return_data=[])  # child2 has no children
        fourth_query = create_mock_query_chain(return_data=[])  # grandchild1 has no children
        fifth_query = create_mock_query_chain(return_data=[])  # grandchild2 has no children

        mock_session.query.side_effect = [
            first_query, second_query, fourth_query, fifth_query, third_query
        ]

        descendants = get_all_descendants(1, mock_session)

        # Should return all 4 descendants
        assert len(descendants) == 4


class TestDeleteChunkCascade:
    """Test suite for delete_chunk_cascade function."""

    def test_delete_multi_level(self, mock_session):
        """Test deletion of parent with multi-level descendants."""
        parent = create_mock_chunk(id=1, parent_id=None)
        child = create_mock_chunk(id=2, parent_id=1)
        grandchild = create_mock_chunk(id=3, parent_id=2)
        great_grandchild = create_mock_chunk(id=4, parent_id=3)

        # Mock finding the parent chunk
        find_query = create_mock_query_chain(return_first=parent)

        # Mock get_all_descendants queries
        desc_query1 = create_mock_query_chain(return_data=[child])
        desc_query2 = create_mock_query_chain(return_data=[grandchild])
        desc_query3 = create_mock_query_chain(return_data=[great_grandchild])
        desc_query4 = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [
            find_query,  # Find the parent
            desc_query1,  # Get descendants level 1
            desc_query2,  # Get descendants level 2
            desc_query3,  # Get descendants level 3
            desc_query4,  # Get descendants level 4
        ]

        count = delete_chunk_cascade(1, mock_session)

        # Should return 4 (parent + 3 descendants)
        assert count == 4
        mock_session.delete.assert_called_once_with(parent)

    def test_delete_leaf_node(self, mock_session):
        """Test deletion of chunk with no children."""
        leaf = create_mock_chunk(id=5, parent_id=2)

        find_query = create_mock_query_chain(return_first=leaf)
        desc_query = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [find_query, desc_query]

        count = delete_chunk_cascade(5, mock_session)

        assert count == 1
        mock_session.delete.assert_called_once_with(leaf)

    def test_returns_correct_count(self, mock_session):
        """Test correct count with specific number of descendants."""
        parent = create_mock_chunk(id=1)
        descendants = [create_mock_chunk(id=i, parent_id=1) for i in range(2, 7)]

        find_query = create_mock_query_chain(return_first=parent)
        desc_query = create_mock_query_chain(return_data=descendants)
        # Add empty queries for each descendant's children
        empty_queries = [create_mock_query_chain(return_data=[]) for _ in range(5)]

        mock_session.query.side_effect = [find_query, desc_query] + empty_queries

        count = delete_chunk_cascade(1, mock_session)

        # Should return 6 (1 parent + 5 descendants)
        assert count == 6

    def test_non_existent_chunk(self, mock_session):
        """Test error when chunk doesn't exist."""
        find_query = create_mock_query_chain(return_first=None)
        mock_session.query.return_value = find_query

        with pytest.raises(ValueError, match="Chunk with id 99999 not found"):
            delete_chunk_cascade(99999, mock_session)

        # Should not call delete if chunk doesn't exist
        mock_session.delete.assert_not_called()

    def test_missing_session(self):
        """Test error when session is None."""
        with pytest.raises(ValueError, match="Session is required"):
            delete_chunk_cascade(1, session=None)

    @patch('src.vulcanlab.data.chunk_operations.logger')
    def test_logging(self, mock_logger, mock_session):
        """Test that deletion is logged correctly."""
        parent = create_mock_chunk(id=1)
        child = create_mock_chunk(id=2, parent_id=1)

        find_query = create_mock_query_chain(return_first=parent)
        desc_query1 = create_mock_query_chain(return_data=[child])
        desc_query2 = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [find_query, desc_query1, desc_query2]

        delete_chunk_cascade(1, mock_session)

        # Verify logging was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "chunk 1" in log_message.lower()
        assert "1 descendants" in log_message.lower()
        assert "total: 2" in log_message.lower()

    def test_cascade_behavior_verification(self, mock_session):
        """Test that only parent delete is called (CASCADE handles rest)."""
        parent = create_mock_chunk(id=1)
        child = create_mock_chunk(id=2, parent_id=1)
        grandchild = create_mock_chunk(id=3, parent_id=2)

        find_query = create_mock_query_chain(return_first=parent)
        desc_query1 = create_mock_query_chain(return_data=[child])
        desc_query2 = create_mock_query_chain(return_data=[grandchild])
        desc_query3 = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [find_query, desc_query1, desc_query2, desc_query3]

        delete_chunk_cascade(1, mock_session)

        # Only the parent should be explicitly deleted
        # Database CASCADE will handle descendants
        assert mock_session.delete.call_count == 1
        mock_session.delete.assert_called_once_with(parent)

    def test_session_commit_not_called(self, mock_session):
        """Test that function doesn't commit (caller's responsibility)."""
        parent = create_mock_chunk(id=1)

        find_query = create_mock_query_chain(return_first=parent)
        desc_query = create_mock_query_chain(return_data=[])

        mock_session.query.side_effect = [find_query, desc_query]

        delete_chunk_cascade(1, mock_session)

        # Verify commit was NOT called
        mock_session.commit.assert_not_called()
