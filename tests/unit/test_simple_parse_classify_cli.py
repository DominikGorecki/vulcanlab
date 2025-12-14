"""Unit tests for parse & classify CLI tool."""

import pytest
from unittest.mock import patch, MagicMock
import sys

from vulcanlab.cli.simple_parse_classify import main


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123'])
def test_cli_success(mock_parse, capsys):
    """Test CLI with successful execution."""
    mock_parse.return_value = (15000, 'small')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Work ID:        123' in captured.out
    assert 'Token Count:    15,000' in captured.out
    assert 'Classification: small' in captured.out


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '456'])
def test_cli_large_document(mock_parse, capsys):
    """Test CLI with large document classification."""
    mock_parse.return_value = (25000, 'large')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert 'Classification: large' in captured.out


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '999'])
def test_cli_work_not_found(mock_parse, capsys):
    """Test CLI with non-existent work."""
    mock_parse.side_effect = ValueError("Work 999 not found")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123'])
def test_cli_unexpected_error(mock_parse, capsys):
    """Test CLI with unexpected error."""
    mock_parse.side_effect = Exception("Database connection failed")

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


@patch('sys.argv', ['simple_parse_classify.py'])
def test_cli_missing_work_id():
    """Test CLI without required --work-id argument."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # argparse exits with code 2 for missing required arguments
    assert exc_info.value.code == 2


@patch('vulcanlab.cli.simple_parse_classify.parse_and_classify_standalone')
@patch('sys.argv', ['simple_parse_classify.py', '--work-id', '123', '--verbose'])
def test_cli_verbose_mode(mock_parse):
    """Test CLI with verbose logging enabled."""
    mock_parse.return_value = (10000, 'small')

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    # Verbose mode sets log level to DEBUG (tested by no exceptions)
