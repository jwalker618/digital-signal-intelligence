"""V7 Phase 6 — locked advance rule (D4) + grade-bump cap."""
from __future__ import annotations

import pytest

from signal_architecture.validation.types import (
    AXES_FULL,
    AxisResult,
)
from signal_architecture.validation.validator import (
    compute_advance,
    grade_after_bump,
)


def _ax(axis, passed, conf="high", rationale="x"):
    return AxisResult(axis=axis, passed=passed, confidence=conf, rationale=rationale)


# ---------------------------------------------------------------------------
# compute_advance
# ---------------------------------------------------------------------------

class TestFullPass:
    def test_all_four_pass_advances(self):
        axes = {a: _ax(a, True) for a in AXES_FULL}
        assert compute_advance("full_pass", axes) is True

    def test_two_pass_two_medium_confidence_advances(self):
        axes = {
            "MATERIAL":                _ax("MATERIAL", True),
            "CORRECT_ENTITY":          _ax("CORRECT_ENTITY", True),
            "OPERATIONALLY_PLAUSIBLE": _ax("OPERATIONALLY_PLAUSIBLE", False, "medium"),
            "GENERALISES_AT_RENEWAL":  _ax("GENERALISES_AT_RENEWAL", False, "medium"),
        }
        assert compute_advance("full_pass", axes) is True

    def test_two_pass_two_low_confidence_does_not_advance(self):
        axes = {
            "MATERIAL":                _ax("MATERIAL", True),
            "CORRECT_ENTITY":          _ax("CORRECT_ENTITY", True),
            "OPERATIONALLY_PLAUSIBLE": _ax("OPERATIONALLY_PLAUSIBLE", False, "low"),
            "GENERALISES_AT_RENEWAL":  _ax("GENERALISES_AT_RENEWAL", False, "low"),
        }
        assert compute_advance("full_pass", axes) is False

    def test_material_fails_does_not_advance(self):
        axes = {a: _ax(a, True) for a in AXES_FULL}
        axes["MATERIAL"] = _ax("MATERIAL", False)
        assert compute_advance("full_pass", axes) is False

    def test_correct_entity_fails_does_not_advance(self):
        axes = {a: _ax(a, True) for a in AXES_FULL}
        axes["CORRECT_ENTITY"] = _ax("CORRECT_ENTITY", False)
        assert compute_advance("full_pass", axes) is False

    def test_one_pass_three_high_confidence_failures_does_not_advance(self):
        axes = {
            "MATERIAL":                _ax("MATERIAL", True),
            "CORRECT_ENTITY":          _ax("CORRECT_ENTITY", False, "high"),
            "OPERATIONALLY_PLAUSIBLE": _ax("OPERATIONALLY_PLAUSIBLE", False, "high"),
            "GENERALISES_AT_RENEWAL":  _ax("GENERALISES_AT_RENEWAL", False, "high"),
        }
        assert compute_advance("full_pass", axes) is False

    def test_missing_axis_does_not_advance(self):
        axes = {a: _ax(a, True) for a in AXES_FULL[:3]}  # one missing
        assert compute_advance("full_pass", axes) is False


class TestQuickPass:
    def test_both_pass_advances(self):
        axes = {
            "MATERIAL": _ax("MATERIAL", True),
            "CORRECT_ENTITY": _ax("CORRECT_ENTITY", True),
        }
        assert compute_advance("quick_pass", axes) is True

    def test_material_fail_does_not_advance(self):
        axes = {
            "MATERIAL": _ax("MATERIAL", False),
            "CORRECT_ENTITY": _ax("CORRECT_ENTITY", True),
        }
        assert compute_advance("quick_pass", axes) is False

    def test_missing_axis_does_not_advance(self):
        axes = {"MATERIAL": _ax("MATERIAL", True)}
        assert compute_advance("quick_pass", axes) is False


# ---------------------------------------------------------------------------
# grade_after_bump
# ---------------------------------------------------------------------------

class TestGradeBump:
    def test_no_advance_no_bump(self):
        assert grade_after_bump(
            "observed", advance=False, mode="full_pass", cap="structured_attested",
        ) == "observed"

    def test_advance_bumps_one_rung(self):
        assert grade_after_bump(
            "observed", advance=True, mode="full_pass", cap="structured_attested",
        ) == "corroborated"

    def test_caps_at_advance_bump_cap(self):
        # Already at cap -> stays at cap
        assert grade_after_bump(
            "structured_attested", advance=True, mode="full_pass", cap="structured_attested",
        ) == "structured_attested"

    def test_quick_pass_capped_at_corroborated(self):
        assert grade_after_bump(
            "observed", advance=True, mode="quick_pass", cap="corroborated",
        ) == "corroborated"

    def test_never_demotes(self):
        # Strange input: cap below current grade. Result should not demote.
        result = grade_after_bump(
            "structured_attested", advance=True, mode="full_pass", cap="observed",
        )
        # bump_evidence guarantees non-demoting; result stays at current grade.
        assert result == "structured_attested"
