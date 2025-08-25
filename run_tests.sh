#!/bin/bash

PYTEST_PATH="./.venv/bin/pytest"
TEST_DIR="tests"

echo "Running all test files individually..."

find "$TEST_DIR" -type f -name 'test_*.py' | while read file; do
    echo "--- Running tests in $file ---"
    "$PYTEST_PATH" "$file"
    
    if [ $? -ne 0 ]; then
        echo "Tests in $file failed. Aborting."
        exit 1
    fi
    echo "--- Finished $file ---"
done

echo "All test files passed successfully! 🎉"