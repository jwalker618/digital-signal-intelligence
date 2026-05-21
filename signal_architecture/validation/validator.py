"""V7 Phase 6 — adversarial validator: core logic + LLM I/O wrapper.

Public surface:
    compute_advance(mode, axes) -> bool
    grade_after_bump(current, advance, mode, cap) -> EvidenceGrade
    Validator(llm_callable).validate(sig, *, entity_id, ...) -> ValidatorVerdict

The Validator class is the runtime entry point. It picks quick_pass or
full_pass mode based on the signal's grade (and policy floor), constructs
a ValidatorInput, calls the LLM, parses the JSON, computes advance + grade
bump, and returns a ValidatorVerdict.

LLM I/O is abstracted as a Protocol: any callable
    (system: str, user: str) -> str
satisfies the contract. Production wires this to the project's LLM client;
tests pass a deterministic stub.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Optional, Protocol

from signal_architecture.signals.evidence import (
    EVIDENCE_GRADES,
    EvidenceGrade,
    bump_evidence,
    evidence_rank,
)
from signal_architecture.signals.types import SignalResult

from .prompts import (
    FULL_PASS_SYSTEM,
    QUICK_PASS_SYSTEM,
    build_user_message,
)
from .types import (
    AXES_FULL,
    AXES_QUICK,
    Axis,
    AxisResult,
    ValidatorInput,
    ValidatorMode,
    ValidatorVerdict,
)

logger = logging.getLogger("dsi.validator")


class LLMCallable(Protocol):
    """Minimum LLM contract the validator needs.

    Returns the model's raw text response. JSON parsing happens here.
    """

    def __call__(self, *, system: str, user: str) -> str: ...


# ---------------------------------------------------------------------------
# Advance rule (D4) — locked, pure
# ---------------------------------------------------------------------------

def compute_advance(mode: ValidatorMode, axes: dict[str, AxisResult]) -> bool:
    """Decide whether the signal advances given axis results.

    full_pass rule:
        ALL four pass, OR
        MATERIAL + CORRECT_ENTITY pass AND
        OPERATIONALLY_PLAUSIBLE.confidence >= medium AND
        GENERALISES_AT_RENEWAL.confidence >= medium.

    quick_pass rule:
        Both MATERIAL and CORRECT_ENTITY pass.
    """
    if mode == "quick_pass":
        for a in AXES_QUICK:
            r = axes.get(a)
            if r is None or not r.passed:
                return False
        return True

    if mode == "full_pass":
        # All four pass -> advance.
        if all((axes.get(a) and axes[a].passed) for a in AXES_FULL):
            return True
        # Fallback: M+CE pass AND OP+GAR confidence>=medium.
        material = axes.get("MATERIAL")
        correct = axes.get("CORRECT_ENTITY")
        op_p = axes.get("OPERATIONALLY_PLAUSIBLE")
        gen = axes.get("GENERALISES_AT_RENEWAL")
        med_or_above = {"high", "medium"}
        if (
            material and correct and op_p and gen
            and material.passed and correct.passed
            and op_p.confidence in med_or_above
            and gen.confidence in med_or_above
        ):
            return True
    return False


def grade_after_bump(
    current: EvidenceGrade,
    *,
    advance: bool,
    mode: ValidatorMode,
    cap: EvidenceGrade,
) -> EvidenceGrade:
    """Bump current by one rung if advance; never exceed cap; never demote."""
    if not advance:
        return current
    try:
        cur_rank = evidence_rank(current)
        cap_rank = evidence_rank(cap)
    except KeyError:
        return current
    target_rank = min(cur_rank + 1, cap_rank)
    target = EVIDENCE_GRADES[target_rank]
    return bump_evidence(current, target)


# ---------------------------------------------------------------------------
# Validator class
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


class Validator:
    """Wraps an LLMCallable to validate one signal at a time."""

    def __init__(
        self,
        llm: LLMCallable,
        *,
        full_pass_floor: EvidenceGrade = "corroborated",
        advance_bump_cap: EvidenceGrade = "structured_attested",
    ) -> None:
        self.llm = llm
        self.full_pass_floor = full_pass_floor
        self.advance_bump_cap = advance_bump_cap

    def _select_mode(
        self,
        sig: SignalResult,
        *,
        in_policy_expected: bool,
    ) -> ValidatorMode:
        """Quick-pass for low-grade signals not gated by policy; otherwise full-pass."""
        if sig.evidence_grade is None:
            return "quick_pass"
        if in_policy_expected:
            return "full_pass"
        try:
            if evidence_rank(sig.evidence_grade) >= evidence_rank(self.full_pass_floor):
                return "full_pass"
        except KeyError:
            return "quick_pass"
        return "quick_pass"

    def validate(
        self,
        sig: SignalResult,
        *,
        entity_id: str,
        entity_name: str,
        entity_country: Optional[str],
        coverage: str,
        in_policy_expected: bool = False,
    ) -> ValidatorVerdict:
        """Run the validator on one signal. Returns a ValidatorVerdict.

        On LLM failure or unparseable JSON, returns a non-advance verdict
        with tie_breaker describing the failure. Caller is expected to log
        a `validator_failure` compliance event for such verdicts.
        """
        if sig.evidence_grade is None:
            raise ValueError(
                f"Validator cannot run on ungraded signal {sig.signal_id!r}"
            )

        mode = self._select_mode(sig, in_policy_expected=in_policy_expected)
        payload = ValidatorInput.from_signal(
            sig,
            entity_id=entity_id,
            entity_name=entity_name,
            entity_country=entity_country,
            coverage=coverage,
        )
        system = FULL_PASS_SYSTEM if mode == "full_pass" else QUICK_PASS_SYSTEM
        user = build_user_message(payload.model_dump_json())

        start = time.monotonic()
        try:
            raw = self.llm(system=system, user=user) or ""
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "validator LLM call failed for %s: %s", sig.signal_id, e,
            )
            elapsed = time.monotonic() - start
            return self._failure_verdict(
                sig, mode, raw="", reason=f"llm_error: {e}", elapsed=elapsed,
            )
        elapsed = time.monotonic() - start

        parsed = self._parse(raw)
        if parsed is None:
            return self._failure_verdict(
                sig, mode, raw=raw, reason="unparseable_json", elapsed=elapsed,
            )

        axes_obj = self._axes_from_dict(parsed.get("axes", {}), mode)
        if not axes_obj:
            return self._failure_verdict(
                sig, mode, raw=raw, reason="missing_axes", elapsed=elapsed,
            )

        advance = compute_advance(mode, axes_obj)
        new_grade = grade_after_bump(
            sig.evidence_grade,
            advance=advance,
            mode=mode,
            cap=self.advance_bump_cap,
        )

        return ValidatorVerdict(
            signal_id=sig.signal_id,
            mode=mode,
            axes=axes_obj,
            advance=advance,
            grade_after_bump=new_grade,
            pro_argument=str(parsed.get("pro_argument", ""))[:2000],
            counter_argument=str(parsed.get("counter_argument", ""))[:2000],
            tie_breaker=str(parsed.get("tie_breaker", ""))[:2000],
            raw_response=raw[:8000],
            elapsed_seconds=round(elapsed, 3),
        )

    # ------------------------------------------------------------------ #
    # internals                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse(raw: str) -> Optional[dict]:
        if not raw:
            return None
        match = _JSON_BLOCK_RE.search(raw)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _axes_from_dict(d: dict, mode: ValidatorMode) -> dict[Axis, AxisResult]:
        required: tuple[Axis, ...] = AXES_FULL if mode == "full_pass" else AXES_QUICK
        out: dict[Axis, AxisResult] = {}
        for a in required:
            entry = d.get(a)
            if not isinstance(entry, dict):
                return {}
            passed = bool(entry.get("passed"))
            conf_raw = str(entry.get("confidence", "low")).lower()
            confidence = conf_raw if conf_raw in {"high", "medium", "low"} else "low"
            rationale = str(entry.get("rationale", ""))[:500]
            out[a] = AxisResult(
                axis=a, passed=passed, confidence=confidence, rationale=rationale,
            )
        return out

    def _failure_verdict(
        self,
        sig: SignalResult,
        mode: ValidatorMode,
        *,
        raw: str,
        reason: str,
        elapsed: float,
    ) -> ValidatorVerdict:
        """Non-advance verdict for LLM/parse failures. Grade stays as-is."""
        return ValidatorVerdict(
            signal_id=sig.signal_id,
            mode=mode,
            axes={},
            advance=False,
            grade_after_bump=sig.evidence_grade,
            pro_argument="",
            counter_argument="",
            tie_breaker=f"validator failure: {reason}",
            raw_response=raw[:8000],
            elapsed_seconds=round(elapsed, 3),
        )
