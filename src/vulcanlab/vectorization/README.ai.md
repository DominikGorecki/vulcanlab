# src/vulcanlab/vectorization

**Purpose**: Creates vector embeddings for document chunks using OpenAI or Google embedding models, storing them in PostgreSQL with pgvector extension for semantic similarity search and retrieval.

## Module Overview

### Core Vectorization

#### [vect_chunks.py](vect_chunks.py)
Core vectorization implementation for processing document chunks into vector embeddings.

**Key Components**:

**Classes**:
- `VectorizationResult` (dataclass) - Result container for vectorization operations
  - `total_eligible: int` - Total chunks available for vectorization
  - `processed: int` - Chunks actually processed
  - `success: int` - Successfully vectorized chunks
  - `failed: int` - Failed vectorization attempts
  - `errors: list[tuple[int, str]]` - List of (chunk_id, error_message) pairs

**Functions**:
- `get_eligible_chunks_count(work_id: int | None = None) -> int`
  - Returns count of chunks ready for vectorization
  - Filters: `vector_status == 'to_vec'` AND `parent_id IS NOT NULL` AND `embedding IS NULL`
  - `work_id=None` counts across all works
  - Lightweight query (no ML libraries loaded)

- `vectorize_chunks(work_id: int | None, limit: int | None, batch_size: int = 20, verbose: bool = False) -> VectorizationResult`
  - Main vectorization function
  - Processes chunks in configurable batches
  - Updates `embedding` field with 768-dimensional vectors
  - Sets `vector_status` to `'vec'` (success) or `'vec_err'` (failure)
  - Commits after each batch for transaction safety
  - Returns detailed result with error tracking

**Workflow**:
1. Validates work exists (if work_id specified)
2. Queries eligible chunks ordered by ID
3. Lazy-imports embeddings model from `vulcanlab.ai.llm_factory`
4. Processes chunks in batches (default: 20 chunks/batch)
5. Updates each chunk's embedding field
6. Tracks success/failure per chunk
7. Commits per-batch for partial retry capability

**Dependencies**:
- `vulcanlab.data.database.get_session`
- `vulcanlab.data.models.Chunk`
- `vulcanlab.data.models.Work`
- `vulcanlab.ai.llm_factory.create_embeddings` (lazy-imported)

### CLI Interface

#### [vect_chunks_cli.py](vect_chunks_cli.py)
Command-line interface for vectorization operations.

**Usage**:
```bash
python -m vulcanlab.vectorization.vect_chunks_cli <work_id> [--limit N] [--batch-size B] [-v|--verbose]
```

**Arguments**:
- `work_id` (int, required) - Database work ID to vectorize
- `--limit` (int, optional) - Maximum chunks to process
- `--batch-size` (int, default=20) - Chunks per API batch call
- `-v, --verbose` (flag) - Enable detailed progress output

**Interactive Mode**:
When `--limit` not specified:
- Prompts: "Enter Y to process all, N to cancel, or a number to set limit:"
- Validates input (Y/N or positive integer)
- Safe cancellation on invalid input

**Output Format**:
```
Vectorization complete for work <id>:
  Total eligible: N
  Processed: N
  Success: N
  Failed: N
Errors:
  Chunk X: <error message>
  ... (first 10 shown)
```

**Exit Codes**:
- `0` - Success or no eligible chunks
- `1` - Errors encountered or invalid input

### Public API

#### [__init__.py](__init__.py)
Public API with lazy import mechanism to avoid loading heavy ML dependencies at module import time.

**Exported** (`__all__`):
- `vectorize_chunks`
- `get_eligible_chunks_count`
- `VectorizationResult`

**Lazy Import Pattern**:
Uses `__getattr__()` to dynamically import from `vect_chunks.py` only when functions are actually called. This prevents loading LangChain, OpenAI, and Google GenAI libraries until vectorization is performed.

## Embedding Models

The module supports multiple embedding providers via `vulcanlab.ai.llm_factory.create_embeddings()`:

### OpenAI (Default)
- **Model**: `text-embedding-3-small`
- **Dimensions**: 1536 (stored as 768 in pgvector)
- **Max Tokens**: 8191
- **Configuration**: Via `LLMSettings` from .env

### Google Gemini
- **Model**: `models/text-embedding-004`
- **Dimensions**: 768 (matches pgvector column)
- **Max Tokens**: 2048
- **Configuration**: Via `LLMSettings` from .env

## Database Integration

### Chunk Model
The `Chunk` model (`vulcanlab.data.models.chunk.py`) includes vectorization fields:

