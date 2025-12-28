"""
Pydantic schemas for Evaluation API.

Defines request/response models with validation for evaluation experiments.
"""

from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    description_x: Optional[str] = Field(None, description="Description of answer set X")
    description_y: Optional[str] = Field(None, description="Description of answer set Y")
    model_x: Optional[str] = Field(None, max_length=100, description="Model name for answer set X")
    model_y: Optional[str] = Field(None, max_length=100, description="Model name for answer set Y")
    judge_model: Optional[str] = Field(None, max_length=100, description="Model name for judge")
    eval_template_id: Optional[int] = Field(None, description="Template ID for evaluation prompts")
    dimension_names: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Additional dimension names (core 5 always included)"
    )

    @field_validator('dimension_names')
    @classmethod
    def validate_dimension_names(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate dimension names."""
        if v is None:
            return v

        # Check for empty strings
        cleaned = [name.strip() for name in v]
        if any(not name for name in cleaned):
            raise ValueError("Dimension names cannot be empty strings")

        # Check for duplicates
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Dimension names must be unique")

        return cleaned

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "GPT-4 vs Claude Comparison",
                "description_x": "GPT-4 answers",
                "description_y": "Claude Sonnet 3.5 answers",
                "model_x": "gpt-4",
                "model_y": "claude-sonnet-3.5",
                "judge_model": "gpt-4o",
                "eval_template_id": None,
                "dimension_names": ["citation_quality", "academic_tone"]
            }
        }
    )


# ============================================================================
# Response Schemas
# ============================================================================

class ExperimentDimensionResponse(BaseModel):
    """Schema for experiment dimension response."""

    id: int
    experiment_id: int
    dimension_name: str
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class ExperimentStats(BaseModel):
    """Schema for experiment statistics."""

    eval_count: int = Field(0, description="Total number of completed evaluations")
    x_win_rate: float = Field(0.0, description="Percentage where X > Y")
    mean_score: float = Field(0.0, description="Mean unblinded score")
    median_score: float = Field(0.0, description="Median unblinded score")
    tie_percentage: float = Field(0.0, description="Percentage of ties (score = 0)")
    harm_rate: float = Field(0.0, description="Percentage where X < Y (harm rate)")
    wilcoxon_p_value: Optional[float] = Field(
        None,
        description="Wilcoxon signed-rank test p-value (None if N <= 1)"
    )

    model_config = ConfigDict(from_attributes=True)


class ExperimentResponse(BaseModel):
    """Schema for experiment response."""

    id: int
    name: str
    description_x: Optional[str]
    description_y: Optional[str]
    model_x: Optional[str]
    model_y: Optional[str]
    judge_model: Optional[str]
    eval_template_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    dimensions: List[ExperimentDimensionResponse] = Field(default_factory=list)
    stats: Optional[ExperimentStats] = None

    model_config = ConfigDict(from_attributes=True)


class ExperimentListItem(BaseModel):
    """Schema for experiment in list view with counts."""

    id: int
    name: str
    description_x: Optional[str]
    description_y: Optional[str]
    created_at: datetime
    prompt_count: int = Field(0, description="Number of prompts in experiment")
    eval_count: int = Field(0, description="Number of completed evaluations")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Prompt Schemas
# ============================================================================

class PromptCreate(BaseModel):
    """Schema for creating a new prompt."""

    prompt_text: str = Field(..., min_length=1, max_length=10000, description="The prompt text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt_text": "What is the capital of France?"
            }
        }
    )


class PromptResponse(BaseModel):
    """Schema for prompt response."""

    id: int
    experiment_id: int
    prompt_text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptListItem(BaseModel):
    """Schema for prompt in list view with eval count."""

    id: int
    experiment_id: int
    prompt_text: str
    created_at: datetime
    eval_count: int = Field(0, description="Number of completed evaluations for this prompt")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Answer Schemas
# ============================================================================

class AnswerPairCreate(BaseModel):
    """Schema for creating an answer pair."""

    answer_x: str = Field(..., min_length=1, max_length=100000, description="Answer from model X")
    answer_y: str = Field(..., min_length=1, max_length=100000, description="Answer from model Y")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer_x": "The capital of France is Paris.",
                "answer_y": "Paris is the capital of France."
            }
        }
    )


class AnswerResponse(BaseModel):
    """Schema for answer response."""

    id: int
    prompt_id: int
    answer_x: str
    answer_y: str
    is_x_mapped_to_a: bool
    answer_a: str
    answer_b: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerListItem(BaseModel):
    """Schema for answer in list view with evaluation status."""

    id: int
    prompt_id: int
    created_at: datetime
    has_evaluation: bool = Field(False, description="Whether this answer has been evaluated")
    evaluation_id: Optional[int] = Field(None, description="ID of evaluation if exists")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Evaluation Schemas
# ============================================================================

class EvaluationSubmitRequest(BaseModel):
    """Schema for submitting an evaluation."""

    overall_score: int = Field(
        ...,
        ge=-10,
        le=10,
        description="Overall comparison score (-10 to 10)"
    )
    justification: Optional[str] = Field(
        None,
        max_length=10000,
        description="Explanation of evaluation"
    )
    dimension_scores: Dict[str, int] = Field(
        ...,
        description="Dimension names mapped to scores (-10 to 10)"
    )

    @field_validator('dimension_scores')
    @classmethod
    def validate_dimension_scores(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Validate dimension scores are in valid range."""
        for dim_name, score in v.items():
            if not isinstance(dim_name, str) or not dim_name.strip():
                raise ValueError("Dimension names must be non-empty strings")
            if not isinstance(score, int):
                raise ValueError(f"Score for '{dim_name}' must be an integer")
            if not -10 <= score <= 10:
                raise ValueError(
                    f"Score for '{dim_name}' must be between -10 and 10, got {score}"
                )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 5,
                "justification": "Answer A provides more detailed explanation with examples.",
                "dimension_scores": {
                    "factual_correctness": 8,
                    "completeness": 6,
                    "clarity": 5
                }
            }
        }
    )


class DimensionResultResponse(BaseModel):
    """Schema for dimension result in evaluation response."""

    dimension_name: str
    score: int

    model_config = ConfigDict(from_attributes=True)


class EvaluationResponse(BaseModel):
    """Schema for evaluation response."""

    id: int
    answer_id: int
    overall_score: int
    justification: Optional[str]
    dimension_results: list[DimensionResultResponse]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalPromptResponse(BaseModel):
    """Schema for evaluation prompt response."""

    prompt: str = Field(..., description="Resolved evaluation prompt")
    answer_id: int = Field(..., description="ID of answer pair")
