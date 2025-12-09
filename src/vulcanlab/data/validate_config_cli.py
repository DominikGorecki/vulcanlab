"""
Configuration validation CLI tool.

This tool helps developers validate their environment configuration before
running the application. It checks for required environment variables and
tests database connectivity.

Usage:
    python -m vulcanlab.data.validate_config_cli
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from vulcanlab.config import load_config
from vulcanlab.data.env_utils import get_required_env_var, MissingEnvironmentVariableError


# Required environment variables with descriptions
REQUIRED_ENV_VARS = [
    ("POSTGRES_ADMIN_PASSWORD", "PostgreSQL admin user password"),
    ("POSTGRES_APP_PASSWORD", "PostgreSQL application user password"),
]

# Optional but recommended environment variables
OPTIONAL_ENV_VARS = [
    ("LLM_OPENAI_API_KEY", "OpenAI API key for GPT models"),
    ("LLM_GOOGLE_API_KEY", "Google API key for Gemini models"),
]


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists.

    Returns:
        Tuple of (success, message).
    """
    env_path = Path(".env")
    if env_path.exists():
        return True, f"[OK] Found .env file at: {env_path.absolute()}"
    else:
        return False, (
            f"[FAIL] .env file not found at: {env_path.absolute()}\n"
            f"       Please create .env file. See .env.example for template."
        )


def check_required_env_vars(verbose: bool = False) -> Tuple[bool, List[str]]:
    """Check if all required environment variables are set.

    Args:
        verbose: If True, show all checks. If False, only show failures.

    Returns:
        Tuple of (all_present, messages).
    """
    messages = []
    all_present = True

    for var_name, description in REQUIRED_ENV_VARS:
        try:
            value = get_required_env_var(var_name, description)
            if verbose:
                # Don't show actual password values
                masked_value = "*" * min(len(value), 8)
                messages.append(f"[OK] {var_name}: {masked_value}")
        except MissingEnvironmentVariableError:
            all_present = False
            messages.append(f"[FAIL] {var_name}: NOT SET (Required: {description})")

    return all_present, messages


def check_optional_env_vars() -> List[str]:
    """Check optional environment variables.

    Returns:
        List of status messages.
    """
    import os
    messages = []

    for var_name, description in OPTIONAL_ENV_VARS:
        value = os.getenv(var_name)
        if value:
            masked_value = "*" * min(len(value), 8)
            messages.append(f"[OK] {var_name}: {masked_value}")
        else:
            messages.append(f"[INFO] {var_name}: Not set ({description})")

    return messages


def check_database_connectivity(check_admin: bool = False) -> Tuple[bool, str]:
    """Check database connectivity.

    Args:
        check_admin: If True, also test admin connection.

    Returns:
        Tuple of (success, message).
    """
    try:
        # Load configuration
        db_config = load_config().database
        app_password = get_required_env_var("POSTGRES_APP_PASSWORD")

        # Build connection URL
        db_url = (
            f"postgresql+psycopg://{db_config.app_user}:{app_password}"
            f"@{db_config.host}:{db_config.port}/{db_config.db_name}"
        )

        # Try to connect
        engine = create_engine(db_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        message = (
            f"[OK] Database connection successful\n"
            f"     Host: {db_config.host}:{db_config.port}\n"
            f"     Database: {db_config.db_name}\n"
            f"     User: {db_config.app_user}"
        )

        # Test admin connection if requested
        if check_admin:
            from vulcanlab.data.database import get_admin_database_url
            admin_url = get_admin_database_url()
            admin_engine = create_engine(admin_url, echo=False)
            with admin_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            message += f"\n     [OK] Admin connection also successful"

        return True, message

    except MissingEnvironmentVariableError as e:
        return False, f"[FAIL] Cannot test connectivity: {str(e)}"
    except Exception as e:
        return False, (
            f"[FAIL] Database connection failed: {str(e)}\n"
            f"       Check that PostgreSQL is running and credentials are correct"
        )


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Validate VulcanLab environment configuration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Quick validation
  %(prog)s --verbose          # Show all checks
  %(prog)s --check-admin      # Also test admin database connection
  %(prog)s --skip-db          # Skip database connectivity test
        """
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed information for all checks"
    )

    parser.add_argument(
        "--check-admin",
        action="store_true",
        help="Also test admin database connection"
    )

    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database connectivity test"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    print("=" * 60)
    print("VulcanLab Configuration Validation")
    print("=" * 60)
    print()

    # Track overall success
    all_checks_passed = True

    # Check .env file
    print("1. Checking .env file...")
    env_exists, env_message = check_env_file()
    print(f"   {env_message}")
    if not env_exists:
        all_checks_passed = False
    print()

    # Check required environment variables
    print("2. Checking required environment variables...")
    vars_present, var_messages = check_required_env_vars(verbose=args.verbose)
    for msg in var_messages:
        print(f"   {msg}")
    if not vars_present:
        all_checks_passed = False
    print()

    # Check optional environment variables
    if args.verbose:
        print("3. Checking optional environment variables...")
        opt_messages = check_optional_env_vars()
        for msg in opt_messages:
            print(f"   {msg}")
        print()

    # Check database connectivity
    if not args.skip_db:
        section_num = 4 if args.verbose else 3
        print(f"{section_num}. Checking database connectivity...")
        db_success, db_message = check_database_connectivity(check_admin=args.check_admin)
        print(f"   {db_message}")
        if not db_success:
            all_checks_passed = False
        print()

    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("[SUCCESS] All checks passed! Configuration is valid.")
        print()
        print("You can now run:")
        print("  python -m vulcanlab.data.init_db    # Initialize database")
        print("  python -m vulcanlab_api.main        # Start API server")
        return 0
    else:
        print("[FAILED] Some checks failed. Please fix the issues above.")
        print()
        print("For help, see:")
        print("  - .env.example for environment variable template")
        print("  - README.md section 'Secrets Configuration (.env)'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
