"""Pytest tests to guard templates against PII and inconsistencies."""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

# --- Configuration ---

TEMPLATE_DIRS = [Path("templates"), Path("email_templates")]
REFERENCE_FILE = Path("docs/TEMPLATE_REFERENCE.md")
EXCLUDE_DIRS = [
    ".git",
    ".github",
    "venv",
    "__pycache__",
    "node_modules",
    "tests/assets",
]
INCLUDE_EXTENSIONS = [".txt", ".md", ".html", ".jinja2", ".j2"]

# Patterns to detect potential PII
# Improved regexes based on user request
PII_PATTERNS: Dict[str, str] = {
    # Matches names like "John Doe", "Mary-Ann Jones", "O'Malley",
    # allowing hyphens/apostrophes
    "NAME": r"\b[A-Z][a-z'-]+(?:\s+[A-Z][a-z'-]+)+\b",
    # Matches various US phone formats
    "PHONE_NUMBER": r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
    # Matches MM/DD/YYYY format
    "DATE": r"\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(19|20)\d{2}\b",
    # Matches SSN
    "SSN": r"\b\d{3}-?\d{2}-?\d{4}\b",
    # Matches unwrapped $ amounts (e.g., $100, $1,234.56) - needs refinement
    # Looks for $ followed by digits, commas, periods, not inside {{ }}
    "UNWRAPPED_DOLLAR": r"(?<!\{\{[^{}]*)\$\s*\d[\d,.]*(?!.*?\}\})",
    # Matches empty Jinja tags {{ }} or {{}} with optional whitespace
    "EMPTY_JINJA_TAG": r"\{\{\s*\}\}",
}

# --- Helper Functions ---


def _get_template_files() -> List[Path]:
    """Get all template files to scan."""
    files = []
    for template_dir in TEMPLATE_DIRS:
        if not template_dir.is_dir():
            continue  # Ignore if directory doesn't exist
        for path in template_dir.glob("**/*"):
            # Check exclusions
            is_excluded = False
            for exclude_dir in EXCLUDE_DIRS:
                if exclude_dir in path.parts:
                    is_excluded = True
                    break
            if is_excluded:
                continue

            if path.is_file() and path.suffix.lower() in INCLUDE_EXTENSIONS:
                files.append(path)
    return files


def _extract_tags_from_reference(ref_file: Path) -> Set[str]:
    """Extract valid Jinja tags from the reference markdown file."""
    if not ref_file.is_file():
        pytest.fail(f"Reference file not found: {ref_file}")

    # Simple extraction: find patterns like `{{ tag.name }}`
    tag_pattern = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")
    allowed_tags = set()
    try:
        with open(ref_file, "r", encoding="utf-8") as f:
            content = f.read()
            for match in tag_pattern.finditer(content):
                allowed_tags.add(match.group(1).strip())
    except Exception as e:
        pytest.fail(f"Error reading reference file {ref_file}: {e}")

    if not allowed_tags:
        print(f"Warning: No tags extracted from {ref_file}. Check its format.")

    return allowed_tags


def _find_jinja_tags_in_file(file_path: Path) -> List[Tuple[int, str]]:
    """Find all Jinja tags {{ ... }} in a file."""
    # tag_pattern = re.compile(r"(\{\{.*?\}\})") # Unused variable
    line_tag_pattern = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")
    found_tags = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Find all distinct tags used in the line
                tags_in_line = set()
                for match in line_tag_pattern.finditer(line):
                    tags_in_line.add(match.group(1).strip())

                for tag in tags_in_line:
                    found_tags.append((line_num, tag))

    except Exception as e:
        print(f"Warning: Could not read/parse file {file_path}: {e}", file=sys.stderr)
    return found_tags


