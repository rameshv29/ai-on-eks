# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_MAX_CONCURRENT_REQUESTS=100 \
    MCP_REQUEST_TIMEOUT_SECONDS=300

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for DynamoDB
RUN pip install boto3 botocore

# Copy the utils module (needed for DynamoDB integration)
COPY src/utils/ /app/src/utils/

# Copy the server code and data
COPY src/mcp_servers/food/ /app/src/mcp_servers/food/

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Command to run the server
CMD ["python", "src/mcp_servers/food/server.py"]
