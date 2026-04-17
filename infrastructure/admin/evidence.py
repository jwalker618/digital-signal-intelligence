"""V6/E8 — Evidence dashboard.

Exposes per-coverage / per-config operational evidence through a single
payload: real-signal %, last-calibration + status, last-drift-alert,
last-golden-check + status, confidence distribution, extractor cost,
active quote count, and referral rate. This is the commercial / sales
artefact — "exactly what we have today".

Function: ``build_evidence_snapshot(...)`` — pure function that assembles
the payload from supplied sources (allowing easy stubbing in tests and
the admin endpoint).

Follow-up:
- ``GET /api/v1/admin/evidence`` — authenticated admin route calls
  build_evidence_snapshot() with live Prometheus / DB sources.
- ``deploy/monitoring/grafana/evidence.json`` — Grafana dashboard
  rendering the same data live.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class CoverageEvidence:
    coverage: str
    config: str
    real_signal_pct: float
    stub_signal_pct: float
    last_calibration_at: Optional[str]
    last_calibration_status: Optional[str]
    last_drift_alert_at: Optional[str]
    last_golden_check_at: Optional[str]
    last_golden_check_status: Optional[str]
    avg_confidence_p50: Optional[float]
    avg_confidence_p95: Optional[float]
    ece: Optional[float]
    monthly_extractor_cost_usd: Optional[float]
    active_quote_count_30d: Optional[int]
    referral_rate_30d: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceSnapshot:
    generated_at: str
    coverages: List[CoverageEvidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "coverages": [c.to_dict() for c in self.coverages],
        }


def compute_real_signal_pct(
    production_signals: int, total_signals: int
) -> Tuple[float, float]:
    """Return (real_pct, stub_pct) for a coverage/config.

    ``production_signals`` is the count of signals that actually
    executed via a production extractor (not stub / not
    neutral-absence). ``total_signals`` is the signal count demanded
    by the config.
    """
    if total_signals <= 0:
        return 0.0, 0.0
    real = max(0, min(production_signals, total_signals)) / total_signals
    return round(real, 4), round(1.0 - real, 4)


CoverageRecord = Dict[str, Any]


def build_evidence_snapshot(
    *,
    coverage_configs: List[Tuple[str, str]],
    extractor_telemetry: Optional[Callable[[str, str], CoverageRecord]] = None,
    calibration_telemetry: Optional[Callable[[str], CoverageRecord]] = None,
    golden_telemetry: Optional[Callable[[str, str], CoverageRecord]] = None,
    drift_telemetry: Optional[Callable[[str, str], CoverageRecord]] = None,
    reference_time: Optional[datetime] = None,
) -> EvidenceSnapshot:
    """Assemble an EvidenceSnapshot from pluggable telemetry callables.

    Each callable returns a dict of the form documented in
    ``CoverageEvidence``; missing fields are treated as None. This keeps
    the function pure + testable while letting the admin endpoint wire
    Prometheus / DB / goldens in production.
    """
    ts = (reference_time or _utcnow()).isoformat()
    evs: List[CoverageEvidence] = []
    for coverage, config in coverage_configs:
        ex = extractor_telemetry(coverage, config) if extractor_telemetry else {}
        cal = calibration_telemetry(coverage) if calibration_telemetry else {}
        gold = golden_telemetry(coverage, config) if golden_telemetry else {}
        drift = drift_telemetry(coverage, config) if drift_telemetry else {}

        real_pct, stub_pct = compute_real_signal_pct(
            ex.get("production_signals", 0),
            ex.get("total_signals", 0),
        )

        evs.append(CoverageEvidence(
            coverage=coverage,
            config=config,
            real_signal_pct=real_pct,
            stub_signal_pct=stub_pct,
            last_calibration_at=cal.get("last_calibration_at"),
            last_calibration_status=cal.get("last_calibration_status"),
            last_drift_alert_at=drift.get("last_drift_alert_at"),
            last_golden_check_at=gold.get("last_golden_check_at"),
            last_golden_check_status=gold.get("last_golden_check_status"),
            avg_confidence_p50=ex.get("avg_confidence_p50"),
            avg_confidence_p95=ex.get("avg_confidence_p95"),
            ece=cal.get("ece"),
            monthly_extractor_cost_usd=ex.get("monthly_extractor_cost_usd"),
            active_quote_count_30d=ex.get("active_quote_count_30d"),
            referral_rate_30d=ex.get("referral_rate_30d"),
        ))

    return EvidenceSnapshot(generated_at=ts, coverages=evs)
