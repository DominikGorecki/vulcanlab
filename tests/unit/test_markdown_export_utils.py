"""
Unit tests for markdown export utilities.

Tests get_exports_dir() and is_safe_path() functions.

Usage:
    pytest tests/unit/test_markdown_export_utils.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from tempfile import TemporaryDirectory

from vulcanlab.markdown_export import get_exports_dir, is_safe_path
from vulcanlab.config import AppConfig, PathsConfig


class TestGetExportsDir:
    """Tests for get_exports_dir() function."""

    def test_get_exports_dir_returns_correct_path(self):
        """Test get_exports_dir returns correct path from config."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.output_dir = "/test/output"

        with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
            with patch.object(Path, 'mkdir') as mock_mkdir:
                result = get_exports_dir()

                assert result == Path("/test/output/exports")
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_exports_dir_creates_directory(self):
        """Test get_exports_dir creates directory if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.output_dir = tmpdir

            with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
                result = get_exports_dir()

                # Verify directory was created
                assert result.exists()
                assert result.is_dir()
                assert result.name == "exports"
                assert result.parent == Path(tmpdir)

    def test_get_exports_dir_with_existing_directory(self):
        """Test get_exports_dir when directory already exists."""
        with TemporaryDirectory() as tmpdir:
            # Create exports directory first
            exports_path = Path(tmpdir) / "exports"
            exports_path.mkdir()

            mock_config = Mock(spec=AppConfig)
            mock_config.paths = Mock(spec=PathsConfig)
            mock_config.paths.output_dir = tmpdir

            with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
                result = get_exports_dir()

                # Should return existing directory without error
                assert result.exists()
                assert result == exports_path

    def test_get_exports_dir_raises_on_empty_output_dir(self):
        """Test get_exports_dir raises ValueError when output_dir is empty."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.output_dir = ""

        with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
            with pytest.raises(ValueError, match="output_dir not configured"):
                get_exports_dir()

    def test_get_exports_dir_raises_on_none_output_dir(self):
        """Test get_exports_dir raises ValueError when output_dir is None."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.output_dir = None

        with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
            with pytest.raises(ValueError, match="output_dir not configured"):
                get_exports_dir()

    def test_get_exports_dir_propagates_mkdir_errors(self):
        """Test get_exports_dir propagates errors from mkdir."""
        mock_config = Mock(spec=AppConfig)
        mock_config.paths = Mock(spec=PathsConfig)
        mock_config.paths.output_dir = "/test/output"

        with patch('vulcanlab.markdown_export.load_config', return_value=mock_config):
            with patch.object(Path, 'mkdir', side_effect=PermissionError("Access denied")):
                with pytest.raises(PermissionError, match="Access denied"):
                    get_exports_dir()


class TestIsSafePath:
    """Tests for is_safe_path() function."""

    def test_is_safe_path_accepts_valid_relative_path(self):
        """Test is_safe_path accepts valid path within base directory."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            safe_path = base_dir / "subdir" / "file.txt"

            result = is_safe_path(safe_path, base_dir)

            assert result is True

    def test_is_safe_path_accepts_path_equal_to_base(self):
        """Test is_safe_path accepts path equal to base directory."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            result = is_safe_path(base_dir, base_dir)

            assert result is True

    def test_is_safe_path_rejects_directory_traversal(self):
        """Test is_safe_path rejects directory traversal attempts."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            unsafe_path = base_dir / ".." / ".." / "etc" / "passwd"

            result = is_safe_path(unsafe_path, base_dir)

            assert result is False

    def test_is_safe_path_rejects_absolute_path_outside_base(self):
        """Test is_safe_path rejects absolute paths outside base directory."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            unsafe_path = Path("/etc/passwd")

            result = is_safe_path(unsafe_path, base_dir)

            assert result is False

    def test_is_safe_path_rejects_multiple_traversal_attempts(self):
        """Test is_safe_path rejects multiple .. traversal attempts."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            # Try to escape with multiple ..
            unsafe_path = base_dir / "subdir" / ".." / ".." / ".." / "etc" / "passwd"

            result = is_safe_path(unsafe_path, base_dir)

            assert result is False

    def test_is_safe_path_with_symlinks(self):
        """Test is_safe_path with symlinks (if supported by OS)."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            target_dir = base_dir / "target"
            target_dir.mkdir()

            # Create symlink inside base directory
            link_path = base_dir / "link"
            try:
                link_path.symlink_to(target_dir)

                # Symlink within base directory should be safe
                result = is_safe_path(link_path, base_dir)
                assert result is True
            except OSError:
                # Skip test if symlinks not supported (e.g., Windows without admin)
                pytest.skip("Symlinks not supported on this system")

    def test_is_safe_path_with_symlink_outside_base(self):
        """Test is_safe_path rejects symlinks pointing outside base."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "base"
            base_dir.mkdir()

            outside_dir = Path(tmpdir) / "outside"
            outside_dir.mkdir()

            # Create symlink inside base pointing outside
            link_path = base_dir / "link"
            try:
                link_path.symlink_to(outside_dir)

                # Symlink pointing outside should be rejected
                result = is_safe_path(link_path, base_dir)
                assert result is False
            except OSError:
                # Skip test if symlinks not supported
                pytest.skip("Symlinks not supported on this system")

    def test_is_safe_path_handles_nonexistent_paths(self):
        """Test is_safe_path handles nonexistent paths correctly."""
        with TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            # Path doesn't exist but would be within base
            nonexistent_path = base_dir / "nonexistent" / "file.txt"

            result = is_safe_path(nonexistent_path, base_dir)

            # Should accept nonexistent paths that would be within base
            assert result is True

    def test_is_safe_path_handles_oserror(self):
        """Test is_safe_path handles OSError gracefully."""
        base_dir = Path("/test/base")
        test_path = Path("/test/base/file.txt")

        with patch.object(Path, 'resolve', side_effect=OSError("Filesystem error")):
            result = is_safe_path(test_path, base_dir)

            assert result is False

    def test_is_safe_path_handles_runtime_error(self):
        """Test is_safe_path handles RuntimeError (e.g., symlink loop)."""
        base_dir = Path("/test/base")
        test_path = Path("/test/base/file.txt")

        with patch.object(Path, 'resolve', side_effect=RuntimeError("Symlink loop")):
            result = is_safe_path(test_path, base_dir)

            assert result is False
