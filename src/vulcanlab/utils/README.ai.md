# src/vulcanlab/utils

**Purpose**: General-purpose utility modules providing cross-cutting functionality for file operations, compression, LLM configuration, citation parsing, and RAG configuration management across the Vulcanlab application.

## Module Overview

### File Operations

#### [file_utils.py](file_utils.py)
Cross-platform file utilities for hash computation, permission management, and path resolution.

**Key Components**:
- `compute_file_hash(file_path: Path) -> str` - Compute SHA-256 hash of a file
- `set_file_readonly(file_path: Path) -> None` - Make file read-only (Windows/Linux)
- `set_file_writable(file_path: Path) -> None` - Remove read-only flag
- `is_file_readonly(file_path: Path) -> bool` - Check file permissions
- `PathResolver` class - Singleton for resolving Work model filenames to absolute paths
  - Caches `input_dir` and `output_dir` from `vulcanlab.config.json`
  - `resolve_work_path(work, key: Optional[str]) -> Path` - Resolve work.files[key]['path'] or work.markdown_path
  - Thread-safe singleton via `get_path_resolver(config_path: Path = None) -> PathResolver`

**Dependencies**: `hashlib`, `stat`, `pathlib`, custom exceptions

#### [file_utils_cli.py](file_utils_cli.py)
Command-line interface for file utility operations.

**Commands**:
- `hash <file>` - Compute SHA-256 hash
- `readonly <file>` - Set file to read-only
- `writable <file>` - Set file to writable
- `check <file>` - Check if file is read-only

**Usage**: `python -m vulcanlab.utils.file_utils_cli <command> <file>`

### Data Compression

#### [compression.py](compression.py)
Automatic compression for large markdown content to save database space.

**Key Functions**:
- `compress_if_large(content: Union[str, bytes]) -> bytes` - Auto-compress content >1MB using gzip
- `decompress_if_needed(data: Union[bytes, str]) -> str` - Safely decompress or decode content
- `COMPRESSION_THRESHOLD = 1024 * 1024` (1MB)

**Features**:
- Handles both string and byte inputs
- Graceful fallback for uncompressed data
- Automatic detection of compressed vs uncompressed content

### LLM & AI Configuration

#### [model_info.py](model_info.py)
Retrieve active LLM configuration without exposing sensitive API keys.

**Key Components**:
- `ActiveLLMInfo` dataclass - Container for provider and model names
  - `provider: str` - LLM provider (e.g., 'openai', 'gemini')
  - `light_model: str` - Model for light/fast tasks
  - `full_model: str` - Model for full/complex tasks
- `get_active_llm_info() -> ActiveLLMInfo` - Get current LLM settings from config

**Dependencies**: `vulcanlab.ai.config.LLMSettings`, `ModelTier`

#### [model_info_cli.py](model_info_cli.py)
CLI to display active LLM configuration in formatted ASCII table.

**Features**:
- `format_table(headers: list[str], rows: list[list[str]]) -> str` - ASCII table formatter
- Displays provider, light model, and full model information

**Usage**: `python -m vulcanlab.utils.model_info_cli`

#### [llm_citation_parser.py](llm_citation_parser.py)
LLM-based citation parsing for extracting bibliographic metadata.

**Key Components**:
- `Citation` Pydantic model - Structured bibliographic data
  - Fields: title, authors, year, publisher, isbn, doi, container_title, volume, issue, pages, url, work_type
  - All fields optional to support partial extraction
- `parse_citation_with_llm(citation_text: str, citation_format: str, settings: LLMSettings = None) -> Citation`
  - Supports APA, MLA, Chicago formats
  - Uses LIGHT tier LLM for extraction
  - Returns structured Citation object

**Dependencies**: `pydantic`, `vulcanlab.ai.config`, `vulcanlab.ai.llm_factory`

### RAG Configuration

#### [rag_config_loader.py](rag_config_loader.py)
Load RAG configuration presets from database for retrieval, consolidation, and augmentation modules.

**Key Functions**:
- `get_default_config() -> dict` - Get default RAG preset (marked as default in DB)
- `get_config_by_name(preset_name: str) -> dict` - Load specific preset by name
- `get_all_preset_names() -> list[str]` - List all available preset names

