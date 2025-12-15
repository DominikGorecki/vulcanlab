"""Unit tests for simple chunking CLI tool."""

import pytest
from unittest.mock import patch

from vulcanlab.cli.simple_chunk import main


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '123'])
def test_cli_success(mock_chunk, capsys):
    """Test CLI with successful execution."""
    mock_chunk.return_value = 8

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:        123' in captured.out
    assert 'Chunks Created: 8' in captured.out


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '999'])
def test_cli_work_not_found(mock_chunk):
    """Test CLI with non-existent work."""
    mock_chunk.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '123'])
def test_cli_no_headings(mock_chunk, capsys):
    """Test CLI when no headings found."""
    mock_chunk.return_value = 0

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Chunks Created: 0' in captured.out


@patch('sys.argv', ['simple_chunk.py'])
def test_cli_missing_work_id():
    """Test CLI without required --work-id argument."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # argparse exits with code 2 for missing required arguments
    assert exc_info.value.code == 2


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '123', '--verbose'])
def test_cli_verbose_mode(mock_chunk):
    """Test CLI with verbose logging enabled."""
    mock_chunk.return_value = 12

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    # Verbose mode sets log level to DEBUG (tested by no exceptions)


@patch('vulcanlab.cli.simple_chunk.create_chunks_standalone')
@patch('sys.argv', ['simple_chunk.py', '--work-id', '456'])
def test_cli_unexpected_error(mock_chunk):
    """Test CLI with unexpected error."""
    mock_chunk.side_effect = Exception("Database connection failed")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
