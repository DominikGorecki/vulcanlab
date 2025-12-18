"""Unit tests for reranker integration in retrieve.py.

Tests the integration of the singleton reranker module with the retrieve pipeline,
verifying that _rerank_chunks() correctly uses get_reranker() and maintains
expected behavior.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import torch

from src.vulcanlab.retrieval.retrieve import _rerank_chunks, RetrievedChunk


class TestRerankChunksIntegration:
    """Tests for _rerank_chunks() integration with singleton reranker."""

    def test_rerank_chunks_produces_valid_scores(self):
        """Test _rerank_chunks() still produces valid rerank scores with singleton reranker."""
        # Create test chunks
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test content 1",
                enriched_content="Enriched content 1", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
            RetrievedChunk(
                id=2, parent_id=None, work_id=1, content="Test content 2",
                enriched_content="Enriched content 2", start_line=6, end_line=10,
                level="H2", heading_breadcrumbs="Chapter 1 > Section 1"
            ),
        ]

        # Mock the singleton reranker
        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            # Setup tokenizer mock
            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            # Setup model mock to return scores
            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = [0.85, 0.92]
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            # Call function
            result = _rerank_chunks("test query", chunks)

            # Verify scores were set
            assert result[0].rerank_score == 0.85
            assert result[1].rerank_score == 0.92
            assert all(isinstance(chunk.rerank_score, float) for chunk in result)

    def test_rerank_chunks_calls_get_reranker_once(self):
        """Test _rerank_chunks() calls get_reranker() exactly once per invocation."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.85
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            _rerank_chunks("test query", chunks)

            # Verify get_reranker called exactly once
            mock_get_reranker.assert_called_once()

    def test_multiple_rerank_calls_reuse_singleton(self):
        """Test multiple calls to _rerank_chunks() in same process reuse singleton."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.85
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            # Make multiple calls
            _rerank_chunks("query 1", chunks)
            _rerank_chunks("query 2", chunks)
            _rerank_chunks("query 3", chunks)

            # Verify get_reranker called multiple times (once per call)
            # Note: The singleton caching happens inside get_reranker(), not in _rerank_chunks()
            assert mock_get_reranker.call_count == 3

    def test_error_propagation_from_get_reranker(self):
        """Test if get_reranker() raises RuntimeError, _rerank_chunks() propagates it."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            # Simulate get_reranker() raising RuntimeError
            mock_get_reranker.side_effect = RuntimeError("Failed to initialize reranker model")

            # Verify error propagates
            with pytest.raises(RuntimeError) as exc_info:
                _rerank_chunks("test query", chunks)

            assert "Failed to initialize reranker model" in str(exc_info.value)

    def test_device_handling_from_get_reranker(self):
        """Test device from get_reranker() used correctly in tokenizer calls."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        # Test with CUDA device
        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cuda"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.85
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            _rerank_chunks("test query", chunks)

            # Verify device used in .to() call
            mock_inputs.to.assert_called_with("cuda")

    def test_empty_chunks_returns_empty(self):
        """Test _rerank_chunks() with empty chunks list returns empty list."""
        result = _rerank_chunks("test query", [])
        assert result == []

    def test_single_chunk_handling(self):
        """Test _rerank_chunks() handles single chunk correctly (batch_scores as float)."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            # Return a float (single item case)
            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.95
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            result = _rerank_chunks("test query", chunks)

            # Verify single score handled correctly
            assert len(result) == 1
            assert result[0].rerank_score == 0.95

    def test_batch_processing(self):
        """Test _rerank_chunks() processes chunks in batches correctly."""
        # Create 20 chunks to test batch processing (default batch_size=8)
        chunks = [
            RetrievedChunk(
                id=i, parent_id=None, work_id=1, content=f"Test {i}",
                enriched_content=f"Enriched {i}", start_line=i, end_line=i+1,
                level="H1", heading_breadcrumbs=f"Chapter {i}"
            )
            for i in range(20)
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            # Mock to return scores for each batch
            mock_outputs = MagicMock()
            # Will be called 3 times: batch of 8, batch of 8, batch of 4
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.side_effect = [
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],  # First batch
                [0.11, 0.21, 0.31, 0.41, 0.51, 0.61, 0.71, 0.81],  # Second batch
                [0.12, 0.22, 0.32, 0.42],  # Third batch
            ]
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            result = _rerank_chunks("test query", chunks, batch_size=8)

            # Verify all chunks have scores
            assert len(result) == 20
            assert all(hasattr(chunk, 'rerank_score') for chunk in result)
            assert all(chunk.rerank_score is not None for chunk in result)

    def test_tokenizer_parameters(self):
        """Test _rerank_chunks() passes correct parameters to tokenizer."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.85
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            _rerank_chunks("test query", chunks, max_length=1024)

            # Verify tokenizer called with correct parameters
            mock_tokenizer.assert_called_once()
            call_args = mock_tokenizer.call_args
            assert call_args.kwargs['padding'] is True
            assert call_args.kwargs['truncation'] is True
            assert call_args.kwargs['max_length'] == 1024
            assert call_args.kwargs['return_tensors'] == "pt"

    def test_no_grad_context_used(self):
        """Test _rerank_chunks() uses torch.no_grad() context for inference."""
        chunks = [
            RetrievedChunk(
                id=1, parent_id=None, work_id=1, content="Test",
                enriched_content="Test enriched", start_line=1, end_line=5,
                level="H1", heading_breadcrumbs="Chapter 1"
            ),
        ]

        with patch('src.vulcanlab.retrieval.retrieve.get_reranker') as mock_get_reranker:
            mock_tokenizer = MagicMock()
            mock_model = MagicMock()
            device = "cpu"

            mock_inputs = MagicMock()
            mock_inputs.to.return_value = mock_inputs
            mock_tokenizer.return_value = mock_inputs

            mock_outputs = MagicMock()
            mock_outputs.logits.squeeze.return_value.cpu.return_value.tolist.return_value = 0.85
            mock_model.return_value = mock_outputs

            mock_get_reranker.return_value = (mock_tokenizer, mock_model, device)

            # Patch torch.no_grad to verify it's used
            with patch('torch.no_grad') as mock_no_grad:
                mock_context = MagicMock()
                mock_no_grad.return_value.__enter__ = MagicMock(return_value=mock_context)
                mock_no_grad.return_value.__exit__ = MagicMock(return_value=False)

                _rerank_chunks("test query", chunks)

                # Verify no_grad was called
                mock_no_grad.assert_called_once()
