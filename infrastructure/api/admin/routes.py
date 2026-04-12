"""
B-1e: Admin health + pipeline metrics endpoints.

All endpoints require `admin:system` permission. The admin dashboard
frontend (built in the FE integration pass) consumes these.

Endpoints:
- GET  /admin/health                 Unified system health
- GET  /admin/health/extractors      Per-extractor metrics
- POST /admin/health/extractors/reset-stale   Reset stale 24h windows
- GET  /admin/health/pipeline        Current pipeline metrics (period param)
- GET  /admin/health/pipeline/history   Historical metric snapshots
- POST /admin/health/pipeline/snapshot  Trigger an hourly snapshot
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.admin import ExtractorTracker, PipelineMetrics, SystemHealthAggregator
from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_db

logger = logging.getLogger("dsi.api.admin")
router = APIRouter()


# =============================================================================
# System health
# =============================================================================


@router.get(
    "/admin/health",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def get_system_health(db: Session = Depends(get_db)) -> dict:
    """Unified green/amber/red health across all subsystems."""
    health = SystemHealthAggregator(db).get_health()
    return {
        "overall": health.overall.value,
        "evaluated_at": health.evaluated_at.isoformat(),
        "subsystems": [
            {
                "name": sub.name,
                "status": sub.status.value,
                "detail": sub.detail,
                "metrics": sub.metrics,
                "latency_ms": sub.latency_ms,
            }
            for sub in health.subsystems
        ],
    }


# =============================================================================
# Extractor health
# =============================================================================


@router.get(
    "/admin/health/extractors",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def list_extractor_health(
    coverage: Optional[str] = None,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict:
    """Return all extractor health records (per-extractor 24h counters)."""
    tracker = ExtractorTracker(db)
    records = tracker.list_health(coverage=coverage, limit=limit)
    return {
        "extractors": [
            {
                "extractor_id": r.extractor_id,
                "coverage": r.coverage,
                "signal_type": r.signal_type,
                "success_count_24h": r.success_count_24h,
                "error_count_24h": r.error_count_24h,
                "success_rate": r.success_rate,
                "avg_latency_ms": r.avg_latency_ms,
                "last_success_at": r.last_success_at.isoformat() if r.last_success_at else None,
                "last_error_at": r.last_error_at.isoformat() if r.last_error_at else None,
                "last_error_message": r.last_error_message,
                "data_freshness_score": r.data_freshness_score,
            }
            for r in records
        ],
        "count": len(records),
    }


@router.post(
    "/admin/health/extractors/reset-stale",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def reset_stale_extractor_windows(
    older_than_hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> dict:
    """Zero out the 24h counters for extractors not seen in `older_than_hours`."""
    count = ExtractorTracker(db).reset_stale_windows(older_than_hours=older_than_hours)
    db.commit()
    return {"reset_count": count}


# =============================================================================
# Pipeline metrics
# =============================================================================


@router.get(
    "/admin/health/pipeline",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def get_pipeline_metrics(
    period: str = Query(default="24h", pattern="^(1h|24h|7d|30d)$"),
    coverage: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Current pipeline metrics: throughput, latency percentiles, failure rate."""
    snapshot = PipelineMetrics(db).compute(period=period, coverage=coverage)
    return {
        "period": snapshot.period,
        "coverage": snapshot.coverage,
        "captured_at": snapshot.captured_at.isoformat(),
        "assessments_total": snapshot.assessments_total,
        "assessments_per_hour": round(snapshot.assessments_per_hour, 2),
        "latency_p50_ms": snapshot.latency_p50_ms,
        "latency_p95_ms": snapshot.latency_p95_ms,
        "latency_p99_ms": snapshot.latency_p99_ms,
        "avg_latency_ms": snapshot.avg_latency_ms,
        "failure_count": snapshot.failure_count,
        "failure_rate": round(snapshot.failure_rate, 4),
        "decision_mix": snapshot.decision_mix,
    }


@router.get(
    "/admin/health/pipeline/history",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def get_pipeline_history(
    snapshot_type: str = Query(default="hourly", pattern="^(hourly|daily)$"),
    coverage: Optional[str] = None,
    limit: int = Query(default=168, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict:
    """Historical pipeline metric snapshots for trend charts."""
    history = PipelineMetrics(db).history(
        snapshot_type=snapshot_type, coverage=coverage, limit=limit
    )
    return {"snapshots": history, "count": len(history)}


@router.post(
    "/admin/health/pipeline/snapshot",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def trigger_pipeline_snapshot(
    snapshot_type: str = Query(default="hourly", pattern="^(hourly|daily)$"),
    coverage: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Manually trigger a metric snapshot (usually called by a scheduler)."""
    metrics = PipelineMetrics(db)
    if snapshot_type == "hourly":
        snap_id = metrics.snapshot_hourly(coverage=coverage)
    else:
        snap_id = metrics.snapshot_daily(coverage=coverage)
    db.commit()
    return {"id": snap_id, "snapshot_type": snapshot_type, "coverage": coverage}
