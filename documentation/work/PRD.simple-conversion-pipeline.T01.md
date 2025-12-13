# T01: Database Schema & Migrations for Simple Conversion

## Context

- **PRD:** [PRD.simple-conversion-pipeline.md](./PRD.simple-conversion-pipeline.md)
- **Relevant sections:** FR7 (Database Schema), FR1.6 (ParsedMarkdown storage), FR2.7 (SanitizedMarkdown storage), FR3.8 (HeadingModifications storage), FR7.4 (Template seeding)
- **Business motivation:** Enable storage of all simple conversion artifacts (parsed markdown, sanitized markdown, heading modifications, and prompt templates) in the database, eliminating dependency on output folder files. This is foundational infrastructure for the entire simple conversion pipeline.

## Outcome

Three new database tables (`parsed_markdown`, `sanitized_markdown`, `heading_modifications`) exist with proper indexes and foreign key constraints. The `io_files` table has a new `simple_conversion` boolean flag. Two new prompt templates (`simple_sanitize_small` and `simple_sanitize_large`) are seeded in the `prompt_templates` table. All models are integrated into `init_db.py` for fresh installs. A migration script (`016_simple_conversion_tables.sql`) exists for upgrading existing databases.

## Scope

### In scope:
- Create `parsed_markdown` table with SQLAlchemy Python ENUMs for `file_type` (pdf/epub) and `classification` (small/large)
- Create `sanitized_markdown` table with automatic compression/decompression for `content` field (all markdown >1MB)
- Create `heading_modifications` table with SQLAlchemy Python ENUM for `action` (remove/change/keep)
- Add `simple_conversion` boolean flag to `io_files` table
- Add compression logic to getters/setters for all markdown content fields
- Create SQLAlchemy models for all three new tables
- Add models to `init_db.py` imports for fresh database creation
- Create SQL migration script `migrations/016_simple_conversion_tables.sql`
- Seed two new prompt templates in migration script AND in `init_db.py` seed function
- Add indexes on `work_id` for all new tables (frequent foreign key lookups)
- Update `Work.processing_status` JSON structure documentation

### Out of scope:
- API endpoints to interact with these tables (handled in T07)
- Business logic for populating these tables (handled in T03, T04, T05)
- Frontend UI to display this data (handled in T08-T11)
- Data migration from existing conversion data to new schema

## Implementation Plan

### Backend - Database Schema

**1. Create Python ENUMs**

File: `src/vulcanlab/data/models/enums.py` (new file or add to existing)

```python
import enum

class FileType(str, enum.Enum):
    """File type for parsed markdown."""
    PDF = 'pdf'
    EPUB = 'epub'

class DocumentClassification(str, enum.Enum):
    """Document size classification."""
    SMALL = 'small'
    LARGE = 'large'

class ModificationAction(str, enum.Enum):
    """Heading modification action."""
    REMOVE = 'remove'
    CHANGE = 'change'
    KEEP = 'keep'
```

**2. Create Compression Utilities**

File: `src/vulcanlab/utils/compression.py` (new file)

```python
"""
Compression utilities for markdown content storage.

Automatically compresses content >1MB to save database space.
Handles both string and byte inputs robustly.
"""
import gzip
import logging
from typing import Union

logger = logging.getLogger(__name__)

# Compression threshold: 1MB
COMPRESSION_THRESHOLD = 1024 * 1024


def compress_if_large(content: Union[str, bytes]) -> bytes:
    """
    Compress content if larger than threshold.

    Args:
        content: Markdown string or raw bytes

    Returns:
        Compressed bytes (if > threshold) or original bytes
    """
    if content is None:
        return b''

    # Standardize to bytes
    if isinstance(content, str):
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content

    if len(content_bytes) > COMPRESSION_THRESHOLD:
        compressed = gzip.compress(content_bytes)
        logger.debug(f"Compressed {len(content_bytes)} bytes to {len(compressed)} bytes")
        return compressed

    return content_bytes


def decompress_if_needed(data: Union[bytes, str]) -> str:
    """
    Decompress data if it was compressed, otherwise decode.

    Args:
        data: Bytes from database or string

    Returns:
        Decompressed markdown string
    """
    if data is None:
        return ''

    # If it's already a string, return it
    if isinstance(data, str):
        return data

    # Try to decompress; if it fails, assume it's uncompressed
    try:
        decompressed = gzip.decompress(data)
        logger.debug(f"Decompressed {len(data)} bytes to {len(decompressed)} bytes")
        return decompressed.decode('utf-8')
    except (gzip.BadGzipFile, OSError):
        # OSError can occur with truncated or invalid gzip data
        # Assume it's uncompressed utf-8 text
        return data.decode('utf-8')
```

