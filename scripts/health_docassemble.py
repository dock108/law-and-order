#!/usr/bin/env python3
"""
Health check script for Docassemble.

This script checks if Docassemble is running properly by making a request
to the health check endpoint. Exits with 0 if Docassemble is healthy,
non-zero otherwise.
"""

import argparse
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_health(url: str, max_retries: int = 10, retry_delay: int = 5) -> bool:
    """
    Check if Docassemble is healthy.

    Args:
        url: The URL to the health check endpoint.
        max_retries: Maximum number of retries.
        retry_delay: Delay between retries in seconds.

    Returns:
        True if healthy, False otherwise.
    """
    for attempt in range(max_retries):
        try:
            req = Request(url)
            with urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8")
                if response.status == 200 and "OK" in content:
                    print(f"Docassemble is healthy after {attempt + 1} attempt(s).")
                    return True
                else:
                    print(f"Unexpected response: {response.status} - {content}")
        except HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
        except URLError as e:
            print(f"URL Error: {e.reason}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        if attempt < max_retries - 1:
            print(
                f"Retrying in {retry_delay} seconds... "
                f"(Attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(retry_delay)

    print(f"Failed to connect to Docassemble after {max_retries} attempts.")
    return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check Docassemble health.")
    parser.add_argument(
        "--url",
        default="http://localhost:8100/health",
        help="URL to the health check endpoint.",
    )
    parser.add_argument(
        "--retries", type=int, default=10, help="Maximum number of retries."
    )
    parser.add_argument(
        "--delay", type=int, default=5, help="Delay between retries in seconds."
    )
    args = parser.parse_args()

    healthy = check_health(args.url, args.retries, args.delay)
    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