**Returns**: Dict with keys: `"retrieval"`, `"consolidation"`, `"augmentation"`

**Dependencies**: `sqlalchemy.orm.Session`, `vulcanlab.data.database`, `vulcanlab.data.models.rag_config.RagConfig`

### Exceptions

#### [exceptions.py](exceptions.py)
Custom exception classes for utility modules.

**Classes**:
- `InvalidFilePathError(Exception)` - Raised when file paths are NULL, empty, or invalid
  - Attributes: `work_id: int`, `field_name: str`

## Public API

Exported via `__init__.py`:
- `compute_file_hash`
- `is_file_readonly`
- `set_file_readonly`
- `set_file_writable`
- `ActiveLLMInfo`
- `get_active_llm_info`

## Design Patterns

1. **Singleton Pattern**: `PathResolver` uses thread-safe singleton for config caching
2. **Cross-platform Compatibility**: File permission utilities work on both Windows and Linux using `stat` module
3. **Graceful Degradation**: Compression utilities handle both compressed and uncompressed data transparently
4. **CLI Integration**: Multiple modules provide CLI entry points for standalone usage
5. **Type Safety**: Extensive use of Pydantic models for structured data validation
6. **Database Integration**: RAG config loader uses SQLAlchemy session management with context managers

## Usage Examples

### File Operations
```python
from vulcanlab.utils import compute_file_hash, set_file_readonly
from vulcanlab.utils.file_utils import get_path_resolver

# Compute file hash
hash_value = compute_file_hash(Path("document.md"))

# Set file permissions
set_file_readonly(Path("document.md"))

# Resolve Work model paths
resolver = get_path_resolver()
sanitized_path = resolver.resolve_work_path(work, "sanitized")
markdown_path = resolver.resolve_work_path(work)  # Resolves markdown_path
```

### Compression
```python
from vulcanlab.utils.compression import compress_if_large, decompress_if_needed

# Auto-compress large content
compressed = compress_if_large("large markdown content...")

# Auto-decompress when reading
content = decompress_if_needed(compressed)
```

### LLM Configuration
```python
from vulcanlab.utils import get_active_llm_info

# Get current LLM settings
info = get_active_llm_info()
print(f"Provider: {info.provider}")
print(f"Light Model: {info.light_model}")
print(f"Full Model: {info.full_model}")
```

### Citation Parsing
```python
from vulcanlab.utils.llm_citation_parser import parse_citation_with_llm

citation_text = "Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252."
result = parse_citation_with_llm(citation_text, "APA")

print(result.title)      # "Prediction, perception and agency"
print(result.authors)    # ["Friston, K."]
print(result.year)       # 2012
print(result.pages)      # "248-252"
```

### RAG Configuration
```python
from vulcanlab.utils.rag_config_loader import get_default_config, get_config_by_name

# Get default configuration
config = get_default_config()
dense_limit = config["retrieval"]["dense_limit"]
coverage_threshold = config["consolidation"]["coverage_threshold"]

# Load specific preset
fast_config = get_config_by_name("Fast")
```

## Dependencies

**Core**: `pathlib`, `hashlib`, `stat`, `json`, `gzip`, `logging`

**Third-party**: `pydantic`, `sqlalchemy`

**Internal**:
- `vulcanlab.ai.config` (LLMSettings, ModelTier)
- `vulcanlab.ai.llm_factory` (create_langchain_chat)
- `vulcanlab.data.database` (get_session)
- `vulcanlab.data.models.rag_config` (RagConfig)

## Testing

CLI modules can be tested via command-line execution:
```bash
# File utilities
python -m vulcanlab.utils.file_utils_cli hash document.md
python -m vulcanlab.utils.file_utils_cli readonly document.md
python -m vulcanlab.utils.file_utils_cli check document.md

# Model info
python -m vulcanlab.utils.model_info_cli
```

## Notes

- **PathResolver Configuration**: Assumes `vulcanlab.config.json` at project root (4 levels up from utils/)
- **Compression Threshold**: Set to 1MB, configurable via `COMPRESSION_THRESHOLD` constant
- **Citation Parsing**: Uses LIGHT tier LLM to minimize cost for simple extraction tasks
- **RAG Config**: Raises `RuntimeError` if no default preset exists in database
- **File Permissions**: Uses `stat` module constants for cross-platform compatibility
