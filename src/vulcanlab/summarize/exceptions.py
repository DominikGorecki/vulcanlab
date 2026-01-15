"""
Custom exceptions for the summarization module.
"""

class SummarizationError(Exception):
    """Base exception for summarization errors."""
    def __init__(self, message: str, work_id: int = None, chunk_id: str = None):
        super().__init__(message)
        self.work_id = work_id
        self.chunk_id = chunk_id

class InsufficientEvidenceError(SummarizationError):
    """Exception raised when the LLM reports insufficient evidence even after escalation."""
    pass

class LLMAPIError(SummarizationError):
    """Base exception for LLM API errors."""
    def __init__(self, message: str, status_code: int = None, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.retry_after = retry_after

class LLMRateLimitError(LLMAPIError):
    """Exception raised when the LLM API returns a 429 Rate Limit error."""
    pass

class LLMTimeoutError(LLMAPIError):
    """Exception raised when the LLM API call times out."""
    pass

class LLMResponseError(LLMAPIError):
    """Exception raised when the LLM returns a malformed or invalid response."""
    pass

def format_summarization_error(e: Exception) -> str:
    """Formats an exception into a user-friendly error message."""
    if isinstance(e, LLMRateLimitError):
        return "LLM rate limit reached. Please try again in a few minutes."
    if isinstance(e, LLMTimeoutError):
        return "The request to the AI model timed out. This may be due to heavy load."
    if isinstance(e, InsufficientEvidenceError):
        return "The AI was unable to summarize some parts because there was not enough evidence."
    if isinstance(e, LLMResponseError):
        return "The AI returned a malformed response. This can happen occasionally, please retry."
    if isinstance(e, LLMAPIError):
        return f"AI Service Error: {str(e)}"
    if isinstance(e, SummarizationError):
        return str(e)
    return f"An unexpected error occurred: {str(e)}"
