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
from typing import Any, Callable, Dict, List, Literal, Optional, Union

import logging
import math

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_logger = logging.getLogger("dsi.config_schema")


class StrictModel(BaseModel):
    """Base model that rejects unknown fields in YAML config."""
    model_config = ConfigDict(extra="forbid")


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
    APPROVE_WITH_FLAG = "APPROVE_WITH_FLAG"


class ComparisonOperator(str, Enum):
    """Comparison operators for constraints and conditions."""
    LT = "<"
    GT = ">"
    LTE = "<="
    GTE = ">="
    EQ = "=="
    NEQ = "!="
    IN = "in"  # Membership test for list values


class ExpectationLevel(str, Enum):
    """Signal expectation levels for adaptive absence handling (Phase 10)."""
    UNIVERSAL = "UNIVERSAL"    # Expected for ALL entities
    ENTERPRISE = "ENTERPRISE"  # Expected for Large/Complex (bands 4-5)
    CORPORATE = "CORPORATE"    # Expected for Medium+ (bands 3-5)
    SME = "SME"                # Expected for Small+ (bands 2-5)
    MICRO = "MICRO"            # Expected only for Micro (band 1)


class LimitConfigType(str, Enum):
    """Limit configuration modes.

    All coverage configs should use DECOUPLED. The pricer prices any
    limit/deductible within the config's min/max range; distribution
    structure (tower layers, subscription lines, bundled packages) is
    now a commercial concern defined in entity YAML.

    TOWER and SUBSCRIPTION are retained for backward compatibility
    with test fixtures and legacy configs but should not be used for
    new configurations.
    """
    BUNDLED = "BUNDLED"      # Menu pricing with packages
    DECOUPLED = "DECOUPLED"  # Independent limit/deductible selection
    TOWER = "TOWER"          # Stacked excess layers (legacy — use entity distribution)
    SUBSCRIPTION = "SUBSCRIPTION"  # Order/line subscription market (legacy — use entity distribution)


class LineRole(str, Enum):
    """Lead vs follow role on a subscription line."""
    LEAD = "LEAD"
    FOLLOW = "FOLLOW"


class PricingMethod(str, Enum):
    """Premium calculation methods."""
    PREMIUM_BASE = "PREMIUM_BASE"  # Fixed base premium per tier
    MULTIPLIER = "MULTIPLIER"      # Rate applied to basis value
    MODIFIER = "MODIFIER"          # Multiplicative factor


# =============================================================================
# SCORE CONDITIONS
# =============================================================================

class ScoreCondition(StrictModel):
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

class MinimumViableInputField(StrictModel):
    """Required input field specification."""
    field: str
    description: str = ""


class RoutingConstraint(StrictModel):
    """Hard filter for multiplexer candidate selection."""
    field: str
    operator: ComparisonOperator
    value: Union[int, float, str, List[str]]
    required_in_input: bool = False


class ConfigMetadata(StrictModel):
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

    @model_validator(mode="before")
    @classmethod
    def _unwrap_minimum_viable_input(cls, data: Any) -> Any:
        """Accept both flat list and nested {required: [...]} format for minimum_viable_input."""
        if isinstance(data, dict):
            mvi = data.get("minimum_viable_input")
            if isinstance(mvi, dict) and "required" in mvi:
                data["minimum_viable_input"] = mvi["required"]
        return data


# =============================================================================
# DIRECT QUERIES
# =============================================================================

