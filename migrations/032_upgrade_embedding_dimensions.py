"""
Migration Script: 032_upgrade_embedding_dimensions.py

This script prepares the database for an embedding dimension upgrade by:
1. Backing up affected tables (chunks, queries) to CSV files.
2. Clearing all existing embedding data (setting columns to NULL).
3. Resetting vector_status from 'vec' to 'to_vec' so content can be re-embedded.

This script MUST be run before applying schema changes (init_db.py) because
altering the dimension of a vector column containing data is not supported
directly by pgvector without clearing the data first.

Usage:
    python migrations/032_upgrade_embedding_dimensions.py
"""

import os
import sys
import logging
import psycopg
from datetime import datetime
from pathlib import Path
from sqlalchemy import text

from vulcanlab.data.database import engine, get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BACKUP_DIR = Path(__file__).parent / "backups"
TABLES_TO_BACKUP = ["chunks", "queries"]

def ensure_backup_dir():
    """Create migrations/backups/ directory if it doesn't exist."""
    if not BACKUP_DIR.exists():
        logger.info(f"Creating backup directory: {BACKUP_DIR}")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    if not os.access(BACKUP_DIR, os.W_OK):
        logger.error(f"Backup directory not writable: {BACKUP_DIR}")
        sys.exit(1)

def backup_tables(timestamp):
    """Backup tables using PostgreSQL COPY to CSV files."""
    db_url = get_database_url()
    # Remove the +psycopg prefix if present for raw psycopg connection
    raw_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    
    logger.info("Starting table backups...")
    
    try:
        with psycopg.connect(raw_url) as conn:
            for table in TABLES_TO_BACKUP:
                backup_file = BACKUP_DIR / f"{table}_backup_{timestamp}.csv"
                logger.info(f"Backing up table '{table}' to {backup_file}...")
                
                with open(backup_file, "wb") as f:
                    with conn.cursor() as cur:
                        copy_sql = f"COPY {table} TO STDOUT WITH (FORMAT CSV, HEADER)"
                        with cur.copy(copy_sql) as copy:
                            for data in copy:
                                f.write(data)
                
                file_size = backup_file.stat().st_size
                logger.info(f"✅ Backup of '{table}' complete ({file_size / 1024 / 1024:.2f} MB)")
                
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        sys.exit(1)

def clear_embeddings(connection):
    """Clear embedding columns in chunks and queries tables."""
    logger.info("Clearing embedding data...")
    
    # Check if chunks already cleared
    res = connection.execute(text("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL"))
    chunks_to_clear = res.scalar()
    
    if chunks_to_clear > 0:
        logger.info(f"Clearing {chunks_to_clear} embeddings in 'chunks' table...")
        connection.execute(text("UPDATE chunks SET embedding = NULL"))
    else:
        logger.info("Embeddings in 'chunks' already NULL, skipping.")

    # Check if queries already cleared
    res = connection.execute(text("""
        SELECT COUNT(*) FROM queries 
        WHERE embedding_original IS NOT NULL OR embedding_hyde IS NOT NULL
    """))
    queries_to_clear = res.scalar()
    
    if queries_to_clear > 0:
        logger.info(f"Clearing {queries_to_clear} embeddings in 'queries' table...")
        connection.execute(text("UPDATE queries SET embedding_original = NULL, embedding_hyde = NULL"))
    else:
        logger.info("Embeddings in 'queries' already NULL, skipping.")

def reset_vector_status(connection):
    """Reset vector_status from 'vec' to 'to_vec'."""
    logger.info("Resetting vector_status...")
    
    # Reset chunks status
    res = connection.execute(text("UPDATE chunks SET vector_status = 'to_vec' WHERE vector_status = 'vec'"))
    chunks_affected = res.rowcount
    if chunks_affected > 0:
        logger.info(f"Reset vector_status for {chunks_affected} rows in 'chunks'.")
    else:
        logger.info("No rows with status 'vec' in 'chunks'.")
        
    # Reset queries status
    res = connection.execute(text("UPDATE queries SET vector_status = 'to_vec' WHERE vector_status = 'vec'"))
    queries_affected = res.rowcount
    if queries_affected > 0:
        logger.info(f"Reset vector_status for {queries_affected} rows in 'queries'.")
    else:
        logger.info("No rows with status 'vec' in 'queries'.")

def main():
    """Main migration entry point."""
    print("=" * 80)
    print("Migration 032: Prepare for Embedding Dimension Upgrade")
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Ensure backup directory exists
    ensure_backup_dir()
    
    # 2. Backup data before modification
    backup_tables(timestamp)
    
    # 3. Perform data modifications in a transaction
    try:
        with engine.begin() as connection:
            clear_embeddings(connection)
            reset_vector_status(connection)
            
        print("\n" + "=" * 80)
        print("✅ Migration 032 completed successfully!")
        print(f"Backups stored in: {BACKUP_DIR}")
        print("Next Step: Run 'python -m vulcanlab.data.init_db -v' to apply dimension changes.")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
