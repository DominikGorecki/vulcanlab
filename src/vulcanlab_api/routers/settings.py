"""
Settings Router - Configuration and settings management.

Endpoints:
    GET  /settings/              - Get full application configuration
    GET  /settings/database      - Get database configuration
    PUT  /settings/database      - Update database configuration
    GET  /settings/llm           - Get LLM configuration
    PUT  /settings/llm           - Update LLM configuration
    GET  /settings/paths         - Get paths configuration
    PUT  /settings/paths         - Update paths configuration
"""

from fastapi import APIRouter, HTTPException, status

from vulcanlab.config.app_config import load_config, save_config, AppConfig
from vulcanlab_api.schemas.settings import (
    AppConfigSchema,
    DatabaseConfigSchema,
    DatabaseConfigUpdateRequest,
    LLMConfigSchema,
    LLMConfigUpdateRequest,
    ModelConfigSchema,
    LLMModelsConfigSchema,
    PathsConfigSchema,
    PathsConfigUpdateRequest,
)

router = APIRouter()


def _config_to_schema(config: AppConfig) -> AppConfigSchema:
    """Convert AppConfig to API schema."""
    return AppConfigSchema(
        database=DatabaseConfigSchema(
            admin_user=config.database.admin_user,
            host=config.database.host,
            port=config.database.port,
            db_name=config.database.db_name,
            app_user=config.database.app_user,
        ),
        llm=LLMConfigSchema(
            provider=config.llm.provider,
            models=LLMModelsConfigSchema(
                openai=ModelConfigSchema(
                    light=config.llm.models.openai.light,
                    full=config.llm.models.openai.full,
                ),
                gemini=ModelConfigSchema(
                    light=config.llm.models.gemini.light,
                    full=config.llm.models.gemini.full,
                ),
            ),
        ),
        paths=PathsConfigSchema(
            input_dir=config.paths.input_dir,
            output_dir=config.paths.output_dir,
        ),
    )


@router.get(
    "/",
    response_model=AppConfigSchema,
    summary="Get all settings",
    description="Retrieve the full application configuration.",
)
async def get_all_settings() -> AppConfigSchema:
    """Get full application configuration."""
    try:
        config = load_config()
        return _config_to_schema(config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {e}",
        )


@router.get(
    "/database",
    response_model=DatabaseConfigSchema,
    summary="Get database settings",
    description="Retrieve database configuration.",
)
async def get_database_settings() -> DatabaseConfigSchema:
    """Get database configuration."""
    try:
        config = load_config()
        return DatabaseConfigSchema(
            admin_user=config.database.admin_user,
            host=config.database.host,
            port=config.database.port,
            db_name=config.database.db_name,
            app_user=config.database.app_user,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {e}",
        )


@router.put(
    "/database",
    response_model=DatabaseConfigSchema,
    summary="Update database settings",
    description="Update database configuration. Only provided fields will be updated.",
)
async def update_database_settings(
    request: DatabaseConfigUpdateRequest,
) -> DatabaseConfigSchema:
    """Update database configuration."""
    try:
        config = load_config(force_reload=True)

        # Update only provided fields
        if request.admin_user is not None:
            config.database.admin_user = request.admin_user
        if request.host is not None:
            config.database.host = request.host
        if request.port is not None:
            config.database.port = request.port
        if request.db_name is not None:
            config.database.db_name = request.db_name
        if request.app_user is not None:
            config.database.app_user = request.app_user

        save_config(config)

        return DatabaseConfigSchema(
            admin_user=config.database.admin_user,
            host=config.database.host,
            port=config.database.port,
            db_name=config.database.db_name,
            app_user=config.database.app_user,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {e}",
        )


@router.get(
    "/llm",
    response_model=LLMConfigSchema,
    summary="Get LLM settings",
    description="Retrieve LLM configuration including active provider and all model settings.",
)
async def get_llm_settings() -> LLMConfigSchema:
    """Get LLM configuration."""
    try:
        config = load_config()
        return LLMConfigSchema(
            provider=config.llm.provider,
            models=LLMModelsConfigSchema(
                openai=ModelConfigSchema(
                    light=config.llm.models.openai.light,
                    full=config.llm.models.openai.full,
                ),
                gemini=ModelConfigSchema(
                    light=config.llm.models.gemini.light,
                    full=config.llm.models.gemini.full,
                ),
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {e}",
        )


@router.put(
    "/llm",
    response_model=LLMConfigSchema,
    summary="Update LLM settings",
    description="Update LLM configuration. Only provided fields will be updated.",
)
async def update_llm_settings(request: LLMConfigUpdateRequest) -> LLMConfigSchema:
    """Update LLM configuration."""
    try:
        config = load_config(force_reload=True)

        # Update provider if provided
        if request.provider is not None:
            config.llm.provider = request.provider

        # Update OpenAI models if provided
        if request.openai_light is not None:
            config.llm.models.openai.light = request.openai_light
        if request.openai_full is not None:
            config.llm.models.openai.full = request.openai_full

        # Update Gemini models if provided
        if request.gemini_light is not None:
            config.llm.models.gemini.light = request.gemini_light
        if request.gemini_full is not None:
            config.llm.models.gemini.full = request.gemini_full

        save_config(config)

        return LLMConfigSchema(
            provider=config.llm.provider,
            models=LLMModelsConfigSchema(
                openai=ModelConfigSchema(
                    light=config.llm.models.openai.light,
                    full=config.llm.models.openai.full,
                ),
                gemini=ModelConfigSchema(
                    light=config.llm.models.gemini.light,
                    full=config.llm.models.gemini.full,
                ),
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {e}",
        )


@router.get(
    "/paths",
    response_model=PathsConfigSchema,
    summary="Get paths settings",
    description="Retrieve file system paths configuration.",
)
async def get_paths_settings() -> PathsConfigSchema:
    """Get paths configuration."""
    try:
        config = load_config()
        return PathsConfigSchema(
            input_dir=config.paths.input_dir,
            output_dir=config.paths.output_dir,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {e}",
        )


@router.put(
    "/paths",
    response_model=PathsConfigSchema,
    summary="Update paths settings",
    description="Update file system paths configuration. Only provided fields will be updated.",
)
async def update_paths_settings(
    request: PathsConfigUpdateRequest,
) -> PathsConfigSchema:
    """Update paths configuration."""
    try:
        from pathlib import Path
        
        config = load_config(force_reload=True)

        # Update only provided fields with validation
        if request.input_dir is not None:
            input_path = Path(request.input_dir)
            if not input_path.is_absolute():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"input_dir must be an absolute path, got: {request.input_dir}",
                )
            config.paths.input_dir = request.input_dir
            
        if request.output_dir is not None:
            output_path = Path(request.output_dir)
            if not output_path.is_absolute():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"output_dir must be an absolute path, got: {request.output_dir}",
                )
            config.paths.output_dir = request.output_dir

        save_config(config)

        return PathsConfigSchema(
            input_dir=config.paths.input_dir,
            output_dir=config.paths.output_dir,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {e}",
        )
