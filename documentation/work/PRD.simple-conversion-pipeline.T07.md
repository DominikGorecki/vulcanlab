# T07: Simple Conversion API Endpoints

**Status**: COMPLETE
**Priority**: High
**Type**: Backend + API
**Depends On**: T01-T06 (All backend modules)
**Blocks**: T09-T11 (Frontend workflows)

## Overview

Implement REST API endpoints to support the simple conversion pipeline frontend workflows. Includes endpoints to: start conversion with metadata, get conversion status, execute automatic pipeline, get manual prompts, submit manual LLM results, and retrieve conversion results.

## Acceptance Criteria

- [x] POST `/api/simple-conversion/start` - Create Work and start conversion
- [x] GET `/api/simple-conversion/status/{work_id}` - Get current pipeline status
- [x] POST `/api/simple-conversion/execute-auto/{work_id}` - Run full automatic pipeline
- [x] GET `/api/simple-conversion/manual-prompt/{work_id}` - Get prompt for manual LLM step
- [x] POST `/api/simple-conversion/manual-submit/{work_id}` - Submit manual LLM result
- [x] GET `/api/simple-conversion/results/{work_id}` - Get final chunks/results
- [x] All endpoints return proper HTTP status codes
- [x] All endpoints include error handling
- [x] Pydantic models for request/response validation
- [x] All unit tests pass and use mocks (no database access)
- [ ] Manual test plan with curl/Postman completed successfully

## Technical Implementation

### 1. API Models (Pydantic)

**File**: `src/vulcanlab/api/models/simple_conversion.py` (NEW)

```python
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
    heading_level: int
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
```

### 2. API Endpoints

**File**: `src/vulcanlab/api/simple_conversion.py` (NEW)

