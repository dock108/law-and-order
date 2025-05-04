#!/usr/bin/env python
"""
Script to check templates for any remaining PII.

This script scans all template files for patterns that might indicate
leftover PII such as real names, phone numbers, SSNs, etc.
"""

import re
import sys
from pathlib import Path

# Define the patterns to search for
PATTERNS = {
    # e.g., JOHN DOE
    "ALL_CAPS_NAME": r"\b[A-Z]{2,}(?:\s+[A-Z]{2,})+\b",
    # Phone numbers in various formats
    "PHONE_NUMBER": (
        r"\b(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
    ),
    "SSN": r"\b[0-9]{3}[-]?[0-9]{2}[-]?[0-9]{4}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ADDRESS": (
        r"\b\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
        r"Drive|Dr|Court|Ct|Lane|Ln|Way|Circle|Cir|Trail|Tr|Place|Pl|Terrace|Ter)\b"
    ),
    "DATE_OF_BIRTH": r"\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/(?:19|20)\d{2}\b",
}

# Common legal document headings and terms that appear in ALL CAPS - these are not PII
LEGAL_TERMS = [
    "RETAINER AGREEMENT",
    "AUTHORIZATION FOR RELEASE",
    "HIPAA",
    "SETTLEMENT DISBURSEMENT SHEET",
    "SETTLEMENT PROCEEDS",
    "MEDICAL LIENS AND BILLS",
    "OTHER LIENS",
    "NET TO CLIENT",
    "FACTS OF THE INCIDENT",
    "INJURIES AND TREATMENT",
    "MEDICAL EXPENSES",
    "LOST WAGES",
    "PAIN AND SUFFERING",
    "SETTLEMENT DEMAND",
    "IN WITNESS WHEREOF",
    "SCOPE OF REPRESENTATION",
    "LEGAL FEES",
    "NO GUARANTEE",
    "THIS AGREEMENT",
    "MEMORANDUM",
    "CLIENT",
    "ATTORNEY",
    "THE LAW FIRM",
    "EXPENSES",
    "TERMINATION",
    "DRUG TREATMENT",
    "MENTAL HEALTH TREATMENT",
    "CONFIDENTIAL HIV",
    "AIDS RELATED INFORMATION",
    "RELEASE OF ALL CLAIMS",
    "KNOW ALL MEN BY THESE PRESENTS",
    "THE UNDERSIGNED HAS READ THE FOREGOING RELEASE AND FULLY UNDERSTANDS IT",
    "STATE OF",
    "COUNTY OF",
    "NOTARY PUBLIC",
    "PERSONAL INFORMATION",
    "EMPLOYMENT INFORMATION",
    "INCIDENT INFORMATION",
    "MEDICAL TREATMENT",
    "INSURANCE INFORMATION",
    "PREVIOUS CLAIMS",
    "REFERRAL INFORMATION",
    "ACCEPTANCE OF LIEN TERMS",
    "COMES NOW",
    "AND VENUE",
    "FACTUAL ALLEGATIONS",
    "CAUSE OF ACTION",
    "JURY DEMAND",
    "COMPLAINT",
    "WHEREFORE",
    "LAWSUITS",
]

# Files and directories to exclude (add more as needed)
EXCLUDE_DIRS = [".git", ".github", "venv", "__pycache__"]
EXCLUDE_FILES = ["check_templates.py"]

# File extensions to include
INCLUDE_EXTENSIONS = [".txt", ".md", ".html", ".docx", ".pdf", ".rtf"]

# Skip jinja tags
JINJA_TAG_PATTERN = r"\{\{.*?\}\}"


def is_excluded(path):
    """Check if a path should be excluded from scanning."""
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in path.parts:
            return True
    return path.name in EXCLUDE_FILES


def should_include(path):
    """Check if a file should be included in scanning based on extension."""
    return path.suffix.lower() in INCLUDE_EXTENSIONS


def get_template_files():
    """Get all template files to scan."""
    template_dir = Path("templates")
    if not template_dir.exists():
        print(f"Error: Template directory {template_dir} not found.")
        sys.exit(1)

    files = []
    for path in template_dir.glob("**/*"):
        if path.is_file() and should_include(path) and not is_excluded(path):
            files.append(path)

    return files


def is_legal_term(text):
    """Check if the text matches a common legal term or heading."""
    for term in LEGAL_TERMS:
        if term in text:
            return True
    return False


def check_file_for_pii(file_path):
    """
    Check a file for patterns that might indicate PII.

    Returns:
        list: A list of (line_number, pattern_type, matched_text) tuples.
    """
    matches = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Skip jinja tags
                line_without_jinja = re.sub(JINJA_TAG_PATTERN, "", line)

                for pattern_name, pattern in PATTERNS.items():
                    for match in re.finditer(pattern, line_without_jinja):
                        matched_text = match.group(0)

                        # Skip if it's a common legal term
                        if pattern_name == "ALL_CAPS_NAME" and is_legal_term(
                            matched_text
                        ):
                            continue

                        matches.append((line_num, pattern_name, matched_text))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return matches


def main():
    """Main function to scan all template files for PII."""
    print("Scanning templates for PII...")

    files = get_template_files()
    if not files:
        print("No template files found.")
        return 0

    print(f"Found {len(files)} template files to scan.")

    all_matches = []
    for file_path in files:
        matches = check_file_for_pii(file_path)
        if matches:
            all_matches.append((file_path, matches))

    if all_matches:
        print("\nPotential PII found:")
        for file_path, matches in all_matches:
            print(f"\n{file_path}:")
            for line_num, pattern_type, matched_text in matches:
                print(f"  Line {line_num}: {pattern_type} - {matched_text}")
        return 1
    else:
        print("\nNo PII detected in templates.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
