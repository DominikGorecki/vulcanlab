# Vectorization Page Documentation

## Overview

The Vectorization page manages the process of generating embeddings for document chunks. Users can view the count of chunks eligible for vectorization and trigger batch vectorization operations.

### Pages

- **Main Page**: `/vec` - View eligible chunks count and vectorize chunks

### User Workflow

1. View count of chunks eligible for vectorization
2. Optionally specify a work ID to vectorize chunks for a specific work
3. Optionally specify a limit on number of chunks to process
4. Click "Vectorize" to start batch vectorization
5. Monitor progress (synchronous operation)
6. Review results (success/failure counts and any errors)

## API Calls

### GET `/vec/eligible`

**Called By**: Main page (`/vec`) on component mount

**Request**: Query parameters: `work_id` (optional integer)

**Response**:
```json
{
  "count": 150,
  "work_id": null
}
```

**Purpose**: Get the count of chunks eligible for vectorization (all works or specific work).

### POST `/vec/vectorize`

**Called By**: Main page (`/vec`) when user clicks "Vectorize" button

**Request**:
```json
{
  "work_id": null,
  "limit": null
}
```

**Response**:
```json
{
  "total_eligible": 150,
  "processed": 150,
  "success": 145,
  "failed": 5,
  "errors": [
    {
      "chunk_id": 42,
      "error": "Embedding dimension mismatch"
    }
  ]
}
```

**Purpose**: Vectorize eligible chunks using embedding model (synchronous batch operation).

## API Implementation Details

### GET `/vec/eligible`

**Router**: `src/vulcanlab_api/routers/vectorization.py` → `get_eligible_count()`

**Processing Steps**:

1. **Call Module Function**: Calls `get_eligible_chunks_count()` from `vulcanLab.vectorization`
2. **Module Processing**:
   - Opens database session
   - Queries `Chunk` table:
     - Filters: `vector_status == 'to_vec'`
     - Filters: `parent_id IS NOT NULL` (excludes top-level heading chunks)
     - Filters: `embedding IS NULL` (not yet vectorized)
     - Optionally filters by `work_id` if provided
   - Returns count of eligible chunks
3. **Return Response**: Returns count and work_id (if specified)

**Modules Called**:
- `vulcanLab.vectorization.vect_chunks.get_eligible_chunks_count()`

**Database Queries**:
- `SELECT COUNT(*) FROM chunks WHERE vector_status = 'to_vec' AND parent_id IS NOT NULL AND embedding IS NULL`
- Optionally: `AND work_id = ?` if work_id provided

**Tables Accessed**: `chunks`

### POST `/vec/vectorize`

**Router**: `src/vulcanlab_api/routers/vectorization.py` → `vectorize_all_chunks(request)`

**Processing Steps**:

1. **Validate Work ID**: If `work_id` provided, verifies work exists in database
2. **Call Module Function**: Calls `vectorize_chunks()` from `vulcanLab.vectorization.vect_chunks`
3. **Module Processing**:
   - Opens database session
   - Queries eligible chunks:
     - Filters: `vector_status == 'to_vec'`
     - Filters: `parent_id IS NOT NULL`
     - Filters: `embedding IS NULL`
     - Optionally filters by `work_id`
     - Optionally limits number of chunks if `limit` provided
     - Orders by `chunk.id` for consistent processing
   - Gets total eligible count
   - Loads embedding model (lazy import):
     - Calls `create_embeddings()` from `vulcanLab.ai.llm_factory`
     - Uses configured embedding model (OpenAI, Gemini, etc.)
   - Processes chunks in batches (default batch_size=20):
     - Extracts chunk content texts
     - Calls `embeddings_model.embed_documents(batch_texts)` to get embeddings
     - For each chunk in batch:
       - Updates `chunk.embedding` with vector (768 dimensions)
       - Updates `chunk.vector_status = 'vec'` (success)
       - On error: Sets `chunk.vector_status = 'vec_err'` and records error
     - Commits batch to database
   - Returns `VectorizationResult` with counts and errors
4. **Format Errors**: Converts error tuples to response format
5. **Return Response**: Returns vectorization results

**Modules Called**:
- `vulcanLab.vectorization.vect_chunks.vectorize_chunks()`
- `vulcanLab.ai.llm_factory.create_embeddings()`

**External API Calls**: Embedding API (OpenAI, Gemini, or other configured provider)

**Database Queries**:
- `SELECT * FROM works WHERE id = ?` (if work_id provided, verify work exists)
- `SELECT COUNT(*) FROM chunks WHERE vector_status = 'to_vec' AND parent_id IS NOT NULL AND embedding IS NULL` (get eligible count)
- `SELECT * FROM chunks WHERE vector_status = 'to_vec' AND parent_id IS NOT NULL AND embedding IS NULL ORDER BY id LIMIT ?` (get chunks to process)
- `UPDATE chunks SET embedding = ?, vector_status = 'vec' WHERE id = ?` (update successful chunks)
- `UPDATE chunks SET vector_status = 'vec_err' WHERE id = ?` (mark failed chunks)

