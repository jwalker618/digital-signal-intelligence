"""V6/E1 Stage 5.1 — pure-function scoring-spec tests.

Locks in the numerical contract so the Rust port (Stage 5.2+) has a
reference. Tests are deliberately low-level: each asserts a specific
mathematical property of `compute_composite`.
"""
from __future__ import annotations

import math

import pytest

from layers.risk._scoring_spec import (
    COMPOSITE_SCALE,
    DEFAULT_CONFIDENCE,
    DEFAULT_SCORE,
    CompositeResult,
    GroupScore,
    GroupWeight,
    SignalInput,
    compute_composite,
)


# ---------------------------------------------------------------
# Single-signal single-group sanity
# ---------------------------------------------------------------


def test_single_signal_single_group():
    signals = [SignalInput("s1", "g1", raw_score=700.0, weight=1.0, confidence=0.8, populated=True)]
    groups = [GroupWeight("g1", risk_weight=0.5, expected_signal_count=1)]
    res = compute_composite(signals, groups)

    assert res.composite_score == pytest.approx(700.0 * 0.5 * COMPOSITE_SCALE)
    assert len(res.group_scores) == 1
    assert res.group_scores[0].group_score == pytest.approx(700.0)
    assert res.group_scores[0].coverage_ratio == pytest.approx(1.0)
    assert res.signal_coverage == pytest.approx(1.0)
    assert res.overall_confidence == pytest.approx(0.8)


# ---------------------------------------------------------------
# Weighted-average correctness
# ---------------------------------------------------------------


def test_weighted_average_within_group():
    signals = [
        SignalInput("s1", "g1", raw_score=800.0, weight=0.7, confidence=0.9, populated=True),
        SignalInput("s2", "g1", raw_score=600.0, weight=0.3, confidence=0.8, populated=True),
    ]
    groups = [GroupWeight("g1", risk_weight=0.5, expected_signal_count=2)]
    res = compute_composite(signals, groups)

    expected_group_score = (800 * 0.7 + 600 * 0.3) / (0.7 + 0.3)
    assert res.group_scores[0].group_score == pytest.approx(expected_group_score)
    assert res.composite_score == pytest.approx(expected_group_score * 0.5 * COMPOSITE_SCALE)


# ---------------------------------------------------------------
# Multi-group summation
# ---------------------------------------------------------------


def test_multi_group_composite_is_sum_of_contributions():
    signals = [
        SignalInput("s1", "g1", raw_score=700.0, weight=1.0, confidence=0.8, populated=True),
        SignalInput("s2", "g2", raw_score=400.0, weight=1.0, confidence=0.9, populated=True),
    ]
    groups = [
        GroupWeight("g1", risk_weight=0.6, expected_signal_count=1),
        GroupWeight("g2", risk_weight=0.4, expected_signal_count=1),
    ]
    res = compute_composite(signals, groups)

    expected = 700 * 0.6 * COMPOSITE_SCALE + 400 * 0.4 * COMPOSITE_SCALE
    assert res.composite_score == pytest.approx(expected)


# ---------------------------------------------------------------
# Empty group falls back to DEFAULT_SCORE
# ---------------------------------------------------------------


def test_empty_group_uses_default_score():
    signals = [
        SignalInput("s1", "g1", raw_score=700.0, weight=1.0, confidence=0.8, populated=True),
    ]
    groups = [
        GroupWeight("g1", risk_weight=0.6, expected_signal_count=1),
        GroupWeight("g2", risk_weight=0.4, expected_signal_count=3),  # no signals for g2
    ]
    res = compute_composite(signals, groups)

    g2 = next(g for g in res.group_scores if g.group_id == "g2")
    assert g2.group_score == pytest.approx(DEFAULT_SCORE)
    assert g2.signal_count == 0
    assert g2.coverage_ratio == 0.0

    expected = 700 * 0.6 * COMPOSITE_SCALE + DEFAULT_SCORE * 0.4 * COMPOSITE_SCALE
    assert res.composite_score == pytest.approx(expected)


# ---------------------------------------------------------------
# Zero-weight group falls back to DEFAULT_SCORE
# ---------------------------------------------------------------


def test_zero_total_weight_uses_default_score():
    signals = [
        SignalInput("s1", "g1", raw_score=900.0, weight=0.0, confidence=0.9, populated=True),
    ]
    groups = [GroupWeight("g1", risk_weight=0.5, expected_signal_count=1)]
    res = compute_composite(signals, groups)

    assert res.group_scores[0].group_score == pytest.approx(DEFAULT_SCORE)


# ---------------------------------------------------------------
# Coverage and confidence aggregation
# ---------------------------------------------------------------


def test_coverage_counts_populated_only():
    signals = [
        SignalInput("s1", "g1", raw_score=700.0, weight=1.0, confidence=0.8, populated=True),
        SignalInput("s2", "g1", raw_score=500.0, weight=1.0, confidence=0.5, populated=False),
    ]
    groups = [GroupWeight("g1", risk_weight=1.0, expected_signal_count=3)]
    res = compute_composite(signals, groups)

    assert res.signal_coverage == pytest.approx(1 / 3)  # only 1 of 3 populated
    assert res.group_scores[0].coverage_ratio == pytest.approx(1 / 3)


