"""
Unit tests for automated research session API endpoints and background tasks.
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from contextlib import contextmanager

from vulcanlab_api.main import app
from vulcanlab.data.models.enums import SessionType, SessionStatus, ResearchPhase
from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.data.models.collection import Collection
from vulcanlab_api.routers.research_sessions import run_automated_research_task

client = TestClient(app)

@contextmanager
def mock_get_session_cm(db):
    yield db

@pytest.fixture
def mock_now():
    return datetime.now(timezone.utc)

@pytest.mark.asyncio
async def test_start_automated_session_success(mock_now):
    """Test starting an automated research session."""
    mock_collection = Collection(id=1, name="Test Collection")
    mock_session = ResearchSession(
        id=20,
        collection_id=1,
        session_type=SessionType.AUTOMATED,
        thread_id="auto_1_12345678",
        status=SessionStatus.IN_PROGRESS,
        current_phase=ResearchPhase.PLANNING,
        created_at=mock_now,
        updated_at=mock_now
    )

    with patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=mock_collection), \
         patch("vulcanlab_api.routers.research_sessions.core_create_research_session", return_value=mock_session), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()), \
         patch("vulcanlab_api.routers.research_sessions.BackgroundTasks.add_task") as mock_add_task:
        
        response = client.post(
            "/api/v1/research-sessions/start-automated",
            json={"collection_id": 1}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == 20
        assert data["thread_id"].startswith("auto_1_")
        assert data["status"] == "in_progress"
        
        # Verify background task was added
        mock_add_task.assert_called_once_with(
            ANY, # run_automated_research_task
            collection_id=1,
            session_id=20
        )

@pytest.mark.asyncio
async def test_start_automated_session_collection_not_found():
    """Test starting automated research for non-existent collection."""
    with patch("vulcanlab_api.routers.research_sessions.core_get_collection", return_value=None), \
         patch("vulcanlab_api.routers.research_sessions.get_db_session", return_value=MagicMock()):
        
        response = client.post(
            "/api/v1/research-sessions/start-automated",
            json={"collection_id": 999}
        )
        assert response.status_code == 404
        assert "Collection 999 not found" in response.json()["detail"]

def test_run_automated_research_task_success():
    """Test the background task success path."""
    mock_db = MagicMock()
    
    with patch("vulcanlab_api.routers.research_sessions.get_session", new_callable=MagicMock) as mock_get_session, \
         patch("vulcanlab_api.routers.research_sessions.start_automated_research") as mock_start:
        
        mock_get_session.side_effect = lambda: mock_get_session_cm(mock_db)
        
        run_automated_research_task(collection_id=1, session_id=20)
        
        mock_start.assert_called_once_with(
            collection_id=1,
            session=mock_db,
            session_id=20
        )

def test_run_automated_research_task_failure():
    """Test the background task failure path."""
    mock_db = MagicMock()
    
    with patch("vulcanlab_api.routers.research_sessions.get_session", new_callable=MagicMock) as mock_get_session, \
         patch("vulcanlab_api.routers.research_sessions.start_automated_research", side_effect=Exception("Test error")), \
         patch("vulcanlab_api.routers.research_sessions.core_update_research_session") as mock_update:
        
        mock_get_session.side_effect = lambda: mock_get_session_cm(mock_db)
        
        run_automated_research_task(collection_id=1, session_id=20)
        
        # Verify status update to FAILED
        mock_update.assert_called_once_with(
            mock_db,
            20,
            {
                "status": SessionStatus.FAILED,
                "state_data": {"error": "Test error"}
            }
        )
        mock_db.commit.assert_called()