class QueryCondition(StrictModel):
    """Condition for a direct query response."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Return value is the trigger (True/False from user)
    return_value: bool = Field(alias="return")
    action: ScoreConditionAction
    override: Optional[int] = None
    applied: Optional[float] = None
    note: Optional[str] = None


class DirectQuery(StrictModel):
    """Binary question that cannot be externally observed."""
    id: str
    question: str
    query_condition: List[QueryCondition]


# =============================================================================
# SIGNAL REGISTRY - CATEGORICAL
# =============================================================================

class CategoryFeature(StrictModel):
    """Category value and its pricing impact."""
    cat: str
    label: Optional[str] = None
    applied: Optional[float] = None  # Pricing modifier
    value: Optional[float] = None    # Base premium value


class SignalCategories(StrictModel):
    """Categorical signal definition."""
    group_id: str
    source: Optional[str] = None  # e.g., "metadata.field_name"
    features: List[CategoryFeature]


# =============================================================================
# SIGNAL REGISTRY - THREE LAYER ASSESSMENT
# =============================================================================

class MetadataBand(StrictModel):
    """Numeric metadata band mapping."""
    min: int
    max: Optional[int] = None  # None = no upper limit
    score: int = Field(ge=0, le=100)


class MetadataCategory(StrictModel):
    """Text metadata category mapping."""
    match: Optional[str] = None  # None = default/catch-all
    score: int = Field(ge=0, le=100)


class DimensionBlock(StrictModel):
    """Single dimension within three-layer assessment."""
    source: Optional[str] = None  # Default: "score"
    bands: Optional[List[MetadataBand]] = None  # For numeric metadata
    categories: Optional[List[MetadataCategory]] = None  # For text metadata
    correlation_direction: CorrelationDirection = CorrelationDirection.POSITIVE
    weight: float = Field(ge=0.0, le=1.0)
    score_conditions: Optional[List[ScoreCondition]] = None


class LossDimension(StrictModel):
    """Loss dimension with frequency and severity."""
    frequency: Optional[DimensionBlock] = None
    severity: Optional[DimensionBlock] = None


class ExposureDimension(StrictModel):
    """Exposure dimension with size and complexity."""
    size: Optional[DimensionBlock] = None
    complexity: Optional[DimensionBlock] = None


class ThreeLayerAssessment(StrictModel):
    """Three-layer assessment block for a signal."""
    group_id: str
    risk: Optional[DimensionBlock] = None
    loss: Optional[LossDimension] = None
    exposure: Optional[ExposureDimension] = None


# =============================================================================
# SIGNAL REGISTRY - COMPLETE SIGNAL
# =============================================================================

class SignalDefinition(StrictModel):
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

class CategoryGroup(StrictModel):
    """Categorical group definition."""
    id: str
    label: str
    description: Optional[str] = None
    impact: Literal["MODIFIER", "PREMIUM_BASE"] = "MODIFIER"
    default_cat: str


class GroupDimension(StrictModel):
    """Dimension block for a three-layer assessment group."""
    weight: float = Field(ge=0.0, le=1.0)
    score_conditions: Optional[List[ScoreCondition]] = None


class ThreeLayerAssessmentGroup(StrictModel):
    """Three-layer assessment group definition."""
    id: str
    label: Optional[str] = None
    description: Optional[str] = None
    risk: Optional[GroupDimension] = None
    loss: Optional[GroupDimension] = None
    exposure: Optional[GroupDimension] = None


class Groups(StrictModel):
    """Groups section containing categories and three-layer assessment."""
    categories: List[CategoryGroup] = Field(default_factory=list)
    three_layer_assessment: List[ThreeLayerAssessmentGroup] = Field(default_factory=list)


# =============================================================================
# TIER BANDS
# =============================================================================

class TierBandRange(StrictModel):
    """Score range for a tier band."""
    min: int
    max: int


class RiskTierApplication(StrictModel):
    """Application block for risk tier."""
    method: PricingMethod = PricingMethod.PREMIUM_BASE
    value: Optional[int] = None    # For PREMIUM_BASE
    applied: Optional[float] = None  # For MULTIPLIER
    basis: Optional[str] = None      # For MULTIPLIER


class RiskTierInterpretation(StrictModel):
    """Interpretation block for risk tier."""
    bands: TierBandRange
    action: TierAction
    application: RiskTierApplication


class RiskTierBand(StrictModel):
    """Single risk tier band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: RiskTierInterpretation


