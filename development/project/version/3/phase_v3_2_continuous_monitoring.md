# Phase V3-2: Continuous Monitoring Pipeline

**Status:** Not Started
**Priority:** High
**Prerequisites:** V3-1 (Test Recovery)

## Context

The DSI Vision Paper describes continuous observation as fundamental — traditional insurance samples risk once per year, violating the Nyquist-Shannon sampling theorem. DSI must observe continuously to satisfy this criterion.

Currently, DSI processes submissions as point-in-time assessments. There is no scheduled re-assessment, signal refresh, or drift detection pipeline.

## Objective

Implement a continuous monitoring pipeline that re-assesses entities on a configurable schedule, detects signal deterioration, triggers alerts, and maintains time-series data for derivative calculations.

## Tasks

1. **Signal Refresh Scheduler** — Configurable per-signal TTL-based refresh (metadata registry provides TTL per signal)
2. **Delta Detection** — Compare new signal values against previous assessment; flag significant changes
3. **Derivative Time-Series** — Store entropy/velocity/drift over time (not just point-in-time)
4. **Alert Pipeline** — When derivatives exceed thresholds, trigger notifications (email, webhook)
5. **Cohort Migration Tracking** — Detect when entity moves between peer groups
6. **API Endpoints** — `/api/v1/monitoring/status`, `/api/v1/monitoring/alerts`

## Architecture

```
Scheduler (cron/celery)
    │
    ├──► Signal Refresh (per-entity, per-signal TTL)
    │       │
    │       └──► Delta Detection
    │               │
    │               ├──► Update Derivatives (entropy/velocity/drift)
    │               │
    │               └──► Check Thresholds
    │                       │
    │                       └──► Alert Pipeline (email/webhook)
    │
    └──► Cohort Recalculation (periodic)
            │
            └──► Migration Detection
```

## Key Files to Create

- `infrastructure/monitoring/scheduler.py` — Signal refresh scheduling
- `infrastructure/monitoring/delta.py` — Change detection
- `infrastructure/monitoring/alerts.py` — Alert pipeline
- `infrastructure/api/routes/monitoring.py` — Monitoring API endpoints

## Success Criteria

- Entities can be enrolled in continuous monitoring
- Signals refresh based on TTL from metadata registry
- Derivatives calculated as time-series (not just snapshots)
- Alerts fire when thresholds exceeded
- Cohort migration detected and logged
