# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|deployment|

---

# DSI Deployment Guide

Complete guide for deploying the Digital Signal Intelligence platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Configuration](#configuration)
4. [Local Development](#local-development)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Database Setup](#database-setup)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)
11. [Runbook](#runbook)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|-|-|-|
| Python | 3.10+ | Runtime |
| PostgreSQL | 14+ | Primary database |
| Redis | 7+ | Caching & sessions |
| Docker | 24+ | Containerization |
| kubectl | 1.28+ | Kubernetes management |
| Helm | 3.12+ | K8s package management |

### Required Accounts/Services

| Service | Purpose | Required For |
|-|-|-|
| AWS/GCP/Azure | Cloud infrastructure | Production |
| Container Registry | Image storage | Production |
| SSL Labs API | TLS scanning | Real extractors |
| SecurityScorecard | Security ratings | Real extractors |

---

## Architecture Overview

```
                                    ┌─────────────────┐
                                    │   Load Balancer │
                                    │   (nginx/ALB)   │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
            ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
            │   DSI API     │       │   DSI API     │       │   DSI API     │
            │   Pod 1       │       │   Pod 2       │       │   Pod 3       │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
            ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
            │  PostgreSQL   │       │    Redis      │       │  S3/Blob      │
            │  (Primary)    │       │   Cluster     │       │  Storage      │
            └───────────────┘       └───────────────┘       └───────────────┘
```

### Component Responsibilities

| Component | Replicas | Purpose |
|-|-|-|
| DSI API | 3+ | Request handling, workflow execution |
| PostgreSQL | 1 primary + 1 replica | Submissions, quotes, audit logs |
| Redis | 3 (cluster) | Signal caching, session storage |
| S3/Blob | N/A | Config storage, document uploads |

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

#### Critical Settings

```bash
# MUST change in production
DSI_ENV=production
DSI_DEBUG=false
JWT_SECRET_KEY=<generate-256-bit-key>

# Database (use managed service in production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dsi_prod

# Redis (use managed service in production)
REDIS_URL=redis://:password@host:6379/0

# CORS (restrict to your domains)
CORS_ORIGINS=https://app.yourcompany.com,https://admin.yourcompany.com
```

#### Generate Secure Keys

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_hex(32))"

# Generate API key
python -c "import secrets; print(f'dsi_{secrets.token_hex(24)}')"
```

### Configuration Hierarchy

```
Environment Variables (highest priority)
    ↓
.env file
    ↓
Default values in code (lowest priority)
```

---

## Local Development

### Quick Start

```bash
# Clone and setup
git clone https://github.com/jwalker618/digital-signal-intelligence.git
cd digital-signal-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure
cp .env.example .env
# Edit .env as needed

# Run API
uvicorn technical_pricing.api.main:app --reload --port 8000
```

### With Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Run Tests

```bash
# All tests
pytest technical_pricing/tests/ -v

# With coverage
pytest technical_pricing/tests/ --cov=technical_pricing --cov-report=html

# Specific test file
pytest technical_pricing/tests/unit/test_workflow.py -v
```

---

## Docker Deployment

### Build Image

```bash
# Build production image
docker build -t dsi-api:latest .

# Build with specific tag
docker build -t dsi-api:v0.2.0 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t dsi-api:latest .
```

### Run Container

```bash
# Run with environment file
docker run -d \
  --name dsi-api \
  --env-file .env \
  -p 8000:8000 \
  dsi-api:latest

# Run with explicit environment
docker run -d \
  --name dsi-api \
  -e DSI_ENV=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -p 8000:8000 \
  dsi-api:latest
```

### Docker Compose Production

See `deploy/docker/docker-compose.prod.yml`:

```bash
cd deploy/docker
docker-compose -f docker-compose.prod.yml up -d
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Verify kubectl access
kubectl cluster-info

# Create namespace
kubectl create namespace dsi-prod
kubectl config set-context --current --namespace=dsi-prod
```

### Deploy with Helm

```bash
cd deploy/kubernetes

# Install/upgrade
helm upgrade --install dsi-api ./helm/dsi-api \
  --namespace dsi-prod \
  --values ./helm/dsi-api/values-prod.yaml \
  --set image.tag=v0.2.0

# Check status
helm status dsi-api -n dsi-prod
kubectl get pods -n dsi-prod
```

### Manual Deployment

```bash
cd deploy/kubernetes

# Create secrets first
kubectl apply -f secrets.yaml

# Deploy components
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Verify
kubectl get all -n dsi-prod
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment dsi-api --replicas=5 -n dsi-prod

# HPA is configured for automatic scaling (see hpa.yaml)
kubectl get hpa -n dsi-prod
```

---

## Database Setup

### PostgreSQL Installation

#### AWS RDS

```bash
aws rds create-db-instance \
  --db-instance-identifier dsi-prod \
  --db-instance-class db.r6g.large \
  --engine postgres \
  --engine-version 15.4 \
  --master-username dsi_admin \
  --master-user-password <secure-password> \
  --allocated-storage 100 \
  --storage-type gp3 \
  --multi-az \
  --vpc-security-group-ids sg-xxx \
  --db-subnet-group-name dsi-subnet-group
```

#### Docker (Development)

```bash
docker run -d \
  --name dsi-postgres \
  -e POSTGRES_USER=dsi_user \
  -e POSTGRES_PASSWORD=dsi_password \
  -e POSTGRES_DB=dsi_db \
  -p 5432:5432 \
  -v dsi-pgdata:/var/lib/postgresql/data \
  postgres:15
```

### Run Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Database Maintenance

```bash
# Backup
pg_dump -h localhost -U dsi_user -d dsi_db > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U dsi_user -d dsi_db < backup_20241229.sql

# Vacuum and analyze
psql -h localhost -U dsi_user -d dsi_db -c "VACUUM ANALYZE;"
```

---

## Monitoring & Observability

### Health Checks

| Endpoint | Purpose | Expected Response |
|-|-|-|
| `/api/v1/health` | Full health check | `{"status": "healthy"}` |
| `/api/v1/health/live` | Liveness probe | `{"alive": true}` |
| `/api/v1/health/ready` | Readiness probe | `{"ready": true}` |
| `/api/v1/metrics` | Prometheus metrics | JSON metrics |

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'dsi-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ['dsi-prod']
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: dsi-api
        action: keep
    metrics_path: /api/v1/metrics
    scrape_interval: 15s
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|-|-|-|
| `request_count` | Total API requests | N/A (info) |
| `request_latency_p99` | 99th percentile latency | > 2s |
| `error_rate` | 5xx error rate | > 1% |
| `db_connection_pool` | Active DB connections | > 80% |
| `workflow_duration` | Pricing workflow time | > 30s |
| `cache_hit_rate` | Redis cache hits | < 50% |

### Grafana Dashboard

Import the dashboard from `deploy/monitoring/grafana-dashboard.json`.

Key panels:
- Request rate and latency
- Error rates by endpoint
- Database connection pool
- Redis cache performance
- Workflow execution time distribution

### Log Aggregation

```bash
# Structured JSON logging is enabled by default
# Forward to your logging platform (ELK, CloudWatch, etc.)

# Example: Stream to CloudWatch
aws logs create-log-group --log-group-name /dsi/api
aws logs create-log-stream --log-group-name /dsi/api --log-stream-name prod
```

### Alerting Rules

```yaml
# alerting-rules.yaml
groups:
  - name: dsi-api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: SlowWorkflow
        expr: histogram_quantile(0.99, workflow_duration_seconds) > 30
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Workflow execution is slow"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 40
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections approaching limit"
```

---

## Security Hardening

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate unique JWT secret (256-bit)
- [ ] Enable TLS everywhere (API, database, Redis)
- [ ] Restrict CORS to specific domains
- [ ] Enable rate limiting
- [ ] Configure WAF rules
- [ ] Set up network policies
- [ ] Enable audit logging
- [ ] Review API key permissions
- [ ] Disable debug mode

### TLS Configuration

```bash
# Generate certificates (use cert-manager in K8s)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=api.dsi.yourcompany.com"

# Create K8s secret
kubectl create secret tls dsi-tls \
  --key tls.key \
  --cert tls.crt \
  -n dsi-prod
```

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dsi-api-policy
  namespace: dsi-prod
spec:
  podSelector:
    matchLabels:
      app: dsi-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: dsi-prod
      ports:
        - port: 5432  # PostgreSQL
        - port: 6379  # Redis
```

### Rate Limiting

Configure in nginx ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dsi-api
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/rate-limit-connections: "10"
```

---

## Troubleshooting

### Common Issues

#### API Won't Start

```bash
# Check logs
kubectl logs -l app=dsi-api -n dsi-prod --tail=100

# Common causes:
# 1. Database connection failed
# 2. Missing environment variables
# 3. Invalid configuration

# Verify database connectivity
kubectl exec -it dsi-api-xxx -n dsi-prod -- python -c "
from technical_pricing.db.config import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database OK' if result else 'Database FAIL')
"
```

#### High Memory Usage

```bash
# Check memory
kubectl top pods -n dsi-prod

# Common causes:
# 1. Signal cache too large
# 2. Memory leak in extractor
# 3. Too many concurrent workflows

# Restart with memory limit
kubectl set resources deployment dsi-api \
  --limits=memory=2Gi \
  --requests=memory=1Gi \
  -n dsi-prod
```

#### Slow Workflow Execution

```bash
# Check workflow timing
curl -s http://localhost:8000/api/v1/metrics | jq '.workflow_duration'

# Common causes:
# 1. External API timeouts
# 2. Database slow queries
# 3. Redis cache miss

# Enable query logging
export DSI_DEBUG=true
```

#### Redis Connection Issues

```bash
# Test Redis connectivity
kubectl exec -it dsi-api-xxx -n dsi-prod -- python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
print('PING:', r.ping())
"

# Check Redis cluster status
kubectl exec -it redis-0 -n dsi-prod -- redis-cli cluster info
```

### Debug Mode

```bash
# Enable debug logging (NOT for production)
kubectl set env deployment/dsi-api DSI_DEBUG=true -n dsi-prod

# Disable after debugging
kubectl set env deployment/dsi-api DSI_DEBUG=false -n dsi-prod
```

---

## Runbook

### Daily Operations

| Task | Command | Frequency |
|-|-|--|
| Check health | `curl /api/v1/health` | Hourly |
| Review error logs | `kubectl logs -l app=dsi-api \| grep ERROR` | Daily |
| Check disk usage | `df -h` on database server | Daily |
| Verify backups | Check backup job status | Daily |

### Weekly Operations

| Task | Command | Notes |
|-|-|-|
| Rotate logs | Automatic with logrotate | Verify rotation |
| Database vacuum | `VACUUM ANALYZE;` | Off-peak hours |
| Review metrics | Grafana dashboard | Check trends |
| Test backup restore | Restore to staging | Verify integrity |

### Deployment Procedure

```bash
# 1. Tag release
git tag -a v0.2.1 -m "Release v0.2.1"
git push origin v0.2.1

# 2. Build and push image
docker build -t dsi-api:v0.2.1 .
docker push your-registry/dsi-api:v0.2.1

# 3. Deploy to staging
helm upgrade dsi-api ./helm/dsi-api \
  --namespace dsi-staging \
  --set image.tag=v0.2.1

# 4. Run smoke tests
./scripts/smoke-test.sh staging

# 5. Deploy to production
helm upgrade dsi-api ./helm/dsi-api \
  --namespace dsi-prod \
  --set image.tag=v0.2.1

# 6. Verify
kubectl rollout status deployment/dsi-api -n dsi-prod
```

### Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/dsi-api -n dsi-prod

# Rollback to specific revision
kubectl rollout history deployment/dsi-api -n dsi-prod
kubectl rollout undo deployment/dsi-api --to-revision=3 -n dsi-prod

# Helm rollback
helm rollback dsi-api 1 -n dsi-prod
```

### Incident Response

1. **Acknowledge** - Update incident channel
2. **Assess** - Check health endpoints and logs
3. **Mitigate** - Scale up, rollback, or disable feature
4. **Communicate** - Update stakeholders
5. **Resolve** - Fix root cause
6. **Review** - Post-incident report

### Contacts

| Role | Contact | Escalation |
|-|-|-|
| On-call Engineer | PagerDuty | Automatic |
| Platform Lead | Slack #dsi-platform | Manual |
| Security | security@company.com | For breaches |

---

## Appendix

### Resource Sizing

| Environment | API Replicas | CPU | Memory | Database |
|-|-|-|--|-|
| Development | 1 | 0.5 | 512Mi | Local |
| Staging | 2 | 1 | 1Gi | db.t3.medium |
| Production | 3+ | 2 | 2Gi | db.r6g.large |

### Version Compatibility

| DSI Version | Python | PostgreSQL | Redis |
|-|-|-|-|
| 0.2.x | 3.10-3.12 | 14-16 | 7.x |
| 0.1.x | 3.10-3.11 | 14-15 | 6.x |

### Useful Commands

```bash
# Port forward for local debugging
kubectl port-forward svc/dsi-api 8000:8000 -n dsi-prod

# Exec into pod
kubectl exec -it dsi-api-xxx -n dsi-prod -- /bin/bash

# View real-time logs
kubectl logs -f -l app=dsi-api -n dsi-prod

# Describe pod issues
kubectl describe pod dsi-api-xxx -n dsi-prod
```
