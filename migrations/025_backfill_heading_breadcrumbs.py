"""
Migration 025: Backfill heading_breadcrumbs for all chunks.

This migration populates the heading_breadcrumbs column for all existing chunks
by traversing the parent hierarchy and extracting titles from heading chunks.
"""

import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_title_from_content(content: str) -> str:
    """Extract title from the first line of content and strip leading #."""
    if not content:
        return ""
    # Take first line and strip markdown headings (#) and whitespace
    first_line = content.splitlines()[0] if content else ""
    title = first_line.lstrip('#').strip()
    
    # Truncate title if it's excessively long (likely not a real heading)
    if len(title) > 120:
        title = title[:117] + "..."
    return title


def upgrade(connection):
    """Apply the migration."""
    print("Starting migration 025: Backfill heading_breadcrumbs (Full Path)")
    print("=" * 60)

    # Step 1: Get total chunk count
    result = connection.execute(text("SELECT COUNT(*) FROM chunks"))
    total_chunks = result.scalar()
    print(f"\nTotal chunks to process: {total_chunks}")

    if total_chunks == 0:
        print("No chunks to process.")
        return

    # Step 2: Process chunks in batches
    batch_size = 500
    processed = 0
    updated = 0

    print(f"\nProcessing all chunks in batches of {batch_size} to ensure full breadcrumb paths...")

    while processed < total_chunks:
        # Fetch a batch of IDs
        id_result = connection.execute(
            text("SELECT id FROM chunks ORDER BY id LIMIT :limit OFFSET :offset"),
            {"limit": batch_size, "offset": processed}
        )
        batch_ids = [row[0] for row in id_result.fetchall()]
        if not batch_ids:
            break

        # For each chunk in the batch, calculate its full breadcrumb
        for chunk_id in batch_ids:
            breadcrumb_query = text("""
                WITH RECURSIVE chunk_hierarchy AS (
                    SELECT id, parent_id, content, level, 0 AS depth
                    FROM chunks
                    WHERE id = :chunk_id
                    UNION ALL
                    SELECT c.id, c.parent_id, c.content, c.level, ch.depth + 1
                    FROM chunks c
                    INNER JOIN chunk_hierarchy ch ON c.id = ch.parent_id
                    WHERE ch.parent_id IS NOT NULL
                )
                SELECT content, level, depth
                FROM chunk_hierarchy
                WHERE level LIKE 'H%'
                ORDER BY depth DESC
            """)
            
            hierarchy_rows = connection.execute(breadcrumb_query, {"chunk_id": chunk_id}).fetchall()
            
            breadcrumb_parts = []
            for row in hierarchy_rows:
                content, level, depth = row
                title = _get_title_from_content(content)
                if title:
                    breadcrumb_parts.append(title)
            
            if breadcrumb_parts:
                breadcrumb_text = " > ".join(breadcrumb_parts)
                # Final safety truncation for the 500 char DB limit
                if len(breadcrumb_text) > 500:
                    breadcrumb_text = breadcrumb_text[:497] + "..."

                connection.execute(
                    text("UPDATE chunks SET heading_breadcrumbs = :breadcrumb WHERE id = :id"),
                    {"breadcrumb": breadcrumb_text, "id": chunk_id}
                )
                updated += 1
            
            processed += 1
            if processed % 100 == 0:
                print(f"  Processed {processed}/{total_chunks} chunks...")

        connection.commit()

    print("\n" + "=" * 60)
    print("Migration 025 completed successfully!")
    print(f"Summary: Processed {processed}, Updated {updated}")
    print("=" * 60)


def downgrade(connection):
    """Revert the migration."""
    print("Starting migration 025 downgrade: Clear heading_breadcrumbs")
    connection.execute(text("UPDATE chunks SET heading_breadcrumbs = NULL"))
    connection.commit()
    print("Migration 025 downgrade completed.")

