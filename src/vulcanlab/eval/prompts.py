"""
Core logic for prompt management in evaluation experiments.

This module provides CRUD operations for experiment prompts,
following the three-tier architecture pattern.
"""

import logging
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentPrompt

# Configure logging
logger = logging.getLogger(__name__)


def create_prompt(
    session: Session,
    experiment_id: int,
    prompt_text: str
) -> ExperimentPrompt:
    """
    Create a new prompt for an experiment.

    Args:
        session: Database session (must be passed explicitly).
        experiment_id: ID of the experiment this prompt belongs to.
        prompt_text: The text of the prompt (required).

    Returns:
        Created ExperimentPrompt object.

    Raises:
        ValueError: If prompt_text is empty or invalid.
        IntegrityError: If database constraints are violated (e.g., invalid experiment_id).
    """
    # Validate required fields
    if not prompt_text or not prompt_text.strip():
        raise ValueError("Prompt text is required and cannot be empty")

    # Create prompt instance
    prompt = ExperimentPrompt(
        experiment_id=experiment_id,
        prompt_text=prompt_text.strip()
    )

    try:
        session.add(prompt)
        session.flush()  # Get the ID without committing
        logger.info(
            f"Created prompt: id={prompt.id}, experiment_id={experiment_id}, "
            f"text_preview='{prompt_text[:50]}...'"
        )
        return prompt
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Failed to create prompt for experiment {experiment_id}: {str(e)}")
        raise


def get_prompts_by_experiment(session: Session, experiment_id: int) -> List[ExperimentPrompt]:
    """
    Get all prompts for a specific experiment.

    Args:
        session: Database session.
        experiment_id: ID of the experiment.

    Returns:
        List of ExperimentPrompt objects, ordered by created_at descending.
    """
    prompts = (
        session.query(ExperimentPrompt)
        .filter(ExperimentPrompt.experiment_id == experiment_id)
        .order_by(ExperimentPrompt.created_at.desc())
        .all()
    )
    logger.debug(f"Retrieved {len(prompts)} prompts for experiment {experiment_id}")
    return prompts


def get_prompt_by_id(session: Session, prompt_id: int) -> ExperimentPrompt:
    """
    Get a specific prompt by ID.

    Args:
        session: Database session.
        prompt_id: ID of the prompt to retrieve.

    Returns:
        ExperimentPrompt object if found.

    Raises:
        ValueError: If prompt_id is not found.
    """
    prompt = session.query(ExperimentPrompt).filter(
        ExperimentPrompt.id == prompt_id
    ).first()

    if not prompt:
        logger.warning(f"Prompt not found: id={prompt_id}")
        raise ValueError(f"Prompt with id {prompt_id} not found")

    logger.debug(f"Retrieved prompt: id={prompt.id}, experiment_id={prompt.experiment_id}")
    return prompt


def delete_prompt(session: Session, prompt_id: int) -> None:
    """
    Delete a prompt (cascade deletes answers and evaluations).

    Args:
        session: Database session.
        prompt_id: ID of the prompt to delete.

    Raises:
        ValueError: If prompt_id is not found.
    """
    prompt = session.query(ExperimentPrompt).filter(
        ExperimentPrompt.id == prompt_id
    ).first()

    if not prompt:
        logger.warning(f"Cannot delete - prompt not found: id={prompt_id}")
        raise ValueError(f"Prompt with id {prompt_id} not found")

    experiment_id = prompt.experiment_id
    prompt_preview = prompt.prompt_text[:50]

    session.delete(prompt)
    session.flush()  # Cascade delete happens here
    logger.info(
        f"Deleted prompt: id={prompt_id}, experiment_id={experiment_id}, "
        f"text_preview='{prompt_preview}...' (cascade deleted answers and evaluations)"
    )
