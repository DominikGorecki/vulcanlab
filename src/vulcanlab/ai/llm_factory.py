"""Factory functions for creating PydanticAI and LangChain instances.

Uses lazy imports to avoid loading heavy ML libraries until actually needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

# Lazy imports - only import heavy libraries when functions are called
if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.embeddings import Embeddings
    from pydantic_ai import Agent

from .config import LLMProvider, LLMSettings, ModelTier


@dataclass
class PydanticAIStack:
    """Container for PydanticAI Agent."""

    agent: "Agent"


@dataclass
class LangChainStack:
    """Container for LangChain ChatModel."""

    chat: "BaseChatModel"


@dataclass
class LLMStack:
    """Combined stack with both PydanticAI and LangChain instances."""

    settings: LLMSettings
    pydantic_ai: PydanticAIStack
    langchain: LangChainStack


def create_pydantic_agent(
    settings: LLMSettings,
    tier: ModelTier = ModelTier.LIGHT,
) -> PydanticAIStack:
    """Create a PydanticAI Agent based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys
        tier: Model tier to use (LIGHT or FULL)
    """
    # Lazy import - only load pydantic_ai when this function is called
    from pydantic_ai import Agent

    model_name = settings.get_model(tier)

    if settings.provider == LLMProvider.OPENAI:
        model_str = f"openai:{model_name}"
    elif settings.provider == LLMProvider.GEMINI:
        model_str = f"google-gla:{model_name}"
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    agent = Agent(
        model_str,
        instructions="You are a helpful assistant.",
    )
    return PydanticAIStack(agent=agent)


def create_langchain_chat(
    settings: LLMSettings | None = None,
    tier: ModelTier = ModelTier.LIGHT,
    search: bool = False,
    temperature: float = 0.2,
    request_timeout: int = 120
) -> LangChainStack:
    """Create a LangChain ChatModel based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys (default: load from .env)
        tier: Model tier to use (LIGHT or FULL)
        search: Enable web search capability (default: False)
        temperature: Model temperature (default 0.2)
        request_timeout: Timeout in seconds (default 120)
    """
    if settings is None:
        settings = LLMSettings()

    model_name = settings.get_model(tier)

    if settings.provider == LLMProvider.OPENAI:
        # Lazy import - only load langchain_openai when needed
        from langchain_openai import ChatOpenAI

        chat = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
            timeout=request_timeout,
        )
        # ...
    elif settings.provider == LLMProvider.GEMINI:
        # Lazy import - only load langchain_google_genai when needed
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Note: Google Search grounding requires specific API setup
        # For now, search parameter is ignored for Gemini
        # Future: implement via google.generativeai native API
        chat = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.google_api_key,
            temperature=temperature,
            timeout=request_timeout,
        )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")

    return LangChainStack(chat=chat)


def create_embeddings(
    settings: LLMSettings | None = None,
) -> "Embeddings":
    """Create an Embeddings model based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys (default: load from .env)

    Returns:
        Embeddings model instance (GoogleGenerativeAIEmbeddings or OpenAIEmbeddings)
    """
    if settings is None:
        settings = LLMSettings()

    if settings.provider == LLMProvider.OPENAI:
        # Lazy import - only load langchain_openai when needed
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
            dimensions=1536,  # Match database vector(1536) column
            chunk_size=100,   # Match our DEFAULT_BATCH_SIZE
        )
    elif settings.provider == LLMProvider.GEMINI:
        # Lazy import - only load langchain_google_genai when needed
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        import langchain_google_genai.embeddings

        # Increase internal token limit to allow larger batches
        # Gemini API supports up to 100 texts or ~20k tokens.
        # LangChain's default estimation is very conservative.
        langchain_google_genai.embeddings._MAX_TOKENS_PER_BATCH = 100000

        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key,
            output_dimensionality=1536,  # Match database vector(1536) column
        )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")


def create_langchain_chat_for_provider(
    provider: LLMProvider,
    settings: LLMSettings | None = None,
    temperature: float = 0.2,
    max_tokens: int = 16000
) -> LangChainStack:
    """Create a LangChain ChatModel with explicit provider selection.

    This function is used for automatic evaluation mode where we need to use
    different providers for answer generation vs judging. It overrides the
    global config provider and always uses FULL tier models.

    Args:
        provider: Explicit provider to use (OPENAI or GEMINI)
        settings: LLM settings with API keys (default: load from .env)
        temperature: Model temperature (default 0.2)
        max_tokens: Maximum tokens to generate (default 16000 for long academic responses)

    Returns:
        LangChainStack with ChatModel for the specified provider

    Examples:
        # Create OpenAI chat for answer generation
        openai_chat = create_langchain_chat_for_provider(LLMProvider.OPENAI)

        # Create Gemini chat for judge evaluation with custom max_tokens
        gemini_chat = create_langchain_chat_for_provider(
            LLMProvider.GEMINI,
            max_tokens=8000
        )
    """
    if settings is None:
        settings = LLMSettings()

    # Always use FULL tier for automatic evaluation
    tier = ModelTier.FULL

    # Get model name for the explicit provider (not from global config)
    if provider == LLMProvider.OPENAI:
        # Lazy import - only load langchain_openai when needed
        from langchain_openai import ChatOpenAI
        from vulcanlab.config import load_config
        import logging

        logger = logging.getLogger(__name__)
        app_config = load_config()
        model_name = app_config.llm.models.openai.full

        logger.info(f"Creating OpenAI ChatModel: model={model_name}, temperature={temperature}, max_tokens={max_tokens}")

        chat = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            verbose=True,  # Enable verbose logging
        )
    elif provider == LLMProvider.GEMINI:
        # Lazy import - only load langchain_google_genai when needed
        from langchain_google_genai import ChatGoogleGenerativeAI
        from vulcanlab.config import load_config
        import logging

        logger = logging.getLogger(__name__)
        app_config = load_config()
        model_name = app_config.llm.models.gemini.full

        logger.info(f"Creating Gemini ChatModel: model={model_name}, temperature={temperature}, max_tokens={max_tokens}")

        chat = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.google_api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,  # Gemini uses max_output_tokens instead of max_tokens
            verbose=True,  # Enable verbose logging
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return LangChainStack(chat=chat)


def create_embeddings_for_provider(
    provider: LLMProvider,
    settings: LLMSettings | None = None,
) -> "Embeddings":
    """Create an Embeddings model with explicit provider selection.

    This function is used for automatic evaluation mode where we need to use
    different providers. It overrides the global config provider.

    Args:
        provider: Explicit provider to use (OPENAI or GEMINI)
        settings: LLM settings with API keys (default: load from .env)

    Returns:
        Embeddings model instance for the specified provider

    Examples:
        # Create OpenAI embeddings
        openai_emb = create_embeddings_for_provider(LLMProvider.OPENAI)

        # Create Gemini embeddings
        gemini_emb = create_embeddings_for_provider(LLMProvider.GEMINI)
    """
    if settings is None:
        settings = LLMSettings()

    if provider == LLMProvider.OPENAI:
        # Lazy import - only load langchain_openai when needed
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
            dimensions=1536,  # Match database vector(1536) column
            chunk_size=100,
        )
    elif provider == LLMProvider.GEMINI:
        # Lazy import - only load langchain_google_genai when needed
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        import langchain_google_genai.embeddings
        
        # Increase internal token limit to allow larger batches
        langchain_google_genai.embeddings._MAX_TOKENS_PER_BATCH = 100000

        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key,
            output_dimensionality=1536,  # Match database vector(1536) column
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_llm_stack(
    tier: ModelTier = ModelTier.LIGHT,
    search: bool = False,
    temperature: float = 0.2
) -> LLMStack:
    """Create a complete LLM stack with both PydanticAI and LangChain.

    Args:
        tier: Model tier to use (LIGHT or FULL)
        search: Enable web search capability (default: False)
        temperature: Model temperature for LangChain (default 0.2)

    Examples:
        # Use default light models from .env
        stack = create_llm_stack()

        # Use full models for complex tasks
        stack = create_llm_stack(tier=ModelTier.FULL)

        # Enable web search
        stack = create_llm_stack(tier=ModelTier.LIGHT, search=True)
    """
    settings = LLMSettings()
    pydantic_stack = create_pydantic_agent(settings, tier=tier)
    langchain_stack = create_langchain_chat(settings, tier=tier, search=search, temperature=temperature)
    return LLMStack(
        settings=settings,
        pydantic_ai=pydantic_stack,
        langchain=langchain_stack,
    )