class RiskTierBands(StrictModel):
    """Risk tier bands section."""
    bands: List[RiskTierBand]

    def get_tier_for_score(self, score: float) -> int:
        """Get tier ID for a given composite score."""
        for band in self.bands:
            if band.interpretation.bands.min <= score <= band.interpretation.bands.max:
                return band.id
        return self.bands[-1].id  # Default to last tier


class LossTierApplication(StrictModel):
    """Application block for loss tier."""
    frequency_modifier: float
    severity_modifier: float


class LossTierInterpretation(StrictModel):
    """Interpretation block for loss tier."""
    bands: TierBandRange
    application: LossTierApplication


class LossTierBand(StrictModel):
    """Single loss tier band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: LossTierInterpretation


class LossTierConstraints(StrictModel):
    """Loss tier modifier constraints."""
    floor: float = 0.75
    cap: float = 1.50


class LossTierBands(StrictModel):
    """Loss tier bands section."""
    bands: List[LossTierBand]
    constraints: LossTierConstraints = Field(default_factory=LossTierConstraints)


# =============================================================================
# EXPOSURE
# =============================================================================

class ExposureBandApplication(StrictModel):
    """Application block for exposure band."""
    method: PricingMethod = PricingMethod.MODIFIER
    applied: float
    basis: Optional[str] = None
    implied_thresholds: Optional[Dict[str, Optional[int]]] = None


class ExposureBandInterpretation(StrictModel):
    """Interpretation block for exposure band."""
    bands: TierBandRange
    application: ExposureBandApplication
    implied_thresholds: Optional[Dict[str, Optional[int]]] = None  # Some configs place this here


class ExposureBand(StrictModel):
    """Single exposure band definition."""
    id: int
    label: str
    description: Optional[str] = None
    interpretation: ExposureBandInterpretation


class ExposureDimensionConfig(StrictModel):
    """Exposure dimension configuration (size or complexity)."""
    weight: float = Field(ge=0.0, le=1.0)
    bands: List[ExposureBand]


class Exposure(StrictModel):
    """Exposure section with size and complexity."""
    size: Optional[ExposureDimensionConfig] = None
    complexity: Optional[ExposureDimensionConfig] = None

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "Exposure":
        if self.size is None or self.complexity is None:
            return self
        total = self.size.weight + self.complexity.weight
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Exposure weights must sum to 1.0, got {total}")
        return self


# =============================================================================
# LIMIT CONFIGURATION
# =============================================================================

class LimitPackage(StrictModel):
    """Bundled limit/deductible package."""
    id: Union[int, str]
    label: str
    limit: int
    deductible: int
    target_segment: Optional[str] = None  # Optional description of target segment


class TowerLayer(StrictModel):
    """A single layer in a tower (excess-of-loss) structure."""
    id: int
    label: str
    attachment: int = Field(ge=0)
    limit: int = Field(gt=0)


class SubscriptionOrder(StrictModel):
    """Order-level terms for a subscription market (100% basis)."""
    total_limit: int = Field(gt=0)
    order_premium: Optional[float] = None  # Set by pricing engine if not explicit


class SubscriptionLine(StrictModel):
    """Insurer's line on a subscription order."""
    minimum_line: float = Field(gt=0.0, le=1.0)
    maximum_line: float = Field(gt=0.0, le=1.0)
    signed_line: Optional[float] = None  # Actual signed %, between min and max
    role: LineRole = LineRole.FOLLOW

    @model_validator(mode="after")
    def validate_line_bounds(self) -> "SubscriptionLine":
        if self.maximum_line < self.minimum_line:
            raise ValueError(
                f"maximum_line ({self.maximum_line}) must be >= minimum_line ({self.minimum_line})"
            )
        if self.signed_line is not None:
            if not (self.minimum_line <= self.signed_line <= self.maximum_line):
                raise ValueError(
                    f"signed_line ({self.signed_line}) must be between "
                    f"minimum_line ({self.minimum_line}) and maximum_line ({self.maximum_line})"
                )
        return self


