"""v8 Phase 4 -- remediation engine."""
from __future__ import annotations

import pytest

from infrastructure.models.config_schema import (
    RemediationEffort,
    SignalRemediation,
)
from layers.risk.impact_breakdown import (
    ImpactBreakdown,
    ImpactClass,
    SignalImpact,
)
from layers.risk.remediation import (
    EFFORT_SCORE,
    RemediationAction,
    RemediationPlan,
    build_remediation_plan,
)


def _drag(
    source_id: str,
    label: str,
    delta_usd: float,
    delta_pct: float = 0.05,
) -> SignalImpact:
    """Build a SignalImpact with classification=DRAG."""
    return SignalImpact(
        signal_key=f"direct_query:{source_id}",
        signal_source="direct_query",
        signal_source_id=source_id,
        signal_label=label,
        classification=ImpactClass.DRAG,
        combined_modifier=1.0 + delta_pct,
        premium_delta_usd=delta_usd,
        premium_delta_pct=delta_pct,
        contributing_modifier_count=1,
    )


def _breakdown(drags: list[SignalImpact]) -> ImpactBreakdown:
    return ImpactBreakdown(
        base_premium=100_000.0,
        final_premium=100_000.0,
        total_modifier=1.0,
        strengths=[],
        drags=drags,
        neutral=[],
    )


def _remediation(effort: RemediationEffort = RemediationEffort.LOW) -> SignalRemediation:
    return SignalRemediation(
        headline="Deploy MFA",
        description="Enable MFA on admin accounts",
        effort=effort,
        typical_duration="2 weeks",
        typical_cost_usd=5000,
        evidence_required="MFA policy screenshot",
        references=[],
    )


class TestEffortScores:
    def test_low_medium_high_ordering(self):
        assert EFFORT_SCORE[RemediationEffort.LOW] < EFFORT_SCORE[RemediationEffort.MEDIUM]
        assert EFFORT_SCORE[RemediationEffort.MEDIUM] < EFFORT_SCORE[RemediationEffort.HIGH]

    def test_low_is_1(self):
        assert EFFORT_SCORE[RemediationEffort.LOW] == 1

    def test_medium_is_3(self):
        assert EFFORT_SCORE[RemediationEffort.MEDIUM] == 3

    def test_high_is_9(self):
        assert EFFORT_SCORE[RemediationEffort.HIGH] == 9


class TestSingleAction:
    def test_authored_drag_produces_real_action(self):
        bd = _breakdown([_drag("mfa_enabled", "MFA", 18_000.0)])
        plan = build_remediation_plan(
            bd, signal_remediation={"mfa_enabled": _remediation()},
        )
        assert len(plan.actions) == 1
        action = plan.actions[0]
        assert action.is_placeholder is False
        assert action.signal_key == "direct_query:mfa_enabled"
        assert action.remediation.headline == "Deploy MFA"

    def test_drag_dollar_delta_is_negated(self):
        # A drag at +18k means remediation SAVES 18k -- delta should be -18k
        bd = _breakdown([_drag("mfa_enabled", "MFA", 18_000.0, delta_pct=0.18)])
        plan = build_remediation_plan(
            bd, signal_remediation={"mfa_enabled": _remediation()},
        )
        assert plan.actions[0].estimated_premium_delta_usd == -18_000.0
        assert plan.actions[0].estimated_premium_delta_pct == -0.18

    def test_leverage_low_effort(self):
        bd = _breakdown([_drag("mfa_enabled", "MFA", 9_000.0)])
        plan = build_remediation_plan(
            bd, signal_remediation={"mfa_enabled": _remediation(RemediationEffort.LOW)},
        )
        # 9000 / 1 = 9000
        assert plan.actions[0].leverage == 9000.0

    def test_leverage_high_effort(self):
        bd = _breakdown([_drag("ir_plan", "IR", 9_000.0)])
        plan = build_remediation_plan(
            bd, signal_remediation={"ir_plan": _remediation(RemediationEffort.HIGH)},
        )
        # 9000 / 9 = 1000
        assert plan.actions[0].leverage == 1000.0


