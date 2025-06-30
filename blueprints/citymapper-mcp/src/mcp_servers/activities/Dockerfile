FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for DynamoDB integration
RUN pip install boto3 botocore

# Copy utility modules
COPY src/utils/ /app/src/utils/

# Copy the consolidated activities server
COPY src/mcp_servers/activities/ /app/src/mcp_servers/activities/

# Set working directory to activities server
WORKDIR /app/src/mcp_servers/activities

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Default command
CMD ["python", "consolidated_server.py"]
