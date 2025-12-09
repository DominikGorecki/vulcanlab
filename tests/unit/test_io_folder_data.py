"""
Unit tests for IO folder data module.

Tests folder scanning logic, file format detection, database synchronization,
file comparison logic, and edge cases.

Usage:
    pytest tests/unit/test_io_folder_data.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone

from vulcanlab.config.io_folder_data import (
    INPUT_FORMATS,
    OUTPUT_FORMATS,
    ProcessedFile,
    IOFolderData,
    IOFileObject,
    sync_files_with_database,
    get_io_files_by_type,
    get_processed_files_from_works,
    get_io_folder_data,
    get_io_folder_objects,
)


class TestConstants:
    """Tests for module constants."""

    def test_input_formats(self):
        """Test INPUT_FORMATS constant."""
        assert isinstance(INPUT_FORMATS, list)
        assert ".pdf" in INPUT_FORMATS
        assert ".epub" in INPUT_FORMATS

    def test_output_formats(self):
        """Test OUTPUT_FORMATS constant."""
        assert isinstance(OUTPUT_FORMATS, list)
        assert ".md" in OUTPUT_FORMATS
        assert ".pdf" in OUTPUT_FORMATS
        assert ".epub" in OUTPUT_FORMATS
        assert ".csv" in OUTPUT_FORMATS


class TestProcessedFile:
    """Tests for ProcessedFile dataclass."""

    def test_processed_file_creation(self):
        """Test creating ProcessedFile."""
        pf = ProcessedFile(
            base_name="test",
            io_file_id=1,
            variants=[".pdf", ".md"]
        )
        assert pf.base_name == "test"
        assert pf.io_file_id == 1
        assert pf.variants == [".pdf", ".md"]

    def test_processed_file_no_id(self):
        """Test ProcessedFile with no io_file_id."""
        pf = ProcessedFile(
            base_name="test",
            io_file_id=None,
            variants=[".md"]
        )
        assert pf.io_file_id is None

    def test_processed_file_empty_variants(self):
        """Test ProcessedFile with empty variants."""
        pf = ProcessedFile(
            base_name="test",
            io_file_id=1,
            variants=[]
        )
        assert pf.variants == []


class TestIOFolderData:
    """Tests for IOFolderData dataclass."""

    def test_io_folder_data_creation(self):
        """Test creating IOFolderData."""
        data = IOFolderData(
            input_files=["file1.pdf", "file2.epub"],
            processed_files=[
                ProcessedFile(base_name="test", io_file_id=1, variants=[".pdf", ".md"])
            ]
        )
        assert len(data.input_files) == 2
        assert len(data.processed_files) == 1

    def test_io_folder_data_empty(self):
        """Test IOFolderData with empty lists."""
        data = IOFolderData(input_files=[], processed_files=[])
        assert data.input_files == []
        assert data.processed_files == []


class TestIOFileObject:
    """Tests for IOFileObject dataclass."""

    def test_io_file_object_creation(self):
        """Test creating IOFileObject."""
        obj = IOFileObject(
            id=1,
            filename="test.pdf",
            file_type="input",
            file_path="/path/to/test.pdf"
        )
        assert obj.id == 1
        assert obj.filename == "test.pdf"
        assert obj.file_type == "input"
        assert obj.file_path == "/path/to/test.pdf"

    def test_io_file_object_with_variants(self):
        """Test IOFileObject with base_name and variants."""
        obj = IOFileObject(
            id=1,
            filename="test.pdf",
            file_type="to_convert",
            file_path="/path/to/test.pdf",
            base_name="test",
            variants=[".pdf", ".md"]
        )
        assert obj.base_name == "test"
        assert obj.variants == [".pdf", ".md"]

    def test_io_file_object_optional_fields(self):
        """Test IOFileObject with optional fields as None."""
        obj = IOFileObject(
            id=1,
            filename="test.pdf",
            file_type="input",
            file_path="/path/to/test.pdf",
            base_name=None,
            variants=None
        )
        assert obj.base_name is None
        assert obj.variants is None


class TestSyncFilesWithDatabase:
    """Tests for sync_files_with_database() function."""

    @patch('vulcanlab.config.io_folder_data.load_config')
    @patch('vulcanlab.data.database.get_session')
    def test_sync_files_adds_new_files(self, mock_get_session, mock_load_config):
        """Test that new files are added to database."""
        # Setup config
        mock_config = MagicMock()
        mock_config.paths.input_dir = "/test/input"
        mock_config.paths.output_dir = "/test/output"
        mock_load_config.return_value = mock_config
        
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []  # No existing files
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            
            # Create test files
            (input_dir / "test.pdf").write_text("PDF content", encoding='utf-8')
            (output_dir / "test.md").write_text("MD content", encoding='utf-8')
            
            mock_config.paths.input_dir = str(input_dir)
            mock_config.paths.output_dir = str(output_dir)
            
            sync_files_with_database()
            
            # Should add 2 files (1 input + 1 output)
            assert mock_session.add.call_count == 2
            mock_session.commit.assert_called_once()

    @patch('vulcanlab.config.io_folder_data.load_config')
    @patch('vulcanlab.data.database.get_session')
    def test_sync_files_updates_existing_files(self, mock_get_session, mock_load_config):
        """Test that existing files have last_seen_at updated."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        # Setup config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        with TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            input_dir.mkdir()
            
            # Create file that matches existing
            test_file = input_dir / "existing.pdf"
            test_file.write_text("PDF content", encoding='utf-8')
            
            # Create existing file in database with actual absolute path
            existing_file = MagicMock(spec=IOFile)
            existing_file.file_path = str(test_file.absolute())  # Use actual absolute path
            existing_file.filename = "existing.pdf"
            existing_file.file_type = FileType.INPUT
            
            # Setup session
            mock_session = MagicMock()
            mock_session.query.return_value.all.return_value = [existing_file]
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            mock_config.paths.input_dir = str(input_dir)
            mock_config.paths.output_dir = str(Path(tmpdir) / "output")
            
            sync_files_with_database()
            
            # Should update last_seen_at, not add new file
            assert mock_session.add.call_count == 0
            assert existing_file.last_seen_at is not None
            mock_session.commit.assert_called_once()

    @patch('vulcanlab.config.io_folder_data.load_config')
    @patch('vulcanlab.data.database.get_session')
    def test_sync_files_removes_missing_files(self, mock_get_session, mock_load_config):
        """Test that files no longer on filesystem are removed from database."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        # Setup config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Create file in database that doesn't exist on filesystem
        missing_file = MagicMock(spec=IOFile)
        missing_file.file_path = "/test/input/missing.pdf"
        missing_file.filename = "missing.pdf"
        missing_file.file_type = FileType.INPUT
        
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [missing_file]
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            input_dir.mkdir()
            # Don't create missing.pdf file
            
            mock_config.paths.input_dir = str(input_dir)
            mock_config.paths.output_dir = str(Path(tmpdir) / "output")
            
            sync_files_with_database()
            
            # Should delete missing file
            mock_session.delete.assert_called_once_with(missing_file)
            mock_session.commit.assert_called_once()

    @patch('vulcanlab.config.io_folder_data.load_config')
    @patch('vulcanlab.data.database.get_session')
    def test_sync_files_empty_directories(self, mock_get_session, mock_load_config):
        """Test syncing with empty directories."""
        # Setup config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        with TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            # Don't create any files
            
            mock_config.paths.input_dir = str(input_dir)
            mock_config.paths.output_dir = str(output_dir)
            
            sync_files_with_database()
            
            # Should not add or delete anything
            mock_session.add.assert_not_called()
            mock_session.delete.assert_not_called()
            mock_session.commit.assert_called_once()

    @patch('vulcanlab.config.io_folder_data.load_config')
    @patch('vulcanlab.data.database.get_session')
    def test_sync_files_nonexistent_directories(self, mock_get_session, mock_load_config):
        """Test syncing when directories don't exist."""
        # Setup config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Setup session
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Use non-existent directories
        mock_config.paths.input_dir = "/nonexistent/input"
        mock_config.paths.output_dir = "/nonexistent/output"
        
        sync_files_with_database()
        
        # Should not add anything
        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()


