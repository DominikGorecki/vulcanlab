"""
Unit tests for LLM factory module.

Tests factory functions for creating PydanticAI and LangChain instances,
including lazy loading behavior, error handling, and mocking of external API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.ai.config import LLMProvider, LLMSettings, ModelTier
from vulcanlab.ai.llm_factory import (
    LLMStack,
    LangChainStack,
    PydanticAIStack,
    create_embeddings,
    create_langchain_chat,
    create_llm_stack,
    create_pydantic_agent,
)


class TestPydanticAIStack:
    """Tests for PydanticAIStack dataclass."""

    def test_instantiation(self):
        """Test that PydanticAIStack can be instantiated with an agent."""
        mock_agent = MagicMock()
        stack = PydanticAIStack(agent=mock_agent)
        assert stack.agent == mock_agent

    def test_dataclass_structure(self):
        """Test that PydanticAIStack has the expected structure."""
        mock_agent = MagicMock()
        stack = PydanticAIStack(agent=mock_agent)
        assert hasattr(stack, "agent")
        assert stack.agent == mock_agent


class TestLangChainStack:
    """Tests for LangChainStack dataclass."""

    def test_instantiation(self):
        """Test that LangChainStack can be instantiated with a chat model."""
        mock_chat = MagicMock()
        stack = LangChainStack(chat=mock_chat)
        assert stack.chat == mock_chat

    def test_dataclass_structure(self):
        """Test that LangChainStack has the expected structure."""
        mock_chat = MagicMock()
        stack = LangChainStack(chat=mock_chat)
        assert hasattr(stack, "chat")
        assert stack.chat == mock_chat


class TestLLMStack:
    """Tests for LLMStack dataclass."""

    def test_instantiation(self):
        """Test that LLMStack can be instantiated with all components."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        
        stack = LLMStack(
            settings=mock_settings,
            pydantic_ai=mock_pydantic_stack,
            langchain=mock_langchain_stack,
        )
        assert stack.settings == mock_settings
        assert stack.pydantic_ai == mock_pydantic_stack
        assert stack.langchain == mock_langchain_stack

    def test_dataclass_structure(self):
        """Test that LLMStack has all required components."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        
        stack = LLMStack(
            settings=mock_settings,
            pydantic_ai=mock_pydantic_stack,
            langchain=mock_langchain_stack,
        )
        assert hasattr(stack, "settings")
        assert hasattr(stack, "pydantic_ai")
        assert hasattr(stack, "langchain")
        assert stack.settings == mock_settings
        assert stack.pydantic_ai == mock_pydantic_stack
        assert stack.langchain == mock_langchain_stack


class TestCreatePydanticAgent:
    """Tests for create_pydantic_agent() function."""

    @pytest.fixture
    def mock_settings_openai(self):
        """Create mock LLMSettings for OpenAI provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.OPENAI
        settings.get_model.return_value = "gpt-4o-mini"
        return settings

    @pytest.fixture
    def mock_settings_gemini(self):
        """Create mock LLMSettings for Gemini provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.GEMINI
        settings.get_model.return_value = "gemini-flash-latest"
        return settings

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_openai_light(self, mock_agent_class, mock_settings_openai):
        """Test creating PydanticAI agent with OpenAI provider and LIGHT tier."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        result = create_pydantic_agent(mock_settings_openai, tier=ModelTier.LIGHT)
        
        assert isinstance(result, PydanticAIStack)
        assert result.agent == mock_agent_instance
        mock_settings_openai.get_model.assert_called_once_with(ModelTier.LIGHT)
        mock_agent_class.assert_called_once_with(
            "openai:gpt-4o-mini",
            instructions="You are a helpful assistant.",
        )

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_openai_full(self, mock_agent_class, mock_settings_openai):
        """Test creating PydanticAI agent with OpenAI provider and FULL tier."""
        mock_settings_openai.get_model.return_value = "gpt-4o"
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        result = create_pydantic_agent(mock_settings_openai, tier=ModelTier.FULL)
        
        assert isinstance(result, PydanticAIStack)
        assert result.agent == mock_agent_instance
        mock_settings_openai.get_model.assert_called_once_with(ModelTier.FULL)
        mock_agent_class.assert_called_once_with(
            "openai:gpt-4o",
            instructions="You are a helpful assistant.",
        )

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_gemini_light(self, mock_agent_class, mock_settings_gemini):
        """Test creating PydanticAI agent with Gemini provider and LIGHT tier."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        result = create_pydantic_agent(mock_settings_gemini, tier=ModelTier.LIGHT)
        
        assert isinstance(result, PydanticAIStack)
        assert result.agent == mock_agent_instance
        mock_settings_gemini.get_model.assert_called_once_with(ModelTier.LIGHT)
        mock_agent_class.assert_called_once_with(
            "google-gla:gemini-flash-latest",
            instructions="You are a helpful assistant.",
        )

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_gemini_full(self, mock_agent_class, mock_settings_gemini):
        """Test creating PydanticAI agent with Gemini provider and FULL tier."""
        mock_settings_gemini.get_model.return_value = "gemini-2.5-pro"
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        result = create_pydantic_agent(mock_settings_gemini, tier=ModelTier.FULL)
        
        assert isinstance(result, PydanticAIStack)
        assert result.agent == mock_agent_instance
        mock_settings_gemini.get_model.assert_called_once_with(ModelTier.FULL)
        mock_agent_class.assert_called_once_with(
            "google-gla:gemini-2.5-pro",
            instructions="You are a helpful assistant.",
        )

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_default_tier(self, mock_agent_class, mock_settings_openai):
        """Test that create_pydantic_agent defaults to LIGHT tier."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        result = create_pydantic_agent(mock_settings_openai)
        
        assert isinstance(result, PydanticAIStack)
        mock_settings_openai.get_model.assert_called_once_with(ModelTier.LIGHT)

    def test_create_pydantic_agent_unsupported_provider(self, mock_settings_openai):
        """Test that unsupported provider raises ValueError."""
        mock_settings_openai.provider = "unsupported_provider"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_pydantic_agent(mock_settings_openai)


