"""
Migration 030: Fix tabs in chunk content.

This migration finds chunks where the ratio of tab characters to word count
is 20% or higher, and:
1. Replaces all tabs with spaces in content
2. Replaces all tabs with spaces in heading_breadcrumbs (if present)
3. Sets embedding to NULL
4. Changes vector_status from 'vec' to 'to_vec' (leaves 'no_vec' unchanged)

The content_tsvector column is automatically updated by the existing trigger
when content changes.
"""

import argparse
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Threshold: if tabs/words >= 0.20 (20%), process the row
TAB_RATIO_THRESHOLD = 0.20
DEFAULT_BATCH_SIZE = 500


def _calculate_tab_ratio(content: str) -> float:
    """
    Calculate the ratio of tab characters to word count.

    Args:
        content: The text content to analyze.

    Returns:
        Ratio of tab count to word count. Returns 0 if no words.
    """
    if not content:
        return 0.0

    tab_count = content.count('\t')
    words = content.split()
    word_count = len(words)

    if word_count == 0:
        return 0.0

    return tab_count / word_count


def _needs_tab_fix(content: str) -> bool:
    """Check if content has tab ratio >= threshold."""
    return _calculate_tab_ratio(content) >= TAB_RATIO_THRESHOLD


def process_single_chunk(connection, chunk_id: int, dry_run: bool = False) -> dict:
    """
    Process a single chunk by ID for testing purposes.

    Args:
        connection: Database connection.
        chunk_id: The ID of the chunk to process.
        dry_run: If True, don't make changes, just report what would happen.

    Returns:
        Dict with processing result information.
    """
    # Fetch the chunk
    result = connection.execute(
        text("""
            SELECT id, content, vector_status, heading_breadcrumbs
            FROM chunks WHERE id = :id
        """),
        {"id": chunk_id}
    )
    row = result.fetchone()

    if not row:
        return {"status": "not_found", "chunk_id": chunk_id}

    chunk_id, content, vector_status, heading_breadcrumbs = row
    tab_ratio = _calculate_tab_ratio(content)
    needs_fix = tab_ratio >= TAB_RATIO_THRESHOLD

    result_info = {
        "chunk_id": chunk_id,
        "tab_count": content.count('\t') if content else 0,
        "word_count": len(content.split()) if content else 0,
        "tab_ratio": tab_ratio,
        "threshold": TAB_RATIO_THRESHOLD,
        "needs_fix": needs_fix,
        "current_vector_status": vector_status,
        "heading_breadcrumbs_has_tabs": bool(heading_breadcrumbs and '\t' in heading_breadcrumbs),
        "dry_run": dry_run,
    }

    if not needs_fix:
        result_info["status"] = "skipped_below_threshold"
        return result_info

    if dry_run:
        result_info["status"] = "would_update"
        result_info["new_vector_status"] = "to_vec" if vector_status == "vec" else vector_status
        return result_info

    # Apply the fix
    new_content = content.replace('\t', ' ')
    new_heading_breadcrumbs = heading_breadcrumbs.replace('\t', ' ') if heading_breadcrumbs else heading_breadcrumbs
    new_vector_status = "to_vec" if vector_status == "vec" else vector_status

    connection.execute(
        text("""
            UPDATE chunks
            SET content = :content,
                heading_breadcrumbs = :heading_breadcrumbs,
                embedding = NULL,
                vector_status = :vector_status
            WHERE id = :id
        """),
        {
            "content": new_content,
            "heading_breadcrumbs": new_heading_breadcrumbs,
            "vector_status": new_vector_status,
            "id": chunk_id
        }
    )
    connection.commit()

    result_info["status"] = "updated"
    result_info["new_vector_status"] = new_vector_status
    return result_info


