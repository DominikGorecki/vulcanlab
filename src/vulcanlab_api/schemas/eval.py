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