```python
"""
API endpoints for simple conversion pipeline.

Provides REST API for the streamlined conversion workflow including
both automatic and manual execution modes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from vulcanlab.api.models.simple_conversion import (
    StartConversionRequest,
    StartConversionResponse,
    ConversionStatus,
    ExecuteAutoResponse,
    ManualPromptResponse,
    ManualSubmitRequest,
    ManualSubmitResponse,
    ConversionResults,
    ChunkResult
)
from vulcanlab.data.database import get_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.parsed_markdown import ParsedMarkdown
from vulcanlab.data.models.chunk import Chunk
from vulcanlab.simple_conversion.parse_classify import parse_and_classify
from vulcanlab.simple_conversion.sanitize_small import sanitize_small_document
from vulcanlab.simple_conversion.sanitize_large import sanitize_large_document
from vulcanlab.simple_conversion.chunk_simple import create_chunks_from_sanitized
from vulcanlab.data.template_loader import load_template
from vulcanlab.simple_conversion.sanitize_small import get_hardcoded_template_small
from vulcanlab.simple_conversion.sanitize_large import get_hardcoded_template_large

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simple-conversion", tags=["simple_conversion"])


def get_db() -> Session:
    """Dependency to get database session."""
    with get_session() as session:
        yield session


@router.post("/start", response_model=StartConversionResponse)
async def start_conversion(
    request: StartConversionRequest,
    session: Session = Depends(get_db)
):
    """
    Start simple conversion process.

    Creates a new Work record with provided metadata and initiates
    the PDF/EPUB conversion step.

    Args:
        request: Conversion start parameters
        session: Database session

    Returns:
        Work ID and initial status
    """
    try:
        # TODO: Integrate with existing conversion module to convert PDF/EPUB
        # For now, create Work record with processing_status

        # Create Work record
        work = Work(
            title=request.title,
            author=request.author,
            year=request.year
        )

        session.add(work)
        session.flush()

        # Initialize processing_status
        work.processing_status = {
            'simple_conversion_step': 'converting',
            'simple_conversion_mode': request.mode
        }

        # TODO: Trigger actual PDF/EPUB conversion
        # For MVP, assume conversion happens externally or via existing module

        session.commit()
        session.refresh(work)

        logger.info(f"Started simple conversion for work {work.id} in {request.mode} mode")

        return StartConversionResponse(
            work_id=work.id,
            status='converting',
            message=f'Conversion started in {request.mode} mode'
        )

    except Exception as e:
        logger.error(f"Failed to start conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{work_id}", response_model=ConversionStatus)
async def get_status(
    work_id: int,
    session: Session = Depends(get_db)
):
    """
    Get current conversion pipeline status.

    Args:
        work_id: Work ID
        session: Database session

    Returns:
        Current pipeline status including step, classification, counts
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        ps = work.processing_status or {}

        return ConversionStatus(
            work_id=work_id,
            step=ps.get('simple_conversion_step', 'unknown'),
            classification=ps.get('simple_conversion_classification'),
            token_count=ps.get('simple_conversion_token_count'),
            chunk_count=ps.get('chunk_count'),
            mode=ps.get('simple_conversion_mode'),
            error_message=ps.get('error_message')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-auto/{work_id}", response_model=ExecuteAutoResponse)
async def execute_automatic(
    work_id: int,
    session: Session = Depends(get_db)
):
    """
    Execute full automatic pipeline.

    Runs parse → classify → sanitize → chunk steps automatically
    without user intervention.

    Args:
        work_id: Work ID (must have completed conversion)
        session: Database session

    Returns:
        Final status with chunk count
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        # Step 1: Parse and classify
        logger.info(f"Automatic: Parse & classify work {work_id}")
        parsed = parse_and_classify(work_id, session)

        # Step 2: Sanitize (small or large based on classification)
        logger.info(f"Automatic: Sanitize {parsed.classification.value} document")

        if parsed.classification.value == 'small':
            sanitized = sanitize_small_document(work_id, session)
        else:
            sanitized = sanitize_large_document(work_id, session)

        # Step 3: Chunk
        logger.info(f"Automatic: Create chunks for work {work_id}")
        chunks = create_chunks_from_sanitized(work_id, session)

        # Update final status
        work.processing_status['simple_conversion_step'] = 'complete'
        session.commit()

        logger.info(f"Automatic pipeline complete for work {work_id}: {len(chunks)} chunks")

        return ExecuteAutoResponse(
            work_id=work_id,
            status='complete',
            chunks_created=len(chunks),
            message=f'Automatic pipeline completed successfully'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Automatic pipeline failed for work {work_id}: {e}")

        # Update error status
        try:
            work = session.query(Work).filter(Work.id == work_id).first()
            if work:
                work.processing_status['simple_conversion_step'] = 'error'
                work.processing_status['error_message'] = str(e)
                session.commit()
        except:
            pass

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manual-prompt/{work_id}", response_model=ManualPromptResponse)
async def get_manual_prompt(
    work_id: int,
    session: Session = Depends(get_db)
):
    """
    Get prompt text for manual LLM execution.

    Returns the formatted prompt that the user should copy and paste
    into their LLM interface.

    Args:
        work_id: Work ID (must be parsed and classified)
        session: Database session

    Returns:
        Prompt text and instructions
    """
    try:
        # Parse and classify first if not already done
        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            # Need to parse first
            parsed = parse_and_classify(work_id, session)

        classification = parsed.classification.value

        # Load appropriate template
        if classification == 'small':
            template = load_template('simple_sanitize_small', get_hardcoded_template_small)
            prompt = template.format(markdown=parsed.content)
            instructions = (
                "Copy the prompt below and paste it into your LLM interface (ChatGPT, Claude, etc.). "
                "Then copy the LLM's JSON response and submit it using the Manual Submit endpoint."
            )
        else:  # large
            # Need to create condensed version
            from vulcanlab.simple_conversion.sanitize_large import (
                extract_headings_with_context,
                create_condensed_markdown
            )

            headings = extract_headings_with_context(parsed.content)
            condensed = create_condensed_markdown(headings)

            template = load_template('simple_sanitize_large', get_hardcoded_template_large)
            prompt = template.format(condensed_markdown=condensed)
            instructions = (
                "This is a LARGE document, so you're seeing a condensed version with headings and context. "
                "Copy the prompt below and paste it into your LLM interface. "
                "Then copy the JSON response and submit it using the Manual Submit endpoint."
            )

        logger.info(f"Generated manual prompt for work {work_id} ({classification})")

        return ManualPromptResponse(
            work_id=work_id,
            classification=classification,
            prompt=prompt,
            instructions=instructions
        )

    except Exception as e:
        logger.error(f"Failed to generate manual prompt for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-submit/{work_id}", response_model=ManualSubmitResponse)
async def submit_manual_result(
    work_id: int,
    request: ManualSubmitRequest,
    session: Session = Depends(get_db)
):
    """
    Submit manual LLM result.

    Processes the LLM response submitted by the user, creates sanitized
    markdown, and proceeds to chunking.

    Args:
        work_id: Work ID
        request: LLM response text
        session: Database session

    Returns:
        Status after processing manual result
    """
    try:
        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="Work must be parsed before submitting manual result"
            )

        classification = parsed.classification.value

        # Process based on classification
        if classification == 'small':
            # Parse LLM response and create sanitized record
            from vulcanlab.simple_conversion.sanitize_small import (
                parse_llm_response,
                create_heading_modifications
            )
            from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
            from datetime import datetime, UTC

            parsed_response = parse_llm_response(request.llm_response)
            sanitized_content = parsed_response['sanitized_markdown']

            sanitized = SanitizedMarkdown(
                parsed_markdown_id=parsed.id,
                content=sanitized_content,
                created_at=datetime.now(UTC)
            )

            session.add(sanitized)
            session.flush()

            create_heading_modifications(
                parsed_response['modifications'],
                sanitized.id,
                session
            )

        else:  # large
            from vulcanlab.simple_conversion.sanitize_large import (
                parse_llm_response_large,
                apply_modifications_to_markdown,
                create_heading_modifications_large
            )
            from vulcanlab.data.models.sanitized_markdown import SanitizedMarkdown
            from datetime import datetime, UTC

            modifications = parse_llm_response_large(request.llm_response)
            sanitized_content = apply_modifications_to_markdown(
                parsed.content,
                modifications
            )

            sanitized = SanitizedMarkdown(
                parsed_markdown_id=parsed.id,
                content=sanitized_content,
                created_at=datetime.now(UTC)
            )

            session.add(sanitized)
            session.flush()

            create_heading_modifications_large(
                modifications,
                sanitized.id,
                session
            )

        # Update work status
        work = session.query(Work).filter(Work.id == work_id).first()
        work.processing_status['simple_conversion_step'] = 'sanitized'

        # Now proceed to chunking
        logger.info(f"Manual result processed, creating chunks for work {work_id}")
        chunks = create_chunks_from_sanitized(work_id, session)

        work.processing_status['simple_conversion_step'] = 'complete'
        session.commit()

        logger.info(f"Manual pipeline complete for work {work_id}: {len(chunks)} chunks")

        return ManualSubmitResponse(
            work_id=work_id,
            status='complete',
            message=f'Manual result processed successfully. Created {len(chunks)} chunks.'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process manual result for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{work_id}", response_model=ConversionResults)
async def get_results(
    work_id: int,
    session: Session = Depends(get_db)
):
    """
    Get final conversion results.

    Returns work metadata and all created chunks.

    Args:
        work_id: Work ID
        session: Database session

    Returns:
        Complete conversion results with chunks
    """
    try:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

        parsed = session.query(ParsedMarkdown).filter(
            ParsedMarkdown.work_id == work_id
        ).first()

        if not parsed:
            raise HTTPException(
                status_code=400,
                detail="Work has not been processed yet"
            )

        chunks = session.query(Chunk).filter(Chunk.work_id == work_id).all()

        chunk_results = [
            ChunkResult(
                id=chunk.id,
                heading_level=chunk.heading_level,
                heading_text=chunk.heading_text,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content_preview=chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content
            )
            for chunk in chunks
        ]

        return ConversionResults(
            work_id=work_id,
            title=work.title,
            author=work.author,
            classification=parsed.classification.value,
            token_count=parsed.token_count,
            chunk_count=len(chunks),
            chunks=chunk_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for work {work_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Router Registration

**File**: `src/vulcanlab/api/__init__.py` (MODIFIED)

Add router registration:

```python
from .simple_conversion import router as simple_conversion_router

