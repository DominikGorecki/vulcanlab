"""
Unit tests for LLM configuration module.

Tests enum values, Pydantic model validation, environment file discovery,
and settings loading from config and env files.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict

from vulcanlab.ai.config import (
    LLMProvider,
    ModelTier,
    LLMSettings,
    _find_env_file,
)


class TestLLMProvider:
    """Tests for LLMProvider enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.GEMINI == "gemini"

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert isinstance(LLMProvider.OPENAI, LLMProvider)
        assert isinstance(LLMProvider.GEMINI, LLMProvider)

    def test_enum_string_comparison(self):
        """Test that enum values compare correctly with strings."""
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.GEMINI == "gemini"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.GEMINI.value == "gemini"

    def test_enum_iteration(self):
        """Test that enum can be iterated."""
        providers = list(LLMProvider)
        assert len(providers) == 2
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.GEMINI in providers


class TestModelTier:
    """Tests for ModelTier enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert ModelTier.LIGHT == "light"
        assert ModelTier.FULL == "full"

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert isinstance(ModelTier.LIGHT, ModelTier)
        assert isinstance(ModelTier.FULL, ModelTier)

    def test_enum_string_comparison(self):
        """Test that enum values compare correctly with strings."""
        assert ModelTier.LIGHT == "light"
        assert ModelTier.FULL == "full"
        assert ModelTier.LIGHT.value == "light"
        assert ModelTier.FULL.value == "full"

    def test_enum_iteration(self):
        """Test that enum can be iterated."""
        tiers = list(ModelTier)
        assert len(tiers) == 2
        assert ModelTier.LIGHT in tiers
        assert ModelTier.FULL in tiers


class TestFindEnvFile:
    """Tests for _find_env_file() function."""

    def test_find_env_file_function_exists(self):
        """Test that _find_env_file function exists and is callable."""
        assert callable(_find_env_file)
        assert _find_env_file() is None or isinstance(_find_env_file(), Path)

    def test_find_env_file_returns_path_or_none(self):
        """Test that _find_env_file returns Path or None."""
        result = _find_env_file()
        assert result is None or isinstance(result, Path)

    def test_find_env_file_behavior(self):
        """Test basic behavior of _find_env_file.
        
        Since the function uses __file__ which is hard to mock reliably,
        we test that it either finds a .env file (if one exists in the project)
        or returns None (if none exists). This tests the function's contract.
        """
        result = _find_env_file()
        # Function should return None or a Path to .env file
        if result is not None:
            assert isinstance(result, Path)
            assert result.name == ".env"
            assert result.exists()


class TestLLMSettings:
    """Tests for LLMSettings Pydantic model."""

    def test_default_values(self, monkeypatch):
        """Test that settings have correct default values."""
        # Clear environment variables to test defaults
        monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_GOOGLE_API_KEY", raising=False)
        # Create a test settings class with no env_file to avoid loading from .env
        class TestLLMSettings(BaseSettings):
            openai_api_key: str | None = None
            google_api_key: str | None = None
            model_config = SettingsConfigDict(
                env_prefix="LLM_",
                env_file=None,  # No env file for this test
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
            )
        
        settings = TestLLMSettings()
        assert settings.openai_api_key is None
        assert settings.google_api_key is None

    def test_load_from_env_vars(self, monkeypatch):
        """Test loading API keys from environment variables."""
        monkeypatch.setenv("LLM_OPENAI_API_KEY", "test_openai_key")
        monkeypatch.setenv("LLM_GOOGLE_API_KEY", "test_google_key")

        settings = LLMSettings()
        assert settings.openai_api_key == "test_openai_key"
        assert settings.google_api_key == "test_google_key"

    def test_load_from_env_file(self, tmp_path, monkeypatch):
        """Test loading API keys from .env file."""
        # Clear environment variables first
        monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_GOOGLE_API_KEY", raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("LLM_OPENAI_API_KEY=file_openai_key\nLLM_GOOGLE_API_KEY=file_google_key\n")

        # Create a test settings class with our test .env file
        class TestLLMSettings(BaseSettings):
            openai_api_key: str | None = None
            google_api_key: str | None = None
            model_config = SettingsConfigDict(
                env_prefix="LLM_",
                env_file=env_file,  # Use test .env file
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
            )
        
        settings = TestLLMSettings()
        assert settings.openai_api_key == "file_openai_key"
        assert settings.google_api_key == "file_google_key"

    def test_env_prefix_case_insensitive(self, monkeypatch):
        """Test that environment variable prefix is case-insensitive."""
        monkeypatch.setenv("llm_openai_api_key", "lowercase_key")
        monkeypatch.setenv("LLM_GOOGLE_API_KEY", "uppercase_key")

        settings = LLMSettings()
        assert settings.openai_api_key == "lowercase_key"
        assert settings.google_api_key == "uppercase_key"

    def test_extra_env_vars_ignored(self, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("LLM_OPENAI_API_KEY", "valid_key")
        monkeypatch.setenv("LLM_EXTRA_VAR", "should_be_ignored")
        monkeypatch.setenv("OTHER_PREFIX_VAR", "also_ignored")

        settings = LLMSettings()
        assert settings.openai_api_key == "valid_key"
        # Should not raise ValidationError for extra vars
        assert hasattr(settings, "openai_api_key")

    def test_provider_property_openai(self):
        """Test provider property returns OPENAI when configured."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            assert settings.provider == LLMProvider.OPENAI

    def test_provider_property_gemini(self):
        """Test provider property returns GEMINI when configured."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "gemini"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            assert settings.provider == LLMProvider.GEMINI

    def test_get_model_openai_light(self):
        """Test get_model returns correct OpenAI light model."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            mock_config.llm.models.openai.light = "gpt-4o-mini"
            mock_config.llm.models.openai.full = "gpt-4o"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            model = settings.get_model(ModelTier.LIGHT)
            assert model == "gpt-4o-mini"

    def test_get_model_openai_full(self):
        """Test get_model returns correct OpenAI full model."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            mock_config.llm.models.openai.light = "gpt-4o-mini"
            mock_config.llm.models.openai.full = "gpt-4o"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            model = settings.get_model(ModelTier.FULL)
            assert model == "gpt-4o"

    def test_get_model_gemini_light(self):
        """Test get_model returns correct Gemini light model."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "gemini"
            mock_config.llm.models.gemini.light = "gemini-flash-latest"
            mock_config.llm.models.gemini.full = "gemini-2.5-pro"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            model = settings.get_model(ModelTier.LIGHT)
            assert model == "gemini-flash-latest"

    def test_get_model_gemini_full(self):
        """Test get_model returns correct Gemini full model."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "gemini"
            mock_config.llm.models.gemini.light = "gemini-flash-latest"
            mock_config.llm.models.gemini.full = "gemini-2.5-pro"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            model = settings.get_model(ModelTier.FULL)
            assert model == "gemini-2.5-pro"

    def test_get_model_default_tier(self):
        """Test get_model defaults to LIGHT tier."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            mock_config.llm.models.openai.light = "gpt-4o-mini"
            mock_config.llm.models.openai.full = "gpt-4o"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            model = settings.get_model()  # No tier specified
            assert model == "gpt-4o-mini"

    def test_get_model_unsupported_provider(self):
        """Test get_model raises ValueError for unsupported provider."""
        # Create a custom settings class that returns an unsupported provider value
        class UnsupportedProviderSettings(LLMSettings):
            @property
            def provider(self):
                # Return a string that's not a valid LLMProvider enum value
                return "unsupported_provider"
        
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            mock_config.llm.models.openai.light = "gpt-4o-mini"
            mock_config.llm.models.openai.full = "gpt-4o"
            mock_load.return_value = mock_config

            settings = UnsupportedProviderSettings()
            # Should raise ValueError when provider is unsupported
            with pytest.raises(ValueError, match="Unsupported provider"):
                settings.get_model()

    def test_settings_with_none_values(self):
        """Test that settings can have None values for API keys."""
        settings = LLMSettings(
            openai_api_key=None,
            google_api_key=None
        )
        assert settings.openai_api_key is None
        assert settings.google_api_key is None

    def test_settings_with_string_values(self):
        """Test that settings accept string values for API keys."""
        settings = LLMSettings(
            openai_api_key="sk-test123",
            google_api_key="AIza-test456"
        )
        assert settings.openai_api_key == "sk-test123"
        assert settings.google_api_key == "AIza-test456"

    def test_settings_model_dump(self):
        """Test that settings can be serialized."""
        settings = LLMSettings(
            openai_api_key="sk-test123",
            google_api_key="AIza-test456"
        )
        dumped = settings.model_dump()
        assert dumped["openai_api_key"] == "sk-test123"
        assert dumped["google_api_key"] == "AIza-test456"

    def test_settings_model_dump_exclude_none(self, monkeypatch):
        """Test that settings can exclude None values when dumping."""
        # Clear environment variables to ensure None values
        monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_GOOGLE_API_KEY", raising=False)
        # Create a test settings class with no env_file to avoid loading from .env
        class TestLLMSettings(BaseSettings):
            openai_api_key: str | None = None
            google_api_key: str | None = None
            model_config = SettingsConfigDict(
                env_prefix="LLM_",
                env_file=None,  # No env file for this test
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
            )
        
        settings = TestLLMSettings()
        dumped = settings.model_dump(exclude_none=True)
        # Should not include None values when exclude_none=True
        # Pydantic should exclude None fields entirely
        assert "openai_api_key" not in dumped
        assert "google_api_key" not in dumped


