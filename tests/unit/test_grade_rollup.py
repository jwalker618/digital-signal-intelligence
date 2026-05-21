"""V7 Phase 3 — grade rollup + promotion-merge tests."""
from __future__ import annotations

import pytest
import warnings
from datetime import datetime, timezone

from signal_architecture.signals.aggregators.grade_rollup import (
    GradeRollup,
    composite_rollup,
    merge_contributors,
    rollup,
    warn_if_thresholded,
)
from signal_architecture.signals.evidence import EvidenceSource
from signal_architecture.signals.types import SignalResult


def _sr(sid, score=None, grade=None, basis="x", category=None, sources=None, **kw):
    """Compact SignalResult helper."""
    return SignalResult(
        signal_id=sid,
        score=score,
        category=category,
        confidence=kw.pop("confidence", 1.0),
        evidence_grade=grade,
        evidence_basis=basis if grade is not None else None,
        evidence_sources=sources or [],
        **kw,
    )


def _src(sid="s"):
    return EvidenceSource(
        source_id=sid, kind="api",
        ref=f"https://example.com/{sid}",
        fetched_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# merge_contributors
# ---------------------------------------------------------------------------

class TestMergeAgreement:
    def test_two_agree_promote_to_max(self):
        a = _sr("s", score=50.0, grade="observed", sources=[_src("a")])
        b = _sr("s", score=51.0, grade="structured_attested", sources=[_src("b")])  # within 5%
        merged = merge_contributors([a, b])
        assert merged.result.evidence_grade == "structured_attested"
        assert merged.disagreement is False
        assert len(merged.result.evidence_sources) == 2  # union

    def test_three_agree_take_max_grade(self):
        a = _sr("s", score=50.0, grade="inferred")
        b = _sr("s", score=50.5, grade="observed")
        c = _sr("s", score=49.5, grade="corroborated")
        merged = merge_contributors([a, b, c])
        assert merged.result.evidence_grade == "corroborated"
        assert merged.disagreement is False

    def test_categorical_agreement(self):
        a = _sr("s", category="A", grade="observed")
        b = _sr("s", category="A", grade="structured_attested")
        merged = merge_contributors([a, b])
        assert merged.result.evidence_grade == "structured_attested"
        assert merged.result.category == "A"

    def test_order_independent(self):
        a = _sr("s", score=50.0, grade="observed")
        b = _sr("s", score=50.0, grade="structured_attested")
        c = _sr("s", score=50.0, grade="corroborated")
        m1 = merge_contributors([a, b, c])
        m2 = merge_contributors([c, b, a])
        m3 = merge_contributors([b, a, c])
        # Grade and value identical regardless of order
        assert m1.result.evidence_grade == m2.result.evidence_grade == m3.result.evidence_grade
        assert m1.result.score == m2.result.score == m3.result.score


class TestMergeDisagreement:
    def test_score_disagreement_takes_min_grade(self):
        a = _sr("s", score=50.0, grade="observed")
        b = _sr("s", score=90.0, grade="structured_attested")  # > 5% disagreement
        merged = merge_contributors([a, b])
        assert merged.disagreement is True
        assert merged.result.evidence_grade == "observed"  # MIN
        assert merged.result.evidence_counter is not None
        assert merged.result.metadata.get("disagreement") is True

    def test_disagreement_lowers_confidence(self):
        a = _sr("s", score=50.0, grade="observed", confidence=0.9)
        b = _sr("s", score=90.0, grade="structured_attested", confidence=0.7)
        merged = merge_contributors([a, b])
        assert merged.result.confidence == 0.7  # min

    def test_categorical_disagreement_majority_wins(self):
        a = _sr("s", category="A", grade="structured_attested")
        b = _sr("s", category="A", grade="observed")
        c = _sr("s", category="B", grade="corroborated")
        merged = merge_contributors([a, b, c])
        assert merged.disagreement is True
        assert merged.result.category == "A"
        assert merged.result.evidence_grade == "observed"  # min of all three


class TestMergeMixedAndDegenerate:
    def test_single_contributor_passthrough(self):
        a = _sr("s", score=50.0, grade="observed")
        merged = merge_contributors([a])
        assert merged.disagreement is False
        assert merged.result.evidence_grade == "observed"

    def test_ungraded_contributor_ignored(self):
        a = _sr("s", score=50.0, grade=None)  # ungraded
        b = _sr("s", score=50.0, grade="structured_attested")
        merged = merge_contributors([a, b])
        # Only the graded one feeds the merge; result reflects b.
        assert merged.result.evidence_grade == "structured_attested"

    def test_all_ungraded_returns_first(self):
        a = SignalResult(signal_id="s", score=50.0, error="x")
        b = SignalResult(signal_id="s", error="y")
        merged = merge_contributors([a, b])
        assert merged.disagreement is False
        assert merged.result is a  # first contributor returned unchanged

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            merge_contributors([])


# ---------------------------------------------------------------------------
# rollup
# ---------------------------------------------------------------------------

class TestRollup:
    def test_excludes_failed_fetch(self):
        a = _sr("a", score=50, grade="observed")
        b = SignalResult(
            signal_id="b", evidence_grade=None,
            absence_sub_type="absence_failed_fetch",
        )
        r = rollup([(a, 1.0), (b, 1.0)])
        assert r.min_grade == "observed"
        assert "observed" in r.distribution
        assert len(r.distribution) == 1

    def test_includes_authoritative_empty(self):
        a = _sr("a", score=50, grade="observed")
        b = _sr("b", score=100, grade="structured_attested",
                absence_sub_type="absence_authoritative_empty")
        r = rollup([(a, 1.0), (b, 1.0)])
        assert r.min_grade == "observed"
        assert "structured_attested" in r.distribution
        assert pytest.approx(r.distribution["structured_attested"]) == 0.5

    def test_excludes_skipped(self):
        a = _sr("a", score=50, grade="observed")
        b = SignalResult(signal_id="b", skipped=True, evidence_grade="structured_attested")
        r = rollup([(a, 1.0), (b, 1.0)])
        assert "structured_attested" not in r.distribution

    def test_excludes_error(self):
        a = _sr("a", score=50, grade="observed")
        b = SignalResult(signal_id="b", error="x", evidence_grade="structured_attested")
        r = rollup([(a, 1.0), (b, 1.0)])
        assert "structured_attested" not in r.distribution

    def test_min_grade_is_actual_minimum(self):
        a = _sr("a", score=50, grade="structured_attested")
        b = _sr("b", score=50, grade="inferred")
        c = _sr("c", score=50, grade="observed")
        r = rollup([(a, 1.0), (b, 1.0), (c, 1.0)])
        assert r.min_grade == "inferred"

    def test_weighted_mean_is_display_form(self):
        # All at "observed" (rank 1) -> mean = 1.0 + 1.0 = 2.0
        a = _sr("a", score=50, grade="observed")
        b = _sr("b", score=50, grade="observed")
        r = rollup([(a, 0.6), (b, 0.4)])
        assert r.weighted_mean_grade == pytest.approx(2.0)

    def test_distribution_shares_sum_to_one(self):
        a = _sr("a", score=50, grade="observed")
        b = _sr("b", score=50, grade="structured_attested")
        c = _sr("c", score=50, grade="corroborated")
        r = rollup([(a, 0.5), (b, 0.3), (c, 0.2)])
        total = sum(r.distribution.values())
        assert pytest.approx(total) == 1.0

    def test_empty_returns_empty_rollup(self):
        r = rollup([])
        assert r.is_empty()
        assert r.min_grade is None
        assert r.weighted_mean_grade is None
        assert r.distribution == {}


# ---------------------------------------------------------------------------
# composite_rollup
# ---------------------------------------------------------------------------

class TestCompositeRollup:
    def test_non_uniform_group_weights(self):
        a_rollup = rollup([(_sr("a", score=50, grade="observed"), 1.0)])
        b_rollup = rollup([(_sr("b", score=50, grade="structured_attested"), 1.0)])
        c = composite_rollup([(a_rollup, 0.2), (b_rollup, 0.8)])
        assert c.min_grade == "observed"
        # 80% of weight at structured_attested -> bias in mean
        assert c.weighted_mean_grade > 3.5

    def test_skips_empty_groups(self):
        a_rollup = rollup([(_sr("a", score=50, grade="observed"), 1.0)])
        empty = rollup([])
        c = composite_rollup([(a_rollup, 0.5), (empty, 0.5)])
        assert c.min_grade == "observed"

    def test_all_empty_returns_empty(self):
        c = composite_rollup([(rollup([]), 0.5), (rollup([]), 0.5)])
        assert c.is_empty()


# ---------------------------------------------------------------------------
# warn_if_thresholded tripwire
# ---------------------------------------------------------------------------

def test_warn_if_thresholded_emits_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_if_thresholded(2.4, context="test_evaluator")
    assert any("ordinal taxonomy" in str(x.message) for x in caught)
