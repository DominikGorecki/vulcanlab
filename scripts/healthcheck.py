#!/usr/bin/env python3
"""
VulcanLab Health Check Script

Validates all services are running correctly:
- Supervisord process manager
- PostgreSQL database
- FastAPI backend
- Next.js frontend
- Database extensions (vector, age)
"""

import sys
import os
import subprocess
import time
import urllib.request
import json
from typing import List, Tuple

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")

def print_failure(text: str):
    """Print failure message."""
    print(f"{RED}✗{RESET} {text}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")

def run_command(cmd: List[str], timeout: int = 5) -> Tuple[bool, str, str]:
    """
    Run a shell command and return success status and output.

    Args:
        cmd: Command and arguments as list
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_supervisord() -> bool:
    """Check if supervisord is running."""
    print("Checking supervisord process manager...")
    success, stdout, stderr = run_command(["pgrep", "-f", "supervisord"])

    if success and stdout.strip():
        print_success("Supervisord is running")
        return True
    else:
        print_failure("Supervisord is not running")
        return False

def check_service_status(service_name: str) -> bool:
    """Check if a supervised service is running."""
    print(f"Checking {service_name} service status...")
    success, stdout, stderr = run_command(["supervisorctl", "status", service_name])

    if success and "RUNNING" in stdout:
        print_success(f"{service_name} is RUNNING")
        return True
    else:
        print_failure(f"{service_name} is not running")
        if stdout:
            print(f"  Status: {stdout.strip()}")
        return False

def check_postgresql() -> bool:
    """Check PostgreSQL database connectivity."""
    print("Checking PostgreSQL database connectivity...")

    # First check if service is running
    if not check_service_status("postgresql"):
        return False

    # Test database connection
    success, stdout, stderr = run_command([
        "psql",
        "-U", "postgres",
        "-d", os.getenv("POSTGRES_DB", "vulcanlab_test"),
        "-c", "SELECT 1;",
        "-t"
    ])

    if success:
        print_success("PostgreSQL database is accessible")
        return True
    else:
        print_failure("Cannot connect to PostgreSQL database")
        if stderr:
            print(f"  Error: {stderr.strip()}")
        return False

def check_database_extensions() -> bool:
    """Check that required PostgreSQL extensions are installed."""
    print("Checking PostgreSQL extensions (vector, age)...")

    success, stdout, stderr = run_command([
        "psql",
        "-U", "postgres",
        "-d", os.getenv("POSTGRES_DB", "vulcanlab_test"),
        "-c", "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'age');",
        "-t"
    ])

    if success:
        extensions = stdout.strip().split('\n')
        extensions = [ext.strip() for ext in extensions if ext.strip()]

        if 'vector' in extensions and 'age' in extensions:
            print_success("Extensions installed: vector, age")
            return True
        else:
            print_failure(f"Missing extensions. Found: {extensions}")
            return False
    else:
        print_failure("Cannot query extensions")
        return False

def check_backend_api() -> bool:
    """Check FastAPI backend health endpoint."""
    print("Checking FastAPI backend API...")

    # First check if service is running
    if not check_service_status("backend"):
        return False

    # Give backend a moment to start if it just came up
    time.sleep(2)

    # Test health endpoint
    try:
        url = "http://localhost:8000/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print_success(f"Backend API is healthy: {data.get('status', 'unknown')}")
                return True
            else:
                print_failure(f"Backend API returned status code: {response.status}")
                return False
    except urllib.error.URLError as e:
        print_failure(f"Cannot reach backend API: {e.reason}")
        return False
    except Exception as e:
        print_failure(f"Backend API check failed: {str(e)}")
        return False

def check_frontend() -> bool:
    """Check Next.js frontend accessibility."""
    print("Checking Next.js frontend...")

    # First check if service is running
    if not check_service_status("frontend"):
        return False

    # Give frontend a moment to start
    time.sleep(2)

    # Test frontend is responding
    try:
        url = "http://localhost:3000"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print_success("Frontend is accessible")
                return True
            else:
                print_failure(f"Frontend returned status code: {response.status}")
                return False
    except urllib.error.URLError as e:
        print_failure(f"Cannot reach frontend: {e.reason}")
        return False
    except Exception as e:
        print_failure(f"Frontend check failed: {str(e)}")
        return False

def check_directories() -> bool:
    """Check that required directories exist and are writable."""
    print("Checking data directories...")

    directories = [
        "/app/data/input",
        "/app/data/output",
        "/var/log/supervisor"
    ]

    all_ok = True
    for directory in directories:
        if os.path.exists(directory) and os.access(directory, os.W_OK):
            print_success(f"{directory} exists and is writable")
        else:
            print_failure(f"{directory} missing or not writable")
            all_ok = False

    return all_ok

def print_troubleshooting():
    """Print troubleshooting commands."""
    print_header("Troubleshooting Commands")

    print("View service status:")
    print("  supervisorctl status")
    print()

    print("View logs:")
    print("  tail -f /var/log/supervisor/backend.log")
    print("  tail -f /var/log/supervisor/frontend.log")
    print("  tail -f /var/log/supervisor/postgresql.log")
    print()

    print("Restart a service:")
    print("  supervisorctl restart backend")
    print("  supervisorctl restart frontend")
    print("  supervisorctl restart postgresql")
    print()

    print("Test database connection:")
    print("  psql -U postgres -d vulcanlab_test -c 'SELECT version();'")
    print()

    print("Test backend API:")
    print("  curl http://localhost:8000/health")
    print()

def main():
    """Run all health checks."""
    print_header("VulcanLab Health Check")

    checks = [
        ("Supervisord", check_supervisord),
        ("PostgreSQL", check_postgresql),
        ("Database Extensions", check_database_extensions),
        ("Backend API", check_backend_api),
        ("Frontend", check_frontend),
        ("Directories", check_directories),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_failure(f"{check_name} check failed with exception: {str(e)}")
            results.append((check_name, False))
        print()  # Blank line between checks

    # Summary
    print_header("Health Check Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        if result:
            print_success(f"{check_name}")
        else:
            print_failure(f"{check_name}")

    print()
    if passed == total:
        print(f"{GREEN}All {total} health checks passed!{RESET}")
        print()
        return 0
    else:
        print(f"{RED}{total - passed} of {total} health checks failed.{RESET}")
        print()
        print_troubleshooting()
        return 1

if __name__ == "__main__":
    sys.exit(main())
