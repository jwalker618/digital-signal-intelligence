"""V6/E8 admin-evidence endpoint unit tests.

Exercises the route handler directly with a stub DB session — full
integration (real Postgres + live Prometheus) happens in the staging
smoke suite.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest


class _StubResult:
    def __init__(self, row):
        self._row = row

    def one_or_none(self):
        return self._row


class _StubDB:
    """Minimal SQLAlchemy-Session-shaped stub."""
    def __init__(self, rows_by_query: Optional[Dict[str, Any]] = None):
        self._rows = rows_by_query or {}
        self.calls: List[str] = []

    def execute(self, stmt, params=None):
        text = str(stmt)
        self.calls.append(text)
        if "FROM quotes" in text:
            return _StubResult((42, 0.12))
        if "FROM drift_alerts" in text:
            return _StubResult((None,))
        return _StubResult(None)


def test_extractor_telemetry_surfaces_quote_counts():
    from infrastructure.api.admin.evidence_routes import _extractor_telemetry_factory

    fn = _extractor_telemetry_factory(_StubDB())
    out = fn("cyber", "cyber_general")
    assert out["active_quote_count_30d"] == 42
    assert out["referral_rate_30d"] == 0.12


def test_drift_telemetry_returns_iso_when_ts_present():
    from infrastructure.api.admin.evidence_routes import _drift_telemetry_factory
    from datetime import datetime, timezone

    class DB:
        def execute(self, stmt, params=None):
            return _StubResult((datetime(2026, 4, 10, tzinfo=timezone.utc),))

    fn = _drift_telemetry_factory(DB())
    out = fn("cyber", "cyber_general")
    assert out["last_drift_alert_at"] == "2026-04-10T00:00:00+00:00"


def test_drift_telemetry_returns_none_when_no_alerts():
    from infrastructure.api.admin.evidence_routes import _drift_telemetry_factory

    class DB:
        def execute(self, stmt, params=None):
            return _StubResult((None,))

    fn = _drift_telemetry_factory(DB())
    assert fn("cyber", "cyber_general") == {"last_drift_alert_at": None}


def test_calibration_telemetry_stub_shape():
    from infrastructure.api.admin.evidence_routes import _calibration_telemetry
    out = _calibration_telemetry("cyber")
    assert set(out) == {"last_calibration_at", "last_calibration_status", "ece"}


def test_golden_telemetry_stub_shape():
    from infrastructure.api.admin.evidence_routes import _golden_telemetry
    out = _golden_telemetry("cyber", "cyber_general")
    assert set(out) == {"last_golden_check_at", "last_golden_check_status"}


def test_discover_coverage_configs_non_empty():
    from infrastructure.api.admin.evidence_routes import _discover_coverage_configs
    pairs = _discover_coverage_configs()
    assert pairs, "compiler must have at least one compiled coverage"
    coverages = {c for c, _ in pairs}
    assert "cyber" in coverages
    assert all(isinstance(c, str) and isinstance(cfg, str) for c, cfg in pairs)
