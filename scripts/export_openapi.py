"""Exports the FastAPI application's OpenAPI specification to a YAML file.

Provides a command-line interface to generate the spec and optionally check
for differences against an existing spec file.
"""

import argparse
import difflib
from pathlib import Path

import yaml
from fastapi.openapi.utils import get_openapi

from pi_auto_api.main import app


def export_openapi_spec(output_path: Path) -> None:
    """Exports the OpenAPI spec to the given path."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    # FastAPI exports as JSON, but we want YAML for readability.
    # However, the spec requests YAML, but the example shows JSON output in a YAML file.
    # For now, let's stick to JSON as it's simpler to manage programmatically.
    # We can convert to YAML later if strictly needed.
    # The spec asks for YAML, but openapi-schema-validator works with JSON or YAML.
    # To ensure consistency with the provided openapi/pi-workflow.yaml (which is YAML),
    # we should ideally convert. For now, let's output JSON and address YAML conversion
    # if the validator or other tools require it.
    # For now, writing as JSON, will adjust if YAML is strictly required by tools.
    # The user initially created a YAML file. Let's try to output YAML.

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)
    print(f"OpenAPI spec exported to {output_path}")


def main():
    """Main function to parse arguments and export/check the OpenAPI spec."""
    parser = argparse.ArgumentParser(description="Export OpenAPI spec.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openapi/pi-workflow.yaml"),
        help="Output path for the OpenAPI spec file.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if the current spec matches the generated one.",
    )
    args = parser.parse_args()

    if args.check:
        current_spec_path = args.output
        if not current_spec_path.exists():
            print(f"Error: {current_spec_path} not found. Generate it first.")
            exit(1)

        with open(current_spec_path, "r") as f:
            current_spec_content = f.read()

        # Generate the spec in memory
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        generated_spec_content = yaml.dump(openapi_schema, sort_keys=False)

        if current_spec_content.strip() != generated_spec_content.strip():
            print("Error: OpenAPI spec drift detected. Differences:")
            diff = difflib.unified_diff(
                current_spec_content.strip().splitlines(keepends=True),
                generated_spec_content.strip().splitlines(keepends=True),
                fromfile=str(current_spec_path),
                tofile="generated",
            )
            for line in diff:
                print(line, end="")
            print("\nPlease run 'poetry run python scripts/export_openapi.py' to fix.")
            exit(1)
        else:
            print("OpenAPI spec is up to date.")
    else:
        export_openapi_spec(args.output)


if __name__ == "__main__":
    main()
