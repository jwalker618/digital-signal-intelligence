"""C-2: Recalibration types.

Pydantic models for the recalibration engine's outputs. These serialise
into the JSONB columns on `recalibration_proposals` and are consumed by
the governance UI in C-3.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPLOYED = "DEPLOYED"


class Alignment(str, Enum):
    """Traffic-light alignment state for a signal report card."""
    WELL_CALIBRATED = "well_calibrated"
    ADJUSTMENT_SUGGESTED = "adjustment_suggested"
    SIGNIFICANT_MISALIGNMENT = "significant_misalignment"


class SignalReportCard(BaseModel):
    """Per-signal predictive power analysis (C-2c output)."""

    signal_id: str
    group_code: Optional[str] = None
    current_weight: float
    evidence_supported_weight: float
    # Component scores
    discrimination_u_stat: Optional[float] = None
    discrimination_p_value: Optional[float] = None
    monotonicity_rho: Optional[float] = None
    stability_coefficient: Optional[float] = None
    information_value: Optional[float] = None
    # Verdict
    alignment: Alignment = Alignment.WELL_CALIBRATED
    sample_size: int = 0
    notes: list[str] = Field(default_factory=list)


class WeightChange(BaseModel):
    """A proposed weight adjustment for a single signal (C-2d output)."""

    signal_id: str
    group_code: Optional[str] = None
    current_weight: float
    proposed_weight: float
    delta: float
    delta_pct: float   # delta / current_weight * 100 (0 if current is 0)


class TierThresholdChange(BaseModel):
    """A proposed tier boundary shift (C-2e output)."""

    band_id: int
    boundary: str   # "min" or "max"
    current_value: float
    proposed_value: float
    delta: float
    evidence: dict = Field(default_factory=dict)


class ImpactAssessment(BaseModel):
    """Real-world impact of applying the proposed config changes."""

    # Tier migration: {current_tier -> {new_tier -> count}}
    tier_migration: dict[str, dict[str, int]] = Field(default_factory=dict)
    # Aggregate premium impact (absolute and percentage)
    total_premium_delta: float = 0.0
    total_premium_delta_pct: float = 0.0
    # Discrimination: AUC / IV improvement over the current model
    discrimination_improvement: float = 0.0
    # Counts
    assessments_evaluated: int = 0
    assessments_tier_changed: int = 0


class RecalibrationProposalPayload(BaseModel):
    """In-memory structure mirroring the persisted proposal row.

    Used both as the generator's output and as the API response type.
    """

    id: Optional[str] = None
    tenant_id: Optional[str] = None
    coverage: str
    config_name: str
    proposed_at: datetime
    proposed_by: str
    trigger: str = "system"
    status: ProposalStatus = ProposalStatus.DRAFT

    signal_report_cards: list[SignalReportCard] = Field(default_factory=list)
    weight_changes: list[WeightChange] = Field(default_factory=list)
    tier_threshold_changes: list[TierThresholdChange] = Field(default_factory=list)
    impact_assessment: ImpactAssessment = Field(default_factory=ImpactAssessment)
    statistical_evidence: dict = Field(default_factory=dict)
    sample_size: int = 0

    reviewer_id: Optional[str] = None
    review_decision: Optional[str] = None
    review_rationale: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    deployed_config_version_id: Optional[str] = None
    deployed_at: Optional[datetime] = None
