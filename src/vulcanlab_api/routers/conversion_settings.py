"""
API endpoints for simple conversion configuration.

Provides REST endpoints to read and update conversion settings including
the token threshold for document classification.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from vulcanlab.config.conversion_config import (
    get_token_threshold,
    set_token_threshold,
    get_advanced_mode_enabled,
    set_advanced_mode_enabled,
    get_use_full_model,
    set_use_full_model
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversion", tags=["conversion_settings"])


class ConversionSettings(BaseModel):
    """Conversion settings response/request model."""
    token_threshold: int = Field(
        ...,
        gt=0,
        description="Token threshold for small vs large document classification"
    )
    advanced_mode_enabled: bool = Field(
        default=False,
        description="Enable advanced conversion mode with additional processing"
    )
    use_full_model: bool = Field(
        default=False,
        description="Use full LLM model tier instead of light for simple conversion"
    )


@router.get("/settings", response_model=ConversionSettings)
async def get_conversion_settings():
    """
    Get current conversion settings.

    Returns:
        Current token threshold, advanced mode, and use_full_model settings
    """
    try:
        threshold = get_token_threshold()
        advanced_mode = get_advanced_mode_enabled()
        use_full = get_use_full_model()
        return ConversionSettings(
            token_threshold=threshold,
            advanced_mode_enabled=advanced_mode,
            use_full_model=use_full
        )
    except Exception as e:
        logger.error(f"Failed to get conversion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to load settings")


@router.put("/settings", response_model=ConversionSettings)
async def update_conversion_settings(settings: ConversionSettings):
    """
    Update conversion settings.

    Args:
        settings: New settings values

    Returns:
        Updated settings
    """
    try:
        set_token_threshold(settings.token_threshold)
        set_advanced_mode_enabled(settings.advanced_mode_enabled)
        set_use_full_model(settings.use_full_model)
        return settings
    except ValueError as e:
        logger.warning(f"Invalid settings update: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update conversion settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save settings")