**Tables Accessed**: `works`, `chunks`

## Modules Used

### `vulcanLab.vectorization.vect_chunks`

**Purpose**: Vectorize chunks using embedding models

**Key Functions**:
- `get_eligible_chunks_count(work_id=None)`: Get count of eligible chunks
  - Queries chunks with `vector_status='to_vec'`, `parent_id IS NOT NULL`, `embedding IS NULL`
  - Optionally filters by `work_id`
  - Returns integer count
- `vectorize_chunks(work_id=None, limit=None, batch_size=20, verbose=False)`: Vectorize chunks
  - Gets eligible chunks from database
  - Loads embedding model (lazy import)
  - Processes chunks in batches
  - Calls embedding API for each batch
  - Updates chunk records with embeddings
  - Updates `vector_status` to 'vec' (success) or 'vec_err' (failure)
  - Returns `VectorizationResult` with counts and errors

**External API Calls**: Embedding API (OpenAI, Gemini, etc.)

**Database Tables**: `chunks`, `works`

### `vulcanLab.ai.llm_factory`

**Purpose**: Create embedding models from configuration

**Key Functions**:
- `create_embeddings()`: Create embeddings model
  - Loads configuration from `vulcanLab.config`
  - Creates appropriate embedding model based on config:
     - OpenAI: `OpenAIEmbeddings`
     - Gemini: `GoogleGenerativeAIEmbeddings`
     - Other providers as configured
  - Returns embeddings model instance

**External API Calls**: Embedding API (based on configuration)

**Configuration**: Uses `vulcanLab.config` for API keys and model settings

## Database Tables

### `chunks`

**Schema**: See Corpus documentation for full schema

**Usage in Vectorization**:
- `vector_status`: Status of vectorization
  - `'to_vec'`: Ready for vectorization (not yet processed)
  - `'vec'`: Successfully vectorized
  - `'vec_err'`: Vectorization failed
- `embedding`: Vector embedding (768 dimensions, pgvector type)
  - `NULL` before vectorization
  - Set to embedding vector after successful vectorization
- `parent_id`: Used to filter out top-level heading chunks
  - `NULL`: Top-level heading chunks (not vectorized)
  - `NOT NULL`: Content chunks (eligible for vectorization)

**Query Patterns**:
- `SELECT COUNT(*) FROM chunks WHERE vector_status = 'to_vec' AND parent_id IS NOT NULL AND embedding IS NULL` (get eligible count)
- `SELECT * FROM chunks WHERE vector_status = 'to_vec' AND parent_id IS NOT NULL AND embedding IS NULL ORDER BY id LIMIT ?` (get chunks to process)
- `UPDATE chunks SET embedding = ?, vector_status = 'vec' WHERE id = ?` (update successful chunks)
- `UPDATE chunks SET vector_status = 'vec_err' WHERE id = ?` (mark failed chunks)

### `works`

**Schema**: See Corpus documentation for full schema

**Usage in Vectorization**:
- Used to validate `work_id` if provided
- Not directly modified during vectorization

**Query Patterns**:
- `SELECT * FROM works WHERE id = ?` (verify work exists)

## Vectorization Strategy

### Eligible Chunks

Only content chunks are vectorized (not heading chunks):

- **Heading Chunks**: Top-level chunks with `parent_id IS NULL`
  - Used for hierarchical grouping and context augmentation
  - Not vectorized (structure only)
- **Content Chunks**: Paragraph-level chunks with `parent_id IS NOT NULL`
  - Vectorized for semantic search
  - Must have `vector_status='to_vec'` and `embedding IS NULL`

### Batch Processing

- Chunks processed in batches (default: 20 chunks per batch)
- Batch size configurable via `batch_size` parameter
- Each batch:
  1. Extract chunk content texts
  2. Call embedding API once for entire batch
  3. Update all chunks in batch with embeddings
  4. Commit to database
- Reduces API calls and improves performance

### Error Handling

- Individual chunk failures don't stop batch processing
- Failed chunks marked with `vector_status='vec_err'`
- Errors recorded in `VectorizationResult.errors` list
- Batch-level failures mark all chunks in batch as errors

### Embedding Dimensions

- All embeddings are 768 dimensions (fixed)
- Stored using pgvector `Vector(768)` type
- Compatible with standard embedding models (OpenAI, Gemini, etc.)

## Configuration

Vectorization uses embedding model configuration from `vulcanLab.config`:

- **Model Provider**: OpenAI, Gemini, or other configured provider
- **API Keys**: Loaded from environment variables or config
- **Model Name**: Specific embedding model name (e.g., "text-embedding-3-small")
- **Batch Size**: Default 20 chunks per batch (configurable)

