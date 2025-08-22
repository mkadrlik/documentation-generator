#!/bin/bash
# Entrypoint script for Documentation Generator

set -e

echo "=== Documentation Generator MCP Server ==="
echo "User: $(id)"
echo "Working directory: $(pwd)"

# Create directories if they don't exist (with fallback handling)
echo "Setting up directories..."

# Try to create directories, but don't fail if we can't
mkdir -p /app/data/output /app/data/templates /app/data/generated /app/logs 2>/dev/null || {
    echo "Warning: Could not create some directories in /app. Will use fallback locations."
}

# Test write permissions and set environment variables for fallbacks
echo "Testing directory permissions..."

if ! touch /app/data/output/.test 2>/dev/null; then
    echo "⚠️  No write access to /app/data/output"
    mkdir -p /tmp/documentation-output
    export FALLBACK_OUTPUT_DIR=/tmp/documentation-output
    echo "✅ Created fallback: /tmp/documentation-output"
else
    echo "✅ /app/data/output is writable"
    rm -f /app/data/output/.test
fi

if ! touch /app/data/templates/.test 2>/dev/null; then
    echo "⚠️  No write access to /app/data/templates"
    mkdir -p /tmp/documentation-templates
    export FALLBACK_TEMPLATES_DIR=/tmp/documentation-templates
    echo "✅ Created fallback: /tmp/documentation-templates"
else
    echo "✅ /app/data/templates is writable"
    rm -f /app/data/templates/.test
fi

if ! touch /app/logs/.test 2>/dev/null; then
    echo "⚠️  No write access to /app/logs (will log to console only)"
else
    echo "✅ /app/logs is writable"
    rm -f /app/logs/.test
fi

echo "Directory setup complete!"
echo ""

# Start the main application
echo "Starting Documentation Generator..."
cd /app/src
exec python main.py "$@"