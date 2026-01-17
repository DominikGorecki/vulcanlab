"""
VulcanLab API - Main FastAPI Application.

Usage:
    # Development server with auto-reload
    venv\\Scripts\\uvicorn vulcanlab_api.main:app --reload

    # Production server
    venv\\Scripts\\uvicorn vulcanlab_api.main:app --host 0.0.0.0 --port 8000

Interactive Documentation:
    Swagger UI: http://localhost:8000/docs
    ReDoc:      http://localhost:8000/redoc
    OpenAPI:    http://localhost:8000/openapi.json
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from vulcanlab_api.config import get_settings
from vulcanlab_api.dependencies import get_db_session
from vulcanlab_api.routers import (
    chunks,
    chunking,
    conversion,
    conversion_settings,
    corpus,
    eval,
    init,
    markdown,
    rag,
    rag_config,
    result_models,
    sanitization,
    search,
    settings,
    simple_conversion,
    templates,
    v1_corpus,
    vectorization,
    collections,
    research_sessions,
    summarize,
)

settings_config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup/shutdown."""
    # Startup
    print("VulcanLab API starting up...")
    yield
    # Shutdown
    print("VulcanLab API shutting down...")


# Create FastAPI application with comprehensive OpenAPI configuration
app = FastAPI(
    title=settings_config.api_title,
    description=settings_config.api_description,
    version=settings_config.api_version,
    lifespan=lifespan,
    # OpenAPI configuration
    openapi_url="/openapi.json",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    # OpenAPI tags for organization
    openapi_tags=[
        {
            "name": "Init",
            "description": "Initialization and setup operations. Database setup, system health checks.",
        },
        {
            "name": "Settings",
            "description": "Configuration and settings management. View and modify system settings.",
        },
        {
            "name": "Conversion",
            "description": "Document conversion operations. Convert EPUBs, PDFs to markdown format.",
        },
        {
            "name": "Sanitization",
            "description": "Content sanitization operations. Clean, normalize, and validate content.",
        },
        {
            "name": "Chunking",
            "description": "Document chunking operations. Split documents into semantic chunks.",
        },
        {
            "name": "Vectorization",
            "description": "Vectorization operations. Generate embeddings for document chunks.",
        },
        {
            "name": "Corpus",
            "description": "Corpus management. Read-only access to works with completed chunking.",
        },
        {
            "name": "RAG",
            "description": "Retrieval, Augmentation and Generation. Query documents and generate responses.",
        },
        {
            "name": "RAG Config",
            "description": "RAG configuration preset management. Create, edit, and manage retrieval/consolidation/augmentation settings.",
        },
        {
            "name": "Markdown",
            "description": "Markdown import/export operations. Export works to markdown files, import markdown files as works.",
        },
        {
            "name": "Chunks",
            "description": "Chunk management operations. Search, preview, and delete chunks with descendants.",
        },
        {
            "name": "Search",
            "description": "Document search operations. Lexical, dense, and hybrid search across chunks.",
        },
        {
            "name": "Eval",
            "description": "Evaluation experiments. Compare and evaluate LLM responses using blind testing and statistical analysis.",
        },
        {
            "name": "Collections",
            "description": "Research organization and item grouping. Create and manage collections of excerpts, results, and queries.",
        },
        {
            "name": "Research Sessions",
            "description": "Core CRUD endpoints for research workflows, sessions, sections, and reports.",
        },
        {
            "name": "Summarization",
            "description": "Document summarization operations. Prepare and generate prompts for summarizing long documents.",
        },
    ],
    # Additional metadata
    contact={
        "name": "VulcanLab Team",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_config.cors_origins,
    allow_credentials=settings_config.cors_allow_credentials,
    allow_methods=settings_config.cors_allow_methods,
    allow_headers=settings_config.cors_allow_headers,
)

# Include routers with prefixes
app.include_router(init.router, prefix="/init", tags=["Init"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(templates.router)  # Templates router has its own prefix
app.include_router(conversion.router, prefix="/conv", tags=["Conversion"])
app.include_router(conversion_settings.router)  # Conversion settings router has its own prefix
app.include_router(sanitization.router, prefix="/sanitization", tags=["Sanitization"])
app.include_router(chunking.router, prefix="/chunk", tags=["Chunking"])
app.include_router(vectorization.router, prefix="/vec", tags=["Vectorization"])
app.include_router(corpus.router, prefix="/corpus", tags=["Corpus"])  # Legacy endpoints for backwards compatibility
app.include_router(v1_corpus.router, prefix="/api/v1/corpus", tags=["Corpus V1"])  # New versioned endpoints
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(rag_config.router, prefix="/api/rag-config", tags=["RAG Config"])
app.include_router(result_models.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(simple_conversion.router)  # Simple conversion router has its own prefix
app.include_router(markdown.router, prefix="/api/v1/markdown", tags=["Markdown"])
app.include_router(chunks.router, prefix="/api/v1/chunks", tags=["Chunks"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(eval.router, prefix="/api/v1/eval", tags=["Eval"])
app.include_router(collections.router, prefix="/api/v1/collections", tags=["Collections"])
app.include_router(research_sessions.router, prefix="/api/v1", tags=["Research Sessions"])
app.include_router(summarize.router, prefix="/api/v1/summarize", tags=["Summarization"])


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect info to docs."""
    return {
        "message": "Welcome to VulcanLab API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Init"])
async def health_check(db: Session = Depends(get_db_session)):
    """
    Health check endpoint for monitoring and validation.

    Verifies database connectivity and returns service status.

    Returns:
        dict: Health status including database connectivity

    Raises:
        HTTPException: 503 if database is unreachable
    """
    try:
        # Test database connection if db session is available
        if db is not None:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        else:
            db_status = "not_configured"

        return {
            "status": "healthy",
            "service": "vulcanlab-api",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "vulcanlab-api",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

