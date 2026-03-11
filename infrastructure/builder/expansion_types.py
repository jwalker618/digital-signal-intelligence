"""
DSI Coverage Expansion Types

Structured spec format for coverage expansion phases.
An expansion spec captures all parameters needed to generate:
- Complete v2.2/v2.3 config YAML sub-configurations
- Signal architecture code (extractors, aggregators, inference functions)

The spec is the machine-consumable counterpart to a phase document.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(str, Enum):
    """How a signal is assessed."""
    THREE_LAYER = "three_layer"
    CATEGORICAL = "categorical"


class PricingMethod(str, Enum):
    """Pricing method for tier bands."""
    MULTIPLIER = "MULTIPLIER"
    PREMIUM_BASE = "PREMIUM_BASE"


class LimitConfigType(str, Enum):
    """Limit configuration mode."""
    BUNDLED = "BUNDLED"
    DECOUPLED = "DECOUPLED"


# =============================================================================
# SIGNAL DEFINITIONS
# =============================================================================

@dataclass
class CategoryFeature:
    """A single category option for a categorical signal."""
    cat: str
    label: str
    applied: float  # modifier factor


@dataclass
class ThreeLayerWeights:
    """Three-layer assessment weights for a signal within a group."""
    risk_direction: str = "positive"
    risk_weight: float = 0.0
    loss_frequency_direction: str = "positive"
    loss_frequency_weight: float = 0.0
    loss_severity_direction: str = "positive"
    loss_severity_weight: float = 0.0
    exposure_size_direction: str = "positive"
    exposure_size_weight: float = 0.0
    exposure_complexity_direction: str = "positive"
    exposure_complexity_weight: float = 0.0
    score_conditions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SignalSpec:
    """Specification for a single signal."""
    id: str
    name: str
    description: str
    group_id: str
    proxy_tier: str = "INFERRED_PROXY"  # DIRECT_OBSERVABLE | INFERRED_PROXY | COHORT_INFERENCE
    signal_type: SignalType = SignalType.THREE_LAYER

    # For THREE_LAYER signals
    three_layer: Optional[ThreeLayerWeights] = None

    # For CATEGORICAL signals
    categories: Optional[List[CategoryFeature]] = None
    category_source: Optional[str] = None  # e.g. "metadata.operator_type"

    # Code generation hints
    extractor_fields: Dict[str, str] = field(default_factory=dict)  # field_name -> type hint
    ttl: str = "WEEKLY"  # DAILY | WEEKLY | MONTHLY


@dataclass
class SignalGroupSpec:
    """Specification for a new signal group introduced by this expansion."""
    id: str
    label: str
    description: str
    group_type: str = "three_layer_assessment"  # three_layer_assessment | categories
    signals: List[SignalSpec] = field(default_factory=list)


# =============================================================================
# DIRECT QUERY DEFINITIONS
# =============================================================================

@dataclass
class QueryCondition:
    """A condition-action pair for a direct query."""
    return_value: bool = True
    action: str = "REFER"  # FLAG | MODIFIER | REFER
    override: Optional[int] = None
    applied: Optional[float] = None
    note: str = ""


@dataclass
class DirectQuerySpec:
    """Specification for a direct query."""
    id: str
    question: str
    conditions: List[QueryCondition] = field(default_factory=list)


# =============================================================================
# TIER BAND DEFINITIONS
# =============================================================================

@dataclass
class RiskTierRate:
    """Simplified risk tier definition — generator expands to full structure."""
    rate: float  # e.g. 0.0008 for PREFERRED
    basis: str = "tiv"  # tiv | revenue | premium


@dataclass
class RiskTierBands:
    """Risk tier band configuration.

    Five standard tiers with customizable score boundaries and rates.
    """
    preferred_min: int = 800
    standard_plus_min: int = 650
    standard_min: int = 500
    substandard_min: int = 350
    # DECLINE is always 0 to substandard_min-1

    preferred_rate: float = 0.0008
    standard_plus_rate: float = 0.0012
    standard_rate: float = 0.0018
    substandard_rate: float = 0.0028
    decline_rate: float = 0.0045

    method: str = "MULTIPLIER"
    basis: str = "tiv"


@dataclass
class LossTierBands:
    """Loss tier band configuration — standard 5-tier structure.

    Uses default modifiers unless overridden.
    """
    floor: float = 0.55
    cap: float = 1.6
    # Standard modifiers (most configs use these defaults)
    very_low_freq: float = 0.7
    very_low_sev: float = 0.8
    low_freq: float = 0.85
    low_sev: float = 0.9
    moderate_freq: float = 1.0
    moderate_sev: float = 1.0
    elevated_freq: float = 1.15
    elevated_sev: float = 1.15
    high_freq: float = 1.35
    high_sev: float = 1.4


@dataclass
class ExposureBands:
    """Exposure band configuration.

    Size and complexity sub-dimensions with standard 5-tier structure.
    """
    size_weight: float = 0.6
    complexity_weight: float = 0.4

    # Size implied thresholds (dollar values)
    size_thresholds: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"label": "MICRO", "max_value": 1_000_000, "applied": 0.5},
        {"label": "SMALL", "max_value": 10_000_000, "applied": 0.75},
        {"label": "MEDIUM", "max_value": 50_000_000, "applied": 1.0},
        {"label": "LARGE", "max_value": 250_000_000, "applied": 1.5},
        {"label": "VERY_LARGE", "max_value": 1_000_000_000, "applied": 2.5},
    ])

    # Complexity modifiers (standard across most configs)
    complexity_modifiers: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"label": "SIMPLE", "applied": 0.85},
        {"label": "MODERATE", "applied": 0.95},
        {"label": "COMPLEX", "applied": 1.1},
        {"label": "HIGHLY_COMPLEX", "applied": 1.3},
        {"label": "EXTREMELY_COMPLEX", "applied": 1.6},
    ])


# =============================================================================
# PRICING DEFINITIONS
# =============================================================================

@dataclass
class ILFCurve:
    """Increased Limit Factor curve for a product type."""
    base_limit: int = 10_000_000
    factors: List[Dict[str, Any]] = field(default_factory=list)
    # Each factor: {"limit": int, "factor": float}


@dataclass
class ProductPricing:
    """Pricing for a specific product type."""
    product_type: str
    ilf_curve: ILFCurve = field(default_factory=ILFCurve)
    deductible_factors: List[Dict[str, float]] = field(default_factory=list)
    # Each: {"deductible": int, "factor": float}
    curve_type: str = "standard"  # "flat" for first-party, "standard" for liability


@dataclass
class PricingSpec:
    """Complete pricing configuration."""
    base_limit_reference: int = 10_000_000
    base_deductible_reference: int = 50_000
    taxes_fees_rate: float = 0.05
    by_product_type: List[ProductPricing] = field(default_factory=list)


# =============================================================================
# LIMIT CONFIGURATION
# =============================================================================

@dataclass
class LimitConfiguration:
    """Limit/deductible configuration."""
    type: LimitConfigType = LimitConfigType.DECOUPLED
    valid_limits: List[int] = field(default_factory=lambda: [
        5_000_000, 10_000_000, 25_000_000, 50_000_000,
        100_000_000, 250_000_000, 500_000_000, 1_000_000_000,
    ])
    valid_deductibles: List[int] = field(default_factory=lambda: [
        10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000,
    ])
    # BUNDLED packages (only used when type=BUNDLED)
    packages: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# GROUP WEIGHT DEFINITIONS
# =============================================================================

@dataclass
class GroupWeights:
    """Three-layer assessment weights for a signal group within a configuration."""
    group_id: str
    risk_weight: float = 0.0
    loss_weight: float = 0.0
    exposure_weight: float = 0.0
    score_conditions: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# ROUTING
# =============================================================================

@dataclass
class RoutingConstraint:
    """Multiplexer routing constraint."""
    field: str
    operator: str  # ==, !=, <, >, <=, >=, IN
    value: Any
    required_in_input: bool = False


# =============================================================================
# CONFIGURATION SPEC (per sub-configuration)
# =============================================================================

@dataclass
class ConfigurationSpec:
    """Specification for a single sub-configuration within the expansion."""
    id: str
    name: str
    description: str

    # Routing
    model_specificity: int = 2
    routing_constraints: List[RoutingConstraint] = field(default_factory=list)

    # Override defaults
    min_premium: Optional[int] = None
    product_types: Optional[List[str]] = None
    applicable_markets: Optional[List[str]] = None
    minimum_viable_input: Optional[List[Dict[str, str]]] = None

    # Direct queries (config-specific)
    direct_queries: List[DirectQuerySpec] = field(default_factory=list)

    # Signals — IDs of signals to include (from new_signal_groups + inherited)
    # If empty, inherits all signals from the base config
    inherit_signals_from: Optional[str] = None  # e.g. "pi_general"
    additional_signals: List[str] = field(default_factory=list)  # signal IDs to add
    exclude_signals: List[str] = field(default_factory=list)  # signal IDs to remove
    signal_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # signal_id -> weight overrides

    # Group weights for this config
    group_weights: List[GroupWeights] = field(default_factory=list)

    # Category groups for this config (references to categorical group definitions)
    category_groups: List[str] = field(default_factory=list)

    # Tier bands
    risk_tier_bands: Optional[RiskTierBands] = None
    loss_tier_bands: Optional[LossTierBands] = None
    exposure_bands: Optional[ExposureBands] = None

    # Pricing
    limit_configuration: Optional[LimitConfiguration] = None
    pricing: Optional[PricingSpec] = None


# =============================================================================
# TOP-LEVEL EXPANSION SPEC
# =============================================================================

@dataclass
class ExpansionSpec:
    """Top-level expansion specification.

    This is the primary input to the CoverageExpansionGenerator.
    One spec per expansion phase (e.g., Phase 6 = PI expansion).
    """
    # Identity
    coverage_line: str  # e.g. "energy", "professional_indemnity", "cyber"
    coverage_key: str   # top-level YAML key, e.g. "energy", "professional_indemnity"
    phase: str          # e.g. "phase_6"
    description: str
    version: str = "2.3.0"

    # Shared defaults (applied to all configs unless overridden)
    default_product_types: List[str] = field(default_factory=list)
    default_markets: List[str] = field(default_factory=lambda: ["us", "uk", "eu", "apac"])
    default_currency: str = "USD"
    default_min_premium: int = 25000
    default_minimum_viable_input: List[Dict[str, str]] = field(default_factory=list)

    # Routing field name (e.g. "operation_segment", "profession_segment", "industry_sector")
    routing_field: str = ""

    # New signal groups introduced by this expansion
    new_signal_groups: List[SignalGroupSpec] = field(default_factory=list)

    # New categorical groups (not signal groups — these are modifier groups like operator_type)
    new_category_groups: List[Dict[str, Any]] = field(default_factory=list)

    # Configurations to generate
    configurations: List[ConfigurationSpec] = field(default_factory=list)

    # Default tier bands (configs can override)
    default_risk_tier_bands: Optional[RiskTierBands] = None
    default_loss_tier_bands: Optional[LossTierBands] = None
    default_exposure_bands: Optional[ExposureBands] = None
    default_limit_configuration: Optional[LimitConfiguration] = None

    # Default pricing template
    default_pricing: Optional[PricingSpec] = None


# =============================================================================
# GENERATION RESULT
# =============================================================================

@dataclass
class ExpansionResult:
    """Result of running the expansion generator."""
    success: bool
    config_yaml: str = ""
    generated_files: Dict[str, str] = field(default_factory=dict)  # path -> content
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
