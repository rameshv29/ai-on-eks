# Multi-Agent System Production Deployment Guide

This guide provides detailed instructions for deploying the multi-agent system (Orchestrator, Weather, and Citymapper agents) in production environments using Amazon EKS.

## Prerequisites

- Amazon EKS cluster running Kubernetes 1.24+
- kubectl configured to access your cluster
- Helm 3.x installed
- AWS CLI configured with appropriate permissions
- Container registry access (ECR or other)

## Infrastructure Setup

### 1. Create Required AWS Resources

```bash
# Create DynamoDB table for agent state
aws dynamodb create-table \
  --table-name agent-state-table \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Create S3 bucket for travel plans (optional)
aws s3 mb s3://travel-plans-bucket --region us-west-2
```

### 2. Create Kubernetes Namespace

```bash
kubectl create namespace multi-agent-system
```

### 3. Create Secrets

```bash
# Create AWS credentials secret
kubectl create secret generic aws-credentials \
  --namespace multi-agent-system \
  --from-literal=aws-access-key-id=$AWS_ACCESS_KEY_ID \
  --from-literal=aws-secret-access-key=$AWS_SECRET_ACCESS_KEY \
  --from-literal=aws-region=$AWS_REGION

# Create Langfuse credentials secret
kubectl create secret generic langfuse-credentials \
  --namespace multi-agent-system \
  --from-literal=langfuse-public-key=$LANGFUSE_PUBLIC_KEY \
  --from-literal=langfuse-secret-key=$LANGFUSE_SECRET_KEY
```

## Deployment Options

### Option 1: Helm Deployment (Recommended)

#### 1. Deploy Langfuse Observability

```bash
# Add Langfuse Helm repository
helm repo add langfuse https://langfuse.github.io/helm-charts
helm repo update

# Deploy Langfuse
helm install langfuse langfuse/langfuse \
  --namespace multi-agent-system \
  --set postgresql.auth.username=langfuse \
  --set postgresql.auth.password=langfuse \
  --set postgresql.auth.database=langfuse \
  --set nextAuthSecret=mysecret \
  --set salt=mysalt
```

#### 2. Deploy Multi-Agent System

```bash
# From the repository root
cd blueprints/agentic/multi-agent-strands-bedrock

# Deploy using Helm
helm install multi-agent ./helm \
  --namespace multi-agent-system \
  --set image.repository=your-registry/multi-agent \
  --set image.tag=latest \
  --set bedrock.modelId=us.anthropic.claude-3-7-sonnet-20250219-v1:0 \
  --set dynamodb.tableName=agent-state-table \
  --set s3.bucketName=travel-plans-bucket
```

### Option 2: Kubernetes Manifests

If you prefer to use raw Kubernetes manifests:

```bash
# From the repository root
cd blueprints/agentic/multi-agent-strands-bedrock

# Apply manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/langfuse.yaml
kubectl apply -f kubernetes/orchestrator.yaml
kubectl apply -f kubernetes/weather.yaml
kubectl apply -f kubernetes/citymapper.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
```

## Accessing the Deployed Services

### 1. Port Forwarding (Development/Testing)

```bash
# Orchestrator
kubectl port-forward -n multi-agent-system svc/orchestrator 3000:3000

# Weather Agent
kubectl port-forward -n multi-agent-system svc/weather 3001:3000

# Citymapper Agent
kubectl port-forward -n multi-agent-system svc/citymapper 3002:3000

# Langfuse
kubectl port-forward -n multi-agent-system svc/langfuse 8000:3000
```

### 2. Ingress (Production)

If you've configured an ingress controller:

```
Orchestrator: https://orchestrator.your-domain.com
Weather: https://weather.your-domain.com
Citymapper: https://citymapper.your-domain.com
Langfuse: https://langfuse.your-domain.com
```

## Scaling and High Availability

### Horizontal Pod Autoscaling

```bash
kubectl apply -f kubernetes/hpa.yaml
```

This configures autoscaling based on CPU and memory usage.

### Resource Requests and Limits

The default deployment includes resource requests and limits:

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

Adjust these values based on your workload requirements.

## Monitoring and Observability

### Langfuse

Access the Langfuse UI to monitor:
- Agent interactions and traces
- Token usage and costs
- Response quality metrics
- User feedback

### Prometheus and Grafana (Optional)

If you have Prometheus and Grafana installed in your cluster:

1. Apply the ServiceMonitor configuration:
   ```bash
   kubectl apply -f kubernetes/servicemonitor.yaml
   ```

2. Import the provided Grafana dashboard:
   - Navigate to Grafana
   - Import dashboard from `monitoring/grafana-dashboard.json`

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n multi-agent-system
```

### View Logs

```bash
# Orchestrator logs
kubectl logs -f deployment/orchestrator -n multi-agent-system

# Weather agent logs
kubectl logs -f deployment/weather -n multi-agent-system

# Citymapper agent logs
kubectl logs -f deployment/citymapper -n multi-agent-system

# Langfuse logs
kubectl logs -f deployment/langfuse -n multi-agent-system
```

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are correctly configured and have permissions for Bedrock, DynamoDB, and S3.

2. **Resource Constraints**: If pods are in Pending state, check if there are sufficient resources in your cluster.

3. **Network Connectivity**: Ensure agents can communicate with each other and with AWS services.

## Backup and Disaster Recovery

### DynamoDB Backup

```bash
aws dynamodb create-backup \
  --table-name agent-state-table \
  --backup-name agent-state-backup-$(date +%Y%m%d)
```

### Langfuse Database Backup

If using the Helm chart with default PostgreSQL:

```bash
kubectl exec -n multi-agent-system \
  $(kubectl get pods -n multi-agent-system -l app.kubernetes.io/name=postgresql -o jsonpath="{.items[0].metadata.name}") \
  -- pg_dump -U langfuse langfuse > langfuse-backup-$(date +%Y%m%d).sql
```

## Security Considerations

1. **Network Policies**: Apply network policies to restrict communication between pods.

2. **Pod Security Policies**: Enforce pod security standards.

3. **Secrets Management**: Consider using AWS Secrets Manager or HashiCorp Vault for production secrets.

4. **TLS**: Enable TLS for all ingress endpoints.

## Upgrading

To upgrade the deployment:

```bash
# Update Helm release
helm upgrade multi-agent ./helm \
  --namespace multi-agent-system \
  --set image.tag=new-version

# Or update with kubectl
kubectl set image deployment/orchestrator orchestrator=your-registry/orchestrator:new-version -n multi-agent-system
kubectl set image deployment/weather weather=your-registry/weather:new-version -n multi-agent-system
kubectl set image deployment/citymapper citymapper=your-registry/citymapper:new-version -n multi-agent-system
```

## Uninstalling

```bash
# Using Helm
helm uninstall multi-agent -n multi-agent-system
helm uninstall langfuse -n multi-agent-system

# Or using kubectl
kubectl delete -f kubernetes/
```
