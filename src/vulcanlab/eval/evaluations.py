"""
Core logic for evaluation management.

This module provides operations for generating evaluation prompts,
submitting evaluations, and managing evaluation lifecycle.
"""

import logging
from typing import Dict

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import (
    ExperimentAnswer,
    ExperimentEvaluation,
    ExperimentDimensionResult,
)
from vulcanlab.data.models.prompt_template import PromptTemplate
from vulcanlab.eval.answers import get_answer_by_id
from vulcanlab.eval.template_utils import resolve_eval_template, get_default_template
from vulcanlab.eval.dimensions import get_dimension_names_set

logger = logging.getLogger(__name__)


def generate_eval_prompt(session: Session, answer_id: int) -> str:
    """
    Generate an evaluation prompt for an answer pair.

    Retrieves the answer pair, loads the prompt, and resolves the evaluation
    template with actual values.

    Args:
        session: Database session.
        answer_id: ID of the answer pair to evaluate.

    Returns:
        Resolved evaluation prompt ready to send to judge model.

    Raises:
        ValueError: If answer_id not found or answer already evaluated.
    """
    # Get answer with eager loading of prompt relationship
    answer = get_answer_by_id(session, answer_id)

    # Check if already evaluated
    if answer.evaluation is not None:
        raise ValueError(
            f"Answer {answer_id} has already been evaluated. "
            "Delete the existing evaluation first."
        )

    # Get prompt text and experiment
    prompt_text = answer.prompt.prompt_text
    experiment = answer.prompt.experiment

    # Load eval template (T06)
    if experiment.eval_template_id:
        # Load template from database
        template_obj = session.query(PromptTemplate).filter(
            PromptTemplate.id == experiment.eval_template_id
        ).first()

        if not template_obj:
            logger.warning(
                f"Experiment {experiment.id} references eval_template_id "
                f"{experiment.eval_template_id} but template not found. "
                "Falling back to default."
            )
            template = get_default_template(session)
        else:
            template = template_obj.template_content
            logger.info(
                f"Using eval template id={experiment.eval_template_id} "
                f"(function_tag='{template_obj.function_tag}') for experiment {experiment.id}"
            )
    else:
        # Use default template from database (function_tag='eval_default')
        template = get_default_template(session)
        logger.info(f"Using default eval template for experiment {experiment.id}")

    # Resolve template with actual values (uses computed answer_a/answer_b)
    resolved = resolve_eval_template(
        template_text=template,
        prompt=prompt_text,
        answer_a=answer.answer_a,
        answer_b=answer.answer_b
    )

    logger.info(
        f"Generated eval prompt for answer_id={answer_id}, "
        f"prompt_id={answer.prompt_id}, resolved_len={len(resolved)}"
    )

    return resolved


def submit_evaluation(
    session: Session,
    answer_id: int,
    overall_score: int,
    justification: str,
    dimension_scores: Dict[str, int]
) -> ExperimentEvaluation:
    """
    Submit an evaluation for an answer pair.

    Creates an ExperimentEvaluation and associated ExperimentDimensionResult
    records. Validates score ranges.

    Args:
        session: Database session.
        answer_id: ID of the answer pair being evaluated.
        overall_score: Overall comparison score (-10 to 10).
        justification: Text explanation of the evaluation.
        dimension_scores: Dict mapping dimension names to scores (-10 to 10).

    Returns:
        Created ExperimentEvaluation object.

    Raises:
        ValueError: If answer not found, already evaluated, or scores invalid.
        IntegrityError: If database constraints violated (e.g., unique constraint).
    """
    # Validate answer exists and not yet evaluated
    answer = get_answer_by_id(session, answer_id)

    if answer.evaluation is not None:
        raise ValueError(
            f"Answer {answer_id} has already been evaluated. "
            "Delete the existing evaluation first."
        )

    # Validate overall score range
    if not -10 <= overall_score <= 10:
        raise ValueError(
            f"Overall score must be between -10 and 10, got {overall_score}"
        )

    # Validate dimension scores
    for dim_name, score in dimension_scores.items():
        if not -10 <= score <= 10:
            raise ValueError(
                f"Dimension score for '{dim_name}' must be between -10 and 10, "
                f"got {score}"
            )
        if not isinstance(dim_name, str) or not dim_name.strip():
            raise ValueError(
                f"Dimension name must be a non-empty string, got {dim_name}"
            )

    # Validate dimension scores against experiment config (T06)
    experiment = answer.prompt.experiment
    expected_dimensions = get_dimension_names_set(session, experiment.id)

    if not expected_dimensions:
        logger.warning(
            f"Experiment {experiment.id} has no dimensions defined, "
            "allowing any dimension scores"
        )
    else:
        provided_dimensions = set(dimension_scores.keys())

        # Check for missing required dimensions
        missing = expected_dimensions - provided_dimensions
        if missing:
            raise ValueError(
                f"Missing required dimensions: {', '.join(sorted(missing))}. "
                f"Expected: {', '.join(sorted(expected_dimensions))}"
            )

        # Check for extra dimensions (lenient - log warning, allow)
        extra = provided_dimensions - expected_dimensions
        if extra:
            logger.warning(
                f"Evaluation for answer {answer_id} includes extra dimensions "
                f"not in experiment config: {', '.join(sorted(extra))}. Allowing."
            )

    # Validate justification
    if justification is not None and not isinstance(justification, str):
        raise ValueError("Justification must be a string or None")

    # Create evaluation
    evaluation = ExperimentEvaluation(
        answer_id=answer_id,
        overall_score=overall_score,
        justification=justification.strip() if justification else None
    )

    try:
        session.add(evaluation)
        session.flush()  # Get evaluation ID

        # Create dimension results
        for dim_name, score in dimension_scores.items():
            dim_result = ExperimentDimensionResult(
                evaluation_id=evaluation.id,
                dimension_name=dim_name.strip(),
                score=score
            )
            session.add(dim_result)

        session.flush()  # Ensure all dimension results are persisted

        logger.info(
            f"Created evaluation: id={evaluation.id}, answer_id={answer_id}, "
            f"overall_score={overall_score}, dimensions={len(dimension_scores)}"
        )

        return evaluation

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Failed to create evaluation for answer {answer_id}: {str(e)}")
        raise


def delete_evaluation(session: Session, evaluation_id: int) -> None:
    """
    Delete an evaluation (cascade deletes dimension results).

    Args:
        session: Database session.
        evaluation_id: ID of the evaluation to delete.

    Raises:
        ValueError: If evaluation_id not found.
    """
    evaluation = session.query(ExperimentEvaluation).filter(
        ExperimentEvaluation.id == evaluation_id
    ).first()

    if not evaluation:
        logger.warning(f"Cannot delete - evaluation not found: id={evaluation_id}")
        raise ValueError(f"Evaluation with id {evaluation_id} not found")

    answer_id = evaluation.answer_id
    overall_score = evaluation.overall_score

    session.delete(evaluation)
    session.flush()  # Cascade delete happens here

    logger.info(
        f"Deleted evaluation: id={evaluation_id}, answer_id={answer_id}, "
        f"overall_score={overall_score} (cascade deleted dimension results)"
    )
