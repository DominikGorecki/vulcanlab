"""Enums for simple conversion pipeline models."""

import enum


class FileType(str, enum.Enum):
    """File type for parsed markdown."""
    PDF = 'pdf'
    EPUB = 'epub'
    MARKDOWN_IMPORT = 'markdown_import'


class DocumentClassification(str, enum.Enum):
    """Document size classification."""
    SMALL = 'small'
    LARGE = 'large'


class ModificationAction(str, enum.Enum):
    """Heading modification action."""
    REMOVE = 'remove'
    CHANGE = 'change'
    KEEP = 'keep'


class CollectionItemType(str, enum.Enum):
    """Item type for collection items."""
    EXCERPT = 'excerpt'
    RESEARCH_RESULT = 'research_result'
    RESEARCH_QUERY = 'research_query'


class SessionType(str, enum.Enum):
    """
    Session type for research sessions.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (session_type IN ('manual', 'automated'))
    See: migrations/028_add_research_tables.sql and schema/specialized_tables.py
    """
    MANUAL = 'manual'
    AUTOMATED = 'automated'


class SessionStatus(str, enum.Enum):
    """
    Status for research sessions.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (status IN ('in_progress', 'completed', 'failed', 'paused'))
    See: migrations/028_add_research_tables.sql and schema/specialized_tables.py
    """
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PAUSED = 'paused'


class ResearchPhase(str, enum.Enum):
    """
    Research phase for tracking session progress.

    IMPORTANT: Values stored as VARCHAR in database (lowercase convention).
    No CHECK constraint, but lowercase is used for consistency.
    See: migrations/028_add_research_tables.sql and schema/specialized_tables.py
    """
    PLANNING = 'planning'
    RESEARCH = 'research'
    CONTEXT_ASSEMBLY = 'context_assembly'
    SYNTHESIS = 'synthesis'
    EVALUATION = 'evaluation'
    REFINEMENT = 'refinement'
    COMPLETED = 'completed'


class QualityStatus(str, enum.Enum):
    """
    Quality status for research sections and reports.

    IMPORTANT: Values MUST match database CHECK constraint exactly (lowercase):
    CHECK (quality_status IS NULL OR quality_status IN ('pending', 'pass', 'fail', 'needs_review'))
    See: migrations/028_add_research_tables.sql and schema/specialized_tables.py
    """
    PENDING = 'pending'
    PASS = 'pass'
    FAIL = 'fail'
    NEEDS_REVIEW = 'needs_review'
