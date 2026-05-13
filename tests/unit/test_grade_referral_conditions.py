"""V7 Phase 4 — evaluator tests for evidence-grade-policy referral conditions."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from infrastructure.models.config_schema import (
    CompositeReferral,
    DistributionShareBelowGradeRule,
    EvidenceGradePolicy,
    ExpectedGradeMap,
    HighWeightSignalBelowExpectedRule,
    MinGradeBelowRule,
)
from layers.risk.scorer import ModelScorer
from layers.risk.types import ConditionAction, SignalOutput


class _StubConfig:
    """Minimal config carrying just the evidence_grade_policy attribute."""

    def __init__(self, policy: EvidenceGradePolicy):
        self.evidence_grade_policy = policy


def _so(sid, grade, weight=1.0, score=50.0):
    return SignalOutput(
        signal_id=sid,
        signal_name=sid,
        group_id="g",
        raw_score=score,
        confidence=1.0,
        weighted_score=score * weight,
        weight=weight,
        evidence_grade=grade,
        evidence_basis="x" if grade else None,
    )


@pytest.fixture
def scorer():
    return ModelScorer()


class TestDefaultPermissive:
    def test_default_policy_no_referrals_when_majority_at_observed(self, scorer):
        # 100% at observed -> default rule (>=50% at observed) is satisfied.
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[DistributionShareBelowGradeRule(
                    condition="distribution_share_below_grade",
                    floor="observed", share=0.5,
                )],
            ),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("a", "observed"), _so("b", "structured_attested")],
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 0.5, "structured_attested": 0.5},
            config=cfg,
        )
        assert out == []

    def test_empty_distribution_skipped(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[DistributionShareBelowGradeRule(
                    condition="distribution_share_below_grade",
                    floor="observed", share=0.5,
                )],
            ),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[],
            composite_min_grade=None,
            composite_grade_distribution={},
            config=cfg,
        )
        assert out == []


class TestDistributionShareBelowGrade:
    def test_fires_when_share_below_threshold(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[DistributionShareBelowGradeRule(
                    condition="distribution_share_below_grade",
                    floor="corroborated", share=0.5,
                )],
            ),
        ))
        # 40% at corroborated+ -> fires (< 50%)
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[],
            composite_min_grade="inferred",
            composite_grade_distribution={"inferred": 0.6, "corroborated": 0.4},
            config=cfg,
        )
        assert len(out) == 1
        cond = out[0]
        assert cond.action == ConditionAction.REFER
        assert cond.condition_class == "evidence_grade"

    def test_no_fire_when_at_threshold(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[DistributionShareBelowGradeRule(
                    condition="distribution_share_below_grade",
                    floor="corroborated", share=0.5,
                )],
            ),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[],
            composite_min_grade="corroborated",
            composite_grade_distribution={"inferred": 0.5, "corroborated": 0.5},
            config=cfg,
        )
        assert out == []


class TestMinGradeBelow:
    def test_fires_when_composite_min_below_threshold(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[MinGradeBelowRule(condition="min_grade_below", threshold="observed")],
            ),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[],
            composite_min_grade="inferred",
            composite_grade_distribution={"inferred": 1.0},
            config=cfg,
        )
        assert len(out) == 1
        assert out[0].condition_class == "evidence_grade"

    def test_no_fire_when_at_threshold(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            composite_referral=CompositeReferral(
                rules=[MinGradeBelowRule(condition="min_grade_below", threshold="observed")],
            ),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[],
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 1.0},
            config=cfg,
        )
        assert out == []


class TestHighWeightSignalBelowExpected:
    def test_fires_when_high_weight_signal_below_expected(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            expected_grades=ExpectedGradeMap(grades={"sanctions": "structured_attested"}),
            composite_referral=CompositeReferral(
                rules=[HighWeightSignalBelowExpectedRule(
                    condition="high_weight_signal_below_expected",
                    weight_threshold=0.10,
                )],
            ),
        ))
        # Total weight = 1.0; sanctions weight=0.2 -> share=0.2 >= 0.10
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("sanctions", "observed", weight=0.2),
                            _so("other", "structured_attested", weight=0.8)],
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 0.2, "structured_attested": 0.8},
            config=cfg,
        )
        assert len(out) >= 1
        # The per-signal expected_grades violation ALSO fires; both should be evidence_grade.
        for tc in out:
            assert tc.condition_class == "evidence_grade"
            assert tc.action == ConditionAction.REFER

    def test_no_fire_when_signal_below_weight_threshold(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            expected_grades=ExpectedGradeMap(grades={"sanctions": "structured_attested"}),
            composite_referral=CompositeReferral(
                rules=[HighWeightSignalBelowExpectedRule(
                    condition="high_weight_signal_below_expected",
                    weight_threshold=0.50,
                )],
            ),
        ))
        # sanctions weight 0.1 < 0.50 -> rule skips; but per-signal expected violation still fires
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("sanctions", "observed", weight=0.1),
                            _so("other", "structured_attested", weight=0.9)],
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 0.1, "structured_attested": 0.9},
            config=cfg,
        )
        # Only per-signal expected_grades violation fires (1 condition), not the high-weight rule.
        assert len(out) == 1
        assert "below expected" in out[0].note


class TestPerSignalExpectedGrades:
    def test_fires_when_actual_below_expected(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            expected_grades=ExpectedGradeMap(grades={"sig_a": "structured_attested"}),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("sig_a", "observed")],
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 1.0},
            config=cfg,
        )
        assert len(out) == 1
        assert out[0].source_id == "sig_a"

    def test_no_fire_when_signal_meets_expected(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            expected_grades=ExpectedGradeMap(grades={"sig_a": "observed"}),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("sig_a", "structured_attested")],
            composite_min_grade="structured_attested",
            composite_grade_distribution={"structured_attested": 1.0},
            config=cfg,
        )
        assert out == []


class TestActionDiscipline:
    def test_all_grade_referrals_are_REFER_not_tier_override(self, scorer):
        cfg = _StubConfig(EvidenceGradePolicy(
            expected_grades=ExpectedGradeMap(grades={"sig_a": "structured_attested"}),
            composite_referral=CompositeReferral(rules=[
                MinGradeBelowRule(condition="min_grade_below", threshold="observed"),
                DistributionShareBelowGradeRule(
                    condition="distribution_share_below_grade",
                    floor="corroborated", share=0.5,
                ),
                HighWeightSignalBelowExpectedRule(
                    condition="high_weight_signal_below_expected",
                    weight_threshold=0.10,
                ),
            ]),
        ))
        out = scorer._evaluate_evidence_grade_policy(
            signal_outputs=[_so("sig_a", "inferred", weight=0.5)],
            composite_min_grade="inferred",
            composite_grade_distribution={"inferred": 1.0},
            config=cfg,
        )
        # Every grade-driven condition is REFER with class="evidence_grade".
        assert len(out) > 0
        for tc in out:
            assert tc.action == ConditionAction.REFER
            assert tc.condition_class == "evidence_grade"


class TestNoScalarMeanCompareInProduction:
    """CI-style tripwire: no production code compares composite_weighted_mean_grade."""

    def test_no_threshold_compare_against_weighted_mean(self):
        import subprocess
        result = subprocess.run(
            [
                "grep", "-rnE",
                r"weighted_mean_grade *([<>!]=?|==)",
                "layers/", "infrastructure/", "signal_architecture/",
                "--include=*.py",
            ],
            capture_output=True, text=True,
        )
        # grep exit 1 = no matches (good); 0 = matches (bad)
        assert result.returncode == 1, (
            f"Found scalar-mean threshold compare(s):\n{result.stdout}"
        )
