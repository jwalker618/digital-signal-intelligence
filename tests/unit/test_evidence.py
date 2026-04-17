"""V6/E8 — evidence-dashboard snapshot tests."""
from __future__ import annotations

from datetime import datetime, timezone

from infrastructure.admin.evidence import (
    EvidenceSnapshot,
    build_evidence_snapshot,
    compute_real_signal_pct,
)


def test_real_signal_pct_zero_when_no_signals():
    assert compute_real_signal_pct(0, 0) == (0.0, 0.0)


def test_real_signal_pct_capped_and_rounded():
    real, stub = compute_real_signal_pct(production_signals=62, total_signals=100)
    assert real == 0.62
    assert stub == 0.38


def test_real_signal_pct_handles_overrun():
    real, stub = compute_real_signal_pct(production_signals=150, total_signals=100)
    assert real == 1.0 and stub == 0.0


def test_snapshot_empty_cover_list():
    snap = build_evidence_snapshot(coverage_configs=[])
    assert isinstance(snap, EvidenceSnapshot)
    assert snap.coverages == []


def test_snapshot_assembles_from_callables():
    def ex(cov, cfg):
        return {
            "production_signals": 30,
            "total_signals": 40,
            "avg_confidence_p50": 0.78,
            "avg_confidence_p95": 0.95,
            "monthly_extractor_cost_usd": 4120.50,
            "active_quote_count_30d": 1284,
            "referral_rate_30d": 0.14,
        }

    def cal(cov):
        return {
            "last_calibration_at": "2026-04-15T09:00:00Z",
            "last_calibration_status": "PASS",
            "ece": 0.04,
        }

    def gold(cov, cfg):
        return {
            "last_golden_check_at": "2026-04-16T02:00:00Z",
            "last_golden_check_status": "PASS",
        }

    def drift(cov, cfg):
        return {"last_drift_alert_at": "2026-04-12T22:30:00Z"}

    snap = build_evidence_snapshot(
        coverage_configs=[("cyber", "cyber_general"), ("fi", "fi_bank")],
        extractor_telemetry=ex,
        calibration_telemetry=cal,
        golden_telemetry=gold,
        drift_telemetry=drift,
        reference_time=datetime(2026, 4, 17, tzinfo=timezone.utc),
    )
    assert len(snap.coverages) == 2
    cyber = snap.coverages[0]
    assert cyber.coverage == "cyber"
    assert cyber.real_signal_pct == 0.75
    assert cyber.stub_signal_pct == 0.25
    assert cyber.last_calibration_status == "PASS"
    assert cyber.monthly_extractor_cost_usd == 4120.50
    assert cyber.ece == 0.04


def test_snapshot_handles_missing_telemetry_callables():
    snap = build_evidence_snapshot(coverage_configs=[("cyber", "cyber_general")])
    cov = snap.coverages[0]
    assert cov.coverage == "cyber"
    assert cov.real_signal_pct == 0.0
    assert cov.last_calibration_status is None
    assert cov.monthly_extractor_cost_usd is None
