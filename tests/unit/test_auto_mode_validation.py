"""
Unit tests for automatic mode validation functions (T03).

Tests the validate_api_keys_for_auto_mode and get_opposite_provider functions.
"""

from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.eval.auto_mode import (
    validate_api_keys_for_auto_mode,
    get_opposite_provider,
)


class TestValidateApiKeysForAutoMode:
    """Tests for validate_api_keys_for_auto_mode() function."""

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_both_present(self, mock_settings_class):
        """Test that validation passes when both API keys are present."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.google_api_key = "AIza-test456"
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is True
        assert error == ""

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_openai_missing(self, mock_settings_class):
        """Test that validation fails when OpenAI key is missing."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.google_api_key = "AIza-test456"
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "OpenAI API key" in error
        assert "LLM_OPENAI_API_KEY" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_openai_empty(self, mock_settings_class):
        """Test that validation fails when OpenAI key is empty string."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = ""
        mock_settings.google_api_key = "AIza-test456"
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "OpenAI API key" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_openai_whitespace(self, mock_settings_class):
        """Test that validation fails when OpenAI key is only whitespace."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "   "
        mock_settings.google_api_key = "AIza-test456"
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "OpenAI API key" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_gemini_missing(self, mock_settings_class):
        """Test that validation fails when Gemini key is missing."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.google_api_key = None
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "Gemini API key" in error
        assert "LLM_GOOGLE_API_KEY" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_gemini_empty(self, mock_settings_class):
        """Test that validation fails when Gemini key is empty string."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.google_api_key = ""
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "Gemini API key" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_gemini_whitespace(self, mock_settings_class):
        """Test that validation fails when Gemini key is only whitespace."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.google_api_key = "   "
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        assert "Gemini API key" in error

    @patch("vulcanlab.eval.auto_mode.LLMSettings")
    def test_validate_api_keys_both_missing(self, mock_settings_class):
        """Test that validation fails when both keys are missing."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.google_api_key = None
        mock_settings_class.return_value = mock_settings

        is_valid, error = validate_api_keys_for_auto_mode()

        assert is_valid is False
        # Should fail on OpenAI first (checked first in implementation)
        assert "OpenAI API key" in error


class TestGetOppositeProvider:
    """Tests for get_opposite_provider() function."""

    def test_get_opposite_provider_openai(self):
        """Test that opposite of 'openai' is 'gemini'."""
        result = get_opposite_provider("openai")
        assert result == "gemini"

    def test_get_opposite_provider_gemini(self):
        """Test that opposite of 'gemini' is 'openai'."""
        result = get_opposite_provider("gemini")
        assert result == "openai"

    def test_get_opposite_provider_invalid(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            get_opposite_provider("claude")

    def test_get_opposite_provider_empty(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            get_opposite_provider("")

    def test_get_opposite_provider_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            get_opposite_provider(None)

    def test_get_opposite_provider_case_sensitive(self):
        """Test that provider matching is case-sensitive."""
        with pytest.raises(ValueError, match="Invalid provider"):
            get_opposite_provider("OpenAI")

    def test_get_opposite_provider_round_trip(self):
        """Test that applying function twice returns original value."""
        assert get_opposite_provider(get_opposite_provider("openai")) == "openai"
        assert get_opposite_provider(get_opposite_provider("gemini")) == "gemini"
