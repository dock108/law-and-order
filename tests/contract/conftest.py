"""Configuration for contract tests, enabling experimental OpenAPI 3.1 support."""

import schemathesis


def pytest_configure(config):
    """Enable experimental features for Schemathesis before tests run."""
    schemathesis.experimental.OPEN_API_3_1.enable()
