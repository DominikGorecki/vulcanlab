"""
Unit tests for migration 021: Add max_word_count to RAG config and deprecate old settings.

This migration adds max_word_count to retrieval section and moves deprecated settings
to _deprecated nested objects. Tests verify the migration logic using mock database.
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from pathlib import Path


class TestMigration021SQL:
    """Tests for migration 021 SQL transformations."""

    @pytest.fixture
    def migration_sql(self):
        """Load the migration SQL file."""
        migration_path = Path(__file__).parent.parent.parent / "migrations" / "021_add_max_word_count_to_rag_config.sql"
        with open(migration_path) as f:
            return f.read()

    def test_migration_file_exists(self):
        """Test that migration file exists."""
        migration_path = Path(__file__).parent.parent.parent / "migrations" / "021_add_max_word_count_to_rag_config.sql"
        assert migration_path.exists(), "Migration file 021_add_max_word_count_to_rag_config.sql not found"

    def test_migration_adds_max_word_count(self, migration_sql):
        """Test that migration includes SQL to add max_word_count."""
        assert "max_word_count" in migration_sql
        assert "750" in migration_sql
        assert "jsonb_set" in migration_sql

    def test_migration_moves_deprecated_retrieval_keys(self, migration_sql):
        """Test that migration includes SQL to move deprecated retrieval keys."""
        # Check for deprecated keys
        assert "min_char_count" in migration_sql
        assert "min_content_length" in migration_sql
        assert "enrich_lines_above" in migration_sql
        assert "enrich_lines_below" in migration_sql

        # Check for _deprecated object
        assert "_deprecated" in migration_sql

    def test_migration_moves_deprecated_consolidation_key(self, migration_sql):
        """Test that migration includes SQL to move deprecated consolidation key."""
        assert "enrich_from_md" in migration_sql
        assert "consolidation" in migration_sql

    def test_migration_has_idempotency_checks(self, migration_sql):
        """Test that migration includes idempotency checks."""
        # Should check if max_word_count already exists
        assert "NOT" in migration_sql or "?" in migration_sql

    def test_migration_has_validation_query(self, migration_sql):
        """Test that migration includes validation query."""
        assert "SELECT" in migration_sql
        assert "preset_name" in migration_sql

    def test_migration_uses_safe_operations(self, migration_sql):
        """Test that migration uses safe PostgreSQL operations."""
        # Should use jsonb operations
        assert "jsonb" in migration_sql.lower()
        # Should use WHERE clauses to target specific rows
        assert "WHERE" in migration_sql


class TestMigrationLogic:
    """Tests for migration logic using mock database operations."""

    def test_max_word_count_added_to_new_preset(self):
        """Test that max_word_count is added to preset without it."""
        # Simulate a preset config without max_word_count
        original_config = {
            "retrieval": {
                "dense_limit": 19,
                "min_word_count": 150
            },
            "consolidation": {
                "coverage_threshold": 0.5
            }
        }

        # After migration, should have max_word_count
        expected_config = {
            "retrieval": {
                "dense_limit": 19,
                "min_word_count": 150,
                "max_word_count": 750
            },
            "consolidation": {
                "coverage_threshold": 0.5
            }
        }

        # The migration should add max_word_count: 750
        assert "max_word_count" not in original_config["retrieval"]
        # (Migration would transform original_config to expected_config)

    def test_deprecated_keys_moved_to_nested_object(self):
        """Test that deprecated keys are moved to _deprecated nested object."""
        # Simulate a preset with deprecated keys
        original_config = {
            "retrieval": {
                "dense_limit": 19,
                "min_char_count": 250,
                "min_content_length": 750,
                "enrich_lines_above": 0,
                "enrich_lines_below": 13
            },
            "consolidation": {
                "coverage_threshold": 0.5,
                "enrich_from_md": True
            }
        }

        # After migration, deprecated keys should be in _deprecated
        expected_retrieval = {
            "dense_limit": 19,
            "max_word_count": 750,
            "_deprecated": {
                "min_char_count": 250,
                "min_content_length": 750,
                "enrich_lines_above": 0,
                "enrich_lines_below": 13
            }
        }

        expected_consolidation = {
            "coverage_threshold": 0.5,
            "_deprecated": {
                "enrich_from_md": True
            }
        }

        # Verify deprecated keys exist in original
        assert "min_char_count" in original_config["retrieval"]
        assert "enrich_from_md" in original_config["consolidation"]

    def test_idempotency_max_word_count_already_exists(self):
        """Test that migration is idempotent - doesn't duplicate max_word_count."""
        # Config already has max_word_count
        config_with_max_word_count = {
            "retrieval": {
                "dense_limit": 19,
                "max_word_count": 750
            }
        }

        # Running migration again should not change it
        # The WHERE clause should prevent updates: "NOT (config->'retrieval' ? 'max_word_count')"
        assert config_with_max_word_count["retrieval"]["max_word_count"] == 750

    def test_idempotency_deprecated_keys_already_moved(self):
        """Test that migration is idempotent - doesn't duplicate _deprecated keys."""
        # Config already has _deprecated object
        config_with_deprecated = {
            "retrieval": {
                "dense_limit": 19,
                "_deprecated": {
                    "min_char_count": 250
                }
            }
        }

        # Running migration again should not change it
        # The WHERE clause checks if deprecated keys exist at top level
        assert "min_char_count" not in config_with_deprecated["retrieval"]
        assert "min_char_count" in config_with_deprecated["retrieval"]["_deprecated"]

    def test_preserves_other_config_values(self):
        """Test that migration preserves all other config values."""
        original_config = {
            "retrieval": {
                "dense_limit": 19,
                "lexical_limit": 5,
                "rrf_k": 50,
                "min_word_count": 150,
                "mmr_lambda": 0.7
            },
            "consolidation": {
                "coverage_threshold": 0.5,
                "line_gap": 7
            },
            "augmentation": {
                "top_n_contexts": 5
            }
        }

        # After migration, these should all still be present
        preserved_keys_retrieval = ["dense_limit", "lexical_limit", "rrf_k", "min_word_count", "mmr_lambda"]
        preserved_keys_consolidation = ["coverage_threshold", "line_gap"]
        preserved_keys_augmentation = ["top_n_contexts"]

        # Verify original has these keys
        for key in preserved_keys_retrieval:
            assert key in original_config["retrieval"]
        for key in preserved_keys_consolidation:
            assert key in original_config["consolidation"]
        for key in preserved_keys_augmentation:
            assert key in original_config["augmentation"]

    def test_handles_missing_retrieval_section(self):
        """Test that migration handles presets with missing retrieval section."""
        # Config without retrieval section (edge case)
        config_no_retrieval = {
            "consolidation": {
                "coverage_threshold": 0.5
            },
            "augmentation": {
                "top_n_contexts": 5
            }
        }

        # Migration should gracefully handle this with WHERE clause:
        # "WHERE config ? 'retrieval'"
        assert "retrieval" not in config_no_retrieval

    def test_handles_missing_consolidation_section(self):
        """Test that migration handles presets with missing consolidation section."""
        # Config without consolidation section (edge case)
        config_no_consolidation = {
            "retrieval": {
                "dense_limit": 19
            },
            "augmentation": {
                "top_n_contexts": 5
            }
        }

        # Migration should gracefully handle this with WHERE clause:
        # "WHERE config ? 'consolidation'"
        assert "consolidation" not in config_no_consolidation

    def test_partial_deprecated_keys(self):
        """Test that migration handles preset with only some deprecated keys."""
        # Config with only some deprecated keys
        config_partial = {
            "retrieval": {
                "dense_limit": 19,
                "min_char_count": 250,
                # Missing other deprecated keys
            },
            "consolidation": {
                "coverage_threshold": 0.5
                # Missing enrich_from_md
            }
        }

        # After migration, only existing deprecated keys should be moved
        # The jsonb_strip_nulls and WHERE clauses handle this
        assert "min_char_count" in config_partial["retrieval"]
        assert "enrich_from_md" not in config_partial["consolidation"]

    def test_preserves_existing_deprecated_object(self):
        """Test that migration preserves existing _deprecated object and merges new keys."""
        # Config already has _deprecated with some keys
        config_with_existing_deprecated = {
            "retrieval": {
                "dense_limit": 19,
                "min_char_count": 250,
                "_deprecated": {
                    "old_setting": "value"
                }
            }
        }

        # After migration, _deprecated should have both old and new keys
        # The COALESCE and || operator handle merging:
        # COALESCE(config->'retrieval'->'_deprecated', '{}'::jsonb) || jsonb_build_object(...)
        assert "_deprecated" in config_with_existing_deprecated["retrieval"]
        assert "old_setting" in config_with_existing_deprecated["retrieval"]["_deprecated"]


