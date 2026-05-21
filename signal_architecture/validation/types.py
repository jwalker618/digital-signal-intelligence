"""V7 Phase 6 — adversarial-validator types.

The validator runs INDEPENDENTLY of the extractor: it sees only the
asserted payload, never the LLM's reasoning or transcript. The Pydantic
`ValidatorInput` model enforces this at the input boundary — `extra=
"forbid"` rejects any field the schema doesn't whitelist, so a stray
`raw_data`, `metadata`, or `reasoning` field can't sneak in.

Four evaluation axes (full_pass):
    MATERIAL                — does this signal change price/tier at all?
    CORRECT_ENTITY          — is the data unambiguously about this entity?
    OPERATIONALLY_PLAUSIBLE — is the state consistent with what we know?
    GENERALISES_AT_RENEWAL  — would re-extraction in 12 months agree?

Two-axis quick-pass (MATERIAL + CORRECT_ENTITY only) is used for low-grade
signals or signals not gated by the per-coverage policy floor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from signal_architecture.signals.evidence import EvidenceGrade

Axis = Literal[
    "MATERIAL",
    "CORRECT_ENTITY",
    "OPERATIONALLY_PLAUSIBLE",
    "GENERALISES_AT_RENEWAL",
]

AXES_FULL: tuple[Axis, ...] = (
    "MATERIAL",
    "CORRECT_ENTITY",
    "OPERATIONALLY_PLAUSIBLE",
    "GENERALISES_AT_RENEWAL",
)
AXES_QUICK: tuple[Axis, ...] = ("MATERIAL", "CORRECT_ENTITY")

ValidatorMode = Literal["quick_pass", "full_pass"]
ConfidenceLevel = Literal["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Input contract — stripped of reasoning/transcripts/raw_data/metadata
# ---------------------------------------------------------------------------

class ValidatorInput(BaseModel):
    """The only payload the validator LLM ever sees.

    `model_config["extra"] = "forbid"` enforces the contract: any caller
    that tries to pass `raw_data`, `metadata`, `reasoning`, or any other
    out-of-schema key gets a hard ValidationError before the prompt is
    built. The `from_signal()` classmethod is the canonical constructor.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float
    evidence_grade: EvidenceGrade
    evidence_basis: str
    evidence_sources: list[dict] = Field(default_factory=list)
    absence_sub_type: Optional[str] = None

    entity_id: str
    entity_name: str
    entity_country: Optional[str] = None
    coverage: str

    @classmethod
    def from_signal(
        cls,
        sig,  # SignalResult
        *,
        entity_id: str,
        entity_name: str,
        entity_country: Optional[str],
        coverage: str,
    ) -> "ValidatorInput":
        """Canonical constructor. Strips every disallowed field."""
        return cls(
            signal_id=sig.signal_id,
            score=sig.score,
            category=sig.category,
            confidence=sig.confidence,
            evidence_grade=sig.evidence_grade,
            evidence_basis=sig.evidence_basis or "",
            evidence_sources=[s.to_dict() for s in (sig.evidence_sources or [])],
            absence_sub_type=sig.absence_sub_type,
            entity_id=entity_id,
            entity_name=entity_name,
            entity_country=entity_country,
            coverage=coverage,
        )


# ---------------------------------------------------------------------------
# Output types — what the validator produces
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AxisResult:
    """One axis verdict."""
    axis: Axis
    passed: bool
    confidence: ConfidenceLevel
    rationale: str  # ≤500 chars


@dataclass(frozen=True)
class ValidatorVerdict:
    """Complete validator output for one signal."""
    signal_id: str
    mode: ValidatorMode
    axes: dict[Axis, AxisResult]
    advance: bool
    grade_after_bump: Optional[EvidenceGrade]
    pro_argument: str
    counter_argument: str
    tie_breaker: str
    raw_response: str
    elapsed_seconds: float
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
