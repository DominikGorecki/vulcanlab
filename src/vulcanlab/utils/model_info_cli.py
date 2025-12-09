"""
CLI for displaying active LLM configuration information.

Usage:
    python -m vulcanlab.utils.model_info_cli
"""

import argparse
import sys

from vulcanlab.utils.model_info import get_active_llm_info


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


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Display active LLM configuration information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                # Display current LLM configuration
        """
    )

    parser.parse_args()

    try:
        info = get_active_llm_info()

        # Create table data
        headers = ["Setting", "Value"]
        rows = [
            ["Provider", info.provider],
            ["Light Model", info.light_model],
            ["Full Model", info.full_model],
        ]

        # Print formatted table
        table = format_table(headers, rows)
        print("\nActive LLM Configuration:")
        print(table)
        print()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
