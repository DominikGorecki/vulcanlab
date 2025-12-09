"""
Unit tests for conversion inspection module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vulcanlab.conversions.inspection import (
    InspectionItem,
    get_conversion_inspection,
)


class TestInspectionItem:
    """Tests for InspectionItem dataclass."""

    def test_inspection_item_creation(self):
        """Test creating an InspectionItem."""
        item = InspectionItem(
            name="inspect_style_hier",
            available=True,
            files_checked=["test.style.md", "test.hier.md"]
        )
        
        assert item.name == "inspect_style_hier"
        assert item.available is True
        assert item.files_checked == ["test.style.md", "test.hier.md"]


class TestGetConversionInspection:
    """Tests for get_conversion_inspection function."""

    @patch("vulcanlab.conversions.inspection.get_session")
    @patch("vulcanlab.conversions.inspection.load_config")
    def test_all_files_present(self, mock_load_config, mock_get_session):
        """Test inspection when all files are present."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config
        
        # Mock file existence
        with patch("vulcanlab.conversions.inspection.Path") as mock_path_class:
            def mock_path_constructor(path_str):
                mock_path = MagicMock(spec=Path)
                # All files exist
                mock_path.exists.return_value = True
                mock_path.is_file.return_value = True
                return mock_path
            
            mock_path_class.side_effect = mock_path_constructor
            
            # Mock Path division operator
            mock_output_dir = MagicMock(spec=Path)
            mock_output_dir.__truediv__ = lambda self, other: mock_path_constructor(str(other))
            
            with patch.object(Path, "__new__", return_value=mock_output_dir):
                result = get_conversion_inspection(1)
        
        # Verify results
        assert len(result) == 5
        assert all(isinstance(item, InspectionItem) for item in result)
        
        # Check order and names
        assert result[0].name == "inspect_style_hier"
        assert result[1].name == "inspect_toc_titles"
        assert result[2].name == "inspect_titles"
        assert result[3].name == "inspect_title_changes"
        assert result[4].name == "inspect_original_md"
        
        # All should be available
        assert all(item.available for item in result)

    @patch("vulcanlab.conversions.inspection.get_session")
    @patch("vulcanlab.conversions.inspection.load_config")
    def test_no_files_present(self, mock_load_config, mock_get_session):
        """Test inspection when no files are present."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config
        
        # Mock file existence - no files exist
        # Use a descriptor-based approach to properly mock instance methods
        existing_files = set()  # No files exist
        
        class MockExistsDescriptor:
            """Descriptor that properly handles Path.exists() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_exists():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_exists
        
        class MockIsFileDescriptor:
            """Descriptor that properly handles Path.is_file() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_is_file():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_is_file
        
        with patch("vulcanlab.conversions.inspection.Path.exists", MockExistsDescriptor(existing_files)):
            with patch("vulcanlab.conversions.inspection.Path.is_file", MockIsFileDescriptor(existing_files)):
                result = get_conversion_inspection(1)
        
        # Verify results
        assert len(result) == 5
        
        # None should be available
        assert all(not item.available for item in result)

    @patch("vulcanlab.conversions.inspection.get_session")
    @patch("vulcanlab.conversions.inspection.load_config")
    def test_some_files_present(self, mock_load_config, mock_get_session):
        """Test inspection when only some files are present."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config
        
        # Mock file existence - only style.md, hier.md, and toc_titles.md exist
        existing_files = {
            "test.style.md",
            "test.hier.md",
            "test.toc_titles.md"
        }
        
        class MockExistsDescriptor:
            """Descriptor that properly handles Path.exists() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_exists():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_exists
        
        class MockIsFileDescriptor:
            """Descriptor that properly handles Path.is_file() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_is_file():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_is_file
        
        with patch("vulcanlab.conversions.inspection.Path.exists", MockExistsDescriptor(existing_files)):
            with patch("vulcanlab.conversions.inspection.Path.is_file", MockIsFileDescriptor(existing_files)):
                result = get_conversion_inspection(1)
        
        # Verify results
        assert len(result) == 5
        
        # Check specific availability
        assert result[0].name == "inspect_style_hier"
        assert result[0].available is True  # Both style.md and hier.md exist
        
        assert result[1].name == "inspect_toc_titles"
        assert result[1].available is True  # toc_titles.md exists
        
        assert result[2].name == "inspect_titles"
        assert result[2].available is False  # titles.md doesn't exist
        
        assert result[3].name == "inspect_title_changes"
        assert result[3].available is False  # title_changes.md doesn't exist
        
        assert result[4].name == "inspect_original_md"
        assert result[4].available is False  # .md doesn't exist

    @patch("vulcanlab.conversions.inspection.get_session")
    def test_file_not_found(self, mock_get_session):
        """Test that ValueError is raised when file ID doesn't exist."""
        # Mock database session to return None
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with pytest.raises(ValueError, match="File with ID 999 not found"):
            get_conversion_inspection(999)

    @patch("vulcanlab.conversions.inspection.get_session")
    def test_invalid_filename_format(self, mock_get_session):
        """Test that ValueError is raised for filename without extension."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test_without_extension"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with pytest.raises(ValueError, match="Invalid filename format"):
            get_conversion_inspection(1)

    @patch("vulcanlab.conversions.inspection.get_session")
    @patch("vulcanlab.conversions.inspection.load_config")
    def test_style_hier_requires_both_files(self, mock_load_config, mock_get_session):
        """Test that style_hier inspection requires both style.md and hier.md."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config
        
        # Mock file existence - only style.md exists, not hier.md
        existing_files = {"test.style.md"}
        
        class MockExistsDescriptor:
            """Descriptor that properly handles Path.exists() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_exists():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_exists
        
        class MockIsFileDescriptor:
            """Descriptor that properly handles Path.is_file() instance method calls."""
            def __init__(self, existing_files_set):
                self.existing_files = existing_files_set
            
            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Return a bound method that checks the filename
                def bound_is_file():
                    filename = obj.name if hasattr(obj, 'name') else str(obj).split('/')[-1]
                    return filename in self.existing_files
                return bound_is_file
        
        with patch("vulcanlab.conversions.inspection.Path.exists", MockExistsDescriptor(existing_files)):
            with patch("vulcanlab.conversions.inspection.Path.is_file", MockIsFileDescriptor(existing_files)):
                result = get_conversion_inspection(1)
        
        # Verify that style_hier is NOT available (requires both files)
        style_hier_item = next(item for item in result if item.name == "inspect_style_hier")
        assert style_hier_item.available is False
        assert len(style_hier_item.files_checked) == 2

    @patch("vulcanlab.conversions.inspection.get_session")
    @patch("vulcanlab.conversions.inspection.load_config")
    def test_files_checked_list(self, mock_load_config, mock_get_session):
        """Test that files_checked list is correctly populated."""
        # Mock database session
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "myfile.pdf"
        
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_io_file
        
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config
        
        # Mock file existence
        with patch("vulcanlab.conversions.inspection.Path") as mock_path_class:
            def mock_path_constructor(path_str):
                mock_path = MagicMock(spec=Path)
                mock_path.exists.return_value = False
                mock_path.is_file.return_value = False
                return mock_path
            
            mock_path_class.side_effect = mock_path_constructor
            
            # Mock Path division operator
            mock_output_dir = MagicMock(spec=Path)
            mock_output_dir.__truediv__ = lambda self, other: mock_path_constructor(str(other))
            
            with patch.object(Path, "__new__", return_value=mock_output_dir):
                result = get_conversion_inspection(1)
        
        # Verify files_checked lists
        assert result[0].files_checked == ["myfile.style.md", "myfile.hier.md"]
        assert result[1].files_checked == ["myfile.toc_titles.md"]
        assert result[2].files_checked == ["myfile.titles.md"]
        assert result[3].files_checked == ["myfile.title_changes.md"]
        assert result[4].files_checked == ["myfile.md"]