**3. Create ParsedMarkdown Model**

File: `src/vulcanlab/data/models/parsed_markdown.py` (new file)

```python
"""ParsedMarkdown model for storing conversion output."""

from sqlalchemy import Column, Integer, Text, Enum as SQLEnum, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import validates

from ..database import Base
from .enums import FileType, DocumentClassification
from ...utils.compression import compress_if_large, decompress_if_needed


class ParsedMarkdown(Base):
    """Stores markdown output from PDF/EPUB conversion."""

    __tablename__ = 'parsed_markdown'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    _content = Column('content', LargeBinary, nullable=False)  # Stored as bytes (compressed if >1MB)
    file_type = Column(SQLEnum(FileType), nullable=False)
    classification = Column(SQLEnum(DocumentClassification), nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_parsed_markdown_work_id', 'work_id'),
    )

    @property
    def content(self) -> str:
        """Get decompressed content."""
        return decompress_if_needed(self._content)

    @content.setter
    def content(self, value: str):
        """Set content with automatic compression."""
        self._content = compress_if_large(value)

    def __repr__(self):
        return f"<ParsedMarkdown(id={self.id}, work_id={self.work_id}, classification={self.classification.value})>"
```

**4. Create SanitizedMarkdown Model**

File: `src/vulcanlab/data/models/sanitized_markdown.py` (new file)

```python
"""SanitizedMarkdown model for storing LLM-cleaned markdown."""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.sql import func

from ..database import Base
from ...utils.compression import compress_if_large, decompress_if_needed


class SanitizedMarkdown(Base):
    """Stores sanitized markdown from Step 2A or 2B."""

    __tablename__ = 'sanitized_markdown'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    _content = Column('content', LargeBinary, nullable=False)  # Stored as bytes (compressed if >1MB)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_sanitized_markdown_work_id', 'work_id'),
    )

    @property
    def content(self) -> str:
        """Get decompressed content."""
        return decompress_if_needed(self._content)

    @content.setter
    def content(self, value: str):
        """Set content with automatic compression."""
        self._content = compress_if_large(value)

    def __repr__(self):
        return f"<SanitizedMarkdown(id={self.id}, work_id={self.work_id}, token_count={self.token_count})>"
```

**5. Create HeadingModifications Model**

File: `src/vulcanlab/data/models/heading_modifications.py` (new file)

```python
"""HeadingModifications model for storing large document heading changes."""

from sqlalchemy import Column, Integer, Text, Boolean, Enum as SQLEnum, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from ..database import Base
from .enums import ModificationAction


class HeadingModification(Base):
    """Stores heading-level modifications for Step 2B (large documents)."""

    __tablename__ = 'heading_modifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id', ondelete='CASCADE'), nullable=False)
    line_number = Column(Integer, nullable=False)
    original_heading = Column(Text, nullable=False)
    modified_heading = Column(Text, nullable=True)  # Null if action=REMOVE
    action = Column(SQLEnum(ModificationAction), nullable=False)
    vectorize_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_heading_modifications_work_id', 'work_id'),
        Index('ix_heading_modifications_work_line', 'work_id', 'line_number'),
    )

    def __repr__(self):
        return f"<HeadingModification(id={self.id}, work_id={self.work_id}, line={self.line_number}, action={self.action.value})>"
```

**6. Update Model Imports**

File: `src/vulcanlab/data/models/__init__.py`