def upgrade(connection, batch_size: int = DEFAULT_BATCH_SIZE, dry_run: bool = False):
    """
    Apply the migration.

    Args:
        connection: Database connection.
        batch_size: Number of rows to process per batch.
        dry_run: If True, don't make changes, just report what would happen.
    """
    print("Starting migration 030: Fix tabs in chunk content")
    print("=" * 60)
    print(f"Tab ratio threshold: {TAB_RATIO_THRESHOLD * 100:.0f}%")
    print(f"Batch size: {batch_size}")
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    print()

    # Step 1: Get total chunk count
    result = connection.execute(text("SELECT COUNT(*) FROM chunks"))
    total_chunks = result.scalar()
    print(f"Total chunks to scan: {total_chunks}")

    if total_chunks == 0:
        print("No chunks to process.")
        return

    # Step 2: Process chunks in batches
    processed = 0
    updated = 0
    skipped = 0

    print(f"\nScanning chunks in batches of {batch_size}...")

    while processed < total_chunks:
        # Fetch a batch of chunks with their content, vector_status, and heading_breadcrumbs
        batch_result = connection.execute(
            text("""
                SELECT id, content, vector_status, heading_breadcrumbs
                FROM chunks
                ORDER BY id
                LIMIT :limit OFFSET :offset
            """),
            {"limit": batch_size, "offset": processed}
        )
        batch_rows = batch_result.fetchall()

        if not batch_rows:
            break

        updates_in_batch = []

        for row in batch_rows:
            chunk_id, content, vector_status, heading_breadcrumbs = row

            if not _needs_tab_fix(content):
                skipped += 1
                processed += 1
                continue

            # Prepare the update
            new_content = content.replace('\t', ' ')
            new_heading_breadcrumbs = heading_breadcrumbs.replace('\t', ' ') if heading_breadcrumbs else heading_breadcrumbs
            new_vector_status = "to_vec" if vector_status == "vec" else vector_status

            updates_in_batch.append({
                "id": chunk_id,
                "content": new_content,
                "heading_breadcrumbs": new_heading_breadcrumbs,
                "vector_status": new_vector_status
            })
            processed += 1

        # Apply updates for this batch
        if updates_in_batch and not dry_run:
            for update in updates_in_batch:
                connection.execute(
                    text("""
                        UPDATE chunks
                        SET content = :content,
                            heading_breadcrumbs = :heading_breadcrumbs,
                            embedding = NULL,
                            vector_status = :vector_status
                        WHERE id = :id
                    """),
                    update
                )
            connection.commit()

        updated += len(updates_in_batch)

        if processed % 1000 == 0 or processed == total_chunks:
            print(f"  Processed {processed}/{total_chunks} chunks "
                  f"(updated: {updated}, skipped: {skipped})...")

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN COMPLETE - No changes were made")
    else:
        print("Migration 030 completed successfully!")
    print(f"Summary: Scanned {processed}, Updated {updated}, Skipped {skipped}")
    print("=" * 60)


def downgrade(connection):
    """
    Revert the migration.

    Note: This migration cannot be fully reverted since we don't store
    the original tab positions. This downgrade is a no-op.
    """
    print("Migration 030 downgrade: No automatic rollback available")
    print("The original tab positions were not preserved.")
    print("To restore, you would need to re-import the affected works.")


def main():
    """CLI entry point for running the migration."""
    parser = argparse.ArgumentParser(
        description="Migration 030: Fix tabs in chunk content"
    )
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="Run downgrade (rollback) instead of upgrade"
    )
    parser.add_argument(
        "--chunk-id",
        type=int,
        help="Process a single chunk by ID (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't make changes, just show what would happen"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size for processing (default: {DEFAULT_BATCH_SIZE})"
    )

    args = parser.parse_args()

    # Import here to avoid circular imports
    from vulcanlab.data.database import engine

    print("=" * 80)
    print("Migration 030: Fix Tabs in Chunk Content")
    print("=" * 80)
    print()

    if args.downgrade:
        print("Running DOWNGRADE...")
        print()
        try:
            with engine.connect() as connection:
                downgrade(connection)
            print()
            print("Migration 030 downgrade completed.")
        except Exception as e:
            print()
            print(f"ERROR during migration downgrade: {e}")
            import traceback
            traceback.print_exc()
            exit(1)

    elif args.chunk_id:
        print(f"Processing single chunk ID: {args.chunk_id}")
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")
        print()
        try:
            with engine.connect() as connection:
                result = process_single_chunk(
                    connection,
                    args.chunk_id,
                    dry_run=args.dry_run
                )
                print("Result:")
                for key, value in result.items():
                    if key == "tab_ratio":
                        print(f"  {key}: {value:.2%}")
                    else:
                        print(f"  {key}: {value}")
        except Exception as e:
            print()
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            exit(1)

    else:
        print("Running UPGRADE...")
        if args.dry_run:
            print("DRY RUN MODE - No changes will be made")
        print()
        try:
            with engine.connect() as connection:
                upgrade(
                    connection,
                    batch_size=args.batch_size,
                    dry_run=args.dry_run
                )
            print()
            print("Migration 030 upgrade completed successfully!")
        except Exception as e:
            print()
            print(f"ERROR during migration upgrade: {e}")
            import traceback
            traceback.print_exc()
            exit(1)


if __name__ == "__main__":
    main()
