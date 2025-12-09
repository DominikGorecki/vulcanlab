"""
Environment variable utilities for secure configuration management.

This module provides fail-fast loading of required environment variables
with clear error messages to guide developers toward proper configuration.
"""

import os
from typing import Optional


class MissingEnvironmentVariableError(Exception):
    """Raised when a required environment variable is not set.

    This error indicates that configuration is incomplete and provides
    actionable guidance for resolving the issue.
    """
    pass


def get_required_env_var(var_name: str, description: Optional[str] = None) -> str:
    """Get a required environment variable with fail-fast behavior.

    This function enforces explicit configuration by raising a clear error
    if the environment variable is not set. No fallback values are provided
    to ensure security and prevent silent failures.

    Args:
        var_name: Name of the environment variable to retrieve.
        description: Optional description of what the variable is used for.

    Returns:
        The value of the environment variable.

    Raises:
        MissingEnvironmentVariableError: If the environment variable is not set.

    Example:
        >>> password = get_required_env_var("POSTGRES_APP_PASSWORD", "Application database password")
    """
    value = os.getenv(var_name)

    if value is None:
        error_msg = _build_error_message(var_name, description)
        raise MissingEnvironmentVariableError(error_msg)

    return value


def _build_error_message(var_name: str, description: Optional[str]) -> str:
    """Build a helpful error message for missing environment variables.

    Args:
        var_name: Name of the missing environment variable.
        description: Optional description of the variable's purpose.

    Returns:
        Formatted error message with troubleshooting guidance.
    """
    lines = [
        f"ERROR: Required environment variable not configured",
        f"",
        f"Environment variable '{var_name}' is not set.",
    ]

    if description:
        lines.append(f"")
        lines.append(f"Purpose: {description}")

    lines.extend([
        f"",
        f"To fix this:",
        f"1. Create a .env file in the project root (if it doesn't exist)",
        f"2. Add: {var_name}=your_value_here",
        f"3. See .env.example for a complete template",
        f"",
        f"For more help, see: README.md section 'Secrets Configuration (.env)'",
    ])

    return "\n".join(lines)
