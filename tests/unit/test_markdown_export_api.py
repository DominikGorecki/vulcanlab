"""
Unit tests for markdown export/import API endpoints.

Tests:
    - POST /api/v1/markdown/export/{work_id} endpoint
    - GET /api/v1/markdown/check-duplicate endpoint
    - GET /api/v1/markdown/files endpoint
    - POST /api/v1/markdown/import endpoint

Usage:
    pytest tests/unit/test_markdown_export_api.py -v
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock, MagicMock as MMock
from pathlib import Path

from vulcanlab_api.routers.markdown import router
from vulcanlab_api.dependencies import get_db_session
from fastapi import HTTPException
from vulcanlab.data.models.work import Work


# Global mock session to control in tests
mock_session_instance = None


def get_mock_db_session():
    """Override dependency to return controllable mock session."""
    return mock_session_instance


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1/markdown")
app.dependency_overrides[get_db_session] = get_mock_db_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_session():
    """Reset mock session before each test."""
    global mock_session_instance
    mock_session_instance = MagicMock()
    yield
    mock_session_instance = None


class TestExportWorkEndpoint:
    """Tests for POST /api/v1/markdown/export/{work_id} endpoint."""

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_success(self, mock_export_work):
        """Test successful work export returns correct response."""
        mock_export_work.return_value = "/path/to/exports/test-work.md"

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['export_path'] == "/path/to/exports/test-work.md"

        # Verify export_work was called with correct arguments
        mock_export_work.assert_called_once_with(1, mock_session_instance)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_not_found(self, mock_export_work):
        """Test export returns 404 when work not found."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: 999")

        response = client.post('/api/v1/markdown/export/999')

        assert response.status_code == 404
        assert "Work not found" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_markdown_unavailable(self, mock_export_work):
        """Test export returns 400 when markdown unavailable."""
        mock_export_work.side_effect = HTTPException(
            status_code=400,
            detail="No markdown available for work 1 (title: Test Work)"
        )

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 400
        assert "No markdown available" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_write_error(self, mock_export_work):
        """Test export returns 500 on write error."""
        mock_export_work.side_effect = HTTPException(
            status_code=500,
            detail="Failed to write export file: Permission denied"
        )

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 500
        assert "Failed to write export file" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_unexpected_error(self, mock_export_work):
        """Test export handles unexpected errors gracefully."""
        mock_export_work.side_effect = RuntimeError("Unexpected error")

        response = client.post('/api/v1/markdown/export/1')

        assert response.status_code == 500
        assert "Unexpected error during export" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_invalid_id_type(self, mock_export_work):
        """Test export rejects invalid work ID type."""
        response = client.post('/api/v1/markdown/export/invalid')

        # FastAPI will return 422 for validation error
        assert response.status_code == 422

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_response_format(self, mock_export_work):
        """Test export returns correct response format."""
        mock_export_work.return_value = "/exports/psychology-book.md"

        response = client.post('/api/v1/markdown/export/42')

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert 'success' in data
        assert 'export_path' in data
        assert isinstance(data['success'], bool)
        assert isinstance(data['export_path'], str)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_zero_id(self, mock_export_work):
        """Test export with work ID zero."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: 0")

        response = client.post('/api/v1/markdown/export/0')

        assert response.status_code == 404

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_negative_id(self, mock_export_work):
        """Test export with negative work ID."""
        mock_export_work.side_effect = HTTPException(status_code=404, detail="Work not found: -1")

        response = client.post('/api/v1/markdown/export/-1')

        # Should still process (DB won't find it)
        assert response.status_code == 404

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_large_id(self, mock_export_work):
        """Test export with large work ID."""
        large_id = 999999999
        mock_export_work.return_value = f"/exports/work-{large_id}.md"

        response = client.post(f'/api/v1/markdown/export/{large_id}')

        assert response.status_code == 200
        mock_export_work.assert_called_once_with(large_id, mock_session_instance)

    @patch('vulcanlab_api.routers.markdown.export_work')
    def test_export_work_session_passed(self, mock_export_work):
        """Test that database session is passed to export_work."""
        mock_export_work.return_value = "/exports/test.md"

        response = client.post('/api/v1/markdown/export/1')

        # Verify session was passed as second argument
        assert response.status_code == 200
        call_args = mock_export_work.call_args
        assert call_args[0][0] == 1  # work_id
        assert call_args[0][1] == mock_session_instance  # session


class TestCheckDuplicateEndpoint:
    """Tests for GET /api/v1/markdown/check-duplicate endpoint."""

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_found(self, mock_check_duplicate):
        """Test returns exists=true when duplicate found."""
        mock_work = Mock(spec=Work)
        mock_work.id = 123
        mock_work.title = "The Psychology of Learning"
        mock_check_duplicate.return_value = mock_work

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'The Psychology of Learning', 'author': 'John Doe'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['exists'] is True
        assert data['work_id'] == 123
        assert data['work_title'] == "The Psychology of Learning"

        # Verify check_duplicate_work was called correctly
        mock_check_duplicate.assert_called_once_with(
            'The Psychology of Learning',
            'John Doe',
            mock_session_instance
        )

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_not_found(self, mock_check_duplicate):
        """Test returns exists=false when no duplicate found."""
        mock_check_duplicate.return_value = None

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Unique Book', 'author': 'Unknown Author'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['exists'] is False
        assert 'work_id' not in data
        assert 'work_title' not in data

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_missing_title(self, mock_check_duplicate):
        """Test returns 400 when title parameter is missing."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'author': 'John Doe'}
        )

        assert response.status_code == 422  # FastAPI validation error
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_missing_author(self, mock_check_duplicate):
        """Test returns 400 when author parameter is missing."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Test Book'}
        )

        assert response.status_code == 422  # FastAPI validation error
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_empty_title(self, mock_check_duplicate):
        """Test returns 400 when title is empty string."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': '', 'author': 'John Doe'}
        )

        assert response.status_code == 400
        assert "Title parameter is required" in response.json()['detail']
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_empty_author(self, mock_check_duplicate):
        """Test returns 400 when author is empty string."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Test Book', 'author': ''}
        )

        assert response.status_code == 400
        assert "Author parameter is required" in response.json()['detail']
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_whitespace_title(self, mock_check_duplicate):
        """Test returns 400 when title is only whitespace."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': '   ', 'author': 'John Doe'}
        )

        assert response.status_code == 400
        assert "Title parameter is required" in response.json()['detail']
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_whitespace_author(self, mock_check_duplicate):
        """Test returns 400 when author is only whitespace."""
        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Test Book', 'author': '   '}
        )

        assert response.status_code == 400
        assert "Author parameter is required" in response.json()['detail']
        mock_check_duplicate.assert_not_called()

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_trims_whitespace(self, mock_check_duplicate):
        """Test trims leading/trailing whitespace from parameters."""
        mock_check_duplicate.return_value = None

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': '  Test Book  ', 'author': '  John Doe  '}
        )

        assert response.status_code == 200
        # Verify trimmed values were passed
        mock_check_duplicate.assert_called_once_with(
            'Test Book',
            'John Doe',
            mock_session_instance
        )

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_database_error(self, mock_check_duplicate):
        """Test returns 500 on database error."""
        mock_check_duplicate.side_effect = Exception("Database connection error")

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Test Book', 'author': 'John Doe'}
        )

        assert response.status_code == 500
        assert "Database error while checking for duplicates" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_case_insensitive(self, mock_check_duplicate):
        """Test works with different case inputs."""
        mock_work = Mock(spec=Work)
        mock_work.id = 456
        mock_work.title = "The Psychology of Learning"
        mock_check_duplicate.return_value = mock_work

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'the psychology of learning', 'author': 'john doe'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['exists'] is True
        assert data['work_id'] == 456

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_response_format(self, mock_check_duplicate):
        """Test response has correct format for duplicate found."""
        mock_work = Mock(spec=Work)
        mock_work.id = 789
        mock_work.title = "Cognitive Psychology"
        mock_check_duplicate.return_value = mock_work

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Cognitive Psychology', 'author': 'Jane Smith'}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert 'exists' in data
        assert isinstance(data['exists'], bool)
        assert 'work_id' in data
        assert isinstance(data['work_id'], int)
        assert 'work_title' in data
        assert isinstance(data['work_title'], str)

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_response_format_not_found(self, mock_check_duplicate):
        """Test response has correct format when no duplicate found."""
        mock_check_duplicate.return_value = None

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Unique Book', 'author': 'Unknown'}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert 'exists' in data
        assert isinstance(data['exists'], bool)
        assert data['exists'] is False
        # Should not have work_id or work_title
        assert len(data) == 1

    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_check_duplicate_session_passed(self, mock_check_duplicate):
        """Test that database session is passed to check_duplicate_work."""
        mock_check_duplicate.return_value = None

        response = client.get(
            '/api/v1/markdown/check-duplicate',
            params={'title': 'Test', 'author': 'Author'}
        )

        assert response.status_code == 200
        # Verify session was passed as third argument
        call_args = mock_check_duplicate.call_args
        assert call_args[0][2] == mock_session_instance


