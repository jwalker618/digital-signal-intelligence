"""V7 Phase 14 — evidence-related Pydantic DTOs.

Each DTO maps directly to the ORM rows added in Phases 5/6/7/8/9. All
new fields are Optional so existing API consumers continue to work
unchanged.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


EvidenceGradeName = Literal[
    "inferred",
    "observed",
    "corroborated",
    "structured_attested",
    "behaviourally_validated",
]

ReproducibilityClass = Literal["stable", "flaky", "unstable", "unknown"]

AbsenceSubType = Literal["absence_failed_fetch", "absence_authoritative_empty"]


class EvidenceSourceDTO(BaseModel):
    source_id: str
    kind: str
    ref: str
    fetched_at: datetime
    response_hash: Optional[str] = None
    notes: str = ""


class SignalEvidenceDTO(BaseModel):
    """Per-signal evidence payload for `GET /signals/{signal_id}`."""
    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float
    evidence_grade: Optional[EvidenceGradeName] = None
    evidence_basis: Optional[str] = None
    evidence_sources: List[EvidenceSourceDTO] = Field(default_factory=list)
    evidence_pro: Optional[str] = None
    evidence_counter: Optional[str] = None
    evidence_tie_breaker: Optional[str] = None
    absence_sub_type: Optional[AbsenceSubType] = None
    primitive_type: Optional[str] = None
    reproducibility: Optional[ReproducibilityClass] = None
    variant_of: Optional[str] = None
    cluster_id: Optional[str] = None


class GradeRollupDTO(BaseModel):
    """Generic (min, weighted-mean, distribution) rollup payload.

    Used for composite, per-group, and per-primitive rollups. The
    `weighted_mean_grade` field is rendered as supplementary text in the
    UI — never thresholded by frontend or backend code.
    """
    min_grade: Optional[EvidenceGradeName] = None
    weighted_mean_grade: Optional[float] = None
    distribution: Dict[str, float] = Field(default_factory=dict)


class CompositeEvidenceDTO(BaseModel):
    """Single payload for `GET /model-versions/{mv_id}/evidence`."""
    composite: GradeRollupDTO
    per_group: Dict[str, GradeRollupDTO] = Field(default_factory=dict)
    per_primitive: Dict[str, GradeRollupDTO] = Field(default_factory=dict)
    grade_referral_reasons: List[str] = Field(default_factory=list)


class SignalHistoryRowDTO(BaseModel):
    """One row from the append-only signal_history table."""
    model_version_id: str
    recorded_at: datetime
    evidence_grade: Optional[EvidenceGradeName] = None
    score: Optional[float] = None
    category: Optional[str] = None
    evidence_basis: Optional[str] = None
