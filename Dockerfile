# Documentation Generator MCP Server
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Create directories with proper permissions
RUN mkdir -p /app/logs /app/data/output /app/data/templates && \
    chown -R 1000:1000 /app

# Run as non-root user
USER 1000:1000

# Simple startup
WORKDIR /app/src
CMD ["python", "main.py"]