class TestGetIOFilesByType:
    """Tests for get_io_files_by_type() function."""

    @patch('vulcanlab.data.database.get_session')
    def test_get_io_files_by_type_input(self, mock_get_session):
        """Test getting input files by type."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_file1 = MagicMock(spec=IOFile)
        mock_file1.id = 1
        mock_file1.filename = "test1.pdf"
        mock_file1.file_type = FileType.INPUT
        
        mock_file2 = MagicMock(spec=IOFile)
        mock_file2.id = 2
        mock_file2.filename = "test2.epub"
        mock_file2.file_type = FileType.INPUT
        
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_file1, mock_file2]
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = get_io_files_by_type(FileType.INPUT)
        
        assert len(result) == 2
        assert result[0].filename == "test1.pdf"
        assert result[1].filename == "test2.epub"

    @patch('vulcanlab.data.database.get_session')
    def test_get_io_files_by_type_empty(self, mock_get_session):
        """Test getting files when none exist."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        from vulcanlab.data.models.io_file import FileType
        result = get_io_files_by_type(FileType.TO_CONVERT)
        
        assert result == []


class TestGetProcessedFilesFromWorks:
    """Tests for get_processed_files_from_works() function."""

    @patch('vulcanlab.data.database.get_session')
    def test_get_processed_files_from_works_success(self, mock_get_session):
        """Test getting processed files from works table."""
        from vulcanlab.data.models.work import Work
        
        mock_work1 = MagicMock(spec=Work)
        mock_work1.files = {
            "original_file": {
                "path": "/path/to/file1.pdf"
            }
        }
        
        mock_work2 = MagicMock(spec=Work)
        mock_work2.files = {
            "original_file": {
                "path": "/path/to/file2.epub"
            }
        }
        
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_work1, mock_work2]
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = get_processed_files_from_works()
        
        assert "file1.pdf" in result
        assert "file2.epub" in result
        assert len(result) == 2

    @patch('vulcanlab.data.database.get_session')
    def test_get_processed_files_from_works_no_files(self, mock_get_session):
        """Test getting processed files when works have no files."""
        from vulcanlab.data.models.work import Work
        
        mock_work = MagicMock(spec=Work)
        mock_work.files = {}
        
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_work]
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = get_processed_files_from_works()
        
        assert result == set()

    @patch('vulcanlab.data.database.get_session')
    def test_get_processed_files_from_works_empty(self, mock_get_session):
        """Test getting processed files when no works exist."""
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = []
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = get_processed_files_from_works()
        
        assert result == set()


