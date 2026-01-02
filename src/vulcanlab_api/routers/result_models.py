"""
Result Models Router - Model management for LLM result tracking.

Endpoints:
    GET  /api/v1/rag/result-models - List all models
    POST /api/v1/rag/result-models - Create new model
"""

import logging
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vulcanlab.data.database import get_session
from vulcanlab.data.models.result_model import ResultModel
from vulcanlab_api.schemas.result_models import (
    ResultModelItem,
    ResultModelListResponse,
    ResultModelCreateRequest,
    ResultModelCreateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/result-models",
    response_model=ResultModelListResponse,
    summary="List all result models",
    description="List all LLM models used for generating results.",
)
async def list_result_models() -> ResultModelListResponse:
    """List all result models."""
    with get_session() as session:
        models = session.query(ResultModel).order_by(ResultModel.name).all()

        items = [
            ResultModelItem(
                id=model.id,
                name=model.name,
                created_at=model.created_at
            )
            for model in models
        ]

        return ResultModelListResponse(models=items, total=len(items))


@router.post(
    "/result-models",
    response_model=ResultModelCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create result model",
    description="Create a new LLM model entry.",
)
async def create_result_model(request: ResultModelCreateRequest) -> ResultModelCreateResponse:
    """Create a new result model."""
    # Validate and clean name
    name = request.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model name cannot be empty or whitespace only"
        )

    with get_session() as session:
        try:
            model = ResultModel(name=name)
            session.add(model)
            session.commit()
            session.refresh(model)

            return ResultModelCreateResponse(
                id=model.id,
                name=model.name,
                created_at=model.created_at,
                message="Model created successfully"
            )
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model with name '{name}' already exists"
            )


def get_or_create_result_model(name: str, session: Session) -> ResultModel:
    """Get or create a result model by name.

    Args:
        name: Model name (e.g., "gpt-4", "claude-sonnet-3.5")
        session: Database session

    Returns:
        ResultModel instance (existing or newly created)

    Raises:
        ValueError: If name is empty or whitespace only
    """
    # Validate and clean name
    name = name.strip()
    if not name:
        raise ValueError("Model name cannot be empty or whitespace only")

    # Try to find existing model
    model = session.query(ResultModel).filter(ResultModel.name == name).first()
    if model:
        return model

    # Create new model
    try:
        model = ResultModel(name=name)
        session.add(model)
        session.flush()  # Flush to get the ID without committing
        logger.info(f"Created new result model: {name} (id={model.id})")
        return model
    except IntegrityError:
        # Handle race condition: another request created the same model concurrently
        session.rollback()
        # Try to find it again
        model = session.query(ResultModel).filter(ResultModel.name == name).first()
        if model:
            logger.info(f"Result model '{name}' created concurrently, using existing (id={model.id})")
            return model
        # If still not found, something went wrong
        raise RuntimeError(f"Failed to create or retrieve model '{name}'")
