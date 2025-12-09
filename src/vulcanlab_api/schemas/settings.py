"""
Pydantic schemas for Settings router.

These schemas mirror the structure in vulcanlab.config.app_config
for API serialization.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Database Configuration Schemas
# ============================================================================

class DatabaseConfigSchema(BaseModel):
    """Database configuration settings."""

    admin_user: str = Field(description="PostgreSQL admin username")
    host: str = Field(description="Database host")
    port: int = Field(description="Database port")
    db_name: str = Field(description="Application database name")
    app_user: str = Field(description="Application user name")


class DatabaseConfigUpdateRequest(BaseModel):
    """Request to update database configuration."""

    admin_user: str | None = Field(default=None, description="PostgreSQL admin username")
    host: str | None = Field(default=None, description="Database host")
    port: int | None = Field(default=None, description="Database port")
    db_name: str | None = Field(default=None, description="Application database name")
    app_user: str | None = Field(default=None, description="Application user name")


# ============================================================================
# LLM Configuration Schemas
# ============================================================================

class ModelConfigSchema(BaseModel):
    """Model configuration for a specific provider."""

    light: str = Field(description="Light/fast model name")
    full: str = Field(description="Full/complex model name")


class LLMModelsConfigSchema(BaseModel):
    """LLM models configuration for all providers."""

    openai: ModelConfigSchema
    gemini: ModelConfigSchema


class LLMConfigSchema(BaseModel):
    """LLM configuration settings."""

    provider: Literal["openai", "gemini"] = Field(description="Active LLM provider")
    models: LLMModelsConfigSchema


class LLMConfigUpdateRequest(BaseModel):
    """Request to update LLM configuration."""

    provider: Literal["openai", "gemini"] | None = Field(
        default=None, description="Active LLM provider"
    )
    openai_light: str | None = Field(default=None, description="OpenAI light model")
    openai_full: str | None = Field(default=None, description="OpenAI full model")
    gemini_light: str | None = Field(default=None, description="Gemini light model")
    gemini_full: str | None = Field(default=None, description="Gemini full model")


# ============================================================================
# Paths Configuration Schemas
# ============================================================================

class PathsConfigSchema(BaseModel):
    """File system paths configuration settings."""

    input_dir: str = Field(description="Absolute path to input directory")
    output_dir: str = Field(description="Absolute path to output directory")


class PathsConfigUpdateRequest(BaseModel):
    """Request to update paths configuration."""

    input_dir: str | None = Field(default=None, description="Absolute path to input directory")
    output_dir: str | None = Field(default=None, description="Absolute path to output directory")


# ============================================================================
# Full Configuration Schemas
# ============================================================================

class AppConfigSchema(BaseModel):
    """Root application configuration response."""

    database: DatabaseConfigSchema
    llm: LLMConfigSchema
    paths: PathsConfigSchema


# ============================================================================
# Legacy Schemas (kept for backwards compatibility)
# ============================================================================

class SettingResponse(BaseModel):
    """Response for a single setting."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "embedding_model",
                "value": "text-embedding-3-small",
                "description": "The embedding model used for vectorization",
            }
        }
    )

    key: str = Field(
        ...,
        description="Setting key/name",
    )
    value: Any = Field(
        ...,
        description="Current setting value",
    )
    description: str | None = Field(
        default=None,
        description="Description of what this setting controls",
    )


class AllSettingsResponse(BaseModel):
    """Response containing all settings."""

    settings: dict[str, Any] = Field(
        ...,
        description="Dictionary of all settings",
    )


class SettingUpdateRequest(BaseModel):
    """Request to update a setting."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": 1024,
            }
        }
    )

    value: Any = Field(
        ...,
        description="New value for the setting",
    )