class TestCreateLangchainChat:
    """Tests for create_langchain_chat() function."""

    @pytest.fixture
    def mock_settings_openai(self):
        """Create mock LLMSettings for OpenAI provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.OPENAI
        settings.openai_api_key = "sk-test123"
        settings.get_model.return_value = "gpt-4o-mini"
        return settings

    @pytest.fixture
    def mock_settings_gemini(self):
        """Create mock LLMSettings for Gemini provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.GEMINI
        settings.google_api_key = "AIza-test456"
        settings.get_model.return_value = "gemini-flash-latest"
        return settings

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_openai_light(self, mock_chat_class, mock_settings_openai):
        """Test creating LangChain chat with OpenAI provider and LIGHT tier."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_openai, tier=ModelTier.LIGHT)
        
        assert isinstance(result, LangChainStack)
        assert result.chat == mock_chat_instance
        mock_settings_openai.get_model.assert_called_once_with(ModelTier.LIGHT)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o-mini",
            api_key="sk-test123",
            temperature=0.2,
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_openai_full(self, mock_chat_class, mock_settings_openai):
        """Test creating LangChain chat with OpenAI provider and FULL tier."""
        mock_settings_openai.get_model.return_value = "gpt-4o"
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_openai, tier=ModelTier.FULL)
        
        assert isinstance(result, LangChainStack)
        mock_settings_openai.get_model.assert_called_once_with(ModelTier.FULL)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o",
            api_key="sk-test123",
            temperature=0.2,
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_openai_custom_temperature(self, mock_chat_class, mock_settings_openai):
        """Test creating LangChain chat with custom temperature."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_openai, temperature=0.7)
        
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o-mini",
            api_key="sk-test123",
            temperature=0.7,
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_openai_search_parameter(self, mock_chat_class, mock_settings_openai):
        """Test that search parameter is accepted (currently placeholder)."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_openai, search=True)
        
        assert isinstance(result, LangChainStack)
        # Search parameter is currently a placeholder, so it doesn't affect the call
        mock_chat_class.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_langchain_chat_default_settings(self, mock_settings_class, mock_chat_class):
        """Test that default settings are loaded when settings=None."""
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.provider = LLMProvider.OPENAI
        mock_default_settings.openai_api_key = "sk-default"
        mock_default_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_default_settings
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(settings=None)
        
        assert isinstance(result, LangChainStack)
        mock_settings_class.assert_called_once()
        mock_chat_class.assert_called_once()

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_gemini_light(self, mock_chat_class, mock_settings_gemini):
        """Test creating LangChain chat with Gemini provider and LIGHT tier."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_gemini, tier=ModelTier.LIGHT)
        
        assert isinstance(result, LangChainStack)
        assert result.chat == mock_chat_instance
        mock_settings_gemini.get_model.assert_called_once_with(ModelTier.LIGHT)
        mock_chat_class.assert_called_once_with(
            model="gemini-flash-latest",
            google_api_key="AIza-test456",
            temperature=0.2,
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_gemini_full(self, mock_chat_class, mock_settings_gemini):
        """Test creating LangChain chat with Gemini provider and FULL tier."""
        mock_settings_gemini.get_model.return_value = "gemini-2.5-pro"
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_gemini, tier=ModelTier.FULL)
        
        assert isinstance(result, LangChainStack)
        mock_settings_gemini.get_model.assert_called_once_with(ModelTier.FULL)
        mock_chat_class.assert_called_once_with(
            model="gemini-2.5-pro",
            google_api_key="AIza-test456",
            temperature=0.2,
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_gemini_custom_temperature(self, mock_chat_class, mock_settings_gemini):
        """Test creating LangChain chat with Gemini and custom temperature."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_gemini, temperature=0.5)
        
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_once_with(
            model="gemini-flash-latest",
            google_api_key="AIza-test456",
            temperature=0.5,
        )

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_gemini_search_ignored(self, mock_chat_class, mock_settings_gemini):
        """Test that search parameter is ignored for Gemini (currently not implemented)."""
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(mock_settings_gemini, search=True)
        
        assert isinstance(result, LangChainStack)
        # Search parameter doesn't affect Gemini implementation currently
        mock_chat_class.assert_called_once()

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_langchain_chat_gemini_default_settings(self, mock_settings_class, mock_chat_class):
        """Test that default settings are loaded for Gemini when settings=None."""
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.provider = LLMProvider.GEMINI
        mock_default_settings.google_api_key = "AIza-default"
        mock_default_settings.get_model.return_value = "gemini-flash-latest"
        mock_settings_class.return_value = mock_default_settings
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        result = create_langchain_chat(settings=None)
        
        assert isinstance(result, LangChainStack)
        mock_settings_class.assert_called_once()
        mock_chat_class.assert_called_once()

    def test_create_langchain_chat_unsupported_provider(self, mock_settings_openai):
        """Test that unsupported provider raises ValueError."""
        mock_settings_openai.provider = "unsupported_provider"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_langchain_chat(mock_settings_openai)


class TestCreateEmbeddings:
    """Tests for create_embeddings() function."""

    @pytest.fixture
    def mock_settings_openai(self):
        """Create mock LLMSettings for OpenAI provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.OPENAI
        settings.openai_api_key = "sk-test123"
        return settings

    @pytest.fixture
    def mock_settings_gemini(self):
        """Create mock LLMSettings for Gemini provider."""
        settings = MagicMock(spec=LLMSettings)
        settings.provider = LLMProvider.GEMINI
        settings.google_api_key = "AIza-test456"
        return settings

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_openai(self, mock_embeddings_class, mock_settings_openai):
        """Test creating OpenAI embeddings."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings(mock_settings_openai)

        assert result == mock_embeddings_instance
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-small",
            api_key="sk-test123",
            dimensions=1536,
        )

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_openai_uses_1536_dimensions(self, mock_embeddings_class, mock_settings_openai):
        """Test that OpenAI embeddings use 1536 dimensions."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings(mock_settings_openai)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["dimensions"] == 1536

    @patch("langchain_openai.OpenAIEmbeddings")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_embeddings_openai_default_settings(self, mock_settings_class, mock_embeddings_class):
        """Test that default settings are loaded for OpenAI when settings=None."""
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.provider = LLMProvider.OPENAI
        mock_default_settings.openai_api_key = "sk-default"
        mock_settings_class.return_value = mock_default_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings(settings=None)

        assert result == mock_embeddings_instance
        mock_settings_class.assert_called_once()
        mock_embeddings_class.assert_called_once_with(
            model="text-embedding-3-small",
            api_key="sk-default",
            dimensions=1536,
        )

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_gemini(self, mock_embeddings_class, mock_settings_gemini):
        """Test creating Gemini embeddings."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings(mock_settings_gemini)

        assert result == mock_embeddings_instance
        mock_embeddings_class.assert_called_once_with(
            model="models/gemini-embedding-001",
            google_api_key="AIza-test456",
            output_dimensionality=1536,
        )

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_gemini_uses_correct_model(self, mock_embeddings_class, mock_settings_gemini):
        """Test that Gemini embeddings use gemini-embedding-001 model."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings(mock_settings_gemini)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["model"] == "models/gemini-embedding-001"

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_gemini_uses_1536_dimensions(self, mock_embeddings_class, mock_settings_gemini):
        """Test that Gemini embeddings use output_dimensionality=1536."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        create_embeddings(mock_settings_gemini)

        call_kwargs = mock_embeddings_class.call_args[1]
        assert call_kwargs["output_dimensionality"] == 1536

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_embeddings_gemini_default_settings(self, mock_settings_class, mock_embeddings_class):
        """Test that default settings are loaded for Gemini when settings=None."""
        mock_default_settings = MagicMock(spec=LLMSettings)
        mock_default_settings.provider = LLMProvider.GEMINI
        mock_default_settings.google_api_key = "AIza-default"
        mock_settings_class.return_value = mock_default_settings

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        result = create_embeddings(settings=None)

        assert result == mock_embeddings_instance
        mock_settings_class.assert_called_once()
        mock_embeddings_class.assert_called_once_with(
            model="models/gemini-embedding-001",
            google_api_key="AIza-default",
            output_dimensionality=1536,
        )

    def test_create_embeddings_unsupported_provider(self, mock_settings_openai):
        """Test that unsupported provider raises ValueError."""
        mock_settings_openai.provider = "unsupported_provider"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_embeddings(mock_settings_openai)


class TestCreateLLMStack:
    """Tests for create_llm_stack() function."""

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_default_parameters(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test creating LLM stack with default parameters."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack()
        
        assert isinstance(result, LLMStack)
        assert result.settings == mock_settings
        assert result.pydantic_ai == mock_pydantic_stack
        assert result.langchain == mock_langchain_stack
        
        mock_settings_class.assert_called_once()
        mock_pydantic_func.assert_called_once_with(mock_settings, tier=ModelTier.LIGHT)
        mock_langchain_func.assert_called_once_with(
            mock_settings,
            tier=ModelTier.LIGHT,
            search=False,
            temperature=0.2,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_full_tier(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test creating LLM stack with FULL tier."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack(tier=ModelTier.FULL)
        
        assert isinstance(result, LLMStack)
        mock_pydantic_func.assert_called_once_with(mock_settings, tier=ModelTier.FULL)
        mock_langchain_func.assert_called_once_with(
            mock_settings,
            tier=ModelTier.FULL,
            search=False,
            temperature=0.2,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_with_search(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test creating LLM stack with search=True."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack(search=True)
        
        assert isinstance(result, LLMStack)
        mock_langchain_func.assert_called_once_with(
            mock_settings,
            tier=ModelTier.LIGHT,
            search=True,
            temperature=0.2,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_custom_temperature(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test creating LLM stack with custom temperature."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack(temperature=0.8)
        
        assert isinstance(result, LLMStack)
        mock_langchain_func.assert_called_once_with(
            mock_settings,
            tier=ModelTier.LIGHT,
            search=False,
            temperature=0.8,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_all_parameters(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test creating LLM stack with all parameters specified."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack(tier=ModelTier.FULL, search=True, temperature=0.5)
        
        assert isinstance(result, LLMStack)
        mock_pydantic_func.assert_called_once_with(mock_settings, tier=ModelTier.FULL)
        mock_langchain_func.assert_called_once_with(
            mock_settings,
            tier=ModelTier.FULL,
            search=True,
            temperature=0.5,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_shared_settings(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test that settings are shared across both stacks."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.return_value = mock_langchain_stack
        
        result = create_llm_stack()
        
        assert result.settings == mock_settings
        # Verify both functions were called with the same settings instance
        assert mock_pydantic_func.call_args[0][0] == mock_settings
        assert mock_langchain_func.call_args[0][0] == mock_settings


class TestLazyLoading:
    """Tests for lazy loading behavior."""

    def test_module_import_does_not_load_libraries(self):
        """Test that importing the module doesn't trigger library imports.
        
        Note: This test verifies that TYPE_CHECKING imports don't cause
        runtime imports. The actual libraries may be imported elsewhere,
        but the module itself uses lazy imports.
        """
        # Import the module - this should not trigger imports of heavy libraries
        import vulcanlab.ai.llm_factory as llm_factory_module
        
        # Verify the module exists and has the expected structure
        assert hasattr(llm_factory_module, "create_pydantic_agent")
        assert hasattr(llm_factory_module, "create_langchain_chat")
        assert hasattr(llm_factory_module, "create_embeddings")
        
        # The module should use TYPE_CHECKING for type hints only
        # Actual imports happen inside functions

    @patch("pydantic_ai.Agent")
    def test_pydantic_ai_imports_on_function_call(self, mock_agent_class):
        """Test that pydantic_ai imports happen when create_pydantic_agent is called."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        # Call the function - this should trigger the import
        create_pydantic_agent(mock_settings)
        
        # Verify Agent was called (which means import happened)
        mock_agent_class.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    def test_langchain_openai_imports_on_function_call(self, mock_chat_class):
        """Test that langchain_openai imports happen when create_langchain_chat is called with OpenAI."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = "sk-test"
        mock_settings.get_model.return_value = "gpt-4o-mini"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Call the function - this should trigger the import
        create_langchain_chat(mock_settings)
        
        # Verify ChatOpenAI was called (which means import happened)
        mock_chat_class.assert_called_once()

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_langchain_google_imports_on_function_call(self, mock_chat_class):
        """Test that langchain_google_genai imports happen when create_langchain_chat is called with Gemini."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.google_api_key = "AIza-test"
        mock_settings.get_model.return_value = "gemini-flash-latest"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Call the function - this should trigger the import
        create_langchain_chat(mock_settings)
        
        # Verify ChatGoogleGenerativeAI was called (which means import happened)
        mock_chat_class.assert_called_once()

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_openai_embeddings_imports_on_function_call(self, mock_embeddings_class):
        """Test that langchain_openai imports happen when create_embeddings is called with OpenAI."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = "sk-test"
        
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Call the function - this should trigger the import
        create_embeddings(mock_settings)
        
        # Verify OpenAIEmbeddings was called (which means import happened)
        mock_embeddings_class.assert_called_once()

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_google_embeddings_imports_on_function_call(self, mock_embeddings_class):
        """Test that langchain_google_genai imports happen when create_embeddings is called with Gemini."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.google_api_key = "AIza-test"
        
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Call the function - this should trigger the import
        create_embeddings(mock_settings)
        
        # Verify GoogleGenerativeAIEmbeddings was called (which means import happened)
        mock_embeddings_class.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in factory functions."""

    def test_create_pydantic_agent_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = "invalid_provider"
        mock_settings.get_model.return_value = "some-model"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_pydantic_agent(mock_settings)

    def test_create_langchain_chat_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = "invalid_provider"
        mock_settings.get_model.return_value = "some-model"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_langchain_chat(mock_settings)

    def test_create_embeddings_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = "invalid_provider"
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_embeddings(mock_settings)

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_none_api_key(self, mock_chat_class):
        """Test that None API key is accepted (may cause runtime errors but not validation errors)."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = None
        mock_settings.get_model.return_value = "gpt-4o-mini"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Should not raise an error at factory level
        result = create_langchain_chat(mock_settings)
        assert isinstance(result, LangChainStack)
        # API key None is passed through - actual API call would fail, but factory doesn't validate

    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_create_langchain_chat_gemini_none_api_key(self, mock_chat_class):
        """Test that None API key is accepted for Gemini."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.google_api_key = None
        mock_settings.get_model.return_value = "gemini-flash-latest"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Should not raise an error at factory level
        result = create_langchain_chat(mock_settings)
        assert isinstance(result, LangChainStack)

    @patch("langchain_openai.OpenAIEmbeddings")
    def test_create_embeddings_none_api_key(self, mock_embeddings_class):
        """Test that None API key is accepted for embeddings."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = None
        
        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance
        
        # Should not raise an error at factory level
        result = create_embeddings(mock_settings)
        assert result == mock_embeddings_instance

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_empty_string_api_key(self, mock_chat_class):
        """Test that empty string API key is accepted (may cause runtime errors but not validation errors)."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = ""
        mock_settings.get_model.return_value = "gpt-4o-mini"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Should not raise an error at factory level
        result = create_langchain_chat(mock_settings)
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_once_with(
            model="gpt-4o-mini",
            api_key="",
            temperature=0.2,
        )

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_temperature_boundaries(self, mock_chat_class):
        """Test that temperature values at boundaries are accepted."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = "sk-test"
        mock_settings.get_model.return_value = "gpt-4o-mini"
        
        mock_chat_instance = MagicMock()
        mock_chat_class.return_value = mock_chat_instance
        
        # Test minimum temperature
        result = create_langchain_chat(mock_settings, temperature=0.0)
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_with(
            model="gpt-4o-mini",
            api_key="sk-test",
            temperature=0.0,
        )
        
        # Test maximum temperature
        result = create_langchain_chat(mock_settings, temperature=2.0)
        assert isinstance(result, LangChainStack)
        mock_chat_class.assert_called_with(
            model="gpt-4o-mini",
            api_key="sk-test",
            temperature=2.0,
        )

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_get_model_error_propagates(self, mock_agent_class):
        """Test that errors from get_model() propagate correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.side_effect = ValueError("Model not found")
        
        with pytest.raises(ValueError, match="Model not found"):
            create_pydantic_agent(mock_settings)
        
        # Agent should not be called if get_model fails
        mock_agent_class.assert_not_called()

    @patch("langchain_openai.ChatOpenAI")
    def test_create_langchain_chat_get_model_error_propagates(self, mock_chat_class):
        """Test that errors from get_model() propagate correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = "sk-test"
        mock_settings.get_model.side_effect = ValueError("Model not found")
        
        with pytest.raises(ValueError, match="Model not found"):
            create_langchain_chat(mock_settings)
        
        # ChatOpenAI should not be called if get_model fails
        mock_chat_class.assert_not_called()

    def test_pydantic_ai_stack_equality(self):
        """Test that PydanticAIStack instances can be compared."""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        
        stack1 = PydanticAIStack(agent=mock_agent1)
        stack2 = PydanticAIStack(agent=mock_agent1)
        stack3 = PydanticAIStack(agent=mock_agent2)
        
        # Same agent instance should be equal
        assert stack1.agent == stack2.agent
        # Different agent instances should not be equal
        assert stack1.agent != stack3.agent

    def test_langchain_stack_equality(self):
        """Test that LangChainStack instances can be compared."""
        mock_chat1 = MagicMock()
        mock_chat2 = MagicMock()
        
        stack1 = LangChainStack(chat=mock_chat1)
        stack2 = LangChainStack(chat=mock_chat1)
        stack3 = LangChainStack(chat=mock_chat2)
        
        # Same chat instance should be equal
        assert stack1.chat == stack2.chat
        # Different chat instances should not be equal
        assert stack1.chat != stack3.chat

    def test_llm_stack_equality(self):
        """Test that LLMStack instances can be compared."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_langchain_stack = MagicMock(spec=LangChainStack)
        
        stack1 = LLMStack(
            settings=mock_settings,
            pydantic_ai=mock_pydantic_stack,
            langchain=mock_langchain_stack,
        )
        stack2 = LLMStack(
            settings=mock_settings,
            pydantic_ai=mock_pydantic_stack,
            langchain=mock_langchain_stack,
        )
        
        # Same components should be equal
        assert stack1.settings == stack2.settings
        assert stack1.pydantic_ai == stack2.pydantic_ai
        assert stack1.langchain == stack2.langchain

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_model_string_format_openai(self, mock_agent_class):
        """Test that OpenAI model strings are formatted correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        create_pydantic_agent(mock_settings)
        
        # Verify the model string format is correct
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[0][0] == "openai:gpt-4o-mini"

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_model_string_format_gemini(self, mock_agent_class):
        """Test that Gemini model strings are formatted correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.get_model.return_value = "gemini-flash-latest"
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        create_pydantic_agent(mock_settings)
        
        # Verify the model string format is correct
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[0][0] == "google-gla:gemini-flash-latest"

    @patch("pydantic_ai.Agent")
    def test_create_pydantic_agent_instructions_always_set(self, mock_agent_class):
        """Test that instructions are always set to the expected value."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        create_pydantic_agent(mock_settings)
        
        # Verify instructions are always set
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["instructions"] == "You are a helpful assistant."

    @patch("langchain_google_genai.GoogleGenerativeAIEmbeddings")
    def test_create_embeddings_gemini_empty_string_api_key(self, mock_embeddings_class):
        """Test that empty string API key is accepted for Gemini embeddings."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.google_api_key = ""

        mock_embeddings_instance = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings_instance

        # Should not raise an error at factory level
        result = create_embeddings(mock_settings)
        assert result == mock_embeddings_instance
        mock_embeddings_class.assert_called_once_with(
            model="models/gemini-embedding-001",
            google_api_key="",
            output_dimensionality=1536,
        )

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_error_handling_pydantic_fails(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test that errors in create_pydantic_agent propagate correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        mock_pydantic_func.side_effect = ValueError("Pydantic error")
        
        with pytest.raises(ValueError, match="Pydantic error"):
            create_llm_stack()
        
        # LangChain should not be called if Pydantic fails
        mock_langchain_func.assert_not_called()

    @patch("vulcanlab.ai.llm_factory.create_langchain_chat")
    @patch("vulcanlab.ai.llm_factory.create_pydantic_agent")
    @patch("vulcanlab.ai.llm_factory.LLMSettings")
    def test_create_llm_stack_error_handling_langchain_fails(self, mock_settings_class, mock_pydantic_func, mock_langchain_func):
        """Test that errors in create_langchain_chat propagate correctly."""
        mock_settings = MagicMock(spec=LLMSettings)
        mock_settings_class.return_value = mock_settings
        mock_pydantic_stack = MagicMock(spec=PydanticAIStack)
        mock_pydantic_func.return_value = mock_pydantic_stack
        mock_langchain_func.side_effect = ValueError("LangChain error")
        
        with pytest.raises(ValueError, match="LangChain error"):
            create_llm_stack()
        
        # Pydantic should be called before LangChain fails
        mock_pydantic_func.assert_called_once()

