#!/bin/bash
# Setup script for Documentation Generator permissions

echo "Setting up Documentation Generator directories and permissions..."

# Create directories if they don't exist
mkdir -p data/output
mkdir -p data/templates
mkdir -p data/generated
mkdir -p logs

# Set proper ownership (1000:1000 is the container user)
if command -v chown >/dev/null 2>&1; then
    echo "Setting ownership to 1000:1000..."
    chown -R 1000:1000 data/ logs/ 2>/dev/null || {
        echo "Warning: Could not set ownership. You may need to run with sudo:"
        echo "  sudo chown -R 1000:1000 data/ logs/"
    }
fi

# Set proper permissions
chmod -R 755 data/
chmod -R 755 logs/

echo "Directory setup complete!"
echo ""
echo "Directories created:"
echo "  - data/output     (generated documents)"
echo "  - data/templates  (custom templates)"
echo "  - data/generated  (document metadata)"
echo "  - logs/           (application logs)"
echo ""
echo "You can now run: docker-compose up"