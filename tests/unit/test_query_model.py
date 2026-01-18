"""
Unit tests for Query model.

Tests model creation, vector embeddings, JSON fields, and basic logic.
Database-specific tests (constraints) moved to integration tests.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from vulcanlab.data.models.query import Query


class TestQueryCreation:
    """Test basic model creation and field values."""

    def test_create_query_basic(self):
        """Test creating a Query with basic fields."""
        query = Query(
            original_query="What is cognitive psychology?",
            vector_status="no_vec"
        )

        assert query.original_query == "What is cognitive psychology?"
        assert query.vector_status == "no_vec"
        assert query.expanded_queries is None
        assert query.hyde_answer is None
        assert query.intent is None
        assert query.entities is None
        assert query.embedding_original is None
        assert query.embeddings_mqe is None
        assert query.embedding_hyde is None
        assert query.retrieved_context is None
        assert query.clean_retrieval_context is None

    def test_create_query_with_all_fields(self):
        """Test creating a Query with all optional fields."""
        query = Query(
            original_query="What is memory?",
            expanded_queries=["What is memory?", "How does memory work?", "Memory processes"],
            hyde_answer="Memory is the process of encoding, storing, and retrieving information.",
            intent="DEFINITION",
            entities=["memory", "encoding", "retrieval"],
            vector_status="vec",
            retrieved_context=[{"chunk_id": 1, "score": 0.95}],
            clean_retrieval_context=[{"chunk_id": 1, "content": "Memory content"}]
        )

        assert query.expanded_queries == ["What is memory?", "How does memory work?", "Memory processes"]
        assert query.hyde_answer == "Memory is the process of encoding, storing, and retrieving information."
        assert query.intent == "DEFINITION"
        assert query.entities == ["memory", "encoding", "retrieval"]
        assert query.retrieved_context == [{"chunk_id": 1, "score": 0.95}]
        assert query.clean_retrieval_context == [{"chunk_id": 1, "content": "Memory content"}]

    def test_repr(self):
        """Test __repr__ method."""
        query = Query(
            original_query="This is a very long query that exceeds fifty characters to test truncation",
            vector_status="no_vec"
        )
        query.id = 1  # Simulate database-assigned ID

        repr_str = repr(query)
        assert "Query" in repr_str
        assert "1" in repr_str
        assert "..." in repr_str  # Should truncate long queries

    def test_repr_short_query(self):
        """Test __repr__ with short query (no truncation)."""
        query = Query(
            original_query="Short query",
            vector_status="no_vec"
        )
        query.id = 1

        repr_str = repr(query)
        assert "Short query" in repr_str
        assert "..." not in repr_str


class TestQueryVectorFields:
    """Test vector embedding fields."""

    def test_embedding_fields_nullable(self):
        """Test that embedding fields can be None."""
        query = Query(
            original_query="Test query",
            vector_status="no_vec"
        )

        assert query.embedding_original is None
        assert query.embeddings_mqe is None
        assert query.embedding_hyde is None

    def test_embedding_original_can_be_set(self):
        """Test that embedding_original can be set to a list."""
        embedding = [0.1] * 1536
        query = Query(
            original_query="Test query",
            vector_status="vec",
            embedding_original=embedding
        )

        assert query.embedding_original == embedding
        assert len(query.embedding_original) == 1536

    def test_embedding_hyde_can_be_set(self):
        """Test that embedding_hyde can be set to a list."""
        embedding = [0.2] * 1536
        query = Query(
            original_query="Test query",
            vector_status="vec",
            embedding_hyde=embedding
        )

        assert query.embedding_hyde == embedding
        assert len(query.embedding_hyde) == 1536

    def test_vector_status_values(self):
        """Test different vector_status values."""
        statuses = ["no_vec", "to_vec", "vec", "vec_err"]

        for status in statuses:
            query = Query(
                original_query=f"Query with status {status}",
                vector_status=status
            )
            assert query.vector_status == status


class TestQueryJSONFields:
    """Test JSON fields (expanded_queries, entities, embeddings_mqe, contexts)."""

    def test_expanded_queries_as_list(self):
        """Test expanded_queries field as list."""
        expanded = ["Query 1", "Query 2", "Query 3"]
        query = Query(
            original_query="Original",
            vector_status="no_vec",
            expanded_queries=expanded
        )

        assert query.expanded_queries == expanded
        assert isinstance(query.expanded_queries, list)
        assert len(query.expanded_queries) == 3

    def test_entities_as_list(self):
        """Test entities field as list."""
        entities = ["entity1", "entity2", "entity3"]
        query = Query(
            original_query="Test query",
            vector_status="no_vec",
            entities=entities
        )

        assert query.entities == entities
        assert isinstance(query.entities, list)
        assert len(query.entities) == 3

    def test_embeddings_mqe_as_list_of_lists(self):
        """Test embeddings_mqe field as list of embeddings."""
        embeddings_mqe = [
            [0.1] * 1536,
            [0.2] * 1536,
            [0.3] * 1536
        ]
        query = Query(
            original_query="Test query",
            vector_status="vec",
            embeddings_mqe=embeddings_mqe
        )

        assert query.embeddings_mqe == embeddings_mqe
        assert isinstance(query.embeddings_mqe, list)
        assert len(query.embeddings_mqe) == 3
        assert len(query.embeddings_mqe[0]) == 1536

    def test_retrieved_context_as_list_of_dicts(self):
        """Test retrieved_context field as list of dicts."""
        context = [
            {"chunk_id": 1, "score": 0.95, "content": "Content 1"},
            {"chunk_id": 2, "score": 0.88, "content": "Content 2"}
        ]
        query = Query(
            original_query="Test query",
            vector_status="no_vec",
            retrieved_context=context
        )

        assert query.retrieved_context == context
        assert len(query.retrieved_context) == 2
        assert query.retrieved_context[0]["chunk_id"] == 1

    def test_clean_retrieval_context_as_list_of_dicts(self):
        """Test clean_retrieval_context field as list of dicts."""
        context = [
            {"chunk_id": 1, "content": "Clean content 1"},
            {"chunk_id": 2, "content": "Clean content 2"}
        ]
        query = Query(
            original_query="Test query",
            vector_status="no_vec",
            clean_retrieval_context=context
        )

        assert query.clean_retrieval_context == context
        assert len(query.clean_retrieval_context) == 2


class TestQueryCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_query(self, mock_get_session):
        """Test creating a Query."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            query = Query(
                original_query="New query",
                vector_status="no_vec"
            )
            session.add(query)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()
            assert query.original_query == "New query"

    @patch('vulcanlab.data.database.get_session')
    def test_update_query(self, mock_get_session):
        """Test updating a Query."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            query = Query(
                original_query="Original query",
                vector_status="no_vec"
            )
            query.id = 1

            # Update fields
            query.vector_status = "vec"
            query.intent = "DEFINITION"
            query.embedding_original = [0.1] * 1536
            session.commit()

            assert query.vector_status == "vec"
            assert query.intent == "DEFINITION"
            assert query.embedding_original == [0.1] * 1536
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_delete_query(self, mock_get_session):
        """Test deleting a Query."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            query = Query(
                original_query="Query to delete",
                vector_status="no_vec"
            )
            query.id = 1

            session.delete(query)
            session.commit()

            session.delete.assert_called_once_with(query)
            session.commit.assert_called_once()

    def test_query_attributes_independent(self):
        """Test that query attributes can be set independently."""
        query1 = Query(
            original_query="Query 1",
            vector_status="no_vec",
            intent="DEFINITION"
        )
        query2 = Query(
            original_query="Query 2",
            vector_status="vec",
            intent="COMPARISON"
        )

        assert query1.original_query == "Query 1"
        assert query2.original_query == "Query 2"
        assert query1.intent == "DEFINITION"
        assert query2.intent == "COMPARISON"


class TestQueryTimestamps:
    """Test timestamp fields."""

    def test_timestamps_can_be_set(self):
        """Test that timestamps can be set explicitly."""
        now = datetime.now()
        query = Query(
            original_query="Test query",
            vector_status="no_vec",
            created_at=now,
            updated_at=now
        )

        assert query.created_at == now
        assert query.updated_at == now

    def test_query_tablename(self):
        """Test that Query uses correct table name."""
        assert Query.__tablename__ == "queries"


# NOTE: The following tests have been moved to integration tests as they require
# a real database to test database-level behavior. See documentation/integration-tests-needed.md
#
# Removed tests (now in integration tests):
# - test_original_query_required - Tests NOT NULL constraint on original_query
# - test_vector_status_required - Tests NOT NULL constraint with default value
# - Tests for database-level timestamp auto-generation (created_at, updated_at)
# - Tests for actual database query/retrieval operations
# - Tests for database filtering and ordering
