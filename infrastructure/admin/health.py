"""
B-1b: SystemHealthAggregator

Produces a single green/amber/red health report across every DSI
subsystem. Drives the admin dashboard's top-level status tiles.

Checks are fail-open: if one subsystem's check raises, the aggregator
returns a DEGRADED status for that subsystem rather than crashing the
dashboard.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.admin.health")


class HealthStatus(str, Enum):
    """Traffic-light status for a subsystem."""
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class SubsystemHealth:
    """Health snapshot for one subsystem."""
    name: str
    status: HealthStatus
    detail: str = ""
    metrics: dict = field(default_factory=dict)
    latency_ms: Optional[float] = None


@dataclass
class SystemHealth:
    """Aggregate health across all subsystems."""
    overall: HealthStatus
    subsystems: list[SubsystemHealth] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SystemHealthAggregator:
    """Unified health across API, DB, Redis, World Engine, extractors."""

    # Any check that exceeds this budget is marked DEGRADED for latency.
    LATENCY_BUDGET_MS = 2000.0

    def __init__(self, db: Session):
        self.db = db

    def get_health(self) -> SystemHealth:
        """Run all subsystem checks and return the aggregated SystemHealth."""
        subsystems = [
            self._check_api(),
            self._check_database(),
            self._check_redis(),
            self._check_world_engine(),
            self._check_extractors(),
        ]
        overall = self._rollup_status(subsystems)
        return SystemHealth(overall=overall, subsystems=subsystems)

    # ------------------------------------------------------------------
    # Per-subsystem checks
    # ------------------------------------------------------------------

    def _check_api(self) -> SubsystemHealth:
        """API is trivially OK -- if this code runs, the API responded."""
        return SubsystemHealth(
            name="api",
            status=HealthStatus.OK,
            detail="API serving requests",
        )

    def _check_database(self) -> SubsystemHealth:
        """Simple SELECT 1 latency check."""
        try:
            start = time.monotonic()
            result = self.db.execute(text("SELECT 1")).scalar()
            latency = (time.monotonic() - start) * 1000.0
            if result != 1:
                return SubsystemHealth(
                    name="database",
                    status=HealthStatus.DOWN,
                    detail="SELECT 1 did not return 1",
                )
            if latency > self.LATENCY_BUDGET_MS:
                return SubsystemHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    detail=f"SELECT 1 took {latency:.0f}ms (> {self.LATENCY_BUDGET_MS:.0f}ms budget)",
                    latency_ms=latency,
                )
            return SubsystemHealth(
                name="database",
                status=HealthStatus.OK,
                detail=f"SELECT 1 in {latency:.0f}ms",
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return SubsystemHealth(
                name="database",
                status=HealthStatus.DOWN,
                detail=f"Database unreachable: {exc}",
            )

    def _check_redis(self) -> SubsystemHealth:
        """Ping Redis if configured. DSI tolerates Redis being absent."""
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return SubsystemHealth(
                name="redis",
                status=HealthStatus.UNKNOWN,
                detail="REDIS_URL not configured",
            )
        try:
            import redis  # noqa: F401  # local import -- optional dependency

            r = redis.Redis.from_url(redis_url, socket_connect_timeout=1.5)
            start = time.monotonic()
            ok = r.ping()
            latency = (time.monotonic() - start) * 1000.0
            if not ok:
                return SubsystemHealth(name="redis", status=HealthStatus.DOWN, detail="Ping returned falsy")
            return SubsystemHealth(
                name="redis",
                status=HealthStatus.OK,
                detail=f"PING in {latency:.0f}ms",
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return SubsystemHealth(
                name="redis",
                status=HealthStatus.DEGRADED,
                detail=f"Redis check failed: {exc}",
            )

    def _check_world_engine(self) -> SubsystemHealth:
        """Maturity stage + last scan run summary."""
        try:
            from world_engine.maturity import MaturityEvaluator
            maturity = MaturityEvaluator().evaluate(self.db)
            last_scan = self.db.execute(
                text(
                    "SELECT completed_at FROM we_scan_runs "
                    "WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1"
                )
            ).scalar_one_or_none()
            detail = f"Maturity {maturity.stage.value}"
            if last_scan:
                last_scan_ts = last_scan if last_scan.tzinfo else last_scan.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - last_scan_ts).total_seconds() / 3600.0
                detail += f", last scan {age_hours:.1f}h ago"
            return SubsystemHealth(
                name="world_engine",
                status=HealthStatus.OK,
                detail=detail,
                metrics={
                    "maturity_stage": maturity.stage.value,
                    "assessed_entities": maturity.assessed_entity_count,
                    "active_relationships": maturity.active_relationships,
                },
            )
        except Exception as exc:  # noqa: BLE001
            return SubsystemHealth(
                name="world_engine",
                status=HealthStatus.DEGRADED,
                detail=f"Maturity check failed: {exc}",
            )

    def _check_extractors(self) -> SubsystemHealth:
        """Aggregate health across all extractor_health rows."""
        try:
            row = self.db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total,
                        SUM(success_count_24h) AS successes,
                        SUM(error_count_24h)   AS errors,
                        MAX(last_success_at)   AS latest_success
                    FROM extractor_health
                    """
                )
            ).mappings().first()
            if row is None or (row["total"] or 0) == 0:
                return SubsystemHealth(
                    name="extractors",
                    status=HealthStatus.UNKNOWN,
                    detail="No extractor health records yet",
                )
            total = int(row["total"])
            successes = int(row["successes"] or 0)
            errors = int(row["errors"] or 0)
            attempts = successes + errors
            error_rate = errors / attempts if attempts > 0 else 0.0

            if error_rate > 0.5:
                status = HealthStatus.DOWN
            elif error_rate > 0.1:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.OK

            detail = (
                f"{total} extractors tracked, {error_rate:.1%} error rate (24h)"
            )
            return SubsystemHealth(
                name="extractors",
                status=status,
                detail=detail,
                metrics={
                    "extractor_count": total,
                    "successes_24h": successes,
                    "errors_24h": errors,
                    "error_rate": round(error_rate, 4),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return SubsystemHealth(
                name="extractors",
                status=HealthStatus.UNKNOWN,
                detail=f"Extractor stats unavailable: {exc}",
            )

    # ------------------------------------------------------------------
    # Rollup
    # ------------------------------------------------------------------

    @staticmethod
    def _rollup_status(subsystems: list[SubsystemHealth]) -> HealthStatus:
        """Overall status = worst subsystem status (DOWN > DEGRADED > OK > UNKNOWN)."""
        priority = {
            HealthStatus.DOWN: 3,
            HealthStatus.DEGRADED: 2,
            HealthStatus.UNKNOWN: 1,
            HealthStatus.OK: 0,
        }
        if not subsystems:
            return HealthStatus.UNKNOWN
        worst = max(subsystems, key=lambda s: priority.get(s.status, 0))
        return worst.status
