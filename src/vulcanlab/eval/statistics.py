"""
Statistical analysis for evaluation experiments.

Computes aggregate statistics across all evaluations in an experiment,
including win rates, score distributions, and statistical significance tests.
"""

import logging
from typing import Optional
from statistics import mean, median

from sqlalchemy import case
from sqlalchemy.orm import Session
from scipy import stats

from vulcanlab.data.models.experiment import (
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentEvaluation,
)

logger = logging.getLogger(__name__)


def compute_experiment_statistics(
    session: Session,
    experiment_id: int
) -> dict:
    """
    Compute statistical analysis for an experiment.

    Returns dictionary with:
    - eval_count: Total number of evaluations
    - x_win_rate: Percentage where X > Y (score > 0)
    - mean_score: Mean of unblinded scores
    - median_score: Median of unblinded scores
    - tie_percentage: Percentage where score == 0
    - harm_rate: Percentage where X < Y (score < 0)
    - wilcoxon_p_value: Wilcoxon signed-rank test p-value (or None)

    Args:
        session: Database session
        experiment_id: ID of experiment to analyze

    Returns:
        Dictionary of statistics
    """
    # Single query to fetch all evaluations with unblinded scores
    # Uses CASE to unblind: if is_x_mapped_to_a then score else -score
    unblinded_score_expr = case(
        (ExperimentAnswer.is_x_mapped_to_a == True, ExperimentEvaluation.overall_score),
        else_=-ExperimentEvaluation.overall_score
    ).label('unblinded_score')

    results = session.query(
        ExperimentEvaluation.id,
        ExperimentPrompt.id.label('prompt_id'),
        unblinded_score_expr,
    ).join(
        ExperimentAnswer,
        ExperimentEvaluation.answer_id == ExperimentAnswer.id
    ).join(
        ExperimentPrompt,
        ExperimentAnswer.prompt_id == ExperimentPrompt.id
    ).filter(
        ExperimentPrompt.experiment_id == experiment_id
    ).all()

    eval_count = len(results)

    # Edge case: no evaluations
    if eval_count == 0:
        logger.info(f"No evaluations found for experiment {experiment_id}")
        return {
            'eval_count': 0,
            'x_win_rate': 0.0,
            'mean_score': 0.0,
            'median_score': 0.0,
            'tie_percentage': 0.0,
            'harm_rate': 0.0,
            'wilcoxon_p_value': None,
        }

    # Extract unblinded scores
    scores = [row.unblinded_score for row in results]

    # Compute basic statistics
    win_count = sum(1 for s in scores if s > 0)
    tie_count = sum(1 for s in scores if s == 0)
    loss_count = sum(1 for s in scores if s < 0)

    x_win_rate = (win_count / eval_count) * 100
    tie_percentage = (tie_count / eval_count) * 100
    harm_rate = (loss_count / eval_count) * 100

    mean_score_val = mean(scores)
    median_score_val = median(scores)

    # Wilcoxon test: only if we have > 1 evaluation
    wilcoxon_p = None
    if eval_count > 1:
        try:
            # Wilcoxon signed-rank test tests if median differs from 0
            # Alternative is 'two-sided' (default)
            result = stats.wilcoxon(scores, alternative='two-sided')
            wilcoxon_p = result.pvalue
            logger.info(
                f"Wilcoxon test for experiment {experiment_id}: "
                f"statistic={result.statistic}, p={wilcoxon_p}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to compute Wilcoxon for experiment {experiment_id}: {e}"
            )
            wilcoxon_p = None

    stats_dict = {
        'eval_count': eval_count,
        'x_win_rate': round(x_win_rate, 2),
        'mean_score': round(mean_score_val, 2),
        'median_score': round(median_score_val, 2),
        'tie_percentage': round(tie_percentage, 2),
        'harm_rate': round(harm_rate, 2),
        'wilcoxon_p_value': round(wilcoxon_p, 4) if wilcoxon_p is not None else None,
    }

    logger.info(
        f"Computed statistics for experiment {experiment_id}: "
        f"eval_count={eval_count}, x_win_rate={x_win_rate:.2f}%, "
        f"mean={mean_score_val:.2f}, median={median_score_val:.2f}"
    )

    return stats_dict
