"""
Pydantic schemas for Research Sessions, Sections, and Reports.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field

from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase, QualityStatus


# --- Research Session Schemas ---

class ResearchSessionBase(BaseModel):
    """Base schema for research session data."""
    collection_id: int = Field(..., description="ID of the collection this session belongs to")
    session_type: SessionType = Field(..., description="Type of session (manual or automated)")


class CreateResearchSessionRequest(BaseModel):
    """Schema for creating a new research session."""
    collection_id: int = Field(..., description="ID of the collection this session belongs to")
    session_type: str = Field(..., description="Type of session ('manual' or 'automated')")


class UpdateResearchSessionRequest(BaseModel):
    """Schema for updating an existing research session."""
    current_phase: Optional[ResearchPhase] = Field(None, description="Current phase of the research process")
    research_plan: Optional[Dict[str, Any]] = Field(None, description="Research plan data")
    state_data: Optional[Dict[str, Any]] = Field(None, description="Session state data")
    status: Optional[SessionStatus] = Field(None, description="Current status of the session")


class ResearchSessionResponse(ResearchSessionBase):
    """Schema for a research session in API responses."""
    id: int
    thread_id: str
    current_phase: Optional[ResearchPhase] = None
    research_plan: Optional[Dict[str, Any]] = None
    state_data: Optional[Dict[str, Any]] = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchSessionListResponse(BaseModel):
    """Schema for a list of research sessions."""
    sessions: List[ResearchSessionResponse]


# --- Research Section Schemas ---

class CreateResearchSectionRequest(BaseModel):
    """Schema for creating a new research section."""
    question_id: str = Field(..., description="Identifier for the question (e.g., 'Q1')")
    question_text: str = Field(..., description="Full question text")
    section_content: Optional[str] = Field(None, description="Generated markdown content")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context information")
    matching_results: Optional[Dict[str, Any]] = Field(None, description="Matching results data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Section metadata")
    reuse_info: Optional[Dict[str, Any]] = Field(None, description="Content reuse information")


class ResearchSectionResponse(BaseModel):
    """Schema for a research section in API responses."""
    id: int
    session_id: int
    question_id: str
    question_text: str
    section_content: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="section_metadata")
    quality_status: QualityStatus = QualityStatus.PENDING
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ResearchSectionListResponse(BaseModel):
    """Schema for a list of research sections."""
    sections: List[ResearchSectionResponse]


# --- Research Report Schemas ---

class CreateResearchReportRequest(BaseModel):
    """Schema for creating a new research report."""
    report_content: str = Field(..., description="Full markdown report content")
    executive_summary: Optional[str] = Field(None, description="Brief summary of the report")
    quality_evaluation: Optional[Dict[str, Any]] = Field(None, description="Quality assessment data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Report metadata")


class ResearchReportResponse(BaseModel):
    """Schema for a research report in API responses."""
    id: int
    session_id: int
    collection_id: Optional[int] = None
    report_content: str
    synthesis_report: Optional[str] = None
    executive_summary: Optional[str] = None
    quality_evaluation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="report_metadata")
    collection: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- Manual Wizard Helper Schemas ---

class AssembleContextRequest(BaseModel):
    """Schema for assembling context for a question."""
    question_id: str = Field(..., description="Identifier for the question (e.g., 'Q1')")
    relevant_item_ids: List[int] = Field(..., description="List of collection item IDs to include")


class AssembleContextResponse(BaseModel):
    """Schema for the assembled context response."""
    context: str = Field(..., description="Assembled and truncated context string")
    token_count: int = Field(..., description="Total token count of the context")
    sources: List[Dict[str, Any]] = Field(..., description="Source attribution metadata")


class MatchResultsRequest(BaseModel):
    """Schema for matching results for a question."""
    question_id: str = Field(..., description="Identifier for the question (e.g., 'Q1')")
    question_text: str = Field(..., description="Full question text to match against")


class MatchResultsResponse(BaseModel):
    """Schema for matching results response."""
    matched_results: List[Dict[str, Any]] = Field(..., description="List of matching research results")
    recommended_strategy: str = Field(..., description="Recommended reuse strategy (e.g., 'exact_reuse')")


class ResumeSessionRequest(BaseModel):
    """Schema for resuming a research session."""
    mode: Optional[str] = Field(None, description="Optional mode switch ('manual' or 'automated')")


class ResumeSessionResponse(BaseModel):
    """Schema for resume session response."""
    session_id: int = Field(..., description="ID of the resumed session")
    current_phase: str = Field(..., description="Current phase of the session")
    next_step: Dict[str, Any] = Field(..., description="Information about the next step to take")


class StartAutomatedResearchRequest(BaseModel):
    """Schema for starting automated research."""
    collection_id: int = Field(..., description="ID of the collection to research")


class StartAutomatedResearchResponse(BaseModel):
    """Schema for automated research start response."""
    session_id: int = Field(..., description="ID of the created session")
    thread_id: str = Field(..., description="Thread ID for the session")
    status: str = Field(..., description="Initial status ('in_progress')")
    message: str = Field(..., description="Status message")


class FormattedPromptResponse(BaseModel):
    """Schema for a formatted prompt response."""
    prompt: str = Field(..., description="The fully formatted prompt string")
    function_tag: str = Field(..., description="The template tag used")
