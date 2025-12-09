"""
Unit tests for apply_title_changes module.

Tests cover:
- Title change application logic
- Markdown modification
- Validation logic
- Error handling
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from vulcanlab.sanitization.apply_title_changes import (
    parse_title_changes,
    preview_title_changes,
    apply_title_changes,
    apply_title_changes_from_work,
)
from vulcanlab.sanitization.extract_titles import HashMismatchError
from vulcanlab.data.models.work import Work
from tests.unit.mock_helpers import mock_session


class TestParseTitleChanges:
    """Tests for parse_title_changes function."""

    def test_parse_title_changes_success(self, tmp_path):
        """Test successful parsing of title changes file."""
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : New Title
5 : H2 : Section Title
10 : REMOVE : Old Title
15 : NO_CHANGE : Updated Text
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        relative_uri, changes = parse_title_changes(changes_file)

        assert relative_uri == "relative/path/to/file.md"
        assert len(changes) == 4
        assert changes[0] == {'line_num': 1, 'action': 'H1', 'title_text': 'New Title'}
        assert changes[1] == {'line_num': 5, 'action': 'H2', 'title_text': 'Section Title'}
        assert changes[2] == {'line_num': 10, 'action': 'REMOVE', 'title_text': 'Old Title'}
        assert changes[3] == {'line_num': 15, 'action': 'NO_CHANGE', 'title_text': 'Updated Text'}

    def test_parse_title_changes_with_whitespace(self, tmp_path):
        """Test parsing handles whitespace correctly."""
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
  1  :  H1  :  Title with spaces  
  2  :  H2  :  Another Title
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        relative_uri, changes = parse_title_changes(changes_file)

        assert relative_uri == "relative/path/to/file.md"
        assert len(changes) == 2
        assert changes[0] == {'line_num': 1, 'action': 'H1', 'title_text': 'Title with spaces'}
        assert changes[1] == {'line_num': 2, 'action': 'H2', 'title_text': 'Another Title'}

    def test_parse_title_changes_all_levels(self, tmp_path):
        """Test parsing supports all heading levels (H1-H4)."""
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : Level 1
2 : H2 : Level 2
3 : H3 : Level 3
4 : H4 : Level 4
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        relative_uri, changes = parse_title_changes(changes_file)

        assert len(changes) == 4
        assert changes[0]['action'] == 'H1'
        assert changes[1]['action'] == 'H2'
        assert changes[2]['action'] == 'H3'
        assert changes[3]['action'] == 'H4'

    def test_parse_title_changes_file_not_found(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        changes_file = tmp_path / "nonexistent.title_changes.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            parse_title_changes(changes_file)

        assert "Changes file not found" in str(exc_info.value)

    def test_parse_title_changes_empty_file(self, tmp_path):
        """Test that empty file raises ValueError."""
        changes_file = tmp_path / "empty.title_changes.md"
        changes_file.write_text("", encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            parse_title_changes(changes_file)

        assert "Changes file is empty" in str(exc_info.value)

    def test_parse_title_changes_no_codeblock(self, tmp_path):
        """Test that missing codeblock raises ValueError."""
        changes_file = tmp_path / "test.title_changes.md"
        changes_file.write_text("relative/path/to/file.md\nNo codeblock here", encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            parse_title_changes(changes_file)

        assert "No changes codeblock found" in str(exc_info.value)

    def test_parse_title_changes_invalid_format(self, tmp_path):
        """Test that invalid format lines are skipped."""
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : Valid Line
invalid line format
2 : H2 : Another Valid Line
also invalid
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        relative_uri, changes = parse_title_changes(changes_file)

        assert len(changes) == 2
        assert changes[0]['line_num'] == 1
        assert changes[1]['line_num'] == 2


class TestPreviewTitleChanges:
    """Tests for preview_title_changes function."""

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_preview_title_changes_success(self, mock_session_local, tmp_path):
        """Test successful preview of title changes."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        # Setup mock work
        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "test.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        # Create markdown file
        markdown_content = """# Original Title
Some content here
## Section Title
More content
### Subsection
Even more content
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        # Create changes file
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : New Title
3 : H2 : Updated Section
5 : REMOVE : Subsection
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        previews = preview_title_changes(changes_file, work_id=1)

        assert len(previews) == 3
        assert previews[0]['line_num'] == 1
        assert previews[0]['old_line'] == "# Original Title"
        assert previews[0]['new_line'] == "# New Title"
        assert previews[1]['line_num'] == 3
        assert previews[1]['old_line'] == "## Section Title"
        assert previews[1]['new_line'] == "## Updated Section"
        assert previews[2]['line_num'] == 5
        assert previews[2]['old_line'] == "### Subsection"
        assert previews[2]['new_line'] == "[REMOVED]"

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_preview_title_changes_no_change_action(self, mock_session_local, tmp_path):
        """Test preview with NO_CHANGE action preserves heading level."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "test.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        markdown_content = """### Original Level 3 Title
Content here
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : NO_CHANGE : Updated Text But Same Level
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        previews = preview_title_changes(changes_file, work_id=1)

        assert len(previews) == 1
        assert previews[0]['old_line'] == "### Original Level 3 Title"
        assert previews[0]['new_line'] == "### Updated Text But Same Level"

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_preview_title_changes_work_not_found(self, mock_session_local, tmp_path):
        """Test that missing work raises ValueError."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = None

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : Title
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            preview_title_changes(changes_file, work_id=999)

        assert "Work with ID 999 not found" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_preview_title_changes_no_markdown_path(self, mock_session_local, tmp_path):
        """Test that work without markdown_path raises ValueError."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_work = MagicMock()
        mock_work.id = 1
        mock_work.markdown_path = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : Title
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            preview_title_changes(changes_file, work_id=1)

        assert "has no markdown_path" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_preview_title_changes_markdown_not_found(self, mock_session_local, tmp_path):
        """Test that missing markdown file raises FileNotFoundError."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "nonexistent.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : Title
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        with pytest.raises(FileNotFoundError) as exc_info:
            preview_title_changes(changes_file, work_id=1)

        assert "Markdown file not found" in str(exc_info.value)


