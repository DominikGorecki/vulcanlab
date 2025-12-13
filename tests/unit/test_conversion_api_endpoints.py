"""
Unit tests for conversion API endpoints (file-content, suggestion, select-file).

These tests use mocks exclusively and do NOT interact with a real database.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

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
    async def test_get_style_file_success(self):
        """Test successful retrieval of style.md file."""
        # Create a proper context manager mock for get_session
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        # Setup query chain
        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        # Mock config
        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("vulcanlab_api.routers.conversion.extract_titles", return_value=["# Test Content"]), \
             patch("pathlib.Path.exists", return_value=True):

            response = await get_file_content(1, "style")

            assert response.content == "# Test Content"
            assert response.filename == "test.style.md"

            # Verify database was not actually queried
            mock_session.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_invalid_type(self):
        """Test that invalid file type raises 400 error."""
        with pytest.raises(HTTPException) as exc_info:
            await get_file_content(1, "invalid")

        assert exc_info.value.status_code == 400
        assert "Invalid file_type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_file_not_found_in_db(self):
        """Test that missing file in database raises 404 error."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm):
            with pytest.raises(HTTPException) as exc_info:
                await get_file_content(999, "style")

            assert exc_info.value.status_code == 404
            assert "not found in database" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_file_not_found_on_disk(self):
        """Test that missing file on disk raises 404 error."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("pathlib.Path.exists", return_value=False):

            with pytest.raises(HTTPException) as exc_info:
                await get_file_content(1, "style")

            assert exc_info.value.status_code == 404
            assert "File not found" in exc_info.value.detail


class TestUpdateFileContent:
    """Tests for update_file_content endpoint."""

    @pytest.mark.asyncio
    async def test_update_file_success(self):
        """Test successful file update."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("vulcanlab_api.routers.conversion.extract_titles", return_value=["# Updated Content"]), \
             patch("vulcanlab_api.routers.conversion.apply_title_edits"), \
             patch("pathlib.Path.exists", return_value=True):

            request = FileContentUpdateRequest(content="# Updated Content")
            response = await update_file_content(1, "hier", request)

            assert response.content == "# Updated Content"
            assert response.filename == "test.hier.md"

    @pytest.mark.asyncio
    async def test_update_file_invalid_type(self):
        """Test that invalid file type raises 400 error."""
        request = FileContentUpdateRequest(content="# Content")

        with pytest.raises(HTTPException) as exc_info:
            await update_file_content(1, "wrong", request)

        assert exc_info.value.status_code == 400


class TestGetFileSuggestion:
    """Tests for get_file_suggestion endpoint."""

    @pytest.mark.asyncio
    async def test_get_suggestion_hier_wins(self):
        """Test suggestion when hier file wins."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

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

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("vulcanlab_api.routers.conversion.extract_headings", return_value=[]), \
             patch("vulcanlab_api.routers.conversion.compute_final_score", side_effect=[mock_style_metrics, mock_hier_metrics]), \
             patch("pathlib.Path.read_text", return_value="# Content\n\n## Section"), \
             patch("pathlib.Path.exists", return_value=True):

            response = await get_file_suggestion(1)

            assert response.winner == "hier"
            assert response.score_difference > 0
            assert response.hier_metrics.final_score > response.style_metrics.final_score

    @pytest.mark.asyncio
    async def test_get_suggestion_file_not_found(self):
        """Test suggestion when files don't exist."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("pathlib.Path.exists", return_value=False):

            with pytest.raises(HTTPException) as exc_info:
                await get_file_suggestion(1)

            assert exc_info.value.status_code == 404


class TestSelectFile:
    """Tests for select_file endpoint."""

    @pytest.mark.asyncio
    async def test_select_file_success(self):
        """Test successful file selection."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("shutil.copy2") as mock_copy2, \
             patch("pathlib.Path.exists", side_effect=[True, False]):

            request = FileSelectionRequest(file_type="hier")
            response = await select_file(1, request)

            assert response.success is True
            assert "hier.md" in response.message
            assert response.output_file == "test.md"
            mock_copy2.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_file_invalid_type(self):
        """Test that invalid file type raises 400 error."""
        request = FileSelectionRequest(file_type="invalid")

        with pytest.raises(HTTPException) as exc_info:
            await select_file(1, request)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_select_file_target_exists(self):
        """Test that existing target file raises 400 error."""
        mock_session_cm = MagicMock()
        mock_session = MagicMock()
        mock_io_file = MagicMock()
        mock_io_file.id = 1
        mock_io_file.filename = "test.pdf"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_io_file
        mock_session_cm.__enter__.return_value = mock_session
        mock_session_cm.__exit__.return_value = None

        mock_config = MagicMock()
        mock_config.paths.output_dir = "/output"

        with patch("vulcanlab_api.routers.conversion.get_session", return_value=mock_session_cm), \
             patch("vulcanlab_api.routers.conversion.load_config", return_value=mock_config), \
             patch("pathlib.Path.exists", return_value=True):

            request = FileSelectionRequest(file_type="style")

            with pytest.raises(HTTPException) as exc_info:
                await select_file(1, request)

            assert exc_info.value.status_code == 400
            assert "already exists" in exc_info.value.detail
