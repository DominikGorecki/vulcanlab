"""
Unit tests for evaluation statistics computation.

Tests statistical analysis including unblinding, aggregations, and Wilcoxon tests.
"""

import pytest
from unittest.mock import Mock
from dataclasses import dataclass

from vulcanlab.eval.statistics import compute_experiment_statistics


@dataclass
class MockRow:
    """Mock query result row."""

    id: int
    prompt_id: int
    unblinded_score: int


class TestComputeExperimentStatistics:
    """Test experiment statistics computation."""

    def test_no_evaluations(self):
        """Test statistics with zero evaluations."""
        session = Mock()
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            []
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 0
        assert stats["x_win_rate"] == 0.0
        assert stats["mean_score"] == 0.0
        assert stats["median_score"] == 0.0
        assert stats["tie_percentage"] == 0.0
        assert stats["harm_rate"] == 0.0
        assert stats["wilcoxon_p_value"] is None

    def test_single_evaluation_positive(self):
        """Test statistics with one positive evaluation."""
        session = Mock()
        mock_results = [MockRow(id=1, prompt_id=1, unblinded_score=5)]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 1
        assert stats["x_win_rate"] == 100.0
        assert stats["mean_score"] == 5.0
        assert stats["median_score"] == 5.0
        assert stats["tie_percentage"] == 0.0
        assert stats["harm_rate"] == 0.0
        assert stats["wilcoxon_p_value"] is None  # Not computed for N=1

    def test_all_ties(self):
        """Test statistics when all scores are zero."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=0),
            MockRow(id=2, prompt_id=2, unblinded_score=0),
            MockRow(id=3, prompt_id=3, unblinded_score=0),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 3
        assert stats["x_win_rate"] == 0.0
        assert stats["mean_score"] == 0.0
        assert stats["median_score"] == 0.0
        assert stats["tie_percentage"] == 100.0
        assert stats["harm_rate"] == 0.0
        assert stats["wilcoxon_p_value"] is not None  # Computed for N>1

    def test_mixed_scores(self):
        """Test statistics with mixed positive, negative, and zero scores."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=8),
            MockRow(id=2, prompt_id=2, unblinded_score=-5),
            MockRow(id=3, prompt_id=3, unblinded_score=0),
            MockRow(id=4, prompt_id=4, unblinded_score=3),
            MockRow(id=5, prompt_id=5, unblinded_score=-2),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 5
        assert stats["x_win_rate"] == 40.0  # 2/5 wins
        assert stats["mean_score"] == 0.8  # (8-5+0+3-2)/5 = 4/5
        assert stats["median_score"] == 0.0  # Middle value
        assert stats["tie_percentage"] == 20.0  # 1/5 ties
        assert stats["harm_rate"] == 40.0  # 2/5 losses
        assert stats["wilcoxon_p_value"] is not None

    def test_all_positive_scores(self):
        """Test statistics when all scores are positive (X wins all)."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=10),
            MockRow(id=2, prompt_id=2, unblinded_score=7),
            MockRow(id=3, prompt_id=3, unblinded_score=5),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 3
        assert stats["x_win_rate"] == 100.0
        assert stats["mean_score"] == pytest.approx(7.33, rel=0.01)
        assert stats["median_score"] == 7.0
        assert stats["tie_percentage"] == 0.0
        assert stats["harm_rate"] == 0.0

    def test_all_negative_scores(self):
        """Test statistics when all scores are negative (Y wins all)."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=-10),
            MockRow(id=2, prompt_id=2, unblinded_score=-7),
            MockRow(id=3, prompt_id=3, unblinded_score=-5),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 3
        assert stats["x_win_rate"] == 0.0
        assert stats["mean_score"] == pytest.approx(-7.33, rel=0.01)
        assert stats["median_score"] == -7.0
        assert stats["tie_percentage"] == 0.0
        assert stats["harm_rate"] == 100.0

    def test_rounding_precision(self):
        """Test that statistics are rounded to correct precision."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=1),
            MockRow(id=2, prompt_id=2, unblinded_score=2),
            MockRow(id=3, prompt_id=3, unblinded_score=3),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        # Check that values are rounded to 2 decimal places
        assert stats["mean_score"] == 2.0
        assert stats["x_win_rate"] == 100.0
        assert stats["tie_percentage"] == 0.0
        assert stats["harm_rate"] == 0.0
        # Wilcoxon p-value should be rounded to 4 decimal places
        assert stats["wilcoxon_p_value"] is not None
        # Should be a float with at most 4 decimal places
        if stats["wilcoxon_p_value"] is not None:
            assert isinstance(stats["wilcoxon_p_value"], float)


class TestWilcoxonComputation:
    """Test Wilcoxon signed-rank test computation."""

    def test_wilcoxon_significant_difference(self):
        """Test Wilcoxon when scores significantly differ from zero."""
        session = Mock()
        # All positive scores should give low p-value
        mock_results = [
            MockRow(id=i, prompt_id=i, unblinded_score=5 + i)
            for i in range(1, 11)
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["wilcoxon_p_value"] is not None
        assert stats["wilcoxon_p_value"] < 0.05  # Significant

    def test_wilcoxon_symmetric_scores(self):
        """Test Wilcoxon when scores are symmetric around zero."""
        session = Mock()
        # Symmetric scores should give high p-value
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=5),
            MockRow(id=2, prompt_id=2, unblinded_score=-5),
            MockRow(id=3, prompt_id=3, unblinded_score=3),
            MockRow(id=4, prompt_id=4, unblinded_score=-3),
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["wilcoxon_p_value"] is not None
        # Note: Exact p-value depends on scipy implementation
        # For symmetric data, p-value should be relatively high
        assert stats["wilcoxon_p_value"] > 0.05

    def test_wilcoxon_not_computed_for_single_eval(self):
        """Test that Wilcoxon is not computed when N=1."""
        session = Mock()
        mock_results = [MockRow(id=1, prompt_id=1, unblinded_score=10)]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["wilcoxon_p_value"] is None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_number_of_evaluations(self):
        """Test statistics computation with many evaluations."""
        session = Mock()
        # Create 100 evaluations with random-ish scores
        mock_results = [
            MockRow(id=i, prompt_id=i % 20, unblinded_score=(i % 20) - 10)
            for i in range(100)
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 100
        assert 0 <= stats["x_win_rate"] <= 100
        assert 0 <= stats["tie_percentage"] <= 100
        assert 0 <= stats["harm_rate"] <= 100
        # Percentages should sum to 100
        assert (
            abs(
                stats["x_win_rate"] + stats["tie_percentage"] + stats["harm_rate"]
                - 100.0
            )
            < 0.01
        )

    def test_extreme_scores(self):
        """Test statistics with extreme scores at boundaries."""
        session = Mock()
        mock_results = [
            MockRow(id=1, prompt_id=1, unblinded_score=10),  # Max score
            MockRow(id=2, prompt_id=2, unblinded_score=-10),  # Min score
            MockRow(id=3, prompt_id=3, unblinded_score=0),  # Tie
        ]
        session.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = (
            mock_results
        )

        stats = compute_experiment_statistics(session, 1)

        assert stats["eval_count"] == 3
        assert stats["mean_score"] == 0.0  # (10 - 10 + 0) / 3
        assert stats["median_score"] == 0.0
        assert stats["x_win_rate"] == pytest.approx(33.33, rel=0.01)
        assert stats["tie_percentage"] == pytest.approx(33.33, rel=0.01)
        assert stats["harm_rate"] == pytest.approx(33.33, rel=0.01)
