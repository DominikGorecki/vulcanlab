"""
Unit tests for conversion API endpoints (file-content, suggestion, select-file).
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch
import shutil

import pytest
from fastapi import HTTPException

from vulcanlab_api.routers.conversion import (
    get_file_content,
    update_file_content,
    get_file_suggestion,
    select_file,
)
from vulcanlab_api.schemas.conversion import (
    FileContentUpdateRequest,
    FileSelectionRequest,
)


class TestGetFileContent:
    """Tests for get_file_content endpoint."""

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("vulcanlab_api.routers.conversion.extract_titles")
    @patch("pathlib.Path.exists")
    async def test_get_style_file_success(
        self, mock_exists, mock_extract_titles, mock_load_config, mock_get_session
    ):
        """Test successful retrieval of style.md file."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Mock file operations
        mock_exists.return_value = True
        # extract_titles returns a list of titles (without line numbers for this test)
        mock_extract_titles.return_value = ["# Test Content"]

        response = await get_file_content(1, "style")

        assert response.content == "# Test Content"
        assert response.filename == "test.style.md"

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    async def test_get_file_invalid_type(self, mock_get_session):
        """Test that invalid file type raises 400 error."""
        with pytest.raises(HTTPException) as exc_info:
            await get_file_content(1, "invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid file_type" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    async def test_get_file_not_found_in_db(self, mock_get_session):
        """Test that missing file in database raises 404 error."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(HTTPException) as exc_info:
            await get_file_content(999, "style")
        
        assert exc_info.value.status_code == 404
        assert "not found in database" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.exists")
    async def test_get_file_not_found_on_disk(
        self, mock_exists, mock_load_config, mock_get_session
    ):
        """Test that missing file on disk raises 404 error."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # File doesn't exist
        mock_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await get_file_content(1, "style")
        
        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail


class TestUpdateFileContent:
    """Tests for update_file_content endpoint."""

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("vulcanlab_api.routers.conversion.extract_titles")
    @patch("vulcanlab.sanitization.apply_title_edits.Path.read_text")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.exists")
    async def test_update_file_success(
        self, mock_exists, mock_write_text, mock_read_text, mock_extract_titles, mock_load_config, mock_get_session
    ):
        """Test successful file update."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # File exists
        mock_exists.return_value = True
        # Mock read_text for apply_title_edits (it reads the file to apply edits)
        mock_read_text.return_value = "# Original Content"
        # Mock extract_titles to return the updated content
        mock_extract_titles.return_value = ["# Updated Content"]

        request = FileContentUpdateRequest(content="# Updated Content")
        response = await update_file_content(1, "hier", request)

        assert response.content == "# Updated Content"
        assert response.filename == "test.hier.md"
        # apply_title_edits should have been called (it writes internally)

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    async def test_update_file_invalid_type(self, mock_get_session):
        """Test that invalid file type raises 400 error."""
        request = FileContentUpdateRequest(content="# Content")
        
        with pytest.raises(HTTPException) as exc_info:
            await update_file_content(1, "wrong", request)
        
        assert exc_info.value.status_code == 400


class TestGetFileSuggestion:
    """Tests for get_file_suggestion endpoint."""

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("vulcanlab_api.routers.conversion.extract_headings")
    @patch("vulcanlab_api.routers.conversion.compute_final_score")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    async def test_get_suggestion_hier_wins(
        self,
        mock_exists,
        mock_read_text,
        mock_compute_final_score,
        mock_extract_headings,
        mock_load_config,
        mock_get_session,
    ):
        """Test suggestion when hier file wins."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Both files exist
        mock_exists.return_value = True
        mock_read_text.return_value = "# Content\n\n## Section"

        # Mock headings
        mock_extract_headings.return_value = []

        # Mock metrics - hier has better score
        mock_style_metrics = MagicMock()
        mock_style_metrics.total_headings = 10
        mock_style_metrics.h1_h2_count = 5
        mock_style_metrics.max_depth = 3
        mock_style_metrics.avg_depth = 2.0
        mock_style_metrics.coverage_score = 0.7
        mock_style_metrics.hierarchy_score = 0.75
        mock_style_metrics.chunkability_score = 0.6
        mock_style_metrics.target_size_sections = 5
        mock_style_metrics.small_sections = 2
        mock_style_metrics.large_sections = 1
        mock_style_metrics.level_jump_count = 2
        mock_style_metrics.penalty_total = 5.0
        mock_style_metrics.final_score = 0.70

        mock_hier_metrics = MagicMock()
        mock_hier_metrics.total_headings = 12
        mock_hier_metrics.h1_h2_count = 6
        mock_hier_metrics.max_depth = 3
        mock_hier_metrics.avg_depth = 2.2
        mock_hier_metrics.coverage_score = 0.8
        mock_hier_metrics.hierarchy_score = 0.85
        mock_hier_metrics.chunkability_score = 0.75
        mock_hier_metrics.target_size_sections = 8
        mock_hier_metrics.small_sections = 1
        mock_hier_metrics.large_sections = 0
        mock_hier_metrics.level_jump_count = 1
        mock_hier_metrics.penalty_total = 0.0
        mock_hier_metrics.final_score = 0.85

        mock_compute_final_score.side_effect = [mock_style_metrics, mock_hier_metrics]

        response = await get_file_suggestion(1)

        assert response.winner == "hier"
        assert response.score_difference > 0
        assert response.hier_metrics.final_score > response.style_metrics.final_score

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.exists")
    async def test_get_suggestion_file_not_found(
        self, mock_exists, mock_load_config, mock_get_session
    ):
        """Test suggestion when files don't exist."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Files don't exist
        mock_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await get_file_suggestion(1)
        
        assert exc_info.value.status_code == 404


class TestSelectFile:
    """Tests for select_file endpoint."""

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("shutil.copy2")
    @patch("pathlib.Path.exists")
    async def test_select_file_success(
        self, mock_exists, mock_copy2, mock_load_config, mock_get_session
    ):
        """Test successful file selection."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Source exists, target doesn't
        mock_exists.side_effect = [True, False]

        request = FileSelectionRequest(file_type="hier")
        response = await select_file(1, request)

        assert response.success is True
        assert "hier.md" in response.message
        assert response.output_file == "test.md"
        mock_copy2.assert_called_once()

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    async def test_select_file_invalid_type(self, mock_get_session):
        """Test that invalid file type raises 400 error."""
        request = FileSelectionRequest(file_type="invalid")
        
        with pytest.raises(HTTPException) as exc_info:
            await select_file(1, request)
        
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("vulcanlab_api.routers.conversion.get_session")
    @patch("vulcanlab_api.routers.conversion.load_config")
    @patch("pathlib.Path.exists")
    async def test_select_file_target_exists(
        self, mock_exists, mock_load_config, mock_get_session
    ):
        """Test that existing target file raises 400 error."""
        # Mock database
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"
        mock_load_config.return_value = mock_config

        # Both source and target exist
        mock_exists.return_value = True

        request = FileSelectionRequest(file_type="style")
        
        with pytest.raises(HTTPException) as exc_info:
            await select_file(1, request)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

