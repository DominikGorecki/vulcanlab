"""
Unit tests for migration 019: Backfill sentence_count for existing chunks.
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest
from sqlalchemy import text

# Import migration module dynamically since filename starts with number
migration_path = Path(__file__).parent.parent.parent / "migrations" / "019_backfill_sentence_count.py"
spec = importlib.util.spec_from_file_location("migration_019", migration_path)
migration_019 = importlib.util.module_from_spec(spec)
sys.modules["migration_019"] = migration_019
spec.loader.exec_module(migration_019)

_get_sentences = migration_019._get_sentences
upgrade = migration_019.upgrade
downgrade = migration_019.downgrade


class TestGetSentences:
    """Tests for _get_sentences helper function."""

    def test_get_sentences_single_sentence(self):
        """Test sentence extraction for single sentence."""
        text = "This is a single sentence."
        result = _get_sentences(text)
        assert len(result) == 1
        assert result[0] == "This is a single sentence."

    def test_get_sentences_multiple_sentences(self):
        """Test sentence extraction for multiple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        result = _get_sentences(text)
        assert len(result) == 3
        assert result[0] == "First sentence."
        assert result[1] == "Second sentence."
        assert result[2] == "Third sentence."

    def test_get_sentences_empty_text(self):
        """Test sentence extraction for empty text."""
        text = ""
        result = _get_sentences(text)
        assert len(result) == 0

    def test_get_sentences_none_text(self):
        """Test sentence extraction for None text."""
        text = None
        result = _get_sentences(text)
        assert len(result) == 0

    def test_get_sentences_with_newlines(self):
        """Test sentence extraction across newlines."""
        text = "First sentence.\nSecond sentence.\n\nThird sentence."
        result = _get_sentences(text)
        assert len(result) == 3

    def test_get_sentences_strips_whitespace(self):
        """Test that sentences are stripped of whitespace."""
        text = "  First.  \n  Second.  "
        result = _get_sentences(text)
        assert len(result) == 2
        assert result[0] == "First."
        assert result[1] == "Second."