- `embedding: Optional[list]` - pgvector Vector(768) field
- `vector_status: str` - Vectorization state tracker
  - `'no_vec'` - Not marked for vectorization
  - `'to_vec'` - Ready for vectorization
  - `'vec'` - Successfully vectorized
  - `'vec_err'` - Vectorization failed
- `parent_id: Optional[int]` - Only non-top-level chunks (parent_id IS NOT NULL) are vectorized

### pgvector Configuration
- **Extension**: Enabled via `enable_pgvector_extension()` in `init_db.py`
- **Vector Type**: `Vector(768)` - 768-dimensional embedding storage
- **Indexes**: Created for efficient similarity search

## API Integration

The module is exposed via FastAPI router at `/home/dardawk/python/vulcanlab/src/vulcanlab_api/routers/vectorization.py`:

### Active Endpoints
- `GET /api/vec/eligible` - Get count of eligible chunks
  - Query params: `work_id` (optional)
  - Uses: `get_eligible_chunks_count()`

- `POST /api/vec/vectorize` - Vectorize chunks synchronously
  - Request body: `{"work_id": int, "limit": int | null, "batch_size": int, "verbose": bool}`
  - Uses: `vectorize_chunks()`
  - Returns: `VectorizationResult`

### Planned Endpoints (Stubs)
- `POST /api/vec/chunks` - Selective chunk vectorization
- `POST /api/vec/query` - Query text vectorization
- `GET /api/vec/models` - List available embedding models
- `GET /api/vec/status/{job_id}` - Async job status tracking

## Design Patterns

### 1. Lazy Imports
**Implementation**: `__getattr__()` in `__init__.py`

**Benefit**: Avoids loading heavy ML libraries (LangChain, OpenAI SDK, Google GenAI) until vectorization is actually performed. Improves startup time and memory usage for non-vectorization operations.

```python
# Heavy imports only loaded when vectorize_chunks() is called
def __getattr__(name):
    if name in ["vectorize_chunks", "get_eligible_chunks_count", "VectorizationResult"]:
        from .vect_chunks import vectorize_chunks, get_eligible_chunks_count, VectorizationResult
        return locals()[name]
```

### 2. Batch Processing
**Implementation**: Configurable `batch_size` parameter (default: 20)

**Benefit**:
- Reduces API calls by processing multiple chunks per request
- Manages rate limits and API costs
- Allows tuning for memory/performance tradeoffs

### 3. Transaction Safety
**Implementation**: Per-batch database commits

**Benefit**:
- Partial failures don't block retry of successful chunks
- Failed chunks can be reprocessed independently
- Maintains data consistency

### 4. Status Tracking
**Implementation**: `vector_status` field with states (no_vec, to_vec, vec, vec_err)

**Benefit**:
- Enables selective re-vectorization of failed chunks
- Tracks processing state across sessions
- Supports retry logic

### 5. Result Objects
**Implementation**: `VectorizationResult` dataclass with detailed error tracking

**Benefit**:
- Structured error reporting with chunk-level detail
- Clear success/failure metrics
- Enables automated retry strategies

### 6. Interactive CLI
**Implementation**: Safe user prompts with validation

**Benefit**:
- Prevents accidental large-scale operations
- User-friendly confirmation workflow
- Input validation and error handling

## Usage Examples

### Programmatic Usage
```python
from vulcanlab.vectorization import vectorize_chunks, get_eligible_chunks_count

# Check eligible chunks for specific work
count = get_eligible_chunks_count(work_id=1)
print(f"Eligible chunks: {count}")

# Check eligible chunks across all works
total_count = get_eligible_chunks_count()

# Vectorize with limit
result = vectorize_chunks(
    work_id=1,
    limit=50,
    batch_size=20,
    verbose=True
)

print(f"Processed: {result.processed}")
print(f"Success: {result.success}")
print(f"Failed: {result.failed}")

# Check for errors
if result.errors:
    for chunk_id, error_msg in result.errors[:10]:
        print(f"Chunk {chunk_id}: {error_msg}")

# Vectorize all eligible chunks for a work
result = vectorize_chunks(work_id=1, limit=None)

# Vectorize across all works
result = vectorize_chunks(work_id=None, limit=100)
```

### CLI Usage
```bash
# Interactive mode (prompts for limit)
python -m vulcanlab.vectorization.vect_chunks_cli 1

# Vectorize 100 chunks
python -m vulcanlab.vectorization.vect_chunks_cli 1 --limit 100

# Verbose output with progress
python -m vulcanlab.vectorization.vect_chunks_cli 1 --limit 50 --verbose

# Custom batch size for larger API limits
python -m vulcanlab.vectorization.vect_chunks_cli 1 --batch-size 50 -v

# Process all eligible chunks
python -m vulcanlab.vectorization.vect_chunks_cli 1 --limit 1000
```

