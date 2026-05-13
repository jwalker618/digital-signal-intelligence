"""V7 Phase 7 — stratified sampler for human grade review.

Two sources of samples per cycle:

  1. high_weight_referred — every signal with weight>=0.10 in a submission
     where at least one grade-driven referral fired (Phase 4). These get
     priority review because they drove the decision.

  2. stratified_random — 5% of signals with weight>=0.05, stratified by
     (coverage, extractor_grade) so no rung is starved. The remainder
     stays unsampled.

Determinism: the RNG is seeded from sha256(salt + model_version_id), so
re-running the sampler on the same cycle produces identical samples.
Tests rely on this — and the workflow's idempotent-by-(mv, signal_id)
upsert means re-emission is harmless anyway.
"""
from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional


_SALT = "v7_phase7_grade_sampler"
_EXPIRY_DAYS = 90
_HIGH_WEIGHT_FLOOR = 0.10
_STRATIFIED_FLOOR = 0.05
_STRATIFIED_RATE = 0.05


@dataclass(frozen=True)
class SamplingCandidate:
    """All the fields the sampler needs from a committed signal."""
    submission_id: uuid.UUID
    model_version_id: uuid.UUID
    coverage: str
    signal_id: str
    signal_weight: float
    extractor_grade: str
    validator_grade: Optional[str]


@dataclass(frozen=True)
class SamplingTarget:
    """One sample to persist."""
    candidate: SamplingCandidate
    reason: str  # high_weight_referred | stratified_random


def _deterministic_rng(mv_id: uuid.UUID) -> random.Random:
    key = f"{_SALT}:{mv_id}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
    return random.Random(seed)


def select_targets(
    candidates: Iterable[SamplingCandidate],
    *,
    any_referral_fired: bool,
    mv_id: uuid.UUID,
) -> list[SamplingTarget]:
    """Apply both sampling rules and return the union (no duplicates).

    `any_referral_fired` is True when the scorer emitted at least one
    TriggeredCondition with condition_class='evidence_grade' for this
    cycle.
    """
    candidates_list = list(candidates)
    out: list[SamplingTarget] = []
    chosen_ids: set[str] = set()

    # Rule 1: high_weight_referred
    if any_referral_fired:
        for c in candidates_list:
            if c.signal_weight >= _HIGH_WEIGHT_FLOOR:
                out.append(SamplingTarget(c, "high_weight_referred"))
                chosen_ids.add(c.signal_id)

    # Rule 2: stratified_random over (coverage, extractor_grade)
    rng = _deterministic_rng(mv_id)
    buckets: dict[tuple[str, str], list[SamplingCandidate]] = {}
    for c in candidates_list:
        if c.signal_weight < _STRATIFIED_FLOOR:
            continue
        buckets.setdefault((c.coverage, c.extractor_grade), []).append(c)

    # Bucket iteration must be deterministic too.
    for key in sorted(buckets.keys()):
        bucket = buckets[key]
        rng.shuffle(bucket)
        k = max(1, int(round(_STRATIFIED_RATE * len(bucket))))
        for c in bucket[:k]:
            if c.signal_id in chosen_ids:
                continue
            out.append(SamplingTarget(c, "stratified_random"))
            chosen_ids.add(c.signal_id)

    return out


def expiry_for(now: Optional[datetime] = None) -> datetime:
    """Default sample expiry: 90 days from now (UTC)."""
    now = now or datetime.now(timezone.utc)
    return now + timedelta(days=_EXPIRY_DAYS)
