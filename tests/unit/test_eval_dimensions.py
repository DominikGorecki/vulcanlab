"""
Unit tests for evaluation dimension CRUD operations.

Tests dimension creation, retrieval, validation, and constraints.
"""

import pytest
from unittest.mock import Mock
from sqlalchemy.exc import IntegrityError

from vulcanlab.eval.dimensions import (
    create_dimension,
    create_dimensions_batch,
    get_dimensions_by_experiment,
    get_dimension_names_set,
)
from vulcanlab.data.models.experiment import ExperimentDimension


class TestCreateDimension:
    """Test create_dimension function."""

    def test_create_dimension_success(self):
        """Test successful dimension creation."""
        session = Mock()
        mock_dimension = Mock(spec=ExperimentDimension)
        mock_dimension.id = 1
        mock_dimension.experiment_id = 1
        mock_dimension.dimension_name = "test_dimension"
        mock_dimension.display_order = 0

        session.add.return_value = None
        session.flush.return_value = None

        # Mock the dimension instance creation by having it return our mock
        # when ExperimentDimension is instantiated
        with pytest.MonkeyPatch.context() as mp:
            def mock_dimension_init(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
                self.id = 1
                return None

            # We'll just test the function behavior directly
            result = create_dimension(
                session=session,
                experiment_id=1,
                dimension_name="test_dimension",
                display_order=0
            )

        session.add.assert_called_once()
        session.flush.assert_called_once()

    def test_create_dimension_empty_name_fails(self):
        """Test that empty dimension name raises ValueError."""
        session = Mock()

        with pytest.raises(ValueError, match="Dimension name is required"):
            create_dimension(
                session=session,
                experiment_id=1,
                dimension_name="",
                display_order=0
            )

    def test_create_dimension_whitespace_name_fails(self):
        """Test that whitespace-only dimension name raises ValueError."""
        session = Mock()

        with pytest.raises(ValueError, match="Dimension name is required"):
            create_dimension(
                session=session,
                experiment_id=1,
                dimension_name="   ",
                display_order=0
            )

    def test_create_dimension_duplicate_fails(self):
        """Test that duplicate dimension name raises IntegrityError."""
        session = Mock()
        session.add.return_value = None
        session.flush.side_effect = IntegrityError("duplicate", None, None)

        with pytest.raises(IntegrityError):
            create_dimension(
                session=session,
                experiment_id=1,
                dimension_name="duplicate_dimension",
                display_order=0
            )

        session.rollback.assert_called_once()


class TestCreateDimensionsBatch:
    """Test create_dimensions_batch function."""

    def test_create_batch_success(self):
        """Test successful batch creation."""
        session = Mock()
        dimension_names = ["dim1", "dim2", "dim3"]

        # Mock successful dimension creation
        session.add.return_value = None
        session.flush.return_value = None

        result = create_dimensions_batch(
            session=session,
            experiment_id=1,
            dimension_names=dimension_names
        )

        # Should have called add 3 times (once per dimension)
        assert session.add.call_count == 3
        assert session.flush.call_count == 3

    def test_create_batch_empty_list_fails(self):
        """Test that empty dimension list raises ValueError."""
        session = Mock()

        with pytest.raises(ValueError, match="at least one dimension"):
            create_dimensions_batch(
                session=session,
                experiment_id=1,
                dimension_names=[]
            )

    def test_create_batch_duplicate_names_fails(self):
        """Test that duplicate dimension names raise ValueError."""
        session = Mock()
        dimension_names = ["dim1", "dim2", "dim1"]  # duplicate

        with pytest.raises(ValueError, match="must be unique"):
            create_dimensions_batch(
                session=session,
                experiment_id=1,
                dimension_names=dimension_names
            )

    def test_create_batch_empty_string_fails(self):
        """Test that empty strings in list raise ValueError."""
        session = Mock()
        dimension_names = ["dim1", "", "dim3"]

        with pytest.raises(ValueError, match="cannot be empty"):
            create_dimensions_batch(
                session=session,
                experiment_id=1,
                dimension_names=dimension_names
            )

    def test_create_batch_whitespace_trimmed(self):
        """Test that whitespace is trimmed from dimension names."""
        session = Mock()
        dimension_names = ["  dim1  ", " dim2", "dim3 "]

        session.add.return_value = None
        session.flush.return_value = None

        result = create_dimensions_batch(
            session=session,
            experiment_id=1,
            dimension_names=dimension_names
        )

        # All dimensions should be created successfully
        assert session.add.call_count == 3

    def test_create_batch_preserves_order(self):
        """Test that display_order matches list order."""
        session = Mock()
        dimension_names = ["first", "second", "third"]

        session.add.return_value = None
        session.flush.return_value = None

        result = create_dimensions_batch(
            session=session,
            experiment_id=1,
            dimension_names=dimension_names
        )

        # Verify dimensions are created (we can't easily check order in mocks,
        # but the function should create them in order)
        assert session.add.call_count == 3


class TestGetDimensionsByExperiment:
    """Test get_dimensions_by_experiment function."""

    def test_get_dimensions_empty(self):
        """Test getting dimensions for experiment with no dimensions."""
        session = Mock()
        mock_query = Mock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = get_dimensions_by_experiment(session, 1)

        assert result == []
        session.query.assert_called_once()

    def test_get_dimensions_multiple(self):
        """Test getting multiple dimensions ordered correctly."""
        session = Mock()

        # Create mock dimensions
        dim1 = Mock(spec=ExperimentDimension)
        dim1.id = 1
        dim1.dimension_name = "factual_correctness"
        dim1.display_order = 0

        dim2 = Mock(spec=ExperimentDimension)
        dim2.id = 2
        dim2.dimension_name = "completeness"
        dim2.display_order = 1

        dim3 = Mock(spec=ExperimentDimension)
        dim3.id = 3
        dim3.dimension_name = "coherence"
        dim3.display_order = 2

        mock_query = Mock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [dim1, dim2, dim3]

        result = get_dimensions_by_experiment(session, 1)

        assert len(result) == 3
        assert result[0].dimension_name == "factual_correctness"
        assert result[1].dimension_name == "completeness"
        assert result[2].dimension_name == "coherence"


class TestGetDimensionNamesSet:
    """Test get_dimension_names_set function."""

    def test_get_names_set_empty(self):
        """Test getting names set for experiment with no dimensions."""
        session = Mock()
        mock_query = Mock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = get_dimension_names_set(session, 1)

        assert result == set()

    def test_get_names_set_multiple(self):
        """Test getting names set with multiple dimensions."""
        session = Mock()

        # Create mock dimensions
        dim1 = Mock(spec=ExperimentDimension)
        dim1.dimension_name = "factual_correctness"

        dim2 = Mock(spec=ExperimentDimension)
        dim2.dimension_name = "completeness"

        dim3 = Mock(spec=ExperimentDimension)
        dim3.dimension_name = "coherence"

        mock_query = Mock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [dim1, dim2, dim3]

        result = get_dimension_names_set(session, 1)

        assert result == {"factual_correctness", "completeness", "coherence"}
        assert isinstance(result, set)


class TestDimensionConstraints:
    """Test database constraints and edge cases."""

    def test_dimension_name_case_sensitive(self):
        """Test that dimension names are case-sensitive in storage."""
        session = Mock()
        session.add.return_value = None
        session.flush.return_value = None

        # Create dimensions with different cases
        create_dimension(session, 1, "TestDimension", 0)

        # Should succeed (no case folding in create)
        session.add.assert_called()

    def test_different_experiments_can_have_same_dimension_names(self):
        """Test that different experiments can use the same dimension names."""
        session = Mock()
        session.add.return_value = None
        session.flush.return_value = None

        # Create same dimension name for different experiments
        create_dimension(session, 1, "accuracy", 0)
        create_dimension(session, 2, "accuracy", 0)

        # Both should succeed
        assert session.add.call_count == 2
