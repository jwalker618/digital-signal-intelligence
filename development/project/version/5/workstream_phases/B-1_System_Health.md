# Phase B-1: System Health & Pipeline Monitoring

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (admin role required for access) |

---

## Overview

Real-time dashboard showing operational health of every DSI subsystem: API, database, Redis, extractors, assessment pipeline throughput, and latency. This is the first admin backend phase and establishes the `/admin` route.

## Current State

- `infrastructure/api/main.py` -- Health endpoints at `/api/v1/health/live` and `/api/v1/health/ready` (basic up/down)
- Prometheus metrics at `/metrics` and `/api/v1/metrics` (request latency, error rates, workflow duration)
- `infrastructure/analytics/performance.py` -- Performance metrics (loss ratios, ROI, approval rates)
- `infrastructure/analytics/workflow_analytics.py` -- Workflow-level metrics (processing time, decision distribution)
- No per-extractor health tracking. No admin UI. No historical metric storage.

## Target State

Admin dashboard with real-time health status, per-extractor metrics, pipeline throughput/latency charts, and alert configuration.

---

## Implementation Plan

### B-1a: System Health Aggregator

**New file**: `infrastructure/admin/health.py`

```python
class SystemHealthAggregator:
    """Queries all subsystems and returns unified health object."""

    def get_health(self) -> SystemHealth:
        """
        Checks: API (self), DB connection pool stats, Redis ping,
        World Engine maturity + last scan run, extractor summary.
        Returns green/amber/red per subsystem.
        """
```

### B-1b: Extractor Health Tracking

**Migration**: `alembic/versions/014_admin_metrics.py`

| Table | Key Columns |
|-------|-------------|
| `extractor_health` | `extractor_id`, `coverage`, `last_success_at`, `last_error_at`, `success_count_24h`, `error_count_24h`, `avg_latency_ms`, `data_freshness_score` |
| `metric_snapshots` | `id`, `snapshot_type` (hourly/daily), `metrics` (JSONB), `captured_at` |

**New file**: `infrastructure/admin/extractor_tracker.py`

```python
class ExtractorTracker:
    """Records per-extractor health metrics from signal extraction pipeline."""

    def record_extraction(self, extractor_id: str, success: bool, latency_ms: float): ...
    def get_health(self, coverage: str | None = None) -> list[ExtractorHealth]: ...
```

**File to modify**: `signal_architecture/extractors/` base class -- Add tracker hook after each extraction.

### B-1c: Pipeline Metrics

**New file**: `infrastructure/admin/pipeline_metrics.py`

```python
class PipelineMetrics:
    """Assessment throughput, latency percentiles, failure rates."""

    def get_metrics(self, period: str = "24h", coverage: str | None = None) -> dict:
        """
        Queries ModelVersionRecord for:
        - Throughput: assessments per hour/day
        - Latency: P50/P95/P99 from workflow duration
        - Failure rate by coverage
        - Average signal extraction time, pricing time
        """
```

Hourly snapshots stored in `metric_snapshots` (7 days granular, 90 days daily aggregates). Snapshot job runs via scheduler.

### B-1d: Admin API

**New file**: `infrastructure/api/admin/routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/health` | GET | Unified system health |
| `/admin/health/extractors` | GET | Per-extractor metrics (filterable by coverage, status) |
| `/admin/health/pipeline` | GET | Throughput, latency, failure rates |
| `/admin/health/pipeline/history` | GET | Historical metrics (date range) |
| `/admin/alerts` | GET/PUT | Alert threshold configuration |

All endpoints require `admin:system` permission.

**File to modify**: `infrastructure/api/main.py` -- Mount admin router at `/api/v1/admin/`.

### B-1e: Frontend -- Admin Dashboard

**New file**: `frontend/src/app/admin/layout.tsx` -- Admin shell with own sidebar navigation, permission-gated to admin role.

**New file**: `frontend/src/app/admin/page.tsx` -- System health dashboard:
- Green/amber/red indicators for API, DB, Redis, World Engine, each extractor group
- Auto-refresh every 30 seconds

**New file**: `frontend/src/components/admin/ExtractorHealthPanel.tsx`
- Table: extractor, status, success rate, last run, data freshness
- Expandable rows with error details. Filter by coverage/status.

**New file**: `frontend/src/components/admin/PipelineMetricsPanel.tsx`
- Time-series charts: throughput, latency, failure rate. Coverage breakdown. Date range selector.

**New file**: `frontend/src/components/admin/AlertConfigPanel.tsx`
- Set thresholds (e.g., extractor error rate > 10%, P95 latency > 5s). Alerts in dashboard header.

---

## Constraints

1. Admin routes return 403 for non-admin users
2. Health checks must complete in <2s (don't block on slow subsystems -- use timeouts)
3. Metric snapshots must not impact assessment pipeline performance

## Success Criteria

1. Dashboard shows real-time health for all subsystems
2. Extractor health table shows per-extractor metrics with real data
3. Pipeline metrics charts render with historical data
4. Alerts trigger when thresholds are breached
5. Non-admin users cannot access `/admin` routes
