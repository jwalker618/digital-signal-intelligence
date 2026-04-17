"""V6/D7 — Velocity derivative.

Given a chronologically-ordered series of observations
``[(timestamp, count), ...]`` for a single entity, computes a rolling
90-day delta and a peer-relative velocity score.

Feeds two signals:
- ``hiring_velocity_score`` — entity-specific rolling delta (log-diff).
- ``hiring_velocity_vs_peers`` — z-score against the peer-group cohort.

The drift detector in ``world_engine/drift/detector.py`` raises a
``VelocityDetection`` when an entity's delta exceeds
``SIGMA_THRESHOLD`` (default 2.0 standard deviations).
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Sequence, Tuple


Observation = Tuple[datetime, float]


@dataclass(frozen=True)
class VelocityDetection:
    entity_id: str
    coverage: str
    signal_id: str
    window_days: int
    delta_log: float
    peer_mean: Optional[float]
    peer_sigma: Optional[float]
    z_score: Optional[float]
    severity: str  # 'low' | 'medium' | 'high'


def _log_ratio(before: float, after: float) -> float:
    """log(after / before) with safe epsilons so zero counts don't explode."""
    b = max(before, 1e-6)
    a = max(after, 1e-6)
    return math.log(a / b)


def compute_velocity(
    series: Sequence[Observation],
    *,
    window_days: int = 90,
    reference: Optional[datetime] = None,
) -> float:
    """Return the log-ratio of the mean observation over the last
    ``window_days`` vs. the immediately preceding window.

    Falls back to 0 (no velocity) when either half of the series is empty.
    """
    if not series:
        return 0.0
    reference = reference or max(ts for ts, _ in series)
    boundary_now = reference
    boundary_mid = reference - timedelta(days=window_days)
    boundary_old = reference - timedelta(days=window_days * 2)

    recent = [v for ts, v in series if boundary_mid <= ts <= boundary_now]
    prior = [v for ts, v in series if boundary_old <= ts < boundary_mid]
    if not recent or not prior:
        return 0.0
    return _log_ratio(sum(prior) / len(prior), sum(recent) / len(recent))


class HiringVelocityComputer:
    """Entity-level + cohort-level velocity computer.

    Usage::

        hv = HiringVelocityComputer()
        delta = hv.entity_velocity(entity_id, series)
        z    = hv.peer_zscore(delta, peer_deltas)
    """

    SIGMA_THRESHOLD: float = 2.0

    def entity_velocity(
        self,
        entity_id: str,
        series: Sequence[Observation],
        *,
        window_days: int = 90,
    ) -> float:
        return compute_velocity(series, window_days=window_days)

    def peer_zscore(
        self,
        entity_delta: float,
        peer_deltas: Iterable[float],
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        peers: List[float] = [d for d in peer_deltas if d != 0.0]
        if len(peers) < 3:
            return None, None, None
        mean = statistics.fmean(peers)
        stdev = statistics.pstdev(peers) or 1e-6
        z = (entity_delta - mean) / stdev
        return mean, stdev, z

    def classify(self, z_score: Optional[float]) -> str:
        if z_score is None:
            return "low"
        if abs(z_score) >= 3.0:
            return "high"
        if abs(z_score) >= self.SIGMA_THRESHOLD:
            return "medium"
        return "low"

    def detect(
        self,
        *,
        entity_id: str,
        coverage: str,
        signal_id: str,
        entity_series: Sequence[Observation],
        peer_deltas: Iterable[float],
        window_days: int = 90,
    ) -> VelocityDetection:
        delta = self.entity_velocity(entity_id, entity_series, window_days=window_days)
        mean, sigma, z = self.peer_zscore(delta, peer_deltas)
        return VelocityDetection(
            entity_id=entity_id,
            coverage=coverage,
            signal_id=signal_id,
            window_days=window_days,
            delta_log=delta,
            peer_mean=mean,
            peer_sigma=sigma,
            z_score=z,
            severity=self.classify(z),
        )
