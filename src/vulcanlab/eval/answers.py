"""
Core logic for answer pair management with blind assignment.

This module provides operations for creating and retrieving answer pairs
with cryptographic random a/b assignment for blind evaluation.
"""

import logging
import secrets
from typing import List

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentAnswer, ExperimentEvaluation

# Configure logging
logger = logging.getLogger(__name__)


def create_answer_pair(
    session: Session,
    prompt_id: int,
    answer_x: str,
    answer_y: str
) -> ExperimentAnswer:
    """
    Create an answer pair with cryptographic random blind assignment.

    Uses secrets.choice() to randomly assign answer_x/answer_y to answer_a/answer_b.
    This ensures blind evaluation where evaluators don't know which answer
    comes from which model.

    Args:
        session: Database session (must be passed explicitly).
        prompt_id: ID of the prompt these answers respond to.
        answer_x: Answer from model X.
        answer_y: Answer from model Y.

    Returns:
        Created ExperimentAnswer object with computed answer_a and answer_b.

    Raises:
        ValueError: If answer_x or answer_y is empty.
        IntegrityError: If database constraints are violated (e.g., invalid prompt_id).
    """
    # Validate required fields
    if not answer_x or not answer_x.strip():
        raise ValueError("Answer X is required and cannot be empty")
    if not answer_y or not answer_y.strip():
        raise ValueError("Answer Y is required and cannot be empty")

    # Cryptographic random assignment for blind evaluation
    is_x_mapped_to_a = secrets.choice([True, False])

    # Create answer instance (answer_a and answer_b are computed properties)
    answer = ExperimentAnswer(
        prompt_id=prompt_id,
        answer_x=answer_x.strip(),
        answer_y=answer_y.strip(),
        is_x_mapped_to_a=is_x_mapped_to_a
    )

    try:
        session.add(answer)
        session.flush()  # Get the ID without committing
        logger.info(
            f"Created answer pair: id={answer.id}, prompt_id={prompt_id}, "
            f"is_x_mapped_to_a={is_x_mapped_to_a}"
        )
        return answer
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Failed to create answer pair for prompt {prompt_id}: {str(e)}")
        raise


def get_answers_by_prompt(session: Session, prompt_id: int) -> List[ExperimentAnswer]:
    """
    Get all answer pairs for a specific prompt.

    Args:
        session: Database session.
        prompt_id: ID of the prompt.

    Returns:
        List of ExperimentAnswer objects, ordered by created_at descending.
    """
    answers = (
        session.query(ExperimentAnswer)
        .filter(ExperimentAnswer.prompt_id == prompt_id)
        .order_by(ExperimentAnswer.created_at.desc())
        .all()
    )
    logger.debug(f"Retrieved {len(answers)} answer pairs for prompt {prompt_id}")
    return answers


def get_answer_by_id(session: Session, answer_id: int) -> ExperimentAnswer:
    """
    Get a specific answer by ID.

    Args:
        session: Database session.
        answer_id: ID of the answer to retrieve.

    Returns:
        ExperimentAnswer object if found.

    Raises:
        ValueError: If answer_id is not found.
    """
    answer = session.query(ExperimentAnswer).filter(
        ExperimentAnswer.id == answer_id
    ).first()

    if not answer:
        logger.warning(f"Answer not found: id={answer_id}")
        raise ValueError(f"Answer with id {answer_id} not found")

    logger.debug(f"Retrieved answer: id={answer.id}, prompt_id={answer.prompt_id}")
    return answer


def delete_answer_pair(session: Session, answer_id: int) -> None:
    """
    Delete an answer pair (cascade deletes evaluation and dimension results).

    Args:
        session: Database session.
        answer_id: ID of the answer to delete.

    Raises:
        ValueError: If answer_id is not found.
    """
    answer = session.query(ExperimentAnswer).filter(
        ExperimentAnswer.id == answer_id
    ).first()

    if not answer:
        logger.warning(f"Cannot delete - answer not found: id={answer_id}")
        raise ValueError(f"Answer with id {answer_id} not found")

    prompt_id = answer.prompt_id

    session.delete(answer)
    session.flush()  # Cascade delete happens here

    logger.info(
        f"Deleted answer pair: id={answer_id}, prompt_id={prompt_id} "
        f"(cascade deleted evaluation and dimension results)"
    )


def get_answer_with_evaluation(session: Session, answer_id: int) -> ExperimentAnswer:
    """
    Get answer by ID with eager-loaded evaluation and dimension results.

    Uses LEFT JOIN to load evaluation relationship if exists.

    Args:
        session: Database session.
        answer_id: ID of the answer to retrieve.

    Returns:
        ExperimentAnswer with evaluation relationship populated.

    Raises:
        ValueError: If answer_id is not found.
    """
    answer = (
        session.query(ExperimentAnswer)
        .options(
            joinedload(ExperimentAnswer.evaluation).joinedload(
                ExperimentEvaluation.dimension_results
            )
        )
        .filter(ExperimentAnswer.id == answer_id)
        .first()
    )

    if not answer:
        logger.warning(f"Answer not found: id={answer_id}")
        raise ValueError(f"Answer with id {answer_id} not found")

    logger.debug(
        f"Retrieved answer with evaluation: id={answer.id}, "
        f"has_evaluation={answer.evaluation is not None}"
    )
    return answer
