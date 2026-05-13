"""V7 Phase 4 — evidence_grade_policy Pydantic schema validation tests."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from infrastructure.models.config_schema import (
    CompositeReferral,
    DistributionShareBelowGradeRule,
    EvidenceGradePolicy,
    ExpectedGradeMap,
    HighWeightSignalBelowExpectedRule,
    MinGradeBelowRule,
)


class TestDefaultPolicy:
    def test_default_constructs_enabled_with_empty_rules(self):
        p = EvidenceGradePolicy()
        assert p.enabled is True
        assert p.composite_referral.enabled is True
        assert p.composite_referral.rules == []
        assert p.expected_grades.grades == {}


class TestMinGradeBelowRule:
    def test_accepts_valid_grade(self):
        r = MinGradeBelowRule(condition="min_grade_below", threshold="observed")
        assert r.threshold == "observed"

    def test_rejects_unknown_grade(self):
        with pytest.raises(ValidationError):
            MinGradeBelowRule(condition="min_grade_below", threshold="badgrade")  # type: ignore[arg-type]

    def test_threshold_required(self):
        with pytest.raises(ValidationError):
            MinGradeBelowRule.model_validate({"condition": "min_grade_below"})


class TestDistributionShareBelowGradeRule:
    def test_accepts_share_in_range(self):
        r = DistributionShareBelowGradeRule(
            condition="distribution_share_below_grade",
            floor="observed",
            share=0.5,
        )
        assert r.share == 0.5

    def test_rejects_share_above_one(self):
        with pytest.raises(ValidationError):
            DistributionShareBelowGradeRule(
                condition="distribution_share_below_grade",
                floor="observed",
                share=1.5,
            )

    def test_rejects_share_below_zero(self):
        with pytest.raises(ValidationError):
            DistributionShareBelowGradeRule(
                condition="distribution_share_below_grade",
                floor="observed",
                share=-0.1,
            )

    def test_rejects_unknown_floor(self):
        with pytest.raises(ValidationError):
            DistributionShareBelowGradeRule(
                condition="distribution_share_below_grade",
                floor="weak",  # type: ignore[arg-type]
                share=0.5,
            )


class TestHighWeightSignalBelowExpectedRule:
    def test_accepts_weight_threshold(self):
        r = HighWeightSignalBelowExpectedRule(
            condition="high_weight_signal_below_expected",
            weight_threshold=0.10,
        )
        assert r.weight_threshold == 0.10

    def test_rejects_weight_threshold_zero(self):
        with pytest.raises(ValidationError):
            HighWeightSignalBelowExpectedRule(
                condition="high_weight_signal_below_expected",
                weight_threshold=0.0,
            )

    def test_rejects_weight_threshold_above_one(self):
        with pytest.raises(ValidationError):
            HighWeightSignalBelowExpectedRule(
                condition="high_weight_signal_below_expected",
                weight_threshold=1.5,
            )


class TestExpectedGradeMap:
    def test_accepts_known_grades(self):
        m = ExpectedGradeMap(grades={
            "sanctions_screening_result": "structured_attested",
            "litigation_history": "corroborated",
        })
        assert m.grades["sanctions_screening_result"] == "structured_attested"

    def test_rejects_unknown_grades(self):
        with pytest.raises(ValidationError):
            ExpectedGradeMap(grades={"sig": "magic"})  # type: ignore[dict-item]


class TestCompositeReferral:
    def test_accepts_mixed_rule_types(self):
        cr = CompositeReferral(rules=[
            DistributionShareBelowGradeRule(
                condition="distribution_share_below_grade",
                floor="observed", share=0.5,
            ),
            MinGradeBelowRule(condition="min_grade_below", threshold="observed"),
        ])
        assert len(cr.rules) == 2


class TestPolicyAttachedToConfig:
    def test_default_factory_keeps_existing_configs_valid(self):
        """Loading a real config should produce a default policy (empty rules)."""
        from infrastructure.models.compiler import get_config
        cfg = get_config("aerospace", "aerospace_general")
        p = cfg.evidence_grade_policy
        assert p.enabled is True
        # Phase 4's rollout injected the permissive default rule
        assert len(p.composite_referral.rules) == 1
        assert p.composite_referral.rules[0].condition == "distribution_share_below_grade"
