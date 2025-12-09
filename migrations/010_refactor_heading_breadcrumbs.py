"""
Migration 010: Refactor heading breadcrumbs to separate column.

This migration extracts heading breadcrumbs from chunk content and stores them
in a dedicated column, improving data separation and enabling flexible UI presentation.

Changes:
1. Add heading_breadcrumbs column to chunks table
2. Extract breadcrumbs from content (format: "H1 > H2 > H3")
3. Remove breadcrumbs from content
4. Reset vector_status to 'to_vec' for all 'vec' chunks (requires re-vectorization)
5. Clear embeddings for affected chunks
6. Update content_tsvector with clean content

Note: All existing vectorized chunks will need to be re-vectorized after this migration.
"""

from sqlalchemy import text


def extract_breadcrumb(content: str) -> tuple[str | None, str]:
    """
    Extract breadcrumb from content if present.

    Based on database verification, the first line is ALWAYS the breadcrumb
    if the content has multiple lines. Single-line content has no breadcrumb.

    Args:
        content: The chunk content to process

    Returns:
        Tuple of (breadcrumb, clean_content):
        - breadcrumb: The extracted breadcrumb string or None
        - clean_content: Content with breadcrumb removed
    """
    if not content:
        return None, content

    # If content has multiple lines, first line is the breadcrumb
    if '\n' in content:
        lines = content.split('\n', 1)
        breadcrumb = lines[0].strip()
        # Get remaining content (after first line and newline)
        clean_content = lines[1] if len(lines) > 1 else ''
        return breadcrumb, clean_content

    # Single-line content has no breadcrumb
    return None, content


SQL_UP_ADD_COLUMN = """
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS heading_breadcrumbs VARCHAR(500) NULL;
"""

SQL_DOWN_DROP_COLUMN = """
ALTER TABLE chunks DROP COLUMN IF EXISTS heading_breadcrumbs;
"""


def upgrade(connection):
    """Apply the migration."""
    print("Starting migration 010: Refactor heading breadcrumbs")
    print("=" * 60)

    # Step 1: Add new column
    print("\nStep 1: Adding heading_breadcrumbs column...")
    connection.execute(text(SQL_UP_ADD_COLUMN))
    connection.commit()
    print("✓ Column added successfully")

    # Step 2: Get total chunk count
    result = connection.execute(text("SELECT COUNT(*) FROM chunks"))
    total_chunks = result.scalar()
    print(f"\nTotal chunks to process: {total_chunks}")

    # Step 3: Process chunks in batches
    batch_size = 1000
    offset = 0
    chunks_with_breadcrumbs = 0
    chunks_revectorize = 0
    chunks_processed = 0

    print(f"\nStep 2: Processing chunks (batch size: {batch_size})...")

    while True:
        # Fetch batch of chunks
        result = connection.execute(
            text("""
                SELECT id, content, vector_status
                FROM chunks
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": batch_size, "offset": offset}
        )

        batch = result.fetchall()
        if not batch:
            break

        # Process each chunk in the batch
        for row in batch:
            chunk_id, content, vector_status = row

            # Extract breadcrumb
            breadcrumb, clean_content = extract_breadcrumb(content)

            if breadcrumb:
                chunks_with_breadcrumbs += 1

            # Determine if we need to reset vectorization
            needs_revectorize = (vector_status == 'vec')
            if needs_revectorize:
                chunks_revectorize += 1
                new_vector_status = 'to_vec'
            else:
                new_vector_status = vector_status

            # Update the chunk
            if breadcrumb or needs_revectorize:
                # Build update query
                if needs_revectorize:
                    # Reset vectorization and update content_tsvector
                    connection.execute(
                        text("""
                            UPDATE chunks
                            SET heading_breadcrumbs = :breadcrumb,
                                content = :content,
                                vector_status = :vector_status,
                                embedding = NULL,
                                content_tsvector = to_tsvector('english', :content)
                            WHERE id = :id
                        """),
                        {
                            "breadcrumb": breadcrumb,
                            "content": clean_content,
                            "vector_status": new_vector_status,
                            "id": chunk_id
                        }
                    )
                else:
                    # Just update breadcrumb, content, and tsvector
                    connection.execute(
                        text("""
                            UPDATE chunks
                            SET heading_breadcrumbs = :breadcrumb,
                                content = :content,
                                content_tsvector = to_tsvector('english', :content)
                            WHERE id = :id
                        """),
                        {
                            "breadcrumb": breadcrumb,
                            "content": clean_content,
                            "id": chunk_id
                        }
                    )

            chunks_processed += 1

        # Commit batch
        connection.commit()

        # Progress update
        if chunks_processed % (batch_size * 5) == 0:
            print(f"  Processed {chunks_processed:,} / {total_chunks:,} chunks...")

        offset += batch_size

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("Migration 010 completed successfully!")
    print(f"\nSummary:")
    print(f"  Total chunks processed: {chunks_processed:,}")
    print(f"  Chunks with breadcrumbs: {chunks_with_breadcrumbs:,}")
    print(f"  Chunks marked for re-vectorization: {chunks_revectorize:,}")
    print("\nNext steps:")
    print("  1. Run vectorization on all 'to_vec' chunks")
    print("  2. Verify breadcrumbs extracted correctly")
    print("  3. Update code to use new schema")
    print("=" * 60)


def downgrade(connection):
    """Revert the migration."""
    print("Starting migration 010 downgrade: Re-embed breadcrumbs")
    print("=" * 60)

    # Step 1: Re-embed breadcrumbs into content
    print("\nStep 1: Re-embedding breadcrumbs into content...")

    batch_size = 1000
    offset = 0
    chunks_updated = 0

    while True:
        # Fetch chunks with breadcrumbs
        result = connection.execute(
            text("""
                SELECT id, content, heading_breadcrumbs
                FROM chunks
                WHERE heading_breadcrumbs IS NOT NULL
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": batch_size, "offset": offset}
        )

        batch = result.fetchall()
        if not batch:
            break

        # Re-embed breadcrumbs
        for row in batch:
            chunk_id, content, breadcrumb = row

            # Re-embed breadcrumb at start of content
            new_content = f"{breadcrumb}\n{content}" if content else breadcrumb

            # Update chunk (mark for re-vectorization since content changed)
            connection.execute(
                text("""
                    UPDATE chunks
                    SET content = :content,
                        vector_status = 'to_vec',
                        embedding = NULL,
                        content_tsvector = to_tsvector('english', :content)
                    WHERE id = :id
                """),
                {
                    "content": new_content,
                    "id": chunk_id
                }
            )

            chunks_updated += 1

        connection.commit()
        offset += batch_size

    print(f"✓ Re-embedded breadcrumbs in {chunks_updated:,} chunks")

    # Step 2: Drop column
    print("\nStep 2: Dropping heading_breadcrumbs column...")
    connection.execute(text(SQL_DOWN_DROP_COLUMN))
    connection.commit()
    print("✓ Column dropped successfully")

    print("\n" + "=" * 60)
    print("Migration 010 downgrade completed!")
    print(f"\nNote: {chunks_updated:,} chunks marked for re-vectorization")
    print("=" * 60)
