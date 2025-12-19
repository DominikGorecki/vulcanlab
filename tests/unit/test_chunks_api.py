"""
Unit tests for chunks API endpoints.

Tests request validation, response formatting, and error handling for:
- GET /api/v1/chunks/search
- GET /api/v1/chunks/{chunk_id}
- GET /api/v1/chunks/{chunk_id}/descendants
- DELETE /api/v1/chunks/{chunk_id}
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from vulcanlab_api.main import app
from tests.unit.mock_helpers import create_mock_chunk

client = TestClient(app)


class TestSearchEndpoint:
    """Test suite for GET /api/v1/chunks/search endpoint."""

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_success(self, mock_search, mock_get_session):
        """Test successful search returns 200 with correct structure."""
        # Mock chunks
        chunks = [
            create_mock_chunk(
                id=1,
                content="This is a test chunk with some content",
                heading_breadcrumbs="Chapter 1 > Introduction",
                level="H2",
                work_id=5,
                start_line=10,
                end_line=20
            ),
            create_mock_chunk(
                id=2,
                content="Another chunk here",
                heading_breadcrumbs="Chapter 2 > Details",
                level="H3",
                work_id=5,
                start_line=25,
                end_line=35
            ),
        ]

        # Mock search function
        mock_search.return_value = (chunks, 50)

        # Mock session context manager
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Make request
        response = client.get("/api/v1/chunks/search?q=test&page=1")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "results" in data
        assert "pagination" in data
        assert len(data["results"]) == 2

        # Verify first result
        assert data["results"][0]["id"] == 1
        assert data["results"][0]["content_preview"] == "This is a test chunk with some content"
        assert data["results"][0]["heading_breadcrumbs"] == "Chapter 1 > Introduction"
        assert data["results"][0]["level"] == "H2"

        # Verify pagination
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 25
        assert data["pagination"]["total_results"] == 50
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_search_empty_query(self, mock_get_session):
        """Test empty query parameter returns 422 (validation error)."""
        # Try with empty string - FastAPI returns 422 for validation errors
        response = client.get("/api/v1/chunks/search?q=&page=1")
        assert response.status_code == 422

        # Try with whitespace only - our explicit validation returns 400
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        response = client.get("/api/v1/chunks/search?q=   &page=1")
        assert response.status_code == 400

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_pagination_has_next(self, mock_search, mock_get_session):
        """Test has_next=True when more results available."""
        # Mock 50 results, page 1 with page_size=25 should have next
        chunks = [create_mock_chunk(id=i) for i in range(1, 26)]
        mock_search.return_value = (chunks, 50)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=test&page=1")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["has_next"] is True

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_pagination_has_prev(self, mock_search, mock_get_session):
        """Test has_prev=True on page 2."""
        chunks = [create_mock_chunk(id=i) for i in range(26, 51)]
        mock_search.return_value = (chunks, 100)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=test&page=2")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["has_prev"] is True

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_pagination_first_page(self, mock_search, mock_get_session):
        """Test has_prev=False on page 1."""
        chunks = [create_mock_chunk(id=i) for i in range(1, 26)]
        mock_search.return_value = (chunks, 50)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=test&page=1")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["has_prev"] is False

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_content_truncation(self, mock_search, mock_get_session):
        """Test content is truncated to 100 characters."""
        long_content = "x" * 200  # 200 characters
        chunks = [create_mock_chunk(id=1, content=long_content)]
        mock_search.return_value = (chunks, 1)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=test&page=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"][0]["content_preview"]) == 100

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_no_results(self, mock_search, mock_get_session):
        """Test empty results returns empty list with total_results=0."""
        mock_search.return_value = ([], 0)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=nonexistent&page=1")

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["pagination"]["total_results"] == 0
        assert data["pagination"]["has_next"] is False

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_default_page(self, mock_search, mock_get_session):
        """Test default page=1 when not specified."""
        chunks = [create_mock_chunk(id=1)]
        mock_search.return_value = (chunks, 1)

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Don't specify page parameter
        response = client.get("/api/v1/chunks/search?q=test")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_search_invalid_page(self, mock_get_session):
        """Test invalid page number returns 422."""
        # Page 0 is invalid (must be >= 1)
        response = client.get("/api/v1/chunks/search?q=test&page=0")
        assert response.status_code == 422

        # Negative page is invalid
        response = client.get("/api/v1/chunks/search?q=test&page=-1")
        assert response.status_code == 422

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.search_chunks_lexical')
    def test_search_sqlalchemy_error(self, mock_search, mock_get_session):
        """Test SQLAlchemy error returns 500."""
        mock_search.side_effect = SQLAlchemyError("Database error")

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/search?q=test&page=1")

        assert response.status_code == 500


class TestGetChunkDetailEndpoint:
    """Test suite for GET /api/v1/chunks/{chunk_id} endpoint."""

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_get_chunk_success(self, mock_get_session):
        """Test successful chunk retrieval returns 200 with full details."""
        # Mock chunk
        chunk = create_mock_chunk(
            id=123,
            content="This is the full content of the chunk without any truncation at all.",
            heading_breadcrumbs="Chapter 1 > Introduction > Overview",
            level="H3",
            work_id=5,
            start_line=42,
            end_line=58
        )

        # Mock session and query
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = chunk
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Make request
        response = client.get("/api/v1/chunks/123")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["id"] == 123
        assert data["content"] == "This is the full content of the chunk without any truncation at all."
        assert data["heading_breadcrumbs"] == "Chapter 1 > Introduction > Overview"
        assert data["level"] == "H3"
        assert data["work_id"] == 5
        assert data["start_line"] == 42
        assert data["end_line"] == 58

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_get_chunk_not_found(self, mock_get_session):
        """Test chunk not found returns 404."""
        # Mock session - no chunk found
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_get_chunk_invalid_id(self, mock_get_session):
        """Test invalid chunk ID returns 422."""
        # Chunk ID must be > 0
        response = client.get("/api/v1/chunks/0")
        assert response.status_code == 422

        response = client.get("/api/v1/chunks/-1")
        assert response.status_code == 422

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_get_chunk_sqlalchemy_error(self, mock_get_session):
        """Test SQLAlchemy error returns 500."""
        # Mock session to raise error
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/123")

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]


class TestDescendantsEndpoint:
    """Test suite for GET /api/v1/chunks/{chunk_id}/descendants endpoint."""

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    def test_descendants_success(self, mock_get_descendants, mock_get_session):
        """Test successful descendants retrieval returns 200."""
        # Mock parent chunk
        parent_chunk = create_mock_chunk(id=1)

        # Mock descendants
        descendants = [
            create_mock_chunk(
                id=2,
                level="H3",
                heading_breadcrumbs="Chapter 1 > Section 1.1"
            ),
            create_mock_chunk(
                id=3,
                level="H4",
                heading_breadcrumbs="Chapter 1 > Section 1.1 > Subsection"
            ),
        ]
        mock_get_descendants.return_value = descendants

        # Mock session
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = parent_chunk
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/1/descendants")

        assert response.status_code == 200
        data = response.json()

        assert "descendants" in data
        assert "total_count" in data
        assert len(data["descendants"]) == 2
        assert data["total_count"] == 2

        # Verify descendant structure
        assert data["descendants"][0]["id"] == 2
        assert data["descendants"][0]["level"] == "H3"
        assert data["descendants"][0]["heading_breadcrumbs"] == "Chapter 1 > Section 1.1"

    @patch('vulcanlab_api.routers.chunks.get_session')
    def test_descendants_chunk_not_found(self, mock_get_session):
        """Test non-existent chunk returns 404."""
        # Mock session with no chunk found
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/99999/descendants")

        assert response.status_code == 404

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    def test_descendants_no_children(self, mock_get_descendants, mock_get_session):
        """Test leaf node with no descendants returns empty list."""
        parent_chunk = create_mock_chunk(id=1)
        mock_get_descendants.return_value = []

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = parent_chunk
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/1/descendants")

        assert response.status_code == 200
        data = response.json()
        assert data["descendants"] == []
        assert data["total_count"] == 0

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    def test_descendants_sqlalchemy_error(self, mock_get_descendants, mock_get_session):
        """Test SQLAlchemy error returns 500."""
        mock_session = MagicMock()
        mock_session.query.side_effect = SQLAlchemyError("Database error")
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.get("/api/v1/chunks/1/descendants")

        assert response.status_code == 500


class TestDeleteEndpoint:
    """Test suite for DELETE /api/v1/chunks/{chunk_id} endpoint."""

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_success(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test successful deletion returns 200 with correct count."""
        # Mock descendants
        descendants = [
            create_mock_chunk(id=2),
            create_mock_chunk(id=3),
        ]
        mock_get_descendants.return_value = descendants

        # Mock delete function
        mock_delete.return_value = 3  # 1 parent + 2 descendants

        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/1")

        assert response.status_code == 200
        data = response.json()

        assert data["deleted_chunk_id"] == 1
        assert data["descendants_deleted"] == [2, 3]
        assert data["total_deleted"] == 3

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_chunk_not_found(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test deleting non-existent chunk returns 404."""
        # Mock ValueError from delete_chunk_cascade
        mock_delete.side_effect = ValueError("Chunk with id 99999 not found")

        mock_get_descendants.return_value = []

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/99999")

        assert response.status_code == 404

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_returns_descendants(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test delete response includes all descendant IDs."""
        # Mock multiple descendants
        descendants = [
            create_mock_chunk(id=i)
            for i in range(2, 7)  # IDs 2, 3, 4, 5, 6
        ]
        mock_get_descendants.return_value = descendants
        mock_delete.return_value = 6  # 1 parent + 5 descendants

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["descendants_deleted"]) == 5
        assert data["descendants_deleted"] == [2, 3, 4, 5, 6]

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_commits_transaction(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test delete endpoint commits transaction."""
        mock_get_descendants.return_value = []
        mock_delete.return_value = 1

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/1")

        assert response.status_code == 200
        # Verify commit was called
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_sqlalchemy_error(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test SQLAlchemy error during deletion returns 500."""
        mock_get_descendants.return_value = []
        mock_delete.side_effect = SQLAlchemyError("Database error")

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/1")

        assert response.status_code == 500

    @patch('vulcanlab_api.routers.chunks.get_session')
    @patch('vulcanlab_api.routers.chunks.get_all_descendants')
    @patch('vulcanlab_api.routers.chunks.delete_chunk_cascade')
    def test_delete_leaf_node(self, mock_delete, mock_get_descendants, mock_get_session):
        """Test deleting chunk with no children."""
        mock_get_descendants.return_value = []
        mock_delete.return_value = 1

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        response = client.delete("/api/v1/chunks/1")

        assert response.status_code == 200
        data = response.json()
        assert data["descendants_deleted"] == []
        assert data["total_deleted"] == 1
