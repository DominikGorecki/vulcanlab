"""
Unit tests for evaluation JSON validation.

Tests the Pydantic schema validation for evaluation submission requests.
"""

import pytest
from pydantic import ValidationError

from vulcanlab_api.schemas.eval import EvaluationSubmitRequest


class TestEvaluationSubmitValidation:
    """Test validation of evaluation submission requests."""

    def test_valid_evaluation_minimal(self):
        """Test valid evaluation with minimal data."""
        data = {
            "overall_score": 0,
            "dimension_scores": {"clarity": 5}
        }

        request = EvaluationSubmitRequest(**data)

        assert request.overall_score == 0
        assert request.justification is None
        assert request.dimension_scores == {"clarity": 5}

    def test_valid_evaluation_full(self):
        """Test valid evaluation with all fields."""
        data = {
            "overall_score": 7,
            "justification": "Answer A is more complete and accurate.",
            "dimension_scores": {
                "factual_correctness": 8,
                "completeness": 7,
                "clarity": 6
            }
        }

        request = EvaluationSubmitRequest(**data)

        assert request.overall_score == 7
        assert request.justification == "Answer A is more complete and accurate."
        assert len(request.dimension_scores) == 3

    def test_overall_score_boundaries(self):
        """Test valid overall score boundaries."""
        # Test -10 (minimum)
        data = {
            "overall_score": -10,
            "dimension_scores": {"clarity": 5}
        }
        request = EvaluationSubmitRequest(**data)
        assert request.overall_score == -10

        # Test 10 (maximum)
        data = {
            "overall_score": 10,
            "dimension_scores": {"clarity": 5}
        }
        request = EvaluationSubmitRequest(**data)
        assert request.overall_score == 10

        # Test 0 (midpoint)
        data = {
            "overall_score": 0,
            "dimension_scores": {"clarity": 5}
        }
        request = EvaluationSubmitRequest(**data)
        assert request.overall_score == 0

    def test_overall_score_too_low(self):
        """Test that overall score < -10 raises validation error."""
        data = {
            "overall_score": -11,
            "dimension_scores": {"clarity": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("overall_score" in str(error) for error in errors)

    def test_overall_score_too_high(self):
        """Test that overall score > 10 raises validation error."""
        data = {
            "overall_score": 11,
            "dimension_scores": {"clarity": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("overall_score" in str(error) for error in errors)

    def test_dimension_score_too_low(self):
        """Test that dimension score < -10 raises validation error."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"clarity": -11}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in str(error) for error in errors)

    def test_dimension_score_too_high(self):
        """Test that dimension score > 10 raises validation error."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"clarity": 11}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in str(error) for error in errors)

    def test_empty_dimension_name(self):
        """Test that empty dimension name raises validation error."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in str(error) for error in errors)

    def test_dimension_score_not_integer(self):
        """Test that non-integer dimension score raises validation error."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"clarity": "five"}
        }

        with pytest.raises(ValidationError):
            EvaluationSubmitRequest(**data)

    def test_dimension_score_float_not_allowed(self):
        """Test that float dimension scores with fractional parts are not allowed."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"clarity": 5.5}
        }

        # Pydantic will reject floats with fractional parts
        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in error.get("loc", []) for error in errors)

    def test_missing_overall_score(self):
        """Test that missing overall_score raises validation error."""
        data = {
            "dimension_scores": {"clarity": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("overall_score" in error.get("loc", []) for error in errors)

    def test_missing_dimension_scores(self):
        """Test that missing dimension_scores raises validation error."""
        data = {
            "overall_score": 5
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in error.get("loc", []) for error in errors)

    def test_empty_dimension_scores_dict(self):
        """Test that empty dimension_scores dict is valid."""
        data = {
            "overall_score": 5,
            "dimension_scores": {}
        }

        # Should be valid - dimensions are optional for T04
        request = EvaluationSubmitRequest(**data)
        assert request.dimension_scores == {}

    def test_justification_too_long(self):
        """Test that justification > 10000 chars raises validation error."""
        data = {
            "overall_score": 5,
            "justification": "x" * 10001,
            "dimension_scores": {"clarity": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("justification" in error.get("loc", []) for error in errors)

    def test_justification_at_max_length(self):
        """Test that justification at exactly 10000 chars is valid."""
        data = {
            "overall_score": 5,
            "justification": "x" * 10000,
            "dimension_scores": {"clarity": 5}
        }

        request = EvaluationSubmitRequest(**data)
        assert len(request.justification) == 10000

    def test_justification_null(self):
        """Test that null justification is valid."""
        data = {
            "overall_score": 5,
            "justification": None,
            "dimension_scores": {"clarity": 5}
        }

        request = EvaluationSubmitRequest(**data)
        assert request.justification is None

    def test_multiple_dimensions(self):
        """Test evaluation with multiple dimension scores."""
        data = {
            "overall_score": 3,
            "justification": "Mixed results",
            "dimension_scores": {
                "factual_correctness": 8,
                "completeness": 6,
                "clarity": 5,
                "coherence": 7,
                "hallucination_risk": -2
            }
        }

        request = EvaluationSubmitRequest(**data)
        assert len(request.dimension_scores) == 5
        assert request.dimension_scores["hallucination_risk"] == -2

    def test_whitespace_dimension_name(self):
        """Test that whitespace-only dimension name raises validation error."""
        data = {
            "overall_score": 5,
            "dimension_scores": {"   ": 5}
        }

        with pytest.raises(ValidationError) as exc_info:
            EvaluationSubmitRequest(**data)

        errors = exc_info.value.errors()
        assert any("dimension_scores" in str(error) for error in errors)

    def test_valid_dimension_names_with_underscores(self):
        """Test that dimension names with underscores are valid."""
        data = {
            "overall_score": 5,
            "dimension_scores": {
                "factual_correctness": 8,
                "hallucination_risk": -2,
                "academic_response": 5
            }
        }

        request = EvaluationSubmitRequest(**data)
        assert len(request.dimension_scores) == 3

    def test_overall_score_not_number(self):
        """Test that non-numeric overall_score raises validation error."""
        data = {
            "overall_score": "five",
            "dimension_scores": {"clarity": 5}
        }

        with pytest.raises(ValidationError):
            EvaluationSubmitRequest(**data)

    def test_dimension_scores_not_dict(self):
        """Test that dimension_scores must be a dictionary."""
        data = {
            "overall_score": 5,
            "dimension_scores": ["clarity", 5]
        }

        with pytest.raises(ValidationError):
            EvaluationSubmitRequest(**data)
