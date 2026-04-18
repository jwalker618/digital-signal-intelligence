"""V6/E6 (stage 1.2) — detector ↔ referral-bridge wiring tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

import pytest

from world_engine.drift.wiring import (
    _priority_for_severity,
    _referral_row_dispatcher,
    wire_default_drift_observers,
)


@dataclass
class _FakeAlert:
    id: str = "drift-1"
    entity_id: Optional[str] = "acme"
    coverage: Optional[str] = "cyber"
    config_id: Optional[str] = "cyber_general"
    drift_type: str = "relationship_shift"
    severity: str = "high"
    detected_at: str = "2026-04-17T12:00:00+00:00"
    message: str = "rho shift"
    metadata: Optional[dict] = None


class _FakeDetector:
    def __init__(self) -> None:
        self._observers: list = []

    def on_alert(self, observer):
        self._observers.append(observer)


class _RecordingDB:
    def __init__(self) -> None:
        self.calls: List[Any] = []
        self.committed = False
        self.closed = False

    def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params))

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_priority_map_matches_spec():
    assert _priority_for_severity("high") == 1
    assert _priority_for_severity("medium") == 3
    assert _priority_for_severity("low") == 6
    assert _priority_for_severity("unknown") == 5  # default


def test_wire_registers_observer_and_returns_bridge():
    detector = _FakeDetector()
    db = _RecordingDB()

    bridge = wire_default_drift_observers(detector, db_factory=lambda: db)
    assert len(detector._observers) == 1
    assert bridge is not None


def test_dispatcher_inserts_referral_row():
    db = _RecordingDB()
    dispatch = _referral_row_dispatcher(lambda: db)

    from world_engine.drift.referral_bridge import drift_alert_to_referral

    referral = drift_alert_to_referral(_FakeAlert())
    dispatch(referral)

    assert len(db.calls) == 1
    stmt, params = db.calls[0]
    assert "INSERT INTO referrals" in stmt
    assert params["drift_alert_id"] == "drift-1"
    assert params["priority"] == 1  # severity=high
    assert params["reasons"][0]["kind"] == "relationship_shift"
    assert params["reasons"][0]["severity"] == "high"
    assert db.committed is True
    assert db.closed is True


def test_wire_end_to_end_dispatches_on_alert():
    db = _RecordingDB()
    detector = _FakeDetector()
    wire_default_drift_observers(detector, db_factory=lambda: db)

    # Simulate the detector firing
    detector._observers[0](_FakeAlert(severity="medium"))
    assert len(db.calls) == 1
    stmt, params = db.calls[0]
    assert params["priority"] == 3  # severity=medium


def test_extra_dispatchers_all_invoked():
    received: list = []

    def extra(r):
        received.append(r)

    detector = _FakeDetector()
    wire_default_drift_observers(
        detector,
        db_factory=None,  # no DB writer
        extra_dispatchers=[extra],
    )
    detector._observers[0](_FakeAlert())
    assert len(received) == 1