class TestGetIOFolderData:
    """Tests for get_io_folder_data() function."""

    @patch('vulcanlab.config.io_folder_data.get_processed_files_from_works')
    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_data_success(
        self, mock_sync, mock_get_by_type, mock_get_processed
    ):
        """Test successful retrieval of IO folder data."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        # Mock sync
        mock_sync.return_value = None
        
        # Mock input files
        mock_input_file = MagicMock(spec=IOFile)
        mock_input_file.filename = "unprocessed.pdf"
        mock_input_file.id = 1
        
        # Mock to_convert files
        mock_output_file1 = MagicMock(spec=IOFile)
        mock_output_file1.filename = "test.pdf"
        mock_output_file1.id = 2
        
        mock_output_file2 = MagicMock(spec=IOFile)
        mock_output_file2.filename = "test.md"
        mock_output_file2.id = 3
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.INPUT:
                return [mock_input_file]
            elif file_type == FileType.TO_CONVERT:
                return [mock_output_file1, mock_output_file2]
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        mock_get_processed.return_value = set()  # No processed files
        
        result = get_io_folder_data()
        
        assert isinstance(result, IOFolderData)
        assert len(result.input_files) == 1
        assert result.input_files[0] == "unprocessed.pdf"
        assert len(result.processed_files) == 1
        assert result.processed_files[0].base_name == "test"
        assert ".pdf" in result.processed_files[0].variants
        assert ".md" in result.processed_files[0].variants

    @patch('vulcanlab.config.io_folder_data.get_processed_files_from_works')
    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_data_filters_processed(
        self, mock_sync, mock_get_by_type, mock_get_processed
    ):
        """Test that processed files are filtered out."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_input_file = MagicMock(spec=IOFile)
        mock_input_file.filename = "processed.pdf"
        mock_input_file.id = 1
        
        mock_get_by_type.return_value = [mock_input_file]
        # File is already processed
        mock_get_processed.return_value = {"processed.pdf"}
        
        result = get_io_folder_data()
        
        # Should filter out processed file
        assert len(result.input_files) == 0

    @patch('vulcanlab.config.io_folder_data.get_processed_files_from_works')
    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_data_filters_sanitized(
        self, mock_sync, mock_get_by_type, mock_get_processed
    ):
        """Test that sanitized files are filtered out."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_output_file = MagicMock(spec=IOFile)
        mock_output_file.filename = "test.sanitized.md"
        mock_output_file.id = 1
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.TO_CONVERT:
                return [mock_output_file]
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        mock_get_processed.return_value = set()
        
        result = get_io_folder_data()
        
        # Should filter out sanitized files
        assert len(result.processed_files) == 0

    @patch('vulcanlab.config.io_folder_data.get_processed_files_from_works')
    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_data_groups_variants(
        self, mock_sync, mock_get_by_type, mock_get_processed
    ):
        """Test that file variants are grouped correctly."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_file1 = MagicMock(spec=IOFile)
        mock_file1.filename = "book.pdf"
        mock_file1.id = 10
        
        mock_file2 = MagicMock(spec=IOFile)
        mock_file2.filename = "book.md"
        mock_file2.id = 11
        
        mock_file3 = MagicMock(spec=IOFile)
        mock_file3.filename = "book.style.md"
        mock_file3.id = 12
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.TO_CONVERT:
                return [mock_file1, mock_file2, mock_file3]
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        mock_get_processed.return_value = set()
        
        result = get_io_folder_data()
        
        # Should group all variants under "book"
        assert len(result.processed_files) == 1
        assert result.processed_files[0].base_name == "book"
        assert result.processed_files[0].io_file_id == 10  # PDF's ID
        assert ".pdf" in result.processed_files[0].variants
        assert ".md" in result.processed_files[0].variants
        assert ".style.md" in result.processed_files[0].variants


