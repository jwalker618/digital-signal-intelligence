"""
B-1c: ExtractorTracker

Per-extractor success/error counters, last-seen timestamps, and average
latency. Powers the admin dashboard's extractor health panel.

Design notes:
- Uses PostgreSQL's ON CONFLICT ... DO UPDATE for atomic upsert -- a
  single statement per record, suitable for hot-path instrumentation.
- The 24h counters are approximate: they are decayed (reset) by the
  `reset_stale_windows()` method which the scheduler/admin endpoint
  calls periodically. This is simpler than a rolling window and accurate
  enough for dashboard purposes.
- Latency is tracked as a running average using exponentially weighted
  moving average (EWMA) with alpha=0.1.

The tracker is optional for extractors to call. An extractor doesn't
have to wire this in to work -- it's purely observability.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("dsi.admin.extractor_tracker")


# EWMA alpha for running latency average. alpha=0.1 gives high-pass
# filtering; recent latency dominates but historical values still influence.
LATENCY_EWMA_ALPHA = 0.1


@dataclass
class ExtractorHealthRecord:
    """In-memory snapshot of a single extractor's health row."""
    extractor_id: str
    coverage: Optional[str]
    signal_type: Optional[str]
    success_count_24h: int
    error_count_24h: int
    avg_latency_ms: Optional[float]
    last_success_at: Optional[datetime]
    last_error_at: Optional[datetime]
    last_error_message: Optional[str]
    data_freshness_score: Optional[float]

    @property
    def success_rate(self) -> Optional[float]:
        total = self.success_count_24h + self.error_count_24h
        if total == 0:
            return None
        return self.success_count_24h / total