class TestPlaceholder:
    def test_unauthored_drag_gets_placeholder(self):
        bd = _breakdown([_drag("obscure_signal", "Obscure", 5_000.0)])
        plan = build_remediation_plan(bd, signal_remediation={})
        assert plan.placeholder_count == 1
        assert plan.actions[0].is_placeholder is True

    def test_placeholder_uses_signal_label(self):
        bd = _breakdown([_drag("obscure_signal", "Network Centrality", 5_000.0)])
        plan = build_remediation_plan(bd, signal_remediation=None)
        assert "Network Centrality" in plan.actions[0].remediation.headline

    def test_mixed_authored_and_placeholder(self):
        bd = _breakdown([
            _drag("mfa_enabled", "MFA", 10_000.0),
            _drag("unknown_signal", "Unknown", 5_000.0),
        ])
        plan = build_remediation_plan(
            bd, signal_remediation={"mfa_enabled": _remediation()},
        )
        assert plan.placeholder_count == 1
        assert len(plan.actions) == 2
        authored = [a for a in plan.actions if not a.is_placeholder]
        placeholders = [a for a in plan.actions if a.is_placeholder]
        assert len(authored) == 1
        assert len(placeholders) == 1

    def test_signal_remediation_none_treats_all_as_placeholders(self):
        bd = _breakdown([_drag("a", "A", 10_000.0), _drag("b", "B", 5_000.0)])
        plan = build_remediation_plan(bd, signal_remediation=None)
        assert plan.placeholder_count == 2
        assert all(a.is_placeholder for a in plan.actions)


class TestSortOrder:
    def test_sort_by_leverage_desc(self):
        # Three actions, all LOW effort, different dollar impacts
        bd = _breakdown([
            _drag("small", "S", 3_000.0),
            _drag("big", "B", 15_000.0),
            _drag("medium", "M", 8_000.0),
        ])
        plan = build_remediation_plan(
            bd,
            signal_remediation={
                "small": _remediation(),
                "big": _remediation(),
                "medium": _remediation(),
            },
        )
        ids = [a.signal_key.split(":")[1] for a in plan.actions]
        assert ids == ["big", "medium", "small"]

    def test_effort_changes_leverage_ranking(self):
        # 9k LOW (leverage 9000) should beat 15k HIGH (leverage ~1666)
        bd = _breakdown([
            _drag("low_action", "L", 9_000.0),
            _drag("high_action", "H", 15_000.0),
        ])
        plan = build_remediation_plan(
            bd,
            signal_remediation={
                "low_action": _remediation(RemediationEffort.LOW),
                "high_action": _remediation(RemediationEffort.HIGH),
            },
        )
        assert plan.actions[0].signal_key.endswith("low_action")

    def test_tie_break_authored_before_placeholder(self):
        # Two drags with same dollar impact; one authored, one placeholder.
        # Both LOW effort by default (placeholder is MEDIUM). To get a real
        # tie we need a placeholder also at LOW. Force same effort via the
        # leverage tie: authored MEDIUM (5000/3=1666) vs placeholder MEDIUM
        # (5000/3=1666). Authored wins.
        bd = _breakdown([
            _drag("authored", "Authored", 5_000.0),
            _drag("placeholder", "Placeholder", 5_000.0),
        ])
        plan = build_remediation_plan(
            bd,
            signal_remediation={
                "authored": _remediation(RemediationEffort.MEDIUM),
            },
        )
        # Same leverage; authored should come first
        assert plan.actions[0].signal_key.endswith("authored")
        assert plan.actions[1].signal_key.endswith("placeholder")


class TestEmptyBreakdown:
    def test_no_drags_produces_empty_plan(self):
        bd = _breakdown([])
        plan = build_remediation_plan(bd, signal_remediation={})
        assert plan.actions == []
        assert plan.placeholder_count == 0


class TestPydanticShape:
    def test_remediation_action_serializable(self):
        bd = _breakdown([_drag("mfa_enabled", "MFA", 10_000.0)])
        plan = build_remediation_plan(
            bd, signal_remediation={"mfa_enabled": _remediation()},
        )
        # Should serialize without error
        dump = plan.model_dump()
        assert "actions" in dump
        assert dump["actions"][0]["signal_key"] == "direct_query:mfa_enabled"