class TestApplyTitleChanges:
    """Tests for apply_title_changes function (legacy)."""

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_apply_title_changes_success(
        self, mock_session_local, mock_set_readonly, mock_compute_hash, tmp_path
    ):
        """Test successful application of title changes."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        # Setup mock work
        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "test.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        # Create markdown file
        markdown_content = """# Original Title
Some content here
## Section Title
More content
### Subsection
Even more content
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        # Create changes file
        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : H1 : New Title
3 : H2 : Updated Section
5 : REMOVE : Subsection
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        # Mock hash computation
        mock_compute_hash.return_value = "abc123hash"

        result_path = apply_title_changes(changes_file, work_id=1)

        # Verify sanitized file was created
        sanitized_path = markdown_path.with_name(markdown_path.stem + '.sanitized.md')
        assert result_path == sanitized_path
        assert sanitized_path.exists()

        # Verify content
        sanitized_content = sanitized_path.read_text(encoding='utf-8')
        lines = sanitized_content.splitlines()
        assert lines[0] == "# New Title"
        assert lines[1] == "Some content here"
        assert lines[2] == "## Updated Section"
        assert lines[3] == "More content"
        # Line 5 (Subsection) should be removed
        assert "### Subsection" not in sanitized_content

        # Verify database was updated
        assert mock_work.content_hash == "abc123hash"
        assert mock_work.markdown_path == str(sanitized_path.absolute())
        mock_session.commit.assert_called_once()

        # Verify file was set to read-only
        mock_set_readonly.assert_called_once_with(sanitized_path)

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_apply_title_changes_no_change_action(self, mock_session_local, tmp_path):
        """Test applying NO_CHANGE action preserves heading level."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "test.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        markdown_content = """### Original Level 3 Title
Content here
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
1 : NO_CHANGE : Updated Text But Same Level
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        with patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash') as mock_hash, \
             patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly'):
            mock_hash.return_value = "hash123"
            result_path = apply_title_changes(changes_file, work_id=1)

            sanitized_content = result_path.read_text(encoding='utf-8')
            assert "### Updated Text But Same Level" in sanitized_content

    @patch('vulcanlab.sanitization.apply_title_changes.SessionLocal')
    def test_apply_title_changes_remove_action(self, mock_session_local, tmp_path):
        """Test REMOVE action removes the line."""
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_session_local.return_value = mock_session

        mock_work = MagicMock()
        mock_work.id = 1
        markdown_path = tmp_path / "test.md"
        mock_work.markdown_path = str(markdown_path)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_work

        markdown_content = """# Title
Content before
## Section to Remove
Content after
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        changes_file = tmp_path / "test.title_changes.md"
        changes_content = """relative/path/to/file.md
