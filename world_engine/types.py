"""
World Engine Core Types

All Pydantic types consumed by the World Engine subsystems. Types are
defined here (WE-1) even if the consuming subsystem is built later, so
type contracts are stable from the start.

See development/project/version/5/world_engine_phases/WE-1_Foundation.md
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================


class MaturityStage(str, Enum):
    """World Engine maturity, gated by population size and time depth."""

    SEED = "seed"  # < 500 entities, 0-6 months
    LEARN = "learn"  # 500-5K entities, 6-18 months
    EMERGE = "emerge"  # 5K-50K entities, 18-36 months
    SIMULATE = "simulate"  # > 50K entities, 36+ months


class LifecycleState(str, Enum):
    """Autonomous lifecycle states for discovered relationships."""

    CANDIDATE = "candidate"
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class CausalDirection(str, Enum):
    """Direction of a causal relationship."""

    A_CAUSES_B = "a_causes_b"
    B_CAUSES_A = "b_causes_a"
    BIDIRECTIONAL = "bidirectional"
    CONTEMPORANEOUS = "contemporaneous"


class DriftSeverity(str, Enum):
    """Severity classification for drift alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# CORE INTELLIGENCE TYPES
# =============================================================================


class StateTransition(BaseModel):
    """A single transition in a relationship's lifecycle."""

    from_state: LifecycleState
    to_state: LifecycleState
    transitioned_at: datetime
    reason: str
    evidence: dict


class DiscoveredRelationship(BaseModel):
    """A causal relationship discovered by the World Engine."""

    id: str
    source_signal: str
    target_signal: str
    direction: CausalDirection
    lag_months: Optional[float] = None
    correlation_rho: float
    granger_f_statistic: Optional[float] = None
    granger_p_value: Optional[float] = None
    effect_size: float
    confounders_tested: list[str] = Field(default_factory=list)
    holdout_rho: Optional[float] = None
    holdout_p_value: Optional[float] = None
    predictive_hit_rate: Optional[float] = None
    population_size: int
    coverage_scope: list[str] = Field(default_factory=list)
    lifecycle_state: LifecycleState
    state_entered_at: datetime
    state_history: list[StateTransition] = Field(default_factory=list)
    influence_weight: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# CONSISTENCY TYPES
# =============================================================================


class ConsistencyScore(BaseModel):
    """Per-assessment cross-signal and cross-layer consistency."""

    entity_id: str
    assessment_id: str
    overall_consistency: float = Field(ge=0.0, le=1.0)
    signal_pair_scores: dict[str, float] = Field(default_factory=dict)
    cross_group_scores: dict[str, float] = Field(default_factory=dict)
    cross_layer_divergence: dict = Field(default_factory=dict)
    divergent_pairs: list[str] = Field(default_factory=list)
    computed_at: datetime


# =============================================================================
# CAF TYPES
# =============================================================================


class PrecursorEvaluation(BaseModel):
    """Evaluation of a single precursor condition for an entity."""

    relationship_id: str
    precursor_signal: str
    entity_value: float
    threshold: float
    distance_from_threshold: float
    implied_probability: float = Field(ge=0.0, le=1.0)
    lag_months: float


class TierMigrationDistribution(BaseModel):
    """Probability distribution over tier migrations during policy period."""

    current_tier: int
    probabilities: dict[int, float] = Field(default_factory=dict)
    expected_tier: float
    policy_period_months: int


class CausalAdjustmentFactor(BaseModel):
    """The CAF that enters the premium formula as a multiplicative adjustment."""

    entity_id: str
    assessment_id: str
    caf_value: float
    confidence: float = Field(ge=0.0, le=1.0)
    active_precursors: list[PrecursorEvaluation] = Field(default_factory=list)
    trajectory: TierMigrationDistribution
    relationships_evaluated: int = 0
    constrained: bool = False
    raw_caf: float = 1.0
    constraint_regime: str = "initial"
    computed_at: datetime

    @classmethod
    def neutral(
        cls,
        entity_id: str = "",
        assessment_id: str = "",
        current_tier: int = 0,
        policy_period_months: int = 12,
    ) -> "CausalAdjustmentFactor":
        """Factory for CAF = 1.0 (zero impact).

        Used when maturity < EMERGE, no active relationships match,
        confidence below gate, or any failure occurs in the pricing engine.
        """
        return cls(
            entity_id=entity_id,
            assessment_id=assessment_id,
            caf_value=1.0,
            confidence=0.0,
            active_precursors=[],
            trajectory=TierMigrationDistribution(
                current_tier=current_tier,
                probabilities={current_tier: 1.0} if current_tier else {},
                expected_tier=float(current_tier),
                policy_period_months=policy_period_months,
            ),
            relationships_evaluated=0,
            constrained=False,
            raw_caf=1.0,
            constraint_regime="neutral",
            computed_at=datetime.utcnow(),
        )


