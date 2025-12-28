"""
DSI Analytics Types (Phase 8)

Data structures for performance monitoring, cohort analysis,
and model tuning.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# ENUMS
# =============================================================================

class TuningMode(Enum):
    """Model tuning modes."""
    MANUAL = "manual"        # Generate recommendations for human review
    SEMI_AUTO = "semi_auto"  # Apply with approval
    AUTO = "auto"            # Automatically adjust within bounds


class RecommendationType(Enum):
    """Types of tuning recommendations."""
    WEIGHT_ADJUST = "weight_adjust"
    THRESHOLD_ADJUST = "threshold_adjust"
    SIGNAL_ADD = "signal_add"
    SIGNAL_DEPRECATE = "signal_deprecate"
    TIER_BOUNDARY = "tier_boundary"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# =============================================================================
# OUTCOME TRACKING
# =============================================================================

@dataclass
class OutcomeRecord:
    """
    Actual outcome for a priced risk.

    Links DSI predictions to real-world results for performance tracking.
    """
    # Identifiers
    entity_id: str
    model_id: str
    outcome_id: str = ""

    # Policy period
    policy_inception: Optional[date] = None
    policy_expiry: Optional[date] = None

    # What we predicted
    dsi_score: float = 0.0
    dsi_tier: int = 3
    quoted_premium: float = 0.0
    bound_premium: float = 0.0  # May differ from quote

    # What actually happened
    claim_count: int = 0
    incurred_losses: float = 0.0
    paid_losses: float = 0.0
    large_losses: List[float] = field(default_factory=list)

    @property
    def loss_ratio(self) -> float:
        """Calculate loss ratio from bound premium."""
        if self.bound_premium <= 0:
            return 0.0
        return self.incurred_losses / self.bound_premium

    @property
    def has_claims(self) -> bool:
        """Check if any claims occurred."""
        return self.claim_count > 0 or self.incurred_losses > 0

    # Signal values at time of quote (for analysis)
    signal_values: Dict[str, float] = field(default_factory=dict)

    # Metadata
    coverage: str = ""
    configuration: str = ""
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_model_version(
        cls,
        model_version: Any,  # ModelVersion from model.types
        bound_premium: float,
        claim_count: int = 0,
        incurred_losses: float = 0.0,
    ) -> "OutcomeRecord":
        """Create outcome record from a model version."""
        return cls(
            entity_id=model_version.entity_id,
            model_id=model_version.model_id,
            outcome_id=f"{model_version.model_id}_outcome",
            dsi_score=model_version.pure_composite_score,
            dsi_tier=model_version.final_tier,
            quoted_premium=model_version.final_premium,
            bound_premium=bound_premium,
            claim_count=claim_count,
            incurred_losses=incurred_losses,
            coverage=model_version.coverage,
            configuration=model_version.configuration,
        )


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@dataclass
class TierPerformance:
    """Performance metrics for a specific tier."""
    tier: int
    tier_label: str = ""

    # Volume
    count: int = 0
    premium_volume: float = 0.0

    # Averages
    average_score: float = 0.0
    average_loss_ratio: float = 0.0
    expected_loss_ratio: float = 0.0

    # Accuracy
    claim_frequency: float = 0.0  # % with claims
    severity_average: float = 0.0  # Average claim size

    @property
    def actual_vs_expected(self) -> float:
        """Ratio of actual to expected loss ratio."""
        if self.expected_loss_ratio <= 0:
            return 1.0
        return self.average_loss_ratio / self.expected_loss_ratio


@dataclass
class SignalPerformance:
    """Performance metrics for a specific signal."""
    signal_id: str
    signal_name: str
    group_id: str

    # Contribution analysis
    weight: float = 0.0
    average_score: float = 0.0

    # Correlation with outcomes
    loss_ratio_correlation: float = 0.0
    claim_frequency_correlation: float = 0.0

    # Recommendation
    recommended_weight_change: float = 0.0  # + increase, - decrease
    change_confidence: float = 0.0


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics for a period."""
    # Period definition
    period: str = "annual"  # 'monthly', 'quarterly', 'annual'
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    coverage: str = ""

    # Volume
    total_records: int = 0
    total_premium: float = 0.0
    total_losses: float = 0.0

    # Accuracy metrics
    tier_accuracy: float = 0.0  # % where tier matched outcome expectation
    score_correlation: float = 0.0  # Correlation with loss ratio
    lift_curve_auc: float = 0.0  # Area under lift curve (model discrimination)
    gini_coefficient: float = 0.0  # Model discrimination (2*AUC - 1)

    # Bias metrics
    average_prediction_error: float = 0.0  # Mean error
    systematic_bias: float = 0.0  # Consistent over/under-pricing

    # Overall loss ratio
    overall_loss_ratio: float = 0.0
    expected_loss_ratio: float = 0.55

    @property
    def actual_vs_expected(self) -> float:
        """Overall actual vs expected."""
        if self.expected_loss_ratio <= 0:
            return 1.0
        return self.overall_loss_ratio / self.expected_loss_ratio

    # Tier breakdown
    tier_metrics: Dict[int, TierPerformance] = field(default_factory=dict)

    # Signal breakdown
    signal_performance: Dict[str, SignalPerformance] = field(default_factory=dict)

    # Alerts
    alerts: List[str] = field(default_factory=list)


