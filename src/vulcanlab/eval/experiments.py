"""
Core logic for experiment management.

This module provides CRUD operations for evaluation experiments,
following the three-tier architecture pattern where all business logic
is framework-independent.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import Experiment

# Configure logging
logger = logging.getLogger(__name__)


def create_experiment(
    session: Session,
    name: str,
    description_x: Optional[str] = None,
    description_y: Optional[str] = None,
    model_x: Optional[str] = None,
    model_y: Optional[str] = None,
    judge_model: Optional[str] = None,
    eval_template_id: Optional[int] = None
) -> Experiment:
    """
    Create a new evaluation experiment.

    Args:
        session: Database session (must be passed explicitly).
        name: Human-readable experiment name (required).
        description_x: Description of answer set X.
        description_y: Description of answer set Y.
        model_x: Model name for answer set X.
        model_y: Model name for answer set Y.
        judge_model: Model name used as evaluation judge.
        eval_template_id: Foreign key to prompt template (nullable).

    Returns:
        Created Experiment object.

    Raises:
        ValueError: If name is empty or invalid.
        IntegrityError: If database constraints are violated.
    """
    # Validate required fields
    if not name or not name.strip():
        raise ValueError("Experiment name is required and cannot be empty")

    # Create experiment instance
    experiment = Experiment(
        name=name.strip(),
        description_x=description_x.strip() if description_x else None,
        description_y=description_y.strip() if description_y else None,
        model_x=model_x.strip() if model_x else None,
        model_y=model_y.strip() if model_y else None,
        judge_model=judge_model.strip() if judge_model else None,
        eval_template_id=eval_template_id
    )

    try:
        session.add(experiment)
        session.flush()  # Get the ID without committing
        logger.info(
            f"Created experiment: id={experiment.id}, name='{experiment.name}'"
        )
        return experiment
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Failed to create experiment '{name}': {str(e)}")
        raise


def get_experiments(session: Session) -> List[Experiment]:
    """
    Get all evaluation experiments.

    Args:
        session: Database session.

    Returns:
        List of all Experiment objects, ordered by created_at descending.
    """
    experiments = (
        session.query(Experiment)
        .order_by(Experiment.created_at.desc())
        .all()
    )
    logger.debug(f"Retrieved {len(experiments)} experiments")
    return experiments


def get_experiment_by_id(session: Session, experiment_id: int) -> Experiment:
    """
    Get a specific experiment by ID.

    Args:
        session: Database session.
        experiment_id: ID of the experiment to retrieve.

    Returns:
        Experiment object if found.

    Raises:
        ValueError: If experiment_id is not found.
    """
    experiment = session.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()

    if not experiment:
        logger.warning(f"Experiment not found: id={experiment_id}")
        raise ValueError(f"Experiment with id {experiment_id} not found")

    logger.debug(f"Retrieved experiment: id={experiment.id}, name='{experiment.name}'")
    return experiment


def delete_experiment(session: Session, experiment_id: int) -> None:
    """
    Delete an experiment (cascade deletes prompts, answers, evaluations).

    Args:
        session: Database session.
        experiment_id: ID of the experiment to delete.

    Raises:
        ValueError: If experiment_id is not found.
    """
    experiment = session.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()

    if not experiment:
        logger.warning(f"Cannot delete - experiment not found: id={experiment_id}")
        raise ValueError(f"Experiment with id {experiment_id} not found")

    experiment_name = experiment.name
    session.delete(experiment)
    session.flush()  # Cascade delete happens here
    logger.info(
        f"Deleted experiment: id={experiment_id}, name='{experiment_name}' "
        "(cascade deleted prompts, answers, evaluations)"
    )
