"""Unit tests for singleton reranker module."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import torch

from src.vulcanlab.retrieval import reranker


class TestGetReranker:
    """Tests for get_reranker() function."""

    def test_first_call_returns_valid_tuple(self):
        """Test that first call returns valid (tokenizer, model, device) tuple with all non-None values."""
        # Reset cache before test
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                # Setup mocks
                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                # Call function
                result = reranker.get_reranker()

                # Verify result is a tuple with 3 elements
                assert isinstance(result, tuple)
                assert len(result) == 3

                # Verify all elements are non-None
                tokenizer, model, device = result
                assert tokenizer is not None
                assert model is not None
                assert device is not None

    def test_model_is_correct_type(self):
        """Test model is instance of AutoModelForSequenceClassification."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                _, model, _ = reranker.get_reranker()

                # Verify from_pretrained was called
                mock_model_class.from_pretrained.assert_called_once()

    def test_tokenizer_is_correct_type(self):
        """Test tokenizer is instance of AutoTokenizer."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                tokenizer, _, _ = reranker.get_reranker()

                # Verify from_pretrained was called
                mock_tokenizer_class.from_pretrained.assert_called_once_with("BAAI/bge-reranker-large")

    def test_device_is_cuda_or_cpu(self):
        """Test device is either 'cuda' or 'cpu' string."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=True):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                _, _, device = reranker.get_reranker()

                assert isinstance(device, str)
                assert device in ("cuda", "cpu")

    def test_subsequent_calls_return_cached_instance(self):
        """Test subsequent calls return same cached instance."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                # First call
                result1 = reranker.get_reranker()

                # Second call
                result2 = reranker.get_reranker()

                # Verify same instance returned (object identity)
                assert result1 is result2

    def test_singleton_persists_multiple_calls(self):
        """Test singleton persists across 3+ calls with identical object IDs."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                # Multiple calls
                result1 = reranker.get_reranker()
                result2 = reranker.get_reranker()
                result3 = reranker.get_reranker()
                result4 = reranker.get_reranker()

                # Verify all return identical objects via id() comparison
                assert id(result1) == id(result2) == id(result3) == id(result4)

    def test_device_selection_cuda_available(self):
        """Test device selection when CUDA available."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=True):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                _, _, device = reranker.get_reranker()

                assert device == "cuda"
                # Verify float16 used for CUDA
                mock_model_class.from_pretrained.assert_called_once_with(
                    "BAAI/bge-reranker-large",
                    torch_dtype=torch.float16
                )

    def test_device_selection_cuda_unavailable(self):
        """Test device selection when CUDA unavailable."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                _, _, device = reranker.get_reranker()

                assert device == "cpu"
                # Verify float16 not used for CPU
                mock_model_class.from_pretrained.assert_called_once_with("BAAI/bge-reranker-large")

    def test_error_handling_model_load_failure(self):
        """Test error handling when model loading fails."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer_class.from_pretrained.return_value = MagicMock()
                # Simulate model loading failure
                mock_model_class.from_pretrained.side_effect = Exception("Model download failed")

                # Verify RuntimeError raised with context
                with pytest.raises(RuntimeError) as exc_info:
                    reranker.get_reranker()

                assert "Failed to initialize reranker model" in str(exc_info.value)
                assert "BAAI/bge-reranker-large" in str(exc_info.value)

    def test_cache_isolation_model_state(self):
        """Test cache isolation: modifying returned model doesn't affect cache."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                # First call
                _, model1, _ = reranker.get_reranker()

                # Modify model state (simulate training mode)
                model1.train = MagicMock()
                model1.train()

                # Second call should still return cached instance
                _, model2, _ = reranker.get_reranker()

                # Verify same cached instance returned
                assert model1 is model2

    def test_debug_logging_toggle(self):
        """Test debug logging toggle for cache hits."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch.object(reranker, 'DEBUG_LOG_CACHE_HITS', True):
                with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                     patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                     patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False), \
                     patch('src.vulcanlab.retrieval.reranker.logger') as mock_logger:

                    mock_tokenizer = MagicMock()
                    mock_model = MagicMock()
                    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                    mock_model_class.from_pretrained.return_value = mock_model
                    mock_model.to.return_value = mock_model
                    mock_model.eval.return_value = mock_model

                    # First call (initialization)
                    reranker.get_reranker()

                    # Second call (cache hit)
                    reranker.get_reranker()

                    # Verify debug log called on cache hit
                    mock_logger.debug.assert_called_with("Returning cached reranker instance")

    def test_model_eval_mode_set(self):
        """Test that model is set to eval mode."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=False):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                reranker.get_reranker()

                # Verify eval() was called
                mock_model.eval.assert_called_once()

    def test_initialization_logging(self):
        """Test INFO level logging during initialization."""
        with patch.object(reranker, '_reranker_cache', None):
            with patch('src.vulcanlab.retrieval.reranker.AutoTokenizer') as mock_tokenizer_class, \
                 patch('src.vulcanlab.retrieval.reranker.AutoModelForSequenceClassification') as mock_model_class, \
                 patch('src.vulcanlab.retrieval.reranker.torch.cuda.is_available', return_value=True), \
                 patch('src.vulcanlab.retrieval.reranker.logger') as mock_logger, \
                 patch('src.vulcanlab.retrieval.reranker.time.perf_counter', side_effect=[0.0, 2.5]):

                mock_tokenizer = MagicMock()
                mock_model = MagicMock()
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                mock_model.to.return_value = mock_model
                mock_model.eval.return_value = mock_model

                reranker.get_reranker()

                # Verify INFO log with device and timing
                mock_logger.info.assert_called_once()
                log_message = mock_logger.info.call_args[0][0]
                assert "BAAI/bge-reranker-large" in log_message
                assert "device=cuda" in log_message
                assert "init_time=2.50s" in log_message


class TestModuleConfiguration:
    """Tests for module-level configuration."""

    def test_debug_log_cache_hits_default_false(self):
        """Test DEBUG_LOG_CACHE_HITS constant defaults to False."""
        assert reranker.DEBUG_LOG_CACHE_HITS is False

    def test_reranker_model_name_constant(self):
        """Test RERANKER_MODEL_NAME constant is correct."""
        assert reranker.RERANKER_MODEL_NAME == "BAAI/bge-reranker-large"

    def test_cache_variable_exists(self):
        """Test _reranker_cache module variable exists."""
        assert hasattr(reranker, '_reranker_cache')
