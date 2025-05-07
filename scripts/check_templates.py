#!/usr/bin/env python3
"""
PII Check Script for Templates.

This script checks templates for personally identifiable information (PII).
"""

import re
import sys
from pathlib import Path

# PII patterns to check for
PII_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b\d{9}\b",  # 9-digit number (potential SSN)
    r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit card
    r"\b\d{16}\b",  # 16-digit number (potential credit card)
    r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # Email address
]


def check_templates():
    """Check templates for PII."""
    template_dir = Path("templates")
    if not template_dir.exists():
        print("Templates directory doesn't exist")
        return 0

    template_files = list(template_dir.glob("**/*"))
    if not template_files:
        print("No template files found")
        return 0

    found_pii = False
    for template_file in template_files:
        if template_file.is_file():
            try:
                content = template_file.read_text()
                for pattern in PII_PATTERNS:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f"PII found in {template_file}: {matches}")
                        found_pii = True
            except Exception as e:
                print(f"Error reading {template_file}: {e}")

    return 1 if found_pii else 0


if __name__ == "__main__":
    sys.exit(check_templates())
