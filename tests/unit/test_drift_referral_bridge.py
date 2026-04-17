"""V6/E6 — drift-alert → referral-queue bridge tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from world_engine.drift.referral_bridge import (
    DriftReferral,
    DriftReferralBridge,
    drift_alert_to_referral,
)


@dataclass
class _Alert:
    id: str = "alert-1"
    entity_id: Optional[str] = "acme"
    coverage: Optional[str] = "cyber"
    config_id: Optional[str] = "cyber_general"
    drift_type: str = "relationship_shift"
    severity: Optional[str] = None
    z_score: Optional[float] = None
    detected_at: str = "2026-04-17T12:00:00Z"
    message: str = "rho shifted"
    metadata: Optional[dict] = None


def test_maps_severity_from_z_score_high():
    r = drift_alert_to_referral(_Alert(severity=None, z_score=3.5))
    assert r.severity == "high"


def test_maps_severity_from_z_score_medium():
    r = drift_alert_to_referral(_Alert(severity=None, z_score=2.2))
    assert r.severity == "medium"


def test_maps_severity_from_z_score_low():
    r = drift_alert_to_referral(_Alert(severity=None, z_score=1.0))
    assert r.severity == "low"


def test_explicit_severity_wins():
    r = drift_alert_to_referral(_Alert(severity="high", z_score=0.1))
    assert r.severity == "high"


def test_referral_fields_populated():
    r = drift_alert_to_referral(_Alert())
    assert r.type == "DRIFT"
    assert r.drift_type == "relationship_shift"
    assert r.entity_id == "acme"
    assert r.drift_alert_id == "alert-1"


def test_bridge_fans_out_to_dispatchers():
    received = []

    def dispatcher_a(r):
        received.append(("a", r))

    def dispatcher_b(r):
        received.append(("b", r))

    bridge = DriftReferralBridge([dispatcher_a, dispatcher_b])
    bridge.dispatch_alert(_Alert(severity="medium"))
    assert [name for name, _ in received] == ["a", "b"]


def test_bridge_isolates_dispatcher_failure():
    received = []

    def bad(r):
        raise RuntimeError("downstream down")

    def good(r):
        received.append(r)

    bridge = DriftReferralBridge([bad, good])
    out = bridge.dispatch_alert(_Alert())
    assert isinstance(out, DriftReferral)
    assert len(received) == 1


def test_dispatch_many_processes_all():
    seen = []
    bridge = DriftReferralBridge([lambda r: seen.append(r)])
    alerts = [_Alert(id=f"a-{i}") for i in range(3)]
    out = bridge.dispatch_many(alerts)
    assert len(out) == 3 and len(seen) == 3
