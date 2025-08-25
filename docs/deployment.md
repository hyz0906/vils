# VILS Deployment Guide

This guide covers various deployment options for VILS, from local development to production Kubernetes clusters.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Compose Production](#docker-compose-production)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Configuration Management](#configuration-management)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Kubernetes** 1.24+ (for K8s deployment)
- **kubectl** (for K8s deployment)
- **Git** for version control

### Recommended Hardware
- **Development**: 4GB RAM, 2 CPU cores, 20GB storage
- **Production**: 8GB RAM, 4 CPU cores, 100GB storage
- **Database**: SSD storage for PostgreSQL

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/vils.git
cd vils

# Setup development environment
./scripts/local-dev.sh setup

# Start all services
./scripts/local-dev.sh start

# Run database migrations
./scripts/local-dev.sh migrate

# Access the application
open http://localhost:3000
```

### Manual Setup

If you prefer to set up services manually:

```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Frontend setup
cd ../frontend
npm install

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start databases
docker-compose up -d postgres redis

# Run migrations
cd ../backend
alembic upgrade head

# Start backend (in one terminal)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd ../frontend
npm run dev

# Start Celery worker (in another terminal)
cd backend
celery -A src.core.celery_app worker --loglevel=info
```

## Docker Compose Production

### Production Configuration

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - VITE_API_BASE_URL=/api
      - VITE_WS_URL=/ws

  backend:
    build: ./backend
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DATABASE_URL=postgresql://vils_user:${DB_PASSWORD}@postgres:5432/vils_db
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

  worker:
    build: ./backend
    command: celery -A src.core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://vils_user:${DB_PASSWORD}@postgres:5432/vils_db
    depends_on:
      - postgres
      - redis
    volumes:
      - /tmp/vils-builds:/tmp/builds

  beat:
    build: ./backend
    command: celery -A src.core.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://vils_user:${DB_PASSWORD}@postgres:5432/vils_db
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=vils_db
      - POSTGRES_USER=vils_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: postgres -c max_connections=100 -c shared_preload_libraries=pg_stat_statements

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables

Create a `.env` file:

```env
# Database
DB_PASSWORD=your_secure_password_here

# Backend
SECRET_KEY=your_secret_key_here
ENCRYPTION_MASTER_KEY=your_encryption_key_here

# External services (optional)
JENKINS_URL=
JENKINS_TOKEN=
GITHUB_TOKEN=
SENTRY_DSN=
```

### Deploy

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Kubernetes Deployment

### Prerequisites

Ensure you have:
- Kubernetes cluster (1.24+)
- kubectl configured
- Ingress controller (nginx recommended)
- Cert-manager for SSL (optional)
- Persistent storage class

### Deploy with Scripts

```bash
# Build and push images
./scripts/ci-cd.sh build
REGISTRY_URL=your-registry.com PUSH_IMAGES=true ./scripts/ci-cd.sh push

# Deploy to Kubernetes
KUBECTL_CONTEXT=your-cluster ./scripts/deploy.sh deploy

# Check deployment status
./scripts/deploy.sh status
```

### Manual Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (update with your values first)
kubectl apply -f k8s/configmap.yaml

# Deploy databases
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# Wait for databases
kubectl -n vils rollout status deployment/postgres
kubectl -n vils rollout status deployment/redis

# Deploy application
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

# Deploy networking
kubectl apply -f k8s/ingress.yaml

# Deploy autoscaling
kubectl apply -f k8s/hpa.yaml
```

### Update Secrets

Update the secrets in `k8s/configmap.yaml` with base64 encoded values:

```bash
# Encode secrets
echo -n "postgresql://user:password@postgres-service:5432/vils_db" | base64
echo -n "your-secret-key" | base64
echo -n "your-encryption-key" | base64

# Update k8s/configmap.yaml with encoded values
```

### Verify Deployment

```bash
# Check pods
kubectl -n vils get pods

# Check services
kubectl -n vils get services

# Check ingress
kubectl -n vils get ingress

# View logs
kubectl -n vils logs -f deployment/vils-backend
```

## Cloud Deployments

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster --name vils-cluster --region us-west-2 --nodes 3

# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Deploy VILS
./scripts/deploy.sh deploy
```

### Google GKE

```bash
# Create GKE cluster
gcloud container clusters create vils-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-standard-2

# Get credentials
gcloud container clusters get-credentials vils-cluster --zone=us-central1-a

# Deploy VILS
./scripts/deploy.sh deploy
```

### Azure AKS

```bash
# Create AKS cluster
az aks create \
  --resource-group vils-rg \
  --name vils-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group vils-rg --name vils-cluster

# Deploy VILS
./scripts/deploy.sh deploy
```

## Configuration Management

### Environment-Specific Configs

Create separate configuration files for each environment:

```bash
configs/
├── development.yaml
├── staging.yaml
└── production.yaml
```

Example `production.yaml`:

```yaml
app:
  environment: production
  debug: false
  log_level: INFO

database:
  pool_size: 20
  max_overflow: 40

redis:
  ttl: 3600

security:
  cors_origins:
    - https://vils.yourdomain.com
    - https://app.yourdomain.com

monitoring:
  sentry_dsn: ${SENTRY_DSN}
  log_level: INFO
```

### Secrets Management

For production, use proper secrets management:

#### Kubernetes Secrets

```bash
# Create secret from command line
kubectl -n vils create secret generic vils-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=SECRET_KEY="..." \
  --from-literal=ENCRYPTION_MASTER_KEY="..."
```

#### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: vils
spec:
  provider:
    vault:
      server: "https://vault.yourdomain.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "vils-role"
```

## SSL/TLS Setup

### Let's Encrypt with Cert-Manager

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Custom SSL Certificates

```bash
# Create TLS secret
kubectl -n vils create secret tls vils-tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

## Monitoring Setup

### Prometheus and Grafana

```bash
# Install Prometheus Operator
kubectl create ns monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Import VILS Grafana dashboard
kubectl -n monitoring create configmap vils-dashboard \
  --from-file=monitoring/grafana/vils-dashboard.json
```

### Application Metrics

VILS exposes metrics at `/api/monitoring/metrics`:

- HTTP request metrics
- Database connection metrics
- Task completion metrics
- WebSocket connection metrics
- System resource metrics

### Log Aggregation

#### ELK Stack

```bash
# Deploy Elasticsearch
kubectl apply -f monitoring/elasticsearch/

# Deploy Logstash
kubectl apply -f monitoring/logstash/

# Deploy Kibana
kubectl apply -f monitoring/kibana/

# Configure log shipping from VILS pods
kubectl apply -f monitoring/filebeat/
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
DB_NAME="vils_db"
DB_USER="vils_user"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
kubectl -n vils exec deployment/postgres -- pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/vils_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/vils_backup_$DATE.sql

# Upload to cloud storage (S3 example)
aws s3 cp $BACKUP_DIR/vils_backup_$DATE.sql.gz s3://your-backup-bucket/database/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "vils_backup_*.sql.gz" -mtime +30 -delete
```

### Volume Snapshots

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
  namespace: vils
spec:
  source:
    persistentVolumeClaimName: postgres-pvc
```

### Disaster Recovery

```bash
# Restore from backup
kubectl -n vils exec -it deployment/postgres -- psql -U vils_user -d vils_db < backup.sql

# Scale down application during restore
kubectl -n vils scale deployment vils-backend --replicas=0
kubectl -n vils scale deployment vils-frontend --replicas=0

# Scale back up after restore
kubectl -n vils scale deployment vils-backend --replicas=3
kubectl -n vils scale deployment vils-frontend --replicas=3
```

## Troubleshooting

### Common Issues

#### Pod Startup Issues

```bash
# Check pod events
kubectl -n vils describe pod <pod-name>

# Check pod logs
kubectl -n vils logs <pod-name>

# Check resource constraints
kubectl top pods -n vils
```

#### Database Connection Issues

```bash
# Test database connectivity
kubectl -n vils exec -it deployment/postgres -- psql -U vils_user -d vils_db -c "SELECT 1;"

# Check database logs
kubectl -n vils logs deployment/postgres

# Verify connection string
kubectl -n vils get secret vils-secrets -o yaml
```

#### Ingress/SSL Issues

```bash
# Check ingress status
kubectl -n vils describe ingress vils-ingress

# Check cert-manager certificates
kubectl -n vils get certificates

# Check ingress controller logs
kubectl -n ingress-nginx logs deployment/ingress-nginx-controller
```

#### Performance Issues

```bash
# Check resource usage
kubectl top pods -n vils
kubectl top nodes

# Check HPA status
kubectl -n vils get hpa

# View metrics
curl http://localhost:8000/api/monitoring/metrics
```

### Log Analysis

```bash
# View application logs
kubectl -n vils logs -f deployment/vils-backend --tail=100

# Filter logs by level
kubectl -n vils logs deployment/vils-backend | grep ERROR

# Export logs for analysis
kubectl -n vils logs deployment/vils-backend --since=1h > vils-logs.txt
```

### Performance Tuning

#### Database Optimization

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'localization_tasks';
```

#### Redis Optimization

```bash
# Check Redis memory usage
kubectl -n vils exec deployment/redis -- redis-cli info memory

# Check key distribution
kubectl -n vils exec deployment/redis -- redis-cli info keyspace

# Monitor commands
kubectl -n vils exec deployment/redis -- redis-cli monitor
```

### Health Checks

```bash
# Check all services health
curl -f http://localhost:8000/api/monitoring/health

# Check detailed health
curl http://localhost:8000/api/monitoring/health/detailed

# Check specific service
kubectl -n vils get pods -l app=vils-backend
```

For more detailed troubleshooting, refer to the [FAQ](faq.md) and [GitHub Issues](https://github.com/yourusername/vils/issues).