class LimitConfiguration(StrictModel):
    """Limit and deductible configuration."""
    type: LimitConfigType = LimitConfigType.DECOUPLED

    # For BUNDLED mode
    packages: Optional[List[LimitPackage]] = None

    # For DECOUPLED mode — programmatic limit generation
    min_limit: Optional[int] = None
    max_limit: Optional[int] = None

    # Deductible range (replaces hard valid_deductibles list)
    # The pricer interpolates between deductible_factors reference points
    min_deductible: Optional[int] = None
    max_deductible: Optional[int] = None

    # Legacy: explicit lists (still supported, overrides min/max)
    valid_limits: Optional[List[int]] = None
    valid_deductibles: Optional[List[int]] = None  # deprecated: use min/max_deductible

    # For TOWER mode — stacked excess layers (bespoke bandings supported)
    layers: Optional[List[TowerLayer]] = None

    # For SUBSCRIPTION mode — order/line model
    subscription_order: Optional[SubscriptionOrder] = None
    subscription_line: Optional[SubscriptionLine] = None

    @model_validator(mode="after")
    def validate_mode(self) -> "LimitConfiguration":
        if self.type == LimitConfigType.BUNDLED and not self.packages:
            raise ValueError("BUNDLED mode requires 'packages'")
        if self.type == LimitConfigType.DECOUPLED:
            has_range = self.min_limit is not None and self.max_limit is not None
            has_list = self.valid_limits is not None and len(self.valid_limits) > 0
            if not has_range and not has_list:
                raise ValueError(
                    "DECOUPLED mode requires either (min_limit + max_limit) "
                    "or valid_limits"
                )
            has_ded_range = self.min_deductible is not None and self.max_deductible is not None
            has_ded_list = self.valid_deductibles is not None and len(self.valid_deductibles) > 0
            if not has_ded_range and not has_ded_list:
                raise ValueError(
                    "DECOUPLED mode requires either (min_deductible + max_deductible) "
                    "or valid_deductibles"
                )
        if self.type == LimitConfigType.TOWER:
            if not self.layers or len(self.layers) == 0:
                raise ValueError("TOWER mode requires 'layers'")
            self._validate_tower_layers()
        if self.type == LimitConfigType.SUBSCRIPTION:
            if not self.subscription_order:
                raise ValueError("SUBSCRIPTION mode requires 'subscription_order'")
        return self

    def _validate_tower_layers(self) -> None:
        """Validate bespoke tower layer ordering and no overlaps."""
        if not self.layers:
            return
        sorted_layers = sorted(self.layers, key=lambda l: l.attachment)
        for i, layer in enumerate(sorted_layers):
            if i > 0:
                prev = sorted_layers[i - 1]
                prev_top = prev.attachment + prev.limit
                if layer.attachment < prev_top:
                    raise ValueError(
                        f"Tower layers overlap: layer '{prev.label}' ends at {prev_top} "
                        f"but layer '{layer.label}' attaches at {layer.attachment}"
                    )

    def generate_limit_options(self, requested_limit: Optional[int] = None) -> List[int]:
        """
        Generate contextual limit options around the requested limit.

        If valid_limits is explicitly set, returns those directly.
        Otherwise, generates a menu of standard limit options between
        min_limit and max_limit, centered around the requested limit.

        Returns:
            Sorted list of limit options
        """
        if self.valid_limits:
            return sorted(self.valid_limits)

        if self.min_limit is None or self.max_limit is None:
            return []

        # Generate standard limit steps between min and max
        # Steps follow market conventions: 1, 2, 3, 5, 10, 15, 20, 25, 50, 75, 100 × base
        standard_multipliers = [
            0.25, 0.5, 1, 2, 3, 5, 7.5, 10, 15, 20, 25, 50, 75, 100,
            150, 200, 250, 500, 750, 1000,
        ]
        all_options = set()
        base = self.min_limit
        for m in standard_multipliers:
            limit = int(base * m)
            if self.min_limit <= limit <= self.max_limit:
                all_options.add(limit)

        # Always include min and max
        all_options.add(self.min_limit)
        all_options.add(self.max_limit)

        # If requested_limit is provided, include it and nearby round limits
        if requested_limit and self.min_limit <= requested_limit <= self.max_limit:
            all_options.add(requested_limit)

        return sorted(all_options)