Add exports:
```python
from .parsed_markdown import ParsedMarkdown
from .sanitized_markdown import SanitizedMarkdown
from .heading_modifications import HeadingModification
from .enums import FileType, DocumentClassification, ModificationAction
```

**7. Update init_db.py**

File: `src/vulcanlab/data/init_db.py`

Add imports (around line 28):
```python
from .models.parsed_markdown import ParsedMarkdown  # noqa: F401
from .models.sanitized_markdown import SanitizedMarkdown  # noqa: F401
from .models.heading_modifications import HeadingModification  # noqa: F401
```

Add seed function for simple conversion templates (after `seed_prompt_templates` function):
```python
def seed_simple_conversion_templates(verbose: bool = False) -> None:
    """
    Seed prompt templates for simple conversion.

    Creates two templates:
    - simple_sanitize_small: Full document sanitization
    - simple_sanitize_large: Condensed document analysis
    """
    if verbose:
        print("Seeding simple conversion prompt templates...")

    with engine.connect() as conn:
        # Check if templates already exist
        result = conn.execute(text("""
            SELECT COUNT(*) FROM prompt_templates
            WHERE function_tag IN ('simple_sanitize_small', 'simple_sanitize_large')
        """))
        count = result.scalar()

        if count > 0:
            if verbose:
                print("Simple conversion templates already exist, skipping")
            return

        # Insert simple_sanitize_small template
        conn.execute(text("""
            INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
            VALUES (
                'simple_sanitize_small',
                1,
                'Simple Conversion - Small Document Sanitization',
                'You are an expert document processor preparing academic and research documents for a Retrieval-Augmented Generation (RAG) system.

Your task is to process the provided markdown document to ensure it has:
1. **Proper document hierarchy**: Adjust title heading levels to create appropriate nesting based on context.
2. **Clean, RAG-relevant content**: Remove all non-topical content and fix conversion artifacts.

## Instructions

### Hierarchy Adjustments
- Review all headings (lines starting with #, ##, ###, etc.)
- If a heading is NOT actually a title (e.g., page numbers, "References", "Table of Contents"), REMOVE the heading markers (delete the #''s entirely)
- For actual titles, adjust heading levels (H1-H6) to create proper nesting based on semantic relationships
- Ensure logical hierarchy: child sections should be one level deeper than their parent

### Content Sanitization
- **Fix conversion artifacts**: Replace poorly converted symbols/glyphs with correct text using surrounding context
- **Remove meta-information**: Delete download sources, file metadata, copyright notices
- **Remove non-topical sections**: Delete References, Acknowledgments, Table of Contents, page numbers, headers/footers
- **Remove gibberish**: Delete any garbled text that resulted from poor OCR or conversion
- **Preserve RAG-relevant content**: Keep all substantive text related to the document''s main topics

### Output Format
- Return ONLY the sanitized markdown
- Do NOT add explanations, comments, or metadata
- Do NOT wrap output in code blocks or additional formatting
- Maintain markdown syntax (headings with #, lists, emphasis, etc.)

---

## Document to Process

{markdown}

---

## Sanitized Output',
                TRUE,
                NOW(),
                NOW()
            )
        """))

        # Insert simple_sanitize_large template
        conn.execute(text("""
            INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
            VALUES (
                'simple_sanitize_large',
                1,
                'Simple Conversion - Large Document Analysis',
                'You are an expert document processor analyzing a large document''s structure for a RAG system.

You will receive a CONDENSED representation showing each heading with contextual sentences. Your task is to provide heading-level modifications.

## Instructions

For each heading, determine:

1. **Action**: Choose one:
   - `KEEP`: Heading is valid, keep as-is
   - `CHANGE`: Heading should be modified (level change, text cleanup)
   - `REMOVE`: Not a real heading (e.g., page numbers, "References")

2. **Modified Heading**: If action=CHANGE, provide the corrected heading with proper markdown level markers (#, ##, ###)
   - Adjust heading level for proper hierarchy
   - Clean up formatting issues (extra spaces, weird characters)
   - If action=REMOVE or action=KEEP, leave this blank

3. **Vectorize**: Choose one:
   - `VECTORIZE`: This section contains RAG-relevant content and should be indexed
   - `SKIP`: This section is not relevant (meta-information, acknowledgments, etc.)

## Output Format

Provide your modifications as a structured list, one per heading:

```
LINE: {line_number}
ACTION: {KEEP|CHANGE|REMOVE}
MODIFIED: {new heading if ACTION=CHANGE, otherwise blank}
VECTORIZE: {VECTORIZE|SKIP}
---
```

## Example

Input:
```
5: ## Introduction
  This paper presents a novel approach to machine learning. We focus on neural networks.
  ...
  The rest of the paper is organized as follows.

