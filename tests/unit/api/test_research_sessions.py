"""
Unit tests for research session API endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from vulcanlab_api.main import app
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase, QualityStatus
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.research_section import ResearchSection
from vulcanlab.data.models.research_report import ResearchReport
from vulcanlab.data.models.collection import Collection

client = TestClient(app)

@pytest.fixture
def mock_now():
    return datetime.now(timezone.utc)

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.mark.asyncio
async def test_create_session_success(mock_now):
    """Test creating a research session."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.MANUAL,
        thread_id="manual_12345_abc",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        created_at=mock_now,
        updated_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_create_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions",
            json={"collection_id": 1, "session_type": "manual"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 10
        assert data["session_type"] == "manual"
        assert data["thread_id"] == "manual_12345_abc"

@pytest.mark.asyncio
async def test_create_session_invalid_type():
    """Test creating a session with invalid type."""
    response = client.post(
        "/api/v1/research-sessions",
        json={"collection_id": 1, "session_type": "invalid_type"}
    )
    # This should be caught by our manual check in the router since it's not a Pydantic enum yet in the request schema
    assert response.status_code == 400
    assert "Invalid session_type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_session_success(mock_now):
    """Test retrieving a research session."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.MANUAL,
        thread_id="manual_12345_abc",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        created_at=mock_now,
        updated_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.get("/api/v1/research-sessions/10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 10
        assert data["thread_id"] == "manual_12345_abc"

@pytest.mark.asyncio
async def test_get_session_not_found():
    """Test retrieving a non-existent session."""
    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=None), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.get("/api/v1/research-sessions/999")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_session_success(mock_now):
    """Test updating a research session."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.MANUAL,
        thread_id="manual_12345_abc",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        created_at=mock_now,
        updated_at=mock_now
    )
    
    updated_session = ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.MANUAL,
        thread_id="manual_12345_abc",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.RESEARCH,
        created_at=mock_now,
        updated_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_update_research_session", return_value=updated_session), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.put(
            "/api/v1/research-sessions/10",
            json={"current_phase": "research"}
        )
        
        assert response.status_code == 200
        assert response.json()["current_phase"] == "research"

@pytest.mark.asyncio
async def test_list_collection_sessions(mock_now):
    """Test listing sessions for a collection."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_sessions = [
        ResearchSession(id=10, collection_id=1, session_type=SessionType.MANUAL, thread_id="t1", status=SessionStatus.IN_PROGRESS, created_at=mock_now, updated_at=mock_now),
        ResearchSession(id=11, collection_id=1, session_type=SessionType.AUTOMATED, thread_id="t2", status=SessionStatus.COMPLETED, created_at=mock_now, updated_at=mock_now)
    ]

    with patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_list_research_sessions", return_value=mock_sessions), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.get("/api/v1/collections/1/research-sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 2
        assert data["sessions"][0]["id"] == 10
        assert data["sessions"][1]["id"] == 11

@pytest.mark.asyncio
async def test_save_section_success(mock_now):
    """Test saving a research section."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(id=10, collection_id=1, session_type=SessionType.MANUAL, thread_id="t1", status=SessionStatus.IN_PROGRESS, created_at=mock_now, updated_at=mock_now)
    mock_section = ResearchSection(
        id=100,
        session_id=10,
        question_id="Q1",
        question_text="What is this?",
        section_content="Content",
        quality_status=QualityStatus.PENDING,
        created_at=mock_now,
        updated_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_create_research_section", return_value=mock_section), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/sections",
            json={"question_id": "Q1", "question_text": "What is this?", "section_content": "Content"}
        )
        
        assert response.status_code == 201
        assert response.json()["id"] == 100
        assert response.json()["question_id"] == "Q1"

@pytest.mark.asyncio
async def test_list_sections_success(mock_now):
    """Test listing sections for a session."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(id=10, collection_id=1, session_type=SessionType.MANUAL, thread_id="t1", status=SessionStatus.IN_PROGRESS, created_at=mock_now, updated_at=mock_now)
    mock_sections = [
        ResearchSection(id=100, session_id=10, question_id="Q1", question_text="Q1?", quality_status=QualityStatus.PENDING, created_at=mock_now, updated_at=mock_now),
        ResearchSection(id=101, session_id=10, question_id="Q2", question_text="Q2?", quality_status=QualityStatus.PASS, created_at=mock_now, updated_at=mock_now)
    ]

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_get_research_sections", return_value=mock_sections), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.get("/api/v1/research-sessions/10/sections")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sections"]) == 2
        assert data["sections"][0]["question_id"] == "Q1"
        assert data["sections"][1]["question_id"] == "Q2"

@pytest.mark.asyncio
async def test_save_report_success(mock_now):
    """Test saving a research report."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(id=10, collection_id=1, session_type=SessionType.MANUAL, thread_id="t1", status=SessionStatus.IN_PROGRESS, created_at=mock_now, updated_at=mock_now)
    mock_report = ResearchReport(
        id=500,
        session_id=10,
        report_content="Full report",
        version=1,
        created_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_create_research_report", return_value=mock_report), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/report",
            json={"report_content": "Full report"}
        )
        
        assert response.status_code == 201
        assert response.json()["id"] == 500
        assert response.json()["report_content"] == "Full report"

@pytest.mark.asyncio
async def test_get_report_success(mock_now):
    """Test retrieving a research report."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(id=10, collection_id=1, session_type=SessionType.MANUAL, thread_id="t1", status=SessionStatus.IN_PROGRESS, created_at=mock_now, updated_at=mock_now)
    mock_report = ResearchReport(
        id=500,
        session_id=10,
        report_content="Full report",
        version=1,
        created_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_get_research_report", return_value=mock_report), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.get("/api/v1/research-sessions/10/report")
        
        assert response.status_code == 200
        assert response.json()["id"] == 500
        assert response.json()["report_content"] == "Full report"
