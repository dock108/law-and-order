#!/usr/bin/env python3
"""
Integration tests for the Docassemble Retainer Agreement API.

This module tests the retainer agreement generation API by:
1. Ensuring Docassemble is running
2. Sending a sample payload to the retainer API
3. Verifying a valid PDF is returned
"""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

API_URL = "http://localhost:5000/api/v1/generate/retainer"
DOCKER_COMPOSE_DIR = Path(__file__).parent.parent / "docker" / "docassemble"
TIMEOUT = 120  # seconds


def is_docker_available():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


@pytest.fixture(scope="module")
def docassemble_service():
    """Start Docassemble for testing."""
    # Skip if running in CI since it will already be running
    if os.environ.get("CI"):
        yield
        return

    # Check if Docker is available
    if not is_docker_available():
        pytest.skip("Docker is not available - skipping Docassemble tests")

    # Start Docassemble
    os.chdir(DOCKER_COMPOSE_DIR)
    start = subprocess.run(
        ["docker", "compose", "up", "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"Docassemble startup stdout: {start.stdout.decode()}")
    print(f"Docassemble startup stderr: {start.stderr.decode()}")

    # Wait for services to be ready
    wait_time = 0
    interval = 5
    health_url = "http://localhost:5000/health"
    while wait_time < TIMEOUT:
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("API service is ready")
                break
        except requests.exceptions.RequestException:
            pass

        time.sleep(interval)
        wait_time += interval
        print(f"Waiting for API service to be ready ({wait_time}s elapsed)...")

    if wait_time >= TIMEOUT:
        raise TimeoutError(
            f"Docassemble API did not become available within {TIMEOUT} seconds"
        )

    # Give services additional time to fully initialize
    time.sleep(10)

    # Yield for tests to run
    yield

    # Skip teardown in CI to save time
    if os.environ.get("CI"):
        return

    # Teardown: Stop Docassemble
    os.chdir(DOCKER_COMPOSE_DIR)
    subprocess.run(["docker", "compose", "down"], stdout=subprocess.PIPE)


@pytest.mark.skip(reason="Skipped: freezes, needs refactor to unit test.")
def test_retainer_generation(docassemble_service):
    """Test retainer generation API."""
    # Prepare test payload
    payload = {
        "client": {
            "full_name": "Test Client",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
        },
        "incident": {
            "type": "Test Incident",
            "date": "January 1, 2025",
            "location": "Test Location",
        },
        "attorney": {"full_name": "Test Attorney"},
        "firm": {
            "address": "456 Law Ave",
            "city": "Law City",
            "state": "LC",
            "zip": "67890",
        },
        "fee": {"percentage": "33.33"},
    }

    # Send request to API
    response = requests.post(API_URL, json=payload, timeout=30)

    # Check response
    status_code = response.status_code
    error_msg = f"Expected status code 200, got {status_code}, "
    error_msg += f"response: {response.text}"
    assert response.status_code == 200, error_msg
    assert response.headers["Content-Type"] == "application/pdf", (
        "Response is not a PDF"
    )

    # Check that it's a valid PDF by checking for the PDF header signature
    assert response.content[:4] == b"%PDF", (
        "Response is not a valid PDF (missing header)"
    )

    # Check file size is reasonable (at least 1KB)
    assert len(response.content) > 1024, "PDF is suspiciously small"
