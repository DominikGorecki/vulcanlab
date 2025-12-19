"""
Unit tests for RAG config Pydantic schemas.

Tests validation logic for RAG configuration parameters including
the new sentence filter fields.
"""

import pytest
from pydantic import ValidationError

from vulcanlab_api.schemas.rag_config import (
    RetrievalParams,
    RagConfigParams,
    RagConfigCreate,
    RagConfigUpdate,
)


class TestRetrievalParamsValidation:
    """Test validation for RetrievalParams schema."""

    def test_min_sentence_filter_enabled_accepts_boolean(self):
        """Test that min_sentence_filter_enabled accepts boolean values."""
        # Test True
        params = RetrievalParams(min_sentence_filter_enabled=True)
        assert params.min_sentence_filter_enabled is True

        # Test False
        params = RetrievalParams(min_sentence_filter_enabled=False)
        assert params.min_sentence_filter_enabled is False

    def test_min_sentence_count_accepts_valid_values(self):
        """Test that min_sentence_count accepts values >= 1."""
        # Test minimum valid value
        params = RetrievalParams(min_sentence_count=1)
        assert params.min_sentence_count == 1

        # Test normal value
        params = RetrievalParams(min_sentence_count=5)
        assert params.min_sentence_count == 5

        # Test larger value
        params = RetrievalParams(min_sentence_count=100)
        assert params.min_sentence_count == 100

    def test_min_sentence_count_rejects_zero(self):
        """Test that min_sentence_count rejects 0."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalParams(min_sentence_count=0)

        # Check that the error is about the constraint
        errors = exc_info.value.errors()
        assert any('greater than or equal to 1' in str(err) for err in errors)

    def test_min_sentence_count_rejects_negative(self):
        """Test that min_sentence_count rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalParams(min_sentence_count=-1)

        errors = exc_info.value.errors()
        assert any('greater than or equal to 1' in str(err) for err in errors)

    def test_default_values(self):
        """Test that default values are set correctly."""
        params = RetrievalParams()
        assert params.min_sentence_filter_enabled is False
        assert params.min_sentence_count == 5

    def test_valid_config_with_new_fields(self):
        """Test that a complete valid config with new fields is accepted."""
        params = RetrievalParams(
            dense_limit=19,
            lexical_limit=5,
            rrf_k=50,
            top_k_rrf=75,
            top_n_final=17,
            entity_boost=0.05,
            min_word_count=150,
            min_char_count=250,
            min_content_length=750,
            enrich_lines_above=0,
            enrich_lines_below=13,
            mmr_lambda=0.7,
            reranker_batch_size=8,
            reranker_max_length=512,
            min_sentence_filter_enabled=True,
            min_sentence_count=10
        )
        assert params.min_sentence_filter_enabled is True
        assert params.min_sentence_count == 10


class TestRagConfigParamsValidation:
    """Test validation for complete RagConfigParams schema."""

    def test_config_includes_new_fields(self):
        """Test that RagConfigParams accepts new fields in retrieval section."""
        from vulcanlab_api.schemas.rag_config import ConsolidationParams, AugmentationParams

        config = RagConfigParams(
            retrieval=RetrievalParams(
                min_sentence_filter_enabled=True,
                min_sentence_count=8
            ),
            consolidation=ConsolidationParams(),
            augmentation=AugmentationParams()
        )

        assert config.retrieval.min_sentence_filter_enabled is True
        assert config.retrieval.min_sentence_count == 8


class TestRagConfigCreateValidation:
    """Test validation for RagConfigCreate request schema."""

    def test_create_accepts_config_with_new_fields(self):
        """Test that RagConfigCreate accepts config with new sentence filter fields."""
        from vulcanlab_api.schemas.rag_config import ConsolidationParams, AugmentationParams

        config_create = RagConfigCreate(
            preset_name="Test Preset",
            description="Test description",
            is_default=False,
            config=RagConfigParams(
                retrieval=RetrievalParams(
                    min_sentence_filter_enabled=True,
                    min_sentence_count=7
                ),
                consolidation=ConsolidationParams(),
                augmentation=AugmentationParams()
            )
        )

        assert config_create.config.retrieval.min_sentence_filter_enabled is True
        assert config_create.config.retrieval.min_sentence_count == 7


class TestRagConfigUpdateValidation:
    """Test validation for RagConfigUpdate request schema."""

    def test_update_accepts_config_with_new_fields(self):
        """Test that RagConfigUpdate accepts config with new sentence filter fields."""
        from vulcanlab_api.schemas.rag_config import ConsolidationParams, AugmentationParams

        config_update = RagConfigUpdate(
            description="Updated description",
            config=RagConfigParams(
                retrieval=RetrievalParams(
                    min_sentence_filter_enabled=False,
                    min_sentence_count=3
                ),
                consolidation=ConsolidationParams(),
                augmentation=AugmentationParams()
            )
        )

        assert config_update.config.retrieval.min_sentence_filter_enabled is False
        assert config_update.config.retrieval.min_sentence_count == 3

    def test_update_rejects_invalid_min_sentence_count(self):
        """Test that RagConfigUpdate rejects invalid min_sentence_count."""
        from vulcanlab_api.schemas.rag_config import ConsolidationParams, AugmentationParams

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
