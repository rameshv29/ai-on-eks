# Langfuse Self-Hosted Deployment on EKS

Deploy open-source Langfuse observability platform alongside the citymapper multi-agent system.

## Quick Setup

### 1. Add Langfuse Helm Repository
```bash
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update
```

### 2. Deploy Langfuse
```bash
# Create namespace
kubectl create namespace langfuse

# Deploy with PostgreSQL
helm install langfuse langfuse/langfuse \
  --namespace langfuse \
  --set postgresql.enabled=true \
  --set postgresql.auth.postgresPassword=your-secure-password \
  --set nextauth.secret=$(openssl rand -base64 32) \
  --set salt=$(openssl rand -base64 32)
```

### 3. Access Langfuse
```bash
# Port forward to access UI
kubectl port-forward -n langfuse svc/langfuse 3000:3000

# Access at http://localhost:3000
```

### 4. Configure Citymapper Agents
```bash
# Get Langfuse service URL
export LANGFUSE_HOST="http://langfuse.langfuse.svc.cluster.local:3000"

# Create API keys in Langfuse UI, then set:
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
```

## Production Configuration

### Values for Production
```yaml
# langfuse-values.yaml
ingress:
  enabled: true
  hosts:
    - host: langfuse.your-domain.com
      paths:
        - path: /
          pathType: Prefix

postgresql:
  enabled: true
  auth:
    postgresPassword: "your-secure-password"
  primary:
    persistence:
      enabled: true
      size: 20Gi

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Deploy with Custom Values
```bash
helm install langfuse langfuse/langfuse \
  --namespace langfuse \
  --values langfuse-values.yaml
```

## Integration with Citymapper

### Update Citymapper Helm Values
```yaml
# citymapper/helm/values.yaml
agent:
  env:
  - name: LANGFUSE_PUBLIC_KEY
    value: "pk-lf-your-key"
  - name: LANGFUSE_SECRET_KEY
    value: "sk-lf-your-secret"  
  - name: LANGFUSE_HOST
    value: "http://langfuse.langfuse.svc.cluster.local:3000"
```

### Deploy Citymapper with Observability
```bash
helm upgrade citymapper-agent citymapper/helm \
  --namespace citymapper \
  --values citymapper-observability-values.yaml
```

## Benefits of Self-Hosted Langfuse

✅ **Data Privacy**: All observability data stays in your cluster  
✅ **Cost Control**: No external SaaS fees  
✅ **Customization**: Full control over configuration  
✅ **Integration**: Direct cluster-to-cluster communication  
✅ **Compliance**: Meet data residency requirements  

## Monitoring Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │───▶│   Citymapper    │───▶│    Langfuse     │
│   (Port 9000)   │    │ (Ports 8080/9000│    │   (Port 3000)   │
│                 │    │      /3000)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │     PostgreSQL DB       │
                    │   (Traces & Metrics)    │
                    └─────────────────────────┘
```

This gives you a complete self-hosted observability stack running entirely within your EKS cluster!