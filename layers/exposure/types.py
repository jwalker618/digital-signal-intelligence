"""
Exposure Shadow Layer Types (Phase 17)

Core types for exposure magnitude and complexity scoring.
Enables TIV estimation without client-provided data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# ENUMS
# =============================================================================

class ProxyTier(Enum):
    """
    Reliability tier for exposure signals.

    Lower tier number = higher reliability.
    """
    DIRECT_OBSERVABLE = 1   # Public financials, regulatory filings
    INFERRED_PROXY = 2      # Digital footprint, network signals
    COHORT_INFERENCE = 3    # Peer group matching
    UNKNOWN = 4             # Insufficient data


class ExposureBand(Enum):
    """
    Exposure magnitude band classification.
    """
    MICRO = "micro"           # $0 - $1M TIV
    SMALL = "small"           # $1M - $10M TIV
    MEDIUM = "medium"         # $10M - $50M TIV
    LARGE = "large"           # $50M - $250M TIV
    VERY_LARGE = "very_large" # $250M+ TIV


class ComplexityCategory(Enum):
    """
    Exposure complexity classification.
    """
    SIMPLE = "simple"                     # Single location, simple structure
    MODERATE = "moderate"                 # Few locations, basic structure
    COMPLEX = "complex"                   # Multiple locations, subsidiaries
    HIGHLY_COMPLEX = "highly_complex"     # Many locations, complex structure
    EXTREMELY_COMPLEX = "extremely_complex"  # Global, very complex structure


class ExposureSignalType(Enum):
    """
    Type of signal for routing to correct scorer.
    """
    RISK = "risk"
    EXPOSURE = "exposure"
    COMPLEXITY = "complexity"


# =============================================================================
# CONFIGURATION TYPES
# =============================================================================

@dataclass
class ExposureBandConfig:
    """Configuration for an exposure band."""
    name: str
    min_score: float
    max_score: float
    implied_tiv_low: float = 0.0
    implied_tiv_high: float = 0.0
    exposure_modifier: float = 1.0
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.name.replace("_", " ").title()


@dataclass
class ComplexityCategoryConfig:
    """Configuration for a complexity category."""
    name: str
    min_score: float
    max_score: float
    complexity_modifier: float = 1.0
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.name.replace("_", " ").title()


@dataclass
class ExposureFeatureConfig:
    """Configuration for an exposure signal feature."""
    id: str
    weight: float
    proxy_tier: ProxyTier = ProxyTier.INFERRED_PROXY
    inference_utility_function: str = ""
    normalizer: str = "linear"
    description: str = ""


@dataclass
class ExposureGroupConfig:
    """Configuration for an exposure signal group."""
    name: str
    weight: float
    signal_type: ExposureSignalType = ExposureSignalType.EXPOSURE
    features: List[ExposureFeatureConfig] = field(default_factory=list)
    confidence_threshold: float = 0.5
    description: str = ""


@dataclass
class CohortPriorConfig:
    """Configuration for cohort priors."""
    cohort_id: str
    name: str
    sector: Optional[str] = None
    region: Optional[str] = None
    size_indicator: Optional[str] = None
    prior_band: ExposureBand = ExposureBand.MEDIUM
    prior_score: float = 50.0
    confidence: float = 0.5


@dataclass
class ExposureConfig:
    """Complete exposure shadow layer configuration."""
    enabled: bool = True
    version: str = ""

    # Signal groups for magnitude
    exposure_groups: List[ExposureGroupConfig] = field(default_factory=list)

    # Signal groups for complexity
    complexity_groups: List[ExposureGroupConfig] = field(default_factory=list)

    # Band mapping
    band_mapping_method: str = "fixed_threshold"  # fixed_threshold | quantile | cohort
    exposure_bands: List[ExposureBandConfig] = field(default_factory=list)

    # Complexity mapping
    complexity_categories: List[ComplexityCategoryConfig] = field(default_factory=list)

    # Cohort priors
    cohort_priors: List[CohortPriorConfig] = field(default_factory=list)

    # Pricing integration
    pricing_integration_method: str = "parallel"  # parallel | embedded | grid

    # Auto-apply rules
    auto_apply_rules: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExposureConfig":
        """Create ExposureConfig from dictionary (YAML config)."""
        exposure_groups = []
        for group_data in data.get("exposure_groups", []):
            features = [
                ExposureFeatureConfig(
                    id=f.get("id", ""),
                    weight=f.get("weight", 0.0),
                    proxy_tier=ProxyTier[f.get("proxy_tier", "INFERRED_PROXY").upper()]
                        if isinstance(f.get("proxy_tier"), str) else ProxyTier.INFERRED_PROXY,
                    inference_utility_function=f.get("inference_utility_function", ""),
                    normalizer=f.get("normalizer", "linear"),
                    description=f.get("description", ""),
                )
                for f in group_data.get("features", [])
            ]
            exposure_groups.append(ExposureGroupConfig(
                name=group_data.get("name", ""),
                weight=group_data.get("weight", 0.0),
                signal_type=ExposureSignalType.EXPOSURE,
                features=features,
                confidence_threshold=group_data.get("confidence_threshold", 0.5),
                description=group_data.get("description", ""),
            ))

        complexity_groups = []
        for group_data in data.get("complexity_groups", []):
            features = [
                ExposureFeatureConfig(
                    id=f.get("id", ""),
                    weight=f.get("weight", 0.0),
                    proxy_tier=ProxyTier[f.get("proxy_tier", "INFERRED_PROXY").upper()]
                        if isinstance(f.get("proxy_tier"), str) else ProxyTier.INFERRED_PROXY,
                    inference_utility_function=f.get("inference_utility_function", ""),
                    normalizer=f.get("normalizer", "linear"),
                    description=f.get("description", ""),
                )
                for f in group_data.get("features", [])
            ]
            complexity_groups.append(ExposureGroupConfig(
                name=group_data.get("name", ""),
                weight=group_data.get("weight", 0.0),
                signal_type=ExposureSignalType.COMPLEXITY,
                features=features,
                confidence_threshold=group_data.get("confidence_threshold", 0.5),
                description=group_data.get("description", ""),
            ))

        # Parse band mapping
        band_data = data.get("band_mapping", {})
        exposure_bands = []
        for band in band_data.get("bands", []):
            exposure_bands.append(ExposureBandConfig(
                name=band.get("name", ""),
                min_score=band.get("min_score", 0.0),
                max_score=band.get("max_score", 100.0),
                implied_tiv_low=band.get("implied_tiv_low", 0.0),
                implied_tiv_high=band.get("implied_tiv_high", 0.0),
                exposure_modifier=band.get("exposure_modifier", 1.0),
                label=band.get("label", ""),
            ))

        # Parse complexity categories
        complexity_categories = []
        for cat in data.get("complexity_categories", []):
            complexity_categories.append(ComplexityCategoryConfig(
                name=cat.get("name", ""),
                min_score=cat.get("min_score", 0.0),
                max_score=cat.get("max_score", 100.0),
                complexity_modifier=cat.get("complexity_modifier", 1.0),
                label=cat.get("label", ""),
            ))

        # Parse cohort priors
        cohort_priors = []
        for prior in data.get("cohort_priors", []):
            cohort_priors.append(CohortPriorConfig(
                cohort_id=prior.get("cohort_id", ""),
                name=prior.get("name", ""),
                sector=prior.get("sector"),
                region=prior.get("region"),
                size_indicator=prior.get("size_indicator"),
                prior_band=ExposureBand(prior.get("prior_band", "medium")),
                prior_score=prior.get("prior_score", 50.0),
                confidence=prior.get("confidence", 0.5),
            ))

        return cls(
            enabled=data.get("enabled", True),
            version=data.get("version", ""),
            exposure_groups=exposure_groups,
            complexity_groups=complexity_groups,
            band_mapping_method=band_data.get("method", "fixed_threshold"),
            exposure_bands=exposure_bands,
            complexity_categories=complexity_categories,
            cohort_priors=cohort_priors,
            pricing_integration_method=data.get("pricing_integration", {}).get("method", "parallel"),
            auto_apply_rules=data.get("auto_apply_rules", []),
        )


# =============================================================================
# SIGNAL OUTPUT TYPES
# =============================================================================

@dataclass
class ExposureSignalOutput:
    """
    Output from an exposure signal extraction.

    Similar to SignalOutput but with exposure-specific fields.
    """
    signal_id: str
    raw_value: float
    normalized_value: float
    confidence: float
    proxy_tier: ProxyTier
    data_sources: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExposureGroupScore:
    """
    Score for an exposure signal group.
    """
    group_name: str
    score: float
    confidence: float
    weight: float
    signals_available: int
    signals_total: int
    contributing_signals: Tuple[str, ...] = field(default_factory=tuple)
    proxy_tier: ProxyTier = ProxyTier.UNKNOWN


# =============================================================================
# RESULT TYPES
# =============================================================================

@dataclass
class ExposureResult:
    """
    Complete result from exposure magnitude scoring.
    """
    # Core outputs
    score: float                          # 0-100
    band: ExposureBand                    # micro → very_large
    confidence: float                     # 0-1
    proxy_tier: ProxyTier                 # Reliability level

    # Range (acknowledges uncertainty)
    range_low: float                      # Score range lower bound
    range_high: float                     # Score range upper bound

    # Implied TIV
    implied_tiv_low: float                # Estimated TIV lower bound
    implied_tiv_high: float               # Estimated TIV upper bound

    # Group-level detail
    group_scores: Dict[str, float] = field(default_factory=dict)

    # Signals used
    signals_used: List[str] = field(default_factory=list)
    signals_available: int = 0
    signals_total: int = 0

    # Cohort information (if used)
    cohort_id: Optional[str] = None
    cohort_name: Optional[str] = None
    cohort_prior_applied: bool = False

    # Pricing modifier
    exposure_modifier: float = 1.0

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    # Referral/flag
    referral_triggered: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)


@dataclass
class ComplexityResult:
    """
    Complete result from complexity scoring.
    """
    # Core outputs
    score: float                          # 0-100
    category: ComplexityCategory          # simple → extremely_complex
    confidence: float                     # 0-1

    # Component scores
    geographic_score: float = 0.0         # Geographic dispersion
    structural_score: float = 0.0         # Organizational complexity
    technical_score: float = 0.0          # Technology heterogeneity
    regulatory_score: float = 0.0         # Regulatory jurisdiction count

    # Group-level detail
    group_scores: Dict[str, float] = field(default_factory=dict)

    # Signals used
    signals_used: List[str] = field(default_factory=list)

    # Pricing modifier
    complexity_modifier: float = 1.0

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CombinedExposureResult:
    """
    Combined exposure and complexity result.
    """
    exposure: ExposureResult
    complexity: ComplexityResult

    # Combined modifier
    combined_modifier: float = 1.0

    # Overall confidence
    overall_confidence: float = 0.0

    # Calculated at
    calculated_at: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# COHORT TYPES
# =============================================================================

@dataclass
class CohortPrior:
    """
    Prior distribution for a cohort.
    """
    cohort_id: str
    name: str
    sector: Optional[str]
    region: Optional[str]
    size_indicator: Optional[str]

    # Prior statistics
    prior_band: ExposureBand
    prior_score_mean: float
    prior_score_std: float

    # Sample statistics
    sample_count: int = 0
    observed_mean: Optional[float] = None
    observed_std: Optional[float] = None

    # Confidence in prior
    prior_confidence: float = 0.5

    # Last updated
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CohortMatch:
    """
    Result of cohort matching for an entity.
    """
    cohort_id: str
    cohort_name: str
    match_confidence: float
    match_criteria: Dict[str, str] = field(default_factory=dict)
    prior: Optional[CohortPrior] = None


# =============================================================================
# AUTO-APPLY RULE TYPES
# =============================================================================

@dataclass
class ExposureRuleResult:
    """
    Result of evaluating an auto-apply rule.
    """
    rule_id: str
    condition: str
    action: str
    triggered: bool
    reason: str = ""
    modifier: Optional[float] = None


@dataclass
class ExposureDecision:
    """
    Decision output from exposure assessment.
    """
    should_refer: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    exposure_modifier: float = 1.0
    complexity_modifier: float = 1.0
    combined_modifier: float = 1.0
    rule_results: List[ExposureRuleResult] = field(default_factory=list)
