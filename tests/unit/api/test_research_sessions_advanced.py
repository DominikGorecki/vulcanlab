"""
Unit tests for advanced research session API endpoints (context, match-results, resume).
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from vulcanlab_api.main import app
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.research_section import ResearchSection
from vulcanlab.data.models.collection import Collection

client = TestClient(app)

@pytest.fixture
def mock_now():
    return datetime.now(timezone.utc)

@pytest.fixture
def mock_session_obj(mock_now):
    return ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.MANUAL,
        thread_id="manual_123",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        research_plan={"sub_questions": [{"id": "Q1", "question": "What?"}]},
        state_data={},
        created_at=mock_now,
        updated_at=mock_now
    )

@pytest.fixture
def mock_collection():
    return Collection(id=1, name="Test Collection")

@pytest.mark.asyncio
async def test_assemble_context_success(mock_session_obj, mock_collection):
    """Test assembling context for a question."""
    mock_result = {
        "context": "Assembled content",
        "token_count": 100,
        "sources": [{"item_id": 1, "type": "excerpt"}]
    }

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.assemble_context_for_question", return_value=mock_result), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/context",
            json={"question_id": "Q1", "relevant_item_ids": [1, 2, 3]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["context"] == "Assembled content"
        assert data["token_count"] == 100
        assert len(data["sources"]) == 1

@pytest.mark.asyncio
async def test_assemble_context_reuse(mock_session_obj, mock_collection):
    """Test assembling context with reuse_info from state_data."""
    mock_session_obj.state_data = {
        "reuse_info": {
            "Q1": {"strategy": "exact_reuse", "source_result_ids": [50]}
        }
    }
    
    mock_result = {
        "context": "Reused content",
        "token_count": 50,
        "sources": [{"item_id": None, "type": "research_result"}]
    }

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.assemble_context_for_question", return_value=mock_result) as mock_assemble, \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/context",
            json={"question_id": "Q1", "relevant_item_ids": []}
        )
        
        assert response.status_code == 200
        # Verify reuse_info was passed correctly
        mock_assemble.assert_called_once()
        args, kwargs = mock_assemble.call_args
        assert kwargs["reuse_info"] == {"strategy": "exact_reuse", "source_result_ids": [50]}

@pytest.mark.asyncio
async def test_match_results_success(mock_session_obj, mock_collection):
    """Test matching results for a question."""
    mock_matches = [
        {"result_id": 50, "similarity": 0.95, "quality_score": 0.8, "result_preview": "Prev"}
    ]

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.match_results_for_question", return_value=mock_matches), \
         patch("vulcanlab_api.routers.research_sessions.recommend_reuse_strategy", return_value="exact_reuse"), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/match-results",
            json={"question_id": "Q1", "question_text": "What is this?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["matched_results"]) == 1
        assert data["recommended_strategy"] == "exact_reuse"

@pytest.mark.asyncio
async def test_resume_session_planning(mock_session_obj, mock_collection):
    """Test resuming a session in planning phase."""
    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post("/api/v1/research-sessions/10/resume", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "planning"
        assert data["next_step"]["step"] == "result_matching"
        assert data["next_step"]["question_id"] == "Q1"

@pytest.mark.asyncio
async def test_resume_session_research(mock_session_obj, mock_collection):
    """Test resuming a session in research phase."""
    mock_session_obj.current_phase = ResearchPhase.RESEARCH
    mock_session_obj.research_plan = {
        "sub_questions": [
            {"id": "Q1", "question": "Q1?"},
            {"id": "Q2", "question": "Q2?"}
        ]
    }
    
    # Q1 is already completed
    mock_sections = [
        ResearchSection(id=100, session_id=10, question_id="Q1", question_text="Q1?")
    ]

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_get_research_sections", return_value=mock_sections), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post("/api/v1/research-sessions/10/resume", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "research"
        assert data["next_step"]["step"] == "section_generation"
        assert data["next_step"]["question_id"] == "Q2"

@pytest.mark.asyncio
async def test_resume_session_mode_switch(mock_session_obj, mock_collection):
    """Test resuming a session with a mode switch."""
    assert mock_session_obj.session_type == SessionType.MANUAL
    
    # Mock update to return automated session
    automated_session = ResearchSession(
        id=10,
        collection_id=1,
        session_type=SessionType.AUTOMATED,
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        research_plan={"sub_questions": [{"id": "Q1"}]}
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", side_effect=[mock_session_obj, automated_session]), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_update_research_session") as mock_update, \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/10/resume",
            json={"mode": "automated"}
        )
        
        assert response.status_code == 200
        mock_update.assert_called_once_with(ANY, 10, {"session_type": SessionType.AUTOMATED})

@pytest.mark.asyncio
async def test_endpoints_authorization(mock_session_obj):
    """Test that endpoints enforce authorization (collection access)."""
    # Mock collection access to fail
    with patch("vulcanlab_api.routers.research_sessions.core_get_research_session", return_value=mock_session_obj), \
         patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=None), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        # Test context
        response = client.post("/api/v1/research-sessions/10/context", json={"question_id": "Q1", "relevant_item_ids": []})
        assert response.status_code == 404
        assert "Collection 1 not found" in response.json()["detail"]
        
        # Test match-results
        response = client.post("/api/v1/research-sessions/10/match-results", json={"question_id": "Q1", "question_text": "text"})
        assert response.status_code == 404
        
        # Test resume
        response = client.post("/api/v1/research-sessions/10/resume", json={})
        assert response.status_code == 404
