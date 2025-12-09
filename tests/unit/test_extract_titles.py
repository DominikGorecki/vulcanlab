"""
Unit tests for extract_titles module.

Tests cover:
- Title extraction from markdown content
- Heading detection at various levels
- Edge cases (no titles, malformed headings)
- File operations
- Database integration

Usage:
    pytest tests/unit/test_extract_titles.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vulcanlab.sanitization.extract_titles import (
    _validate_input,
    _extract_titles_from_content,
    extract_titles,
    extract_titles_to_file,
    extract_titles_from_work,
    HashMismatchError,
)
from vulcanlab.data.models.work import Work
from tests.unit.mock_helpers import mock_session


class TestValidateInput:
    """Tests for _validate_input function."""

    def test_validate_input_success(self, tmp_path):
        """Test validation succeeds for valid markdown file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')

        # Should not raise
        _validate_input(test_file)

    def test_validate_input_markdown_uppercase(self, tmp_path):
        """Test validation succeeds for .MARKDOWN extension."""
        test_file = tmp_path / "test.MARKDOWN"
        test_file.write_text("# Title\n", encoding='utf-8')

        # Should not raise
        _validate_input(test_file)

    def test_validate_input_file_not_found(self, tmp_path):
        """Test validation raises FileNotFoundError for missing file."""
        test_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            _validate_input(test_file)

        assert "Input file not found" in str(exc_info.value)

    def test_validate_input_not_markdown(self, tmp_path):
        """Test validation raises ValueError for non-markdown file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content", encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            _validate_input(test_file)

        assert "must be a markdown file" in str(exc_info.value)


class TestExtractTitlesFromContent:
    """Tests for _extract_titles_from_content function."""

    def test_extract_titles_all_levels(self):
        """Test extraction of headings at all levels (H1-H6+)."""
        content = """# H1 Heading
Some content
## H2 Heading
More content
### H3 Heading
Even more
#### H4 Heading
Content
##### H5 Heading
More
###### H6 Heading
Final
####### H7 Heading (still extracted)
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 7
        assert titles[0] == "1: # H1 Heading"
        assert titles[1] == "3: ## H2 Heading"
        assert titles[2] == "5: ### H3 Heading"
        assert titles[3] == "7: #### H4 Heading"
        assert titles[4] == "9: ##### H5 Heading"
        assert titles[5] == "11: ###### H6 Heading"
        assert titles[6] == "13: ####### H7 Heading (still extracted)"

    def test_extract_titles_no_headings(self):
        """Test extraction with no headings returns empty list."""
        content = """Just some regular content
with no headings at all.
More content here.
"""
        titles = _extract_titles_from_content(content)

        assert titles == []

    def test_extract_titles_with_whitespace(self):
        """Test extraction handles whitespace correctly."""
        content = """#   Heading with spaces
## Heading with space
###  Multiple   spaces
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 3
        assert titles[0] == "1: #   Heading with spaces"
        assert titles[1] == "2: ## Heading with space"
        assert titles[2] == "3: ###  Multiple   spaces"

    def test_extract_titles_mixed_content(self):
        """Test extraction from content with headings and regular text."""
        content = """Some intro text