def _check_file_for_violations(
    file_path: Path, allowed_tags: Set[str]
) -> List[Tuple[int, str, str]]:
    """Check a single file for PII and tag violations."""
    violations = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content_lines = f.readlines()

        for line_num, line in enumerate(content_lines, 1):
            # --- Check for PII Patterns ---
            # Improve performance by skipping checks inside Jinja tags first?
            # Simple approach: Check whole line, then maybe filter false positives
            # later.
            for pattern_name, pattern in PII_PATTERNS.items():
                for match in re.finditer(pattern, line):
                    # Check if match is inside a Jinja tag - basic check
                    # A more robust check would involve parsing, but regex might suffice
                    start, end = match.span()
                    pre_match = line[:start]
                    post_match = line[end:]
                    # Crude check: if opening {{ exists before match without closing }}
                    # or closing }} exists after match without opening {{ before it.
                    if re.search(r"\{\{[^{}]*$", pre_match) and re.search(
                        r"^[^}]*\}\}", post_match
                    ):
                        continue  # Likely inside a tag, skip

                    # Specific rule for unwrapped dollar - skip if inside {{ }}
                    # still needed?
                    # The regex attempts this but might need refinement.

                    violations.append((line_num, pattern_name, match.group(0)))

            # --- Check for Undefined Jinja Tags ---
            line_tag_pattern = re.compile(r"\{\{\s*([\w\.]+)\s*\}\}")
            for match in line_tag_pattern.finditer(line):
                tag = match.group(1).strip()
                if tag and tag not in allowed_tags:
                    violations.append((line_num, "UNDEFINED_TAG", tag))

    except UnicodeDecodeError:
        print(
            f"Warning: Skipping binary or non-UTF8 file: {file_path}",
            file=sys.stderr,
        )
    except Exception as e:
        violations.append((0, "FILE_READ_ERROR", str(e)))

    return violations


# --- Pytest Test Function ---


@pytest.mark.template_guard
def test_templates_are_clean():
    """Asserts that template files contain no PII or undefined tags."""
    template_files = _get_template_files()
    allowed_tags = _extract_tags_from_reference(REFERENCE_FILE)
    all_violations: Dict[Path, List[Tuple[int, str, str]]] = {}

    print(f"\nScanning {len(template_files)} template files...")
    print(f"Allowed tags found in {REFERENCE_FILE}: {len(allowed_tags)}")

    if not template_files:
        print("No template files found to check.")
        return  # Pass if no templates found

    for file_path in template_files:
        file_violations = _check_file_for_violations(file_path, allowed_tags)
        if file_violations:
            all_violations[file_path] = file_violations

    if all_violations:
        error_message = "\nTemplate Guard Violations Found:\n"
        for file_path, violations in all_violations.items():
            error_message += f"\n--- {file_path} ---\n"
            for line_num, v_type, v_text in violations:
                error_message += f"  Line {line_num}: [{v_type}] - '{v_text}'\n"
        pytest.fail(error_message, pytrace=False)
    else:
        print("Template scan complete. No violations detected.")


# --- Test for the Guard Itself (using a dummy bad file) ---

BAD_TEMPLATE_CONTENT = """
Hello John Doe,
Your phone is 555-123-4567 and DOB is 01/01/1990.
Your SSN is 123-45-6789.
Amount due: $100.50 (unwrapped!)
This tag is okay: {{ client.name }}
This tag is empty: {{ }}
This tag is undefined: {{ non.existent.tag }}
"""


@pytest.fixture
def create_bad_template(tmp_path) -> Path:
    """Creates a temporary bad template file for testing the guard."""
    assets_dir = tmp_path / "tests" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    bad_file = assets_dir / "bad_template.txt"
    bad_file.write_text(BAD_TEMPLATE_CONTENT, encoding="utf-8")
    return bad_file


@pytest.mark.template_guard  # Also mark this test
def test_guard_catches_violations(create_bad_template):
    """Test that the guard function correctly identifies violations."""
    bad_file_path = create_bad_template
    allowed_tags = {"client.name"}  # Only allow one tag for this test

    violations = _check_file_for_violations(bad_file_path, allowed_tags)

    assert violations, "Guard did not find any violations in the bad template!"

    violation_types = {v_type for _, v_type, _ in violations}
    expected_types = {
        "NAME",
        "PHONE_NUMBER",
        "DATE",
        "SSN",
        "UNWRAPPED_DOLLAR",
        "EMPTY_JINJA_TAG",
        "UNDEFINED_TAG",
    }

    assert violation_types == expected_types, (
        f"Guard found unexpected violation types: {violation_types}"
    )

    # Check specific line numbers if needed (more brittle)
    # Example: assert any(line == 1 and v_type == 'NAME'
    # for line, v_type, _ in violations)
