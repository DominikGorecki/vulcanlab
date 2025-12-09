"""
Pydantic schemas for prompt template API endpoints.

Defines request and response models for template CRUD operations.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any


class PromptTemplateBase(BaseModel):
    """Base schema for prompt template."""
    function_tag: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1)


class PromptTemplateCreate(BaseModel):
    """Schema for creating a new template version."""
    title: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1)

    @field_validator('template_content')
    @classmethod
    def validate_template_format(cls, v: str) -> str:
        """Validate that template can be parsed as LangChain PromptTemplate."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        try:
            LCPromptTemplate.from_template(v)
        except Exception as e:
            raise ValueError(f"Invalid PromptTemplate format: {e}")
        return v


class PromptTemplateUpdate(BaseModel):
    """Schema for updating an existing template."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    template_content: Optional[str] = Field(None, min_length=1)

    @field_validator('template_content')
    @classmethod
    def validate_template_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate that template can be parsed as LangChain PromptTemplate."""
        if v is None:
            return v
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        try:
            LCPromptTemplate.from_template(v)
        except Exception as e:
            raise ValueError(f"Invalid PromptTemplate format: {e}")
        return v


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for template response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    variables: Optional[List[Dict[str, str]]] = Field(default=None, description="Variable metadata from prompt_meta")


class TemplateSummary(BaseModel):
    """Summary of a template version for list views."""
    version: int
    title: str
    is_active: bool
    created_at: datetime


class FunctionTemplateSummary(BaseModel):
    """Summary of all versions for a function tag."""
    function_tag: str
    active_version: Optional[int]
    versions: List[TemplateSummary]


class TemplateListResponse(BaseModel):
    """Response for listing all template functions."""
    templates: List[FunctionTemplateSummary]


class PromptVariable(BaseModel):
    """Schema for a prompt template variable."""
    variable_name: str = Field(..., min_length=1)
    variable_description: str = Field(..., min_length=1)


class PromptMetaCreate(BaseModel):
    """Schema for creating prompt metadata."""
    function_tag: str = Field(..., min_length=1, max_length=100)
    variables: List[PromptVariable] = Field(default_factory=list)


class PromptMetaUpdate(BaseModel):
    """Schema for updating prompt metadata."""
    variables: List[PromptVariable] = Field(default_factory=list)


class PromptMetaResponse(BaseModel):
    """Schema for prompt metadata response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    function_tag: str
    variables: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
