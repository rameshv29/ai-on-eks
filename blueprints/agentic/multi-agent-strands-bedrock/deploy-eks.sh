#!/bin/bash

# Multi-Agent System EKS Deployment Script
# Deploys the complete multi-agent system to Amazon EKS

set -e

# Display banner
echo "=================================================="
echo "  Multi-Agent System EKS Deployment"
echo "=================================================="
echo "Deploying Orchestrator, Weather, and Citymapper agents"
echo "with Langfuse observability to Amazon EKS"
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

# Check for kubectl
if ! command -v kubectl &> /dev/null; then
  echo "Error: kubectl is not installed or not in PATH"
  echo "Please install kubectl and try again"
  exit 1
fi

# Check for helm
if ! command -v helm &> /dev/null; then
  echo "Error: helm is not installed or not in PATH"
  echo "Please install Helm and try again"
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

# Check if namespace exists, create if not
kubectl get namespace multi-agent-system >/dev/null 2>&1 || \
  kubectl create namespace multi-agent-system

# Create AWS credentials secret
echo "Creating AWS credentials secret..."
kubectl create secret generic aws-credentials \
  --namespace multi-agent-system \
  --from-literal=aws-access-key-id=${AWS_ACCESS_KEY_ID} \
  --from-literal=aws-secret-access-key=${AWS_SECRET_ACCESS_KEY} \
  --from-literal=aws-region=${AWS_REGION:-us-west-2} \
  --dry-run=client -o yaml | kubectl apply -f -

# Create Langfuse credentials secret
echo "Creating Langfuse credentials secret..."
kubectl create secret generic langfuse-credentials \
  --namespace multi-agent-system \
  --from-literal=langfuse-public-key=${LANGFUSE_PUBLIC_KEY:-pk-lf-local-test} \
  --from-literal=langfuse-secret-key=${LANGFUSE_SECRET_KEY:-sk-lf-local-test} \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy Langfuse
echo "Deploying Langfuse observability stack..."
helm repo add langfuse https://langfuse.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1

helm upgrade --install langfuse langfuse/langfuse \
  --namespace multi-agent-system \
  --set postgresql.auth.username=langfuse \
  --set postgresql.auth.password=langfuse \
  --set postgresql.auth.database=langfuse \
  --set nextAuthSecret=mysecret \
  --set salt=mysalt

# Wait for Langfuse to be ready
echo "Waiting for Langfuse to be ready..."
kubectl rollout status deployment/langfuse -n multi-agent-system --timeout=300s

# Deploy Multi-Agent System
echo "Deploying Multi-Agent System..."
helm upgrade --install multi-agent ./helm \
  --namespace multi-agent-system \
  --set bedrock.modelId=${BEDROCK_MODEL_ID:-us.anthropic.claude-3-7-sonnet-20250219-v1:0} \
  --set dynamodb.tableName=${DYNAMODB_AGENT_STATE_TABLE_NAME:-agent-state-table} \
  --set s3.bucketName=${S3_BUCKET_NAME:-travel-plans-bucket}

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/orchestrator -n multi-agent-system --timeout=300s
kubectl rollout status deployment/weather -n multi-agent-system --timeout=300s
kubectl rollout status deployment/citymapper -n multi-agent-system --timeout=300s

# Set up port forwarding for testing
echo "Setting up port forwarding for testing..."
kubectl port-forward -n multi-agent-system svc/orchestrator 3000:3000 &
PF1_PID=$!
kubectl port-forward -n multi-agent-system svc/weather 3001:3000 &
PF2_PID=$!
kubectl port-forward -n multi-agent-system svc/citymapper 3002:3000 &
PF3_PID=$!
kubectl port-forward -n multi-agent-system svc/langfuse 8000:3000 &
PF4_PID=$!

# Give port forwarding time to establish
sleep 5

# Display access information
echo ""
echo "=================================================="
echo "  Multi-Agent System Deployed to EKS"
echo "=================================================="
echo "Access your services at:"
echo "- Orchestrator FastAPI: http://localhost:3000"
echo "- Weather Agent FastAPI: http://localhost:3001"
echo "- Citymapper Agent FastAPI: http://localhost:3002"
echo "- Langfuse UI: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop port forwarding"
echo "=================================================="

# Wait for user to press Ctrl+C
trap "kill $PF1_PID $PF2_PID $PF3_PID $PF4_PID 2>/dev/null" EXIT
wait
