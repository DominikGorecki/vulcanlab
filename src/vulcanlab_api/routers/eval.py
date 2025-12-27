"""
Eval Router - Evaluation experiment management.

Endpoints for managing evaluation experiments, prompts, answers, and evaluations.

Endpoints (T02):
    GET    /api/v1/eval/experiments           - List all experiments
    POST   /api/v1/eval/experiments           - Create new experiment
    GET    /api/v1/eval/experiments/{id}      - Get experiment details
    DELETE /api/v1/eval/experiments/{id}      - Delete experiment

Endpoints (T03):
    POST   /api/v1/eval/experiments/{id}/prompts       - Add prompt to experiment
    GET    /api/v1/eval/experiments/{id}/prompts       - List prompts for experiment
    GET    /api/v1/eval/prompts/{id}                   - Get prompt details
    DELETE /api/v1/eval/prompts/{id}                   - Delete prompt
    POST   /api/v1/eval/prompts/{id}/answers           - Add answer pair to prompt
    GET    /api/v1/eval/prompts/{id}/answers           - List answers for prompt
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, exists, select
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
from vulcanlab.eval.prompts import (
    create_prompt,
    get_prompts_by_experiment,
    get_prompt_by_id,
    delete_prompt,
)
from vulcanlab.eval.answers import (
    create_answer_pair,
    get_answers_by_prompt,
)
from vulcanlab.eval.evaluations import (
    generate_eval_prompt,
    submit_evaluation,
    delete_evaluation,
)
from vulcanlab.eval.statistics import compute_experiment_statistics
from vulcanlab_api.schemas.eval import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentListItem,
    ExperimentStats,
    PromptCreate,
    PromptResponse,
    PromptListItem,
    AnswerPairCreate,
    AnswerResponse,
    AnswerListItem,
    EvaluationSubmitRequest,
    EvaluationResponse,
    EvalPromptResponse,
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
    description="Get detailed information about a specific experiment with statistical analysis.",
)
async def get_experiment(experiment_id: int) -> ExperimentResponse:
    """Get experiment by ID with computed statistics."""
    try:
        with get_session() as session:
            experiment = get_experiment_by_id(session, experiment_id)

            # Compute statistics
            stats_dict = compute_experiment_statistics(session, experiment_id)

            # Build response
            response = ExperimentResponse.model_validate(experiment)
            response.stats = ExperimentStats(**stats_dict)

            return response

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


# ============================================================================
# Prompt Endpoints (T03)
# ============================================================================

@router.post(
    "/experiments/{experiment_id}/prompts",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add prompt to experiment",
    description="Create a new prompt for an experiment.",
)
async def create_experiment_prompt(experiment_id: int, data: PromptCreate) -> PromptResponse:
    """Add a prompt to an experiment."""
    try:
        with get_session() as session:
            # Verify experiment exists
            get_experiment_by_id(session, experiment_id)

            prompt = create_prompt(
                session=session,
                experiment_id=experiment_id,
                prompt_text=data.prompt_text
            )
            session.commit()
            session.refresh(prompt)
            return PromptResponse.model_validate(prompt)

    except ValueError as e:
        # Check if it's experiment not found or validation error
        error_msg = str(e)
        if "Experiment" in error_msg and "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Integrity constraint violation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )


@router.get(
    "/experiments/{experiment_id}/prompts",
    response_model=List[PromptListItem],
    summary="List prompts for experiment",
    description="Get all prompts for a specific experiment with evaluation counts.",
)
async def list_experiment_prompts(experiment_id: int) -> List[PromptListItem]:
    """List all prompts for an experiment."""
    try:
        with get_session() as session:
            # Verify experiment exists
            get_experiment_by_id(session, experiment_id)

            # Query prompts with evaluation counts
            prompts = session.query(
                ExperimentPrompt,
                func.count(func.distinct(ExperimentEvaluation.id)).label('eval_count')
            ).outerjoin(
                ExperimentAnswer,
                ExperimentPrompt.id == ExperimentAnswer.prompt_id
            ).outerjoin(
                ExperimentEvaluation,
                ExperimentAnswer.id == ExperimentEvaluation.answer_id
            ).filter(
                ExperimentPrompt.experiment_id == experiment_id
            ).group_by(
                ExperimentPrompt.id
            ).order_by(
                ExperimentPrompt.created_at.desc()
            ).all()

            # Convert to response schema
            result = []
            for prompt, eval_count in prompts:
                result.append(PromptListItem(
                    id=prompt.id,
                    experiment_id=prompt.experiment_id,
                    prompt_text=prompt.prompt_text,
                    created_at=prompt.created_at,
                    eval_count=eval_count
                ))

            return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    summary="Get prompt details",
    description="Get detailed information about a specific prompt.",
)
async def get_prompt(prompt_id: int) -> PromptResponse:
    """Get prompt by ID."""
    try:
        with get_session() as session:
            prompt = get_prompt_by_id(session, prompt_id)
            return PromptResponse.model_validate(prompt)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@router.delete(
    "/prompts/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete prompt",
    description="Delete a prompt and all associated answers and evaluations (cascade).",
)
async def delete_prompt_endpoint(prompt_id: int):
    """Delete a prompt."""
    try:
        with get_session() as session:
            delete_prompt(session, prompt_id)
            session.commit()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}"
        )


# ============================================================================
# Answer Endpoints (T03)
# ============================================================================

@router.post(
    "/prompts/{prompt_id}/answers",
    response_model=AnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add answer pair to prompt",
    description="Create an answer pair with cryptographic random blind assignment.",
)
async def create_prompt_answer_pair(prompt_id: int, data: AnswerPairCreate) -> AnswerResponse:
    """Add an answer pair to a prompt."""
    try:
        with get_session() as session:
            # Verify prompt exists
            get_prompt_by_id(session, prompt_id)

            answer = create_answer_pair(
                session=session,
                prompt_id=prompt_id,
                answer_x=data.answer_x,
                answer_y=data.answer_y
            )
            session.commit()
            session.refresh(answer)
            return AnswerResponse.model_validate(answer)

    except ValueError as e:
        # Check if it's prompt not found or validation error
        error_msg = str(e)
        if "Prompt" in error_msg and "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Integrity constraint violation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create answer pair: {str(e)}"
        )


@router.get(
    "/prompts/{prompt_id}/answers",
    response_model=List[AnswerListItem],
    summary="List answers for prompt",
    description="Get all answer pairs for a specific prompt with evaluation status.",
)
async def list_prompt_answers(prompt_id: int) -> List[AnswerListItem]:
    """List all answer pairs for a prompt."""
    try:
        with get_session() as session:
            # Verify prompt exists
            get_prompt_by_id(session, prompt_id)

            # Query answers with evaluation status and ID
            answers = session.query(
                ExperimentAnswer,
                ExperimentEvaluation.id.label('evaluation_id')
            ).outerjoin(
                ExperimentEvaluation,
                ExperimentAnswer.id == ExperimentEvaluation.answer_id
            ).filter(
                ExperimentAnswer.prompt_id == prompt_id
            ).order_by(
                ExperimentAnswer.created_at.desc()
            ).all()

            # Convert to response schema
            result = []
            for answer, eval_id in answers:
                result.append(AnswerListItem(
                    id=answer.id,
                    prompt_id=answer.prompt_id,
                    created_at=answer.created_at,
                    has_evaluation=eval_id is not None,
                    evaluation_id=eval_id
                ))

            return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list answers: {str(e)}"
        )


# ============================================================================
# Evaluation Endpoints (T04)
# ============================================================================

@router.get(
    "/answers/{answer_id}/eval-prompt",
    response_model=EvalPromptResponse,
    summary="Generate evaluation prompt",
    description="Generate an evaluation prompt for an answer pair with template resolution.",
)
async def get_evaluation_prompt(answer_id: int) -> EvalPromptResponse:
    """Generate evaluation prompt for an answer pair."""
    try:
        with get_session() as session:
            prompt = generate_eval_prompt(session, answer_id)
            return EvalPromptResponse(prompt=prompt, answer_id=answer_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate evaluation prompt: {str(e)}"
        )


@router.post(
    "/answers/{answer_id}/evaluation",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit evaluation",
    description="Submit an evaluation for an answer pair with dimension scores.",
)
async def submit_answer_evaluation(
    answer_id: int,
    data: EvaluationSubmitRequest
) -> EvaluationResponse:
    """Submit an evaluation for an answer pair."""
    try:
        with get_session() as session:
            evaluation = submit_evaluation(
                session=session,
                answer_id=answer_id,
                overall_score=data.overall_score,
                justification=data.justification,
                dimension_scores=data.dimension_scores
            )
            session.commit()
            session.refresh(evaluation)
            return EvaluationResponse.model_validate(evaluation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        # Check if it's duplicate evaluation
        error_msg = str(e)
        if "unique" in error_msg.lower() or "answer_id" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Answer {answer_id} has already been evaluated"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Integrity constraint violation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit evaluation: {str(e)}"
        )


@router.delete(
    "/evaluations/{evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete evaluation",
    description="Delete an evaluation and all associated dimension results (cascade).",
)
async def delete_evaluation_endpoint(evaluation_id: int):
    """Delete an evaluation."""
    try:
        with get_session() as session:
            delete_evaluation(session, evaluation_id)
            session.commit()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evaluation: {str(e)}"
        )


@router.get(
    "/prompts/{prompt_id}/evaluations",
    response_model=List[EvaluationResponse],
    summary="List evaluations for prompt",
    description="Get all evaluations for answers associated with a prompt.",
)
async def list_prompt_evaluations(prompt_id: int) -> List[EvaluationResponse]:
    """List all evaluations for a prompt."""
    try:
        with get_session() as session:
            # Verify prompt exists
            get_prompt_by_id(session, prompt_id)

            # Query evaluations for this prompt's answers
            evaluations = (
                session.query(ExperimentEvaluation)
                .join(
                    ExperimentAnswer,
                    ExperimentEvaluation.answer_id == ExperimentAnswer.id,
                )
                .filter(ExperimentAnswer.prompt_id == prompt_id)
                .order_by(ExperimentEvaluation.created_at.desc())
                .all()
            )

            return [EvaluationResponse.model_validate(e) for e in evaluations]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evaluations: {str(e)}",
        )
