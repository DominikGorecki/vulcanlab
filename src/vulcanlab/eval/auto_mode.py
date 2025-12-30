"""
Automatic evaluation mode functions.

Provides validation and helper functions for automatic evaluation mode
where answer generation and judging use different LLM providers.
"""

from typing import Tuple

from vulcanlab.ai.config import LLMSettings


def validate_api_keys_for_auto_mode() -> Tuple[bool, str]:
    """Validate that both OpenAI and Gemini API keys are configured.

    Automatic evaluation mode requires both OpenAI and Gemini API keys
    to be present in the environment, as one provider is used for answer
    generation and the other for judge evaluation.

    Returns:
        Tuple of (is_valid, error_message):
            - is_valid: True if both API keys are present and non-empty
            - error_message: Empty string if valid, error description if invalid

    Examples:
        >>> is_valid, error = validate_api_keys_for_auto_mode()
        >>> if not is_valid:
        ...     print(f"Cannot enable auto mode: {error}")
    """
    settings = LLMSettings()

    # Check OpenAI API key
    if not settings.openai_api_key or not settings.openai_api_key.strip():
        return False, "OpenAI API key is not configured. Please set LLM_OPENAI_API_KEY in .env"

    # Check Gemini API key
    if not settings.google_api_key or not settings.google_api_key.strip():
        return False, "Gemini API key is not configured. Please set LLM_GOOGLE_API_KEY in .env"

    return True, ""


def get_opposite_provider(provider: str) -> str:
    """Get the opposite provider for automatic mode.

    In automatic mode, the judge provider is always set to the opposite
    of the answer provider to ensure unbiased evaluation.

    Args:
        provider: The answer provider ('openai' or 'gemini')

    Returns:
        The opposite provider ('gemini' if input is 'openai', 'openai' if input is 'gemini')

    Raises:
        ValueError: If provider is not 'openai' or 'gemini'

    Examples:
        >>> get_opposite_provider('openai')
        'gemini'
        >>> get_opposite_provider('gemini')
        'openai'
    """
    if provider == "openai":
        return "gemini"
    elif provider == "gemini":
        return "openai"
    else:
        raise ValueError(f"Invalid provider: {provider}. Must be 'openai' or 'gemini'")
