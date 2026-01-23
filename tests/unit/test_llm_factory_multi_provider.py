"""
Unit tests for LLM factory multi-provider functions (T02).

Tests the create_langchain_chat_for_provider and create_embeddings_for_provider
functions that support explicit provider selection for automatic evaluation mode.
"""

from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.ai.config import LLMProvider, LLMSettings
from vulcanlab.ai.llm_factory import (
    LangChainStack,
    create_embeddings_for_provider,
    create_langchain_chat_for_provider,
)


class TestCreateLangchainChatForProvider:
    """Tests for create_langchain_chat_for_provider() function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock LLMSettings with API keys."""
        settings = MagicMock(spec=LLMSettings)
        settings.openai_api_key = "sk-test123"
        settings.google_api_key = "AIza-test456"
        return settings

    @pytest.fixture
    def mock_config(self):
        """Create mock config object."""
        config = MagicMock()
        config.llm.models.openai.full = "gpt-4o"
        config.llm.models.gemini.full = "gemini-3-flash-preview"
        return config

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_openai(
        self, mock_chat_class, mock_load_config, mock_settings, mock_config
    ):
        """Test creating LangChain chat with explicit OpenAI provider."""
        mock_load_config.return_value = mock_config
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings
        )

        assert isinstance(result, LangChainStack)
        assert result.chat == mock_chat_instance
        mock_chat_class.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.2,
        )

    @patch("vulcanlab.config.load_config")
    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_for_provider_gemini(
        self, mock_chat_class, mock_load_config, mock_settings, mock_config
    ):
        """Test creating LangChain chat with explicit Gemini provider."""
        mock_load_config.return_value = mock_config
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        result = create_langchain_chat_for_provider(
            LLMProvider.GEMINI, mock_settings
        )

        assert isinstance(result, LangChainStack)
        assert result.chat == mock_chat_instance
        mock_chat_class.assert_called_once_with(
            model="gemini-3-flash-preview",
            google_api_key="AIza-test456",
            temperature=0.2,
        )

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_custom_temperature(
        self, mock_chat_class, mock_load_config, mock_settings, mock_config
    ):
        """Test creating LangChain chat with custom temperature."""
        mock_load_config.return_value = mock_config
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings, temperature=0.7
        )

        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.7,
        )

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_langchain_chat_for_provider_default_settings(
        self, mock_settings_class, mock_chat_class, mock_load_config, mock_config
    ):
        """Test that default settings are loaded when settings=None."""
        mock_load_config.return_value = mock_config
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.openai_api_key = "sk-default"
        mock_settings_class.return_value = mock_default_settings

        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, settings=None
        )

        assert isinstance(result, LangChainStack)
        mock_settings_class.assert_called_once()
        mock_chat_class.assert_called_once()

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_always_uses_full_tier(
        self, mock_chat_class, mock_load_config, mock_settings, mock_config
    ):
        """Test that FULL tier models are always used."""
        mock_load_config.return_value = mock_config
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings
        )

        assert isinstance(result, LangChainStack)
        # Verify FULL model (gpt-4o) is used, not LIGHT model (gpt-4o-mini)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.2,
        )

    def test_create_langchain_chat_for_provider_invalid_provider(
        self, mock_settings
    ):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_langchain_chat_for_provider(
                "invalid_provider", mock_settings
            )

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_reads_config_not_settings_provider(
        self, mock_chat_class, mock_load_config, mock_settings, mock_config
    ):
        """Test that provider parameter overrides settings.provider."""
        mock_load_config.return_value = mock_config
        # Set settings.provider to something different to ensure it's not used
        mock_settings.provider = LLMProvider.GEMINI

        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        # Explicitly request OpenAI
        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings
        )

        assert isinstance(result, LangChainStack)
        # Should use OpenAI despite settings.provider=GEMINI
        mock_chat_class.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.2,
        )


