import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlalchemy import text
import pytest

# Import migration module dynamically since filename starts with number
migration_path = Path(__file__).parent.parent.parent.parent / "migrations" / "033_add_dense_lexical_use.py"
spec = importlib.util.spec_from_file_location("migration_033", migration_path)
migration_033 = importlib.util.module_from_spec(spec)
sys.modules["migration_033"] = migration_033
spec.loader.exec_module(migration_033)

backfill_dense_lexical_use = migration_033.backfill_dense_lexical_use

class TestMigration033:
    """Test data backfill for dense_lexical_use."""

    @patch('migration_033.engine')
    def test_backfill_dense_lexical_use(self, mock_engine):
        """Test that backfill query is executed correctly."""
        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_connection
        
        mock_result = MagicMock()
        mock_result.rowcount = 50
        mock_connection.execute.return_value = mock_result

        backfill_dense_lexical_use()

        # Verify SQL execution
        mock_connection.execute.assert_called()
        call_args = mock_connection.execute.call_args[0][0]
        sql_text = str(call_args)
        
        assert "UPDATE chunks" in sql_text
        assert "SET dense_lexical_use = TRUE" in sql_text
        assert "WHERE level LIKE '%chunk%'" in sql_text

    @patch('migration_033.engine')
    def test_backfill_handles_missing_column_error(self, mock_engine):
        """Test that helpful tip is logged if column is missing."""
        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_connection
        
        # Simulate missing column error
        mock_connection.execute.side_effect = Exception('column "dense_lexical_use" does not exist')

        with patch('migration_033.logger') as mock_logger:
            with pytest.raises(SystemExit):
                backfill_dense_lexical_use()
            
            # Check that TIP was logged
            mock_logger.error.assert_any_call("TIP: Run 'python -m vulcanlab.data.init_db -v' first to apply schema changes.")