# First Heading
Content here
## Second Heading
More content
Regular paragraph
### Third Heading
Final content
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 3
        assert titles[0] == "2: # First Heading"
        assert titles[1] == "4: ## Second Heading"
        assert titles[2] == "7: ### Third Heading"

    def test_extract_titles_not_at_start_of_line(self):
        """Test that headings not at start of line are not extracted."""
        content = """Some text # Not a heading
# Real heading
  # Indented, not a heading
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 1
        assert titles[0] == "2: # Real heading"

    def test_extract_titles_empty_heading_text(self):
        """Test extraction of headings with minimal text (just # and space)."""
        content = """# 
## 
###  
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 3
        assert titles[0] == "1: # "
        assert titles[1] == "2: ## "
        assert titles[2] == "3: ###  "

    def test_extract_titles_malformed_headings(self):
        """Test that malformed headings (no space after #) are not extracted."""
        content = """#Not a heading (no space)
# Valid heading
##Also not a heading
## Valid heading
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 2
        assert titles[0] == "2: # Valid heading"
        assert titles[1] == "4: ## Valid heading"

    def test_extract_titles_multiple_same_level(self):
        """Test extraction of multiple headings at same level."""
        content = """# First H1
Content
# Second H1
More content
# Third H1
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 3
        assert titles[0] == "1: # First H1"
        assert titles[1] == "3: # Second H1"
        assert titles[2] == "5: # Third H1"

    def test_extract_titles_nested_structure(self):
        """Test extraction from nested heading structure."""
        content = """# Chapter 1
Content
## Section 1.1
Content
### Subsection 1.1.1
Content
## Section 1.2
Content
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 4
        assert titles[0] == "1: # Chapter 1"
        assert titles[1] == "3: ## Section 1.1"
        assert titles[2] == "5: ### Subsection 1.1.1"
        assert titles[3] == "7: ## Section 1.2"

    def test_extract_titles_single_heading(self):
        """Test extraction with single heading."""
        content = """# Only Heading
Content here
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 1
        assert titles[0] == "1: # Only Heading"

    def test_extract_titles_heading_at_end(self):
        """Test extraction when heading is at end of file."""
        content = """Content here
# Heading at end"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 1
        assert titles[0] == "2: # Heading at end"

    def test_extract_titles_heading_at_start(self):
        """Test extraction when heading is at start of file."""
        content = """# Heading at start
Content here"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 1
        assert titles[0] == "1: # Heading at start"

    def test_extract_titles_special_characters(self):
        """Test extraction handles special characters in headings."""
        content = """# Heading with "quotes"
## Heading with 'apostrophes'
### Heading with - dashes
#### Heading with _ underscores
##### Heading with (parentheses)
"""
        titles = _extract_titles_from_content(content)

        assert len(titles) == 5
        assert '"quotes"' in titles[0]
        assert "'apostrophes'" in titles[1]
        assert "- dashes" in titles[2]
        assert "_ underscores" in titles[3]
        assert "(parentheses)" in titles[4]


class TestExtractTitles:
    """Tests for extract_titles function."""

    def test_extract_titles_success(self, tmp_path):
        """Test successful title extraction from file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Title
Content
## Section
More content
""", encoding='utf-8')

        titles = extract_titles(test_file)

        assert len(titles) == 2
        assert titles[0] == "1: # Title"
        assert titles[1] == "3: ## Section"

    def test_extract_titles_string_path(self, tmp_path):
        """Test extraction accepts string path."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')

        titles = extract_titles(str(test_file))

        assert len(titles) == 1
        assert titles[0] == "1: # Title"

    def test_extract_titles_file_not_found(self, tmp_path):
        """Test extraction raises FileNotFoundError for missing file."""
        test_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            extract_titles(test_file)

        assert "Input file not found" in str(exc_info.value)

    def test_extract_titles_not_markdown(self, tmp_path):
        """Test extraction raises ValueError for non-markdown file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("# Title\n", encoding='utf-8')

        with pytest.raises(ValueError) as exc_info:
            extract_titles(test_file)

        assert "must be a markdown file" in str(exc_info.value)


class TestExtractTitlesToFile:
    """Tests for extract_titles_to_file function."""

    def test_extract_titles_to_file_default_output(self, tmp_path, monkeypatch):
        """Test extraction to file with default output path."""
        # Change to tmp_path for testing
        monkeypatch.chdir(tmp_path)
        
        test_file = tmp_path / "test.md"
        test_file.write_text("""# Title
Content
## Section
""", encoding='utf-8')

        output_path = extract_titles_to_file(test_file)

        # Default output should be in output/ directory
        expected_path = tmp_path / "output" / "test.titles.md"
        assert output_path == expected_path
        assert output_path.exists()

        content = output_path.read_text(encoding='utf-8')
        assert "# ALL TITLES IN DOC" in content
        assert "1: # Title" in content
        assert "3: ## Section" in content
        assert "```" in content

    def test_extract_titles_to_file_custom_output(self, tmp_path):
        """Test extraction to file with custom output path."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')

        custom_output = tmp_path / "custom" / "titles.md"
        output_path = extract_titles_to_file(test_file, custom_output)

        assert output_path == custom_output
        assert output_path.exists()

        content = output_path.read_text(encoding='utf-8')
        assert "1: # Title" in content

    def test_extract_titles_to_file_relative_uri(self, tmp_path):
        """Test that output file contains relative URI to input."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')

        output_path = tmp_path / "output" / "titles.md"
        extract_titles_to_file(test_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        # First line should be relative path
        assert lines[0].startswith("./") or "test.md" in lines[0]

    def test_extract_titles_to_file_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Title\n", encoding='utf-8')

        nested_output = tmp_path / "nested" / "deep" / "titles.md"
        output_path = extract_titles_to_file(test_file, nested_output)

        assert output_path.exists()
        assert nested_output.parent.exists()

    def test_extract_titles_to_file_empty_content(self, tmp_path):
        """Test extraction to file with no headings."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Just content, no headings\n", encoding='utf-8')

        output_path = tmp_path / "titles.md"
        extract_titles_to_file(test_file, output_path)

        content = output_path.read_text(encoding='utf-8')
        # Should still create file with header and empty code block
        assert "# ALL TITLES IN DOC" in content
        assert "```" in content


class TestHashMismatchError:
    """Tests for HashMismatchError exception."""

    def test_hash_mismatch_error_creation(self):
        """Test HashMismatchError can be created with stored and current hash."""
        error = HashMismatchError("stored_hash_123", "current_hash_456")

        assert error.stored_hash == "stored_hash_123"
        assert error.current_hash == "current_hash_456"
        assert "stored_hash_123" in str(error)
        assert "current_hash_456" in str(error)


class TestExtractTitlesFromWork:
    """Tests for extract_titles_from_work function."""

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.set_file_readonly')
    @patch('vulcanlab.sanitization.extract_titles.set_file_writable')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_success(
        self, mock_get_session, mock_set_writable, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test successful title extraction from work."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        markdown_hash = "markdown_hash_123"
        titles_hash = "titles_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": markdown_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("""# Title
Content
## Section
""", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return markdown_hash
            else:
                return titles_hash
        mock_compute_hash.side_effect = hash_side_effect

        result_path = extract_titles_from_work(
            work_id=1,
            source_key='original_markdown',
            verbose=False
        )

        # Verify output file was created
        expected_path = tmp_path / "test.titles.md"
        assert result_path == expected_path
        assert expected_path.exists()

        # Verify content
        content = expected_path.read_text(encoding='utf-8')
        assert "1: # Title" in content
        assert "3: ## Section" in content

        # Verify database was updated
        mock_session.refresh.assert_called_once_with(work)
        assert "titles" in work.files
        assert work.files["titles"]["hash"] == titles_hash

        # Verify file was set to read-only
        mock_set_readonly.assert_called_once_with(expected_path)

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.set_file_readonly')
    @patch('vulcanlab.sanitization.extract_titles.set_file_writable')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_sanitized_source(
        self, mock_get_session, mock_set_writable, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test extraction from sanitized source."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        sanitized_path = tmp_path / "test.sanitized.md"
        sanitized_hash = "sanitized_hash_123"
        titles_hash = "titles_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "sanitized": {
                    "path": str(sanitized_path),
                    "hash": sanitized_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        sanitized_path.write_text("# Title\n", encoding='utf-8')

        def hash_side_effect(path):
            if path == sanitized_path:
                return sanitized_hash
            else:
                return titles_hash
        mock_compute_hash.side_effect = hash_side_effect

        result_path = extract_titles_from_work(
            work_id=1,
            source_key='sanitized',
            verbose=False
        )

        # Should create test.sanitized.titles.md
        expected_path = tmp_path / "test.sanitized.titles.md"
        assert result_path == expected_path

        # Verify database was updated with sanitized_titles key
        mock_session.refresh.assert_called_once_with(work)
        assert "sanitized_titles" in work.files

    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_not_found(self, mock_get_session, mock_session):
        """Test that missing work raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            extract_titles_from_work(work_id=999, source_key='original_markdown')

        assert "Work with ID 999 not found" in str(exc_info.value)

    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_no_files(self, mock_get_session, mock_session):
        """Test that work without files raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(id=1, title="Test Work", files=None)
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            extract_titles_from_work(work_id=1, source_key='original_markdown')

        assert "has no files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_invalid_source_key(self, mock_get_session, mock_session, tmp_path):
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
            extract_titles_from_work(work_id=1, source_key='invalid_key')

        assert "Invalid source_key" in str(exc_info.value)
        assert "Must be 'original_markdown' or 'sanitized'" in str(exc_info.value)

    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_missing_source_file(self, mock_get_session, mock_session, tmp_path):
        """Test that missing source file in metadata raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        work = Work(
            id=1,
            title="Test Work",
            files={"other_file": {"path": str(tmp_path / "test.md"), "hash": "hash"}}
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(ValueError) as exc_info:
            extract_titles_from_work(work_id=1, source_key='original_markdown')

        assert "does not have 'original_markdown' in files metadata" in str(exc_info.value)

    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_file_not_found_on_disk(self, mock_get_session, mock_session, tmp_path):
        """Test that missing file on disk raises FileNotFoundError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "nonexistent.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "hash"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        with pytest.raises(FileNotFoundError) as exc_info:
            extract_titles_from_work(work_id=1, source_key='original_markdown')

        assert "File not found on disk" in str(exc_info.value)

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_hash_mismatch(
        self, mock_get_session, mock_compute_hash, tmp_path, mock_session
    ):
        """Test that hash mismatch raises HashMismatchError."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "stored_hash_123"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\n", encoding='utf-8')

        # Return different hash
        mock_compute_hash.return_value = "current_hash_456"

        with pytest.raises(HashMismatchError) as exc_info:
            extract_titles_from_work(work_id=1, source_key='original_markdown', force=False)

        assert exc_info.value.stored_hash == "stored_hash_123"
        assert exc_info.value.current_hash == "current_hash_456"

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.set_file_readonly')
    @patch('vulcanlab.sanitization.extract_titles.set_file_writable')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_hash_mismatch_force(
        self, mock_get_session, mock_set_writable, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test that hash mismatch with force=True proceeds anyway."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": "stored_hash_123"
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# Title\n", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return "current_hash_456"  # Different from stored
            else:
                return "titles_hash"
        mock_compute_hash.side_effect = hash_side_effect

        # Should not raise error with force=True
        result_path = extract_titles_from_work(
            work_id=1,
            source_key='original_markdown',
            force=True,
            verbose=False
        )

        assert result_path.exists()

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.set_file_readonly')
    @patch('vulcanlab.sanitization.extract_titles.set_file_writable')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_overwrite_existing(
        self, mock_get_session, mock_set_writable, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test that existing titles file is overwritten."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        titles_path = tmp_path / "test.titles.md"
        markdown_hash = "markdown_hash_123"
        titles_hash = "titles_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": markdown_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("# New Title\n", encoding='utf-8')
        # Create existing titles file
        titles_path.write_text("# OLD TITLES\n", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return markdown_hash
            else:
                return titles_hash
        mock_compute_hash.side_effect = hash_side_effect

        result_path = extract_titles_from_work(
            work_id=1,
            source_key='original_markdown',
            verbose=False
        )

        # Verify file was made writable before overwrite
        mock_set_writable.assert_called_once_with(titles_path)

        # Verify content was updated
        content = titles_path.read_text(encoding='utf-8')
        assert "# New Title" in content or "1: # New Title" in content
        assert "# OLD TITLES" not in content

    @patch('vulcanlab.sanitization.extract_titles.compute_file_hash')
    @patch('vulcanlab.sanitization.extract_titles.set_file_readonly')
    @patch('vulcanlab.sanitization.extract_titles.set_file_writable')
    @patch('vulcanlab.sanitization.extract_titles.get_session')
    def test_extract_titles_from_work_no_headings(
        self, mock_get_session, mock_set_writable, mock_set_readonly,
        mock_compute_hash, tmp_path, mock_session
    ):
        """Test extraction from work with no headings."""
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value.__exit__.return_value = None

        markdown_path = tmp_path / "test.md"
        markdown_hash = "markdown_hash_123"
        titles_hash = "titles_hash_456"

        work = Work(
            id=1,
            title="Test Work",
            files={
                "original_markdown": {
                    "path": str(markdown_path),
                    "hash": markdown_hash
                }
            }
        )
        mock_session.query.return_value.filter.return_value.first.return_value = work
        mock_session.get.return_value = work

        markdown_path.write_text("Just content, no headings\n", encoding='utf-8')

        def hash_side_effect(path):
            if path == markdown_path:
                return markdown_hash
            else:
                return titles_hash
        mock_compute_hash.side_effect = hash_side_effect

        result_path = extract_titles_from_work(
            work_id=1,
            source_key='original_markdown',
            verbose=False
        )

        # File should still be created
        assert result_path.exists()

        # Content should have header but no titles
        content = result_path.read_text(encoding='utf-8')
        assert "# ALL TITLES IN DOC" in content
        assert "```" in content
