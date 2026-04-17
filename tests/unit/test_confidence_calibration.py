"""V6/E3 — confidence calibration harness tests."""
from __future__ import annotations

import json
from pathlib import Path

from infrastructure.validation.confidence_calibration import (
    CalibrationHarness,
    CalibrationSample,
    _brier,
    _ece,
)


def test_brier_perfect_calibration():
    # confidence = 1.0 when outcome = True, 0.0 otherwise → Brier = 0.
    assert _brier([1.0, 0.0, 1.0], [True, False, True]) == 0.0


def test_brier_fully_miscalibrated():
    # Flipped confidences → max Brier.
    b = _brier([0.0, 1.0], [True, False])
    assert b == 1.0


def test_ece_single_bin_matches():
    # All samples in one bin, mean confidence == observed fraction → ECE 0.
    ece, curve = _ece([0.5, 0.5, 0.5, 0.5], [True, False, True, False])
    assert ece == 0.0
    assert len(curve) == 1


def test_ece_flags_overconfidence():
    # All claim 0.9 but only 50% succeed.
    ece, _ = _ece([0.9, 0.9, 0.9, 0.9], [True, True, False, False])
    assert abs(ece - 0.4) < 1e-9


def test_harness_groups_by_coverage():
    h = CalibrationHarness()
    h.record(CalibrationSample("s1", "cyber", "cyber_general", 0.8, True))
    h.record(CalibrationSample("s1", "cyber", "cyber_general", 0.8, False))
    h.record(CalibrationSample("s1", "pi",    "pi_general",    0.5, True))

    report = h.build_report()
    assert set(report.brier_by_coverage) == {"cyber", "pi"}
    # Cyber brier: mean of (0.8-1)^2 + (0.8-0)^2 = (0.04 + 0.64)/2 = 0.34
    assert abs(report.brier_by_coverage["cyber"] - 0.34) < 1e-9
    # PI brier: (0.5-1)^2 = 0.25
    assert abs(report.brier_by_coverage["pi"] - 0.25) < 1e-9


def test_report_json_round_trip(tmp_path: Path):
    h = CalibrationHarness()
    h.record(CalibrationSample("s1", "cyber", "cyber_general", 0.8, True))
    report = h.build_report()
    out = tmp_path / "cal.json"
    report.write_json(out)
    data = json.loads(out.read_text())
    assert data["sample_count"] == 1
    assert "cyber" in data["brier_by_coverage"]


def test_miscalibrated_flagged_at_ece_threshold():
    h = CalibrationHarness()
    # 4 samples all predicting 0.95 confidence; only 1/4 succeeds → ECE 0.7 > 0.1.
    for avail in (True, False, False, False):
        h.record(CalibrationSample("s1", "cyber", "cyber_general", 0.95, avail))
    report = h.build_report()
    assert "cyber" in report.to_dict()["miscalibrated_coverages"]
