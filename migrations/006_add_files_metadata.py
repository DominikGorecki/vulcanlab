"""
Migration 006: Add files metadata column to works table.

This migration adds a JSON column to track all processing pipeline files
with their absolute paths and SHA-256 hashes.

The files column structure:
{
  "original_file": {"path": "/absolute/path/doc.pdf", "hash": "sha256..."},
  "hier_markdown": {"path": "/absolute/path/doc.hier.md", "hash": "sha256..."},
  "style_markdown": {"path": "/absolute/path/doc.style.md", "hash": "sha256..."},
  "original_markdown": {"path": "/absolute/path/doc.md", "hash": "sha256..."},
  "toc_titles": {"path": "/absolute/path/doc.toc_titles.md", "hash": "sha256..."},
  "titles": {"path": "/absolute/path/doc.titles.md", "hash": "sha256..."},
  "san_mapping": {"path": "/absolute/path/doc.san_mapping.csv", "hash": "sha256..."},
  "sanitized": {"path": "/absolute/path/doc.sanitized.md", "hash": "sha256..."},
  "sanitized_titles": {"path": "/absolute/path/doc.sanitized.titles.md", "hash": "sha256..."},
  "vec_suggestions": {"path": "/absolute/path/doc.sanitized.vec_sugg.md", "hash": "sha256..."}
}

Note: Existing records will have NULL for the files column.
      No data migration is performed.
"""

SQL_UP = """
ALTER TABLE works ADD COLUMN files JSON NULL;
"""

SQL_DOWN = """
ALTER TABLE works DROP COLUMN files;
"""


def upgrade(connection):
    """Apply the migration."""
    connection.execute(SQL_UP)


def downgrade(connection):
    """Revert the migration."""
    connection.execute(SQL_DOWN)