# =============================================================================
# PORTFOLIO TYPES
# =============================================================================


class PortfolioConcentration(BaseModel):
    """Concentration alert for a commercial entity's portfolio."""

    entity_id: str  # Commercial entity (portfolio owner)
    dimension: str  # node | pathway | derivative | cohort
    detail: str
    severity: float = Field(ge=0.0, le=1.0)
    affected_entities: list[str] = Field(default_factory=list)
    computed_at: datetime


# =============================================================================
# DRIFT ALERT TYPES
# =============================================================================


class DriftAlert(BaseModel):
    """A structural drift or regime change detected in the signal landscape."""

    id: str
    alert_type: str  # relationship_shift | regime_change | signal_degradation | correlation_inversion
    severity: DriftSeverity
    source_signal: Optional[str] = None
    target_signal: Optional[str] = None
    relationship_id: Optional[str] = None
    description: str
    evidence: dict = Field(default_factory=dict)
    detected_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


# =============================================================================
# DISCOVERY PIPELINE INTERMEDIATE TYPES
# =============================================================================


class CandidateRelationship(BaseModel):
    """Output of CorrelationScanner (WE-3a) -- pre-causal-inference."""

    source_signal: str
    target_signal: str
    correlation_rho: float
    p_value: float
    population_size: int
    coverage_scope: list[str] = Field(default_factory=list)


class DirectedCandidate(BaseModel):
    """Output of CausalInferencer (WE-3b) -- has direction and lag."""

    source_signal: str
    target_signal: str
    direction: CausalDirection
    lag_months: Optional[float] = None
    correlation_rho: float
    granger_f_statistic: Optional[float] = None
    granger_p_value: Optional[float] = None
    effect_size: float
    confounders_tested: list[str] = Field(default_factory=list)
    population_size: int
    coverage_scope: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Output of HoldoutValidator (WE-3c)."""

    candidate: DirectedCandidate
    holdout_rho: float
    holdout_p_value: float
    passed: bool


class StabilityResult(BaseModel):
    """Output of TemporalStabilityTracker (WE-3c)."""

    relationship_id: str
    windows_checked: int
    windows_stable: int
    correlation_trend: list[float] = Field(default_factory=list)
    stable: bool
    sign_flip_detected: bool


class PredictiveResult(BaseModel):
    """Output of PredictiveValidator (WE-3c)."""

    relationship_id: str
    predictions_made: int
    predictions_hit: int
    hit_rate: float = Field(ge=0.0, le=1.0)
    passed: bool


class ScanRunReport(BaseModel):
    """Audit record for a complete discovery cycle (WE-3g)."""

    run_id: str
    started_at: datetime
    completed_at: datetime
    maturity_stage: MaturityStage
    entities_scanned: int = 0
    pairs_tested: int = 0
    candidates_found: int = 0
    candidates_after_inference: int = 0
    candidates_after_confound: int = 0
    candidates_after_holdout: int = 0
    new_registrations: int = 0
    state_transitions: list[StateTransition] = Field(default_factory=list)
    drift_alerts_raised: int = 0
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# MATURITY STATE TYPE
# =============================================================================


class MaturityState(BaseModel):
    """Current maturity assessment of the World Engine."""

    stage: MaturityStage
    assessed_entity_count: int
    entities_with_temporal_data: int  # entities with >= 2 assessments
    earliest_assessment: Optional[datetime] = None
    time_depth_months: float
    active_relationships: int
    provisional_relationships: int
    candidate_relationships: int
    capabilities: dict[str, bool] = Field(default_factory=dict)
    evaluated_at: datetime
