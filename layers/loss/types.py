"""
Loss Correlation Layer Types (Phase 16)

Core data types for loss propensity scoring, cohort analysis,
and continuous monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class CorrelationType(Enum):
    """Type of loss correlation for a signal."""
    FREQUENCY = "frequency"   # Correlates with loss frequency
    SEVERITY = "severity"     # Correlates with loss severity
    BOTH = "both"             # Correlates with both


class CorrelationDirection(Enum):
    """Direction of signal-loss correlation."""
    POSITIVE = "positive"     # Higher signal value = higher loss
    NEGATIVE = "negative"     # Higher signal value = lower loss


class LossPropensityBand(Enum):
    """Loss propensity classification bands."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class SeverityPropensityBand(Enum):
    """Severity propensity classification bands."""
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"


class TrendDirection(Enum):
    """Direction of loss propensity trend over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"


# =============================================================================
# Signal Results
# =============================================================================

@dataclass
class LossSignalResult:
    """Output from a loss-predictive signal extraction."""
    signal_id: str
    value: Any
    normalized_value: float  # 0-100
    confidence: float  # 0-1
    correlation_type: CorrelationType
    correlation_direction: CorrelationDirection
    source_urls: List[str]
    extracted_at: datetime
    notes: Optional[str] = None


# =============================================================================
# Configuration Types
# =============================================================================

@dataclass
class LossCorrelationFeatureConfig:
    """Configuration for a single loss-predictive signal."""
    id: str
    weight: float
    correlation_type: CorrelationType
    correlation_direction: CorrelationDirection
    normalizer: str
    thresholds: Optional[List[float]] = None
    percentiles: Optional[List[float]] = None
    mapping: Optional[Dict[str, float]] = None
    cap: Optional[float] = None
    lag_months: Optional[int] = None


@dataclass
class LossCorrelationGroupConfig:
    """Configuration for a group of loss-predictive signals."""
    name: str
    weight: float
    confidence_threshold: float
    features: List[LossCorrelationFeatureConfig]


@dataclass
class PropensityBandConfig:
    """Configuration for a loss propensity band."""
    name: str
    min_score: float
    max_score: float
    expected_frequency_multiplier: float
    expected_severity_multiplier: float


@dataclass
class CohortDefinition:
    """Definition of a signal-derived peer cohort."""
    id: str
    name: str
    criteria: Dict[str, Any]
    historical_frequency: Optional[float] = None
    historical_severity: Optional[float] = None
    member_count: Optional[int] = None
    calibration_date: Optional[datetime] = None


@dataclass
class MonitoringConfig:
    """Configuration for continuous monitoring."""
    refresh_frequency: str = "monthly"  # daily, weekly, monthly
    deterioration_threshold: float = 15.0
    improvement_threshold: float = 15.0
    alert_on_band_change: bool = True
    alert_on_velocity_spike: bool = True
    velocity_spike_threshold: float = 10.0  # points per month


@dataclass
class LossCorrelationConfig:
    """Complete loss correlation configuration from YAML."""
    enabled: bool
    version: str
    correlation_groups: List[LossCorrelationGroupConfig]
    propensity_band_mapping_method: str
    propensity_bands: List[PropensityBandConfig]
    severity_bands: List[PropensityBandConfig]
    cohort_definitions: List[CohortDefinition]
    pricing_integration_method: str
    frequency_impact_cap: float
    frequency_impact_floor: float
    severity_impact_cap: float
    severity_impact_floor: float
    frequency_weight: float
    severity_weight: float
    auto_apply_rules: List[Dict[str, Any]]
    monitoring_config: MonitoringConfig

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LossCorrelationConfig":
        """Create config from dictionary (parsed YAML)."""
        # Parse correlation groups
        groups = []
        for group_data in data.get("correlation_groups", []):
            features = []
            for feat_data in group_data.get("features", []):
                features.append(LossCorrelationFeatureConfig(
                    id=feat_data["id"],
                    weight=feat_data.get("weight", 1.0),
                    correlation_type=CorrelationType(feat_data.get("correlation_type", "both")),
                    correlation_direction=CorrelationDirection(feat_data.get("correlation_direction", "positive")),
                    normalizer=feat_data.get("normalizer", "linear"),
                    thresholds=feat_data.get("thresholds"),
                    percentiles=feat_data.get("percentiles"),
                    mapping=feat_data.get("mapping"),
                    cap=feat_data.get("cap"),
                    lag_months=feat_data.get("lag_months"),
                ))
            groups.append(LossCorrelationGroupConfig(
                name=group_data["name"],
                weight=group_data.get("weight", 1.0),
                confidence_threshold=group_data.get("confidence_threshold", 0.5),
                features=features,
            ))

        # Parse propensity bands
        propensity_bands = []
        for band_data in data.get("propensity_band_mapping", {}).get("bands", []):
            propensity_bands.append(PropensityBandConfig(
                name=band_data["name"],
                min_score=band_data["min_score"],
                max_score=band_data["max_score"],
                expected_frequency_multiplier=band_data.get("expected_frequency_multiplier", 1.0),
                expected_severity_multiplier=band_data.get("expected_severity_multiplier", 1.0),
            ))

        # Parse severity bands (may be same as propensity or separate)
        severity_bands = []
        severity_data = data.get("severity_band_mapping", data.get("propensity_band_mapping", {}))
        for band_data in severity_data.get("bands", []):
            severity_bands.append(PropensityBandConfig(
                name=band_data["name"],
                min_score=band_data["min_score"],
                max_score=band_data["max_score"],
                expected_frequency_multiplier=band_data.get("expected_frequency_multiplier", 1.0),
                expected_severity_multiplier=band_data.get("expected_severity_multiplier", 1.0),
            ))

        # Parse cohort definitions
        cohorts = []
        for cohort_data in data.get("cohort_definitions", []):
            cohorts.append(CohortDefinition(
                id=cohort_data["id"],
                name=cohort_data["name"],
                criteria=cohort_data.get("criteria", {}),
                historical_frequency=cohort_data.get("historical_frequency"),
                historical_severity=cohort_data.get("historical_severity"),
                member_count=cohort_data.get("member_count"),
            ))

        # Parse pricing integration
        pricing = data.get("pricing_integration", {})

        # Parse monitoring config
        monitoring_data = data.get("monitoring", {})
        monitoring = MonitoringConfig(
            refresh_frequency=monitoring_data.get("refresh_frequency", "monthly"),
            deterioration_threshold=monitoring_data.get("deterioration_threshold", 15.0),
            improvement_threshold=monitoring_data.get("improvement_threshold", 15.0),
        )

        return cls(
            enabled=data.get("enabled", False),
            version=data.get("version", "1.0.0"),
            correlation_groups=groups,
            propensity_band_mapping_method=data.get("propensity_band_mapping", {}).get("method", "fixed_threshold"),
            propensity_bands=propensity_bands,
            severity_bands=severity_bands if severity_bands else propensity_bands,
            cohort_definitions=cohorts,
            pricing_integration_method=pricing.get("method", "multiplicative"),
            frequency_impact_cap=pricing.get("frequency_impact_cap", 1.50),
            frequency_impact_floor=pricing.get("frequency_impact_floor", 0.70),
            severity_impact_cap=pricing.get("severity_impact_cap", 1.50),
            severity_impact_floor=pricing.get("severity_impact_floor", 0.70),
            frequency_weight=pricing.get("frequency_weight", 0.60),
            severity_weight=pricing.get("severity_weight", 0.40),
            auto_apply_rules=data.get("auto_apply_rules", []),
            monitoring_config=monitoring,
        )


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class LossPropensityResult:
    """Complete output from loss propensity calculation."""
    # Primary scores
    loss_propensity_score: float  # 0-100
    severity_propensity_score: float  # 0-100
    loss_propensity_band: LossPropensityBand
    severity_propensity_band: SeverityPropensityBand
    loss_confidence: float  # 0-1

    # Cohort assignment
    cohort_id: str
    cohort_name: str
    cohort_confidence: float

    # Component scores
    group_scores: Dict[str, float]
    group_confidences: Dict[str, float]
    frequency_group_scores: Dict[str, float]
    severity_group_scores: Dict[str, float]

    # Pricing impact
    frequency_multiplier: float
    severity_multiplier: float
    combined_loss_modifier: float

    # Monitoring
    trend_direction: TrendDirection
    score_velocity: float  # points per month
    days_since_last_assessment: int
    previous_score: Optional[float]

    # Referral triggers
    referral_triggered: bool
    referral_reasons: List[str]
    flags: List[str]

    # Audit trail
    signal_results: List[LossSignalResult]
    calculated_at: datetime
    config_version: str
    correlation_matrix_version: Optional[str] = None


# =============================================================================
# Correlation Matrix Types
# =============================================================================

@dataclass
class CorrelationMatrixEntry:
    """Entry in the loss correlation matrix."""
    signal_id: str
    frequency_correlation: float  # -1 to 1
    severity_correlation: float  # -1 to 1
    information_value: float  # 0 to 1
    stability_score: float  # 0 to 1
    sample_size: int
    last_updated: datetime
    interaction_effects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CorrelationMatrix:
    """Complete correlation matrix for a coverage."""
    coverage: str
    version: str
    created_at: datetime
    observation_period_start: datetime
    observation_period_end: datetime
    policy_count: int
    claim_count: int
    entries: List[CorrelationMatrixEntry]
    cohort_calibrations: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Monitoring Types
# =============================================================================

@dataclass
class DeteriorationAlert:
    """Alert for deteriorating loss propensity."""
    entity_id: str
    alert_type: str  # 'warning', 'critical'
    current_score: float
    previous_score: float
    score_delta: float
    days_elapsed: int
    current_band: str
    previous_band: str
    trigger_reason: str
    recommended_action: str
    created_at: datetime


@dataclass
class MonitoringResult:
    """Result of monitoring check."""
    entity_id: str
    current_result: LossPropensityResult
    previous_result: Optional[LossPropensityResult]
    alerts: List[DeteriorationAlert]
    refresh_recommended: bool
    next_refresh_date: datetime
