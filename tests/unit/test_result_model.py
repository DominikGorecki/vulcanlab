"""
Unit tests for Result model.

Tests model creation, field validation, and basic logic.
Database-specific tests (CASCADE, constraints, timestamps) moved to integration tests.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from vulcanlab.data.models.result import Result
from vulcanlab.data.models.query import Query


class TestResultCreation:
    """Test basic model creation and field values."""

    def test_create_result(self):
        """Test creating a Result instance."""
        result = Result(
            query_id=1,
            response_text="Cognitive psychology is the study of mental processes..."
        )

        assert result.query_id == 1
        assert result.response_text == "Cognitive psychology is the study of mental processes..."

    def test_repr(self):
        """Test __repr__ method."""
        result = Result(
            query_id=1,
            response_text="This is a test response that is longer than 50 characters to test truncation"
        )
        result.id = 1  # Simulate database-assigned ID

        repr_str = repr(result)
        assert "Result" in repr_str
        assert "1" in repr_str
        assert "..." in repr_str  # Should truncate long responses

    def test_repr_short_response(self):
        """Test __repr__ with short response (no truncation)."""
        result = Result(
            query_id=1,
            response_text="Short response"
        )
        result.id = 1

        repr_str = repr(result)
        assert "Short response" in repr_str
        assert "..." not in repr_str


class TestResultRelationships:
    """Test relationships with Query model."""

    def test_result_has_query_id(self):
        """Test that Result has query_id attribute."""
        result = Result(
            query_id=5,
            response_text="Memory is the process of encoding, storing, and retrieving information."
        )

        assert result.query_id == 5

    def test_multiple_results_same_query(self):
        """Test that multiple Results can reference the same query_id."""
        query_id = 10

        result1 = Result(
            query_id=query_id,
            response_text="First response about attention."
        )
        result2 = Result(
            query_id=query_id,
            response_text="Second response about attention."
        )
        result3 = Result(
            query_id=query_id,
            response_text="Third response about attention."
        )

        assert result1.query_id == query_id
        assert result2.query_id == query_id
        assert result3.query_id == query_id


class TestResultCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_result(self, mock_get_session):
        """Test creating a Result."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            result = Result(
                query_id=1,
                response_text="Created response"
            )
            session.add(result)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()
            assert result.response_text == "Created response"

    @patch('vulcanlab.data.database.get_session')
    def test_update_result(self, mock_get_session):
        """Test updating a Result."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            result = Result(
                query_id=1,
                response_text="Original response"
            )
            result.id = 1

            # Update response_text
            result.response_text = "Updated response"
            session.commit()

            assert result.response_text == "Updated response"
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_delete_result(self, mock_get_session):
        """Test deleting a Result."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            result = Result(
                query_id=1,
                response_text="Response to delete"
            )
            result.id = 1

            session.delete(result)
            session.commit()

            session.delete.assert_called_once_with(result)
            session.commit.assert_called_once()

    def test_result_attributes_independent(self):
        """Test that result attributes can be set independently."""
        result1 = Result(
            query_id=1,
            response_text="Response 1"
        )
        result2 = Result(
            query_id=1,
            response_text="Response 2"
        )
        result3 = Result(
            query_id=2,
            response_text="Response 3"
        )

        assert result1.query_id == 1
        assert result2.query_id == 1
        assert result3.query_id == 2
        assert result1.response_text == "Response 1"
        assert result2.response_text == "Response 2"
        assert result3.response_text == "Response 3"


class TestResultTimestamps:
    """Test timestamp fields."""

    def test_timestamps_can_be_set(self):
        """Test that timestamps can be set explicitly."""
        now = datetime.now()
        result = Result(
            query_id=1,
            response_text="Test response",
            created_at=now,
            updated_at=now
        )

        assert result.created_at == now
        assert result.updated_at == now

    def test_result_tablename(self):
        """Test that Result uses correct table name."""
        assert Result.__tablename__ == "results"


# NOTE: The following tests have been moved to integration tests as they require
# a real database to test database-level behavior. See documentation/integration-tests-needed.md
#
# Removed tests (now in integration tests):
# - test_cascade_delete - Tests CASCADE DELETE from Query to Results
# - test_query_id_required - Tests NOT NULL constraint on query_id
# - test_response_text_required - Tests NOT NULL constraint on response_text
# - test_foreign_key_constraint - Tests FK constraint to Query table
# - test_read_result - Tests actual database query/retrieval
# - test_query_by_query_id - Tests database filtering by query_id
# - test_timestamps_auto_populate - Tests server-side timestamp generation
# - test_multiple_results_different_timestamps - Tests database timestamp ordering
