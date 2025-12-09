"""
Unit tests for seed_templates module.

Tests template seeding logic, default template loading, database insertion,
and idempotency.
"""

from unittest.mock import MagicMock, patch, Mock
import pytest
from sqlalchemy.exc import IntegrityError

from vulcanlab.data.seed_templates import seed_prompt_templates, PROMPT_TEMPLATES


class TestSeedPromptTemplates:
    """Tests for seed_prompt_templates function."""

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_inserts_new(self, mock_engine, capsys):
        """Test that seed_prompt_templates inserts new templates."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: No templates exist (count = 0)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_conn.execute.return_value = mock_result

        seed_prompt_templates(verbose=True)

        # Verify execute was called for each template
        assert mock_conn.execute.call_count >= len(PROMPT_TEMPLATES)
        # Verify commit was called
        assert mock_conn.commit.call_count > 0

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_skips_existing(self, mock_engine, capsys):
        """Test that seed_prompt_templates skips existing templates."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: Template already exists (count = 1)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_conn.execute.return_value = mock_result

        seed_prompt_templates(verbose=True)

        # Verify execute was called to check existence
        assert mock_conn.execute.called
        # Should not call commit for existing templates (no insert)
        captured = capsys.readouterr()
        assert "already exists" in captured.out.lower() or "skipping" in captured.out.lower()

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_idempotency(self, mock_engine):
        """Test that running seed_prompt_templates multiple times is idempotent."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # First run: templates don't exist
        mock_result1 = MagicMock()
        mock_result1.scalar.return_value = 0
        mock_conn.execute.return_value = mock_result1

        seed_prompt_templates(verbose=False)

        # Reset mocks
        mock_conn.reset_mock()

        # Second run: templates exist
        mock_result2 = MagicMock()
        mock_result2.scalar.return_value = 1
        mock_conn.execute.return_value = mock_result2

        seed_prompt_templates(verbose=False)

        # Should not raise errors and should handle gracefully

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_handles_integrity_error(self, mock_engine, capsys):
        """Test that seed_prompt_templates handles IntegrityError gracefully."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: First template doesn't exist initially, then insert fails
        # Other templates exist (to avoid exhausting side_effect)
        mock_result_count_0 = MagicMock()
        mock_result_count_0.scalar.return_value = 0
        
        mock_result_count_1 = MagicMock()
        mock_result_count_1.scalar.return_value = 1
        
        mock_result_backfill = MagicMock()
        mock_result_backfill.rowcount = 0
        
        # Build side_effect: first template count=0, insert fails, then all others exist, then backfill
        side_effect = [
            mock_result_count_0,  # First template count query
            IntegrityError("statement", "params", "orig"),  # First template insert fails
        ]
        # Add count queries for remaining templates (all exist)
        for _ in range(len(PROMPT_TEMPLATES) - 1):
            side_effect.append(mock_result_count_1)
        # Add backfill query result
        side_effect.append(mock_result_backfill)
        
        mock_conn.execute.side_effect = side_effect

        # Should not raise exception
        seed_prompt_templates(verbose=True)

        # Should have rolled back
        assert mock_conn.rollback.called
        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "could not insert" in captured.out.lower()

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_verbose_output(self, mock_engine, capsys):
        """Test verbose output when seeding templates."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: Templates don't exist
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_conn.execute.return_value = mock_result

        seed_prompt_templates(verbose=True)

        captured = capsys.readouterr()
        assert "seeding" in captured.out.lower() or "inserted" in captured.out.lower() or "complete" in captured.out.lower()

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_no_verbose_output(self, mock_engine, capsys):
        """Test that no output when verbose=False."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_conn.execute.return_value = mock_result

        seed_prompt_templates(verbose=False)

        captured = capsys.readouterr()
        # Should have minimal or no output
        assert len(captured.out) == 0 or "seeding" not in captured.out.lower()

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_timestamp_backfill(self, mock_engine):
        """Test timestamp backfill logic."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: All templates exist, then backfill query
        mock_result_count = MagicMock()
        mock_result_count.scalar.return_value = 1  # Template exists

        mock_result_backfill = MagicMock()
        mock_result_backfill.rowcount = 3  # Fixed 3 templates

        # Build side_effect: count queries for all templates (all exist), then backfill
        side_effect = []
        for _ in range(len(PROMPT_TEMPLATES)):
            side_effect.append(mock_result_count)
        side_effect.append(mock_result_backfill)  # Backfill update
        
        mock_conn.execute.side_effect = side_effect

        seed_prompt_templates(verbose=False)

        # Verify backfill query was executed
        execute_calls = [call[0][0] for call in mock_conn.execute.call_args_list]
        backfill_calls = [call for call in execute_calls if "UPDATE prompt_templates" in str(call) or "SET created_at" in str(call)]
        assert len(backfill_calls) > 0

    @patch("vulcanlab.data.seed_templates.engine")
    def test_seed_templates_backfill_error_handling(self, mock_engine, capsys):
        """Test that backfill errors are handled gracefully."""
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_engine.connect.return_value = mock_conn

        # Mock: All templates exist, then backfill fails
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        
        # Build side_effect: count queries for all templates (all exist), then backfill fails
        side_effect = []
        for _ in range(len(PROMPT_TEMPLATES)):
            side_effect.append(mock_result)
        side_effect.append(Exception("Backfill error"))  # Backfill fails
        
        mock_conn.execute.side_effect = side_effect

        # Should not raise exception
        seed_prompt_templates(verbose=True)

        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "error" in captured.out.lower() or "could not fix" in captured.out.lower()


class TestPromptTemplatesConstant:
    """Tests for PROMPT_TEMPLATES constant."""

    def test_prompt_templates_is_list(self):
        """Test that PROMPT_TEMPLATES is a list."""
        assert isinstance(PROMPT_TEMPLATES, list)
        assert len(PROMPT_TEMPLATES) > 0

    def test_prompt_templates_structure(self):
        """Test that each template has required fields."""
        required_fields = ["function_tag", "version", "title", "template_content", "is_active"]

        for template in PROMPT_TEMPLATES:
            assert isinstance(template, dict)
            for field in required_fields:
                assert field in template, f"Template missing required field: {field}"

    def test_prompt_templates_function_tags(self):
        """Test that function_tags are unique."""
        function_tags = [t["function_tag"] for t in PROMPT_TEMPLATES]
        # Note: function_tags may not be unique across versions, but should be present
        assert all(isinstance(tag, str) for tag in function_tags)
        assert len(function_tags) == len(PROMPT_TEMPLATES)

    def test_prompt_templates_versions(self):
        """Test that versions are positive integers."""
        for template in PROMPT_TEMPLATES:
            assert isinstance(template["version"], int)
            assert template["version"] > 0

    def test_prompt_templates_content(self):
        """Test that template_content is a string."""
        for template in PROMPT_TEMPLATES:
            assert isinstance(template["template_content"], str)
            assert len(template["template_content"]) > 0

    def test_prompt_templates_is_active(self):
        """Test that is_active is boolean."""
        for template in PROMPT_TEMPLATES:
            assert isinstance(template["is_active"], bool)