12: ### Page 3
  Lorem ipsum dolor sit amet.
```

Output:
```
LINE: 5
ACTION: KEEP
MODIFIED:
VECTORIZE: VECTORIZE
---
LINE: 12
ACTION: REMOVE
MODIFIED:
VECTORIZE: SKIP
---
```

---

## Condensed Document

{condensed_document}

---

## Your Modifications',
                TRUE,
                NOW(),
                NOW()
            )
        """))

        conn.commit()

        if verbose:
            print("Simple conversion templates seeded successfully")
```

Update `init_database` function to call the new seed function:
```python
def init_database(verbose: bool = False) -> None:
    # ... existing code ...
    seed_prompt_templates(verbose=verbose)
    seed_simple_conversion_templates(verbose=verbose)  # Add this line
    create_default_rag_config(verbose=verbose)
    # ... rest of function ...
```

**8. Create Migration Script**

File: `migrations/016_simple_conversion_tables.sql`

```sql
-- Migration 016: Create tables for simple conversion pipeline
-- Description: Creates parsed_markdown, sanitized_markdown, and heading_modifications tables
--              Adds simple_conversion flag to io_files table
--              Seeds two new prompt templates for simple conversion

BEGIN;

-- Create ENUMs
DO $$ BEGIN
    CREATE TYPE file_type AS ENUM ('pdf', 'epub');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE document_classification AS ENUM ('small', 'large');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE modification_action AS ENUM ('remove', 'change', 'keep');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create parsed_markdown table
CREATE TABLE IF NOT EXISTS parsed_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    file_type file_type NOT NULL,
    classification document_classification NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_parsed_markdown_work_id ON parsed_markdown(work_id);

-- Create sanitized_markdown table
CREATE TABLE IF NOT EXISTS sanitized_markdown (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    content BYTEA NOT NULL,  -- Stores compressed markdown
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sanitized_markdown_work_id ON sanitized_markdown(work_id);

-- Create heading_modifications table
CREATE TABLE IF NOT EXISTS heading_modifications (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    original_heading TEXT NOT NULL,
    modified_heading TEXT,
    action modification_action NOT NULL,
    vectorize_flag BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_id ON heading_modifications(work_id);
CREATE INDEX IF NOT EXISTS ix_heading_modifications_work_line ON heading_modifications(work_id, line_number);

-- Add simple_conversion flag to io_files
ALTER TABLE io_files ADD COLUMN IF NOT EXISTS simple_conversion BOOLEAN DEFAULT FALSE;

-- Seed simple conversion prompt templates
-- Note: Only insert if they don't already exist

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_small',
    1,
    'Simple Conversion - Small Document Sanitization',
    'You are an expert document processor preparing academic and research documents for a Retrieval-Augmented Generation (RAG) system.

Your task is to process the provided markdown document to ensure it has:
1. **Proper document hierarchy**: Adjust title heading levels to create appropriate nesting based on context.
2. **Clean, RAG-relevant content**: Remove all non-topical content and fix conversion artifacts.

## Instructions

### Hierarchy Adjustments
- Review all headings (lines starting with #, ##, ###, etc.)
- If a heading is NOT actually a title (e.g., page numbers, "References", "Table of Contents"), REMOVE the heading markers (delete the #''s entirely)
- For actual titles, adjust heading levels (H1-H6) to create proper nesting based on semantic relationships
- Ensure logical hierarchy: child sections should be one level deeper than their parent

### Content Sanitization
- **Fix conversion artifacts**: Replace poorly converted symbols/glyphs with correct text using surrounding context
- **Remove meta-information**: Delete download sources, file metadata, copyright notices
- **Remove non-topical sections**: Delete References, Acknowledgments, Table of Contents, page numbers, headers/footers
- **Remove gibberish**: Delete any garbled text that resulted from poor OCR or conversion
- **Preserve RAG-relevant content**: Keep all substantive text related to the document''s main topics

### Output Format
- Return ONLY the sanitized markdown
- Do NOT add explanations, comments, or metadata
- Do NOT wrap output in code blocks or additional formatting
- Maintain markdown syntax (headings with #, lists, emphasis, etc.)

---

## Document to Process

{markdown}

---

## Sanitized Output',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_small'
);

INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
SELECT
    'simple_sanitize_large',
    1,
    'Simple Conversion - Large Document Analysis',
    'You are an expert document processor analyzing a large document''s structure for a RAG system.

You will receive a CONDENSED representation showing each heading with contextual sentences. Your task is to provide heading-level modifications.

## Instructions

For each heading, determine:

1. **Action**: Choose one:
   - `KEEP`: Heading is valid, keep as-is
   - `CHANGE`: Heading should be modified (level change, text cleanup)
   - `REMOVE`: Not a real heading (e.g., page numbers, "References")

2. **Modified Heading**: If action=CHANGE, provide the corrected heading with proper markdown level markers (#, ##, ###)
   - Adjust heading level for proper hierarchy
   - Clean up formatting issues (extra spaces, weird characters)
   - If action=REMOVE or action=KEEP, leave this blank

3. **Vectorize**: Choose one:
   - `VECTORIZE`: This section contains RAG-relevant content and should be indexed
   - `SKIP`: This section is not relevant (meta-information, acknowledgments, etc.)

## Output Format

Provide your modifications as a structured list, one per heading:

```
LINE: {line_number}
ACTION: {KEEP|CHANGE|REMOVE}
MODIFIED: {new heading if ACTION=CHANGE, otherwise blank}
VECTORIZE: {VECTORIZE|SKIP}
---
```

## Example

Input:
```
5: ## Introduction
  This paper presents a novel approach to machine learning. We focus on neural networks.
  ...
  The rest of the paper is organized as follows.

