#!/bin/bash
# Fix imports in Python files

echo "Running isort on Python files..."
isort --profile black tests/

echo "Adding fixed files to git..."
git add tests/

echo "Done! Fixed imports should now be staged for commit."
