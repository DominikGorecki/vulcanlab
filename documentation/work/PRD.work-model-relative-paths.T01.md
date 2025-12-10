COMPLETE

# T01: Implement PathResolver utility and Work model path helpers

## Context

- **PRD:** [PRD.work-model-relative-paths.md](PRD.work-model-relative-paths.md)
- **PRD Sections:** Section 5.1 FR1 (Path Utility Module), FR2 (Work Model Property Setters)
- **Business Value:** Establishes the core infrastructure for environment-portable path management, enabling database dumps to be moved seamlessly between local, Docker, and production environments without path rewriting.

## Outcome

The PathResolver utility class is fully implemented with config caching, and the Work model has helper methods for setting/resolving paths. All unit tests pass, validating path resolution logic, filename extraction, and error handling for NULL values.

## Scope

### In scope:
- Implement `PathResolver` class in `src/vulcanlab/utils/file_utils.py`
  - Load and cache `input_dir` and `output_dir` from `vulcanlab.config.json`
  - Provide `resolve_work_path(work, key)` method that returns Path objects
  - Handle special case: `files["original_file"]["path"]` uses `input_dir`, all others use `output_dir`
  - Throw custom `InvalidFilePathError` for NULL/empty filenames with context (Work ID, field name)
- Create custom exception `InvalidFilePathError` in `src/vulcanlab/utils/exceptions.py` (create file if needed)
- Add helper methods to Work model (`src/vulcanlab/data/models/work.py`):
  - `set_markdown_path(value)`: Extract filename from full path and store
  - `set_file_path(file_key, value)`: Extract filename and update `files[file_key]["path"]`
- Implement singleton pattern or module-level caching for PathResolver via `get_path_resolver()` function
- Comprehensive unit tests for all functionality

### Out of scope:
- Updating existing code to use the new utilities (handled in T03-T06)
- Database migration (handled in T02)
- Changes to the deprecated `source_path` field

## Implementation plan

### Backend