```
3 : REMOVE : Section to Remove
```
"""
        changes_file.write_text(changes_content, encoding='utf-8')

        with patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash') as mock_hash, \
             patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly'):
            mock_hash.return_value = "hash123"
            result_path = apply_title_changes(changes_file, work_id=1)

            sanitized_content = result_path.read_text(encoding='utf-8')
            assert "## Section to Remove" not in sanitized_content
            assert "# Title" in sanitized_content
            assert "Content before" in sanitized_content
            assert "Content after" in sanitized_content


class TestApplyTitleChangesFromWork:
    """Tests for apply_title_changes_from_work function."""

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.is_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_success(
        self, mock_get_session, mock_is_readonly, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test successful application from work with original_markdown source."""
        # Setup mock session
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        # Create work with files metadata
        markdown_path = tmp_path / "test.md"
        title_changes_path = tmp_path / "test.title_changes.md"
        markdown_hash = "markdown_hash_123"
        title_changes_hash = "changes_hash_456"
        sanitized_hash = "sanitized_hash_789"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": markdown_hash
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": title_changes_hash
                }
            }
        )
        # Configure mock session to return the work
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        # Create markdown file
        markdown_content = """# Original Title
Some content
## Section
More content
"""
        markdown_path.write_text(markdown_content, encoding='utf-8')

        # Create changes file
        changes_content = """relative/path/to/file.md
```
1 : H1 : New Title
3 : H2 : Updated Section
```
"""
        title_changes_path.write_text(changes_content, encoding='utf-8')

        # Mock hash computations
        def hash_side_effect(path):
            if path == markdown_path:
                return markdown_hash
            elif path == title_changes_path:
                return title_changes_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        # Mock file readonly check
        mock_is_readonly.return_value = False

        result_path = apply_title_changes_from_work(
            work_id=1,
            source_key='original_markdown',
            verbose=False
        )

        # Verify output file was created
        output_path = tmp_path / "test.sanitized.md"
        assert result_path == output_path
        assert output_path.exists()

        # Verify content
        sanitized_content = output_path.read_text(encoding='utf-8')
        lines = sanitized_content.splitlines()
        assert lines[0] == "# New Title"
        assert lines[2] == "## Updated Section"

        # Verify database was updated
        # session.refresh(work)  # Not needed with mocks as we modify the object in place
        assert "sanitized" in work.files
        assert work.files["sanitized"]["hash"] == sanitized_hash
        assert work.files["sanitized"]["path"] == str(output_path.resolve())

        # Verify file was set to read-only
        mock_set_readonly.assert_called_once_with(output_path)

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_writable')
    @patch('vulcanlab.sanitization.apply_title_changes.is_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_overwrite_readonly(
        self, mock_get_session, mock_is_readonly, mock_set_writable,
        mock_set_readonly, mock_compute_hash, tmp_path, mock_session
    ):
        """Test overwriting existing read-only sanitized file."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        title_changes_path = tmp_path / "test.title_changes.md"
        sanitized_path = tmp_path / "test.sanitized.md"
        markdown_hash = "markdown_hash_123"
        title_changes_hash = "changes_hash_456"
        sanitized_hash = "sanitized_hash_789"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": markdown_hash
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": title_changes_hash
                },
                "sanitized": {
                    "path": str(sanitized_path),
                    "hash": "old_hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\nContent\n", encoding='utf-8')
        title_changes_path.write_text("""relative/path/to/file.md
