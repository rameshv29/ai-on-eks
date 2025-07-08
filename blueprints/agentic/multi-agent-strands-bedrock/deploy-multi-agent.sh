#!/bin/bash

# Multi-Agent System Deployment Script
# Deploys the complete multi-agent system with observability

set -e

# Display banner
echo "=================================================="
echo "  Multi-Agent System Deployment"
echo "=================================================="
echo "Deploying Orchestrator, Weather, and Citymapper agents"
echo "with Langfuse observability"
echo ""

# Check for .env file
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
else
  echo "No .env file found. Using default configuration."
  echo "Consider creating a .env file for custom settings."
  echo ""
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed or not in PATH"
  echo "Please install Docker and try again"
  exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
  echo "Error: Docker Compose is not installed or not in PATH"
  echo "Please install Docker Compose and try again"
  exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Warning: AWS credentials not found in environment variables"
  echo "Checking for credentials in ~/.aws..."
  
  if [ ! -f ~/.aws/credentials ]; then
    echo "Warning: AWS credentials not found in ~/.aws/credentials"
    echo "You may need to configure AWS credentials for Bedrock access"
  else
    echo "Found AWS credentials file"
  fi
fi

# Create Docker network if it doesn't exist
docker network inspect multi-agent-network >/dev/null 2>&1 || \
  docker network create multi-agent-network

# Build and start services
echo "Building and starting all services..."
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."
ORCHESTRATOR_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${ORCHESTRATOR_PORT:-3000}/health || echo "error")
WEATHER_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${WEATHER_FASTAPI_PORT:-3001}/health || echo "error")
CITYMAPPER_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${CITYMAPPER_FASTAPI_PORT:-3002}/health || echo "error")
LANGFUSE_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/public/health || echo "error")

echo "Service health status:"
echo "- Orchestrator: ${ORCHESTRATOR_HEALTH}"
echo "- Weather Agent: ${WEATHER_HEALTH}"
echo "- Citymapper Agent: ${CITYMAPPER_HEALTH}"
echo "- Langfuse: ${LANGFUSE_HEALTH}"

# Display access information
echo ""
echo "=================================================="
echo "  Multi-Agent System Deployed"
echo "=================================================="
echo "Access your services at:"
echo "- Orchestrator FastAPI: http://localhost:${ORCHESTRATOR_PORT:-3000}"
echo "- Weather Agent FastAPI: http://localhost:${WEATHER_FASTAPI_PORT:-3001}"
echo "- Citymapper Agent FastAPI: http://localhost:${CITYMAPPER_FASTAPI_PORT:-3002}"
echo "- Langfuse UI: http://localhost:8000"
echo ""
echo "Try these example queries with the orchestrator:"
echo "1. \"What's the weather like in San Francisco today?\""
echo "2. \"Plan a 3-day trip to New York City with focus on museums and parks\""
echo "3. \"I'm planning a trip to San Francisco next week. What's the weather forecast and what activities would you recommend?\""
echo ""
echo "To stop all services:"
echo "docker-compose down"
echo ""
echo "For more information, see README.md"
echo "=================================================="
