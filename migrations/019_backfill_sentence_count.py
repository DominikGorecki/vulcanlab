"""
Migration 019: Backfill sentence_count for existing chunks.

This migration populates the sentence_count column for all existing chunks
by counting sentences directly from the chunks.content column.

Changes:
1. Query all chunks WHERE sentence_count IS NULL AND vector_status = 'vec'
2. Count sentences using _get_sentences() logic from content_chunking
3. Update chunks.sentence_count in batches
4. Handle errors gracefully: log warning, set sentence_count=NULL, continue

Note: This migration is idempotent and safe to re-run.
"""

import logging

import spacy
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model for sentence tokenization
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise ImportError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install with: python -m spacy download en_core_web_sm"
    )


def _get_sentences(text: str) -> list[str]:
    """Split text into sentences using spaCy.

    This is the same logic used in content_chunking.py to ensure
    consistent sentence counting.
    """
    if not text:
        return []
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def upgrade(connection):
    """Apply the migration."""
    print("Starting migration 019: Backfill sentence_count")
    print("=" * 60)

    # Step 1: Get total chunk count to process
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM chunks
        WHERE sentence_count IS NULL AND vector_status = 'vec'
    """))
    total_chunks = result.scalar()
    print(f"\nTotal chunks to process: {total_chunks}")

    if total_chunks == 0:
        print("No chunks to process (all chunks already have sentence_count)")
        print("=" * 60)
        return

    # Step 2: Process chunks in batches
    batch_size = 100
    chunks_processed = 0
    chunks_updated = 0
    chunks_with_errors = 0

    print(f"\nProcessing chunks in batches of {batch_size}...")

    while chunks_processed < total_chunks:
        # Fetch batch of chunks (always fetch first N since we update as we go)
        # This avoids offset issues where updating chunks changes the result set
        result = connection.execute(
            text("""
                SELECT id, content
                FROM chunks
                WHERE sentence_count IS NULL AND vector_status = 'vec'
                ORDER BY id
                LIMIT :limit
            """),
            {"limit": batch_size}
        )

        batch = result.fetchall()
        if not batch:
            break

        # Process each chunk in the batch
        updates = []
        for row in batch:
            chunk_id, content = row
            chunks_processed += 1

            try:
                # Count sentences
                sentences = _get_sentences(content)
                sentence_count = len(sentences)

                updates.append({
                    'chunk_id': chunk_id,
                    'sentence_count': sentence_count
                })
                chunks_updated += 1

            except Exception as e:
                logger.warning(
                    f"Error counting sentences for chunk {chunk_id}: {e}"
                )
                # Add with NULL value
                updates.append({
                    'chunk_id': chunk_id,
                    'sentence_count': None
                })
                chunks_with_errors += 1

        # Batch update
        for update in updates:
            connection.execute(
                text("UPDATE chunks SET sentence_count = :count WHERE id = :id"),
                {"count": update['sentence_count'], "id": update['chunk_id']}
            )
        connection.commit()

        # Progress logging
        if chunks_processed % 100 == 0 or chunks_processed == total_chunks:
            print(f"  Processed {chunks_processed:,} / {total_chunks:,} chunks...")

        # No offset increment - we always fetch from the beginning since we're
        # removing chunks from the WHERE clause as we update them

    # Step 3: Summary
    print("\n" + "=" * 60)
    print("Migration 019 completed successfully!")
    print(f"\nSummary:")
    print(f"  Total chunks processed: {chunks_processed:,}")
    print(f"  Chunks updated with sentence_count: {chunks_updated:,}")
    print(f"  Chunks with errors (set to NULL): {chunks_with_errors:,}")
    print("=" * 60)


def downgrade(connection):
    """Revert the migration."""
    print("Starting migration 019 downgrade: Reset sentence_count")
    print("=" * 60)

    # Reset all sentence_count values to NULL
    print("\nResetting all sentence_count values to NULL...")

    result = connection.execute(text("""
        UPDATE chunks
        SET sentence_count = NULL
        WHERE sentence_count IS NOT NULL
    """))
    connection.commit()

    # Get count of updated rows
    result = connection.execute(text("""
        SELECT COUNT(*) FROM chunks WHERE sentence_count IS NULL
    """))
    total_reset = result.scalar()

    print(f"✓ Reset sentence_count for all chunks")

    print("\n" + "=" * 60)
    print("Migration 019 downgrade completed!")
    print(f"\nTotal chunks reset: {total_reset:,}")
    print("=" * 60)