```
1 : H1 : New Title
```
""", encoding='utf-8')
        sanitized_path.write_text("# Old Content\n", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return markdown_hash
            elif path == title_changes_path:
                return title_changes_hash
            else:
                return sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        mock_is_readonly.return_value = True

        result_path = apply_title_changes_from_work(
            work_id=1,
            source_key='original_markdown',
            verbose=False
        )

        # Verify file was made writable before overwrite
        mock_set_writable.assert_called_once_with(sanitized_path)
        # Verify file was set back to read-only
        mock_set_readonly.assert_called_once_with(sanitized_path)

        # Verify content was updated
        content = sanitized_path.read_text(encoding='utf-8')
        assert "# New Title" in content

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_not_found(self, mock_get_session, mock_session):
        """Test that missing work raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            apply_title_changes_from_work(work_id=999, source_key='original_markdown')

        assert "Work with ID 999 not found" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_no_files(self, mock_get_session, mock_session):
        """Test that work without files raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(id=1, title="Test Work", files=None)
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='original_markdown')

        assert "has no files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_invalid_source_key(self, mock_get_session, mock_session, tmp_path):
        """Test that invalid source_key raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"original_markdown": {"path": str(tmp_path / "test.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='invalid_key')

        assert "Invalid source_key" in str(exc_info.value)
        assert "Must be 'original_markdown' or 'sanitized'" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_missing_markdown_file(self, mock_get_session, mock_session, tmp_path):
        """Test that missing markdown file in metadata raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"title_changes": {"path": str(tmp_path / "changes.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='original_markdown')

        assert "does not have 'original_markdown' in files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_missing_title_changes_file(self, mock_get_session, mock_session, tmp_path):
        """Test that missing title_changes file in metadata raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"original_markdown": {"path": str(tmp_path / "test.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='original_markdown')

        assert "does not have 'title_changes' in files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_hash_mismatch(
        self, mock_get_session, mock_compute_hash, tmp_path, mock_session
    ):
        """Test that hash mismatch raises HashMismatchError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        title_changes_path = tmp_path / "test.title_changes.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "stored_hash_123"
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": "stored_hash_456"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\n", encoding='utf-8')
        title_changes_path.write_text("""relative/path/to/file.md
```
1 : H1 : New Title
```
""", encoding='utf-8')

        # Mock hash to return different values
        def hash_side_effect(path):
            if path == markdown_path:
                return "current_hash_123"  # Different from stored
            elif path == title_changes_path:
                return "stored_hash_456"  # Same as stored
            return "hash"
        mock_compute_hash.side_effect = hash_side_effect

        with pytest.raises(HashMismatchError):
            apply_title_changes_from_work(work_id=1, source_key='original_markdown', force=False)

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.is_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_hash_mismatch_force(
        self, mock_get_session, mock_is_readonly, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test that hash mismatch with force=True proceeds anyway."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        title_changes_path = tmp_path / "test.title_changes.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "stored_hash_123"
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": "stored_hash_456"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\n", encoding='utf-8')
        title_changes_path.write_text("""relative/path/to/file.md
```
1 : H1 : New Title
```
""", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return "current_hash_123"  # Different from stored
            elif path == title_changes_path:
                return "stored_hash_456"
            return "sanitized_hash"
        mock_compute_hash.side_effect = hash_side_effect

        mock_is_readonly.return_value = False

        # Should not raise error with force=True
        result_path = apply_title_changes_from_work(
            work_id=1,
            source_key='original_markdown',
            force=True,
            verbose=False
        )

        assert result_path.exists()

    @patch('vulcanlab.sanitization.apply_title_changes.compute_file_hash')
    @patch('vulcanlab.sanitization.apply_title_changes.set_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.is_file_readonly')
    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_sanitized_source(
        self, mock_get_session, mock_is_readonly, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test applying changes from sanitized source."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        sanitized_path = tmp_path / "test.sanitized.md"
        title_changes_path = tmp_path / "test.sanitized.title_changes.md"
        sanitized_hash = "sanitized_hash_123"
        title_changes_hash = "changes_hash_456"
        new_sanitized_hash = "new_sanitized_hash_789"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "sanitized": {
                    "path": str(sanitized_path),
                    "hash": sanitized_hash
                },
                "sanitized_title_changes": {
                    "path": str(title_changes_path),
                    "hash": title_changes_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        sanitized_path.write_text("# Title\nContent\n", encoding='utf-8')
        title_changes_path.write_text("""relative/path/to/file.md
```
1 : H1 : Updated Title
```
""", encoding='utf-8')

        def hash_side_effect(path):
            if path == sanitized_path:
                return sanitized_hash
            elif path == title_changes_path:
                return title_changes_hash
            else:
                return new_sanitized_hash
        mock_compute_hash.side_effect = hash_side_effect

        mock_is_readonly.return_value = False

        result_path = apply_title_changes_from_work(
            work_id=1,
            source_key='sanitized',
            verbose=False
        )

        # Should overwrite the same file
        assert result_path == sanitized_path
        assert sanitized_path.exists()

        # Verify content was updated
        content = sanitized_path.read_text(encoding='utf-8')
        assert "# Updated Title" in content

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_markdown_not_found_on_disk(
        self, mock_get_session, tmp_path, mock_session
    ):
        """Test that missing markdown file on disk raises FileNotFoundError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "nonexistent.md"
        title_changes_path = tmp_path / "changes.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "hash"
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        # Don't create the markdown file
        title_changes_path.write_text("""relative/path/to/file.md
```
1 : H1 : Title
```
""", encoding='utf-8')

        with pytest.raises(FileNotFoundError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='original_markdown')

        assert "Markdown file not found on disk" in str(exc_info.value)

    @patch('vulcanlab.sanitization.apply_title_changes.get_session')
    def test_apply_title_changes_from_work_title_changes_not_found_on_disk(
        self, mock_get_session, tmp_path, mock_session
    ):
        """Test that missing title_changes file on disk raises FileNotFoundError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        title_changes_path = tmp_path / "nonexistent.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "hash"
                },
                "title_changes": {
                    "path": str(title_changes_path),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\n", encoding='utf-8')
        # Don't create the title_changes file

        with pytest.raises(FileNotFoundError) as exc_info:
            apply_title_changes_from_work(work_id=1, source_key='original_markdown')

        assert "Title changes file not found on disk" in str(exc_info.value)
