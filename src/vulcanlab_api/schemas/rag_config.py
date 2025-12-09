"""
Pydantic schemas for RAG configuration API.

Defines request/response models with validation for RAG config presets.
Validation ensures parameters are within acceptable ranges per PRD specs.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# Parameter Schemas with Validation
# ============================================================================

class RetrievalParams(BaseModel):
    """Retrieval stage parameters with validation constraints."""

    dense_limit: int = Field(19, ge=0, le=100, description="Max results per dense vector query (0 to disable)")
    lexical_limit: int = Field(5, ge=0, le=50, description="Max results per lexical (BM25) query (0 to disable)")
    rrf_k: int = Field(50, ge=1, le=100, description="RRF constant for rank fusion")
    top_k_rrf: int = Field(75, ge=1, le=200, description="Top candidates after RRF fusion")
    top_n_final: int = Field(17, ge=1, le=50, description="Final number of results after MMR")
    entity_boost: float = Field(0.05, ge=0.0, le=0.5, description="Score boost per entity match")
    min_word_count: int = Field(150, ge=0, le=1000, description="Minimum words in chunk (0 to disable)")
    min_char_count: int = Field(250, ge=0, le=5000, description="Minimum characters in chunk (0 to disable)")
    min_content_length: int = Field(750, ge=0, le=5000, description="Min content length before enrichment")
    enrich_lines_above: int = Field(0, ge=0, le=50, description="Lines to add above chunk when enriching")
    enrich_lines_below: int = Field(13, ge=0, le=50, description="Lines to add below chunk when enriching")
    mmr_lambda: float = Field(0.7, ge=0.0, le=1.0, description="MMR balance: relevance (1.0) vs diversity (0.0)")
    reranker_batch_size: int = Field(8, ge=1, le=32, description="Batch size for BGE reranker inference")
    reranker_max_length: int = Field(512, ge=128, le=1024, description="Max token length for reranker")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dense_limit": 19,
                "lexical_limit": 5,
                "rrf_k": 50,
                "top_k_rrf": 75,
                "top_n_final": 17,
                "entity_boost": 0.05,
                "min_word_count": 150,
                "min_char_count": 250,
                "min_content_length": 750,
                "enrich_lines_above": 0,
                "enrich_lines_below": 13,
                "mmr_lambda": 0.7,
                "reranker_batch_size": 8,
                "reranker_max_length": 512
            }
        }
    )

    @model_validator(mode='after')
    def validate_top_k_consistency(self):
        """Ensure top_k_rrf >= top_n_final."""
        if self.top_k_rrf < self.top_n_final:
            raise ValueError("top_k_rrf must be >= top_n_final")
        return self


class ConsolidationParams(BaseModel):
    """Consolidation stage parameters with validation constraints."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }
    )

    coverage_threshold: float = Field(0.5, ge=0.0, le=1.0, description="% of parent coverage to replace with parent")
    line_gap: int = Field(7, ge=0, le=50, description="Max lines between chunks to merge them")
    min_content_length: int = Field(350, ge=0, le=5000, description="Min characters for final output inclusion")
    enrich_from_md: bool = Field(True, description="Read content from markdown during consolidation")


class AugmentationParams(BaseModel):
    """Augmentation stage parameters with validation constraints."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "top_n_contexts": 5
            }
        }
    )

    top_n_contexts: int = Field(5, ge=1, le=20, description="Number of top contexts to include in prompt")


class RagConfigParams(BaseModel):
    """Complete RAG configuration parameters (all stages)."""

    retrieval: RetrievalParams
    consolidation: ConsolidationParams
    augmentation: AugmentationParams


# ============================================================================
# Request Schemas
# ============================================================================

class RagConfigCreate(BaseModel):
    """Request schema for creating a new RAG config preset."""

    preset_name: str = Field(..., min_length=1, max_length=100, description="Unique preset name")
    description: Optional[str] = Field(None, description="Optional description of preset purpose")
    is_default: bool = Field(False, description="Set as default preset (will unset other defaults)")
    config: RagConfigParams = Field(..., description="Configuration parameters")

    @field_validator('preset_name')
    @classmethod
    def validate_preset_name(cls, v: str) -> str:
        """Validate preset name: no leading/trailing whitespace, no special chars."""
        v = v.strip()
        if not v:
            raise ValueError("Preset name cannot be empty or whitespace")
        # Allow alphanumeric, spaces, hyphens, underscores
        if not all(c.isalnum() or c in [' ', '-', '_'] for c in v):
            raise ValueError("Preset name can only contain letters, numbers, spaces, hyphens, and underscores")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "preset_name": "Fast Retrieval",
                "description": "Optimized for speed with fewer candidates",
                "is_default": False,
                "config": {
                    "retrieval": {
                        "dense_limit": 10,
                        "lexical_limit": 3,
                        "rrf_k": 50,
                        "top_k_rrf": 75,
                        "top_n_final": 10,
                        "entity_boost": 0.05,
                        "min_word_count": 150,
                        "min_char_count": 250,
                        "min_content_length": 750,
                        "enrich_lines_above": 0,
                        "enrich_lines_below": 13,
                        "mmr_lambda": 0.7,
                        "reranker_batch_size": 8,
                        "reranker_max_length": 512
                    },
                    "consolidation": {"coverage_threshold": 0.5, "line_gap": 7, "min_content_length": 350, "enrich_from_md": True},
                    "augmentation": {"top_n_contexts": 3}
                }
            }
        }
    )


class RagConfigUpdate(BaseModel):
    """Request schema for updating an existing RAG config preset."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated description",
                "config": {
                    "retrieval": {
                        "dense_limit": 20,
                        "lexical_limit": 5,
                        "rrf_k": 50,
                        "top_k_rrf": 75,
                        "top_n_final": 17,
                        "entity_boost": 0.05,
                        "min_word_count": 150,
                        "min_char_count": 250,
                        "min_content_length": 750,
                        "enrich_lines_above": 0,
                        "enrich_lines_below": 13,
                        "mmr_lambda": 0.7,
                        "reranker_batch_size": 8,
                        "reranker_max_length": 512
                    },
                    "consolidation": {"coverage_threshold": 0.5, "line_gap": 10, "min_content_length": 350, "enrich_from_md": True},
                    "augmentation": {"top_n_contexts": 7}
                }
            }
        }
    )

    description: Optional[str] = Field(None, description="Update preset description")
    config: Optional[RagConfigParams] = Field(None, description="Update configuration parameters")


# ============================================================================
# Response Schema
# ============================================================================

class RagConfigResponse(BaseModel):
    """Response schema for RAG config preset."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "preset_name": "Default",
                "is_default": True,
                "description": "Default balanced configuration",
                "config": {
                    "retrieval": {"dense_limit": 19, "lexical_limit": 5, "rrf_k": 50, "top_k_rrf": 75, "top_n_final": 17},
                    "consolidation": {"coverage_threshold": 0.5, "line_gap": 7, "min_content_length": 350, "enrich_from_md": True},
                    "augmentation": {"top_n_contexts": 5}
                },
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    )

    id: int
    preset_name: str
    is_default: bool
    description: Optional[str]
    config: RagConfigParams
    created_at: datetime
    updated_at: datetime
