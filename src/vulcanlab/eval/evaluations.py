"""
Core logic for evaluation management.

This module provides operations for generating evaluation prompts,
submitting evaluations, and managing evaluation lifecycle.
"""

import logging
import csv
import io
import json
from typing import Dict, List, Set, Generator

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import (
    ExperimentAnswer,
    ExperimentEvaluation,
    ExperimentDimensionResult,
    ExperimentPrompt,
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
    template with actual values. Can be called for already-evaluated answers
    to regenerate the prompt.

    Args:
        session: Database session.
        answer_id: ID of the answer pair to evaluate.

    Returns:
        Resolved evaluation prompt ready to send to judge model.

    Raises:
        ValueError: If answer_id not found.
    """
    # Get answer with eager loading of prompt relationship
    answer = get_answer_by_id(session, answer_id)

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
    dimension_scores: Dict[str, int],
    overwrite: bool = False
) -> ExperimentEvaluation:
    """
    Submit an evaluation for an answer pair.

    Creates an ExperimentEvaluation and associated ExperimentDimensionResult
    records. Validates score ranges. Can optionally overwrite existing evaluation.

    Args:
        session: Database session.
        answer_id: ID of the answer pair being evaluated.
        overall_score: Overall comparison score (-10 to 10).
        justification: Text explanation of the evaluation.
        dimension_scores: Dict mapping dimension names to scores (-10 to 10).
        overwrite: If True, deletes existing evaluation before creating new one.
                  If False (default), raises ValueError if evaluation exists.

    Returns:
        Created ExperimentEvaluation object.

    Raises:
        ValueError: If answer not found, already evaluated (when overwrite=False),
                   or scores invalid.
        IntegrityError: If database constraints violated (e.g., unique constraint).
    """
    # Validate answer exists and handle existing evaluation
    answer = get_answer_by_id(session, answer_id)

    if answer.evaluation is not None:
        if not overwrite:
            raise ValueError(
                f"Answer {answer_id} has already been evaluated. "
                "Delete the existing evaluation first."
            )
        # If overwrite=True, delete existing evaluation
        existing_eval_id = answer.evaluation.id
        session.delete(answer.evaluation)
        session.flush()  # CASCADE deletes dimension_results
        logger.info(
            f"Deleted existing evaluation id={existing_eval_id} "
            f"for answer {answer_id} (overwrite=True)"
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
            f"{'Overwrote' if overwrite else 'Created'} evaluation: "
            f"id={evaluation.id}, answer_id={answer_id}, "
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


def get_experiment_evaluation_data_for_export(
    session: Session,
    experiment_id: int
) -> List[Dict]:
    """
    Retrieve all completed evaluation data for an experiment, structured for CSV export.

    Assigns a stable grouping_id to each unique prompt based on its creation time.
    Only returns evaluations that are linked to the specified experiment.

    Args:
        session: Database session.
        experiment_id: ID of the experiment to export.

    Returns:
        List of dictionaries containing evaluation data and grouping_id.
    """
    # 1. Establish stable grouping_id for all prompts in this experiment
    # Ordered by created_at (primary) and id (fallback)
    prompts = (
        session.query(ExperimentPrompt)
        .filter(ExperimentPrompt.experiment_id == experiment_id)
        .order_by(ExperimentPrompt.created_at.asc(), ExperimentPrompt.id.asc())
        .all()
    )

    prompt_id_to_grouping_id = {
        prompt.id: index + 1
        for index, prompt in enumerate(prompts)
    }

    # 2. Query all evaluations for this experiment
    # Joined with answer and prompt to filter by experiment_id and access prompt_id
    evaluations = (
        session.query(ExperimentEvaluation)
        .join(ExperimentAnswer, ExperimentEvaluation.answer_id == ExperimentAnswer.id)
        .join(ExperimentPrompt, ExperimentAnswer.prompt_id == ExperimentPrompt.id)
        .filter(ExperimentPrompt.experiment_id == experiment_id)
        .options(
            joinedload(ExperimentEvaluation.dimension_results),
            joinedload(ExperimentEvaluation.answer)
        )
        .all()
    )

    # 3. Format data for export
    export_data = []
    for evaluation in evaluations:
        prompt = evaluation.answer.prompt
        grouping_id = prompt_id_to_grouping_id.get(prompt.id)

        # Skip if for some reason prompt_id not in mapping (shouldn't happen)
        if grouping_id is None:
            logger.warning(
                f"Evaluation {evaluation.id} linked to prompt {prompt.id} "
                f"which was not found in experiment {experiment_id} prompts."
            )
            continue

        # Adjust scores based on blind mapping
        # If is_x_mapped_to_a is True: A=X, B=Y. Scores are X relative to Y.
        # If is_x_mapped_to_a is False: A=Y, B=X. Scores are Y relative to X.
        # So if is_x_mapped_to_a is False, we must invert the scores to represent X vs Y.
        multiplier = 1 if evaluation.answer.is_x_mapped_to_a else -1

        row = {
            "prompt": prompt.prompt_text,
            "grouping_id": grouping_id,
            "overall_score": evaluation.overall_score * multiplier,
            "justification": evaluation.justification,
            "dimension_scores": {
                dr.dimension_name: dr.score * multiplier
                for dr in evaluation.dimension_results
            }
        }
        export_data.append(row)

    logger.info(
        f"Retrieved {len(export_data)} evaluations for export for "
        f"experiment_id={experiment_id}"
    )

    return export_data


def export_experiment_evaluations_to_csv(
    session: Session,
    experiment_id: int
) -> str:
    """
    Export all completed evaluations for an experiment to a CSV string.

    The CSV includes prompt text, grouping ID, overall score, dimension scores,
    and justification. Dimension columns are generated dynamically.

    Args:
        session: Database session.
        experiment_id: ID of the experiment to export.

    Returns:
        String containing the generated CSV data.
    """
    # 1. Retrieve the evaluation data
    eval_data = get_experiment_evaluation_data_for_export(session, experiment_id)

    if not eval_data:
        logger.info(f"No evaluations found for experiment {experiment_id} export.")
        # Return only the header if no data
        return "prompt,grouping_id,overall_score,justification\n"

    # 2. Collect all unique dimension names to define columns
    dimension_names: Set[str] = set()
    for row in eval_data:
        dimension_names.update(row["dimension_scores"].keys())

    sorted_dimensions = sorted(list(dimension_names))

    # 3. Define CSV fieldnames (R1 order)
    # prompt, grouping_id, overall_score, [dimensions...], justification
    fieldnames = ["prompt", "grouping_id", "overall_score"]
    fieldnames.extend(sorted_dimensions)
    fieldnames.append("justification")

    # 4. Generate CSV content
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    for row in eval_data:
        # Flatten the row for DictWriter
        csv_row = {
            "prompt": row["prompt"],
            "grouping_id": row["grouping_id"],
            "overall_score": row["overall_score"],
            "justification": row["justification"]
        }
        # Add dimension scores (missing dimensions will be blank)
        for dim in sorted_dimensions:
            csv_row[dim] = row["dimension_scores"].get(dim, "")

        writer.writerow(csv_row)

    csv_string = output.getvalue()
    output.close()

    logger.info(
        f"Generated CSV export for experiment {experiment_id} "
        f"({len(eval_data)} rows, {len(csv_string)} bytes)"
    )

    return csv_string


def export_experiment_answers_to_jsonl(
    session: Session,
    experiment_id: int
) -> Generator[str, None, None]:
    """
    Export answer pairs with completed evaluations to JSONL format.

    Generates one JSON object per line (newline-delimited JSON) containing
    prompt_text, answer_x, and answer_y for each answer pair that has been
    evaluated. Uses a generator pattern for memory-efficient streaming.

    Args:
        session: Database session.
        experiment_id: ID of the experiment to export.

    Yields:
        JSONL lines (each line is a JSON object followed by newline).

    Example output:
        {"prompt_text":"...", "answer_x":"...", "answer_y":"..."}\n
        {"prompt_text":"...", "answer_x":"...", "answer_y":"..."}\n
    """
    # Query answer pairs with completed evaluations
    # Join Answer -> Prompt -> Evaluation to filter by experiment and evaluation existence
    answer_pairs = (
        session.query(ExperimentAnswer, ExperimentPrompt)
        .join(ExperimentPrompt, ExperimentAnswer.prompt_id == ExperimentPrompt.id)
        .join(ExperimentEvaluation, ExperimentAnswer.id == ExperimentEvaluation.answer_id)
        .filter(ExperimentPrompt.experiment_id == experiment_id)
        .order_by(ExperimentPrompt.created_at.asc(), ExperimentAnswer.id.asc())
        .all()
    )

    record_count = 0
    for answer, prompt in answer_pairs:
        record = {
            "prompt_text": prompt.prompt_text,
            "answer_x": answer.answer_x,
            "answer_y": answer.answer_y
        }

        # Serialize to JSON with Unicode support, append newline for JSONL format
        jsonl_line = json.dumps(record, ensure_ascii=False) + "\n"
        yield jsonl_line
        record_count += 1

    logger.info(
        f"Generated JSONL export for experiment {experiment_id} "
        f"({record_count} records)"
    )