class TestCreateEmbeddingsForProvider:
    """Tests for create_embeddings_for_provider() function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock LLMSettings with API keys."""
        settings = MagicMock(spec=LLMSettings)
        settings.openai_api_key = "sk-test123"
        settings.google_api_key = "AIza-test456"
        return settings

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_for_provider_openai(
        self, mock_embeddings_class, mock_settings
    ):
        """Test creating OpenAI embeddings with explicit provider."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings_for_provider(
            LLMProvider.OPENAI, mock_settings
        )

        assert result == mock_embeddings_instance
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-small",
            api_key="sk-test123",
            dimensions=1536,
        )

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_for_provider_openai_uses_1536_dimensions(
        self, mock_embeddings_class, mock_settings
    ):
        """Test that OpenAI embeddings use dimensions=1536."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings_for_provider(LLMProvider.OPENAI, mock_settings)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["dimensions"] == 1536

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_for_provider_gemini(
        self, mock_embeddings_class, mock_settings
    ):
        """Test creating Gemini embeddings with explicit provider."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings_for_provider(
            LLMProvider.GEMINI, mock_settings
        )

        assert result == mock_embeddings_instance
        mock_embeddings_class.assert_called_once_with(
            model="models/gemini-embedding-001",
            google_api_key="AIza-test456",
            output_dimensionality=1536,
        )

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_for_provider_gemini_uses_correct_model(
        self, mock_embeddings_class, mock_settings
    ):
        """Test that Gemini embeddings use gemini-embedding-001 model."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings_for_provider(LLMProvider.GEMINI, mock_settings)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["model"] == "models/gemini-embedding-001"

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_for_provider_gemini_uses_1536_dimensions(
        self, mock_embeddings_class, mock_settings
    ):
        """Test that Gemini embeddings use output_dimensionality=1536."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings_for_provider(LLMProvider.GEMINI, mock_settings)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["output_dimensionality"] == 1536

    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_embeddings_for_provider_default_settings(
        self, mock_settings_class, mock_embeddings_class
    ):
        """Test that default settings are loaded when settings=None."""
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.openai_api_key = "sk-default"
        mock_settings_class.return_value = mock_default_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings_for_provider(
            LLMProvider.OPENAI, settings=None
        )

        assert result == mock_embeddings_instance
        mock_settings_class.assert_called_once()
        mock_embeddings_class.assert_called_once()

    def test_create_embeddings_for_provider_invalid_provider(
        self, mock_settings
    ):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_embeddings_for_provider("invalid_provider", mock_settings)

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_for_provider_overrides_settings_provider(
        self, mock_embeddings_class, mock_settings
    ):
        """Test that provider parameter overrides settings.provider."""
        # Set settings.provider to something different to ensure it's not used
        mock_settings.provider = LLMProvider.GEMINI

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        # Explicitly request OpenAI
        result = create_embeddings_for_provider(
            LLMProvider.OPENAI, mock_settings
        )

        assert result == mock_embeddings_instance
        # Should use OpenAI despite settings.provider=GEMINI
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-small",
            api_key="sk-test123",
            dimensions=1536,
        )


class TestMultiProviderLazyLoading:
    """Tests for lazy loading behavior in multi-provider functions."""

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_langchain_openai_imports_on_provider_function_call(
        self, mock_chat_class, mock_load_config
    ):
        """Test that langchain_openai imports happen when called with OPENAI provider."""
        mock_config = MagicMock()
        mock_config.llm.models.openai.full = "gpt-4o"
        mock_load_config.return_value = mock_config

        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.openai_api_key = "sk-test"

        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        create_langchain_chat_for_provider(LLMProvider.OPENAI, mock_settings)

        # Verify ChatOpenAI was called (which means import happened)
        mock_chat_class.assert_called_once()

    @patch("vulcanlab.config.load_config")
    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_langchain_google_imports_on_provider_function_call(
        self, mock_chat_class, mock_load_config
    ):
        """Test that langchain_google_genai imports happen when called with GEMINI provider."""
        mock_config = MagicMock()
        mock_config.llm.models.gemini.full = "gemini-3-flash-preview"
        mock_load_config.return_value = mock_config

        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.google_api_key = "AIza-test"

        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        create_langchain_chat_for_provider(LLMProvider.GEMINI, mock_settings)

        # Verify ChatGoogleGenerativeAI was called (which means import happened)
        mock_chat_class.assert_called_once()

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_openai_embeddings_imports_on_provider_function_call(
        self, mock_embeddings_class
    ):
        """Test that langchain_openai imports happen for embeddings."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.openai_api_key = "sk-test"

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings_for_provider(LLMProvider.OPENAI, mock_settings)

        # Verify OpenAIEmbeddings was called (which means import happened)
        mock_embeddings_class.assert_called_once()

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_google_embeddings_imports_on_provider_function_call(
        self, mock_embeddings_class
    ):
        """Test that langchain_google_genai imports happen for embeddings."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.google_api_key = "AIza-test"

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings_for_provider(LLMProvider.GEMINI, mock_settings)

        # Verify GoogleGenerativeAIEmbeddings was called (which means import happened)
        mock_embeddings_class.assert_called_once()


class TestMultiProviderErrorHandling:
    """Tests for error handling in multi-provider functions."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock LLMSettings with API keys."""
        settings = MagicMock(spec=LLMSettings)
        settings.openai_api_key = "sk-test123"
        settings.google_api_key = "AIza-test456"
        return settings

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_none_api_key(
        self, mock_chat_class, mock_load_config, mock_settings
    ):
        """Test that None API key is accepted (may cause runtime errors but not validation errors)."""
        mock_config = MagicMock()
        mock_config.llm.models.openai.full = "gpt-4o"
        mock_load_config.return_value = mock_config

        mock_settings.openai_api_key = None
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        # Should not raise an error at factory level
        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings
        )
        assert isinstance(result, LangChainStack)
        # API key None is passed through - actual API call would fail, but factory doesn't validate

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_for_provider_none_api_key(
        self, mock_embeddings_class, mock_settings
    ):
        """Test that None API key is accepted for embeddings."""
        mock_settings.openai_api_key = None
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        # Should not raise an error at factory level
        result = create_embeddings_for_provider(
            LLMProvider.OPENAI, mock_settings
        )
        assert result == mock_embeddings_instance

    @patch("vulcanlab.config.load_config")
    def test_create_langchain_chat_for_provider_config_load_error_propagates(
        self, mock_load_config, mock_settings
    ):
        """Test that errors from load_config() propagate correctly."""
        mock_load_config.side_effect = ValueError("Config not found")

        with pytest.raises(ValueError, match="Config not found"):
            create_langchain_chat_for_provider(
                LLMProvider.OPENAI, mock_settings
            )

    @patch("vulcanlab.config.load_config")
    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_for_provider_temperature_boundaries(
        self, mock_chat_class, mock_load_config, mock_settings
    ):
        """Test that temperature values at boundaries are accepted."""
        mock_config = MagicMock()
        mock_config.llm.models.openai.full = "gpt-4o"
        mock_load_config.return_value = mock_config

        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance

        # Test minimum temperature
        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings, temperature=0.0
        )
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.0,
        )

        # Test maximum temperature
        result = create_langchain_chat_for_provider(
            LLMProvider.OPENAI, mock_settings, temperature=2.0
        )
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=2.0,
        )
