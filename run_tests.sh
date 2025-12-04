#!/bin/bash
# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Running tests using venv..."
    venv/bin/python3 -m unittest discover tests
else
    echo "Running tests using system python..."
    python3 -m unittest discover tests
fi
