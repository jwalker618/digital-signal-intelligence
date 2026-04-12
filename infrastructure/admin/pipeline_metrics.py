"""
B-1d: PipelineMetrics

Assessment pipeline throughput, latency percentiles, and failure rates.
Computed on-demand from model_versions / submissions, with hourly
snapshots persisted to metric_snapshots for trend charts.

Metrics:
- throughput: assessments per hour / per day
- latency P50 / P95 / P99: from submissions.processing_duration_ms
- failure rate: count of submissions with status=FAILED / total
- average signal extraction time: from model_versions latency columns
  (when available; falls back to a heuristic when not)

Scheduler integration: `snapshot_hourly()` is designed to be called on
an hourly cron or as a periodic task by the scheduler. It writes one row
to metric_snapshots and can be queried for trend data.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.admin.pipeline_metrics")


@dataclass
class PipelineSnapshot:
    """A point-in-time snapshot of pipeline metrics."""

    captured_at: datetime
    period: str   # "1h" | "24h" | "7d" | "30d"
    coverage: Optional[str] = None
    # Throughput
    assessments_total: int = 0
    assessments_per_hour: float = 0.0
    # Latency (workflow execution)
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    # Failure
    failure_count: int = 0
    failure_rate: float = 0.0
    # Decision mix
    decision_mix: dict = field(default_factory=dict)


class PipelineMetrics:
    """Assessment throughput, latency, and failure rate computation."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # On-demand computation
    # ------------------------------------------------------------------

    def compute(
        self,
        period: str = "24h",
        coverage: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> PipelineSnapshot:
        """Compute pipeline metrics for the given period window.

        Period values: '1h', '24h', '7d', '30d'.
        """
        as_of = as_of or datetime.now(timezone.utc)
        since = self._period_start(as_of, period)

        snapshot = PipelineSnapshot(captured_at=as_of, period=period, coverage=coverage)

        # Throughput + failure
        conditions = ["s.created_at >= :since", "s.created_at <= :as_of"]
        params: dict = {"since": since, "as_of": as_of}
        if coverage:
            conditions.append("s.coverage = :coverage")
            params["coverage"] = coverage
        where = " AND ".join(conditions)

        try:
            counts = self.db.execute(
                text(
                    f"""
                    SELECT
                        COUNT(*)                                              AS total,
                        SUM(CASE WHEN s.status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
                        AVG(s.processing_duration_ms)                         AS avg_latency
                    FROM submissions s
                    WHERE {where}
                    """
                ),
                params,
            ).mappings().first()
        except Exception:
            counts = None

        if counts:
            snapshot.assessments_total = int(counts["total"] or 0)
            snapshot.failure_count = int(counts["failed"] or 0)
            if snapshot.assessments_total > 0:
                snapshot.failure_rate = snapshot.failure_count / snapshot.assessments_total
                hours = max(1.0, (as_of - since).total_seconds() / 3600.0)
                snapshot.assessments_per_hour = snapshot.assessments_total / hours
            snapshot.avg_latency_ms = (
                float(counts["avg_latency"]) if counts["avg_latency"] is not None else None
            )

        # Latency percentiles
        try:
            latency_rows = self.db.execute(
                text(
                    f"""
                    SELECT
                        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY s.processing_duration_ms) AS p50,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY s.processing_duration_ms) AS p95,
                        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY s.processing_duration_ms) AS p99
                    FROM submissions s
                    WHERE {where} AND s.processing_duration_ms IS NOT NULL
                    """
                ),
                params,
            ).mappings().first()
        except Exception:
            latency_rows = None

        if latency_rows:
            snapshot.latency_p50_ms = _safe_float(latency_rows["p50"])
            snapshot.latency_p95_ms = _safe_float(latency_rows["p95"])
            snapshot.latency_p99_ms = _safe_float(latency_rows["p99"])

        # Decision mix (from model_versions)
        try:
            mix = self.db.execute(
                text(
                    f"""
                    SELECT m.decision, COUNT(*) AS n
                    FROM submissions s
                    JOIN model_versions m ON m.submission_id = s.id
                    WHERE {where} AND m.decision IS NOT NULL
                    GROUP BY m.decision
                    """
                ),
                params,
            ).all()
            snapshot.decision_mix = {str(row[0]): int(row[1]) for row in mix}
        except Exception:
            pass

        return snapshot

    # ------------------------------------------------------------------
    # Snapshot persistence
    # ------------------------------------------------------------------

    def snapshot_hourly(self, coverage: Optional[str] = None) -> str:
        """Persist a 1-hour-window snapshot for trend charts. Returns the row id."""
        return self._persist_snapshot(period="1h", snapshot_type="hourly", coverage=coverage)

    def snapshot_daily(self, coverage: Optional[str] = None) -> str:
        """Persist a 24h-window snapshot."""
        return self._persist_snapshot(period="24h", snapshot_type="daily", coverage=coverage)

    def _persist_snapshot(
        self, period: str, snapshot_type: str, coverage: Optional[str]
    ) -> str:
        snapshot = self.compute(period=period, coverage=coverage)
        import uuid as _uuid

        snap_id = str(_uuid.uuid4())
        self.db.execute(
            text(
                """
                INSERT INTO metric_snapshots (
                    id, snapshot_type, captured_at, coverage, metrics
                ) VALUES (
                    :id, :snapshot_type, :captured_at, :coverage, CAST(:metrics AS jsonb)
                )
                """
            ),
            {
                "id": snap_id,
                "snapshot_type": snapshot_type,
                "captured_at": snapshot.captured_at,
                "coverage": snapshot.coverage,
                "metrics": json.dumps({
                    "period": snapshot.period,
                    "assessments_total": snapshot.assessments_total,
                    "assessments_per_hour": snapshot.assessments_per_hour,
                    "latency_p50_ms": snapshot.latency_p50_ms,
                    "latency_p95_ms": snapshot.latency_p95_ms,
                    "latency_p99_ms": snapshot.latency_p99_ms,
                    "avg_latency_ms": snapshot.avg_latency_ms,
                    "failure_count": snapshot.failure_count,
                    "failure_rate": snapshot.failure_rate,
                    "decision_mix": snapshot.decision_mix,
                }, default=str),
            },
        )
        return snap_id

    # ------------------------------------------------------------------
    # Historical retrieval
    # ------------------------------------------------------------------

    def history(
        self,
        snapshot_type: str = "hourly",
        coverage: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 168,
    ) -> list[dict]:
        """Return persisted snapshot rows, newest first. 168 = 7 days of hourly."""
        since = since or (datetime.now(timezone.utc) - timedelta(days=7))
        params: dict = {"snapshot_type": snapshot_type, "since": since, "limit": limit}
        conditions = ["snapshot_type = :snapshot_type", "captured_at >= :since"]
        if coverage:
            conditions.append("coverage = :coverage")
            params["coverage"] = coverage
        where = " WHERE " + " AND ".join(conditions)

        try:
            rows = self.db.execute(
                text(
                    f"""
                    SELECT captured_at, coverage, metrics
                    FROM metric_snapshots{where}
                    ORDER BY captured_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            ).mappings().all()
        except Exception:
            return []

        return [
            {
                "captured_at": row["captured_at"].isoformat() if row["captured_at"] else None,
                "coverage": row["coverage"],
                **(row["metrics"] or {}),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _period_start(as_of: datetime, period: str) -> datetime:
        mapping = {"1h": 1, "24h": 24, "7d": 24 * 7, "30d": 24 * 30}
        hours = mapping.get(period, 24)
        return as_of - timedelta(hours=hours)


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
