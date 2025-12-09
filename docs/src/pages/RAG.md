# RAG Page Documentation

## Overview

The RAG (Retrieval-Augmented Generation) page manages the complete RAG pipeline for answering queries using document chunks. Users create queries, expand them, retrieve relevant chunks, consolidate context, and generate LLM responses.

### Pages

- **Main Page**: `/rag` - List all queries and manage RAG pipeline
- **New Query**: `/rag/new` - Create a new query with expansion
- **Query Response**: `/rag/[id]` - Generate response for a query
- **Inspect Query**: `/rag/[id]/inspect` - Inspect query details and pipeline status
- **Query Results**: `/rag/[id]/results` - List all results for a query
- **View Result**: `/rag/[id]/results/[resultId]` - View a specific result

### User Workflow

1. Create a new query (original question)
2. Expand query (generates MQE queries and HyDE answer)
3. Vectorize query (creates embeddings for original, MQE, and HyDE)
4. Retrieve chunks (dense + lexical retrieval with reranking)
5. Consolidate context (group chunks under parents, merge adjacent)
6. Generate augmented prompt (combine query with retrieved context)
7. Run LLM or paste manual response
8. View results

## API Calls

### GET `/rag/queries`

**Called By**: Main page (`/rag`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "queries": [
    {
      "id": 1,
      "original_query": "What is working memory?",
      "intent": "DEFINITION",
      "vector_status": "vec",
      "has_retrieved_context": true,
      "has_clean_context": true,
      "results_count": 2
    }
  ],
  "total": 10
}
```

**Purpose**: List all queries with pipeline status information.

### GET `/rag/queries/{id}`

**Called By**: Query response page (`/rag/[id]`) on component mount

**Request**: Path parameter `id` (integer)

**Response**:
```json
{
  "id": 1,
  "original_query": "What is working memory?",
  "expanded_queries": [
    "What is the definition of working memory?",
    "How does working memory function?"
  ],
  "hyde_answer": "Working memory is a cognitive system...",
  "intent": "DEFINITION",
  "entities": ["working memory", "cognitive system"],
  "vector_status": "vec",
  "retrieved_context": [...],
  "clean_retrieval_context": [...],
  "available_context_count": 15
}
```

**Purpose**: Get detailed query information including expansion, embeddings, and retrieved context.

### PATCH `/rag/queries/{id}`

**Called By**: Query response page when user edits query fields

**Request**:
```json
{
  "original_query": "Updated question",
  "intent": "MECHANISM"
}
```

**Response**: Updated query object

**Purpose**: Update query fields (original_query, intent, entities, etc.).

### POST `/rag/queries/{id}/embed`

**Called By**: Main page or query response page when user clicks "Embed"

**Request**: No body

**Response**:
```json
{
  "success": true,
  "message": "Query vectorized successfully",
  "vector_status": "vec"
}
```

**Purpose**: Vectorize query (original, MQE queries, and HyDE answer).

### POST `/rag/queries/{id}/retrieve`

**Called By**: Main page or query response page when user clicks "Retrieve"

**Request**: No body

**Response**:
```json
{
  "success": true,
  "message": "Retrieved 15 chunks",
  "chunks_retrieved": 15
}
```

**Purpose**: Retrieve relevant chunks using dense + lexical retrieval with reranking.

### POST `/rag/queries/{id}/consolidate`

**Called By**: Main page or query response page when user clicks "Consolidate"

**Request**: No body

**Response**:
```json
{
  "success": true,
  "message": "Consolidated 15 chunks into 8 groups",
  "original_count": 15,
  "consolidated_count": 8
}
```

**Purpose**: Consolidate retrieved chunks by grouping under parents and merging adjacent chunks.

### GET `/rag/queries/{id}/augment/prompt`

**Called By**: Query response page (`/rag/[id]`) on component mount and when user changes top_n

**Request**: Query parameters: `top_n` (integer, default: 5)

**Response**:
```json
{
  "prompt": "You are an expert...\n\nQuery: What is working memory?\n\nContext:\n[Chunk 1]...",
  "context_count": 5
}
```

**Purpose**: Generate augmented prompt combining query with top N retrieved contexts.

### POST `/rag/queries/{id}/augment/run`

**Called By**: Query response page when user clicks "Run LLM"

**Request**:
```json
{
  "top_n": 5,
  "use_full_model": false
}
```

**Response**:
```json
{
  "success": true,
  "result_id": 42,
  "response_text": "Working memory is a cognitive system..."
}
```

**Purpose**: Run augmented prompt with LLM and save response as result.

### POST `/rag/queries/{id}/augment/manual`

**Called By**: Query response page when user pastes manual response

**Request**:
```json
{
  "response_text": "Working memory is a cognitive system...",
  "top_n": 5
}
```

**Response**:
```json
{
  "success": true,
  "result_id": 42,
  "message": "Response saved successfully"
}
```

**Purpose**: Save manually provided LLM response as result.

### GET `/rag/queries/{id}/results`

**Called By**: Query results page (`/rag/[id]/results`) on component mount

**Request**: Path parameter `id` (integer)

**Response**:
```json
{
  "results": [
    {
      "id": 42,
      "response_text": "Working memory is a cognitive system...",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 2
}
```

**Purpose**: List all results for a query.

### GET `/rag/queries/{id}/results/{resultId}`

**Called By**: View result page (`/rag/[id]/results/[resultId]`) on component mount

**Request**: Path parameters: `id` (query ID), `resultId` (result ID)

**Response**:
```json
{
  "id": 42,
  "query_id": 1,
  "response_text": "Working memory is a cognitive system...",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Purpose**: Get a specific result by ID.

### POST `/rag/expansion/prompt`

**Called By**: New query page (`/rag/new`) to show prompt before running

**Request**:
```json
{
  "original_query": "What is working memory?"
}
```

**Response**:
```json
{
  "prompt": "You are an expert...",
  "query": "What is working memory?"
}
```

**Purpose**: Generate expansion prompt without executing LLM.

### POST `/rag/expansion/run`

**Called By**: New query page when user clicks "Run Expansion"

**Request**:
```json
{
  "original_query": "What is working memory?",
  "use_full_model": true
}
```

**Response**:
```json
{
  "success": true,
  "query_id": 1,
  "expanded_queries": [
    "What is the definition of working memory?",
    "How does working memory function?"
  ],
  "hyde_answer": "Working memory is a cognitive system...",
  "intent": "DEFINITION",
  "entities": ["working memory"]
}
```

**Purpose**: Run full query expansion with LLM and create query record.

### POST `/rag/expansion/manual`

**Called By**: New query page when user pastes manual expansion response

**Request**:
```json
{
  "original_query": "What is working memory?",
  "llm_response": "Here are the expanded queries..."
}
```

**Response**:
```json
{
  "success": true,
  "query_id": 1,
  "message": "Query created successfully"
}
```

**Purpose**: Parse and save manual expansion response as query record.

## API Implementation Details

### GET `/rag/queries`

**Router**: `src/vulcanlab_api/routers/rag.py` → `list_queries()`

**Processing Steps**:

1. **Query All Queries**: `session.query(Query).order_by(Query.id.desc()).all()`
2. **Build Query Items**: For each query:
   - Extracts `id`, `original_query`, `intent`
   - Gets `vector_status` from query
   - Checks `retrieved_context` exists → `has_retrieved_context`
   - Checks `clean_retrieval_context` exists → `has_clean_context`
   - Counts results: `session.query(Result).filter(Result.query_id == query.id).count()`
3. **Return Response**: Returns query list with total count

**Database Queries**:
- `SELECT * FROM queries ORDER BY id DESC`
- `SELECT COUNT(*) FROM results WHERE query_id = ?` (for each query)

**Tables Accessed**: `queries`, `results`

### POST `/rag/queries/{id}/embed`

**Router**: `src/vulcanlab_api/routers/rag.py` → `vectorize_query(query_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `vectorize_query()` from `vulcanLab.retrieval`
2. **Module Processing**:
   - Gets `Query` by ID
   - Loads embedding model (lazy import)
   - Vectorizes original query: `embeddings_model.embed_query(query.original_query)`
   - Vectorizes MQE queries: `embeddings_model.embed_documents(expanded_queries)`
   - Vectorizes HyDE answer: `embeddings_model.embed_query(query.hyde_answer)`
   - Updates query:
     - `embedding_original`: original query embedding
     - `embeddings_mqe`: array of MQE query embeddings
     - `embedding_hyde`: HyDE answer embedding
     - `vector_status`: "vec"
   - Commits database changes
3. **Return Response**: Returns success status

**Modules Called**:
- `vulcanLab.retrieval.query_embeddings.vectorize_query()`
- `vulcanLab.ai.llm_factory.create_embeddings()`

**External API Calls**: Embedding API (OpenAI, Gemini, etc.)

**Database Queries**:
- `SELECT * FROM queries WHERE id = ?`
- `UPDATE queries SET embedding_original = ?, embeddings_mqe = ?, embedding_hyde = ?, vector_status = 'vec' WHERE id = ?`

**Tables Accessed**: `queries`

### POST `/rag/queries/{id}/retrieve`

**Router**: `src/vulcanlab_api/routers/rag.py` → `retrieve_chunks(query_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `retrieve()` from `vulcanLab.retrieval`
2. **Module Processing**:
   - Gets `Query` by ID
   - Validates query has embeddings (`vector_status == 'vec'`)
   - Loads RAG config (retrieval parameters)
   - **Dense Retrieval**:
     - Uses pgvector similarity search with original query embedding
     - Uses pgvector similarity search with MQE query embeddings
     - Uses pgvector similarity search with HyDE embedding
     - Combines results with max pooling
   - **Lexical Retrieval**:
     - Uses PostgreSQL full-text search (`ts_rank`, `tsvector`)
     - Searches against chunk content
   - **RRF Fusion**:
     - Combines dense and lexical ranks using Reciprocal Rank Fusion
     - Formula: `RRF(d, k) = 1 / (k + rank)`
   - **BGE Reranking**:
     - Loads BGE reranking model (`BAAI/bge-reranker-base`)
     - Reranks top candidates with entity/intent bias
     - Entity boost: increases score for chunks mentioning extracted entities
     - Intent boost: adjusts score based on query intent
   - **Final Selection**:
     - Selects top N chunks (default: 15)
     - Stores in `query.retrieved_context` as JSON array
     - Each chunk includes: id, content, scores, metadata
   - Commits database changes
3. **Return Response**: Returns success status and chunk count

**Modules Called**:
- `vulcanLab.retrieval.retrieve.retrieve()`
- `vulcanLab.utils.rag_config_loader.get_default_config()`

**External API Calls**: None (uses local models and database)

**Database Queries**:
- `SELECT * FROM queries WHERE id = ?`
- `SELECT *, embedding <-> ? AS distance FROM chunks WHERE embedding IS NOT NULL ORDER BY distance LIMIT ?` (dense retrieval)
- `SELECT *, ts_rank(to_tsvector(content), query) AS rank FROM chunks WHERE to_tsvector(content) @@ query ORDER BY rank DESC LIMIT ?` (lexical retrieval)
- `UPDATE queries SET retrieved_context = ? WHERE id = ?`

**Tables Accessed**: `queries`, `chunks`

### POST `/rag/queries/{id}/consolidate`

**Router**: `src/vulcanlab_api/routers/rag.py` → `consolidate_context(query_id)`

**Processing Steps**:

1. **Call Module Function**: Calls `consolidate_context()` from `vulcanLab.augmentation`
2. **Module Processing**:
   - Gets `Query` by ID
   - Gets `retrieved_context` from query
   - **Group by Parent**:
     - Groups chunks under their parent heading chunks
     - Creates parent groups with all child chunks
   - **Merge Adjacent**:
     - Merges chunks from same work that are close in line numbers
     - Default line gap: 7 lines
     - Combines content and takes max score
   - **Filter by Coverage**:
     - Removes groups with low coverage (default threshold: 0.5)
   - **Enrich from Markdown**:
     - Reads actual markdown files to get full content
     - Replaces chunk content with enriched content from files
   - **Final Selection**:
     - Filters groups by minimum content length (default: 350 chars)
     - Stores in `query.clean_retrieval_context` as JSON array
     - Each group includes: chunk_ids, parent_id, work_id, content, heading_chain, score
   - Commits database changes
3. **Return Response**: Returns success status and consolidation counts

**Modules Called**:
- `vulcanLab.augmentation.consolidate_context.consolidate_context()`
- `vulcanLab.utils.rag_config_loader.get_default_config()`

**File System Operations**: Reads sanitized markdown files to enrich content

**Database Queries**:
- `SELECT * FROM queries WHERE id = ?`
- `SELECT * FROM chunks WHERE id IN (...) AND parent_id IS NULL` (get parent chunks)
- `UPDATE queries SET clean_retrieval_context = ? WHERE id = ?`

**Tables Accessed**: `queries`, `chunks`, `works`

### GET `/rag/queries/{id}/augment/prompt`

**Router**: `src/vulcanlab_api/routers/rag.py` → `get_augmented_prompt(query_id, top_n)`

**Processing Steps**:

1. **Call Module Function**: Calls `generate_augmented_prompt()` from `vulcanLab.augmentation`
2. **Module Processing**:
   - Gets `Query` by ID
   - Gets `clean_retrieval_context` from query (or `retrieved_context` if clean not available)
   - Selects top N contexts (default: 5)
   - Loads prompt template from database (function_tag: "rag_augmentation")
   - Formats contexts as markdown blocks:
     - Each context includes heading breadcrumbs and content
     - Format: `## [Work Title] > Heading > Subheading\n\nContent...`
   - Builds prompt with template variables:
     - `{query}`: original query
     - `{contexts}`: formatted context blocks
     - `{intent}`: query intent (if available)
     - `{entities}`: extracted entities (if available)
   - Returns prompt string
3. **Return Response**: Returns prompt and context count

**Modules Called**:
- `vulcanLab.augmentation.augment.generate_augmented_prompt()`
- `vulcanLab.data.template_loader.load_template()`

**Database Queries**:
- `SELECT * FROM queries WHERE id = ?`
- `SELECT * FROM prompt_meta WHERE function_tag = 'rag_augmentation'` (template loading)
- `SELECT * FROM works WHERE id = ?` (get work titles for context formatting)

**Tables Accessed**: `queries`, `prompt_meta`, `works`

### POST `/rag/queries/{id}/augment/run`

**Router**: `src/vulcanlab_api/routers/rag.py` → `run_augmented_prompt(query_id, request)`

**Processing Steps**:

1. **Generate Prompt**: Calls `generate_augmented_prompt()` to get prompt
2. **Call LLM**: 
   - Creates LLM chat instance (LIGHT or FULL model based on `use_full_model`)
   - Calls `llm.chat.invoke(prompt)`
   - Extracts response text
3. **Save Result**:
   - Creates `Result` object:
     - `query_id`: query ID
     - `response_text`: LLM response
   - Inserts into database
   - Commits changes
4. **Return Response**: Returns success status and result ID

**Modules Called**:
- `vulcanLab.augmentation.augment.generate_augmented_prompt()`
- `vulcanLab.ai.llm_factory.create_langchain_chat()`

**External API Calls**: LLM API (OpenAI or Gemini)

**Database Queries**:
- `SELECT * FROM queries WHERE id = ?`
- `INSERT INTO results (query_id, response_text) VALUES (?, ?)`

**Tables Accessed**: `queries`, `results`

### POST `/rag/expansion/run`

**Router**: `src/vulcanlab_api/routers/rag.py` → `run_expansion(request)`

**Processing Steps**:

1. **Call Module Function**: Calls `expand_query()` from `vulcanLab.retrieval`
2. **Module Processing**:
   - Loads prompt template from database (function_tag: "query_expansion")
   - Builds prompt with original query
   - Creates LLM chat instance (FULL model for expansion)
   - Calls `llm.chat.invoke(prompt)`
   - Parses LLM response:
     - Extracts MQE expanded queries (list)
     - Extracts HyDE answer (hypothetical document)
     - Extracts intent (DEFINITION, MECHANISM, etc.)
     - Extracts entities (names, theories, keywords)
   - Creates `Query` object:
     - `original_query`: original query text
     - `expanded_queries`: JSON array of MQE queries
     - `hyde_answer`: hypothetical document text
     - `intent`: extracted intent
     - `entities`: JSON array of entities
     - `vector_status`: "no_vec" (not yet vectorized)
   - Inserts into database
   - Commits changes
3. **Return Response**: Returns success status and query ID

**Modules Called**:
- `vulcanLab.retrieval.query_expansion.expand_query()`
- `vulcanLab.data.template_loader.load_template()`
- `vulcanLab.ai.llm_factory.create_langchain_chat()`

**External API Calls**: LLM API (OpenAI or Gemini) - FULL model

**Database Queries**:
- `SELECT * FROM prompt_meta WHERE function_tag = 'query_expansion'` (template loading)
- `INSERT INTO queries (...) VALUES (...)`

**Tables Accessed**: `queries`, `prompt_meta`

## Modules Used

### `vulcanLab.retrieval.query_expansion`

**Purpose**: Expand queries using LLM

**Key Functions**:
- `expand_query(original_query, use_full_model, verbose)`: Run full expansion
  - Builds prompt with template
  - Calls LLM (FULL model)
  - Parses response to extract MQE queries, HyDE answer, intent, entities
  - Creates and saves Query record
  - Returns `QueryExpansionResult`
- `generate_expansion_prompt(original_query)`: Build prompt without executing
  - Returns prompt string
- `parse_expansion_response(response_text)`: Parse LLM response
  - Extracts structured data from response
  - Returns `ParsedExpansion` object
- `save_expansion_to_db(original_query, parsed_expansion)`: Save to database
  - Creates Query record
  - Returns query ID

**External API Calls**: LLM API (FULL model)

**Database Tables**: `queries`, `prompt_meta`

### `vulcanLab.retrieval.query_embeddings`

**Purpose**: Vectorize queries

**Key Functions**:
- `vectorize_query(query_id, verbose)`: Vectorize a single query
  - Gets Query by ID
  - Loads embedding model
  - Vectorizes original query, MQE queries, and HyDE answer
  - Updates query with embeddings
  - Sets `vector_status = 'vec'`
  - Returns `QueryVectorizationResult`

**External API Calls**: Embedding API

**Database Tables**: `queries`

### `vulcanLab.retrieval.retrieve`

**Purpose**: Retrieve relevant chunks using hybrid search

**Key Functions**:
- `retrieve(query_id, verbose)`: Run full retrieval pipeline
  - Gets Query by ID
  - Validates embeddings exist
  - **Dense Retrieval**: pgvector similarity search with all query embeddings
  - **Lexical Retrieval**: PostgreSQL full-text search
  - **RRF Fusion**: Combines dense and lexical ranks
  - **BGE Reranking**: Reranks with entity/intent bias
  - Stores results in `query.retrieved_context`
  - Returns `RetrievalResult`

**External Dependencies**: BGE reranking model (`BAAI/bge-reranker-base`)

**Database Tables**: `queries`, `chunks`

### `vulcanLab.augmentation.consolidate_context`

**Purpose**: Consolidate retrieved chunks

**Key Functions**:
- `consolidate_context(query_id, verbose)`: Run consolidation
  - Gets Query by ID and retrieved_context
  - Groups chunks under parent headings
  - Merges adjacent chunks from same work
  - Filters by coverage threshold
  - Enriches content from markdown files
  - Filters by minimum content length
  - Stores in `query.clean_retrieval_context`
  - Returns `ConsolidationResult`

**File System Operations**: Reads sanitized markdown files

**Database Tables**: `queries`, `chunks`, `works`

### `vulcanLab.augmentation.augment`

**Purpose**: Generate augmented prompts

**Key Functions**:
- `generate_augmented_prompt(query_id, top_n)`: Generate prompt
  - Gets Query by ID
  - Gets clean_retrieval_context (or retrieved_context)
  - Selects top N contexts
  - Formats contexts as markdown blocks
  - Loads prompt template
  - Builds prompt with query and contexts
  - Returns prompt string

**Database Tables**: `queries`, `prompt_meta`, `works`

### `vulcanLab.ai.llm_factory`

**Purpose**: Create LLM and embedding models

**Key Functions**: See Vectorization documentation

**External API Calls**: LLM API, Embedding API

### `vulcanLab.data.template_loader`

**Purpose**: Load prompt templates from database

**Key Functions**: See Sanitization documentation

**Database Tables**: `prompt_meta`

### `vulcanLab.utils.rag_config_loader`

**Purpose**: Load RAG configuration presets

**Key Functions**:
- `get_default_config()`: Get default RAG config
  - Loads from `RagConfig` table (preset_name: "default")
  - Returns config dict with retrieval parameters
- `get_config_by_name(preset_name)`: Get config by preset name
  - Loads from `RagConfig` table
  - Returns config dict

**Database Tables**: `rag_config`

## Database Tables

### `queries`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `original_query` (TEXT, NOT NULL)
- `expanded_queries` (JSON, NULLABLE) - Array of MQE expanded queries
- `hyde_answer` (TEXT, NULLABLE) - Hypothetical document embedding answer
- `intent` (VARCHAR(50), NULLABLE, INDEXED) - Query intent (DEFINITION, MECHANISM, etc.)
- `entities` (JSON, NULLABLE) - Array of extracted entities
- `embedding_original` (VECTOR(768), NULLABLE) - Original query embedding
- `embeddings_mqe` (JSON, NULLABLE) - Array of MQE query embeddings
- `embedding_hyde` (VECTOR(768), NULLABLE) - HyDE answer embedding
- `vector_status` (VARCHAR(10), NOT NULL, INDEXED) - Status (no_vec, to_vec, vec, vec_err)
- `retrieved_context` (JSON, NULLABLE) - Retrieved chunks with scores
- `clean_retrieval_context` (JSON, NULLABLE) - Consolidated chunks
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Usage in RAG**:
- Stores query expansion results (MQE, HyDE, intent, entities)
- Stores query embeddings (original, MQE, HyDE)
- Stores retrieved chunks (before consolidation)
- Stores consolidated chunks (after consolidation)

**Query Patterns**:
- `SELECT * FROM queries ORDER BY id DESC` (list all queries)
- `SELECT * FROM queries WHERE id = ?` (get query by ID)
- `INSERT INTO queries (...) VALUES (...)` (create new query)
- `UPDATE queries SET embedding_original = ?, ... WHERE id = ?` (update embeddings)
- `UPDATE queries SET retrieved_context = ? WHERE id = ?` (update retrieved chunks)
- `UPDATE queries SET clean_retrieval_context = ? WHERE id = ?` (update consolidated chunks)

### `results`

**Schema**: See Corpus documentation for full schema

**Usage in RAG**:
- Stores LLM responses for queries
- One query can have multiple results (multiple runs)
- Linked to query via `query_id` foreign key

**Query Patterns**:
- `SELECT * FROM results WHERE query_id = ? ORDER BY created_at DESC` (list results for query)
- `SELECT * FROM results WHERE id = ?` (get result by ID)
- `INSERT INTO results (query_id, response_text) VALUES (?, ?)` (create new result)
- `SELECT COUNT(*) FROM results WHERE query_id = ?` (count results for query)

### `chunks`

**Schema**: See Corpus documentation for full schema

**Usage in RAG**:
- Queried for dense retrieval (pgvector similarity search)
- Queried for lexical retrieval (PostgreSQL full-text search)
- Must have `embedding IS NOT NULL` for dense retrieval
- `heading_breadcrumbs` used for context formatting

**Query Patterns**:
- `SELECT *, embedding <-> ? AS distance FROM chunks WHERE embedding IS NOT NULL ORDER BY distance LIMIT ?` (dense retrieval)
- `SELECT *, ts_rank(to_tsvector(content), query) AS rank FROM chunks WHERE to_tsvector(content) @@ query ORDER BY rank DESC LIMIT ?` (lexical retrieval)
- `SELECT * FROM chunks WHERE id IN (...) AND parent_id IS NULL` (get parent chunks for consolidation)

### `rag_config`

**Schema**:
- `id` (INTEGER, PRIMARY KEY)
- `preset_name` (VARCHAR, NOT NULL, UNIQUE) - e.g., "default"
- `config` (JSON, NOT NULL) - RAG configuration parameters
- `description` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Usage in RAG**:
- Stores RAG configuration presets
- Config includes: retrieval parameters, reranking parameters, consolidation parameters
- Default preset: "default"

**Query Patterns**:
- `SELECT * FROM rag_config WHERE preset_name = 'default'` (get default config)
- `SELECT * FROM rag_config WHERE preset_name = ?` (get config by preset name)

### `prompt_meta`

**Schema**: See Sanitization documentation for full schema

**Usage in RAG**:
- Stores prompt templates for RAG operations
- `function_tag="query_expansion"`: Template for query expansion
- `function_tag="rag_augmentation"`: Template for augmented prompt generation

**Query Patterns**:
- `SELECT * FROM prompt_meta WHERE function_tag = 'query_expansion'` (get expansion template)
- `SELECT * FROM prompt_meta WHERE function_tag = 'rag_augmentation'` (get augmentation template)

## RAG Pipeline Stages

### 1. Query Expansion

- **Input**: Original user query
- **Process**: LLM generates MQE queries, HyDE answer, intent, entities
- **Output**: Query record with expansion data
- **Status**: `vector_status = "no_vec"`

### 2. Query Vectorization

- **Input**: Query with expansion data
- **Process**: Generate embeddings for original query, MQE queries, HyDE answer
- **Output**: Query record with embeddings
- **Status**: `vector_status = "vec"`

### 3. Retrieval

- **Input**: Query with embeddings
- **Process**: 
  - Dense retrieval (pgvector similarity)
  - Lexical retrieval (PostgreSQL full-text search)
  - RRF fusion
  - BGE reranking with entity/intent bias
- **Output**: Query record with `retrieved_context`
- **Status**: `has_retrieved_context = true`

### 4. Consolidation

- **Input**: Query with retrieved_context
- **Process**:
  - Group chunks under parent headings
  - Merge adjacent chunks
  - Filter by coverage and content length
  - Enrich from markdown files
- **Output**: Query record with `clean_retrieval_context`
- **Status**: `has_clean_context = true`

### 5. Augmentation & Generation

- **Input**: Query with clean_retrieval_context
- **Process**:
  - Generate augmented prompt (query + top N contexts)
  - Run LLM or paste manual response
- **Output**: Result record with response_text
- **Status**: `results_count > 0`