# =============================================================================
# PRICING
# =============================================================================


# ---- Parametric ILF raw curve functions ------------------------------------
#
# Each function returns raw(L) — the un-normalised curve value at limit L.
# Anchor normalisation (ILF = raw(L) / raw(anchor)) is applied uniformly
# in ILFCurve._parametric_factor(), so adding a new curve type only requires
# defining its raw(L) shape.  All curves guarantee ILF(anchor) = 1.0.
#

def _raw_bounded_exponential(L: float, anchor: float, max_ilf: float, k: float) -> float:
    """raw(L) = 1 + (max_ilf-1) * (1 - exp(-k * L/anchor))"""
    return 1.0 + (max_ilf - 1.0) * (1.0 - math.exp(-k * (L / anchor)))


def _raw_power(L: float, anchor: float, alpha: float) -> float:
    """raw(L) = (L/anchor)^alpha — already 1.0 at anchor."""
    return (L / anchor) ** alpha


def _raw_logarithmic(L: float, anchor: float, a: float, b: float) -> float:
    """raw(L) = a + b * ln(L/anchor + 1)"""
    return a + b * math.log((L / anchor) + 1.0)


def _raw_pareto(L: float, anchor: float, alpha: float) -> float:
    """raw(L) = (L/anchor)^alpha — single-Pareto severity scaling."""
    return (L / anchor) ** alpha


def _raw_iso_pareto(L: float, anchor: float, q: float, b: float) -> float:
    """
    ISO Pareto ILF — based on the truncated Pareto severity distribution.

    raw(L) = 1 - (b / (b + L))^(q - 1)

    where q is the Pareto shape parameter (typically 1.5-3.0) and b is the
    loss elimination ratio threshold (typically a small fraction of the anchor).

    The ISO increased limits table is a discretised version of this curve.
    Actuarial teams can specify 'iso_pareto' with (q, b) to reproduce
    standard ISO tables without hand-fitting.
    """
    return 1.0 - (b / (b + L)) ** (q - 1.0)


_CURVE_REGISTRY: Dict[str, Callable] = {
    "bounded_exponential": _raw_bounded_exponential,
    "power": _raw_power,
    "logarithmic": _raw_logarithmic,
    "pareto": _raw_pareto,
    "iso_pareto": _raw_iso_pareto,
}


class ILFCurve(StrictModel):
    """
    Increased Limit Factor curve — parametric only.

    Supported curve types: bounded_exponential, power, logarithmic, pareto, iso_pareto.

    Example:
        anchor_limit: 5000000
        curve: bounded_exponential
        params:
            max_ilf: 3.0
            k: 1.2
    """
    anchor_limit: int
    curve: str
    params: Optional[Dict[str, float]] = None

    @model_validator(mode="after")
    def validate_curve_config(self) -> "ILFCurve":
        if self.curve not in _CURVE_REGISTRY:
            raise ValueError(
                f"Unknown ILF curve type '{self.curve}'. "
                f"Valid types: {list(_CURVE_REGISTRY.keys())}"
            )
        return self

    @property
    def is_parametric(self) -> bool:
        """Always True — table-based ILF has been removed."""
        return True

    def get_factor_for_limit(self, limit: int) -> float:
        """Get ILF factor for a given limit."""
        curve_fn = _CURVE_REGISTRY[self.curve]
        params = dict(self.params or {})

        # Extract cap before passing to raw function (not all curves use it)
        cap = params.pop("cap", None)

        anchor = float(self.anchor_limit)
        raw_at_limit = curve_fn(float(limit), anchor, **params)
        raw_at_anchor = curve_fn(anchor, anchor, **params)

        # Normalise: ILF(anchor) = 1.0
        if raw_at_anchor == 0:
            ilf = 1.0
        else:
            ilf = raw_at_limit / raw_at_anchor

        # Apply cap if specified
        if cap is not None:
            ilf = min(ilf, cap)

        # Floor at 1.0
        return max(ilf, 1.0)

    def get_cumulative_factor(self, limit: int) -> float:
        """Get cumulative ILF factor for tower layer pricing.

        Unlike get_factor_for_limit(), this does NOT floor at 1.0.
        This is required for tower pricing where the layer premium is
        derived from ILF(A+L) - ILF(A), and ILF(0) must be 0.0 (not 1.0).
        """
        if limit <= 0:
            return 0.0
        curve_fn = _CURVE_REGISTRY[self.curve]
        params = dict(self.params or {})
        cap = params.pop("cap", None)
        anchor = float(self.anchor_limit)
        raw_at_limit = curve_fn(float(limit), anchor, **params)
        raw_at_anchor = curve_fn(anchor, anchor, **params)
        if raw_at_anchor == 0:
            ilf = 1.0
        else:
            ilf = raw_at_limit / raw_at_anchor
        if cap is not None:
            ilf = min(ilf, cap)
        return ilf