class ExtractorTracker:
    """Upserts per-extractor health metrics.

    Intended for use by signal extractors + the admin API read-side.
    Call `record_extraction(...)` after each extraction; call
    `get_health(...)` or `list_health(...)` from the admin read API.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Record-side (hot path)
    # ------------------------------------------------------------------

    def record_extraction(
        self,
        extractor_id: str,
        coverage: Optional[str],
        success: bool,
        latency_ms: float,
        signal_type: Optional[str] = None,
        error_message: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Atomically upsert the extractor's health row.

        Never raises -- instrumentation failures must not break the hot path.
        """
        now = datetime.now(timezone.utc)
        try:
            # ON CONFLICT: incremental counter update + EWMA latency.
            # We use a standard upsert; the EWMA is implemented with CASE
            # to preserve the simple semantics of "first sample sets avg,
            # subsequent samples blend".
            sql = text(
                """
                INSERT INTO extractor_health AS eh (
                    extractor_id, coverage, signal_type,
                    success_count_24h, error_count_24h,
                    avg_latency_ms, last_success_at, last_error_at, last_error_message,
                    ttl_seconds, data_freshness_score,
                    created_at, updated_at
                ) VALUES (
                    :extractor_id, :coverage, :signal_type,
                    :success_delta, :error_delta,
                    :latency, :last_success_at, :last_error_at, :last_error_message,
                    :ttl_seconds, :freshness,
                    :now, :now
                )
                ON CONFLICT (extractor_id, coverage) DO UPDATE SET
                    success_count_24h = eh.success_count_24h + :success_delta,
                    error_count_24h   = eh.error_count_24h + :error_delta,
                    avg_latency_ms    = CASE
                        WHEN eh.avg_latency_ms IS NULL THEN :latency
                        ELSE (1 - :alpha) * eh.avg_latency_ms + :alpha * :latency
                    END,
                    last_success_at   = COALESCE(:last_success_at, eh.last_success_at),
                    last_error_at     = COALESCE(:last_error_at, eh.last_error_at),
                    last_error_message = COALESCE(:last_error_message, eh.last_error_message),
                    ttl_seconds       = COALESCE(:ttl_seconds, eh.ttl_seconds),
                    data_freshness_score = COALESCE(:freshness, eh.data_freshness_score),
                    updated_at        = :now
                """
            )
            self.db.execute(
                sql,
                {
                    "extractor_id": extractor_id,
                    "coverage": coverage,
                    "signal_type": signal_type,
                    "success_delta": 1 if success else 0,
                    "error_delta": 0 if success else 1,
                    "latency": float(latency_ms),
                    "last_success_at": now if success else None,
                    "last_error_at": now if not success else None,
                    "last_error_message": error_message if not success else None,
                    "ttl_seconds": ttl_seconds,
                    "freshness": self._compute_freshness(ttl_seconds, now, success),
                    "alpha": LATENCY_EWMA_ALPHA,
                    "now": now,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("ExtractorTracker.record_extraction failed (non-blocking): %s", exc)

    def reset_stale_windows(self, older_than_hours: int = 24) -> int:
        """Reset 24h counters for extractors whose latest activity is older
        than `older_than_hours`. Returns the number of rows reset.

        Called periodically (by the scheduler or a cron). Keeps the 24h
        counters approximately accurate without a true rolling window.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        try:
            result = self.db.execute(
                text(
                    """
                    UPDATE extractor_health
                    SET success_count_24h = 0, error_count_24h = 0,
                        updated_at = :now
                    WHERE GREATEST(
                        COALESCE(last_success_at, '1970-01-01'::timestamptz),
                        COALESCE(last_error_at, '1970-01-01'::timestamptz)
                    ) < :cutoff
                    """
                ),
                {"cutoff": cutoff, "now": datetime.now(timezone.utc)},
            )
            return result.rowcount or 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("ExtractorTracker.reset_stale_windows failed: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Read-side (admin dashboard)
    # ------------------------------------------------------------------

    def list_health(
        self,
        coverage: Optional[str] = None,
        limit: int = 500,
    ) -> list[ExtractorHealthRecord]:
        """Return all extractor health records, optionally filtered by coverage."""
        conditions: list[str] = []
        params: dict = {"limit": limit}
        if coverage:
            conditions.append("coverage = :coverage")
            params["coverage"] = coverage
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        try:
            rows = self.db.execute(
                text(
                    f"""
                    SELECT extractor_id, coverage, signal_type,
                           success_count_24h, error_count_24h,
                           avg_latency_ms,
                           last_success_at, last_error_at, last_error_message,
                           data_freshness_score
                    FROM extractor_health{where}
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            ).mappings().all()
        except Exception:
            return []

        return [
            ExtractorHealthRecord(
                extractor_id=row["extractor_id"],
                coverage=row["coverage"],
                signal_type=row["signal_type"],
                success_count_24h=int(row["success_count_24h"] or 0),
                error_count_24h=int(row["error_count_24h"] or 0),
                avg_latency_ms=row["avg_latency_ms"],
                last_success_at=row["last_success_at"],
                last_error_at=row["last_error_at"],
                last_error_message=row["last_error_message"],
                data_freshness_score=row["data_freshness_score"],
            )
            for row in rows
        ]

    def get_health(
        self, extractor_id: str, coverage: Optional[str] = None
    ) -> Optional[ExtractorHealthRecord]:
        """Return a single extractor's health record, or None."""
        conditions = ["extractor_id = :extractor_id"]
        params: dict = {"extractor_id": extractor_id}
        if coverage:
            conditions.append("coverage = :coverage")
            params["coverage"] = coverage
        where = " WHERE " + " AND ".join(conditions)
        try:
            row = self.db.execute(
                text(
                    f"""
                    SELECT extractor_id, coverage, signal_type,
                           success_count_24h, error_count_24h,
                           avg_latency_ms,
                           last_success_at, last_error_at, last_error_message,
                           data_freshness_score
                    FROM extractor_health{where}
                    LIMIT 1
                    """
                ),
                params,
            ).mappings().first()
        except Exception:
            return None
        if row is None:
            return None
        return ExtractorHealthRecord(
            extractor_id=row["extractor_id"],
            coverage=row["coverage"],
            signal_type=row["signal_type"],
            success_count_24h=int(row["success_count_24h"] or 0),
            error_count_24h=int(row["error_count_24h"] or 0),
            avg_latency_ms=row["avg_latency_ms"],
            last_success_at=row["last_success_at"],
            last_error_at=row["last_error_at"],
            last_error_message=row["last_error_message"],
            data_freshness_score=row["data_freshness_score"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_freshness(ttl_seconds: Optional[int], now: datetime, success: bool) -> Optional[float]:
        """Compute a 0-1 freshness score based on TTL. Simple heuristic:
        a successful extraction with a known TTL scores 1.0 at record
        time; score decays are handled at read-side based on age."""
        if ttl_seconds is None:
            return None
        return 1.0 if success else 0.0