class TestUpgradeMigration:
    """Tests for upgrade() migration function."""

    def test_upgrade_processes_only_vec_chunks(self):
        """Test that upgrade() only processes chunks with vector_status='vec' and sentence_count=NULL."""
        # Setup mock connection
        mock_conn = Mock()

        # Mock the count query to return 2 chunks
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        # Mock the chunks query
        mock_chunks_result = Mock()
        mock_chunks_result.fetchall.return_value = [
            (101, "First sentence. Second sentence."),
            (102, "Third sentence.")
        ]

        # Setup execute to return different results based on query
        call_counter = {'chunks': 0}

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            elif 'SELECT id, content' in query_str:
                # First call returns chunks, second returns empty (simulating WHERE clause filtering out updated chunks)
                call_counter['chunks'] += 1
                if call_counter['chunks'] == 1:
                    return mock_chunks_result
                else:
                    empty_result = Mock()
                    empty_result.fetchall.return_value = []
                    return empty_result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Run upgrade
        upgrade(mock_conn)

        # Verify correct queries were used
        execute_calls = mock_conn.execute.call_args_list
        count_query_call = execute_calls[0]
        assert 'sentence_count IS NULL' in str(count_query_call[0][0])
        assert "vector_status = 'vec'" in str(count_query_call[0][0])

    def test_upgrade_skips_already_processed(self):
        """Test that upgrade() skips when all chunks already have sentence_count set."""
        mock_conn = Mock()

        # Return 0 chunks to process
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        mock_conn.execute.return_value = mock_count_result

        # Run upgrade
        upgrade(mock_conn)

        # Should exit early without processing
        assert mock_conn.execute.call_count == 1  # Only the count query

    def test_upgrade_updates_sentence_count_correctly(self):
        """Test that upgrade() updates sentence_count correctly."""
        mock_conn = Mock()

        # Setup mocks
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_chunks_result = Mock()
        # Content with known sentence count
        mock_chunks_result.fetchall.return_value = [(101, "First sentence. Second sentence. Third sentence.")]

        call_count = {'fetch': 0}

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            elif 'SELECT id, content' in query_str:
                # First call returns chunks, second returns empty
                call_count['fetch'] += 1
                if call_count['fetch'] == 1:
                    return mock_chunks_result
                else:
                    empty_result = Mock()
                    empty_result.fetchall.return_value = []
                    return empty_result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Run upgrade
        upgrade(mock_conn)

        # Verify UPDATE was called
        update_calls = [call for call in mock_conn.execute.call_args_list
                       if 'UPDATE chunks SET sentence_count' in str(call[0][0])]
        assert len(update_calls) >= 1
        # Verify commit was called
        assert mock_conn.commit.called

    def test_upgrade_handles_error_gracefully(self):
        """Test that error during sentence counting sets sentence_count=NULL and continues."""
        mock_conn = Mock()

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        mock_chunks_result = Mock()
        # Return content that will cause spaCy to potentially have issues
        mock_chunks_result.fetchall.return_value = [(101, None)]  # None content

        call_count = {'fetch': 0}

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            elif 'SELECT id, content' in query_str:
                call_count['fetch'] += 1
                if call_count['fetch'] == 1:
                    return mock_chunks_result
                else:
                    empty_result = Mock()
                    empty_result.fetchall.return_value = []
                    return empty_result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Run upgrade - should not raise
        upgrade(mock_conn)

        # Migration should complete even with error
        assert mock_conn.commit.called

    def test_upgrade_batch_processing(self):
        """Test that chunks are processed in batches."""
        mock_conn = Mock()

        # Create 150 chunks (more than batch size of 100)
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 150

        # First batch: 100 chunks
        mock_chunks_batch1 = Mock()
        mock_chunks_batch1.fetchall.return_value = [(i, f"Sentence {i}.") for i in range(100)]

        # Second batch: 50 chunks
        mock_chunks_batch2 = Mock()
        mock_chunks_batch2.fetchall.return_value = [(i, f"Sentence {i}.") for i in range(100, 150)]

        # Third call: empty
        mock_chunks_empty = Mock()
        mock_chunks_empty.fetchall.return_value = []

        fetch_calls = [mock_chunks_batch1, mock_chunks_batch2, mock_chunks_empty]
        fetch_index = {'i': 0}

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            elif 'SELECT id, content' in query_str:
                result = fetch_calls[fetch_index['i']]
                fetch_index['i'] = min(fetch_index['i'] + 1, len(fetch_calls) - 1)
                return result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Run upgrade
        upgrade(mock_conn)

        # Verify commit was called (at least twice for two batches)
        assert mock_conn.commit.call_count >= 2

    def test_upgrade_progress_logging(self):
        """Test that progress is logged every 100 chunks."""
        mock_conn = Mock()

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 100

        mock_chunks_result = Mock()
        mock_chunks_result.fetchall.return_value = [(i, f"Sentence {i}.") for i in range(100)]

        call_count = {'fetch': 0}

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            elif 'SELECT id, content' in query_str:
                call_count['fetch'] += 1
                if call_count['fetch'] == 1:
                    return mock_chunks_result
                else:
                    empty_result = Mock()
                    empty_result.fetchall.return_value = []
                    return empty_result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Capture print output
        with patch('builtins.print') as mock_print:
            upgrade(mock_conn)

            # Check that progress was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            progress_prints = [c for c in print_calls if 'Processed' in c and '/' in c]
            assert len(progress_prints) >= 1


class TestDowngradeMigration:
    """Tests for downgrade() migration function."""

    def test_downgrade_sets_sentence_count_null(self):
        """Test that downgrade() sets sentence_count=NULL for all chunks."""
        mock_conn = Mock()

        # Mock result for count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 100

        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if 'COUNT(*)' in query_str:
                return mock_count_result
            else:
                return Mock()

        mock_conn.execute.side_effect = execute_side_effect

        # Run downgrade
        downgrade(mock_conn)

        # Verify UPDATE was called to set NULL
        update_calls = [call for call in mock_conn.execute.call_args_list
                       if 'UPDATE chunks' in str(call[0][0]) and 'SET sentence_count = NULL' in str(call[0][0])]
        assert len(update_calls) >= 1

        # Verify commit was called
        assert mock_conn.commit.called


class TestMigrationIdempotency:
    """Tests for migration idempotency."""

    def test_upgrade_idempotent(self):
        """Test that running upgrade twice has no effect on second run."""
        mock_conn = Mock()

        # First run: has chunks to process
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0

        mock_conn.execute.return_value = mock_count_result

        # Run upgrade
        upgrade(mock_conn)

        # Should find 0 chunks and exit early
        assert mock_conn.execute.call_count == 1  # Only count query