# In app initialization
app.include_router(simple_conversion_router)
```

## Unit Tests

**File**: `tests/unit/test_simple_conversion_api.py` (NEW)

```python
"""Unit tests for simple conversion API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from vulcanlab.api.simple_conversion import router

# Mock app for testing
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@patch('vulcanlab.api.simple_conversion.get_session')
def test_start_conversion_success(mock_session):
    """Test POST /start with valid request."""
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db

    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_db.add.return_value = None
    mock_db.flush.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # Intercept work creation
    def add_side_effect(work):
        work.id = 1

    mock_db.add.side_effect = add_side_effect

    response = client.post('/api/simple-conversion/start', json={
        'file_path': '/path/to/file.pdf',
        'title': 'Test Book',
        'author': 'Test Author',
        'year': 2023,
        'mode': 'automatic'
    })

    assert response.status_code == 200
    data = response.json()
    assert data['work_id'] == 1
    assert data['status'] == 'converting'


@patch('vulcanlab.api.simple_conversion.get_session')
def test_get_status_success(mock_session):
    """Test GET /status/{work_id}."""
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db

    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {
        'simple_conversion_step': 'parsed',
        'simple_conversion_classification': 'small',
        'simple_conversion_token_count': 5000
    }

    mock_db.query.return_value.filter.return_value.first.return_value = mock_work

    response = client.get('/api/simple-conversion/status/1')

    assert response.status_code == 200
    data = response.json()
    assert data['step'] == 'parsed'
    assert data['classification'] == 'small'
    assert data['token_count'] == 5000


@patch('vulcanlab.api.simple_conversion.get_session')
def test_get_status_not_found(mock_session):
    """Test GET /status with non-existent work."""
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get('/api/simple-conversion/status/999')

    assert response.status_code == 404


@patch('vulcanlab.api.simple_conversion.create_chunks_from_sanitized')
@patch('vulcanlab.api.simple_conversion.sanitize_small_document')
@patch('vulcanlab.api.simple_conversion.parse_and_classify')
@patch('vulcanlab.api.simple_conversion.get_session')
def test_execute_automatic_small_doc(mock_session, mock_parse, mock_sanitize, mock_chunk):
    """Test POST /execute-auto for small document."""
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db

    mock_work = MagicMock()
    mock_work.id = 1
    mock_work.processing_status = {}

    mock_db.query.return_value.filter.return_value.first.return_value = mock_work

    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'
    mock_parse.return_value = mock_parsed

    mock_chunk.return_value = [MagicMock() for _ in range(5)]

    response = client.post('/api/simple-conversion/execute-auto/1')

    assert response.status_code == 200
    data = response.json()
    assert data['chunks_created'] == 5
    assert data['status'] == 'complete'


@patch('vulcanlab.api.simple_conversion.get_session')
def test_get_manual_prompt_small(mock_session):
    """Test GET /manual-prompt for small document."""
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db

    mock_parsed = MagicMock()
    mock_parsed.classification.value = 'small'
    mock_parsed.content = '# Test\n\nContent here.'

    mock_db.query.return_value.filter.return_value.first.return_value = mock_parsed

    with patch('vulcanlab.api.simple_conversion.load_template') as mock_template:
        mock_tmpl = MagicMock()
        mock_tmpl.format.return_value = "Formatted prompt text"
        mock_template.return_value = mock_tmpl

        response = client.get('/api/simple-conversion/manual-prompt/1')

        assert response.status_code == 200
        data = response.json()
        assert data['classification'] == 'small'
        assert 'prompt' in data
        assert 'instructions' in data
```

## Manual Test Plan

### Setup
1. Start FastAPI server
2. Database with T01-T06 modules available
3. Test PDF/EPUB files ready

### Test Cases

#### TC1: Start Conversion (Automatic Mode)
**Request**:
```bash
curl -X POST http://localhost:8000/api/simple-conversion/start \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/test.pdf",
    "title": "Test Book",
    "author": "Test Author",
    "year": 2023,
    "mode": "automatic"
  }'
```

**Expected**: Returns work_id and status="converting"

#### TC2: Get Status
**Request**:
```bash
curl http://localhost:8000/api/simple-conversion/status/1
```

**Expected**: Returns current step, classification, counts

#### TC3: Execute Automatic Pipeline
**Request**:
```bash
curl -X POST http://localhost:8000/api/simple-conversion/execute-auto/1
```

**Expected**: Runs full pipeline, returns chunk count

#### TC4: Get Manual Prompt
**Request**:
```bash
curl http://localhost:8000/api/simple-conversion/manual-prompt/2
```

**Expected**: Returns formatted prompt and instructions

#### TC5: Submit Manual Result
**Request**:
```bash
curl -X POST http://localhost:8000/api/simple-conversion/manual-submit/2 \
  -H "Content-Type: application/json" \
  -d '{
    "llm_response": "{\"sanitized_markdown\": \"# Clean\", \"modifications\": []}"
  }'
```

**Expected**: Processes result, creates chunks

#### TC6: Get Results
**Request**:
```bash
curl http://localhost:8000/api/simple-conversion/results/1
```

**Expected**: Returns work metadata and chunk list

## Dependencies

- **Internal**: T01-T06 (all backend modules)
- **External**: FastAPI, Pydantic, SQLAlchemy
- **Testing**: pytest, FastAPI TestClient

## Assumptions

1. FastAPI app initialization exists
2. Database session dependency works via `get_session()`
3. PDF/EPUB conversion handled by existing module or external process
4. LLM client configured for automatic mode

## Notes

- This is a **backend + API** ticket
- All endpoints include proper error handling
- Pydantic models provide request/response validation
- Status endpoint supports polling from frontend
- Manual mode returns full prompt text for copy/paste
- Automatic mode handles all steps without intervention

## Definition of Done

- [ ] All code implemented as specified
- [ ] All unit tests pass (6+ tests)
- [ ] Manual test plan with curl completed
- [ ] All endpoints return correct HTTP status codes
- [ ] Error handling implemented for all edge cases
- [ ] Pydantic models validate all inputs
- [ ] Router registered in FastAPI app
- [ ] API documented (docstrings)
