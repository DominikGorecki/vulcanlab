"""
CLI for database health checks.

Usage:
    python -m vulcanlab.data.db_health_check_cli
"""

import argparse
import sys

from vulcanlab.data.db_health_check import run_all_health_checks


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Run database health checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                # Run all health checks
        """
    )

    parser.parse_args()

    try:
        print("\n" + "=" * 70)
        print("DATABASE HEALTH CHECK")
        print("=" * 70 + "\n")

        results = run_all_health_checks()

        # Track pass/fail counts
        passed = 0
        failed = 0

        # Display results
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            status_symbol = "+" if result.passed else "X"

            # Simple pass/fail format
            print(f"[{status_symbol}] {status:4} {result.name}")

            if not result.passed:
                print(f"       {result.message}")
                if result.details:
                    print(f"       → {result.details}")

            if result.passed:
                passed += 1
            else:
                failed += 1

        # Summary
        print("\n" + "=" * 70)
        total = passed + failed
        print(f"SUMMARY: {passed}/{total} checks passed")

        if failed > 0:
            print(f"         {failed} checks failed")
            print("\nTo fix database issues, run:")
            print("  python -m vulcanlab.data.init_db -v")

        print("=" * 70 + "\n")

        # Return non-zero exit code if any checks failed
        return 1 if failed > 0 else 0

    except Exception as e:
        print(f"Error running health checks: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