class DeductibleFactor(StrictModel):
    """Deductible adjustment factor."""
    deductible: int
    factor: float


class ProductTypePricing(StrictModel):
    """Pricing parameters for a product type."""
    ilf_curve: ILFCurve
    deductible_factors: List[DeductibleFactor]
    lead_loading_factor: float = Field(default=1.0, ge=1.0, le=2.0)

    def get_deductible_factor(self, deductible: int) -> float:
        """Get deductible factor for a given deductible, interpolating between reference points.

        Uses log-linear interpolation between the two nearest reference deductibles,
        matching the approach used for ILF curves. If the deductible falls outside
        the reference range, the nearest boundary factor is returned (no extrapolation).
        """
        if not self.deductible_factors:
            return 1.0

        # Sort reference points by deductible
        sorted_refs = sorted(self.deductible_factors, key=lambda f: f.deductible)

        # Exact match — fast path
        for f in sorted_refs:
            if f.deductible == deductible:
                return f.factor

        # Below minimum reference — clamp to lowest factor
        if deductible <= sorted_refs[0].deductible:
            return sorted_refs[0].factor

        # Above maximum reference — clamp to highest factor
        if deductible >= sorted_refs[-1].deductible:
            return sorted_refs[-1].factor

        # Find bracketing reference points and interpolate log-linearly
        import math
        for i in range(len(sorted_refs) - 1):
            lo = sorted_refs[i]
            hi = sorted_refs[i + 1]
            if lo.deductible < deductible < hi.deductible:
                # Log-linear interpolation: factor = lo.factor * (hi.factor/lo.factor)^t
                # where t = log(ded/lo.ded) / log(hi.ded/lo.ded)
                if lo.factor <= 0 or hi.factor <= 0:
                    # Fallback to linear if factors aren't positive
                    t = (deductible - lo.deductible) / (hi.deductible - lo.deductible)
                    return round(lo.factor + t * (hi.factor - lo.factor), 6)
                log_t = math.log(deductible / lo.deductible) / math.log(hi.deductible / lo.deductible)
                return round(lo.factor * (hi.factor / lo.factor) ** log_t, 6)

        # Shouldn't reach here, but safety fallback
        return 1.0


class Pricing(StrictModel):
    """Pricing section."""
    base_limit_reference: int = 1000000
    base_deductible_reference: int = 50000
    by_product_type: Dict[str, ProductTypePricing]
    basis_damping: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Sub-linear exponent for total-value bases (tiv, hull_value, total_assets). "
        "When basis_value >> limit, effective_basis = limit × (basis/limit)^damping. "
        "1.0 = linear (no damping), 0.5 = moderate sqrt (default), 0.3 = heavy."
    )

    @field_validator("by_product_type")
    @classmethod
    def validate_anchor_presence(cls, v: Dict[str, ProductTypePricing], info) -> Dict[str, ProductTypePricing]:
        """Ensure base_limit_reference exists in every ILF curve with factor 1.0."""
        # Note: Can't access base_limit_reference in field_validator
        # Full validation done in CoverageConfig model_validator
        return v


