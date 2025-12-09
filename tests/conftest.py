"""Shared test fixtures for the test suite.

This module provides shared test utilities.

Note: Database fixtures have been removed. Unit tests should use mocks from
tests/unit/mock_helpers.py. Integration tests should use fixtures from
tests/integration/conftest.py (when implemented).
"""

import pytest

# If you need to add shared non-database fixtures for all tests, add them here.
# Example:
#
# @pytest.fixture
# def sample_config():
#     return {"key": "value"}
