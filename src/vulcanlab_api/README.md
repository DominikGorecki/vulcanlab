# VulcanLab API

FastAPI REST interface for the VulcanLab Retrieval-Augmented Generation system.

## Project Structure

```
src/vulcanlab_api/
├── __init__.py           # Package init with usage docs
├── __main__.py           # Run as module: python -m vulcanlab_api
├── main.py               # Main FastAPI application
├── config.py             # Settings with pydantic-settings
├── dependencies.py       # Shared dependencies (pagination, etc.)
├── routers/              # Route handlers (1 file per group)
│   ├── __init__.py
│   ├── init.py           # /init/...
│   ├── settings.py       # /settings/...
│   ├── conversion.py     # /conv/...
│   ├── sanitization.py   # /sanitization/...
│   ├── chunking.py       # /chunk/...
│   ├── vectorization.py  # /vec/...
│   └── rag.py            # /rag/...
└── schemas/              # Pydantic models (1 file per router)
    ├── __init__.py
    ├── common.py         # Shared schemas
    ├── init.py
    ├── settings.py
    ├── conversion.py
    ├── sanitization.py
    ├── chunking.py
    ├── vectorization.py
    └── rag.py
```

## Features

- **Interactive Documentation**: Swagger UI (`/docs`), ReDoc (`/redoc`), OpenAPI JSON (`/openapi.json`)
- **Model Schemas & Examples**: Full Pydantic v2 schemas with examples for try-it-out
- **Validation**: Built-in request validation via Pydantic
- **CORS**: Configured and ready
- **OpenAPI Tags**: All 7 route groups properly tagged and documented
- **Lifespan Events**: Startup/shutdown hooks ready for initialization

## API Endpoints

### Init (`/init`)
Initialization and setup operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/init/status` | Get system initialization status |
| POST | `/init/database` | Initialize/reset database |
| GET | `/init/health` | Detailed health check |

### Settings (`/settings`)
Configuration and settings management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings/` | Get all current settings |
| GET | `/settings/{key}` | Get a specific setting |
| PUT | `/settings/{key}` | Update a specific setting |

### Conversion (`/conv`)
Document conversion operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/conv/formats` | List supported formats |
| POST | `/conv/epub` | Convert EPUB to markdown |
| POST | `/conv/pdf` | Convert PDF to markdown |
| GET | `/conv/status/{job_id}` | Get conversion job status |

### Sanitization (`/sanitization`)
Content sanitization operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sanitization/extract-toc` | Extract table of contents |
| POST | `/sanitization/extract-titles` | Extract titles from markdown |
| POST | `/sanitization/suggest-changes` | Get suggested heading changes |
| POST | `/sanitization/apply-changes` | Apply heading changes |

### Chunking (`/chunk`)
Document chunking operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chunk/headings` | Chunk by heading structure |
| POST | `/chunk/content` | Chunk by content/size |
| POST | `/chunk/suggest` | Get suggested chunk boundaries |
| POST | `/chunk/extract-bib` | Extract bibliography entries |
| POST | `/chunk/process-llm` | Process chunks with LLM |

### Vectorization (`/vec`)
Embedding generation operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vec/models` | List available embedding models |
| POST | `/vec/chunks` | Vectorize document chunks |
| POST | `/vec/query` | Vectorize a query string |
| GET | `/vec/status/{job_id}` | Get vectorization job status |

### RAG (`/rag`)
Retrieval, Augmentation and Generation operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/query` | Execute a RAG query |
| POST | `/rag/retrieve` | Retrieve relevant chunks only |
| POST | `/rag/expand-query` | Expand a query with variations |
| POST | `/rag/augment` | Augment content with context |
| POST | `/rag/generate` | Generate response from context |

## How to Run

### Development Server (with auto-reload)

```bash
# Using uvicorn directly
venv\Scripts\uvicorn vulcanlab_api.main:app --reload

# Or as a Python module
venv\Scripts\python -m vulcanlab_api --reload

# With custom host/port
venv\Scripts\python -m vulcanlab_api --host 0.0.0.0 --port 8080
```

### Production Server

```bash
venv\Scripts\uvicorn vulcanlab_api.main:app --host 0.0.0.0 --port 8000
```

## Interactive Documentation

Once the server is running, access the interactive docs at:

- **Swagger UI (Try it out!)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Running Tests

```bash
# Run all API tests
venv\Scripts\pytest tests/unit/test_api_endpoints.py -v

# Run with coverage
venv\Scripts\pytest tests/unit/test_api_endpoints.py -v --cov=vulcanlab_api
```

## Configuration

The API uses environment variables with the `VULCANLAB_API_` prefix. Configuration is managed via `pydantic-settings`.

Available settings:
- `VULCANLAB_API_DEBUG` - Enable debug mode (default: `false`)
- `VULCANLAB_API_CORS_ORIGINS` - Allowed CORS origins (default: `["*"]`)

## Library Usage

```python
from fastapi.testclient import TestClient
from vulcanlab_api.main import app

# Create a test client
client = TestClient(app)

# Make requests
response = client.get("/health")
print(response.json())

# Query the RAG endpoint
response = client.post("/rag/query", json={
    "query": "What is cognitive load theory?",
    "top_k": 5
})
print(response.json())
```

## Dependencies

Added to `pyproject.toml`:
- `fastapi[standard]` - FastAPI framework with standard extras
- `uvicorn[standard]` - ASGI server

## Implementation Status

All endpoints are currently **stubbed** with mock responses. Each endpoint includes:
- Proper request/response Pydantic models
- OpenAPI documentation with examples
- Validation rules
- TODO comments indicating which `vulcanlab` modules to integrate

To implement actual functionality, update the router functions to call the corresponding modules from `vulcanlab.*`.

