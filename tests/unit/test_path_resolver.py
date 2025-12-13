"""
Unit tests for PathResolver utility.
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from vulcanlab.utils.file_utils import PathResolver, get_path_resolver
from vulcanlab.utils.exceptions import InvalidFilePathError
from vulcanlab.data.models.work import Work


class TestPathResolver:
    """Tests for the PathResolver class."""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary config file for testing."""
        config_path = tmp_path / "test_config.json"
        config_data = {
            "paths": {
                "input_dir": str(tmp_path / "input"),
                "output_dir": str(tmp_path / "output")
            }
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        # Create directories
        (tmp_path / "input").mkdir()
        (tmp_path / "output").mkdir()

        return config_path

    @pytest.fixture
    def resolver(self, temp_config):
        """Create a PathResolver instance with test config."""
        return PathResolver(temp_config)

    @pytest.fixture
    def mock_work(self):
        """Create a mock Work instance for testing."""
        work = Mock(spec=Work)
        work.id = 1
        work.markdown_path = "test.md"
        work.files = {
            "sanitized": {"path": "test.sanitized.md", "hash": "abc123"},
            "original_file": {"path": "test.pdf", "hash": "def456"}
        }
        return work

    def test_path_resolver_loads_config(self, temp_config, tmp_path):
        """Test PathResolver loads config and caches input_dir and output_dir correctly."""
        resolver = PathResolver(temp_config)

        assert resolver.input_dir == tmp_path / "input"
        assert resolver.output_dir == tmp_path / "output"
        assert isinstance(resolver.input_dir, Path)
        assert isinstance(resolver.output_dir, Path)

    def test_path_resolver_singleton(self, temp_config):
        """Test get_path_resolver returns same instance (singleton pattern)."""
        # Clear any existing instance
        import vulcanlab.utils.file_utils as file_utils_module
        file_utils_module._path_resolver_instance = None

        resolver1 = get_path_resolver(temp_config)
        resolver2 = get_path_resolver()

        assert resolver1 is resolver2

    def test_resolve_markdown_path_success(self, resolver, mock_work, tmp_path):
        """Test resolving markdown_path returns correct absolute path."""
        result = resolver.resolve_work_path(mock_work)

        expected = tmp_path / "output" / "test.md"
        assert result == expected
        assert isinstance(result, Path)

    def test_resolve_file_path_output_dir(self, resolver, mock_work, tmp_path):
        """Test resolving files['sanitized'] uses output_dir."""
        result = resolver.resolve_work_path(mock_work, "sanitized")

        expected = tmp_path / "output" / "test.sanitized.md"
        assert result == expected

    def test_resolve_file_path_input_dir(self, resolver, mock_work, tmp_path):
        """Test resolving files['original_file'] uses input_dir."""
        result = resolver.resolve_work_path(mock_work, "original_file")

        expected = tmp_path / "input" / "test.pdf"
        assert result == expected

    def test_resolve_markdown_path_null_raises_error(self, resolver, mock_work):
        """Test NULL markdown_path raises InvalidFilePathError."""
        mock_work.markdown_path = None

        with pytest.raises(InvalidFilePathError) as exc_info:
            resolver.resolve_work_path(mock_work)

        assert "markdown_path is NULL or empty" in str(exc_info.value)
        assert exc_info.value.work_id == 1
        assert exc_info.value.field_name == "markdown_path"

    def test_resolve_markdown_path_empty_raises_error(self, resolver, mock_work):
        """Test empty markdown_path raises InvalidFilePathError."""
        mock_work.markdown_path = ""

        with pytest.raises(InvalidFilePathError):
            resolver.resolve_work_path(mock_work)

    def test_resolve_file_path_missing_key_raises_error(self, resolver, mock_work):
        """Test resolving non-existent file key raises InvalidFilePathError."""
        with pytest.raises(InvalidFilePathError) as exc_info:
            resolver.resolve_work_path(mock_work, "nonexistent")

        assert "files['nonexistent'] does not exist" in str(exc_info.value)
        assert exc_info.value.work_id == 1
        assert exc_info.value.field_name == "files.nonexistent"

    def test_resolve_file_path_null_value_raises_error(self, resolver, mock_work):
        """Test NULL path value in files raises InvalidFilePathError."""
        mock_work.files["sanitized"]["path"] = None

        with pytest.raises(InvalidFilePathError) as exc_info:
            resolver.resolve_work_path(mock_work, "sanitized")

        assert "files['sanitized']['path'] is NULL or empty" in str(exc_info.value)

    def test_resolve_file_path_empty_value_raises_error(self, resolver, mock_work):
        """Test empty path value in files raises InvalidFilePathError."""
        mock_work.files["sanitized"]["path"] = ""

        with pytest.raises(InvalidFilePathError):
            resolver.resolve_work_path(mock_work, "sanitized")

    def test_path_resolver_config_not_found(self, tmp_path):
        """Test PathResolver raises FileNotFoundError for non-existent config."""
        non_existent = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            PathResolver(non_existent)

    def test_path_resolver_config_missing_paths(self, tmp_path):
        """Test PathResolver raises KeyError for config missing paths."""
        bad_config = tmp_path / "bad_config.json"
        with open(bad_config, 'w') as f:
            json.dump({"other": "data"}, f)

        with pytest.raises(KeyError):
            PathResolver(bad_config)

    def test_resolve_work_path_with_null_files(self, resolver, mock_work):
        """Test resolving when work.files is None raises error."""
        mock_work.files = None

        with pytest.raises(InvalidFilePathError):
            resolver.resolve_work_path(mock_work, "sanitized")

    def test_resolve_work_path_with_empty_files(self, resolver, mock_work):
        """Test resolving when work.files is empty dict raises error."""
        mock_work.files = {}

        with pytest.raises(InvalidFilePathError):
            resolver.resolve_work_path(mock_work, "sanitized")
