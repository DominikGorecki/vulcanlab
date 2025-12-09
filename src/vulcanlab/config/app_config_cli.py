"""
CLI for managing application configuration.

Usage:
    python -m vulcanlab.config.app_config_cli show
    python -m vulcanlab.config.app_config_cli set --provider openai
    python -m vulcanlab.config.app_config_cli set --db-host localhost
    python -m vulcanlab.config.app_config_cli validate
"""

import argparse
import sys
from pathlib import Path

from vulcanlab.config.app_config import (
    AppConfig,
    get_config_path,
    load_config,
    save_config,
)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format data as a simple ASCII table.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell values

    Returns:
        Formatted table as a string
    """
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Create separator line
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    # Format header
    header_row = "| " + " | ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    ) + " |"

    # Format data rows
    data_rows = []
    for row in rows:
        formatted_row = "| " + " | ".join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(row))
        ) + " |"
        data_rows.append(formatted_row)

    # Combine all parts
    table_lines = [
        separator,
        header_row,
        separator,
        *data_rows,
        separator,
    ]

    return "\n".join(table_lines)


def show_config(config: AppConfig) -> None:
    """Display current configuration in table format."""
    print(f"\nConfiguration File: {get_config_path()}")
    print()

    # Database configuration
    print("Database Configuration:")
    db_headers = ["Setting", "Value"]
    db_rows = [
        ["Admin User", config.database.admin_user],
        ["Host", config.database.host],
        ["Port", str(config.database.port)],
        ["Database Name", config.database.db_name],
        ["App User", config.database.app_user],
    ]
    print(format_table(db_headers, db_rows))
    print()

    # LLM configuration
    print("LLM Configuration:")
    llm_headers = ["Setting", "Value"]
    llm_rows = [
        ["Provider", config.llm.provider],
        ["OpenAI Light Model", config.llm.models.openai.light],
        ["OpenAI Full Model", config.llm.models.openai.full],
        ["Gemini Light Model", config.llm.models.gemini.light],
        ["Gemini Full Model", config.llm.models.gemini.full],
    ]
    print(format_table(llm_headers, llm_rows))
    print()

    # Paths configuration
    print("Paths Configuration:")
    paths_headers = ["Setting", "Value"]
    paths_rows = [
        ["Input Directory", config.paths.input_dir],
        ["Output Directory", config.paths.output_dir],
    ]
    print(format_table(paths_headers, paths_rows))
    print()


def set_config_value(args: argparse.Namespace) -> int:
    """Set configuration values and save."""
    try:
        config = load_config()

        # Database settings
        if args.db_admin_user:
            config.database.admin_user = args.db_admin_user
        if args.db_host:
            config.database.host = args.db_host
        if args.db_port:
            config.database.port = args.db_port
        if args.db_name:
            config.database.db_name = args.db_name
        if args.db_app_user:
            config.database.app_user = args.db_app_user

        # LLM settings
        if args.provider:
            if args.provider not in ["openai", "gemini"]:
                print(f"Error: Invalid provider '{args.provider}'. Must be 'openai' or 'gemini'", file=sys.stderr)
                return 1
            config.llm.provider = args.provider
        if args.openai_light:
            config.llm.models.openai.light = args.openai_light
        if args.openai_full:
            config.llm.models.openai.full = args.openai_full
        if args.gemini_light:
            config.llm.models.gemini.light = args.gemini_light
        if args.gemini_full:
            config.llm.models.gemini.full = args.gemini_full

        # Path settings
        if args.input_dir:
            input_path = Path(args.input_dir)
            if not input_path.is_absolute():
                print(f"Error: input_dir must be an absolute path, got: {args.input_dir}", file=sys.stderr)
                return 1
            config.paths.input_dir = str(input_path)
        if args.output_dir:
            output_path = Path(args.output_dir)
            if not output_path.is_absolute():
                print(f"Error: output_dir must be an absolute path, got: {args.output_dir}", file=sys.stderr)
                return 1
            config.paths.output_dir = str(output_path)

        # Save configuration
        save_config(config)
        print("Configuration updated successfully!")
        print()
        show_config(config)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def validate_config() -> int:
    """Validate configuration file."""
    try:
        config = load_config()
        print("Configuration is valid!")
        print()
        show_config(config)
        return 0

    except FileNotFoundError:
        print(f"Error: Configuration file not found at {get_config_path()}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Manage application configuration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s show                                      # Display current config
  %(prog)s set --provider openai                     # Change LLM provider
  %(prog)s set --openai-light gpt-4o-mini            # Change OpenAI light model
  %(prog)s set --db-host localhost --db-port 5433    # Change database settings
  %(prog)s set --input-dir C:\\data\\input           # Set input directory (absolute path)
  %(prog)s set --output-dir C:\\data\\output         # Set output directory (absolute path)
  %(prog)s validate                                  # Validate config file
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # show command
    subparsers.add_parser("show", help="Display current configuration")

    # set command
    set_parser = subparsers.add_parser("set", help="Update configuration settings")

    # Database settings
    set_parser.add_argument("--db-admin-user", type=str, help="PostgreSQL admin username")
    set_parser.add_argument("--db-host", type=str, help="Database host")
    set_parser.add_argument("--db-port", type=int, help="Database port")
    set_parser.add_argument("--db-name", type=str, help="Database name")
    set_parser.add_argument("--db-app-user", type=str, help="Application user name")

    # LLM settings
    set_parser.add_argument("--provider", type=str, choices=["openai", "gemini"], help="LLM provider")
    set_parser.add_argument("--openai-light", type=str, help="OpenAI light model name")
    set_parser.add_argument("--openai-full", type=str, help="OpenAI full model name")
    set_parser.add_argument("--gemini-light", type=str, help="Gemini light model name")
    set_parser.add_argument("--gemini-full", type=str, help="Gemini full model name")

    # Path settings
    set_parser.add_argument("--input-dir", type=str, help="Absolute path to input directory")
    set_parser.add_argument("--output-dir", type=str, help="Absolute path to output directory")

    # validate command
    subparsers.add_parser("validate", help="Validate configuration file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "show":
            config = load_config()
            show_config(config)
            return 0

        elif args.command == "set":
            return set_config_value(args)

        elif args.command == "validate":
            return validate_config()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
