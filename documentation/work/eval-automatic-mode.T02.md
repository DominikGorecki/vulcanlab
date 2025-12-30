# Ticket: eval-automatic-mode.T02 - LLM Factory Extensions for Multi-Provider Support

## Source

* Spec: documentation/work/eval-automatic-mode.spec.md
* Patterns: documentation/patterns.md

## Goal

* Extend llm_factory to support explicit provider selection
* Create new factory functions that accept provider parameter
* Maintain backwards compatibility with existing factory functions
* Enable automatic mode to use both OpenAI and Gemini simultaneously

## Scope

### In scope

* Create create_langchain_chat_for_provider function that accepts explicit provider parameter
* Create create_embeddings_for_provider function that accepts explicit provider parameter
* Both functions override global config provider and read API keys from .env
* Always use FULL tier models (parameter forced to ModelTier.FULL)
* Add unit tests with mocked LLM clients
* Keep existing factory functions unchanged

### Out of scope

* Modifying existing factory functions (backwards compatibility)
* PydanticAI agent creation for multi-provider (only LangChain needed)
* API key validation logic (handled in T03)
* Automatic eval orchestration (T04)
* UI components

## Dependencies

* Depends on: T01 (for database models)
* Unblocks: T04

## Implementation plan

1. Open src/vulcanlab/ai/llm_factory.py
2. Add create_langchain_chat_for_provider function:
   * Signature: `def create_langchain_chat_for_provider(provider: LLMProvider, settings: LLMSettings | None = None, temperature: float = 0.2) -> LangChainStack`
   * Force tier=ModelTier.FULL
   * If provider is OPENAI, create ChatOpenAI with FULL model
   * If provider is GEMINI, create ChatGoogleGenerativeAI with FULL model
   * Ignore global config provider, use parameter
   * Read API keys from settings (which loads from .env)
3. Add create_embeddings_for_provider function:
   * Signature: `def create_embeddings_for_provider(provider: LLMProvider, settings: LLMSettings | None = None) -> Embeddings`
   * If provider is OPENAI, create OpenAIEmbeddings
   * If provider is GEMINI, create GoogleGenerativeAIEmbeddings
   * Use same embedding models as existing create_embeddings function
4. Ensure existing functions (create_langchain_chat, create_embeddings, create_pydantic_agent, create_llm_stack) remain unchanged
5. Add comprehensive docstrings explaining usage for automatic mode
6. Patterns to apply:
   * Lazy imports - only import LangChain libraries when functions called
   * Configuration pattern - read API keys from .env via LLMSettings
   * Factory pattern - create instances based on provider parameter
* Deviations (if any):
   * None

## Unit tests (required)

* Add tests for:
   * create_langchain_chat_for_provider with provider=LLMProvider.OPENAI creates ChatOpenAI with FULL model
   * create_langchain_chat_for_provider with provider=LLMProvider.GEMINI creates ChatGoogleGenerativeAI with FULL model
   * create_embeddings_for_provider with provider=LLMProvider.OPENAI creates OpenAIEmbeddings
   * create_embeddings_for_provider with provider=LLMProvider.GEMINI creates GoogleGenerativeAIEmbeddings
   * Settings defaults work correctly (None parameter)
   * Temperature parameter passed correctly to chat model
   * Invalid provider raises ValueError
* Suggested locations:
   * tests/unit/test_llm_factory_multi_provider.py (create new)
* Mocking/fakes needed:
   * Mock LLMSettings to return fake API keys
   * Mock ChatOpenAI and ChatGoogleGenerativeAI constructors
   * Mock OpenAIEmbeddings and GoogleGenerativeAIEmbeddings constructors
   * Patch lazy imports to avoid loading actual LangChain libraries

## Acceptance criteria (checklist)

* [ ] create_langchain_chat_for_provider function created
* [ ] create_embeddings_for_provider function created
* [ ] Both functions accept explicit provider parameter
* [ ] Both functions use FULL tier models
* [ ] Functions read API keys from .env via LLMSettings
* [ ] Functions override global config provider
* [ ] Existing factory functions unchanged
* [ ] Unit tests pass for both OpenAI and Gemini providers
* [ ] Docstrings explain usage for automatic mode
* [ ] Code follows lazy import pattern

## Manual verification

* Steps:
  1. Create test script that calls create_langchain_chat_for_provider with OPENAI
  2. Verify ChatOpenAI instance created with FULL model name
  3. Call create_langchain_chat_for_provider with GEMINI
  4. Verify ChatGoogleGenerativeAI instance created with FULL model name
  5. Call create_embeddings_for_provider with both providers
  6. Verify correct embedding model instances created
  7. Verify existing create_langchain_chat still works with global config
* Expected results:
  * New functions create correct LLM instances
  * FULL tier models used (e.g., gpt-4o, gemini-1.5-pro)
  * API keys read from .env correctly
  * Existing functions unaffected
  * No import errors or lazy loading issues

## Notes

* Requirements covered: R10, R12, R13
* Always use ModelTier.FULL - no parameter for tier selection
* Backwards compatibility critical: do not modify existing functions
* API key validation happens in T03, not here
* These functions will be used by automatic eval orchestration in T04
