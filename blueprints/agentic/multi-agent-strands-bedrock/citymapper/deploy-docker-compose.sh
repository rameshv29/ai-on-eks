#!/bin/bash

# Deploy Citymapper with Docker Compose
set -e

echo "🚀 Deploying Citymapper with Docker Compose..."

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️ AWS credentials not set. Please configure:"
    echo "   export AWS_ACCESS_KEY_ID=your-key"
    echo "   export AWS_SECRET_ACCESS_KEY=your-secret"
    echo "   export AWS_REGION=us-west-2"
fi

# Start services
echo "🐳 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Service Endpoints:"
echo "   Citymapper MCP:    http://localhost:8080"
echo "   Citymapper A2A:    http://localhost:9000"
echo "   Citymapper FastAPI: http://localhost:3000"
echo "   Langfuse UI:       http://localhost:3001"
echo ""
echo "🧪 Test Commands:"
echo "   curl http://localhost:3000/health"
echo "   curl http://localhost:3001/api/public/health"
echo ""
echo "📊 Setup Observability:"
echo "   1. Open http://localhost:3001"
echo "   2. Create account and project"
echo "   3. Get API keys from Settings"
echo "   4. Update environment variables:"
echo "      export LANGFUSE_PUBLIC_KEY='pk-lf-your-key'"
echo "      export LANGFUSE_SECRET_KEY='sk-lf-your-secret'"
echo "   5. Restart: docker-compose restart citymapper"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "🎉 Citymapper deployment ready!"