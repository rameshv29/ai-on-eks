#!/bin/bash

# Deploy Langfuse on EKS
set -e

echo "🚀 Deploying Langfuse on EKS..."

# Configuration
NAMESPACE="langfuse"
RELEASE_NAME="langfuse"

# Add Langfuse Helm repository
echo "📦 Adding Langfuse Helm repository..."
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update

# Create namespace
echo "🏗️ Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Generate secrets
echo "🔐 Generating secrets..."
NEXTAUTH_SECRET=$(openssl rand -base64 32)
SALT=$(openssl rand -base64 32)

# Create secret
kubectl create secret generic langfuse-secrets \
  --namespace=$NAMESPACE \
  --from-literal=nextauth-secret="$NEXTAUTH_SECRET" \
  --from-literal=salt="$SALT" \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy Langfuse
echo "🚀 Deploying Langfuse..."
helm upgrade --install $RELEASE_NAME langfuse/langfuse \
  --namespace $NAMESPACE \
  --values langfuse-values.yaml \
  --wait

# Wait for deployment
echo "⏳ Waiting for Langfuse to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/langfuse -n $NAMESPACE

# Get service info
echo "✅ Langfuse deployed successfully!"
echo ""
echo "📋 Service Information:"
kubectl get svc -n $NAMESPACE
echo ""
echo "🔗 Access Langfuse:"
echo "   kubectl port-forward -n $NAMESPACE svc/langfuse 3000:3000"
echo "   Then open: http://localhost:3000"
echo ""
echo "🔧 For citymapper integration, use:"
echo "   LANGFUSE_HOST=http://langfuse.$NAMESPACE.svc.cluster.local:3000"
echo ""
echo "🎉 Setup complete!"