# =============================================================================
# COHORT ANALYSIS
# =============================================================================

@dataclass
class CohortDefinition:
    """Definition of a comparison cohort."""
    cohort_id: str
    name: str
    description: str = ""

    # Filters to define cohort membership
    # e.g., {"coverage": "fi", "tier": [1,2], "revenue_min": 100000000}
    criteria: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    member_count: int = 0


@dataclass
class CohortComparison:
    """Result of comparing two cohorts."""
    cohort_a: CohortDefinition
    cohort_b: CohortDefinition

    # Comparison metrics
    metric_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # e.g., {"loss_ratio": {"a": 0.45, "b": 0.55, "diff": -0.10}}

    # Statistical significance
    significant_differences: List[str] = field(default_factory=list)

    # Recommendations
    insights: List[str] = field(default_factory=list)


@dataclass
class OutlierRisk:
    """A risk that deviates significantly from its cohort."""
    entity_id: str
    model_id: str
    cohort_id: str

    # Deviation
    metric: str  # Which metric is outlying
    value: float
    cohort_mean: float
    cohort_std: float
    z_score: float

    # Context
    notes: List[str] = field(default_factory=list)


# =============================================================================
# TUNING RECOMMENDATIONS
# =============================================================================

@dataclass
class TuningRecommendation:
    """A specific tuning recommendation."""
    recommendation_id: str
    type: RecommendationType

    # Target
    target_id: str  # Signal ID, group ID, or tier
    target_name: str = ""

    # Change
    current_value: Any = None
    recommended_value: Any = None

    # Impact assessment
    expected_impact: float = 0.0  # Estimated improvement (% or absolute)
    confidence: float = 0.0  # 0-1 confidence in recommendation

    # Rationale
    rationale: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: str = "pending"  # pending, approved, applied, rejected
    reviewed_by: str = ""
    reviewed_at: Optional[datetime] = None

    @property
    def change_description(self) -> str:
        """Human-readable description of the change."""
        if self.type == RecommendationType.WEIGHT_ADJUST:
            change = self.recommended_value - self.current_value
            direction = "increase" if change > 0 else "decrease"
            return f"{direction} {self.target_name} weight by {abs(change):.2f}"
        elif self.type == RecommendationType.THRESHOLD_ADJUST:
            return f"Adjust {self.target_name} threshold from {self.current_value} to {self.recommended_value}"
        elif self.type == RecommendationType.SIGNAL_DEPRECATE:
            return f"Deprecate signal {self.target_name} (low correlation with outcomes)"
        else:
            return f"{self.type.value}: {self.target_name}"


@dataclass
class TuningResult:
    """Result of applying tuning recommendations."""
    applied_recommendations: List[str]  # IDs
    skipped_recommendations: List[str]  # IDs
    errors: List[str]

    # New configuration version
    new_config_version: str = ""
    new_config_hash: str = ""

    # Expected impact
    estimated_improvement: float = 0.0


@dataclass
class BacktestResult:
    """Result of backtesting tuning recommendations."""
    recommendations_tested: List[str]  # IDs

    # Current model performance
    current_metrics: PerformanceMetrics

    # Simulated performance with changes
    simulated_metrics: PerformanceMetrics

    # Comparison
    improvement: Dict[str, float] = field(default_factory=dict)
    # e.g., {"tier_accuracy": +0.05, "loss_ratio_correlation": +0.03}

    # Confidence
    sample_size: int = 0
    confidence_interval: float = 0.95


# =============================================================================
# ALERTS
# =============================================================================

@dataclass
class PerformanceAlert:
    """Alert for performance issues."""
    alert_id: str
    severity: AlertSeverity
    category: str  # 'drift', 'anomaly', 'trend', 'threshold'

    # Details
    title: str
    description: str
    metric: str
    current_value: float
    threshold_value: float

    # Context
    coverage: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)

    # Resolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""
