"""V7 Phase 7 — sampler determinism, stratification, weight floor."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from signal_architecture.validation.sampler import (
    SamplingCandidate,
    expiry_for,
    select_targets,
)


def _c(sid, *, weight=0.2, coverage="cyber", grade="observed"):
    return SamplingCandidate(
        submission_id=uuid.UUID(int=1),
        model_version_id=uuid.UUID(int=2),
        coverage=coverage,
        signal_id=sid,
        signal_weight=weight,
        extractor_grade=grade,
        validator_grade=None,
    )


_MV = uuid.UUID(int=42)


class TestHighWeightReferred:
    def test_picks_high_weight_when_referred(self):
        candidates = [
            _c("a", weight=0.20),
            _c("b", weight=0.05),  # below high-weight floor
        ]
        out = select_targets(candidates, any_referral_fired=True, mv_id=_MV)
        signal_ids = {t.candidate.signal_id for t in out}
        # 'a' must be picked under high_weight_referred; 'b' too small.
        a_targets = [t for t in out if t.candidate.signal_id == "a"]
        assert len(a_targets) == 1
        assert a_targets[0].reason == "high_weight_referred"

    def test_skips_high_weight_when_no_referral_fired(self):
        candidates = [_c("a", weight=0.30)]
        out = select_targets(candidates, any_referral_fired=False, mv_id=_MV)
        # Stratified sampling still picks it (single bucket, k>=1)
        for t in out:
            assert t.reason == "stratified_random"


class TestStratifiedSampling:
    def test_stratified_pick_per_bucket(self):
        # Two distinct buckets; with stratification each gets at least 1.
        candidates = [
            _c(f"cyber_a_{i}", coverage="cyber", grade="observed", weight=0.10)
            for i in range(5)
        ] + [
            _c(f"do_x_{i}", coverage="do", grade="structured_attested", weight=0.10)
            for i in range(5)
        ]
        out = select_targets(candidates, any_referral_fired=False, mv_id=_MV)
        coverages = {t.candidate.coverage for t in out}
        assert coverages == {"cyber", "do"}

    def test_excludes_below_stratified_floor(self):
        candidates = [
            _c("a", weight=0.01),  # below 0.05 floor
            _c("b", weight=0.05),
            _c("c", weight=0.10),
        ]
        out = select_targets(candidates, any_referral_fired=False, mv_id=_MV)
        signal_ids = {t.candidate.signal_id for t in out}
        assert "a" not in signal_ids


class TestDeterminism:
    def test_same_mv_same_targets(self):
        candidates = [
            _c(f"s{i}", weight=0.10, grade="observed", coverage="cyber")
            for i in range(20)
        ]
        a = select_targets(candidates, any_referral_fired=False, mv_id=_MV)
        b = select_targets(candidates, any_referral_fired=False, mv_id=_MV)
        a_ids = sorted(t.candidate.signal_id for t in a)
        b_ids = sorted(t.candidate.signal_id for t in b)
        assert a_ids == b_ids

    def test_different_mv_different_targets(self):
        candidates = [
            _c(f"s{i}", weight=0.10, grade="observed", coverage="cyber")
            for i in range(40)
        ]
        a = select_targets(candidates, any_referral_fired=False, mv_id=uuid.UUID(int=1))
        b = select_targets(candidates, any_referral_fired=False, mv_id=uuid.UUID(int=2))
        a_ids = sorted(t.candidate.signal_id for t in a)
        b_ids = sorted(t.candidate.signal_id for t in b)
        # Different seed -> shuffle order differs; with 40 candidates and ~5%
        # rate the picks are statistically very likely to differ.
        assert a_ids != b_ids


class TestNoDuplicate:
    def test_signal_appears_at_most_once(self):
        # The same signal qualifies for both rules; should only be sampled once.
        candidates = [_c("s", weight=0.30, grade="observed", coverage="cyber")]
        out = select_targets(candidates, any_referral_fired=True, mv_id=_MV)
        ids = [t.candidate.signal_id for t in out]
        assert ids.count("s") == 1
        # high_weight_referred wins over stratified_random
        assert out[0].reason == "high_weight_referred"


class TestExpiry:
    def test_default_90_days(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        e = expiry_for(now=now)
        assert e == now + timedelta(days=90)
