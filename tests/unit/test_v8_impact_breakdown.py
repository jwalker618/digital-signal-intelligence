"""v8 Phase 3 -- signal impact breakdown."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from layers.risk.impact_breakdown import (
    DEADBAND_LOWER,
    DEADBAND_UPPER,
    NEUTRAL_MAX_ENTRIES,
    ImpactBreakdown,
    ImpactClass,
    SignalImpact,
    compute_from_model_version,
    compute_impact_breakdown,
)


def _mod(source: str, source_id: str, factor: float, before: float, name: str = "") -> dict:
    """Build a JSONB-shaped modifier dict."""
    return {
        "source": source,
        "source_id": source_id,
        "name": name or f"{source_id} modifier",
        "factor": factor,
        "premium_before": before,
        "premium_after": before * factor,
    }


@dataclass
class _FakeAppliedModifier:
    """Mirrors layers.risk.types.AppliedModifier attribute shape."""
    source: str
    source_id: str
    name: str
    factor: float
    premium_before: float
    premium_after: float


class TestClassification:
    def test_strength_below_deadband(self):
        bd = compute_impact_breakdown(
            [_mod("direct_query", "mfa_enabled", 0.92, 100_000)],
            base_premium=100_000,
            final_premium=92_000,
        )
        assert len(bd.strengths) == 1
        assert bd.strengths[0].classification == ImpactClass.STRENGTH
        assert bd.drags == []
        assert bd.neutral == []

    def test_drag_above_deadband(self):
        bd = compute_impact_breakdown(
            [_mod("direct_query", "no_mfa", 1.18, 100_000)],
            base_premium=100_000,
            final_premium=118_000,
        )
        assert len(bd.drags) == 1
        assert bd.drags[0].classification == ImpactClass.DRAG
        assert bd.strengths == []

    def test_neutral_within_deadband(self):
        bd = compute_impact_breakdown(
            [_mod("categorical", "minor_thing", 1.01, 100_000)],
            base_premium=100_000,
            final_premium=101_000,
        )
        assert len(bd.neutral) == 1
        assert bd.neutral[0].classification == ImpactClass.NEUTRAL

    def test_deadband_boundary_lower_is_strength(self):
        # 0.9799... < 0.98 -> strength
        bd = compute_impact_breakdown(
            [_mod("x", "y", 0.97, 100_000)],
            base_premium=100_000, final_premium=97_000,
        )
        assert bd.strengths[0].classification == ImpactClass.STRENGTH

    def test_exactly_at_deadband_lower_is_neutral(self):
        # 0.98 is inclusive in NEUTRAL
        bd = compute_impact_breakdown(
            [_mod("x", "y", DEADBAND_LOWER, 100_000)],
            base_premium=100_000, final_premium=98_000,
        )
        assert bd.neutral[0].classification == ImpactClass.NEUTRAL

    def test_exactly_at_deadband_upper_is_neutral(self):
        bd = compute_impact_breakdown(
            [_mod("x", "y", DEADBAND_UPPER, 100_000)],
            base_premium=100_000, final_premium=102_000,
        )
        assert bd.neutral[0].classification == ImpactClass.NEUTRAL


class TestGrouping:
    def test_modifiers_with_same_source_id_collapse(self):
        mods = [
            _mod("direct_query", "mfa_enabled", 0.95, 100_000),  # 100k -> 95k
            _mod("direct_query", "mfa_enabled", 0.97, 95_000),    # 95k -> 92.15k
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=92_150)
        assert len(bd.strengths) == 1
        s = bd.strengths[0]
        assert s.contributing_modifier_count == 2
        # combined modifier is the product
        assert s.combined_modifier == pytest.approx(0.9215, abs=1e-4)

    def test_different_source_ids_stay_separate(self):
        mods = [
            _mod("direct_query", "mfa_enabled", 0.95, 100_000),
            _mod("direct_query", "security_training", 1.08, 95_000),
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=102_600)
        assert len(bd.strengths) == 1
        assert len(bd.drags) == 1
        assert bd.strengths[0].signal_source_id == "mfa_enabled"
        assert bd.drags[0].signal_source_id == "security_training"

    def test_same_source_id_different_source_stay_separate(self):
        # source distinguishes categorical "mfa" from direct_query "mfa"
        mods = [
            _mod("categorical", "mfa", 0.95, 100_000),
            _mod("direct_query", "mfa", 0.95, 95_000),
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=90_250)
        assert len(bd.strengths) == 2
        keys = {s.signal_key for s in bd.strengths}
        assert "categorical:mfa" in keys
        assert "direct_query:mfa" in keys


class TestSorting:
    def test_strengths_sorted_by_absolute_dollar_desc(self):
        mods = [
            _mod("direct_query", "small_reduction", 0.97, 100_000),   # -3k delta
            _mod("direct_query", "big_reduction", 0.85, 100_000),     # -15k delta
            _mod("direct_query", "medium_reduction", 0.92, 100_000),  # -8k delta
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=74_000)
        ids = [s.signal_source_id for s in bd.strengths]
        assert ids == ["big_reduction", "medium_reduction", "small_reduction"]

    def test_drags_sorted_by_absolute_dollar_desc(self):
        mods = [
            _mod("direct_query", "small_drag", 1.03, 100_000),
            _mod("direct_query", "big_drag", 1.20, 100_000),
            _mod("direct_query", "medium_drag", 1.10, 100_000),
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=136_000)
        ids = [s.signal_source_id for s in bd.drags]
        assert ids == ["big_drag", "medium_drag", "small_drag"]


class TestNeutralTruncation:
    def test_neutral_truncated(self):
        # Build NEUTRAL_MAX_ENTRIES + 5 neutral modifiers
        mods = [
            _mod("categorical", f"neutral_{i}", 1.005, 100_000)
            for i in range(NEUTRAL_MAX_ENTRIES + 5)
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=100_000)
        assert len(bd.neutral) == NEUTRAL_MAX_ENTRIES


class TestDualInputShape:
    """The function accepts both AppliedModifier objects and JSONB dicts."""

    def test_dataclass_input(self):
        m = _FakeAppliedModifier(
            source="direct_query",
            source_id="mfa_enabled",
            name="MFA",
            factor=0.92,
            premium_before=100_000,
            premium_after=92_000,
        )
        bd = compute_impact_breakdown([m], base_premium=100_000, final_premium=92_000)
        assert bd.strengths[0].signal_label == "MFA"

    def test_mixed_input(self):
        mods = [
            _FakeAppliedModifier(
                source="direct_query", source_id="mfa", name="MFA",
                factor=0.95, premium_before=100_000, premium_after=95_000,
            ),
            _mod("categorical", "industry", 1.05, 95_000, name="Industry: Tech"),
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=99_750)
        assert len(bd.strengths) == 1
        assert len(bd.drags) == 1


class TestMalformedInputs:
    def test_modifier_missing_source_skipped(self):
        bd = compute_impact_breakdown(
            [
                {"source": "", "source_id": "x", "factor": 0.9,
                 "premium_before": 100, "premium_after": 90, "name": ""},
                _mod("direct_query", "valid", 0.95, 100_000),
            ],
            base_premium=100_000, final_premium=95_000,
        )
        assert len(bd.strengths) == 1
        assert bd.strengths[0].signal_source_id == "valid"

    def test_modifier_missing_source_id_skipped(self):
        bd = compute_impact_breakdown(
            [
                {"source": "categorical", "source_id": None, "factor": 0.9,
                 "premium_before": 100, "premium_after": 90, "name": ""},
                _mod("direct_query", "valid", 0.95, 100_000),
            ],
            base_premium=100_000, final_premium=95_000,
        )
        assert len(bd.strengths) == 1

    def test_empty_modifiers(self):
        bd = compute_impact_breakdown([], base_premium=100_000, final_premium=100_000)
        assert bd.strengths == []
        assert bd.drags == []
        assert bd.neutral == []
        assert bd.total_modifier == 1.0


class TestTotalModifier:
    def test_total_modifier_computed(self):
        bd = compute_impact_breakdown(
            [_mod("direct_query", "mfa", 0.9, 100_000)],
            base_premium=100_000, final_premium=90_000,
        )
        assert bd.total_modifier == 0.9

    def test_zero_base_premium_returns_neutral_total(self):
        bd = compute_impact_breakdown(
            [], base_premium=0.0, final_premium=0.0,
        )
        assert bd.total_modifier == 1.0


class TestComputeFromModelVersion:
    def test_works_with_object_attrs(self):
        class _MV:
            modifiers_applied = [
                _FakeAppliedModifier(
                    source="direct_query", source_id="mfa", name="MFA",
                    factor=0.92, premium_before=100_000, premium_after=92_000,
                )
            ]
            base_premium = 100_000.0
            final_premium = 92_000.0
            premium_after_modifiers = 92_000.0

        bd = compute_from_model_version(_MV())
        assert isinstance(bd, ImpactBreakdown)
        assert len(bd.strengths) == 1

    def test_handles_missing_attrs_gracefully(self):
        class _Empty:
            pass

        bd = compute_from_model_version(_Empty())
        assert bd.base_premium == 0.0
        assert bd.final_premium == 0.0
        assert bd.strengths == []


class TestSignalImpactShape:
    def test_signal_key_format(self):
        bd = compute_impact_breakdown(
            [_mod("direct_query", "mfa_enabled", 0.92, 100_000)],
            base_premium=100_000, final_premium=92_000,
        )
        assert bd.strengths[0].signal_key == "direct_query:mfa_enabled"

    def test_label_uses_first_modifier_name(self):
        bd = compute_impact_breakdown(
            [_mod("direct_query", "mfa", 0.95, 100_000, name="MFA Deployed")],
            base_premium=100_000, final_premium=95_000,
        )
        assert bd.strengths[0].signal_label == "MFA Deployed"

    def test_premium_delta_sign(self):
        # Strength has NEGATIVE delta (reduction); drag has POSITIVE
        mods = [
            _mod("direct_query", "s", 0.90, 100_000),
            _mod("direct_query", "d", 1.10, 90_000),
        ]
        bd = compute_impact_breakdown(mods, base_premium=100_000, final_premium=99_000)
        assert bd.strengths[0].premium_delta_usd < 0
        assert bd.drags[0].premium_delta_usd > 0
