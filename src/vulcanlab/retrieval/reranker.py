"""Singleton reranker module for BGE reranker model.

This module provides a singleton pattern for loading and caching the BGE reranker model.
The model is loaded once per process and reused across all retrieval operations to avoid
repeated initialization overhead.

Usage:
    from vulcanlab.retrieval.reranker import get_reranker

    tokenizer, model, device = get_reranker()
    # Use tokenizer and model for reranking
"""

import logging
import time
from typing import Tuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Module logger
logger = logging.getLogger(__name__)

# Singleton cache for reranker components
_reranker_cache: Tuple | None = None

# Debug logging toggle for cache hits
DEBUG_LOG_CACHE_HITS = False

# Model configuration
RERANKER_MODEL_NAME = "BAAI/bge-reranker-large"


def _initialize_reranker() -> Tuple:
    """Initialize the BGE reranker model and tokenizer.

    This private function handles the one-time initialization of the reranker model.
    It selects the appropriate device (CUDA if available, else CPU), loads the model
    with appropriate dtype, and sets it to evaluation mode.

    Returns:
        Tuple containing (tokenizer, model, device)

    Raises:
        RuntimeError: If model or tokenizer loading fails
    """
    try:
        # Detect device
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Record start time for initialization timing
        start_time = time.perf_counter()

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL_NAME)

        # Load model with appropriate dtype based on device
        if device == "cuda":
            model = AutoModelForSequenceClassification.from_pretrained(
                RERANKER_MODEL_NAME,
                torch_dtype=torch.float16
            ).to(device)
        else:
            model = AutoModelForSequenceClassification.from_pretrained(
                RERANKER_MODEL_NAME
            ).to(device)

        # Set model to evaluation mode
        model.eval()

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - start_time

        # Log initialization at INFO level
        logger.info(
            f"Reranker model initialized: model={RERANKER_MODEL_NAME}, "
            f"device={device}, init_time={elapsed_time:.2f}s"
        )

        return (tokenizer, model, device)

    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize reranker model '{RERANKER_MODEL_NAME}': {e}"
        ) from e


def get_reranker() -> Tuple:
    """Get the singleton reranker model instance.

    Returns the cached reranker components (tokenizer, model, device) if already
    initialized, otherwise initializes them on first call. This ensures the model
    is loaded only once per process.

    Returns:
        Tuple containing (tokenizer, model, device)

    Raises:
        RuntimeError: If model initialization fails
    """
    global _reranker_cache

    # Return cached instance if available
    if _reranker_cache is not None:
        if DEBUG_LOG_CACHE_HITS:
            logger.debug("Returning cached reranker instance")
        return _reranker_cache

    # Initialize and cache on first call
    _reranker_cache = _initialize_reranker()
    return _reranker_cache
