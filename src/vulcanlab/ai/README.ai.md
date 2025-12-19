# vulcanlab/ai (AI README)

## Purpose
- Provides a unified abstraction layer for Large Language Model (LLM) providers.
- Handles configuration, model tier selection, and factory instantiation for both PydanticAI and LangChain.
- Ensures consistent LLM behavior across the VulcanLab ecosystem while keeping resource usage low via lazy imports.

## Quick start
- To use the default configured LLM stack:
  ```python
  from vulcanlab.ai import create_llm_stack
  stack = create_llm_stack()
  # access stack.pydantic_ai.agent or stack.langchain.chat
  ```
- To create a specific model tier:
  ```python
  from vulcanlab.ai import create_llm_stack, ModelTier
  stack = create_llm_stack(tier=ModelTier.FULL)
  ```
- To create embeddings:
  ```python
  from vulcanlab.ai import create_embeddings
  embeddings = create_embeddings()
  ```

## Architecture overview
- **Lazy Loading**: Heavy ML libraries (LangChain, PydanticAI) are imported only when factory functions are called, preventing slow application startup.
- **Configuration Management**: Settings are merged from `vulcanlab.config.json` (model names/providers) and `.env` (API keys).
- **Model Tiers**: Abstracts models into `LIGHT` and `FULL` tiers, allowing components to request capabilities rather than specific model strings.
- **Provider Abstraction**: Currently supports OpenAI and Google Gemini via a consistent interface.

Key folders:
- `src/vulcanlab/ai` - Root of the AI module containing config and factory logic.

## Entry points and main flows
- Entry points:
  - `src/vulcanlab/ai/llm_factory.py` - Primary source of factory functions: `create_llm_stack`, `create_pydantic_agent`, `create_langchain_chat`, `create_embeddings`.
  - `src/vulcanlab/ai/config.py` - Configuration and settings management.
- Typical flows:
  - **Initialization**: `LLMSettings` searches upward for `.env`, loads secrets, and reads provider/model mapping from the global `load_config()`.
  - **Agent Creation**: `create_pydantic_agent` maps the requested tier to a model string (e.g., `openai:gpt-4o-mini`) and initializes a `PydanticAI` Agent.
  - **Chat Creation**: `create_langchain_chat` initializes a `ChatOpenAI` or `ChatGoogleGenerativeAI` instance with appropriate parameters like temperature and search grounding.

## Key conventions
- **Naming**: Uses `LLMStack` to represent a bundle of configuration and active model instances.
- **Layering**: Separates configuration logic (`config.py`) from instantiation logic (`llm_factory.py`).
- **Error Handling**: Raises `ValueError` for unsupported providers or missing configurations.
- **Lazy Imports**: All heavy library imports (`langchain_*`, `pydantic_ai`) must remain inside function scopes or behind `TYPE_CHECKING` blocks.

## Dependencies overview
- Runtime dependencies:
  - `pydantic-settings`: For environment-based configuration.
  - `pydantic-ai`: For type-safe agent interactions.
  - `langchain-core`: Base interfaces for LangChain components.
  - `langchain-openai` / `langchain-google-genai`: Provider-specific implementations.
- Dev dependencies and tooling:
  - `vulcanlab.config`: Internal configuration loader.

## APIs and contracts
- **Data Models**:
  - `LLMSettings`: Pydantic model for API keys and model selection logic.
  - `LLMStack`: Dataclass containing `settings`, `pydantic_ai` stack, and `langchain` stack.
- **Interfaces**:
  - `create_embeddings()` -> `langchain_core.embeddings.Embeddings`
  - `create_langchain_chat(...)` -> `LangChainStack`
  - `create_pydantic_agent(...)` -> `PydanticAIStack`

## Subfolders
(No subfolders present in this directory.)

## File tree (depth 3)
/home/dardawk/python/vulcanlab/src/vulcanlab/ai/
  - __init__.py
  - config.py
  - llm_factory.py

## LLM handoff
- When asking an LLM to work in this folder, include:
  - `src/vulcanlab/ai/llm_factory.py` (Main implementation)
  - `src/vulcanlab/ai/config.py` (Configuration logic)
  - `src/vulcanlab/ai/__init__.py` (Public API exports)
- Good first questions to ask:
  - "How do I add a new LLM provider like Anthropic?"
  - "Where are the default model names defined?"
  - "How does the lazy loading mechanism work in `__init__.py`?"
- Guardrails:
  - **Do NOT** move heavy imports to the top of files; keep them in functions to preserve lazy loading.
  - **Do NOT** hardcode model names in `llm_factory.py`; use `LLMSettings` and `vulcanlab.config.json`.
  - Ensure any new provider supports both PydanticAI and LangChain if adding to the stack.

## Gotchas
- **Env Discovery**: `LLMSettings` searches up to 10 levels for a `.env` file; ensure the file is in a parent directory.
- **Gemini Search**: Web search grounding is currently a placeholder for Gemini in `create_langchain_chat`.
- **Model Tiers**: `ModelTier.LIGHT` and `ModelTier.FULL` must be correctly mapped in the global configuration or it will fall back to hardcoded defaults or raise errors.
- **Lazy Import Complexity**: Adding new exports to `__init__.py` requires updating both `__all__` and `__getattr__`.
