"""
DSI World Engine

The autonomous intelligence layer. Consumes the output of every assessment
across all entities, all coverages, and all time. Discovers emergent
cross-signal causal relationships. Validates them statistically without
human authorisation. Publishes intelligence to a read-only registry that
lower layers can consume but are not required to obey.

See development/project/version/5/world_engine_phases/ for phase docs.
"""

from world_engine.types import (
    MaturityStage,
    LifecycleState,
    CausalDirection,
    DriftSeverity,
    StateTransition,
    DiscoveredRelationship,
    ConsistencyScore,
    PrecursorEvaluation,
    TierMigrationDistribution,
    CausalAdjustmentFactor,
    PortfolioConcentration,
    DriftAlert,
    CandidateRelationship,
    DirectedCandidate,
    ValidationResult,
    StabilityResult,
    PredictiveResult,
    ScanRunReport,
    MaturityState,
)

__all__ = [
    "MaturityStage",
    "LifecycleState",
    "CausalDirection",
    "DriftSeverity",
    "StateTransition",
    "DiscoveredRelationship",
    "ConsistencyScore",
    "PrecursorEvaluation",
    "TierMigrationDistribution",
    "CausalAdjustmentFactor",
    "PortfolioConcentration",
    "DriftAlert",
    "CandidateRelationship",
    "DirectedCandidate",
    "ValidationResult",
    "StabilityResult",
    "PredictiveResult",
    "ScanRunReport",
    "MaturityState",
]
