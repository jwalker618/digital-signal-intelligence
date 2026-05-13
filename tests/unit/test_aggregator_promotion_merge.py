"""V7 Phase 3 — BaseAggregator.merge_contributing_signals + aggregate_evidence."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import List

from signal_architecture.signals.base import BaseAggregator
from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.types import (
    AggregatorResult,
    ExtractorResult,
    SignalResult,
)


class _StubAgg(BaseAggregator):
    """Concrete subclass so we can instantiate."""
    def aggregate(
        self,
        extractor_results: List[ExtractorResult],
        **kwargs,
    ) -> AggregatorResult:
        raise NotImplementedError


def _src(sid):
    return EvidenceSource(
        source_id=sid, kind="api",
        ref=f"https://example.com/{sid}",
        fetched_at=datetime.now(timezone.utc),
    )


def _sig(grade=None, score=50.0, sources=None, **kw):
    return SignalResult(
        signal_id=kw.pop("sid", "x"),
        score=score,
        confidence=1.0,
        evidence_grade=grade,
        evidence_basis="x" if grade else None,
        evidence_sources=sources or [],
        **kw,
    )


class TestAggregateEvidence:
    def test_returns_max_grade_and_union_of_sources(self):
        agg = _StubAgg()
        s1 = _sig(grade="observed", sources=[_src("a")])
        s2 = _sig(grade="structured_attested", sources=[_src("b")])
        grade, srcs = agg.aggregate_evidence([s1, s2])
        assert grade == "structured_attested"
        ids = {s.source_id for s in srcs}
        assert ids == {"a", "b"}

    def test_skips_failed_fetch(self):
        agg = _StubAgg()
        s1 = _sig(grade="observed", sources=[_src("a")])
        s2 = SignalResult(
            signal_id="x", evidence_grade="structured_attested",
            evidence_basis="x", absence_sub_type="absence_failed_fetch",
        )
        grade, srcs = agg.aggregate_evidence([s1, s2])
        assert grade == "observed"
        assert len(srcs) == 1

    def test_skips_error(self):
        agg = _StubAgg()
        s1 = _sig(grade="observed")
        s2 = SignalResult(
            signal_id="x", evidence_grade="structured_attested",
            evidence_basis="x", error="boom",
        )
        grade, _ = agg.aggregate_evidence([s1, s2])
        assert grade == "observed"

    def test_empty_returns_none(self):
        agg = _StubAgg()
        assert agg.aggregate_evidence([]) == (None, [])


class TestMergeContributingSignals:
    def test_delegates_to_promotion_merge(self):
        agg = _StubAgg()
        s1 = _sig(sid="z", grade="observed", score=50.0)
        s2 = _sig(sid="z", grade="structured_attested", score=51.0)  # within 5%
        merged = agg.merge_contributing_signals("z", [s1, s2])
        assert merged.signal_id == "z"
        assert merged.evidence_grade == "structured_attested"  # promoted

    def test_disagreement_takes_min(self):
        agg = _StubAgg()
        s1 = _sig(sid="z", grade="observed", score=50.0)
        s2 = _sig(sid="z", grade="structured_attested", score=90.0)
        merged = agg.merge_contributing_signals("z", [s1, s2])
        assert merged.evidence_grade == "observed"
        assert merged.evidence_counter is not None

    def test_signal_id_mismatch_raises(self):
        agg = _StubAgg()
        s1 = _sig(sid="a", grade="observed")
        with pytest.raises(ValueError):
            agg.merge_contributing_signals("b", [s1])

    def test_empty_raises(self):
        agg = _StubAgg()
        with pytest.raises(ValueError):
            agg.merge_contributing_signals("z", [])
