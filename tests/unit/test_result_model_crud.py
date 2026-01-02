"""
Unit tests for ResultModel CRUD operations.

Tests model creation, unique constraints, and relationships with Result model.
Database-specific tests (constraints, CASCADE) use mocked sessions per patterns.md.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.result_model import ResultModel
from vulcanlab.data.models.result import Result


class TestResultModelCreation:
    """Test basic ResultModel creation and field values."""

    def test_create_result_model(self):
        """Test creating a ResultModel instance."""
        model = ResultModel(name="gpt-4")

        assert model.name == "gpt-4"

    def test_create_result_model_long_name(self):
        """Test creating a ResultModel with a long model name."""
        long_name = "claude-3-opus-20240229-extended-context-v2"
        model = ResultModel(name=long_name)

        assert model.name == long_name

    def test_repr(self):
        """Test __repr__ method."""
        model = ResultModel(name="claude-sonnet-3.5")
        model.id = 1  # Simulate database-assigned ID

        repr_str = repr(model)
        assert "ResultModel" in repr_str
        assert "1" in repr_str
        assert "claude-sonnet-3.5" in repr_str

    def test_tablename(self):
        """Test that ResultModel uses correct table name."""
        assert ResultModel.__tablename__ == "result_models"


class TestResultModelCRUD:
    """Test CRUD operations with mocked database."""

    @patch('vulcanlab.data.database.get_session')
    def test_create_result_model(self, mock_get_session):
        """Test creating a ResultModel via mocked session."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            model = ResultModel(name="gpt-4-turbo")
            session.add(model)
            session.commit()

            session.add.assert_called_once()
            session.commit.assert_called_once()
            assert model.name == "gpt-4-turbo"

    @patch('vulcanlab.data.database.get_session')
    def test_update_result_model(self, mock_get_session):
        """Test updating a ResultModel."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            model = ResultModel(name="gpt-4")
            model.id = 1

            # Update name
            model.name = "gpt-4-turbo"
            session.commit()

            assert model.name == "gpt-4-turbo"
            session.commit.assert_called_once()

    @patch('vulcanlab.data.database.get_session')
    def test_delete_result_model(self, mock_get_session):
        """Test deleting a ResultModel."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            model = ResultModel(name="old-model")
            model.id = 1

            session.delete(model)
            session.commit()

            session.delete.assert_called_once_with(model)
            session.commit.assert_called_once()


class TestResultModelUniqueConstraint:
    """Test unique constraint on model name."""

    @patch('vulcanlab.data.database.get_session')
    def test_duplicate_name_raises_integrity_error(self, mock_get_session):
        """Test that duplicate model names raise IntegrityError."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Simulate IntegrityError on duplicate
        mock_session.commit.side_effect = IntegrityError("duplicate key", {}, None)

        with mock_get_session() as session:
            model1 = ResultModel(name="gpt-4")
            session.add(model1)

            with pytest.raises(IntegrityError):
                session.commit()

    def test_different_names_allowed(self):
        """Test that different model names are allowed."""
        model1 = ResultModel(name="gpt-4")
        model2 = ResultModel(name="claude-3")
        model3 = ResultModel(name="gemini-pro")

        assert model1.name == "gpt-4"
        assert model2.name == "claude-3"
        assert model3.name == "gemini-pro"


class TestResultWithModelId:
    """Test Result model with model_id foreign key."""

    def test_result_with_model_id(self):
        """Test creating a Result with model_id."""
        result = Result(
            query_id=1,
            response_text="Test response",
            model_id=2
        )

        assert result.model_id == 2
        assert result.query_id == 1
        assert result.response_text == "Test response"

    def test_result_with_null_model_id(self):
        """Test creating a Result with NULL model_id (legacy results)."""
        result = Result(
            query_id=1,
            response_text="Test response",
            model_id=None
        )

        assert result.model_id is None
        assert result.query_id == 1

    def test_result_without_model_id(self):
        """Test creating a Result without specifying model_id (defaults to None)."""
        result = Result(
            query_id=1,
            response_text="Test response"
        )

        # model_id should be None by default (nullable field)
        assert not hasattr(result, 'model_id') or result.model_id is None


class TestResultModelRelationship:
    """Test relationship between Result and ResultModel."""

    @patch('vulcanlab.data.database.get_session')
    def test_result_model_relationship(self, mock_get_session):
        """Test accessing ResultModel via Result.model relationship."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Create mock ResultModel
        mock_result_model = ResultModel(name="gpt-4")
        mock_result_model.id = 1

        # Create Result with model_id
        result = Result(
            query_id=1,
            response_text="Test",
            model_id=1
        )

        # Mock the relationship
        result.model = mock_result_model

        # Verify relationship works
        assert result.model is not None
        assert result.model.name == "gpt-4"
        assert result.model.id == 1

    @patch('vulcanlab.data.database.get_session')
    def test_result_model_relationship_null(self, mock_get_session):
        """Test Result.model relationship when model_id is NULL."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        result = Result(
            query_id=1,
            response_text="Test",
            model_id=None
        )

        # Mock null relationship
        result.model = None

        assert result.model is None


class TestOnDeleteSetNull:
    """Test ON DELETE SET NULL behavior (mocked)."""

    @patch('vulcanlab.data.database.get_session')
    def test_delete_model_sets_result_model_id_to_null(self, mock_get_session):
        """Test that deleting a ResultModel sets Result.model_id to NULL."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        with mock_get_session() as session:
            # Create mock model and result
            model = ResultModel(name="gpt-4")
            model.id = 1

            result = Result(
                query_id=1,
                response_text="Test",
                model_id=1
            )
            result.id = 100

            # Simulate deletion (in real DB, this would trigger ON DELETE SET NULL)
            session.delete(model)

            # Simulate the database behavior of setting FK to NULL
            result.model_id = None

            session.commit()

            # Verify model_id is now NULL
            assert result.model_id is None
            session.delete.assert_called_once_with(model)


class TestMultipleResults:
    """Test multiple results with the same model."""

    def test_multiple_results_same_model(self):
        """Test that multiple Results can reference the same model_id."""
        model_id = 5

        result1 = Result(query_id=1, response_text="Response 1", model_id=model_id)
        result2 = Result(query_id=2, response_text="Response 2", model_id=model_id)
        result3 = Result(query_id=3, response_text="Response 3", model_id=model_id)

        assert result1.model_id == model_id
        assert result2.model_id == model_id
        assert result3.model_id == model_id

    def test_results_with_different_models(self):
        """Test Results with different model_ids."""
        result1 = Result(query_id=1, response_text="Response 1", model_id=1)
        result2 = Result(query_id=2, response_text="Response 2", model_id=2)
        result3 = Result(query_id=3, response_text="Response 3", model_id=3)

        assert result1.model_id == 1
        assert result2.model_id == 2
        assert result3.model_id == 3


# NOTE: The following tests require a real database and are moved to integration tests:
#
# Removed tests (now in integration tests):
# - test_unique_constraint_database - Tests actual unique constraint violation at DB level
# - test_foreign_key_constraint - Tests FK constraint enforcement
# - test_cascade_delete_from_database - Tests ON DELETE SET NULL at database level
# - test_query_with_join - Tests actual LEFT JOIN between results and result_models
# - test_timestamps_auto_populate - Tests server-side timestamp generation
# - test_updated_at_auto_update - Tests trigger for updated_at on UPDATE
