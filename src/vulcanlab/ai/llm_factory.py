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
    temperature: float = 0.2
) -> LangChainStack:
    """Create a LangChain ChatModel based on the configured provider.

    Args:
        settings: LLM settings with provider and API keys (default: load from .env)
        tier: Model tier to use (LIGHT or FULL)
        search: Enable web search capability (default: False)
        temperature: Model temperature (default 0.2)
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
        )
        # Note: OpenAI web search would require additional tools/plugins
        # This is a placeholder for future implementation
        if search:
            # Web search for OpenAI would be implemented via function calling
            pass
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
        )
    elif settings.provider == LLMProvider.GEMINI:
        # Lazy import - only load langchain_google_genai when needed
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key,
        )
    else:
        raise ValueError(f"Unsupported provider: {settings.provider}")


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