### REST API Usage
```bash
# Get eligible chunk count for work 1
curl http://localhost:8000/api/vec/eligible?work_id=1

# Get total eligible chunks across all works
curl http://localhost:8000/api/vec/eligible

# Vectorize all chunks for work 1
curl -X POST http://localhost:8000/api/vec/vectorize \
  -H "Content-Type: application/json" \
  -d '{
    "work_id": 1,
    "limit": null,
    "batch_size": 20,
    "verbose": false
  }'

# Vectorize 50 chunks with verbose output
curl -X POST http://localhost:8000/api/vec/vectorize \
  -H "Content-Type: application/json" \
  -d '{
    "work_id": 1,
    "limit": 50,
    "batch_size": 20,
    "verbose": true
  }'
```

## Dependencies

### Internal Dependencies
- `vulcanlab.data.database` - Database session management
- `vulcanlab.data.models.Chunk` - ORM model for chunks
- `vulcanlab.data.models.Work` - ORM model for works
- `vulcanlab.ai.llm_factory` - Embedding model factory (lazy-imported)
- `vulcanlab.ai.config` - LLM settings and configuration

### External Dependencies
**Core**:
- `sqlalchemy` - ORM for database operations
- `pgvector.sqlalchemy` - Vector column type for PostgreSQL

**ML Libraries** (lazy-loaded):
- `langchain_openai` - OpenAI embeddings (if using OpenAI provider)
- `langchain_google_genai` - Google embeddings (if using Google provider)

## Error Handling

### Chunk-Level Errors
Individual chunk failures are tracked but don't stop batch processing:
- Error stored in `VectorizationResult.errors` as `(chunk_id, error_message)`
- Chunk marked with `vector_status='vec_err'`
- Other chunks in batch continue processing

### Batch-Level Errors
If entire batch fails:
- All chunks in batch marked as `'vec_err'`
- Error logged and added to result
- Processing continues with next batch

### Common Error Scenarios
1. **Invalid Work ID**: Raises `ValueError` before processing
2. **Empty Chunk Content**: Individual chunk error, processing continues
3. **API Rate Limits**: Batch-level error, retry recommended
4. **Database Connection**: Raised immediately, stops processing
5. **Invalid Embedding Dimensions**: Validation error during insert

## Performance Considerations

### Batch Size Tuning
- **Small batches (10-20)**: Lower memory, more API calls, slower but safer
- **Large batches (50-100)**: Higher memory, fewer API calls, faster but higher failure impact
- **Default (20)**: Balanced for most use cases

### Eligible Chunk Filtering
Only chunks meeting ALL criteria are processed:
- `vector_status = 'to_vec'` - Explicitly marked for vectorization
- `parent_id IS NOT NULL` - Non-top-level chunks only
- `embedding IS NULL` - Not already vectorized

### Transaction Management
- Commits per batch (not per chunk) for performance
- Failed chunks can be retried by re-running with same parameters
- Status tracking prevents duplicate vectorization

## Configuration

### Environment Variables
Configure via `.env` file (loaded by `LLMSettings`):

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai

# Google Configuration
GOOGLE_API_KEY=...
LLM_PROVIDER=gemini

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Database Setup
Ensure pgvector extension is enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run database initialization:
```bash
python -m vulcanlab.data.init_db
```

## Testing Considerations

Recommended test coverage:
1. **Status Transitions**: Test `to_vec → vec` and `to_vec → vec_err` transitions
2. **Batch Processing**: Verify correct batch boundaries and commits
3. **Error Handling**: Test individual chunk failures don't stop processing
4. **Eligibility Filtering**: Verify only eligible chunks are selected
5. **Database Transactions**: Test rollback on batch failure
6. **Embedding Dimensions**: Verify 768-dimension compatibility with pgvector
7. **Work Validation**: Test invalid work_id handling
8. **Empty Results**: Test behavior with no eligible chunks

## Notes

- **Parent Chunks**: Top-level chunks (parent_id IS NULL) are NOT vectorized
- **Vector Dimensions**: Stored as 768-dim vectors regardless of source model dimensions
- **Retry Strategy**: Simply re-run vectorization; status tracking prevents duplicates
- **Async Processing**: Current implementation is synchronous; async job endpoints planned
- **Model Selection**: Controlled by `LLMSettings` provider configuration, not per-call
- **Memory Usage**: Batch size directly impacts memory consumption during processing
