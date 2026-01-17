"""
Unit tests for summarization settings endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from vulcanlab_api.main import app
from vulcanlab.data.models.summarize_settings import SummarizeSettings

client = TestClient(app)


class TestSummarizeRouterSettings:
    """Test suite for /api/v1/summarize/settings endpoints."""

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_get_settings_existing(self, mock_get_session):
        """Test getting existing settings."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        settings = SummarizeSettings(
            min_heading_word_count=600,
            max_total_heading_words=3000,
            dense_top_k=7,
            lexical_top_k=7,
            rrf_k=60,
            rrf_top_k=7,
            mmr_lambda=0.7,
            mmr_top_n=5,
            max_llm_calls=5,
            max_tokens_per_call=15000,
            tokens_per_word=0.75,
            h1_h2_min_chunks=2,
            h3_min_chunks=1
        )
        mock_session.execute.return_value.scalar_one_or_none.return_value = settings
        
        response = client.get("/api/v1/summarize/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["min_heading_word_count"] == 600
        assert data["max_total_heading_words"] == 3000

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_get_settings_create_default(self, mock_get_session):
        """Test that default settings are created if none exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Return None for first call, then a settings object with defaults
        def side_effect(settings_obj):
            settings_obj.min_heading_word_count = 500
            settings_obj.max_total_heading_words = 2500
            settings_obj.dense_top_k = 7
            settings_obj.lexical_top_k = 7
            settings_obj.rrf_k = 60
            settings_obj.rrf_top_k = 7
            settings_obj.mmr_lambda = 0.7
            settings_obj.mmr_top_n = 5
            settings_obj.max_llm_calls = 5
            settings_obj.max_tokens_per_call = 15000
            settings_obj.tokens_per_word = 0.75
            settings_obj.h1_h2_min_chunks = 2
            settings_obj.h3_min_chunks = 1
            
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_session.refresh.side_effect = side_effect
        
        response = client.get("/api/v1/summarize/settings")
        
        assert response.status_code == 200
        assert mock_session.add.called
        assert mock_session.commit.called

    @patch('vulcanlab_api.routers.summarize.get_session')
    def test_update_settings(self, mock_get_session):
        """Test updating settings."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        settings = SummarizeSettings()
        mock_session.execute.return_value.scalar_one_or_none.return_value = settings
        
        payload = {
            "min_heading_word_count": 400,
            "max_total_heading_words": 2000,
            "dense_top_k": 5,
            "lexical_top_k": 5,
            "rrf_k": 60,
            "rrf_top_k": 5,
            "mmr_lambda": 0.5,
            "mmr_top_n": 4,
            "max_llm_calls": 3,
            "max_tokens_per_call": 12000,
            "tokens_per_word": 0.8,
            "h1_h2_min_chunks": 3,
            "h3_min_chunks": 2
        }
        
        response = client.put("/api/v1/summarize/settings", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["min_heading_word_count"] == 400
        assert data["tokens_per_word"] == 0.8
        assert mock_session.commit.called
        
        # Verify settings object was updated
        assert settings.min_heading_word_count == 400
        assert settings.tokens_per_word == 0.8