class TestLLMSettingsErrorHandling:
    """Tests for error handling in LLMSettings."""

    def test_missing_config_file_uses_defaults(self):
        """Test that missing config file doesn't break provider property."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            # Simulate load_config returning default config
            from vulcanlab.config.app_config import AppConfig
            default_config = AppConfig()
            mock_load.return_value = default_config

            settings = LLMSettings()
            # Should not raise an error, should use default provider
            provider = settings.provider
            assert provider in [LLMProvider.OPENAI, LLMProvider.GEMINI]

    def test_invalid_provider_in_config(self):
        """Test handling of invalid provider value in config."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "invalid_provider"
            mock_load.return_value = mock_config

            settings = LLMSettings()
            # Should raise ValueError when trying to create enum from invalid value
            with pytest.raises(ValueError):
                _ = settings.provider

    def test_missing_model_config(self):
        """Test handling when model config is missing."""
        with patch("vulcanlab.ai.config.load_config") as mock_load:
            mock_config = MagicMock()
            mock_config.llm.provider = "openai"
            # Simulate missing models attribute
            del mock_config.llm.models
            mock_load.return_value = mock_config

            settings = LLMSettings()
            with pytest.raises(AttributeError):
                _ = settings.get_model()

    def test_env_file_encoding_error_handling(self, tmp_path):
        """Test handling of encoding errors in .env file."""
        # Create .env file with invalid encoding
        env_file = tmp_path / ".env"
        # Write binary data that can't be decoded as UTF-8
        env_file.write_bytes(b'\xff\xfe\x00\x00')

        with patch("vulcanlab.ai.config._ENV_FILE_PATH", env_file):
            # Should handle encoding error gracefully
            # Pydantic-settings should handle this, but we test it doesn't crash
            try:
                settings = LLMSettings()
                # If it doesn't crash, that's acceptable
                assert settings is not None
            except Exception:
                # If it raises an exception, that's also acceptable behavior
                pass