# =============================================================================
# GUARDRAILS
# =============================================================================

class Guardrails(StrictModel):
    """
    Runtime pricing guardrails.

    Enforced by the pricer to prevent commercially impossible outputs.
    Modifier clamping bounds the total modifier product; premium caps
    ensure final premiums stay within acceptable ratios to limit and revenue.
    """
    modifier_floor: float = Field(default=0.10, ge=0.0, le=1.0)
    modifier_cap: float = Field(default=2.50, ge=1.0)
    max_premium_to_limit_ratio: float = Field(default=0.35, ge=0.0, le=1.0)
    max_premium_to_revenue_ratio: float = Field(default=0.01, ge=0.0, le=1.0)
    max_ilf_factor: float = Field(
        default=10.0, ge=1.0,
        description="Maximum allowed ILF factor at any limit point. "
        "Prevents runaway premium amplification at high limits."
    )

    @model_validator(mode="after")
    def validate_floor_below_cap(self) -> "Guardrails":
        if self.modifier_floor >= self.modifier_cap:
            raise ValueError(
                f"modifier_floor ({self.modifier_floor}) must be < modifier_cap ({self.modifier_cap})"
            )
        return self


# =============================================================================
# COMPLETE COVERAGE CONFIG
# =============================================================================

class CoverageConfig(StrictModel):
    """
    Complete coverage configuration.

    This is the top-level model representing a single configuration
    within a coverage (e.g., cyber_general within cyber).
    """
    # Identity fields (set by compiler during loading)
    coverage_id: str = ""
    config_id: str = ""

    metadata: ConfigMetadata
    direct_queries: List[DirectQuery] = Field(default_factory=list)
    signal_registry: List[SignalDefinition] = Field(default_factory=list)
    groups: Groups = Field(default_factory=Groups)
    risk_tier_bands: RiskTierBands
    loss_tier_bands: Optional[LossTierBands] = None
    exposure: Optional[Exposure] = None
    limit_configuration: Optional[LimitConfiguration] = None
    pricing: Pricing
    guardrails: Guardrails = Field(default_factory=Guardrails)

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
            ilf = prod_pricing.ilf_curve
            # Parametric curves normalise to 1.0 at anchor_limit by construction
            if ilf.anchor_limit != base_limit:
                _logger.info(
                    f"Product '{prod_name}' parametric anchor_limit ({ilf.anchor_limit}) "
                    f"differs from base_limit_reference ({base_limit})"
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
            _logger.warning(
                "Configuration validation warnings for %s/%s: %s",
                self.coverage_id, self.config_id,
                "; ".join(errors),
            )

        return self

    # -------------------------------------------------------------------------
    # Backward-compatibility properties
    # -------------------------------------------------------------------------

    @property
    def coverage(self) -> str:
        """Backward compat: alias for coverage_id."""
        return self.coverage_id

    @property
    def configuration(self) -> str:
        """Backward compat: alias for config_id."""
        return self.config_id

    @property
    def config_hash(self) -> str:
        """Backward compat: no hash in compiled configs."""
        return ""

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

    def get_cumulative_ilf(self, product_type: str, limit: int) -> float:
        """Get cumulative ILF for tower layer pricing (no floor at 1.0)."""
        if product_type not in self.pricing.by_product_type:
            return 0.0 if limit <= 0 else 1.0
        return self.pricing.by_product_type[product_type].ilf_curve.get_cumulative_factor(limit)

    def get_deductible_factor(self, product_type: str, deductible: int) -> float:
        """Get deductible factor for product type and deductible."""
        if product_type not in self.pricing.by_product_type:
            return 1.0
        return self.pricing.by_product_type[product_type].get_deductible_factor(deductible)


# =============================================================================
# COVERAGE WRAPPER
# =============================================================================

class Coverage(StrictModel):
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
