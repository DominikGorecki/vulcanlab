"""
Unit tests for summarization API router.
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from vulcanlab_api.main import app
from vulcanlab.summarization.heading_selector import HeadingInfo
from vulcanlab.summarization.chunk_ranker import RankedChunk
from vulcanlab.summarization.prompt_generator import PromptBatch, HeadingWithChunks
from vulcanlab.data.models.work import Work
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab.data.models.chunk import Chunk

client = TestClient(app)


class TestSummarizeRouter:
    """Test suite for /api/v1/summarize endpoints."""

    @patch('vulcanlab_api.routers.summarize.get_session')
    @patch('vulcanlab_api.routers.summarize.select_headings_for_summarization')
    @patch('vulcanlab_api.routers.summarize.rank_content_chunks')
    def test_prepare_success(self, mock_rank, mock_select, mock_get_session):
        """Test successful preparation returns 200 and stores rankings."""
        # Mock session
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock Work
        mock_work = MagicMock(spec=Work)
        mock_work.id = 1
        mock_session.get.return_value = mock_work
        
        # Mock Chunk existence check
        mock_session.execute.return_value.scalar.return_value = 1
        
        # Mock Settings
        mock_settings = SummarizeSettings(id=1, tokens_per_word=0.75, max_tokens_per_call=10000, max_llm_calls=5)
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_settings
        
        # Mock Headings
        headings = [
            HeadingInfo(chunk_id=10, level="H1", start_line=1, end_line=100, content_word_count=1000, heading_title="Title 1"),
            HeadingInfo(chunk_id=20, level="H2", start_line=101, end_line=200, content_word_count=800, heading_title="Title 2"),
        ]
        mock_select.return_value = headings
        
        # Mock Ranking
        mock_rank.side_effect = [
            [RankedChunk(chunk_id=11, content="C1", word_count=100, start_line=2, end_line=10, rank_position=1)],
            [RankedChunk(chunk_id=21, content="C2", word_count=100, start_line=102, end_line=110, rank_position=1)],
        ]
        
        # Mock SummaryResult check
        mock_session.execute.return_value.scalar.side_effect = [1, None] # 1 for chunk check, None for existing summaries

        # Make request
        response = client.post("/api/v1/summarize/works/1/prepare")

        assert response.status_code == 200
        data = response.json()
        
        assert len(data["headings"]) == 2
        assert data["total_prompts"] > 0
        assert data["estimated_tokens"] > 0
        assert data["has_existing_summaries"] is False
        
        # Verify storage calls
        assert mock_session.add.call_count >= 2 # 2 SummaryChunks
        mock_session.commit.assert_called_once()

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_prepare_work_not_found(self, mock_get_session):
        """Test prepare returns 404 when work not found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None

        response = client.post("/api/v1/summarize/works/999/prepare")
        assert response.status_code == 404

    @patch('vulcanlab_api.routers.summarize.get_session')
    @patch('vulcanlab_api.routers.summarize.select_headings_for_summarization')
    @patch('vulcanlab_api.routers.summarize.rank_content_chunks')
    @patch('vulcanlab_api.routers.summarize.assemble_prompts')
    def test_generate_prompts_success(self, mock_assemble, mock_rank, mock_select, mock_get_session):
        """Test successful prompt generation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock Work
        mock_work = MagicMock(spec=Work)
        mock_work.id = 1
        mock_session.get.return_value = mock_work
        
        # Mock Settings
        mock_settings = SummarizeSettings(id=1, tokens_per_word=0.75, max_tokens_per_call=10000, max_llm_calls=5)
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_settings
        
        # Mock SummaryChunks and Chunks join
        mock_sc = MagicMock()
        mock_sc.heading_chunk_id = 10
        mock_sc.rank_position = 1
        mock_sc.word_count = 100
        
        mock_chunk = MagicMock(spec=Chunk)
        mock_chunk.id = 11
        mock_chunk.content = "Some content"
        mock_chunk.start_line = 2
        mock_chunk.end_line = 10
        
        mock_session.execute.return_value.all.return_value = [(mock_sc, mock_chunk)]
        
        # Mock all headings for context
        headings = [
            HeadingInfo(chunk_id=10, level="H1", start_line=1, end_line=100, content_word_count=1000, heading_title="Title 1"),
        ]
        mock_select.return_value = headings
        
        # Mock assemble_prompts
        mock_assemble.return_value = [
            PromptBatch(prompt_index=0, content="Prompt text", heading_ids=[10], estimated_tokens=100)
        ]

        # Make request
        response = client.post("/api/v1/summarize/works/1/generate-prompts", json={"regenerate_all": False})

        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["prompt_index"] == 0
        assert data["prompts"][0]["content"] == "Prompt text"
        assert data["prompts"][0]["heading_ids"] == [10]
        
        # Verify update call for prompt_index
        assert mock_session.execute.called

    @patch('vulcanlab_api.routers.summarize.get_session')
    @patch('vulcanlab_api.routers.summarize.delete_existing_summaries')
    @patch('vulcanlab_api.routers.summarize.select_headings_for_summarization')
    @patch('vulcanlab_api.routers.summarize.rank_content_chunks')
    @patch('vulcanlab_api.routers.summarize.assemble_prompts')
    def test_generate_prompts_regenerate_true(self, mock_assemble, mock_rank, mock_select, mock_delete, mock_get_session):
        """Test regeneration deletes existing and re-runs preparation logic."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_work = MagicMock(spec=Work)
        mock_work.id = 1
        mock_session.get.return_value = mock_work
        
        mock_settings = SummarizeSettings(
            tokens_per_word=0.75,
            max_tokens_per_call=10000,
            max_llm_calls=5,
            h1_h2_min_chunks=2,
            h3_min_chunks=1
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_settings
        
        # Mock selection and ranking (re-run logic)
        mock_select.return_value = [HeadingInfo(chunk_id=10, level="H1", start_line=1, end_line=100, content_word_count=1000, heading_title="T1")]
        mock_rank.return_value = [RankedChunk(chunk_id=11, content="C1", word_count=100, start_line=2, end_line=10, rank_position=1)]
        mock_assemble.return_value = [PromptBatch(prompt_index=0, content="P1", heading_ids=[10], estimated_tokens=50)]

        response = client.post("/api/v1/summarize/works/1/generate-prompts", json={"regenerate_all": True})
        
        if response.status_code != 200:
            print(f"Response error: {response.json()}")

        assert response.status_code == 200
        mock_delete.assert_called_once_with(1, ANY)
        assert mock_select.called
        assert mock_rank.called
        assert mock_session.execute.called # Should have called update for prompt_index