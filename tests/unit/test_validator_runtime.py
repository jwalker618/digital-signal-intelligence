"""V7 Phase 6 — Validator.validate() end-to-end with a stub LLM."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from signal_architecture.signals.types import SignalResult
from signal_architecture.validation.validator import Validator


def _sig(grade="corroborated", score=72.0):
    return SignalResult(
        signal_id="sanctions_check",
        score=score,
        confidence=0.85,
        evidence_grade=grade,
        evidence_basis="Multi-source agreement",
    )


def _full_pass_response_all_pass():
    return json.dumps({
        "axes": {
            "MATERIAL":                {"passed": True, "confidence": "high", "rationale": "weight high"},
            "CORRECT_ENTITY":          {"passed": True, "confidence": "high", "rationale": "ID match"},
            "OPERATIONALLY_PLAUSIBLE": {"passed": True, "confidence": "high", "rationale": "consistent"},
            "GENERALISES_AT_RENEWAL":  {"passed": True, "confidence": "high", "rationale": "stable register"},
        },
        "pro_argument": "Authoritative register + corroborating feed.",
        "counter_argument": "Possible jurisdictional gap.",
        "tie_breaker": "OFAC SDN refresh window <24h.",
    })


def _full_pass_response_fail_material():
    return json.dumps({
        "axes": {
            "MATERIAL":                {"passed": False, "confidence": "high", "rationale": "weight too small"},
            "CORRECT_ENTITY":          {"passed": True, "confidence": "high", "rationale": "ID match"},
            "OPERATIONALLY_PLAUSIBLE": {"passed": True, "confidence": "high", "rationale": "consistent"},
            "GENERALISES_AT_RENEWAL":  {"passed": True, "confidence": "high", "rationale": "stable"},
        },
        "pro_argument": "x",
        "counter_argument": "x",
        "tie_breaker": "x",
    })


def _quick_pass_response_both_pass():
    return json.dumps({
        "axes": {
            "MATERIAL":       {"passed": True, "confidence": "medium", "rationale": "weight modest"},
            "CORRECT_ENTITY": {"passed": True, "confidence": "high", "rationale": "ID match"},
        },
        "pro_argument": "ok",
        "counter_argument": "ok",
        "tie_breaker": "ok",
    })


class TestModeSelection:
    def test_grade_below_floor_uses_quick_pass(self):
        llm = MagicMock(return_value=_quick_pass_response_both_pass())
        v = Validator(llm, full_pass_floor="corroborated")
        verdict = v.validate(
            _sig(grade="observed"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.mode == "quick_pass"

    def test_grade_at_floor_uses_full_pass(self):
        llm = MagicMock(return_value=_full_pass_response_all_pass())
        v = Validator(llm, full_pass_floor="corroborated")
        verdict = v.validate(
            _sig(grade="corroborated"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.mode == "full_pass"

    def test_in_policy_expected_forces_full_pass(self):
        llm = MagicMock(return_value=_full_pass_response_all_pass())
        v = Validator(llm, full_pass_floor="corroborated")
        verdict = v.validate(
            _sig(grade="inferred"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
            in_policy_expected=True,
        )
        assert verdict.mode == "full_pass"


class TestVerdictPropagation:
    def test_all_pass_advances_and_bumps(self):
        llm = MagicMock(return_value=_full_pass_response_all_pass())
        v = Validator(llm, advance_bump_cap="structured_attested")
        verdict = v.validate(
            _sig(grade="corroborated"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is True
        assert verdict.grade_after_bump == "structured_attested"
        assert verdict.pro_argument
        assert verdict.tie_breaker

    def test_fail_does_not_bump(self):
        llm = MagicMock(return_value=_full_pass_response_fail_material())
        v = Validator(llm)
        verdict = v.validate(
            _sig(grade="corroborated"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is False
        assert verdict.grade_after_bump == "corroborated"

    def test_bump_caps_at_advance_bump_cap(self):
        llm = MagicMock(return_value=_full_pass_response_all_pass())
        v = Validator(llm, advance_bump_cap="structured_attested")
        verdict = v.validate(
            _sig(grade="structured_attested"), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is True
        # Already at cap -> stays at cap
        assert verdict.grade_after_bump == "structured_attested"


class TestFailureModes:
    def test_llm_exception_returns_non_advance_failure_verdict(self):
        def boom(*, system, user):
            raise RuntimeError("network down")

        v = Validator(boom)
        verdict = v.validate(
            _sig(), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is False
        assert "validator failure" in verdict.tie_breaker
        assert "llm_error" in verdict.tie_breaker
        # Grade preserved
        assert verdict.grade_after_bump == "corroborated"
        # No axes recorded
        assert verdict.axes == {}

    def test_unparseable_json_returns_failure(self):
        llm = MagicMock(return_value="this is not JSON")
        v = Validator(llm)
        verdict = v.validate(
            _sig(), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is False
        assert "unparseable_json" in verdict.tie_breaker

    def test_missing_axes_returns_failure(self):
        llm = MagicMock(return_value=json.dumps({"axes": {}, "pro_argument": "", "counter_argument": "", "tie_breaker": ""}))
        v = Validator(llm)
        verdict = v.validate(
            _sig(), entity_id="e", entity_name="E",
            entity_country=None, coverage="cyber",
        )
        assert verdict.advance is False
        assert "missing_axes" in verdict.tie_breaker

    def test_ungraded_signal_rejected_at_runtime(self):
        sig = SignalResult(signal_id="x", score=50.0, confidence=1.0)  # no grade
        v = Validator(lambda **_: "")
        with pytest.raises(ValueError):
            v.validate(sig, entity_id="e", entity_name="E",
                       entity_country=None, coverage="cyber")
