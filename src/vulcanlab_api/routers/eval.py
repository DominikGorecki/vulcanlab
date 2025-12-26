"""
Eval Router - Evaluation experiment management.

Endpoints for managing evaluation experiments, prompts, answers, and evaluations.

Endpoints (T02):
    GET    /api/v1/eval/experiments           - List all experiments
    POST   /api/v1/eval/experiments           - Create new experiment
    GET    /api/v1/eval/experiments/{id}      - Get experiment details
    DELETE /api/v1/eval/experiments/{id}      - Delete experiment
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.database import get_session
from vulcanlab.data.models.experiment import (
    Experiment,
    ExperimentPrompt,
    ExperimentAnswer,
    ExperimentEvaluation,
)
from vulcanlab.eval.experiments import (
    create_experiment,
    get_experiments,
    get_experiment_by_id,
    delete_experiment,
)
from vulcanlab_api.schemas.eval import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentListItem,
)

router = APIRouter()


# ============================================================================
# GET Endpoints
# ============================================================================

@router.get(
    "/experiments",
    response_model=List[ExperimentListItem],
    summary="List all experiments",
    description="Get a list of all evaluation experiments with prompt and evaluation counts.",
)
async def list_experiments() -> List[ExperimentListItem]:
    """List all evaluation experiments."""
    try:
        with get_session() as session:
            # Query experiments with counts
            experiments = session.query(
                Experiment,
                func.count(func.distinct(ExperimentPrompt.id)).label('prompt_count'),
                func.count(func.distinct(ExperimentEvaluation.id)).label('eval_count')
            ).outerjoin(
                ExperimentPrompt,
                Experiment.id == ExperimentPrompt.experiment_id
            ).outerjoin(
                ExperimentAnswer,
                ExperimentPrompt.id == ExperimentAnswer.prompt_id
            ).outerjoin(
                ExperimentEvaluation,
                ExperimentAnswer.id == ExperimentEvaluation.answer_id
            ).group_by(
                Experiment.id
            ).order_by(
                Experiment.created_at.desc()
            ).all()

            # Convert to response schema
            result = []
            for exp, prompt_count, eval_count in experiments:
                result.append(ExperimentListItem(
                    id=exp.id,
                    name=exp.name,
                    description_x=exp.description_x,
                    description_y=exp.description_y,
                    created_at=exp.created_at,
                    prompt_count=prompt_count,
                    eval_count=eval_count
                ))

            return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list experiments: {str(e)}"
        )


@router.get(
    "/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Get experiment details",
    description="Get detailed information about a specific experiment.",
)
async def get_experiment(experiment_id: int) -> ExperimentResponse:
    """Get experiment by ID."""
    try:
        with get_session() as session:
            experiment = get_experiment_by_id(session, experiment_id)
            return ExperimentResponse.model_validate(experiment)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment: {str(e)}"
        )


# ============================================================================
# POST Endpoints
# ============================================================================

@router.post(
    "/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new experiment",
    description="Create a new evaluation experiment with the specified configuration.",
)
async def create_new_experiment(data: ExperimentCreate) -> ExperimentResponse:
    """Create a new evaluation experiment."""
    try:
        with get_session() as session:
            experiment = create_experiment(
                session=session,
                name=data.name,
                description_x=data.description_x,
                description_y=data.description_y,
                model_x=data.model_x,
                model_y=data.model_y,
                judge_model=data.judge_model,
                eval_template_id=data.eval_template_id
            )
            session.commit()
            session.refresh(experiment)
            return ExperimentResponse.model_validate(experiment)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Integrity constraint violation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}"
        )


# ============================================================================
# DELETE Endpoints
# ============================================================================

@router.delete(
    "/experiments/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete experiment",
    description="Delete an experiment and all associated prompts, answers, and evaluations (cascade).",
)
async def delete_experiment_endpoint(experiment_id: int):
    """Delete an experiment."""
    try:
        with get_session() as session:
            delete_experiment(session, experiment_id)
            session.commit()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete experiment: {str(e)}"
        )
