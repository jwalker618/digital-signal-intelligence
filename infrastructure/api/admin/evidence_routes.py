"""V6/E8 Evidence Dashboard admin endpoint.

`GET /api/v1/admin/evidence` returns the per-coverage evidence snapshot
(real-signal %, last calibration / drift / golden timestamps, avg
confidence, extractor cost, referral rate). Identical shape to the
Grafana `evidence.json` dashboard.

Gated by ``Permission.ADMIN_SYSTEM`` so only platform admins can query
it — the snapshot surfaces cost and operational posture that is
sensitive for commercial conversations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.admin.evidence import build_evidence_snapshot
from infrastructure.api.auth.permissions import Permission, require_permission
from infrastructure.db.config import get_db
from infrastructure.models.compiler import get_compiled_configs

logger = logging.getLogger("dsi.api.admin.evidence")
router = APIRouter()


def _discover_coverage_configs() -> List[Tuple[str, str]]:
    """Return every (coverage_id, config_id) pair registered in the compiler."""
    pairs: List[Tuple[str, str]] = []
    for coverage_id, coverage in get_compiled_configs().items():
        for config_id in coverage.configurations:
            pairs.append((coverage_id, config_id))
    return pairs


def _extractor_telemetry_factory(db: Session):
    """Pull Prometheus-style aggregates from the local DB.

    The DB does not carry live Prometheus data; the real admin endpoint
    queries the monitoring backend via HTTP. For the initial release we
    surface the schema + DB-derived counts (30-day quote count, referral
    rate) and leave extractor-cost / confidence percentiles at None —
    the Grafana dashboard renders those directly from Prometheus.
    """
    def fn(coverage: str, config: str) -> Dict[str, Any]:
        try:
            row = db.execute(
                text(
                    "SELECT "
                    "  COUNT(*) AS active_30d, "
                    "  SUM(CASE WHEN status = 'REFERRED' THEN 1 ELSE 0 END)::float "
                    "    / NULLIF(COUNT(*), 0) AS referral_rate "
                    "FROM quotes "
                    "WHERE coverage = :cov AND config = :cfg "
                    "AND created_at > now() - INTERVAL '30 days'"
                ),
                {"cov": coverage, "cfg": config},
            ).one_or_none()
        except Exception as exc:  # pragma: no cover — shape-only test
            logger.debug("evidence: quotes query failed: %s", exc)
            row = None
        return {
            # V6 extraction telemetry is Prometheus-backed — left None here.
            "production_signals": 0,
            "total_signals": 0,
            "avg_confidence_p50": None,
            "avg_confidence_p95": None,
            "monthly_extractor_cost_usd": None,
            "active_quote_count_30d": (row[0] if row else None),
            "referral_rate_30d": (float(row[1]) if row and row[1] is not None else None),
        }
    return fn


def _calibration_telemetry(coverage: str) -> Dict[str, Any]:
    """Stub — the nightly calibration CI job writes a JSON artefact
    that the dashboard can ingest. The admin endpoint surfaces the
    calibration status once the artefact-ingest loop lands."""
    return {
        "last_calibration_at": None,
        "last_calibration_status": None,
        "ece": None,
    }


def _golden_telemetry(coverage: str, config: str) -> Dict[str, Any]:
    """Last golden-check is the most recent successful CI run against
    the golden-entity suite for this coverage. Surfaced as None until
    the CI-run-log ingestor lands — the Grafana dashboard reads
    Prometheus `dsi_coverage_last_golden_check_at` directly."""
    return {
        "last_golden_check_at": None,
        "last_golden_check_status": None,
    }


def _drift_telemetry_factory(db: Session):
    def fn(coverage: str, config: str) -> Dict[str, Any]:
        try:
            row = db.execute(
                text(
                    "SELECT MAX(detected_at) AS last_drift "
                    "FROM drift_alerts "
                    "WHERE coverage = :cov AND config = :cfg"
                ),
                {"cov": coverage, "cfg": config},
            ).one_or_none()
        except Exception as exc:  # pragma: no cover
            logger.debug("evidence: drift query failed: %s", exc)
            row = None
        ts = row[0] if row else None
        return {
            "last_drift_alert_at": ts.isoformat() if ts else None,
        }
    return fn


@router.get(
    "/admin/evidence",
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def get_evidence_snapshot(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Per-(coverage, config) evidence snapshot. Shape matches
    `infrastructure.admin.evidence.EvidenceSnapshot.to_dict()`."""
    snapshot = build_evidence_snapshot(
        coverage_configs=_discover_coverage_configs(),
        extractor_telemetry=_extractor_telemetry_factory(db),
        calibration_telemetry=_calibration_telemetry,
        golden_telemetry=_golden_telemetry,
        drift_telemetry=_drift_telemetry_factory(db),
    )
    return snapshot.to_dict()
