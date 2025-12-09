"""
Pydantic schemas for Init router.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Database Health Check Schemas
# ============================================================================

class DbHealthCheckResult(BaseModel):
    """Result of a single health check."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Connection",
                "passed": True,
                "message": "App user can connect to database",
                "details": None,
            }
        }
    )

    name: str = Field(
        ...,
        description="Name of the health check",
    )
    passed: bool = Field(
        ...,
        description="Whether the check passed",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    details: str | None = Field(
        default=None,
        description="Additional details (usually for failures)",
    )


class DbHealthCheckResponse(BaseModel):
    """Response containing all database health check results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {"name": "Connection", "passed": True, "message": "App user can connect to database", "details": None},
                    {"name": "Extension: vector", "passed": True, "message": "Extension 'vector' is installed", "details": None},
                ],
                "all_passed": True,
                "connection_ok": True,
            }
        }
    )

    results: list[DbHealthCheckResult] = Field(
        ...,
        description="List of all health check results",
    )
    all_passed: bool = Field(
        ...,
        description="Whether all checks passed",
    )
    connection_ok: bool = Field(
        ...,
        description="Whether the connection check passed (first check)",
    )


# ============================================================================
# Init Status Schemas
# ============================================================================

class InitStatusResponse(BaseModel):
    """Response for system initialization status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_initialized": True,
                "embeddings_ready": True,
                "models_loaded": False,
                "message": "System partially initialized - LLM not configured",
            }
        }
    )

    database_initialized: bool = Field(
        ...,
        description="Whether the database is initialized",
    )
    embeddings_ready: bool = Field(
        ...,
        description="Whether embedding models are loaded",
    )
    models_loaded: bool = Field(
        ...,
        description="Whether LLM models are configured",
    )
    message: str | None = Field(
        default=None,
        description="Additional status information",
    )


class DatabaseInitRequest(BaseModel):
    """Request to initialize the database."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reset": False,
                "create_indexes": True,
            }
        }
    )

    reset: bool = Field(
        default=False,
        description="If True, drop and recreate all tables (WARNING: deletes data!)",
    )
    create_indexes: bool = Field(
        default=True,
        description="Whether to create database indexes",
    )


class DatabaseInitResponse(BaseModel):
    """Response for database initialization."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Database initialized successfully",
                "tables_created": ["works", "chunks", "embeddings"],
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether initialization was successful",
    )
    message: str = Field(
        ...,
        description="Status message",
    )
    tables_created: list[str] = Field(
        default_factory=list,
        description="List of tables that were created/verified",
    )


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "latency_ms": 12.5,
            }
        }
    )

    status: str = Field(
        ...,
        description="Component status: healthy, degraded, unhealthy, unknown",
    )
    latency_ms: float | None = Field(
        default=None,
        description="Response latency in milliseconds",
    )
    error: str | None = Field(
        default=None,
        description="Error message if unhealthy",
    )


class HealthCheckResponse(BaseModel):
    """Detailed health check response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "components": {
                    "database": {"status": "healthy", "latency_ms": 5.2},
                    "embedding_model": {"status": "healthy", "latency_ms": 120.0},
                    "llm": {"status": "healthy", "latency_ms": 450.0},
                },
            }
        }
    )

    status: str = Field(
        ...,
        description="Overall system status",
    )
    components: dict[str, Any] = Field(
        default_factory=dict,
        description="Health status of individual components",
    )


