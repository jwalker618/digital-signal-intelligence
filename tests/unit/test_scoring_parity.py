"""V6/E1 Stage 5.4 — Rust vs Python scoring parity.

Drives `dsi_core.scoring.compute_composite` (Rust via PyO3) and
`layers.risk._scoring_spec.compute_composite` (Python reference) on
the same inputs and asserts bit-level agreement to 1e-9 absolute.

The Rust extension is optional; tests are skipped if the wheel is
not installed. CI (Stage 5.4) will install it via `maturin build`
before running this test.
"""
from __future__ import annotations

import random

import pytest

from layers.risk._scoring_spec import (
    GroupWeight as PyGroupWeight,
    SignalInput as PySignalInput,
    compute_composite as py_compute,
)

pytest_plugins = []

try:
    from dsi_core import scoring as rs  # type: ignore[import-not-found]
    RUST_AVAILABLE = True
except ImportError:  # pragma: no cover — exercised when the wheel isn't built
    RUST_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not RUST_AVAILABLE,
    reason="Rust dsi_core extension not installed; run `maturin build --release` first.",
)


# ------------------------------------------------------------------ helpers


def _mirror_py_to_rs(signals, groups):
    rs_signals = [
        rs.SignalInput(s.signal_id, s.group_id, s.raw_score, s.weight, s.confidence, s.populated)
        for s in signals
    ]
    rs_groups = [
        rs.GroupWeight(g.group_id, g.risk_weight, g.expected_signal_count) for g in groups
    ]
    return rs_signals, rs_groups


def _assert_parity(py_res, rs_res, tol: float = 1e-9):
    assert abs(py_res.composite_score - rs_res.composite_score) < tol, (
        f"composite mismatch: py={py_res.composite_score} rs={rs_res.composite_score}"
    )
    assert abs(py_res.overall_confidence - rs_res.overall_confidence) < tol
    assert abs(py_res.signal_coverage - rs_res.signal_coverage) < tol
    assert len(py_res.group_scores) == len(rs_res.group_scores)
    for pg, rg in zip(py_res.group_scores, rs_res.group_scores):
        assert pg.group_id == rg.group_id
        assert abs(pg.group_score - rg.group_score) < tol
        assert abs(pg.risk_contribution - rg.risk_contribution) < tol
        assert pg.signal_count == rg.signal_count
        assert pg.expected_signal_count == rg.expected_signal_count
        assert abs(pg.coverage_ratio - rg.coverage_ratio) < tol


# ------------------------------------------------------------------ tests


def test_parity_single_signal_single_group():
    signals = [PySignalInput("s1", "g1", 700.0, 1.0, 0.8, True)]
    groups = [PyGroupWeight("g1", risk_weight=0.5, expected_signal_count=1)]
    _assert_parity(py_compute(signals, groups), rs.compute_composite(*_mirror_py_to_rs(signals, groups)))


def test_parity_weighted_average_within_group():
    signals = [
        PySignalInput("s1", "g1", 800.0, 0.7, 0.9, True),
        PySignalInput("s2", "g1", 600.0, 0.3, 0.8, True),
    ]
    groups = [PyGroupWeight("g1", risk_weight=0.5, expected_signal_count=2)]
    _assert_parity(py_compute(signals, groups), rs.compute_composite(*_mirror_py_to_rs(signals, groups)))


def test_parity_empty_group_uses_default():
    signals = [PySignalInput("s1", "g1", 700.0, 1.0, 0.8, True)]
    groups = [
        PyGroupWeight("g1", 0.6, expected_signal_count=1),
        PyGroupWeight("g2", 0.4, expected_signal_count=3),
    ]
    _assert_parity(py_compute(signals, groups), rs.compute_composite(*_mirror_py_to_rs(signals, groups)))


def test_parity_zero_total_weight_group():
    signals = [PySignalInput("s1", "g1", 900.0, 0.0, 0.9, True)]
    groups = [PyGroupWeight("g1", 0.5, expected_signal_count=1)]
    _assert_parity(py_compute(signals, groups), rs.compute_composite(*_mirror_py_to_rs(signals, groups)))


def test_parity_no_expected_signals():
    signals: list[PySignalInput] = []
    groups = [PyGroupWeight("g1", 0.5, expected_signal_count=0)]
    _assert_parity(py_compute(signals, groups), rs.compute_composite(*_mirror_py_to_rs(signals, groups)))


@pytest.mark.parametrize("seed", list(range(50)))
def test_parity_randomized_fixtures(seed):
    """50 randomized fixtures — the closest in-process analogue to the
    1,000-fixture nightly parity job described in the V6 spec."""
    rng = random.Random(seed)
    num_groups = rng.randint(1, 6)
    groups_py = []
    for i in range(num_groups):
        groups_py.append(PyGroupWeight(
            f"g{i}",
            risk_weight=rng.uniform(0.0, 0.5),
            expected_signal_count=rng.randint(0, 10),
        ))
    group_ids = [g.group_id for g in groups_py]
    num_signals = rng.randint(0, 30)
    signals_py = []
    for i in range(num_signals):
        signals_py.append(PySignalInput(
            f"s{i}",
            group_id=rng.choice(group_ids),
            raw_score=rng.uniform(0.0, 1000.0),
            weight=rng.uniform(0.0, 1.0),
            confidence=rng.uniform(0.0, 1.0),
            populated=rng.random() < 0.7,
        ))
    _assert_parity(
        py_compute(signals_py, groups_py),
        rs.compute_composite(*_mirror_py_to_rs(signals_py, groups_py)),
    )
