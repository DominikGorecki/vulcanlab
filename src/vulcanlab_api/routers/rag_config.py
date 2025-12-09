"""
RAG Config Router - Configuration preset management.

Endpoints for managing RAG pipeline configuration presets.

Endpoints:
    GET    /api/rag-config/                    - List all presets
    GET    /api/rag-config/default             - Get default preset
    GET    /api/rag-config/{preset_name}       - Get specific preset
    POST   /api/rag-config/                    - Create new preset
    PUT    /api/rag-config/{preset_name}       - Update preset
    PUT    /api/rag-config/{preset_name}/set-default - Set as default
    DELETE /api/rag-config/{preset_name}       - Delete preset
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.database import get_session
from vulcanlab.data.models.rag_config import RagConfig
from vulcanlab_api.schemas.rag_config import (
    RagConfigCreate,
    RagConfigUpdate,
    RagConfigResponse,
)

router = APIRouter()


# ============================================================================
# GET Endpoints
# ============================================================================

@router.get(
    "/",
    response_model=List[RagConfigResponse],
    summary="List all RAG config presets",
    description="Get a list of all available RAG configuration presets.",
)
async def list_presets() -> List[RagConfigResponse]:
    """List all RAG config presets."""
    try:
        with get_session() as session:
            presets = session.query(RagConfig).order_by(
                RagConfig.is_default.desc(),  # Default first
                RagConfig.preset_name
            ).all()
            return [RagConfigResponse.model_validate(preset) for preset in presets]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list presets: {str(e)}"
        )


@router.get(
    "/default",
    response_model=RagConfigResponse,
    summary="Get default preset",
    description="Get the RAG configuration preset marked as default.",
)
async def get_default_preset() -> RagConfigResponse:
    """Get default RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(RagConfig.is_default == True).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No default preset found. Database may not be initialized."
                )
            return RagConfigResponse.model_validate(preset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default preset: {str(e)}"
        )


@router.get(
    "/{preset_name}",
    response_model=RagConfigResponse,
    summary="Get preset by name",
    description="Get a specific RAG configuration preset by name.",
)
async def get_preset_by_name(preset_name: str) -> RagConfigResponse:
    """Get RAG config preset by name."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )
            return RagConfigResponse.model_validate(preset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preset: {str(e)}"
        )


# ============================================================================
# POST Endpoint
# ============================================================================

@router.post(
    "/",
    response_model=RagConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new preset",
    description="Create a new RAG configuration preset.",
)
async def create_preset(preset_data: RagConfigCreate) -> RagConfigResponse:
    """Create new RAG config preset."""
    try:
        with get_session() as session:
            # Check for duplicate name
            existing = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_data.preset_name
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Preset '{preset_data.preset_name}' already exists"
                )

            # Create new preset
            new_preset = RagConfig(
                preset_name=preset_data.preset_name,
                is_default=preset_data.is_default,
                description=preset_data.description,
                config=preset_data.config.model_dump()
            )
            session.add(new_preset)
            session.commit()
            session.refresh(new_preset)

            return RagConfigResponse.model_validate(new_preset)

    except HTTPException:
        raise
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Preset name already exists: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create preset: {str(e)}"
        )


# ============================================================================
# PUT Endpoints
# ============================================================================

@router.put(
    "/{preset_name}",
    response_model=RagConfigResponse,
    summary="Update preset",
    description="Update an existing RAG configuration preset.",
)
async def update_preset(preset_name: str, update_data: RagConfigUpdate) -> RagConfigResponse:
    """Update RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Update fields
            if update_data.description is not None:
                preset.description = update_data.description
            if update_data.config is not None:
                preset.config = update_data.config.model_dump()

            session.commit()
            session.refresh(preset)

            return RagConfigResponse.model_validate(preset)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preset: {str(e)}"
        )


@router.put(
    "/{preset_name}/set-default",
    response_model=RagConfigResponse,
    summary="Set preset as default",
    description="Mark a preset as the default configuration. Unsets any other default.",
)
async def set_default_preset(preset_name: str) -> RagConfigResponse:
    """Set preset as default."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Set as default (trigger will handle unsetting others)
            preset.is_default = True
            session.commit()
            session.refresh(preset)

            return RagConfigResponse.model_validate(preset)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default: {str(e)}"
        )


# ============================================================================
# DELETE Endpoint
# ============================================================================

@router.delete(
    "/{preset_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete preset",
    description="Delete a RAG configuration preset. Cannot delete the default preset.",
)
async def delete_preset(preset_name: str):
    """Delete RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Prevent deleting default preset
            if preset.is_default:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete default preset. Set another preset as default first."
                )

            session.delete(preset)
            session.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete preset: {str(e)}"
        )
