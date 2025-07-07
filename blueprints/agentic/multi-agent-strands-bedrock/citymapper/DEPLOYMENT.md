# Citymapper Agent Deployment Guide

Complete deployment guide for Citymapper Travel Agent with observability on EKS and local environments.

## 🚀 EKS Deployment

### Prerequisites
- EKS cluster running
- kubectl configured
- Helm 3.x installed
- AWS credentials configured

### 1. Deploy Langfuse Observability Stack
```bash
# Deploy self-hosted Langfuse
cd ../langfuse
./deploy-langfuse.sh

# Verify deployment
kubectl get pods -n langfuse
kubectl port-forward -n langfuse svc/langfuse 3000:3000
```

### 2. Deploy Citymapper Agent
```bash
# Build and push image (update values.yaml with your registry)
docker build -t your-registry/citymapper:latest .
docker push your-registry/citymapper:latest

# Deploy via Helm
helm install citymapper-agent ./helm \
  --namespace citymapper \
  --create-namespace \
  --set image.repository=your-registry/citymapper \
  --set image.tag=latest

# Verify deployment
kubectl get pods -n citymapper
kubectl get svc -n citymapper
```

### 3. Configure Observability
```bash
# Get Langfuse API keys from UI (http://localhost:3000)
# Create observability secret
kubectl create secret generic citymapper-observability \
  --namespace citymapper \
  --from-literal=langfuse-public-key="pk-lf-your-key" \
  --from-literal=langfuse-secret-key="sk-lf-your-secret"

# Update deployment
helm upgrade citymapper-agent ./helm \
  --namespace citymapper \
  --set observability.enabled=true
```

### 4. Access Services
```bash
# Port forward Citymapper services
kubectl port-forward -n citymapper svc/citymapper-agent 8080:8080  # MCP
kubectl port-forward -n citymapper svc/citymapper-agent 9000:9000  # A2A
kubectl port-forward -n citymapper svc/citymapper-agent 3000:3000  # FastAPI

# Test endpoints
curl http://localhost:3000/health
curl -X POST http://localhost:3000/prompt -H "Content-Type: application/json" \
  -d '{"text": "Plan a 3-day trip to San Francisco"}'
```

## 🐳 Docker Compose Deployment

### 1. Create Docker Compose File
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Langfuse observability stack
  langfuse-db:
    image: postgres:15
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    volumes:
      - langfuse_db:/var/lib/postgresql/data
    networks:
      - citymapper-network

  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_URL: http://localhost:3001
      NEXTAUTH_SECRET: mysecret
      SALT: mysalt
      TELEMETRY_ENABLED: false
    depends_on:
      - langfuse-db
    networks:
      - citymapper-network

  # Citymapper agent
  citymapper:
    build: .
    ports:
      - "8080:8080"  # MCP
      - "9000:9000"  # A2A  
      - "3000:3000"  # FastAPI
    environment:
      - AWS_REGION=${AWS_REGION:-us-west-2}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-us.anthropic.claude-3-7-sonnet-20250219-v1:0}
      - LANGFUSE_PUBLIC_KEY=pk-lf-local-test
      - LANGFUSE_SECRET_KEY=sk-lf-local-test
      - LANGFUSE_HOST=http://langfuse:3000
    volumes:
      - ~/.aws:/app/.aws:ro
    networks:
      - citymapper-network
    depends_on:
      - langfuse

volumes:
  langfuse_db:

networks:
  citymapper-network:
    driver: bridge
```

### 2. Deploy with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs citymapper
docker-compose logs langfuse

# Test endpoints
curl http://localhost:3000/health
curl http://localhost:3001/api/public/health  # Langfuse
```

### 3. Setup Observability
```bash
# Access Langfuse UI
open http://localhost:3001

# Create project and get API keys
# Update docker-compose.yml with real API keys
# Restart services
docker-compose restart citymapper
```

## 🧪 Testing Deployment

### End-to-End Test
```bash
# Test travel planning with observability
python test_complete_observability.py

# Test MCP tools
python test_e2e_mcp.py

# Test A2A communication
python test_e2e_a2a.py

# Test FastAPI endpoints
./test_e2e_fastapi_curl.sh
```

### Verify Observability
```bash
# Check Langfuse traces
open http://localhost:3001  # (Docker Compose)
# or
kubectl port-forward -n langfuse svc/langfuse 3001:3000  # (EKS)
open http://localhost:3001
```

## 📊 Monitoring & Troubleshooting

### EKS Troubleshooting
```bash
# Check pod status
kubectl get pods -n citymapper -o wide
kubectl describe pod <pod-name> -n citymapper

# Check logs
kubectl logs -f deployment/citymapper-agent -n citymapper

# Check services
kubectl get svc -n citymapper
kubectl describe svc citymapper-agent -n citymapper

# Check observability
kubectl get pods -n langfuse
kubectl logs -f deployment/langfuse -n langfuse
```

### Docker Compose Troubleshooting
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f citymapper
docker-compose logs -f langfuse

# Restart services
docker-compose restart citymapper

# Clean restart
docker-compose down
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for Bedrock
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# Required for Observability
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret
LANGFUSE_HOST=http://langfuse:3000  # Docker Compose
# or
LANGFUSE_HOST=http://langfuse.langfuse.svc.cluster.local:3000  # EKS
```

### Helm Values Customization
```yaml
# helm/values.yaml
image:
  repository: your-registry/citymapper
  tag: latest

observability:
  enabled: true
  langfuse:
    host: "http://langfuse.langfuse.svc.cluster.local:3000"

resources:
  requests:
    memory: 512Mi
    cpu: 250m
  limits:
    memory: 1Gi
    cpu: 500m
```

## 🎯 Production Considerations

### Security
- Use proper secrets management (AWS Secrets Manager, Kubernetes secrets)
- Configure RBAC for service accounts
- Use private container registries
- Enable network policies

### Scaling
- Configure HPA for auto-scaling
- Use node selectors for GPU nodes if needed
- Set appropriate resource requests/limits

### Monitoring
- Enable Prometheus metrics
- Configure alerting rules
- Set up log aggregation
- Monitor Langfuse performance

### Backup
- Backup Langfuse PostgreSQL database
- Version control Helm configurations
- Document deployment procedures