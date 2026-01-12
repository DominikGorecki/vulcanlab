"""
Trigger creation functions and shared helpers.

Contains reusable patterns for creating PostgreSQL triggers
and transferring ownership to application users.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

from vulcanlab.config import load_config
from ..database import engine


def transfer_function_ownership(
    function_names: list[str],
    sequence_names: list[str] | None = None,
    verbose: bool = False
) -> None:
    """
    Transfer ownership of PostgreSQL functions and sequences to app user.

    This is necessary when init_db is run with admin credentials but the
    app user needs to own the functions for proper permissions.

    Args:
        function_names: List of function names (without parentheses) to transfer.
        sequence_names: Optional list of sequence names to transfer.
        verbose: If True, print progress information.
    """
    db_config = load_config().database
    app_user = db_config.app_user

    try:
        with engine.connect() as conn:
            for func_name in function_names:
                conn.execute(text(f'ALTER FUNCTION {func_name}() OWNER TO "{app_user}"'))

            if sequence_names:
                for seq_name in sequence_names:
                    conn.execute(text(f'ALTER SEQUENCE IF EXISTS {seq_name} OWNER TO "{app_user}"'))

            conn.commit()

            if verbose:
                items = function_names + (sequence_names or [])
                print(f"Transferred ownership of {', '.join(items)} to {app_user}")
    except Exception as e:
        if verbose:
            print(f"Note: Could not transfer ownership (this is okay if running as app user): {e}")


def create_timestamp_trigger(
    conn: Connection,
    table_name: str,
    column_name: str = "updated_at"
) -> str:
    """
    Create a standard timestamp trigger for auto-updating a column.

    Creates a trigger function and trigger that automatically updates
    the specified column to CURRENT_TIMESTAMP on row updates.

    Args:
        conn: Database connection to use.
        table_name: Name of the table to add trigger to.
        column_name: Name of the timestamp column (default: "updated_at").

    Returns:
        The function name created, for use with transfer_function_ownership.
    """
    func_name = f"update_{table_name}_{column_name}"
    trigger_name = f"trigger_{func_name}"

    # Create trigger function
    conn.execute(text(f"""
        CREATE OR REPLACE FUNCTION {func_name}()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.{column_name} = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    # Drop existing trigger if any
    conn.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}"))

    # Create trigger
    conn.execute(text(f"""
        CREATE TRIGGER {trigger_name}
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION {func_name}()
    """))

    return func_name


def create_io_files_triggers(verbose: bool = False) -> None:
    """
    Create triggers for io_files table.

    The table itself is created by SQLAlchemy's create_all(), but we need
    to manually add the trigger for automatically updating the updated_at column.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating io_files triggers...")

    with engine.connect() as conn:
        # Create trigger function to automatically update updated_at timestamp
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_io_files_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_io_files_updated_at ON io_files"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_io_files_updated_at
                BEFORE UPDATE ON io_files
                FOR EACH ROW
                EXECUTE FUNCTION update_io_files_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_io_files_updated_at"],
        verbose=verbose
    )

    if verbose:
        print("io_files triggers created successfully")


def create_experiments_triggers(verbose: bool = False) -> None:
    """
    Create triggers for experiments table.

    Creates trigger to auto-update the updated_at timestamp.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating experiments triggers...")

    with engine.connect() as conn:
        # Create trigger function for updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_experiments_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger
        conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_experiments_updated_at ON experiments"))
        conn.execute(text("""
            CREATE TRIGGER trigger_update_experiments_updated_at
                BEFORE UPDATE ON experiments
                FOR EACH ROW
                EXECUTE FUNCTION update_experiments_updated_at()
        """))

        conn.commit()

    # Transfer ownership to app user
    transfer_function_ownership(
        function_names=["update_experiments_updated_at"],
        verbose=verbose
    )

    if verbose:
        print("Experiments triggers created successfully")
