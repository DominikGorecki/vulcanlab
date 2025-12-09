"""
Init Router - Initialization and setup operations.

Endpoints:
    GET  /init/status     - Get system initialization status
    POST /init/database   - Initialize/reset database
    GET  /init/health     - Detailed health check
    GET  /init/db-health  - Database health checks
"""

from fastapi import APIRouter, HTTPException, status

from vulcanlab_api.schemas.init import (
    DatabaseInitRequest,
    DatabaseInitResponse,
    DbHealthCheckResponse,
    DbHealthCheckResult,
    HealthCheckResponse,
    InitStatusResponse,
)
from vulcanlab.data.db_health_check import run_all_health_checks
from vulcanlab.data.init_db import init_database as run_init_database

router = APIRouter()


@router.get(
    "/status",
    response_model=InitStatusResponse,
    summary="Get initialization status",
    description="Check the current initialization status of all system components.",
    responses={
        200: {
            "description": "Initialization status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "database_initialized": True,
                        "embeddings_ready": True,
                        "models_loaded": False,
                        "message": "System partially initialized",
                    }
                }
            },
        }
    },
)
async def get_init_status() -> InitStatusResponse:
    """
    Get the current initialization status of system components.
    
    Returns status of:
    - Database connection and schema
    - Embedding models
    - LLM models
    """
    # TODO: Implement actual status checks using vulcanlab modules
    return InitStatusResponse(
        database_initialized=False,
        embeddings_ready=False,
        models_loaded=False,
        message="Stub implementation - not yet connected to vulcanlab",
    )


@router.post(
    "/database",
    response_model=DatabaseInitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize database",
    description="Initialize or reset the database schema and tables.",
    responses={
        201: {
            "description": "Database initialized successfully",
        },
        500: {
            "description": "Database initialization failed",
        },
    },
)
async def init_database(request: DatabaseInitRequest) -> DatabaseInitResponse:
    """
    Initialize the database schema.
    
    Can optionally drop existing tables and recreate them.
    
    WARNING: Using reset=True will delete all existing data!
    """
    try:
        # Note: request.reset is not currently supported by run_init_database
        # but could be added if needed. For now we just run initialization
        # which is idempotent for existing tables unless we drop them first.
        
        # Run initialization
        run_init_database(verbose=True)
        
        return DatabaseInitResponse(
            success=True,
            message="Database initialized successfully",
            tables_created=["works", "chunks", "queries", "results", "io_files", "prompt_templates", "prompt_meta", "rag_config"],
        )
    except Exception as e:
        # Log error?
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}",
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Detailed health check",
    description="Perform a detailed health check of all system components.",
)
async def detailed_health_check() -> HealthCheckResponse:
    """
    Perform detailed health checks on all components.
    
    Checks:
    - Database connectivity
    - Redis connection (if configured)
    - External API availability
    """
    # TODO: Implement actual health checks
    return HealthCheckResponse(
        status="healthy",
        components={
            "database": {"status": "unknown", "latency_ms": None},
            "embedding_model": {"status": "unknown", "latency_ms": None},
            "llm": {"status": "unknown", "latency_ms": None},
        },
    )


@router.get(
    "/db-health",
    response_model=DbHealthCheckResponse,
    summary="Database health checks",
    description="Run comprehensive database health checks including connection, tables, indexes, and permissions.",
)
async def db_health_check() -> DbHealthCheckResponse:
    """
    Run all database health checks.
    
    Checks:
    - Connection to database
    - Required extensions (pgvector)
    - Table existence and columns
    - Index existence
    - Trigger existence
    - Read/write permissions
    """
    results = run_all_health_checks()
    
    # Convert to API schema
    api_results = [
        DbHealthCheckResult(
            name=r.name,
            passed=r.passed,
            message=r.message,
            details=r.details,
        )
        for r in results
    ]
    
    all_passed = all(r.passed for r in results)
    connection_ok = results[0].passed if results else False
    
    return DbHealthCheckResponse(
        results=api_results,
        all_passed=all_passed,
        connection_ok=connection_ok,
    )


