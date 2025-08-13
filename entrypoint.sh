#!/bin/bash
# Entrypoint script for Documentation Generator

set -e

echo "Starting Documentation Generator MCP Server..."

# Create directories if they don't exist (with fallback handling)
echo "Setting up directories..."

# Try to create directories, but don't fail if we can't
mkdir -p /app/data/output /app/data/templates /app/data/generated /app/logs 2>/dev/null || {
    echo "Warning: Could not create some directories in /app. Using fallback locations."
}

# Test write permissions and create fallback directories if needed
if ! touch /app/data/output/.test 2>/dev/null; then
    echo "Warning: No write access to /app/data/output, using /tmp/documentation-output"
    mkdir -p /tmp/documentation-output
    export FALLBACK_OUTPUT_DIR=/tmp/documentation-output
else
    rm -f /app/data/output/.test
fi

if ! touch /app/logs/.test 2>/dev/null; then
    echo "Warning: No write access to /app/logs, logging to console only"
else
    rm -f /app/logs/.test
fi

echo "Directory setup complete. Starting server..."

# Start the main application
cd /app/src
exec python main.py "$@"