"""
Core logic for experiment dimension management.

This module provides CRUD operations for experiment dimensions.
"""

import logging
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.models.experiment import ExperimentDimension

logger = logging.getLogger(__name__)


def create_dimension(
    session: Session,
    experiment_id: int,
    dimension_name: str,
    display_order: int = 0
) -> ExperimentDimension:
    """
    Create a dimension for an experiment.

    Args:
        session: Database session.
        experiment_id: ID of parent experiment.
        dimension_name: Name of the dimension.
        display_order: Order for display (default 0).

    Returns:
        Created ExperimentDimension object.

    Raises:
        ValueError: If dimension_name is empty or invalid.
        IntegrityError: If dimension_name already exists for this experiment.
    """
    # Validate dimension name
    if not dimension_name or not dimension_name.strip():
        raise ValueError("Dimension name is required and cannot be empty")

    dimension = ExperimentDimension(
        experiment_id=experiment_id,
        dimension_name=dimension_name.strip(),
        display_order=display_order
    )

    try:
        session.add(dimension)
        session.flush()
        logger.info(
            f"Created dimension: id={dimension.id}, "
            f"experiment_id={experiment_id}, name='{dimension_name}'"
        )
        return dimension
    except IntegrityError as e:
        session.rollback()
        logger.error(
            f"Failed to create dimension '{dimension_name}' "
            f"for experiment {experiment_id}: {str(e)}"
        )
        raise


def create_dimensions_batch(
    session: Session,
    experiment_id: int,
    dimension_names: List[str]
) -> List[ExperimentDimension]:
    """
    Create multiple dimensions for an experiment.

    Args:
        session: Database session.
        experiment_id: ID of parent experiment.
        dimension_names: List of dimension names in display order.

    Returns:
        List of created ExperimentDimension objects.

    Raises:
        ValueError: If dimension_names is empty or contains duplicates/empty strings.
    """
    if not dimension_names:
        raise ValueError("Must provide at least one dimension name")

    # Validate no duplicates
    cleaned_names = [name.strip() for name in dimension_names]
    if len(cleaned_names) != len(set(cleaned_names)):
        raise ValueError("Dimension names must be unique")

    # Validate no empty strings
    if any(not name for name in cleaned_names):
        raise ValueError("Dimension names cannot be empty")

    dimensions = []
    for idx, name in enumerate(cleaned_names):
        dimension = create_dimension(
            session=session,
            experiment_id=experiment_id,
            dimension_name=name,
            display_order=idx
        )
        dimensions.append(dimension)

    logger.info(
        f"Created {len(dimensions)} dimensions for experiment {experiment_id}"
    )
    return dimensions


def get_dimensions_by_experiment(
    session: Session,
    experiment_id: int
) -> List[ExperimentDimension]:
    """
    Get all dimensions for an experiment, ordered by display_order.

    Args:
        session: Database session.
        experiment_id: ID of experiment.

    Returns:
        List of ExperimentDimension objects.
    """
    dimensions = (
        session.query(ExperimentDimension)
        .filter(ExperimentDimension.experiment_id == experiment_id)
        .order_by(ExperimentDimension.display_order)
        .all()
    )
    logger.debug(f"Retrieved {len(dimensions)} dimensions for experiment {experiment_id}")
    return dimensions


def get_dimension_names_set(
    session: Session,
    experiment_id: int
) -> set:
    """
    Get set of dimension names for an experiment (for validation).

    Args:
        session: Database session.
        experiment_id: ID of experiment.

    Returns:
        Set of dimension name strings.
    """
    dimensions = get_dimensions_by_experiment(session, experiment_id)
    return {d.dimension_name for d in dimensions}