class TestGetIOFolderObjects:
    """Tests for get_io_folder_objects() function."""

    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_objects_success(
        self, mock_sync, mock_get_by_type
    ):
        """Test successful retrieval of IO folder objects."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_input_file = MagicMock(spec=IOFile)
        mock_input_file.id = 1
        mock_input_file.filename = "input.pdf"
        mock_input_file.file_type = FileType.INPUT
        mock_input_file.file_path = "/path/to/input.pdf"
        
        mock_output_file = MagicMock(spec=IOFile)
        mock_output_file.id = 2
        mock_output_file.filename = "output.md"
        mock_output_file.file_type = FileType.TO_CONVERT
        mock_output_file.file_path = "/path/to/output.md"
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.INPUT:
                return [mock_input_file]
            elif file_type == FileType.TO_CONVERT:
                return [mock_output_file]
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        
        result = get_io_folder_objects()
        
        assert len(result) == 2
        assert isinstance(result[0], IOFileObject)
        assert result[0].filename == "input.pdf"
        assert result[0].file_type == FileType.INPUT.value

    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_objects_groups_variants(
        self, mock_sync, mock_get_by_type
    ):
        """Test that variants are grouped into single objects."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_file1 = MagicMock(spec=IOFile)
        mock_file1.id = 10
        mock_file1.filename = "book.pdf"
        mock_file1.file_path = "/path/to/book.pdf"
        
        mock_file2 = MagicMock(spec=IOFile)
        mock_file2.id = 11
        mock_file2.filename = "book.md"
        mock_file2.file_path = "/path/to/book.md"
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.TO_CONVERT:
                return [mock_file1, mock_file2]
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        
        result = get_io_folder_objects()
        
        # Should create one object for the group
        assert len(result) == 1
        assert result[0].base_name == "book"
        assert result[0].id == 10  # PDF's ID
        assert result[0].variants == [".md", ".pdf"]  # Sorted
        assert result[0].filename == "book.pdf"  # Uses PDF filename

    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_objects_empty(self, mock_sync, mock_get_by_type):
        """Test getting objects when no files exist."""
        mock_sync.return_value = None
        mock_get_by_type.return_value = []
        
        result = get_io_folder_objects()
        
        assert result == []

    @patch('vulcanlab.config.io_folder_data.get_io_files_by_type')
    @patch('vulcanlab.config.io_folder_data.sync_files_with_database')
    def test_get_io_folder_objects_pdf_epub_both(
        self, mock_sync, mock_get_by_type
    ):
        """Test behavior when both PDF and EPUB exist."""
        from vulcanlab.data.models.io_file import IOFile, FileType
        
        mock_sync.return_value = None
        
        mock_pdf = MagicMock(spec=IOFile)
        mock_pdf.id = 10
        mock_pdf.filename = "book.pdf"
        mock_pdf.file_path = "/path/to/book.pdf"
        
        mock_epub = MagicMock(spec=IOFile)
        mock_epub.id = 20
        mock_epub.filename = "book.epub"
        mock_epub.file_path = "/path/to/book.epub"
        
        def get_by_type_side_effect(file_type):
            if file_type == FileType.TO_CONVERT:
                return [mock_pdf, mock_epub]  # PDF comes first, EPUB last
            return []
        
        mock_get_by_type.side_effect = get_by_type_side_effect
        
        result = get_io_folder_objects()
        
        # Should use EPUB's ID (last PDF/EPUB encountered) but PDF filename (preferred)
        assert len(result) == 1
        assert result[0].id == 20  # EPUB's ID (last PDF/EPUB processed)
        assert result[0].filename == "book.pdf"  # PDF filename is preferred
        assert ".pdf" in result[0].variants
        assert ".epub" in result[0].variants

