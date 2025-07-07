#!/bin/bash

# Simple test runner which sources the API key before running tests

set -e

# Check if riot-key.sh exists
if [ ! -f "riot-key.sh" ]; then
    echo "Error: riot-key.sh not found. Please copy riot-key.sh.example to riot-key.sh and add your API key."
    exit 1
fi

# Source the API key
echo "Sourcing Riot API key..."
source riot-key.sh

# Check if API key was set
if [ -z "$RIOT_API_KEY" ]; then
    echo "Error: RIOT_API_KEY not set. Please check your riot-key.sh file."
    exit 1
fi

echo "Running tests with uv (sequential execution to avoid database locks)..."
uv run pytest tests/ -v --maxfail=1 -x
