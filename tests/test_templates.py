"""Tests to verify that templates are properly set up and contain no PII."""

import subprocess
import sys
from pathlib import Path


def test_templates_exist():
    """Test that the templates directory exists and contains files."""
    template_dir = Path("templates")
    assert template_dir.exists(), "Templates directory doesn't exist"

    # Check that we have template files
    template_files = list(template_dir.glob("**/*"))
    assert len(template_files) > 0, "No template files found"


def test_no_pii_in_templates():
    """Test that no PII is found in the templates by running the check script."""
    script_path = Path("scripts/check_templates.py")
    assert script_path.exists(), "PII check script doesn't exist"

    # Make script executable if needed
    if not script_path.stat().st_mode & 0o100:
        script_path.chmod(script_path.stat().st_mode | 0o100)

    # Run the PII check script
    result = subprocess.run(
        [sys.executable, str(script_path)], capture_output=True, text=True
    )

    # If the script returns a non-zero exit code, it found PII
    error_msg = f"PII found in templates:\n{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, error_msg
