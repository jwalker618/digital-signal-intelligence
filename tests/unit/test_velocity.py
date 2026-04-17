"""V6/D7 — velocity derivative tests."""
from __future__ import annotations

from datetime import datetime, timedelta

from world_engine.derivatives.velocity import (
    HiringVelocityComputer,
    VelocityDetection,
    compute_velocity,
)


def _series(base: datetime, days_back: int, value: float):
    return (base - timedelta(days=days_back), value)


def test_zero_series_returns_zero_velocity():
    assert compute_velocity([]) == 0.0


def test_half_empty_series_returns_zero():
    now = datetime(2026, 4, 1)
    s = [_series(now, 10, 5.0), _series(now, 30, 5.0)]
    # All entries in the recent half → no prior window data.
    assert compute_velocity(s, window_days=90, reference=now) == 0.0


def test_growth_returns_positive_log():
    now = datetime(2026, 4, 1)
    # Prior window (90-180d ago) averaged 10; recent 90d averaged 20.
    s = [
        _series(now, 150, 10.0),
        _series(now, 120, 10.0),
        _series(now, 30, 20.0),
        _series(now, 10, 20.0),
    ]
    delta = compute_velocity(s, window_days=90, reference=now)
    assert delta > 0
    # log(20/10) = ~0.693
    assert 0.6 < delta < 0.8


def test_contraction_returns_negative_log():
    now = datetime(2026, 4, 1)
    s = [
        _series(now, 150, 100.0),
        _series(now, 120, 100.0),
        _series(now, 30, 50.0),
        _series(now, 10, 50.0),
    ]
    delta = compute_velocity(s, window_days=90, reference=now)
    assert delta < 0


def test_peer_zscore_flat_deltas_return_low_severity():
    hv = HiringVelocityComputer()
    _, _, z = hv.peer_zscore(0.1, [0.09, 0.1, 0.11, 0.1])
    assert z is not None and abs(z) < 1.0
    assert hv.classify(z) == "low"


def test_peer_zscore_high_severity():
    hv = HiringVelocityComputer()
    _, _, z = hv.peer_zscore(5.0, [0.1, 0.1, 0.1, 0.1, 0.1])
    # 5 std deviations above peers → high
    assert hv.classify(z) == "high"


def test_peer_zscore_insufficient_peers_returns_none():
    hv = HiringVelocityComputer()
    mean, sigma, z = hv.peer_zscore(0.5, [0.1])  # only 1 peer
    assert mean is None and sigma is None and z is None


def test_detect_returns_populated_detection():
    now = datetime(2026, 4, 1)
    hv = HiringVelocityComputer()
    entity_series = [
        _series(now, 150, 10.0),
        _series(now, 10, 25.0),
    ]
    detection = hv.detect(
        entity_id="acme",
        coverage="cyber",
        signal_id="hiring_velocity",
        entity_series=entity_series,
        peer_deltas=[0.02, 0.05, 0.03, 0.04],
    )
    assert isinstance(detection, VelocityDetection)
    assert detection.entity_id == "acme"
    assert detection.signal_id == "hiring_velocity"
    assert detection.delta_log > 0
    assert detection.severity in {"low", "medium", "high"}