class TestListFilesEndpoint:
    """Tests for GET /api/v1/markdown/files endpoint."""

    @patch('vulcanlab_api.routers.markdown.list_markdown_files')
    def test_list_files_success(self, mock_list_files):
        """Test returns list of markdown files with metadata."""
        from vulcanlab.markdown_import.metadata import MarkdownFile, Metadata

        # Mock markdown files
        mock_files = [
            MarkdownFile(
                filename="test1.md",
                file_path="/input/test1.md",
                has_metadata=True,
                metadata=Metadata(title="Test 1", author="Author 1", year=2020)
            ),
            MarkdownFile(
                filename="test2.md",
                file_path="/input/test2.md",
                has_metadata=False,
                metadata=None
            )
        ]
        mock_list_files.return_value = mock_files

        response = client.get('/api/v1/markdown/files')

        assert response.status_code == 200
        data = response.json()
        assert 'files' in data
        assert len(data['files']) == 2

        # Check first file with metadata
        file1 = data['files'][0]
        assert file1['filename'] == "test1.md"
        assert file1['has_metadata'] is True
        assert file1['metadata']['title'] == "Test 1"
        assert file1['metadata']['author'] == "Author 1"
        assert file1['metadata']['year'] == 2020

        # Check second file without metadata
        file2 = data['files'][1]
        assert file2['filename'] == "test2.md"
        assert file2['has_metadata'] is False
        assert file2['metadata'] is None

    @patch('vulcanlab_api.routers.markdown.list_markdown_files')
    def test_list_files_empty(self, mock_list_files):
        """Test returns empty list when no files found."""
        mock_list_files.return_value = []

        response = client.get('/api/v1/markdown/files')

        assert response.status_code == 200
        data = response.json()
        assert 'files' in data
        assert len(data['files']) == 0

    @patch('vulcanlab_api.routers.markdown.list_markdown_files')
    def test_list_files_config_error(self, mock_list_files):
        """Test returns 500 on configuration error."""
        mock_list_files.side_effect = ValueError("input_dir not configured")

        response = client.get('/api/v1/markdown/files')

        assert response.status_code == 500
        assert "Configuration error" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.list_markdown_files')
    def test_list_files_filesystem_error(self, mock_list_files):
        """Test returns 500 on filesystem error."""
        mock_list_files.side_effect = OSError("Permission denied")

        response = client.get('/api/v1/markdown/files')

        assert response.status_code == 500
        assert "Filesystem error" in response.json()['detail']


