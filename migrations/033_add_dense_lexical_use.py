"""
Migration Script: 033_backfill_dense_lexical_use.py

This script backfills the 'dense_lexical_use' column for existing chunks.
It marks chunks that are intended for dense and lexical retrieval (RAG).

Note: The schema alteration (adding the column and index) is handled
automatically by 'src/vulcanlab/data/init_db.py'.

Usage:
    python migrations/033_add_dense_lexical_use.py
"""

import logging
import sys
from sqlalchemy import text
from vulcanlab.data.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backfill_dense_lexical_use():
    """Backfill dense_lexical_use data for existing chunks."""
    logger.info("Starting migration 033: Backfill dense_lexical_use...")
    
    try:
        with engine.begin() as connection:
            # Backfill data: set to TRUE for levels containing 'chunk'
            # This matches 'chunk', 'H1-chunk', 'H2-chunk', etc.
            logger.info("Backfilling 'dense_lexical_use' data...")
            res = connection.execute(text("""
                UPDATE chunks 
                SET dense_lexical_use = TRUE 
                WHERE level LIKE '%chunk%'
            """))
            logger.info(f"Backfilled {res.rowcount} rows.")
            
        logger.info("✅ Migration 033 completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        # If the column doesn't exist yet, remind the user to run init_db
        if 'column "dense_lexical_use" does not exist' in str(e):
            logger.error("TIP: Run 'python -m vulcanlab.data.init_db -v' first to apply schema changes.")
        sys.exit(1)

if __name__ == "__main__":
    backfill_dense_lexical_use()
