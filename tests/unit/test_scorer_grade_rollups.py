"""V7 Phase 3 — scorer integration: per-group + composite grade rollups."""
from __future__ import annotations

import pytest

from layers.risk.scorer import ModelScorer
from layers.risk.types import GroupGradeRollup, ScoringResult, SignalOutput


def _so(sid, group, score=50.0, weight=0.5, grade=None, basis="x", sub=None, error=None):
    return SignalOutput(
        signal_id=sid,
        signal_name=sid,
        group_id=group,
        raw_score=score,
        confidence=1.0,
        weighted_score=score * weight,
        weight=weight,
        evidence_grade=grade,
        evidence_basis=basis if grade is not None else None,
        absence_sub_type=sub,
        error=error,
    )


class TestBuildGradeRollups:
    def test_single_group_single_grade(self):
        scorer = ModelScorer()
        outs = [
            _so("a", "g1", grade="observed"),
            _so("b", "g1", grade="observed"),
        ]
        group_scores = {"g1": {"risk_weight": 1.0}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        assert "g1" in groups
        assert groups["g1"].min_grade == "observed"
        assert composite.min_grade == "observed"
        assert composite.distribution == {"observed": 1.0}

    def test_two_groups_different_min_grades(self):
        scorer = ModelScorer()
        outs = [
            _so("a", "g1", grade="structured_attested", weight=1.0),
            _so("b", "g2", grade="inferred", weight=1.0),
        ]
        group_scores = {"g1": {"risk_weight": 0.6}, "g2": {"risk_weight": 0.4}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        assert groups["g1"].min_grade == "structured_attested"
        assert groups["g2"].min_grade == "inferred"
        # Composite min is the global min across all rungs present in dist
        assert composite.min_grade == "inferred"
        # Distribution honours group weights
        assert composite.distribution["structured_attested"] == pytest.approx(0.6)
        assert composite.distribution["inferred"] == pytest.approx(0.4)

    def test_failed_fetch_excluded(self):
        scorer = ModelScorer()
        outs = [
            _so("a", "g1", grade="observed"),
            _so("b", "g1", grade=None, sub="absence_failed_fetch"),
        ]
        group_scores = {"g1": {"risk_weight": 1.0}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        assert groups["g1"].distribution == {"observed": 1.0}
        assert composite.min_grade == "observed"

    def test_authoritative_empty_included_at_its_grade(self):
        scorer = ModelScorer()
        outs = [
            _so("a", "g1", grade="observed"),
            _so("b", "g1", grade="structured_attested",
                sub="absence_authoritative_empty"),
        ]
        group_scores = {"g1": {"risk_weight": 1.0}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        # Authoritative empty contributes its grade to the distribution
        assert "structured_attested" in groups["g1"].distribution
        assert composite.min_grade == "observed"

    def test_error_signal_excluded(self):
        scorer = ModelScorer()
        outs = [
            _so("a", "g1", grade="observed"),
            _so("b", "g1", grade="structured_attested", error="boom"),
        ]
        group_scores = {"g1": {"risk_weight": 1.0}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        assert "structured_attested" not in groups["g1"].distribution

    def test_empty_signal_outputs_returns_empty_composite(self):
        scorer = ModelScorer()
        groups, composite = scorer._build_grade_rollups([], {})
        assert groups == {}
        assert composite.is_empty()

    def test_composite_grade_distribution_populated_on_scoring_result(self):
        """ScoringResult dataclass has the V7 fields and they're populated."""
        scorer = ModelScorer()
        outs = [_so("a", "g1", grade="observed")]
        group_scores = {"g1": {"risk_weight": 1.0}}
        groups, composite = scorer._build_grade_rollups(outs, group_scores)
        sr = ScoringResult(
            composite_min_grade=composite.min_grade,
            composite_weighted_mean_grade=composite.weighted_mean_grade,
            composite_grade_distribution=dict(composite.distribution),
            group_grade_rollups=groups,
        )
        assert sr.composite_min_grade == "observed"
        assert isinstance(sr.group_grade_rollups["g1"], GroupGradeRollup)
