#!/bin/bash

# Setup Local Observability Testing
set -e

echo "🔧 Setting up Local Observability Testing..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Start Langfuse first
echo "🚀 Starting Langfuse..."
docker-compose -f docker-compose-observability.yml up -d langfuse-db langfuse

# Wait for Langfuse to be ready
echo "⏳ Waiting for Langfuse to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:3001/api/public/health &>/dev/null; then
        echo "✅ Langfuse is ready!"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo "   Waiting... ($counter/$timeout seconds)"
done

if [ $counter -ge $timeout ]; then
    echo "❌ Langfuse failed to start within $timeout seconds"
    exit 1
fi

# Setup Langfuse project
echo "🔧 Setting up Langfuse project..."
echo ""
echo "📋 Next Steps:"
echo "1. Open Langfuse UI: http://localhost:3001"
echo "2. Create an account (first time setup)"
echo "3. Create a new project"
echo "4. Go to Settings → API Keys"
echo "5. Create new API keys and note them down"
echo ""
echo "🔑 Update environment variables with your API keys:"
echo "   export LANGFUSE_PUBLIC_KEY='pk-lf-your-key'"
echo "   export LANGFUSE_SECRET_KEY='sk-lf-your-secret'"
echo ""
echo "🧪 Then run the full test:"
echo "   ./test-observability-e2e.sh"
echo ""
echo "✅ Langfuse setup complete!"

# Keep Langfuse running
echo "🔄 Langfuse is running in the background..."
echo "   To stop: docker-compose -f docker-compose-observability.yml down"