
from sqlalchemy import text
from vulcanlab.data.database import engine

def run_migration_028():
    with open('migrations/028_add_research_tables.sql', 'r') as f:
        sql = f.read()
    
    # Split by -- ================== to avoid issues with some multi-statement blocks if any,
    # but SQLAlchemy's engine.connect().execute(text(sql)) usually handles multiple statements in one call for PostgreSQL.
    
    print("Applying migration 028...")
    try:
        with engine.connect() as connection:
            # We need to execute the script. SQLAlchemy might struggle with multiple statements in one execute call depending on the driver.
            # However, psycopg usually handles it. Let's try.
            # Note: The SQL file contains multiple statements.
            connection.execute(text(sql))
            connection.commit()
        print("✅ Migration 028 applied successfully.")
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration_028()
