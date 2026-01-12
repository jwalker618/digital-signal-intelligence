# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|deployment|

---

# DSI Deployment Configurations

This directory contains production deployment configurations for the DSI platform.

For the complete deployment guide, see: [docs/deployment/deployment_guide.md](../docs/deployment/deployment_guide.md)

## Directory Structure

```
deploy/
├── docker/                    # Docker deployment
│   ├── docker-compose.prod.yml   # Production compose file
│   └── init-db.sql              # Database initialization
├── kubernetes/                # Kubernetes manifests
│   ├── namespace.yaml           # DSI namespace
│   ├── configmap.yaml           # Configuration
│   ├── secrets.yaml             # Secrets template
│   ├── deployment.yaml          # API deployment
│   ├── service.yaml             # ClusterIP service
│   ├── ingress.yaml             # Ingress rules
│   ├── hpa.yaml                 # Horizontal Pod Autoscaler
│   └── kustomization.yaml       # Kustomize config
└── monitoring/                # Observability
    ├── prometheus-config.yaml   # Prometheus scrape configs + alerts
    └── grafana-dashboard.json   # DSI metrics dashboard
```

## Quick Start

### Docker Compose (Simplest)

```bash
# From repository root
cd deploy/docker

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop
docker-compose -f docker-compose.prod.yml down
```

Services started:
- **dsi-api**: FastAPI application on port 8000
- **dsi-db**: PostgreSQL database on port 5432
- **dsi-redis**: Redis cache on port 6379

### Kubernetes

```bash
# From repository root
cd deploy/kubernetes

# Create namespace and resources
kubectl apply -k .

# Or apply individually
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml  # Edit with real values first!
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Check status
kubectl get pods -n dsi
kubectl get svc -n dsi
```

### Monitoring Setup

```bash
# Add Prometheus scrape config
kubectl apply -f monitoring/prometheus-config.yaml

# Import Grafana dashboard
# 1. Open Grafana UI
# 2. Go to Dashboards > Import
# 3. Upload monitoring/grafana-dashboard.json
```

## Configuration

### Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET_KEY` | Yes | JWT signing secret (generate with `openssl rand -hex 32`) |
| `API_KEY_SECRET` | Yes | API key encryption secret |
| `DSI_ENV` | No | Environment (development/staging/production) |

### Secrets

Before deploying, update `kubernetes/secrets.yaml` with real values:

```bash
# Generate secrets
echo -n "your-db-password" | base64
echo -n "your-jwt-secret" | base64

# Edit secrets.yaml with encoded values
```

## Health Checks

The API exposes health endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/health` | Full health status |
| `/api/v1/health/ready` | Kubernetes readiness probe |
| `/api/v1/health/live` | Kubernetes liveness probe |

## Scaling

### Horizontal Pod Autoscaler

The included HPA scales based on CPU/memory:

```yaml
# Current settings in hpa.yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilization: 70%
targetMemoryUtilization: 80%
```

### Manual Scaling

```bash
kubectl scale deployment dsi-api -n dsi --replicas=5
```

## Monitoring

### Prometheus Metrics

The API exposes metrics at `/metrics`:
- Request latency histograms
- Request counts by endpoint
- Error rates
- Active connections

### Grafana Dashboard

The included dashboard shows:
- Request rate and latency (p50, p95, p99)
- Error rates
- Assessment processing times
- Tier and decision distributions
- Cache hit rates
- Database connection pool status

### Alerts

Configured alerts in `prometheus-config.yaml`:
- High error rate (>5%)
- High latency (p99 > 5s)
- Pod restarts
- Database connection failures
- Cache connection failures

## Troubleshooting

### Common Issues

**API won't start:**
```bash
# Check logs
kubectl logs -f deployment/dsi-api -n dsi

# Common causes:
# - DATABASE_URL not set or incorrect
# - Database not reachable
# - Missing secrets
```

**Database connection failed:**
```bash
# Test connection
kubectl run -it --rm debug --image=postgres:15 -- psql $DATABASE_URL

# Check network policies
kubectl get networkpolicies -n dsi
```

**High latency:**
```bash
# Check resource usage
kubectl top pods -n dsi

# Scale up if needed
kubectl scale deployment dsi-api -n dsi --replicas=5
```

## Security Notes

- Never commit real secrets to version control
- Use Kubernetes secrets or external secret managers
- Enable TLS for all external traffic
- Restrict database access to API pods only
- Rotate JWT secrets periodically
