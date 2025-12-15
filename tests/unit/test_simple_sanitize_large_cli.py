"""Unit tests for large sanitization CLI tool."""

import pytest
from unittest.mock import patch

from vulcanlab.cli.simple_sanitize_large import main


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '123'])
def test_cli_success(mock_sanitize, capsys):
    """Test CLI with successful execution."""
    mock_sanitize.return_value = (15, 3500)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:               123' in captured.out
    assert 'Headings Analyzed:     15' in captured.out
    assert 'Condensed Size:        3,500 chars' in captured.out


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '999'])
def test_cli_work_not_found(mock_sanitize):
    """Test CLI with non-existent work."""
    mock_sanitize.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '123'])
def test_cli_unexpected_error(mock_sanitize):
    """Test CLI with unexpected error."""
    mock_sanitize.side_effect = Exception("LLM timeout")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


@patch('sys.argv', ['simple_sanitize_large.py'])
def test_cli_missing_work_id():
    """Test CLI without required --work-id argument."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # argparse exits with code 2 for missing required arguments
    assert exc_info.value.code == 2


@patch('vulcanlab.cli.simple_sanitize_large.sanitize_large_document_standalone')
@patch('sys.argv', ['simple_sanitize_large.py', '--work-id', '123', '--verbose'])
def test_cli_verbose_mode(mock_sanitize):
    """Test CLI with verbose logging enabled."""
    mock_sanitize.return_value = (20, 5000)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    # Verbose mode sets log level to DEBUG (tested by no exceptions)