12: ### Page 3
  Lorem ipsum dolor sit amet.
```

Output:
```
LINE: 5
ACTION: KEEP
MODIFIED:
VECTORIZE: VECTORIZE
---
LINE: 12
ACTION: REMOVE
MODIFIED:
VECTORIZE: SKIP
---
```

---

## Condensed Document

{condensed_document}

---

## Your Modifications',
    TRUE,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM prompt_templates WHERE function_tag = 'simple_sanitize_large'
);

COMMIT;
```

**9. Update Work Model Documentation**

File: `src/vulcanlab/data/models/work.py`

Add documentation comment for `processing_status` JSON structure:

```python
"""
processing_status JSON structure for simple conversion:
{
    "simple_conversion_step": "parsing" | "sanitizing" | "chunking" | "complete" | "failed",
    "simple_conversion_classification": "small" | "large",
    "simple_conversion_mode": "automatic" | "manual",
    "simple_conversion_error": "error message" | null
}
"""
```

## Unit Tests

File: `tests/unit/test_simple_conversion_models.py`

**All tests must be mocked - NEVER hit the database.**

**Test Cases:**

1. **`test_file_type_enum_values`**
   - Assert `FileType.PDF.value == 'pdf'`
   - Assert `FileType.EPUB.value == 'epub'`

2. **`test_document_classification_enum_values`**
   - Assert `DocumentClassification.SMALL.value == 'small'`
   - Assert `DocumentClassification.LARGE.value == 'large'`

