"""
DSI Pydantic Configuration Schema (Version 4 - Phase 1)

Strongly-typed Pydantic models mirroring master_config_layout.yaml v2.3.
Provides O(1) attribute access, IDE autocomplete, and boot-time validation.

All raw dictionary lookups are replaced with typed dot notation:
  OLD: config.get("pricing", {}).get("base_limit_reference")
  NEW: config.pricing.base_limit_reference
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================

class ProxyTier(str, Enum):
    """Signal data quality tier."""
    DIRECT_OBSERVABLE = "DIRECT_OBSERVABLE"
    INFERRED_PROXY = "INFERRED_PROXY"
    COHORT_INFERENCE = "COHORT_INFERENCE"


class CorrelationDirection(str, Enum):
    """How signal score correlates with risk."""
    POSITIVE = "positive"  # High score = good
    NEGATIVE = "negative"  # High score = bad


class ScoreConditionAction(str, Enum):
    """Actions for score_conditions (not DECLINE - that's tier-level only)."""
    FLAG = "FLAG"
    MODIFIER = "MODIFIER"
    REFER = "REFER"


class TierAction(str, Enum):
    """Actions for tier bands (includes DECLINE)."""
    APPROVE = "APPROVE"
    REFER = "REFER"
    DECLINE = "DECLINE"


class ComparisonOperator(str, Enum):
    """Comparison operators for constraints and conditions."""
    LT = "<"
    GT = ">"
    LTE = "<="
    GTE = ">="
    EQ = "=="
    NEQ = "!="


class ExpectationLevel(str, Enum):
    """Signal expectation levels for adaptive absence handling (Phase 10)."""
    UNIVERSAL = "UNIVERSAL"    # Expected for ALL entities
    ENTERPRISE = "ENTERPRISE"  # Expected for Large/Complex (bands 4-5)
    CORPORATE = "CORPORATE"    # Expected for Medium+ (bands 3-5)
    SME = "SME"                # Expected for Small+ (bands 2-5)
    MICRO = "MICRO"            # Expected only for Micro (band 1)


class LimitConfigType(str, Enum):
    """Limit configuration modes."""
    BUNDLED = "BUNDLED"      # Menu pricing with packages
    DECOUPLED = "DECOUPLED"  # Independent limit/deductible selection


class PricingMethod(str, Enum):
    """Premium calculation methods."""
    PREMIUM_BASE = "PREMIUM_BASE"  # Fixed base premium per tier
    MULTIPLIER = "MULTIPLIER"      # Rate applied to basis value
    MODIFIER = "MODIFIER"          # Multiplicative factor


# =============================================================================
# SCORE CONDITIONS
# =============================================================================

class ScoreCondition(BaseModel):
    """Banded score condition for signals and groups."""
    threshold: int
    comparison: ComparisonOperator
    action: ScoreConditionAction
    applied: Optional[float] = None  # Required for MODIFIER
    override: Optional[int] = None   # Optional tier override for REFER
    note: Optional[str] = None       # Required for FLAG

    @model_validator(mode="after")
    def validate_action_requirements(self) -> "ScoreCondition":
        if self.action == ScoreConditionAction.MODIFIER and self.applied is None:
            raise ValueError("MODIFIER action requires 'applied' value")
        if self.action == ScoreConditionAction.FLAG and not self.note:
            raise ValueError("FLAG action requires 'note'")
        return self


# =============================================================================
# METADATA
# =============================================================================

class MinimumViableInputField(BaseModel):
    """Required input field specification."""
    field: str
    description: str


class RoutingConstraint(BaseModel):
    """Hard filter for multiplexer candidate selection."""
    field: str
    operator: ComparisonOperator
    value: Union[int, float, str]
    required_in_input: bool = False


class ConfigMetadata(BaseModel):
    """Configuration metadata block."""
    name: str
    description: Optional[str] = None
    version: str
    product_types: List[str]
    applicable_markets: List[str] = Field(default_factory=list)
    minimum_viable_input: Optional[List[MinimumViableInputField]] = None
    min_premium: int = 0
    default_currency: str = "USD"

    # Multiplexer support (Phase V4)
    model_specificity: int = Field(default=1, ge=1, le=5)
    routing_constraints: List[RoutingConstraint] = Field(default_factory=list)


# =============================================================================
# DIRECT QUERIES
# =============================================================================

class QueryCondition(BaseModel):
    """Condition for a direct query response."""
    # Return value is the trigger (True/False from user)
    return_value: bool = Field(alias="return")
    action: ScoreConditionAction
    override: Optional[int] = None
    applied: Optional[float] = None
    note: Optional[str] = None

    class Config:
        populate_by_name = True


class DirectQuery(BaseModel):
    """Binary question that cannot be externally observed."""
    id: str
    question: str
    query_condition: List[QueryCondition]


# =============================================================================
# SIGNAL REGISTRY - CATEGORICAL
# =============================================================================

class CategoryFeature(BaseModel):
    """Category value and its pricing impact."""
    cat: str
    label: Optional[str] = None
    applied: Optional[float] = None  # Pricing modifier
    value: Optional[float] = None    # Base premium value


class SignalCategories(BaseModel):
    """Categorical signal definition."""
    group_id: str
    source: Optional[str] = None  # e.g., "metadata.field_name"
    features: List[CategoryFeature]


# =============================================================================
# SIGNAL REGISTRY - THREE LAYER ASSESSMENT
# =============================================================================

class MetadataBand(BaseModel):
    """Numeric metadata band mapping."""
    min: int
    max: Optional[int] = None  # None = no upper limit
    score: int = Field(ge=0, le=100)


class MetadataCategory(BaseModel):
    """Text metadata category mapping."""
    match: Optional[str] = None  # None = default/catch-all
    score: int = Field(ge=0, le=100)


class DimensionBlock(BaseModel):
    """Single dimension within three-layer assessment."""
    source: Optional[str] = None  # Default: "score"
    bands: Optional[List[MetadataBand]] = None  # For numeric metadata
    categories: Optional[List[MetadataCategory]] = None  # For text metadata
    correlation_direction: CorrelationDirection = CorrelationDirection.POSITIVE
    weight: float = Field(ge=0.0, le=1.0)
    score_conditions: Optional[List[ScoreCondition]] = None


class LossDimension(BaseModel):
    """Loss dimension with frequency and severity."""
    frequency: Optional[DimensionBlock] = None
    severity: Optional[DimensionBlock] = None


class ExposureDimension(BaseModel):
    """Exposure dimension with size and complexity."""
    size: Optional[DimensionBlock] = None
    complexity: Optional[DimensionBlock] = None


class ThreeLayerAssessment(BaseModel):
    """Three-layer assessment block for a signal."""
    group_id: str
    risk: Optional[DimensionBlock] = None
    loss: Optional[LossDimension] = None
    exposure: Optional[ExposureDimension] = None


# =============================================================================
# SIGNAL REGISTRY - COMPLETE SIGNAL
# =============================================================================

class SignalDefinition(BaseModel):
    """Complete signal definition in signal_registry."""
    id: str
    inference_utility_function: str
    proxy_tier: ProxyTier = ProxyTier.INFERRED_PROXY
    expectation_level: ExpectationLevel = ExpectationLevel.UNIVERSAL

    # Either categories OR three_layer_assessment
    categories: Optional[SignalCategories] = None
    three_layer_assessment: Optional[ThreeLayerAssessment] = None

    @model_validator(mode="after")
    def validate_signal_type(self) -> "SignalDefinition":
        if not self.categories and not self.three_layer_assessment:
            raise ValueError(
                f"Signal '{self.id}' must have either 'categories' or 'three_layer_assessment'"
            )
        return self


# =============================================================================
# GROUPS
# =============================================================================

class CategoryGroup(BaseModel):
    """Categorical group definition."""
    id: str
    label: str
    description: Optional[str] = None
    impact: Literal["MODIFIER", "PREMIUM_BASE"] = "MODIFIER"
    default_cat: str


class GroupDimension(BaseModel):
    """Dimension block for a three-layer assessment group."""
    weight: float = Field(ge=0.0, le=1.0)
    score_conditions: Optional[List[ScoreCondition]] = None


class ThreeLayerAssessmentGroup(BaseModel):
    """Three-layer assessment group definition."""
    id: str
    label: Optional[str] = None
    description: Optional[str] = None
    risk: Optional[GroupDimension] = None
    loss: Optional[GroupDimension] = None
    exposure: Optional[GroupDimension] = None


class Groups(BaseModel):
    """Groups section containing categories and three-layer assessment."""
    categories: List[CategoryGroup] = Field(default_factory=list)
    three_layer_assessment: List[ThreeLayerAssessmentGroup] = Field(default_factory=list)


# =============================================================================
# TIER BANDS
# =============================================================================

class TierBandRange(BaseModel):
    """Score range for a tier band."""
    min: int
    max: int


class RiskTierApplication(BaseModel):
    """Application block for risk tier."""
    method: PricingMethod = PricingMethod.PREMIUM_BASE
    value: Optional[int] = None    # For PREMIUM_BASE
    applied: Optional[float] = None  # For MULTIPLIER
    basis: Optional[str] = None      # For MULTIPLIER


class RiskTierInterpretation(BaseModel):
    """Interpretation block for risk tier."""
    bands: TierBandRange
    action: TierAction
    application: RiskTierApplication


class RiskTierBand(BaseModel):
    """Single risk tier band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: RiskTierInterpretation


class RiskTierBands(BaseModel):
    """Risk tier bands section."""
    bands: List[RiskTierBand]

    def get_tier_for_score(self, score: float) -> int:
        """Get tier ID for a given composite score."""
        for band in self.bands:
            if band.interpretation.bands.min <= score <= band.interpretation.bands.max:
                return band.id
        return self.bands[-1].id  # Default to last tier


class LossTierApplication(BaseModel):
    """Application block for loss tier."""
    frequency_modifier: float
    severity_modifier: float


class LossTierInterpretation(BaseModel):
    """Interpretation block for loss tier."""
    bands: TierBandRange
    application: LossTierApplication


class LossTierBand(BaseModel):
    """Single loss tier band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: LossTierInterpretation


class LossTierConstraints(BaseModel):
    """Loss tier modifier constraints."""
    floor: float = 0.75
    cap: float = 1.50


class LossTierBands(BaseModel):
    """Loss tier bands section."""
    bands: List[LossTierBand]
    constraints: LossTierConstraints = Field(default_factory=LossTierConstraints)


# =============================================================================
# EXPOSURE
# =============================================================================

class ExposureBandApplication(BaseModel):
    """Application block for exposure band."""
    method: PricingMethod = PricingMethod.MODIFIER
    applied: float
    basis: Optional[str] = None
    implied_thresholds: Optional[Dict[str, Optional[int]]] = None


class ExposureBandInterpretation(BaseModel):
    """Interpretation block for exposure band."""
    bands: TierBandRange
    application: ExposureBandApplication


class ExposureBand(BaseModel):
    """Single exposure band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: ExposureBandInterpretation


class ExposureDimensionConfig(BaseModel):
    """Exposure dimension configuration (size or complexity)."""
    weight: float = Field(ge=0.0, le=1.0)
    bands: List[ExposureBand]


class Exposure(BaseModel):
    """Exposure section with size and complexity."""
    size: ExposureDimensionConfig
    complexity: ExposureDimensionConfig

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "Exposure":
        total = self.size.weight + self.complexity.weight
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Exposure weights must sum to 1.0, got {total}")
        return self


# =============================================================================
# LIMIT CONFIGURATION
# =============================================================================

class LimitPackage(BaseModel):
    """Bundled limit/deductible package."""
    id: int
    label: str
    limit: int
    deductible: int


class LimitConfiguration(BaseModel):
    """Limit and deductible configuration."""
    type: LimitConfigType = LimitConfigType.DECOUPLED

    # For BUNDLED mode
    packages: Optional[List[LimitPackage]] = None

    # For DECOUPLED mode
    valid_limits: Optional[List[int]] = None
    valid_deductibles: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_mode(self) -> "LimitConfiguration":
        if self.type == LimitConfigType.BUNDLED and not self.packages:
            raise ValueError("BUNDLED mode requires 'packages'")
        if self.type == LimitConfigType.DECOUPLED:
            if not self.valid_limits or not self.valid_deductibles:
                raise ValueError("DECOUPLED mode requires 'valid_limits' and 'valid_deductibles'")
        return self


# =============================================================================
# PRICING
# =============================================================================

class ILFCurveFactor(BaseModel):
    """Single point on ILF curve."""
    limit: int
    factor: float


class ILFCurve(BaseModel):
    """Increased Limit Factor curve."""
    base_limit: int
    factors: List[ILFCurveFactor]

    def get_factor_for_limit(self, limit: int) -> float:
        """Get ILF factor for a given limit (with interpolation)."""
        if not self.factors:
            return 1.0

        # Find exact match or interpolate
        for f in self.factors:
            if f.limit == limit:
                return f.factor

        # Simple linear interpolation
        sorted_factors = sorted(self.factors, key=lambda x: x.limit)

        # Below minimum
        if limit < sorted_factors[0].limit:
            return sorted_factors[0].factor

        # Above maximum
        if limit > sorted_factors[-1].limit:
            return sorted_factors[-1].factor

        # Find bracket and interpolate
        for i in range(len(sorted_factors) - 1):
            if sorted_factors[i].limit <= limit <= sorted_factors[i + 1].limit:
                low = sorted_factors[i]
                high = sorted_factors[i + 1]
                ratio = (limit - low.limit) / (high.limit - low.limit)
                return low.factor + ratio * (high.factor - low.factor)

        return 1.0


class DeductibleFactor(BaseModel):
    """Deductible adjustment factor."""
    deductible: int
    factor: float


class ProductTypePricing(BaseModel):
    """Pricing parameters for a product type."""
    ilf_curve: ILFCurve
    deductible_factors: List[DeductibleFactor]

    def get_deductible_factor(self, deductible: int) -> float:
        """Get deductible factor for a given deductible."""
        for f in self.deductible_factors:
            if f.deductible == deductible:
                return f.factor
        # Default to 1.0 if not found
        return 1.0


class Pricing(BaseModel):
    """Pricing section."""
    base_limit_reference: int
    base_deductible_reference: int
    by_product_type: Dict[str, ProductTypePricing]
    taxes_fees_rate: float = 0.05

    @field_validator("by_product_type")
    @classmethod
    def validate_anchor_presence(cls, v: Dict[str, ProductTypePricing], info) -> Dict[str, ProductTypePricing]:
        """Ensure base_limit_reference exists in every ILF curve with factor 1.0."""
        # Note: Can't access base_limit_reference in field_validator
        # Full validation done in CoverageConfig model_validator
        return v


# =============================================================================
# COMPLETE COVERAGE CONFIG
# =============================================================================

class CoverageConfig(BaseModel):
    """
    Complete coverage configuration.

    This is the top-level model representing a single configuration
    within a coverage (e.g., cyber_general within cyber).
    """
    metadata: ConfigMetadata
    direct_queries: List[DirectQuery] = Field(default_factory=list)
    signal_registry: List[SignalDefinition] = Field(default_factory=list)
    groups: Groups = Field(default_factory=Groups)
    risk_tier_bands: RiskTierBands
    loss_tier_bands: LossTierBands
    exposure: Exposure
    limit_configuration: Optional[LimitConfiguration] = None
    pricing: Pricing

    @model_validator(mode="after")
    def validate_cross_references(self) -> "CoverageConfig":
        """Validate cross-references between sections."""
        errors = []

        # Collect group IDs from signal registry
        signal_group_ids = set()
        for sig in self.signal_registry:
            if sig.three_layer_assessment:
                signal_group_ids.add(sig.three_layer_assessment.group_id)
            if sig.categories:
                signal_group_ids.add(sig.categories.group_id)

        # Collect defined group IDs
        defined_groups = set()
        for cat in self.groups.categories:
            defined_groups.add(cat.id)
        for tla in self.groups.three_layer_assessment:
            defined_groups.add(tla.id)

        # Check for missing groups
        missing = signal_group_ids - defined_groups
        if missing:
            errors.append(f"Signal registry references undefined groups: {missing}")

        # Validate ILF anchor
        base_limit = self.pricing.base_limit_reference
        for prod_name, prod_pricing in self.pricing.by_product_type.items():
            anchor_factor = None
            for f in prod_pricing.ilf_curve.factors:
                if f.limit == base_limit:
                    anchor_factor = f.factor
                    break
            if anchor_factor is None:
                errors.append(
                    f"Product '{prod_name}' ILF curve missing base_limit_reference ({base_limit})"
                )
            elif anchor_factor != 1.0:
                errors.append(
                    f"Product '{prod_name}' ILF anchor at {base_limit} should be 1.0, got {anchor_factor}"
                )

        # Validate deductible anchor
        base_ded = self.pricing.base_deductible_reference
        for prod_name, prod_pricing in self.pricing.by_product_type.items():
            anchor_factor = None
            for f in prod_pricing.deductible_factors:
                if f.deductible == base_ded:
                    anchor_factor = f.factor
                    break
            if anchor_factor is None:
                errors.append(
                    f"Product '{prod_name}' missing base_deductible_reference ({base_ded})"
                )
            elif anchor_factor != 1.0:
                errors.append(
                    f"Product '{prod_name}' deductible anchor at {base_ded} should be 1.0, got {anchor_factor}"
                )

        if errors:
            raise ValueError("Configuration validation errors: " + "; ".join(errors))

        return self

    # -------------------------------------------------------------------------
    # Convenience methods
    # -------------------------------------------------------------------------

    def get_tier_for_score(self, composite_score: float) -> int:
        """Get risk tier ID for a given composite score."""
        return self.risk_tier_bands.get_tier_for_score(composite_score)

    def get_tier_band(self, tier_id: int) -> Optional[RiskTierBand]:
        """Get tier band by ID."""
        for band in self.risk_tier_bands.bands:
            if band.id == tier_id:
                return band
        return None

    def get_signal(self, signal_id: str) -> Optional[SignalDefinition]:
        """Get signal definition by ID."""
        for sig in self.signal_registry:
            if sig.id == signal_id:
                return sig
        return None

    def get_group(self, group_id: str) -> Optional[ThreeLayerAssessmentGroup]:
        """Get three-layer assessment group by ID."""
        for grp in self.groups.three_layer_assessment:
            if grp.id == group_id:
                return grp
        return None

    def get_ilf(self, product_type: str, limit: int) -> float:
        """Get ILF factor for product type and limit."""
        if product_type not in self.pricing.by_product_type:
            return 1.0
        return self.pricing.by_product_type[product_type].ilf_curve.get_factor_for_limit(limit)

    def get_deductible_factor(self, product_type: str, deductible: int) -> float:
        """Get deductible factor for product type and deductible."""
        if product_type not in self.pricing.by_product_type:
            return 1.0
        return self.pricing.by_product_type[product_type].get_deductible_factor(deductible)


# =============================================================================
# COVERAGE WRAPPER
# =============================================================================

class Coverage(BaseModel):
    """
    Top-level coverage containing one or more configurations.

    Structure: coverage_id -> config_id -> CoverageConfig
    e.g., cyber -> cyber_general -> CoverageConfig
    """
    coverage_id: str
    configurations: Dict[str, CoverageConfig]

    def get_config(self, config_id: Optional[str] = None) -> CoverageConfig:
        """Get configuration by ID, defaulting to {coverage}_general."""
        if config_id is None:
            config_id = f"{self.coverage_id}_general"
        if config_id not in self.configurations:
            raise KeyError(f"Configuration '{config_id}' not found in coverage '{self.coverage_id}'")
        return self.configurations[config_id]
