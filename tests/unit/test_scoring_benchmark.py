"""V6/E1 Stage 5.5 — Rust scoring p99 benchmark.

Asserts that the Rust `compute_composite` meets the V6 production
target of p99 < 5 ms per call on a realistic fixture (25 signals × 5
groups — the typical A-series coverage composite).

Rust vs Python speed-up is also reported. The test is skipped when
the Rust extension is not installed.
"""
from __future__ import annotations

import random
import time

import pytest

from layers.risk._scoring_spec import (
    GroupWeight as PyGroupWeight,
    SignalInput as PySignalInput,
    compute_composite as py_compute,
)


try:
    from dsi_core import scoring as rs  # type: ignore[import-not-found]
    RUST_AVAILABLE = True
except ImportError:  # pragma: no cover
    RUST_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not RUST_AVAILABLE,
    reason="Rust dsi_core extension not installed",
)


# Target: p99 < 5 ms per call for a 25-signal × 5-group realistic fixture.
P99_TARGET_MS = 5.0
N_SAMPLES = 2_000


def _realistic_fixture(seed: int = 0):
    rng = random.Random(seed)
    groups = [
        PyGroupWeight(f"g{i}", risk_weight=[0.4, 0.3, 0.15, 0.1, 0.05][i],
                      expected_signal_count=5)
        for i in range(5)
    ]
    signals = []
    for i in range(25):
        signals.append(PySignalInput(
            f"s{i}",
            group_id=f"g{i % 5}",
            raw_score=rng.uniform(300.0, 900.0),
            weight=rng.uniform(0.05, 0.3),
            confidence=rng.uniform(0.5, 0.95),
            populated=True,
        ))
    return signals, groups


def _to_rs(signals, groups):
    return (
        [rs.SignalInput(s.signal_id, s.group_id, s.raw_score, s.weight, s.confidence, s.populated) for s in signals],
        [rs.GroupWeight(g.group_id, g.risk_weight, g.expected_signal_count) for g in groups],
    )


def _p99(samples_ns: list[int]) -> float:
    sorted_ns = sorted(samples_ns)
    idx = int(0.99 * len(sorted_ns))
    return sorted_ns[idx] / 1e6  # → ms


def test_rust_compute_composite_p99_under_5ms():
    signals, groups = _realistic_fixture()
    rs_signals, rs_groups = _to_rs(signals, groups)

    # Warm up
    for _ in range(50):
        rs.compute_composite(rs_signals, rs_groups)

    samples = []
    for _ in range(N_SAMPLES):
        t0 = time.perf_counter_ns()
        rs.compute_composite(rs_signals, rs_groups)
        samples.append(time.perf_counter_ns() - t0)

    p99_ms = _p99(samples)
    mean_ms = sum(samples) / len(samples) / 1e6
    print(f"\n  rust compute_composite: mean={mean_ms:.3f} ms, p99={p99_ms:.3f} ms")
    assert p99_ms < P99_TARGET_MS, (
        f"Rust p99 {p99_ms:.3f} ms exceeds {P99_TARGET_MS} ms target"
    )


def test_rust_is_faster_than_python():
    """Report Rust-vs-Python speed-up — assert at least 2x for the
    realistic-fixture workload."""
    signals, groups = _realistic_fixture()
    rs_signals, rs_groups = _to_rs(signals, groups)

    # Warm up both
    for _ in range(50):
        rs.compute_composite(rs_signals, rs_groups)
        py_compute(signals, groups)

    N = 500  # smaller count for Python — it's the slower leg
    rs_samples = []
    for _ in range(N):
        t0 = time.perf_counter_ns()
        rs.compute_composite(rs_signals, rs_groups)
        rs_samples.append(time.perf_counter_ns() - t0)

    py_samples = []
    for _ in range(N):
        t0 = time.perf_counter_ns()
        py_compute(signals, groups)
        py_samples.append(time.perf_counter_ns() - t0)

    rs_mean_us = sum(rs_samples) / N / 1e3
    py_mean_us = sum(py_samples) / N / 1e3
    speedup = py_mean_us / rs_mean_us
    print(
        f"\n  py mean={py_mean_us:.2f} µs, rs mean={rs_mean_us:.2f} µs, "
        f"speedup={speedup:.1f}x"
    )
    assert speedup >= 2.0, f"Expected ≥2x Rust speedup, got {speedup:.1f}x"