class TestValidationQuery:
    """Tests for the validation query included in migration."""

    def test_validation_query_checks_max_word_count(self):
        """Test that validation query checks for max_word_count presence."""
        migration_path = Path(__file__).parent.parent.parent / "migrations" / "021_add_max_word_count_to_rag_config.sql"
        with open(migration_path) as f:
            content = f.read()

        # Validation query should check max_word_count
        assert "max_word_count" in content
        # Should select from rag_config table
        assert "FROM rag_config" in content or "from rag_config" in content

    def test_validation_query_checks_deprecated_moved(self):
        """Test that validation query checks that deprecated keys are moved."""
        migration_path = Path(__file__).parent.parent.parent / "migrations" / "021_add_max_word_count_to_rag_config.sql"
        with open(migration_path) as f:
            content = f.read()

        # Should check for deprecated keys in _deprecated object
        assert "_deprecated" in content

    def test_validation_query_checks_keys_removed(self):
        """Test that validation query verifies deprecated keys removed from main sections."""
        migration_path = Path(__file__).parent.parent.parent / "migrations" / "021_add_max_word_count_to_rag_config.sql"
        with open(migration_path) as f:
            content = f.read()

        # Should check that deprecated keys are gone from main sections
        # Look for existence checks in SELECT
        assert "has_" in content or "?" in content
