"""
Unit tests for dimension validation in evaluation submission.

Tests that submit_evaluation() properly validates dimension scores against
experiment configuration.
"""

import pytest
from unittest.mock import Mock, MagicMock

from vulcanlab.eval.evaluations import submit_evaluation
from vulcanlab.data.models.experiment import (
    Experiment,
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentDimension,
)


class TestDimensionValidation:
    """Test dimension score validation during evaluation submission."""

    def setup_method(self):
        """Set up common test fixtures."""
        self.session = Mock()

        # Create mock experiment
        self.experiment = Mock(spec=Experiment)
        self.experiment.id = 1
        self.experiment.name = "Test Experiment"

        # Create mock prompt
        self.prompt = Mock(spec=ExperimentPrompt)
        self.prompt.id = 1
        self.prompt.experiment_id = 1
        self.prompt.experiment = self.experiment
        self.prompt.prompt_text = "Test prompt"

        # Create mock answer
        self.answer = Mock(spec=ExperimentAnswer)
        self.answer.id = 1
        self.answer.prompt_id = 1
        self.answer.prompt = self.prompt
        self.answer.answer_a = "Answer A"
        self.answer.answer_b = "Answer B"
        self.answer.is_x_mapped_to_a = True
        self.answer.evaluation = None  # Not yet evaluated

    def mock_dimensions(self, dimension_names):
        """Helper to mock dimension query results."""
        dimensions = []
        for idx, name in enumerate(dimension_names):
            dim = Mock(spec=ExperimentDimension)
            dim.id = idx + 1
            dim.experiment_id = 1
            dim.dimension_name = name
            dim.display_order = idx
            dimensions.append(dim)

        # Mock the dimension query
        mock_query = Mock()
        self.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = dimensions

        return dimensions

    def test_validation_passes_with_exact_dimensions(self):
        """Test that validation passes when all required dimensions provided."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock dimensions
        self.mock_dimensions([
            "factual_correctness",
            "completeness",
            "coherence"
        ])

        # Mock add and flush
        self.session.add.return_value = None
        self.session.flush.return_value = None

        # Create mock evaluation to return
        mock_eval = Mock()
        mock_eval.id = 1
        mock_eval.dimension_results = []

        # Dimension scores match exactly
        dimension_scores = {
            "factual_correctness": 5,
            "completeness": 3,
            "coherence": 7
        }

        # Should not raise an error
        result = submit_evaluation(
            session=self.session,
            answer_id=1,
            overall_score=5,
            justification="Test",
            dimension_scores=dimension_scores
        )

    def test_validation_fails_with_missing_dimension(self):
        """Test that validation fails when required dimension is missing."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock dimensions - experiment requires 3 dimensions
        self.mock_dimensions([
            "factual_correctness",
            "completeness",
            "coherence"
        ])

        # Dimension scores missing "coherence"
        dimension_scores = {
            "factual_correctness": 5,
            "completeness": 3
        }

        with pytest.raises(ValueError, match="Missing required dimensions"):
            submit_evaluation(
                session=self.session,
                answer_id=1,
                overall_score=5,
                justification="Test",
                dimension_scores=dimension_scores
            )

    def test_validation_allows_extra_dimensions(self):
        """Test that validation allows extra dimensions with warning."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock dimensions
        self.mock_dimensions([
            "factual_correctness",
            "completeness"
        ])

        # Mock add and flush
        self.session.add.return_value = None
        self.session.flush.return_value = None

        # Dimension scores include extra "custom_dimension"
        dimension_scores = {
            "factual_correctness": 5,
            "completeness": 3,
            "custom_dimension": 8  # Extra dimension
        }

        # Should succeed with warning logged (we can't easily test logging here)
        result = submit_evaluation(
            session=self.session,
            answer_id=1,
            overall_score=5,
            justification="Test",
            dimension_scores=dimension_scores
        )

    def test_validation_skipped_when_no_dimensions_configured(self):
        """Test that validation is lenient when experiment has no dimensions."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock NO dimensions for this experiment
        self.mock_dimensions([])

        # Mock add and flush
        self.session.add.return_value = None
        self.session.flush.return_value = None

        # Any dimension scores should be allowed
        dimension_scores = {
            "anything": 5,
            "goes": 3
        }

        # Should succeed with warning logged
        result = submit_evaluation(
            session=self.session,
            answer_id=1,
            overall_score=5,
            justification="Test",
            dimension_scores=dimension_scores
        )

    def test_validation_fails_with_multiple_missing_dimensions(self):
        """Test clear error message when multiple dimensions missing."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock dimensions - 5 core dimensions
        self.mock_dimensions([
            "factual_correctness",
            "completeness",
            "coherence",
            "hallucination_risk",
            "academic_response"
        ])

        # Only provide 2 dimensions
        dimension_scores = {
            "factual_correctness": 5,
            "completeness": 3
        }

        with pytest.raises(ValueError) as exc_info:
            submit_evaluation(
                session=self.session,
                answer_id=1,
                overall_score=5,
                justification="Test",
                dimension_scores=dimension_scores
            )

        error_msg = str(exc_info.value)
        assert "Missing required dimensions" in error_msg
        assert "coherence" in error_msg
        assert "hallucination_risk" in error_msg
        assert "academic_response" in error_msg

    def test_validation_case_sensitive_dimension_names(self):
        """Test that dimension names are case-sensitive in validation."""
        # Mock answer query
        answer_query = Mock()
        self.session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = self.answer

        # Mock dimensions (lowercase)
        self.mock_dimensions([
            "factual_correctness",
            "completeness"
        ])

        # Provide dimensions with wrong case
        dimension_scores = {
            "Factual_Correctness": 5,  # Wrong case
            "Completeness": 3  # Wrong case
        }

        # Should fail - case doesn't match
        with pytest.raises(ValueError, match="Missing required dimensions"):
            submit_evaluation(
                session=self.session,
                answer_id=1,
                overall_score=5,
                justification="Test",
                dimension_scores=dimension_scores
            )


class TestDimensionValidationEdgeCases:
    """Test edge cases in dimension validation."""

    def test_empty_dimension_scores_fails_if_dimensions_required(self):
        """Test that empty dimension scores fail validation."""
        session = Mock()

        # Mock answer
        answer = Mock(spec=ExperimentAnswer)
        answer.id = 1
        prompt = Mock(spec=ExperimentPrompt)
        experiment = Mock(spec=Experiment)
        experiment.id = 1
        prompt.experiment = experiment
        answer.prompt = prompt
        answer.is_x_mapped_to_a = True
        answer.evaluation = None  # Not yet evaluated

        answer_query = Mock()
        session.query.return_value = answer_query
        answer_query.filter.return_value.first.return_value = answer

        # Mock dimensions exist
        dim_query = Mock()
        session.query.return_value = dim_query
        dim_query.filter.return_value = dim_query
        dim_query.order_by.return_value = dim_query

        dimension = Mock(spec=ExperimentDimension)
        dimension.dimension_name = "accuracy"
        dim_query.all.return_value = [dimension]

        # Empty dimension scores
        dimension_scores = {}

        with pytest.raises(ValueError, match="Missing required dimensions"):
            submit_evaluation(
                session=session,
                answer_id=1,
                overall_score=5,
                justification="Test",
                dimension_scores=dimension_scores
            )

    def test_none_dimension_scores_fails(self):
        """Test that None dimension_scores parameter is properly handled."""
        session = Mock()

        # This should fail earlier in the API layer (Pydantic validation)
        # but we test the function handles it gracefully
        with pytest.raises((ValueError, AttributeError, TypeError)):
            submit_evaluation(
                session=session,
                answer_id=1,
                overall_score=5,
                justification="Test",
                dimension_scores=None  # Invalid
            )
