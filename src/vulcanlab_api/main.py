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
    chunking,
    conversion,
    conversion_settings,
    corpus,
    init,
    rag,
    rag_config,
    sanitization,
    settings,
    templates,
    vectorization,
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
app.include_router(corpus.router, prefix="/corpus", tags=["Corpus"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(rag_config.router, prefix="/api/rag-config", tags=["RAG Config"])


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

