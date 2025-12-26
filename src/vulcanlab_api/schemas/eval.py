"""
Pydantic schemas for Evaluation API.

Defines request/response models with validation for evaluation experiments.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "GPT-4 vs Claude Comparison",
                "description_x": "GPT-4 answers",
                "description_y": "Claude Sonnet 3.5 answers",
                "model_x": "gpt-4",
                "model_y": "claude-sonnet-3.5",
                "judge_model": "gpt-4o",
                "eval_template_id": None
            }
        }
    )


# ============================================================================
# Response Schemas
# ============================================================================

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

    answer_x: str = Field(..., min_length=1, max_length=10000, description="Answer from model X")
    answer_y: str = Field(..., min_length=1, max_length=10000, description="Answer from model Y")

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

    model_config = ConfigDict(from_attributes=True)
