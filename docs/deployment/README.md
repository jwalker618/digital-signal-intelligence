# Deployment Documentation

This folder contains the complete deployment guide for the DSI platform.

## Contents

| Document | Description |
|----------|-------------|
| `deployment_guide.md` | Complete production deployment guide |

## Deployment Guide Overview

The deployment guide covers:

1. **Prerequisites** - Required software and accounts
2. **Architecture Overview** - System components and responsibilities
3. **Configuration** - Environment variables and settings
4. **Local Development** - Quick start for development
5. **Docker Deployment** - Container-based deployment
6. **Kubernetes Deployment** - Production K8s deployment
7. **Database Setup** - PostgreSQL configuration and migrations
8. **Monitoring & Observability** - Prometheus, Grafana, logging
9. **Security Hardening** - Production security checklist
10. **Troubleshooting** - Common issues and solutions
11. **Runbook** - Daily/weekly operations and procedures

## Related Resources

| Location | Description |
|----------|-------------|
| `/deploy/` | Deployment configuration files |
| `/deploy/docker/` | Docker Compose files |
| `/deploy/kubernetes/` | K8s manifests |
| `/deploy/monitoring/` | Prometheus and Grafana configs |
| `/.env.example` | Environment variable template |
| `/Dockerfile` | Production container image |

## Quick Start

### Local Development

```bash
# From repository root
pip install -r requirements.txt
cp .env.example .env
uvicorn technical_pricing.api.main:app --reload --port 8000
```

### Docker

```bash
cd deploy/docker
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
cd deploy/kubernetes
kubectl apply -k .
```

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/health` | Health check |
| `/api/v1/health/ready` | K8s readiness probe |
| `/api/v1/health/live` | K8s liveness probe |
| `/api/v1/metrics` | Prometheus metrics |
| `/api/docs` | OpenAPI documentation |

## Security Checklist

Before production deployment:

- [ ] Generate unique JWT secret (256-bit)
- [ ] Configure TLS certificates
- [ ] Restrict CORS origins
- [ ] Enable rate limiting
- [ ] Set up network policies
- [ ] Configure audit logging
- [ ] Disable debug mode
