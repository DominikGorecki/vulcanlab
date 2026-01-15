import pytest
from unittest.mock import MagicMock, patch
from vulcanlab.summarize.llm_summarize import llm_retry, EvidencePacket
from vulcanlab.summarize.exceptions import (
    LLMRateLimitError, 
    LLMTimeoutError, 
    LLMResponseError,
    LLMAPIError
)

def test_retry_success_first_try():
    mock_func = MagicMock(return_value="success")
    decorated = llm_retry(max_retries=3, base_delay=0.01)(mock_func)
    
    result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_success_after_failure():
    mock_func = MagicMock(side_effect=[LLMRateLimitError("rate limit"), "success"])
    # Use very small base_delay to speed up tests
    decorated = llm_retry(max_retries=3, base_delay=0.01)(mock_func)
    
    with patch("time.sleep"): # Don't actually sleep
        result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 2

def test_retry_respects_max_retries():
    mock_func = MagicMock(side_effect=LLMRateLimitError("rate limit"))
    decorated = llm_retry(max_retries=2, base_delay=0.01)(mock_func)
    
    with patch("time.sleep"):
        with pytest.raises(LLMRateLimitError):
            decorated()
    
    # 1 initial call + 2 retries = 3 calls total
    assert mock_func.call_count == 3

def test_no_retry_on_non_retryable_error():
    mock_func = MagicMock(side_effect=LLMAPIError("client error", status_code=400))
    decorated = llm_retry(max_retries=3, base_delay=0.01)(mock_func)
    
    with pytest.raises(LLMAPIError) as excinfo:
        decorated()
    
    assert excinfo.value.status_code == 400
    assert mock_func.call_count == 1

def test_retry_on_response_error():
    mock_func = MagicMock(side_effect=[LLMResponseError("malformed"), "success"])
    decorated = llm_retry(max_retries=3, base_delay=0.01)(mock_func)
    
    with patch("time.sleep"):
        result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 2

@patch("time.sleep")
def test_exponential_backoff_timing(mock_sleep):
    mock_func = MagicMock(side_effect=LLMTimeoutError("timeout"))
    decorated = llm_retry(max_retries=3, base_delay=1.0)(mock_func)
    
    with pytest.raises(LLMTimeoutError):
        decorated()
    
    # Check sleep calls. They should be roughly 1s, 2s, 4s (plus jitter)
    assert mock_sleep.call_count == 3
    
    # First sleep: 1.0 * 2^0 = 1.0 + jitter
    args, _ = mock_sleep.call_args_list[0]
    assert 1.0 <= args[0] <= 1.2
    
    # Second sleep: 1.0 * 2^1 = 2.0 + jitter
    args, _ = mock_sleep.call_args_list[1]
    assert 2.0 <= args[0] <= 2.4
    
    # Third sleep: 1.0 * 2^2 = 4.0 + jitter
    args, _ = mock_sleep.call_args_list[2]
    assert 4.0 <= args[0] <= 4.8
