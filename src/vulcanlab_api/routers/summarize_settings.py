from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from vulcanlab_api.dependencies import get_db_session
from vulcanlab.data.models.summarize_settings import SummarizeSettings
from vulcanlab_api.schemas.summarize import (
    SummarizeSettingsResponse,
    SummarizeSettingsUpdateRequest
)

router = APIRouter()

@router.get(
    "/",
    response_model=SummarizeSettingsResponse,
    summary="Get summarization settings",
    description="Retrieve the current configuration for salience-based summarization."
)
async def get_summarize_settings(db: Session = Depends(get_db_session)):
    """Retrieve summarization settings from the database."""
    stmt = select(SummarizeSettings).order_by(SummarizeSettings.id.desc()).limit(1)
    settings = db.execute(stmt).scalar_one_or_none()
    
    if not settings:
        # Return default values if no row exists
        return SummarizeSettings()
    
    return settings

@router.put(
    "/",
    response_model=SummarizeSettingsResponse,
    summary="Update summarization settings",
    description="Update the configuration for salience-based summarization. Supports partial updates."
)
async def update_summarize_settings(
    request: SummarizeSettingsUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """Update or create summarization settings."""
    # Validation
    if request.h2_top_percent is not None and not (0 <= request.h2_top_percent <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="h2_top_percent must be between 0 and 100"
        )
    
    # Range validation for thresholds and weights
    for field, value in request.model_dump(exclude_unset=True).items():
        if field.endswith("_threshold") or field.endswith("_weight"):
            if not (0.0 <= value <= 1.0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field} must be between 0.0 and 1.0"
                )

    # Get existing or create new
    stmt = select(SummarizeSettings).order_by(SummarizeSettings.id.desc()).limit(1)
    settings = db.execute(stmt).scalar_one_or_none()
    
    if not settings:
        settings = SummarizeSettings()
        db.add(settings)
    
    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
        
    db.commit()
    db.refresh(settings)
    
    return settings
