# Documentation Generator MCP Server
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and scripts
COPY src/ ./src/
COPY entrypoint.sh ./entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV BUILD_VERSION=2025-08-13-v2

# Create directories with proper permissions and make entrypoint executable
RUN mkdir -p /app/logs /app/data/output /app/data/templates /app/data/generated && \
    chmod +x /app/entrypoint.sh && \
    chmod -R 755 /app && \
    chown -R 1000:1000 /app

# Run as non-root user
USER 1000:1000

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]