#### 1. Custom Exception Class
**File:** `src/vulcanlab/utils/exceptions.py` (create if doesn't exist)

```python
class InvalidFilePathError(Exception):
    """Raised when a file path is NULL, empty, or invalid."""

    def __init__(self, message: str, work_id: int = None, field_name: str = None):
        self.work_id = work_id
        self.field_name = field_name
        super().__init__(message)
```

#### 2. PathResolver Utility Class
**File:** `src/vulcanlab/utils/file_utils.py` (extend existing file)

Add imports:
```python
import json
from pathlib import Path
from typing import Optional
from .exceptions import InvalidFilePathError
```

Implement `PathResolver` class:
```python
class PathResolver:
    """
    Resolves Work model filenames to absolute paths using config-based directories.

    Caches input_dir and output_dir from vulcanlab.config.json at initialization.
    Thread-safe singleton pattern via get_path_resolver().
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize PathResolver from config file.

        Args:
            config_path: Path to config file (defaults to vulcanlab.config.json at project root)

        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If config missing required paths.input_dir or paths.output_dir
        """
        if config_path is None:
            # Assume config at project root (4 levels up from utils/)
            config_path = Path(__file__).parent.parent.parent.parent / "vulcanlab.config.json"

        with open(config_path, 'r') as f:
            config = json.load(f)

        self.input_dir = Path(config["paths"]["input_dir"])
        self.output_dir = Path(config["paths"]["output_dir"])

    def resolve_work_path(self, work, key: Optional[str] = None) -> Path:
        """
        Resolve a Work model path field to absolute Path.

        Args:
            work: Work model instance
            key: Key in work.files JSON (e.g., "sanitized", "original_file").
                 If None, resolves work.markdown_path instead.

        Returns:
            Absolute Path object

        Raises:
            InvalidFilePathError: If filename is NULL or empty

        Examples:
            resolver.resolve_work_path(work, "sanitized")
            resolver.resolve_work_path(work, "original_file")
            resolver.resolve_work_path(work)  # Resolves markdown_path
        """
        if key is None:
            # Resolve markdown_path
            filename = work.markdown_path
            if not filename:
                raise InvalidFilePathError(
                    f"Work {work.id}: markdown_path is NULL or empty",
                    work_id=work.id,
                    field_name="markdown_path"
                )
            base_dir = self.output_dir
        else:
            # Resolve files[key]["path"]
            if not work.files or key not in work.files:
                raise InvalidFilePathError(
                    f"Work {work.id}: files['{key}'] does not exist",
                    work_id=work.id,
                    field_name=f"files.{key}"
                )

            file_info = work.files[key]
            filename = file_info.get("path")

            if not filename:
                raise InvalidFilePathError(
                    f"Work {work.id}: files['{key}']['path'] is NULL or empty",
                    work_id=work.id,
                    field_name=f"files.{key}.path"
                )

            # Determine base directory
            base_dir = self.input_dir if key == "original_file" else self.output_dir

        return base_dir / filename
```

Implement singleton accessor:
```python
_path_resolver_instance = None

def get_path_resolver(config_path: Path = None) -> PathResolver:
    """
    Get or create the singleton PathResolver instance.

    Args:
        config_path: Optional config path (only used on first call)

    Returns:
        Cached PathResolver instance
    """
    global _path_resolver_instance
    if _path_resolver_instance is None:
        _path_resolver_instance = PathResolver(config_path)
    return _path_resolver_instance
```

#### 3. Work Model Helper Methods
**File:** `src/vulcanlab/data/models/work.py`

Add import at top:
```python
from pathlib import Path
```

Add helper methods to the `Work` class (after the relationship definition, before `__repr__`):

```python
def set_markdown_path(self, value: str) -> None:
    """
    Set markdown_path, automatically extracting filename from full path.

    Args:
        value: Full path or filename

    Examples:
        work.set_markdown_path("/full/path/file.md")  # Stores "file.md"
        work.set_markdown_path("file.md")             # Stores "file.md"
    """
    if value:
        self.markdown_path = Path(value).name
    else:
        self.markdown_path = value

def set_file_path(self, file_key: str, value: str, file_hash: str = None) -> None:
    """
    Set a path in the files JSON field, automatically extracting filename.

    Args:
        file_key: Key in files dict (e.g., "sanitized", "original_file")
        value: Full path or filename
        file_hash: Optional hash to update alongside path

    Examples:
        work.set_file_path("sanitized", "/full/path/file.md", "abc123...")
        work.set_file_path("original_file", "input.pdf")
    """
    if not self.files:
        self.files = {}

    filename = Path(value).name if value else value

    if file_key not in self.files:
        self.files[file_key] = {}

    self.files[file_key]["path"] = filename

    if file_hash is not None:
        self.files[file_key]["hash"] = file_hash
```

### Frontend
Not applicable - backend-only ticket.

### Other / cross-cutting

- **Configuration dependency:** Code assumes `vulcanlab.config.json` exists at project root with valid `paths.input_dir` and `paths.output_dir` entries
- **Thread safety:** Singleton pattern should be thread-safe for read operations (config cached at init)
- **Logging:** Consider adding debug logging in PathResolver for troubleshooting path resolution issues

## Unit tests

**Test file:** `tests/unit/test_path_resolver.py` (create new file)

Use pytest framework following existing repo patterns.

### Test cases for PathResolver:

1. **test_path_resolver_loads_config**
   - Verify PathResolver loads config and caches input_dir and output_dir correctly
   - Assert paths are Path objects

2. **test_path_resolver_singleton**
   - Call `get_path_resolver()` twice
   - Assert same instance returned (singleton pattern)

3. **test_resolve_markdown_path_success**
   - Create Work with `markdown_path = "test.md"`
   - Call `resolver.resolve_work_path(work)`
   - Assert returns `Path(output_dir / "test.md")`

4. **test_resolve_file_path_output_dir**
   - Create Work with `files = {"sanitized": {"path": "test_sanitized.md"}}`
   - Call `resolver.resolve_work_path(work, "sanitized")`
   - Assert returns `Path(output_dir / "test_sanitized.md")`

5. **test_resolve_file_path_input_dir**
   - Create Work with `files = {"original_file": {"path": "input.pdf"}}`
   - Call `resolver.resolve_work_path(work, "original_file")`
   - Assert returns `Path(input_dir / "input.pdf")`

6. **test_resolve_markdown_path_null_raises_error**
   - Create Work with `markdown_path = None`
   - Assert `resolver.resolve_work_path(work)` raises `InvalidFilePathError`
   - Assert exception contains work.id and field name

7. **test_resolve_markdown_path_empty_raises_error**
   - Create Work with `markdown_path = ""`
   - Assert raises `InvalidFilePathError`

8. **test_resolve_file_path_missing_key_raises_error**
   - Create Work with `files = {}`
   - Assert `resolver.resolve_work_path(work, "nonexistent")` raises `InvalidFilePathError`

9. **test_resolve_file_path_null_value_raises_error**
   - Create Work with `files = {"sanitized": {"path": None}}`
   - Assert raises `InvalidFilePathError`

10. **test_resolve_file_path_empty_value_raises_error**
    - Create Work with `files = {"sanitized": {"path": ""}}`
    - Assert raises `InvalidFilePathError`

11. **test_path_resolver_config_not_found**
    - Create PathResolver with non-existent config path
    - Assert raises `FileNotFoundError`

12. **test_path_resolver_config_missing_paths**
    - Create temp config file missing `paths.input_dir`
    - Assert raises `KeyError`

**Test file:** `tests/unit/test_work_model_path_helpers.py` (create new file)

### Test cases for Work model helpers:

1. **test_set_markdown_path_extracts_filename_linux**
   - Create Work instance
   - Call `work.set_markdown_path("/home/user/data/file.md")`
   - Assert `work.markdown_path == "file.md"`

2. **test_set_markdown_path_extracts_filename_windows**
   - Call `work.set_markdown_path("C:\\data\\file.md")`
   - Assert `work.markdown_path == "file.md"`

3. **test_set_markdown_path_plain_filename**
   - Call `work.set_markdown_path("file.md")`
   - Assert `work.markdown_path == "file.md"`

4. **test_set_markdown_path_none**
   - Call `work.set_markdown_path(None)`
   - Assert `work.markdown_path is None`

5. **test_set_file_path_extracts_filename**
   - Create Work with `files = None`
   - Call `work.set_file_path("sanitized", "/full/path/file.md", "hash123")`
   - Assert `work.files == {"sanitized": {"path": "file.md", "hash": "hash123"}}`

6. **test_set_file_path_updates_existing_key**
   - Create Work with `files = {"sanitized": {"path": "old.md", "hash": "old_hash"}}`
   - Call `work.set_file_path("sanitized", "/new/path/new.md", "new_hash")`
   - Assert `work.files["sanitized"] == {"path": "new.md", "hash": "new_hash"}`

7. **test_set_file_path_no_hash_preserves_existing**
   - Create Work with `files = {"sanitized": {"path": "old.md", "hash": "old_hash"}}`
   - Call `work.set_file_path("sanitized", "new.md")` (no hash arg)
   - Assert `work.files["sanitized"]["path"] == "new.md"`
   - Assert `work.files["sanitized"]["hash"] == "old_hash"` (preserved)

8. **test_set_file_path_creates_files_dict**
   - Create Work with `files = None`
   - Call `work.set_file_path("original_file", "input.pdf")`
   - Assert `work.files == {"original_file": {"path": "input.pdf"}}`

### Test fixtures:
- Create fixtures for mock Work instances with various path configurations
- Consider using pytest's `tmp_path` fixture for config file tests

## Dependencies and sequencing

### Dependencies:
- None - this is the foundational ticket

### Blocks:
- T02: Database migration (needs PathResolver to validate migration results)
- T03: Conversion modules update
- T04: Sanitization modules update
- T05: Chunking modules update
- T06: Augmentation/Retrieval/API modules update

### Rollout notes:
- This ticket can be merged without breaking existing code (additive changes only)
- Existing code continues using absolute paths until T03-T06 updates are complete
- Migration (T02) should run only after all code updates (T03-T06) are deployed

## Manual test plan

After implementation, manually verify:

1. **Config loading:**
   - Start Python REPL
   - Import and call `get_path_resolver()`
   - Verify no errors and paths are cached

2. **Path resolution:**
   - Query a Work record from database (with existing absolute paths)
   - Call `resolver.resolve_work_path(work, "sanitized")`
   - Verify it constructs path using `output_dir + filename`

3. **Helper methods:**
   - Create new Work instance
   - Call `work.set_markdown_path("/tmp/test.md")`
   - Verify `work.markdown_path == "test.md"`
   - Call `work.set_file_path("sanitized", "/tmp/san.md", "hash")`
   - Verify `work.files == {"sanitized": {"path": "san.md", "hash": "hash"}}`

4. **Error handling:**
   - Create Work with `markdown_path = None`
   - Attempt `resolver.resolve_work_path(work)`
   - Verify `InvalidFilePathError` raised with clear message

## Clarifications and assumptions

### Assumptions:
1. **Config location:** Assuming `vulcanlab.config.json` is always 4 directory levels up from `src/vulcanlab/utils/file_utils.py` (i.e., at project root)
2. **Path object return:** `resolve_work_path()` returns `Path` objects (not strings) to match existing code patterns that use `Path(work.markdown_path)`
3. **Hash handling:** `set_file_path()` optionally accepts hash parameter for convenience, but doesn't compute hashes (caller's responsibility)
4. **Thread safety:** Singleton pattern is read-only after initialization, so no explicit threading locks needed
5. **Existing exceptions module:** If `src/vulcanlab/utils/exceptions.py` doesn't exist, create it as a new module

### Open questions (non-blocking):
1. Should PathResolver support reloading config at runtime (e.g., for testing different configs)?
   - *Current assumption:* No, singleton pattern caches config for application lifetime
2. Should `set_markdown_path()` and `set_file_path()` validate that the extracted filename is non-empty?
   - *Current assumption:* No validation, store whatever Path.name returns (empty string for edge cases)

### Before implementing:
Review this ticket with the product owner. Confirm the singleton pattern and Path return type align with the codebase's existing patterns. If there are concerns about thread safety or config reloading, discuss before implementation.
