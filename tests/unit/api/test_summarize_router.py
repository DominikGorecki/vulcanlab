import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from vulcanlab_api.main import app
from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.summary_node import SummaryNode
from vulcanlab.data.models.work_summary import WorkSummary, WorkSummaryType
from vulcanlab.summarize.orchestrator import SummarizationStatus, SummarizationProgress

client = TestClient(app)

# Mock dependency
@pytest.fixture
def mock_db():
    mock = MagicMock(spec=Session)
    yield mock

@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db_session] = lambda: mock_db
    yield
    app.dependency_overrides.pop(get_db_session)

@pytest.mark.usefixtures("override_get_db")
class TestSummarizeRouter:

    def test_trigger_summarization_work_not_found(self, mock_db):
        mock_db.get.return_value = None
        
        response = client.post("/api/v1/summarize/999")
        
        assert response.status_code == 404
        assert "Work 999 not found" in response.json()["detail"]

    @patch("vulcanlab_api.routers.summarize.orchestrator")
    def test_trigger_summarization_success(self, mock_orchestrator, mock_db):
        mock_db.get.return_value = Work(id=1, title="Test Work")
        mock_orchestrator.get_summarization_status.return_value = None
        mock_orchestrator.summarize_work.return_value = SummarizationProgress(
            work_id=1,
            status=SummarizationStatus.COMPLETED,
            total_nodes=5,
            completed_nodes=5
        )
        
        response = client.post("/api/v1/summarize/1")
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        mock_orchestrator.summarize_work.assert_called_once_with(1, mock_db, force_regenerate=False)

    @patch("vulcanlab_api.routers.summarize.orchestrator")
    def test_trigger_summarization_force(self, mock_orchestrator, mock_db):
        mock_db.get.return_value = Work(id=1, title="Test Work")
        mock_orchestrator.summarize_work.return_value = SummarizationProgress(
            work_id=1,
            status=SummarizationStatus.COMPLETED,
            total_nodes=5,
            completed_nodes=5
        )
        
        response = client.post("/api/v1/summarize/1?force=true")
        
        assert response.status_code == 200
        mock_orchestrator.summarize_work.assert_called_once_with(1, mock_db, force_regenerate=True)

    @patch("vulcanlab_api.routers.summarize.orchestrator")
    def test_get_status_success(self, mock_orchestrator, mock_db):
        mock_orchestrator.get_summarization_status.return_value = SummarizationProgress(
            work_id=1,
            status=SummarizationStatus.IN_PROGRESS,
            total_nodes=10,
            completed_nodes=4
        )
        
        response = client.get("/api/v1/summarize/1/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["total_nodes"] == 10
        assert data["completed_nodes"] == 4

    @patch("vulcanlab_api.routers.summarize.orchestrator")
    def test_get_status_not_found(self, mock_orchestrator, mock_db):
        mock_orchestrator.get_summarization_status.return_value = None
        
        response = client.get("/api/v1/summarize/1/status")
        
        assert response.status_code == 404

    @patch("vulcanlab_api.routers.summarize.compile")
    def test_get_nodes_success(self, mock_compile, mock_db):
        mock_node = SummaryNode(
            id=1, chunk_id=1, work_id=1, gist="Test gist",
            key_points=[], definitions=[], key_terms=[], examples=[],
            start_line=1, end_line=10, salience_score=0.8
        )
        mock_compile.load_summary_nodes.return_value = [mock_node]
        
        response = client.get("/api/v1/summarize/1/nodes")
        
        assert response.status_code == 200
        assert len(response.json()["nodes"]) == 1
        assert response.json()["nodes"][0]["gist"] == "Test gist"

    @patch("vulcanlab_api.routers.summarize.compile")
    def test_derive_output_no_nodes(self, mock_compile, mock_db):
        mock_compile.load_summary_nodes.return_value = []
        
        response = client.post("/api/v1/summarize/1/derive", json={"type": "outline"})
        
        assert response.status_code == 400
        assert "No summary nodes found" in response.json()["detail"]

    @patch("vulcanlab_api.routers.summarize.compile")
    def test_derive_output_success(self, mock_compile, mock_db):
        mock_compile.load_summary_nodes.return_value = [MagicMock()]
        mock_summary = WorkSummary(
            id=1, work_id=1, type=WorkSummaryType.OUTLINE,
            content={"outline": []}, line_references=[]
        )
        mock_compile.generate_derived_output.return_value = mock_summary
        
        response = client.post("/api/v1/summarize/1/derive", json={"type": "outline"})
        
        assert response.status_code == 200
        assert response.json()["type"] == "outline"
        mock_db.commit.assert_called_once()

    @patch("vulcanlab_api.routers.summarize.compile")
    def test_get_summaries_success(self, mock_compile, mock_db):
        mock_summary = WorkSummary(
            id=1, work_id=1, type=WorkSummaryType.ABSTRACT,
            content={"abstract": "Test"}, line_references=[]
        )
        mock_compile.get_derived_outputs.return_value = [mock_summary]
        
        response = client.get("/api/v1/summarize/1/summaries")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["type"] == "abstract"

    def test_list_summarized_works(self, mock_db):
        # Mock result from complex query
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(id=1, title="Work 1", node_count=5),
            MagicMock(id=2, title="Work 2", node_count=3)
        ]
        mock_db.execute.return_value = mock_result
        
        # Second call for summary types - we'll just return empty lists for simplicity in mock
        # To be more precise, we'd need multiple execute side effects
        mock_db.execute.side_effect = [
            mock_result, # first call for works
            MagicMock(scalars=lambda: MagicMock(all=lambda: ["abstract"])), # work 1
            MagicMock(scalars=lambda: MagicMock(all=lambda: ["outline"])) # work 2
        ]
        
        response = client.get("/api/v1/summarize/works")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["works"]) == 2
        assert data["works"][0]["title"] == "Work 1"
        assert data["works"][0]["summaries"] == ["abstract"]

    @patch("vulcanlab_api.routers.summarize.orchestrator")
    def test_delete_summaries_success(self, mock_orchestrator, mock_db):
        response = client.delete("/api/v1/summarize/1")
        
        assert response.status_code == 200
        assert "Summaries deleted" in response.json()["message"]
        mock_orchestrator.delete_existing_summaries.assert_called_once_with(1, mock_db)
