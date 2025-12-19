"""
Unit tests for RAG config API endpoints.

Tests API validation for RAG configuration endpoints, focusing on
the new sentence filter fields.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from vulcanlab_api.schemas.rag_config import (
    RagConfigCreate,
    RagConfigUpdate,
    RagConfigParams,
    RetrievalParams,
    ConsolidationParams,
    AugmentationParams,
)


class TestRagConfigAPIValidation:
    """Test API validation for RAG config endpoints."""

    def test_api_accepts_valid_config_with_sentence_fields(self):
        """Test that API accepts valid config with new sentence filter fields."""
        config_data = RagConfigCreate(
            preset_name="Test Config",
            description="Test description",
            is_default=False,
            config=RagConfigParams(
                retrieval=RetrievalParams(
                    min_sentence_filter_enabled=True,
                    min_sentence_count=10
                ),
                consolidation=ConsolidationParams(),
                augmentation=AugmentationParams()
            )
        )

        # Validate that the config was created successfully
        assert config_data.config.retrieval.min_sentence_filter_enabled is True
        assert config_data.config.retrieval.min_sentence_count == 10

    def test_api_rejects_min_sentence_count_zero(self):
        """Test that API rejects min_sentence_count < 1."""
        with pytest.raises(ValidationError) as exc_info:
            RagConfigCreate(
                preset_name="Invalid Config",
                description="Should fail validation",
                is_default=False,
                config=RagConfigParams(
                    retrieval=RetrievalParams(
                        min_sentence_count=0  # Invalid: must be >= 1
                    ),
                    consolidation=ConsolidationParams(),
                    augmentation=AugmentationParams()
                )
            )

        errors = exc_info.value.errors()
        assert any('greater than or equal to 1' in str(err) for err in errors)

    def test_api_rejects_negative_min_sentence_count(self):
        """Test that API rejects negative min_sentence_count."""
        with pytest.raises(ValidationError) as exc_info:
            RagConfigCreate(
                preset_name="Invalid Config",
                description="Should fail validation",
                is_default=False,
                config=RagConfigParams(
                    retrieval=RetrievalParams(
                        min_sentence_count=-5  # Invalid: must be >= 1
                    ),
                    consolidation=ConsolidationParams(),
                    augmentation=AugmentationParams()
                )
            )

        errors = exc_info.value.errors()
        assert any('greater than or equal to 1' in str(err) for err in errors)

    def test_api_update_accepts_valid_sentence_fields(self):
        """Test that API update accepts valid sentence filter fields."""
        update_data = RagConfigUpdate(
            description="Updated config",
            config=RagConfigParams(
                retrieval=RetrievalParams(
                    min_sentence_filter_enabled=False,
                    min_sentence_count=3
                ),
                consolidation=ConsolidationParams(),
                augmentation=AugmentationParams()
            )
        )

        assert update_data.config.retrieval.min_sentence_filter_enabled is False
        assert update_data.config.retrieval.min_sentence_count == 3

    def test_api_update_rejects_invalid_min_sentence_count(self):
        """Test that API update rejects invalid min_sentence_count."""
        with pytest.raises(ValidationError):
            RagConfigUpdate(
                config=RagConfigParams(
                    retrieval=RetrievalParams(
                        min_sentence_count=0  # Invalid: must be >= 1
                    ),
                    consolidation=ConsolidationParams(),
                    augmentation=AugmentationParams()
                )
            )

    def test_default_config_includes_sentence_fields(self):
        """Test that default config includes sentence filter fields with correct defaults."""
        params = RetrievalParams()

        # Verify defaults match the spec
        assert params.min_sentence_filter_enabled is False
        assert params.min_sentence_count == 5

    def test_config_serialization_includes_sentence_fields(self):
        """Test that config serialization includes sentence filter fields."""
        config = RagConfigParams(
            retrieval=RetrievalParams(
                min_sentence_filter_enabled=True,
                min_sentence_count=7
            ),
            consolidation=ConsolidationParams(),
            augmentation=AugmentationParams()
        )

        # Serialize to dict
        config_dict = config.model_dump()

        # Verify sentence fields are present in serialized output
        assert 'retrieval' in config_dict
        assert 'min_sentence_filter_enabled' in config_dict['retrieval']
        assert 'min_sentence_count' in config_dict['retrieval']
        assert config_dict['retrieval']['min_sentence_filter_enabled'] is True
        assert config_dict['retrieval']['min_sentence_count'] == 7

    def test_config_deserialization_includes_sentence_fields(self):
        """Test that config can be deserialized from dict with sentence filter fields."""
        config_dict = {
            "retrieval": {
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
                "reranker_max_length": 512,
                "min_sentence_filter_enabled": True,
                "min_sentence_count": 12
            },
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            },
            "augmentation": {
                "top_n_contexts": 5
            }
        }

        config = RagConfigParams(**config_dict)

        assert config.retrieval.min_sentence_filter_enabled is True
        assert config.retrieval.min_sentence_count == 12

    def test_partial_update_preserves_sentence_fields(self):
        """Test that partial updates can modify sentence filter fields."""
        # Create initial config
        initial_config = RagConfigParams(
            retrieval=RetrievalParams(
                min_sentence_filter_enabled=False,
                min_sentence_count=5
            ),
            consolidation=ConsolidationParams(),
            augmentation=AugmentationParams()
        )

        # Create update with modified sentence fields
        updated_config = RagConfigParams(
            retrieval=RetrievalParams(
                min_sentence_filter_enabled=True,
                min_sentence_count=8
            ),
            consolidation=ConsolidationParams(),
            augmentation=AugmentationParams()
        )

        # Verify the update changed the values
        assert updated_config.retrieval.min_sentence_filter_enabled is True
        assert updated_config.retrieval.min_sentence_count == 8

    def test_boundary_values_for_min_sentence_count(self):
        """Test boundary values for min_sentence_count validation."""
        # Test minimum valid value (1)
        config = RetrievalParams(min_sentence_count=1)
        assert config.min_sentence_count == 1

        # Test large value (no upper limit per spec)
        config = RetrievalParams(min_sentence_count=1000)
        assert config.min_sentence_count == 1000

        # Test that 0 is rejected
        with pytest.raises(ValidationError):
            RetrievalParams(min_sentence_count=0)