def test_confidence_is_weighted_by_actual_count_over_expected_total():
    signals = [
        SignalInput("s1", "g1", raw_score=500.0, weight=1.0, confidence=0.8, populated=True),
        SignalInput("s2", "g2", raw_score=500.0, weight=1.0, confidence=0.6, populated=True),
    ]
    groups = [
        GroupWeight("g1", risk_weight=0.5, expected_signal_count=1),
        GroupWeight("g2", risk_weight=0.5, expected_signal_count=1),
    ]
    res = compute_composite(signals, groups)

    assert res.overall_confidence == pytest.approx((0.8 * 1 + 0.6 * 1) / 2)


# ---------------------------------------------------------------
# No-expected-signals path falls back to defaults
# ---------------------------------------------------------------


def test_no_expected_signals_yields_default_confidence():
    signals: list[SignalInput] = []
    groups = [GroupWeight("g1", risk_weight=0.5, expected_signal_count=0)]
    res = compute_composite(signals, groups)

    assert res.overall_confidence == pytest.approx(DEFAULT_CONFIDENCE)
    assert res.signal_coverage == 0.0
    # Composite still flows through DEFAULT_SCORE * risk_weight * 10
    assert res.composite_score == pytest.approx(DEFAULT_SCORE * 0.5 * COMPOSITE_SCALE)


# ---------------------------------------------------------------
# Determinism: two calls yield bit-identical results
# ---------------------------------------------------------------


def test_pure_spec_matches_scorer_calculate_composite():
    """Cross-validates the pure spec against the production scorer.

    This is the parity contract the Rust port will also need to honour
    (Stage 5.4). If this test ever fails, one of two things is true:
      1. `_scoring_spec.compute_composite` diverged from `scorer.calculate_composite`.
      2. `scorer.calculate_composite` was intentionally changed — in which case the
         spec + Rust port both need synchronized updates.
    """
    from unittest.mock import MagicMock
    from layers.risk.scorer import ModelScorer
    from layers.risk.types import SignalOutput, utcnow

    # Build one SignalOutput per synthetic fixture
    signal_outputs = [
        SignalOutput(
            signal_id="s1", signal_name="s1", group_id="g1",
            raw_score=800.0, confidence=0.9, weighted_score=800.0 * 0.7,
            weight=0.7, data_sources=[], extracted_at=utcnow(),
            from_cache=False, execution_time_ms=0.0,
        ),
        SignalOutput(
            signal_id="s2", signal_name="s2", group_id="g1",
            raw_score=600.0, confidence=0.8, weighted_score=600.0 * 0.3,
            weight=0.3, data_sources=[], extracted_at=utcnow(),
            from_cache=False, execution_time_ms=0.0,
        ),
        SignalOutput(
            signal_id="s3", signal_name="s3", group_id="g2",
            raw_score=400.0, confidence=0.7, weighted_score=400.0 * 1.0,
            weight=1.0, data_sources=[], extracted_at=utcnow(),
            from_cache=False, execution_time_ms=0.0,
        ),
    ]

    # Fake a minimum config with matching signal_registry + groups
    cfg = MagicMock()
    cfg.signal_registry = [
        MagicMock(three_layer_assessment=MagicMock(group_id="g1")),
        MagicMock(three_layer_assessment=MagicMock(group_id="g1")),
        MagicMock(three_layer_assessment=MagicMock(group_id="g2")),
    ]
    g1 = MagicMock(id="g1", risk=MagicMock(weight=0.6))
    g2 = MagicMock(id="g2", risk=MagicMock(weight=0.4))
    cfg.groups = MagicMock(three_layer_assessment=[g1, g2])

    scorer = ModelScorer(default_score=50.0, default_confidence=0.5)
    composite, group_scores_detail, conf, coverage = scorer.calculate_composite(
        signal_outputs, cfg
    )

    # Call pure spec with same data
    spec_input = [
        SignalInput("s1", "g1", 800.0, 0.7, 0.9, True),
        SignalInput("s2", "g1", 600.0, 0.3, 0.8, True),
        SignalInput("s3", "g2", 400.0, 1.0, 0.7, True),
    ]
    spec_groups = [
        GroupWeight("g1", 0.6, expected_signal_count=2),
        GroupWeight("g2", 0.4, expected_signal_count=1),
    ]
    spec_result = compute_composite(spec_input, spec_groups, default_score=50.0)

    assert spec_result.composite_score == pytest.approx(composite, abs=1e-9)
    assert spec_result.overall_confidence == pytest.approx(conf, abs=1e-9)
    assert spec_result.signal_coverage == pytest.approx(coverage, abs=1e-9)

    for g in spec_result.group_scores:
        scorer_entry = group_scores_detail[g.group_id]
        assert g.risk_contribution == pytest.approx(scorer_entry["risk_contribution"], abs=1e-9)


def test_compute_composite_is_deterministic():
    signals = [
        SignalInput(f"s{i}", f"g{i % 3}", raw_score=float(500 + i),
                    weight=0.1 + 0.01 * i,
                    confidence=0.5 + 0.01 * i,
                    populated=(i % 2 == 0))
        for i in range(25)
    ]
    groups = [
        GroupWeight("g0", 0.4, expected_signal_count=9),
        GroupWeight("g1", 0.4, expected_signal_count=8),
        GroupWeight("g2", 0.2, expected_signal_count=8),
    ]
    r1 = compute_composite(signals, groups)
    r2 = compute_composite(signals, groups)
    assert r1.composite_score == r2.composite_score
    assert r1.overall_confidence == r2.overall_confidence
    assert r1.signal_coverage == r2.signal_coverage
    # bit-identical group-score list
    for a, b in zip(r1.group_scores, r2.group_scores):
        assert a == b
