"""V6/E6 — Drift-alert → referral-queue bridge.

When the drift detector produces an alert, this module converts it to
a structured referral payload for the existing referral API / queue.
Keeps the drift detector ignorant of the referral service (no coupling
reversal). The bridge is registered as an alert-observer by the
detector's ``on_alert`` hook (added in follow-up wiring).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("dsi.drift.referral_bridge")


@dataclass(frozen=True)
class DriftReferral:
    """Structured payload dispatched to ReferralService."""
    type: str                             # "DRIFT" — fixed
    severity: str                         # 'low' | 'medium' | 'high'
    entity_id: Optional[str]
    coverage: Optional[str]
    config_id: Optional[str]
    drift_type: str                       # relationship_shift | correlation_inversion | regime_change | emergence_burst | velocity
    drift_alert_id: Optional[str]         # FK into drift_alerts table
    detected_at: str                      # ISO timestamp
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _severity_from_alert(alert: Any) -> str:
    """Map DriftAlert.severity / z_score to a 3-level band."""
    sev = getattr(alert, "severity", None)
    if isinstance(sev, str) and sev.lower() in ("low", "medium", "high"):
        return sev.lower()
    z = getattr(alert, "z_score", None) or getattr(alert, "delta_sigma", None)
    try:
        z = float(z) if z is not None else 0.0
    except (TypeError, ValueError):
        z = 0.0
    if abs(z) >= 3.0:
        return "high"
    if abs(z) >= 2.0:
        return "medium"
    return "low"


def drift_alert_to_referral(alert: Any) -> DriftReferral:
    """Normalise a DriftAlert-like object into a DriftReferral."""
    return DriftReferral(
        type="DRIFT",
        severity=_severity_from_alert(alert),
        entity_id=getattr(alert, "entity_id", None),
        coverage=getattr(alert, "coverage", None),
        config_id=getattr(alert, "config_id", None),
        drift_type=getattr(alert, "drift_type", None)
                   or getattr(alert, "kind", None)
                   or "unknown",
        drift_alert_id=(
            str(getattr(alert, "id", "")) if getattr(alert, "id", None) else None
        ),
        detected_at=(
            getattr(alert, "detected_at", "")
            if isinstance(getattr(alert, "detected_at", ""), str)
            else (
                getattr(getattr(alert, "detected_at", None), "isoformat", lambda: "")()
            )
        ),
        message=getattr(alert, "message", "Drift detected"),
        metadata=getattr(alert, "metadata", {}) or {},
    )


ReferralDispatcher = Callable[[DriftReferral], Any]


class DriftReferralBridge:
    """Fan-out adapter.

    Construct with a list of dispatchers (functions that take a
    DriftReferral and persist / enqueue it). On each alert the bridge
    invokes every dispatcher; individual dispatcher failures are logged
    but do not block the rest.
    """

    def __init__(self, dispatchers: Optional[List[ReferralDispatcher]] = None):
        self._dispatchers: List[ReferralDispatcher] = list(dispatchers or [])

    def register(self, dispatcher: ReferralDispatcher) -> None:
        self._dispatchers.append(dispatcher)

    def dispatch_alert(self, alert: Any) -> DriftReferral:
        referral = drift_alert_to_referral(alert)
        for fn in self._dispatchers:
            try:
                fn(referral)
            except Exception as e:  # pragma: no cover — isolated failure
                log.warning("drift referral dispatcher failed: %s", e)
        return referral

    def dispatch_many(self, alerts: List[Any]) -> List[DriftReferral]:
        return [self.dispatch_alert(a) for a in alerts]
