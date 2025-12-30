"""
Unit tests for migration 024 - Add automatic evaluation mode.

Tests the migration SQL file content and structure.
"""

import os


class TestMigration024SQL:
    """Tests for migration 024 SQL file content."""

    def test_migration_file_exists(self):
        """Test that migration file exists."""
        migration_path = "/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql"
        assert os.path.exists(migration_path)

    def test_migration_adds_auto_mode_enabled_column(self):
        """Test that migration adds auto_mode_enabled column to experiments."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "ALTER TABLE experiments" in content
        assert "ADD COLUMN IF NOT EXISTS auto_mode_enabled BOOLEAN NOT NULL DEFAULT FALSE" in content

    def test_migration_adds_auto_answer_provider_column(self):
        """Test that migration adds auto_answer_provider column to experiments."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "ADD COLUMN IF NOT EXISTS auto_answer_provider VARCHAR(50)" in content

    def test_migration_adds_auto_judge_provider_column(self):
        """Test that migration adds auto_judge_provider column to experiments."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "ADD COLUMN IF NOT EXISTS auto_judge_provider VARCHAR(50)" in content

    def test_migration_adds_check_constraint(self):
        """Test that migration adds CHECK constraint for provider validation."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "ADD CONSTRAINT chk_auto_mode_providers" in content
        assert "CHECK" in content
        assert "auto_mode_enabled = FALSE" in content or "auto_mode_enabled = TRUE" in content

    def test_migration_adds_prompt_group_id_column(self):
        """Test that migration adds prompt_group_id to experiment_prompts."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "ALTER TABLE experiment_prompts" in content
        assert "ADD COLUMN IF NOT EXISTS prompt_group_id INTEGER" in content

    def test_migration_creates_index_on_group_id(self):
        """Test that migration creates index on (experiment_id, prompt_group_id)."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "CREATE INDEX IF NOT EXISTS idx_experiment_prompts_group" in content
        assert "ON experiment_prompts(experiment_id, prompt_group_id)" in content
        assert "WHERE prompt_group_id IS NOT NULL" in content

    def test_migration_adds_column_comments(self):
        """Test that migration includes comments for new columns."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        assert "COMMENT ON COLUMN experiments.auto_mode_enabled" in content
        assert "COMMENT ON COLUMN experiments.auto_answer_provider" in content
        assert "COMMENT ON COLUMN experiments.auto_judge_provider" in content
        assert "COMMENT ON COLUMN experiment_prompts.prompt_group_id" in content

    def test_migration_uses_if_not_exists(self):
        """Test that migration uses IF NOT EXISTS for idempotency."""
        with open("/home/dardawk/python/vulcanlab/migrations/024_add_auto_eval_mode.sql", "r") as f:
            content = f.read()

        # Should have IF NOT EXISTS for column additions and index
        assert content.count("IF NOT EXISTS") >= 4
