"""
Pydantic models for simple conversion API endpoints.

Request and response models for the simple conversion pipeline API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StartConversionRequest(BaseModel):
    """Request to start simple conversion."""
    file_path: str = Field(..., description="Path to PDF/EPUB file")
    title: str = Field(..., min_length=1, description="Work title")
    author: str = Field(..., min_length=1, description="Work author")
    year: Optional[int] = Field(None, description="Publication year")
    mode: str = Field(..., pattern="^(automatic|manual)$", description="Execution mode")


class StartConversionResponse(BaseModel):
    """Response from starting conversion."""
    work_id: int
    status: str
    mode: str
    message: str


class ConversionStatus(BaseModel):
    """Current status of conversion pipeline."""
    work_id: int
    step: str  # 'parsing', 'parsed', 'sanitizing', 'sanitized', 'chunking', 'chunked', 'complete', 'error'
    classification: Optional[str] = None  # 'small' or 'large'
    token_count: Optional[int] = None
    chunk_count: Optional[int] = None
    mode: Optional[str] = None  # 'automatic' or 'manual'
    error_message: Optional[str] = None


class ExecuteAutoResponse(BaseModel):
    """Response from automatic execution."""
    work_id: int
    status: str
    chunks_created: int
    message: str


class ManualPromptResponse(BaseModel):
    """Prompt for manual LLM execution."""
    work_id: int
    classification: str
    prompt: str
    instructions: str


class ManualSubmitRequest(BaseModel):
    """Submission of manual LLM result."""
    llm_response: str = Field(..., min_length=1, description="LLM response text")


class ManualSubmitResponse(BaseModel):
    """Response from manual submission."""
    work_id: int
    status: str
    message: str


class ChunkResult(BaseModel):
    """Single chunk result."""
    id: int
    heading_level: str  # "H1", "H2", etc.
    heading_text: str
    start_line: int
    end_line: int
    content_preview: str  # First 200 chars


class ConversionResults(BaseModel):
    """Final conversion results."""
    work_id: int
    title: str
    author: str
    classification: str
    token_count: int
    chunk_count: int
    chunks: List[ChunkResult]