3. **`test_modification_action_enum_values`**
   - Assert `ModificationAction.REMOVE.value == 'remove'`
   - Assert `ModificationAction.CHANGE.value == 'change'`
   - Assert `ModificationAction.KEEP.value == 'keep'`

4. **`test_compress_small_content`**
   - Content = "small text" (< 1MB)
   - Call `compress_if_large(content)`
   - Assert: Returns uncompressed bytes (len < 1MB)

5. **`test_compress_large_content`**
   - Content = "x" * (2 * 1024 * 1024) (2MB)
   - Call `compress_if_large(content)`
   - Assert: Returns compressed bytes (len < original)

6. **`test_decompress_compressed_data`**
   - Compressed data from gzip
   - Call `decompress_if_needed(data)`
   - Assert: Returns original string

7. **`test_decompress_uncompressed_data`**
   - Uncompressed UTF-8 bytes
   - Call `decompress_if_needed(data)`
   - Assert: Returns decoded string

8. **`test_parsed_markdown_content_property_decompresses`**
   - Mock ParsedMarkdown instance with `_content` = compressed bytes
   - Access `.content` property
   - Assert: Returns decompressed string

9. **`test_parsed_markdown_content_setter_compresses`**
   - Create ParsedMarkdown instance
   - Set `.content` = large string (>1MB)
   - Assert: `_content` is compressed bytes

10. **`test_sanitized_markdown_compression_roundtrip`**
    - Create SanitizedMarkdown instance
    - Set `.content` = large markdown
    - Get `.content` back
    - Assert: Returns same string (compression is transparent)

11. **`test_parsed_markdown_table_structure`**
    - Inspect `ParsedMarkdown.__table__`
    - Assert: Columns exist: id, work_id, content (as 'content'), file_type, classification, token_count, created_at
    - Assert: `work_id` has ForeignKey to 'works.id' with ondelete='CASCADE'

12. **`test_sanitized_markdown_table_structure`**
    - Inspect `SanitizedMarkdown.__table__`
    - Assert: Columns exist: id, work_id, content, token_count, created_at
    - Assert: CASCADE delete on work_id

13. **`test_heading_modifications_table_structure`**
    - Inspect `HeadingModification.__table__`
    - Assert: Columns exist with correct types
    - Assert: CASCADE delete on work_id

14. **`test_parsed_markdown_indexes`**
    - Inspect `ParsedMarkdown.__table__.indexes`
    - Assert: Index on 'work_id' exists

15. **`test_heading_modifications_composite_index`**
    - Inspect indexes
    - Assert: Composite index on (work_id, line_number) exists

## Dependencies and Sequencing

### Must be done before:
- None (this is the foundation ticket)

### Must be done after:
- T02, T03, T04, T05, T06, T07, T08, T09, T10, T11 all depend on this ticket

### Rollback considerations:
- Migration script can be reversed by dropping tables and ENUMs
- Foreign key CASCADE ensures no orphaned records if Works are deleted
- No impact on existing conversion pipeline (separate tables)
- Template seeding is idempotent (won't duplicate if run multiple times)

## Clarifications and Assumptions

### Assumptions:

1. **Compression strategy:** Using Python gzip in application layer via SQLAlchemy properties. Content is stored as BYTEA/LargeBinary. Compression happens automatically in setters, decompression in getters.

2. **ENUM types:** Using SQLAlchemy Python ENUMs which map to PostgreSQL ENUM types in the database for type safety.

3. **Content column type:** Using `LargeBinary` (BYTEA in PostgreSQL) to store compressed bytes. This is more efficient than TEXT for compressed data.

4. **Template content:** Using placeholder prompt content that covers the basic requirements. These can be refined in the Settings UI later.

5. **IOFile flag:** Adding `simple_conversion` boolean to distinguish simple conversion files from regular conversion files for UI filtering.

6. **Multiple sanitized versions:** Schema allows multiple `SanitizedMarkdown` records per work_id (no UNIQUE constraint) for re-running sanitization.

---

**Before implementing:** Verify compression threshold (1MB) is appropriate for your use case. Review template content with product owner before finalizing.
