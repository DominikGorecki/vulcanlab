"""
Unit tests for original markdown API endpoints.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from vulcanlab_api.routers.conversion import (
    get_original_markdown,
    update_original_markdown,
)
from vulcanlab_api.schemas.conversion import FileContentUpdateRequest


class TestOriginalMarkdown:
    """Tests for original markdown endpoints."""

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    async def test_get_original_markdown_success(
        self, mock_exists, mock_read_text, mock_load_config, mock_get_session
    ):
        """Test successful retrieval of original markdown file via source IOFile ID."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        # This simulates an IOFile for a source file (e.g. EPUB/PDF)
        mock_io_file.filename = "test.epub"
        # The file path would be in input dir, but the code derives output path from filename
        mock_io_file.file_path = "/input/test.epub"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config to return output directory
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Mock file operations
        mock_exists.return_value = True
        mock_read_text.return_value = "# Original Content"

        response = await get_original_markdown(1)

        assert response.content == "# Original Content"
        # The filename returned should be the derived markdown filename
        assert response.filename == "test.md"
        mock_read_text.assert_called_once()

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    async def test_get_original_markdown_not_found_in_db(self, mock_get_session):
        """Test that missing file in database raises 404 error."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(HTTPException) as exc_info:
            await get_original_markdown(999)
        
        assert exc_info.value.status_code == 404
        assert "not found in database" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.exists")
    async def test_get_original_markdown_not_found_on_disk(
        self, mock_exists, mock_load_config, mock_get_session
    ):
        """Test that missing file on disk raises 404 error."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.epub"
        mock_io_file.file_path = "/input/test.epub"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # File doesn't exist
        mock_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await get_original_markdown(1)
        
        assert exc_info.value.status_code == 404
        assert "Original markdown file not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.exists")
    async def test_update_original_markdown_success(
        self, mock_exists, mock_write_text, mock_load_config, mock_get_session
    ):
        """Test successful update of original markdown file via source IOFile ID."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.epub"
        mock_io_file.file_path = "/input/test.epub"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # File exists
        mock_exists.return_value = True

        request = FileContentUpdateRequest(content="# Updated Content")
        response = await update_original_markdown(1, request)

        assert response.content == "# Updated Content"
        assert response.filename == "test.md"
        mock_write_text.assert_called_once_with("# Updated Content", encoding="utf-8")

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.exists")
    async def test_update_original_markdown_not_found(
        self, mock_exists, mock_load_config, mock_get_session
    ):
        """Test that updating non-existent file raises 404 error."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.epub"
        mock_io_file.file_path = "/input/test.epub"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # File doesn't exist
        mock_exists.return_value = False

        request = FileContentUpdateRequest(content="# Updated Content")
        with pytest.raises(HTTPException) as exc_info:
            await update_original_markdown(1, request)
        
        assert exc_info.value.status_code == 404
        assert "Original markdown file not found" in exc_info.value.detail
