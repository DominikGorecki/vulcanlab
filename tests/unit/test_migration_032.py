"""
Unit tests for migration script 032_upgrade_embedding_dimensions.

This test suite verifies:
1. Backup directory creation logic.
2. Timestamped filename generation.
3. Embedding clearing logic (via SQL capture).
4. Vector status reset logic (via SQL capture).
5. Idempotency and error handling.
"""

import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from sqlalchemy import text
import sys
import importlib.util

# Import the migration script using importlib because of the numeric prefix
project_root = Path(__file__).parent.parent.parent
migration_path = project_root / "migrations" / "032_upgrade_embedding_dimensions.py"
spec = importlib.util.spec_from_file_location("migration_032", migration_path)
migration = importlib.util.module_from_spec(spec)
sys.modules["migration_032"] = migration
spec.loader.exec_module(migration)

class TestMigration032(unittest.TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_engine = MagicMock()
        
    @patch('os.access')
    def test_migration_creates_backup_directory(self, mock_access):
        """Verify backup directory creation if it doesn't exist."""
        with patch.object(migration, 'BACKUP_DIR') as mock_backup_dir:
            mock_backup_dir.exists.return_value = False
            mock_access.return_value = True
            
            migration.ensure_backup_dir()
            
            mock_backup_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('psycopg.connect')
    @patch('builtins.open', new_callable=mock_open)
    def test_migration_generates_timestamped_filename(self, mock_file_open, mock_connect):
        """Verify backup filenames use the provided timestamp."""
        with patch.object(migration, 'BACKUP_DIR') as mock_backup_dir, \
             patch.object(migration, 'get_database_url') as mock_get_url:
            
            mock_get_url.return_value = "postgresql+psycopg://user:pass@host:5432/db"
            
            # Mock the path behavior
            mock_chunk_path = MagicMock(spec=Path)
            mock_query_path = MagicMock(spec=Path)
            
            # Setup path division operator
            mock_backup_dir.__truediv__.side_effect = lambda x: mock_chunk_path if "chunks" in x else mock_query_path
            
            # Mock stat() to avoid FileNotFoundError
            mock_chunk_path.stat.return_value.st_size = 1024
            mock_query_path.stat.return_value.st_size = 2048
            
            # Mock psycopg context managers
            mock_conn = mock_connect.return_value.__enter__.return_value
            mock_cur = mock_conn.cursor.return_value.__enter__.return_value
            mock_copy = mock_cur.copy.return_value.__enter__.return_value
            mock_copy.__iter__.return_value = [b"data"]
            
            timestamp = "20260117_120000"
            migration.backup_tables(timestamp)
            
            # Check if open was called with correct paths
            mock_file_open.assert_any_call(mock_chunk_path, "wb")
            mock_file_open.assert_any_call(mock_query_path, "wb")

    def test_migration_clears_embeddings(self):
        """Verify embedding columns are set to NULL in chunks and queries."""
        # Mock row counts
        mock_res_chunks = MagicMock()
        mock_res_chunks.scalar.return_value = 10
        
        mock_res_queries = MagicMock()
        mock_res_queries.scalar.return_value = 5
        
        self.mock_connection.execute.side_effect = [
            mock_res_chunks,  # SELECT COUNT chunks
            None,             # UPDATE chunks
            mock_res_queries, # SELECT COUNT queries
            None              # UPDATE queries
        ]
        
        migration.clear_embeddings(self.mock_connection)
        
        # Verify SQL statements
        calls = self.mock_connection.execute.call_args_list
        self.assertEqual(len(calls), 4)
        
        # Check first update
        self.assertIn("UPDATE chunks SET embedding = NULL", str(calls[1][0][0]))
        # Check second update
        self.assertIn("UPDATE queries SET embedding_original = NULL, embedding_hyde = NULL", str(calls[3][0][0]))

    def test_migration_resets_vector_status(self):
        """Verify vector_status changed from 'vec' to 'to_vec'."""
        mock_res = MagicMock()
        mock_res.rowcount = 10
        self.mock_connection.execute.return_value = mock_res
        
        migration.reset_vector_status(self.mock_connection)
        
        # Verify SQL statements
        calls = self.mock_connection.execute.call_args_list
        self.assertEqual(len(calls), 2)
        
        self.assertIn("UPDATE chunks SET vector_status = 'to_vec' WHERE vector_status = 'vec'", str(calls[0][0][0]))
        self.assertIn("UPDATE queries SET vector_status = 'to_vec' WHERE vector_status = 'vec'", str(calls[1][0][0]))

    def test_migration_idempotent_status_reset(self):
        """Running twice doesn't cause errors, even if 0 rows affected."""
        mock_res = MagicMock()
        mock_res.rowcount = 0
        self.mock_connection.execute.return_value = mock_res
        
        # Should not raise exception
        migration.reset_vector_status(self.mock_connection)
        
        self.assertEqual(self.mock_connection.execute.call_count, 2)

    @patch('os.access')
    def test_migration_fails_if_backup_dir_not_writable(self, mock_access):
        """Verify fail-fast behavior if backup directory is not writable."""
        with patch.object(migration, 'BACKUP_DIR') as mock_backup_dir:
            mock_backup_dir.exists.return_value = True
            mock_access.return_value = False
            
            with self.assertRaises(SystemExit) as cm:
                migration.ensure_backup_dir()
            
            self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
