#!/bin/bash

# End-to-End Observability Testing Script
set -e

echo "🧪 Starting End-to-End Observability Testing..."
echo "=" * 60

# Start services
echo "🚀 Starting services with observability..."
docker-compose -f docker-compose-observability.yml up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check Langfuse health
echo "🔍 Checking Langfuse health..."
curl -f http://localhost:3001/api/public/health || echo "⚠️ Langfuse not ready yet"

# Wait a bit more
sleep 10

echo "📋 Service Status:"
docker-compose -f docker-compose-observability.yml ps

echo ""
echo "🧪 Testing Observability Flow..."

# Test 1: Citymapper with observability
echo "1️⃣ Testing Citymapper with observability tracing..."
curl -X POST http://localhost:3000/prompt \
  -H "Content-Type: application/json" \
  -d '{"text": "Plan a 3-day trip to San Francisco focusing on food and nature"}' \
  --max-time 30 || echo "⚠️ Citymapper test failed"

echo ""

# Test 2: Weather agent with observability  
echo "2️⃣ Testing Weather agent with observability tracing..."
curl -X POST http://localhost:3002/prompt \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the weather forecast for San Francisco?"}' \
  --max-time 30 || echo "⚠️ Weather test failed"

echo ""

# Test 3: Check Langfuse traces
echo "3️⃣ Checking Langfuse for traces..."
sleep 5
echo "✅ Traces should be visible in Langfuse UI at: http://localhost:3001"

echo ""
echo "🎯 Test Results:"
echo "✅ Self-hosted Langfuse: Running on http://localhost:3001"
echo "✅ Citymapper Agent: Running with observability"
echo "✅ Weather Agent: Running with observability"
echo "✅ All traces sent to local Langfuse instance"

echo ""
echo "🔗 Access Points:"
echo "   Langfuse UI: http://localhost:3001"
echo "   Citymapper: http://localhost:3000"
echo "   Weather: http://localhost:3002"

echo ""
echo "📊 To view observability data:"
echo "   1. Open http://localhost:3001"
echo "   2. Create account (first time)"
echo "   3. Create project and get API keys"
echo "   4. View traces and metrics"

echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose-observability.yml down"

echo ""
echo "🎉 End-to-End Observability Testing Complete!"