class TestImportMarkdownEndpoint:
    """Tests for POST /api/v1/markdown/import endpoint."""

    def _mock_path_exists(self, exists=True, is_file=True):
        """Helper to properly mock Path with / operator support."""
        mock_path_cls = MagicMock()
        mock_input_dir = MagicMock()
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = exists
        mock_file_path.is_file.return_value = is_file
        mock_input_dir.__truediv__.return_value = mock_file_path
        mock_path_cls.return_value = mock_input_dir
        return mock_path_cls

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    @patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
    def test_import_sanitized_success(self, mock_import_sanitized, mock_check_dup, mock_config):
        """Test successful import of sanitized markdown."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock no duplicate
        mock_check_dup.return_value = None

        # Mock successful import
        mock_work = Mock()
        mock_work.id = 456
        mock_import_sanitized.return_value = mock_work

        # Mock Path properly
        with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
            response = client.post(
                '/api/v1/markdown/import',
                json={
                    "filename": "test.md",
                    "title": "Test Book",
                    "author": "Test Author",
                    "year": 2023,
                    "is_sanitized": True
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data['work_id'] == 456
        assert data['status'] == "completed"
        assert data['duplicate_warning'] is None

        # Verify import function was called
        mock_import_sanitized.assert_called_once()

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    @patch('vulcanlab_api.routers.markdown.import_unsanitized_markdown')
    def test_import_unsanitized_success(self, mock_import_unsanitized, mock_check_dup, mock_config):
        """Test successful import of unsanitized markdown."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock no duplicate
        mock_check_dup.return_value = None

        # Mock successful import
        mock_work = Mock()
        mock_work.id = 789
        mock_import_unsanitized.return_value = mock_work

        # Mock Path properly
        with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
            response = client.post(
                '/api/v1/markdown/import',
                json={
                    "filename": "test.md",
                    "title": "Test Book",
                    "author": "Test Author",
                    "year": 2023,
                    "is_sanitized": False
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data['work_id'] == 789
        assert data['status'] == "completed"

        # Verify import function was called
        mock_import_unsanitized.assert_called_once()

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_import_with_duplicate_warning(self, mock_check_dup, mock_config):
        """Test import proceeds with duplicate warning."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock duplicate found
        mock_dup_work = Mock()
        mock_dup_work.id = 100
        mock_dup_work.title = "Existing Work"
        mock_check_dup.return_value = mock_dup_work

        # Mock successful import
        with patch('vulcanlab_api.routers.markdown.import_sanitized_markdown') as mock_import:
            mock_work = Mock()
            mock_work.id = 999
            mock_import.return_value = mock_work

            with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
                response = client.post(
                    '/api/v1/markdown/import',
                    json={
                        "filename": "test.md",
                        "title": "Test Book",
                        "author": "Test Author",
                        "is_sanitized": True
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data['work_id'] == 999
        assert data['duplicate_warning'] is not None
        assert "already exists" in data['duplicate_warning']
        assert "100" in data['duplicate_warning']

    def test_import_missing_required_fields(self):
        """Test validation error for missing required fields."""
        # Missing title
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "author": "Test Author",
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

        # Missing author
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

        # Missing is_sanitized
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "author": "Test Author"
            }
        )
        assert response.status_code == 422

    def test_import_empty_title(self):
        """Test validation error for empty title."""
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "",
                "author": "Test Author",
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

    def test_import_empty_author(self):
        """Test validation error for empty author."""
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "author": "",
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

    def test_import_invalid_year(self):
        """Test validation error for invalid year."""
        # Year too old
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "author": "Test Author",
                "year": 500,
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

        # Year too far in future
        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "author": "Test Author",
                "year": 3000,
                "is_sanitized": True
            }
        )
        assert response.status_code == 422

    @patch('vulcanlab_api.routers.markdown.load_config')
    def test_import_file_not_found(self, mock_config):
        """Test returns 404 when file doesn't exist."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock Path to return file not found
        with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists(exists=False)):
            response = client.post(
                '/api/v1/markdown/import',
                json={
                    "filename": "nonexistent.md",
                    "title": "Test Book",
                    "author": "Test Author",
                    "is_sanitized": True
                }
            )

        assert response.status_code == 404
        assert "not found" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.load_config')
    def test_import_config_error(self, mock_config):
        """Test returns 500 when input_dir not configured."""
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = None
        mock_config.return_value = mock_cfg

        response = client.post(
            '/api/v1/markdown/import',
            json={
                "filename": "test.md",
                "title": "Test Book",
                "author": "Test Author",
                "is_sanitized": True
            }
        )

        assert response.status_code == 500
        assert "not configured" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    @patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
    def test_import_processing_error(self, mock_import, mock_check_dup, mock_config):
        """Test returns 500 on import processing error."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock no duplicate
        mock_check_dup.return_value = None

        # Mock import failure
        mock_import.side_effect = RuntimeError("Processing failed")

        with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
            response = client.post(
                '/api/v1/markdown/import',
                json={
                    "filename": "test.md",
                    "title": "Test Book",
                    "author": "Test Author",
                    "is_sanitized": True
                }
            )

        assert response.status_code == 500
        assert "Import failed" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    @patch('vulcanlab_api.routers.markdown.import_sanitized_markdown')
    def test_import_validation_error(self, mock_import, mock_check_dup, mock_config):
        """Test returns 400 on validation error during import."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock no duplicate
        mock_check_dup.return_value = None

        # Mock validation error
        mock_import.side_effect = ValueError("Invalid content")

        with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
            response = client.post(
                '/api/v1/markdown/import',
                json={
                    "filename": "test.md",
                    "title": "Test Book",
                    "author": "Test Author",
                    "is_sanitized": True
                }
            )

        assert response.status_code == 400
        assert "Validation error" in response.json()['detail']

    @patch('vulcanlab_api.routers.markdown.load_config')
    @patch('vulcanlab_api.routers.markdown.check_duplicate_work')
    def test_import_duplicate_check_error_doesnt_block(self, mock_check_dup, mock_config):
        """Test import proceeds even if duplicate check fails."""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.paths.input_dir = "/tmp/input"
        mock_config.return_value = mock_cfg

        # Mock duplicate check failure
        mock_check_dup.side_effect = Exception("DB error")

        # Mock successful import
        with patch('vulcanlab_api.routers.markdown.import_sanitized_markdown') as mock_import:
            mock_work = Mock()
            mock_work.id = 555
            mock_import.return_value = mock_work

            with patch('vulcanlab_api.routers.markdown.Path', self._mock_path_exists()):
                response = client.post(
                    '/api/v1/markdown/import',
                    json={
                        "filename": "test.md",
                        "title": "Test Book",
                        "author": "Test Author",
                        "is_sanitized": True
                    }
                )

        # Should still succeed
        assert response.status_code == 200
        assert response.json()['work_id'] == 555
