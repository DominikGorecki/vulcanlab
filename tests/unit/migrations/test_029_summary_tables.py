"""
Unit tests for migration 029 - Add summary tables.
Implementation of Ticket: work-summarization.T02
"""

import os
import re
import pytest
from unittest.mock import MagicMock

MIGRATION_FILE = "migrations/029_add_summary_tables.sql"

class TestMigration029SQL:
    """Tests for migration 029 SQL file content and structure."""

    def test_migration_file_exists(self):
        """Test that migration file exists at the correct location."""
        assert os.path.exists(MIGRATION_FILE)

    def test_migration_uses_if_not_exists(self):
        """Test that table and index creations use IF NOT EXISTS for idempotency."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        # Should have IF NOT EXISTS for all three tables
        assert re.search(r"CREATE TABLE IF NOT EXISTS summarize_settings", content)
        assert re.search(r"CREATE TABLE IF NOT EXISTS summary_nodes", content)
        assert re.search(r"CREATE TABLE IF NOT EXISTS work_summaries", content)
        
        # Should have IF NOT EXISTS for indexes
        assert re.search(r"CREATE INDEX IF NOT EXISTS idx_summary_nodes_work_id", content)
        assert re.search(r"CREATE INDEX IF NOT EXISTS idx_summary_nodes_chunk_id", content)
        assert re.search(r"CREATE INDEX IF NOT EXISTS idx_work_summaries_work_id", content)

    def test_summary_nodes_columns(self):
        """Test that summary_nodes has all required columns and foreign keys."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()
            
        # Verify columns and types/constraints
        assert "chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE" in content
        assert "work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE" in content
        assert "gist TEXT NOT NULL" in content
        assert "key_points JSONB NOT NULL DEFAULT '[]'" in content
        assert "definitions JSONB NOT NULL DEFAULT '[]'" in content
        assert "key_terms JSONB NOT NULL DEFAULT '[]'" in content
        assert "examples JSONB NOT NULL DEFAULT '[]'" in content
        assert "start_line INTEGER NOT NULL" in content
        assert "end_line INTEGER NOT NULL" in content
        assert "salience_score FLOAT NOT NULL" in content
        assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL" in content

    def test_work_summaries_constraints(self):
        """Test that work_summaries has CHECK and UNIQUE constraints."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        # Check for type discriminator constraint
        assert "CONSTRAINT chk_work_summary_type CHECK (type IN ('abstract', 'outline', 'key_concepts', 'chapter_summaries'))" in content
        # Check for unique constraint
        assert "CONSTRAINT unq_work_summary_work_type UNIQUE (work_id, type)" in content

    def test_summarize_settings_defaults(self):
        """Test that summarize_settings has correct default values."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        expected_defaults = [
            "h1_always_summarize BOOLEAN DEFAULT true",
            "h2_top_percent INTEGER DEFAULT 100",
            "h3_salience_threshold FLOAT DEFAULT 0.5",
            "h4_salience_threshold FLOAT DEFAULT 0.7",
            "definition_density_weight FLOAT DEFAULT 0.3",
            "list_density_weight FLOAT DEFAULT 0.2",
            "keyphrase_novelty_weight FLOAT DEFAULT 0.2",
            "location_prior_weight FLOAT DEFAULT 0.15",
            "heading_depth_weight FLOAT DEFAULT 0.15"
        ]
        
        for default in expected_defaults:
            assert default in content

    def test_migration_has_comments(self):
        """Test that migration includes table comments for documentation."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        assert "COMMENT ON TABLE summarize_settings IS 'Configuration for salience-based summarization node selection'" in content
        assert "COMMENT ON TABLE summary_nodes IS 'Granular summary data for individual heading-level chunks'" in content
        assert "COMMENT ON TABLE work_summaries IS 'Derived high-level summaries for works (abstract, outline, etc.)'" in content

    def test_migration_has_verification_queries(self):
        """Test that migration includes verification queries at the end."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        # Should check for table existence in information_schema
        assert "information_schema.tables" in content
        assert "SELECT 'summarize_settings table created successfully'" in content
        assert "SELECT 'summary_nodes table created successfully'" in content
        assert "SELECT 'work_summaries table created successfully'" in content

    def test_migration_has_timestamp_trigger(self):
        """Test that migration includes updated_at trigger for settings table."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()

        assert "CREATE OR REPLACE FUNCTION update_summarize_settings_updated_at()" in content
        assert "CREATE TRIGGER trigger_update_summarize_settings_updated_at" in content
        assert "BEFORE UPDATE ON summarize_settings" in content

    def test_sql_syntax_basic_parse(self):
        """
        Check that the migration contains all expected major operations.
        """
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()
            
        # Check that we have the expected number of major operations
        assert content.upper().count("CREATE TABLE IF NOT EXISTS") >= 3
        assert content.upper().count("CREATE INDEX IF NOT EXISTS") >= 3
        assert content.upper().count("CREATE OR REPLACE FUNCTION") >= 1
        assert content.upper().count("CREATE TRIGGER") >= 1
        assert content.upper().count("COMMENT ON TABLE") >= 3
        assert content.upper().count("SELECT") >= 3

    def test_check_constraint_values(self):
        """Verify that the CHECK constraint contains the expected lowercase values."""
        with open(MIGRATION_FILE, "r") as f:
            content = f.read()
            
        match = re.search(r"CHECK\s*\(type IN \((.*?)\)\)", content)
        assert match is not None
        
        allowed_types = match.group(1)
        expected = ["'abstract'", "'outline'", "'key_concepts'", "'chapter_summaries'"]
        for t in expected:
            assert t in allowed_types
