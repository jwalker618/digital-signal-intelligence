"""
DSI Model Layer - Core Data Types (Phase 4)

This module defines the dataclasses used by the model layer to:
- Parse and represent YAML configuration
- Track model data and versions
- Pass results between workflow steps

These types connect the signal architecture to the pricing workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# ENUMS
# =============================================================================

class DecisionType(Enum):
    """Workflow decision outcomes."""
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class ConditionAction(Enum):
    """Actions that can be triggered by conditions."""
    TIER_OVERRIDE = "tier_override"
    REFERRAL = "referral"
    NOTE = "note"
    MODIFIER = "modifier"
    FLAG = "flag"
    REFER = "refer"


class PremiumMethod(Enum):
    """Methods for base premium calculation."""
    PURE = "pure"               # Direct premium amount from tier
    RATE_BASED = "rate"         # Rate applied to metric (TIV, revenue, etc.)
    PREMIUM_BASE = "PREMIUM_BASE"  # v2.0: Direct premium from tier application.applied
    MULTIPLIER = "MULTIPLIER"      # v2.0: Rate × basis value (tiv, limit, revenue)
    CATEGORICAL = "CATEGORICAL"    # v2.0: Category-derived premium


class VersionType(str, Enum):
    """Model version types."""
    INITIAL = "initial"
    REFERRAL_REVIEW = "referral_review"
    AMENDMENT = "amendment"


class DiscoveryConfidence(Enum):
    """Confidence levels for website discovery."""
    HIGH = "high"           # 90%+ confidence - multiple signals align
    MEDIUM = "medium"       # 70-89% confidence - some ambiguity
    LOW = "low"             # 50-69% confidence - significant uncertainty
    UNVERIFIED = "unverified"  # <50% - requires manual verification


# =============================================================================
# CONFIGURATION TYPES (from YAML)
# =============================================================================

@dataclass
class SignalCondition:
    """
    Condition that can trigger tier override, referral, flag, or modifier.

    v2.0: Defined via score_conditions (plural) list on signal_registry
    items and groups. Each condition has threshold, comparison, action.
    Actions: FLAG | MODIFIER | REFER (DECLINE is tier-level only).
    """
    condition_type: str       # 'threshold', 'max', 'equals', 'contains'
    condition_value: Any      # The value to compare against
    comparison: str           # v2.0: "<=", ">=", "==", ">", "<"
    action: ConditionAction   # What happens when triggered
    action_value: Any         # tier number, modifier applied, note text
    applied: Optional[float] = None  # v2.0: MODIFIER applied value
    note: str = ""            # v2.0: descriptive note
    inclusive: bool = False   # v1.0 compat: whether threshold is inclusive

    @classmethod
    def from_yaml_band(cls, band: Dict[str, Any]) -> 'SignalCondition':
        """Create from YAML band definition (v1.0 or v2.0 format)."""
        # Map YAML action strings to ConditionAction
        action_map = {
            "DECLINE": ConditionAction.TIER_OVERRIDE,
            "REFER": ConditionAction.REFER,
            "MODIFIER": ConditionAction.MODIFIER,
            "FLAG": ConditionAction.FLAG,
            "NOTE": ConditionAction.NOTE,
        }

        action_str = band.get("action", "NOTE")
        action = action_map.get(action_str, ConditionAction.NOTE)

        # v2.0 format: threshold + comparison
        if "threshold" in band:
            comparison = band.get("comparison", "<=")
            threshold_value = band["threshold"]

            # Determine action_value based on action type
            if action == ConditionAction.TIER_OVERRIDE:
                action_value = band.get("override", 5)
            elif action == ConditionAction.REFER:
                action_value = band.get("override", band.get("note", "Referral triggered"))
            elif action == ConditionAction.MODIFIER:
                action_value = band.get("applied", band.get("modifier", 1.0))
            elif action == ConditionAction.FLAG:
                action_value = band.get("note", "Flag triggered")
            else:
                action_value = band.get("note", "")

            return cls(
                condition_type="threshold",
                condition_value=threshold_value,
                comparison=comparison,
                action=action,
                action_value=action_value,
                applied=band.get("applied"),
                note=band.get("note", ""),
            )

        # v1.0 fallback: max field
        if action == ConditionAction.TIER_OVERRIDE:
            action_value = band.get("override", 5)
        elif action == ConditionAction.MODIFIER:
            action_value = band.get("modifier", 1.0)
        elif action in (ConditionAction.REFERRAL, ConditionAction.REFER):
            action_value = band.get("note", "Referral triggered")
        else:
            action_value = band.get("note", "")

        return cls(
            condition_type="max",
            condition_value=band.get("max", 0),
            comparison="<=",
            action=action,
            action_value=action_value,
            applied=band.get("applied", band.get("modifier")),
            note=band.get("note", ""),
            inclusive=band.get("inclusive_max", False),
        )


@dataclass
class SignalFeatureConfig:
    """
    Single signal feature definition from YAML.

    Represents one signal within a signal group.
    """
    id: str
    name: str
    description: str
    weight: float
    inference_function: str
    score_condition: bool = False
    conditions: List[SignalCondition] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'SignalFeatureConfig':
        """Create from YAML feature definition (v1.0 or v2.0 format)."""
        conditions = []

        # v2.0: score_conditions (plural) as list of condition objects
        if "score_conditions" in data and isinstance(data["score_conditions"], list):
            conditions = [
                SignalCondition.from_yaml_band(cond)
                for cond in data["score_conditions"]
            ]
            has_conditions = True
        # v1.0 fallback: score_condition (singular) boolean + bands
        elif data.get("score_condition") and "bands" in data:
            conditions = [
                SignalCondition.from_yaml_band(band)
                for band in data["bands"]
            ]
            has_conditions = True
        else:
            has_conditions = bool(data.get("score_condition", False))

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            weight=data.get("weight", 0.0),
            inference_function=data.get("inference_utility_function", ""),
            score_condition=has_conditions,
            conditions=conditions,
        )


@dataclass
class SignalGroupConfig:
    """
    Group of signals with collective weight.

    Signal groups contribute to the composite score.
    """
    id: str
    name: str
    description: str
    weight: float
    score_condition: bool = False
    conditions: List[SignalCondition] = field(default_factory=list)
    features: List[SignalFeatureConfig] = field(default_factory=list)
    test_scores: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_yaml(
        cls,
        group_data: Dict[str, Any],
        features_data: List[Dict[str, Any]]
    ) -> 'SignalGroupConfig':
        """Create from YAML group and features definitions (v1.0 or v2.0)."""
        conditions = []

        # v2.0: score_conditions (plural) as list of condition objects
        if "score_conditions" in group_data and isinstance(group_data["score_conditions"], list):
            conditions = [
                SignalCondition.from_yaml_band(cond)
                for cond in group_data["score_conditions"]
            ]
            has_conditions = True
        # v1.0 fallback: score_condition (singular) boolean + bands
        elif group_data.get("score_condition") and "bands" in group_data:
            conditions = [
                SignalCondition.from_yaml_band(band)
                for band in group_data["bands"]
            ]
            has_conditions = True
        else:
            has_conditions = bool(group_data.get("score_condition", False))

        features = [
            SignalFeatureConfig.from_yaml(f)
            for f in features_data
        ]

        return cls(
            id=group_data["id"],
            name=group_data.get("name", group_data["id"]),
            description=group_data.get("description", ""),
            weight=group_data.get("weight", 0.0),
            score_condition=has_conditions,
            conditions=conditions,
            features=features,
            test_scores=group_data.get("test_scores", {}),
        )


@dataclass
class DirectQueryImpact:
    """Impact triggered by a direct query response."""
    trigger_value: bool       # The response that triggers this impact
    tier_override: Optional[int] = None
    action: Optional[str] = None  # "REFER", "DECLINE", "MODIFIER"
    modifier: Optional[float] = None
    note: Optional[str] = None

    @classmethod
    def from_yaml_band(cls, band: Dict[str, Any]) -> 'DirectQueryImpact':
        """Create from YAML band definition."""
        return cls(
            trigger_value=band.get("return", True),
            tier_override=band.get("override"),
            action=band.get("action"),
            modifier=band.get("modifier"),
            note=band.get("note"),
        )


@dataclass
class DirectQueryConfig:
    """
    Direct query (boolean question) definition.

    Direct queries are optional and evaluated in Step 7.
    """
    id: str
    question: str
    impacts: List[DirectQueryImpact] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'DirectQueryConfig':
        """Create from YAML query definition."""
        impacts = [
            DirectQueryImpact.from_yaml_band(band)
            for band in data.get("bands", [])
        ]

        return cls(
            id=data["id"],
            question=data.get("question", ""),
            impacts=impacts,
        )


@dataclass
class CategoricalFeatureValue:
    """Single value option for a categorical feature."""
    category: str
    label: str
    modifier: float
    description: str = ""

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'CategoricalFeatureValue':
        """Create from YAML category definition."""
        return cls(
            category=data.get("cat", "UNKNOWN"),
            label=data.get("label", ""),
            modifier=data.get("modifier", 1.0),
            description=data.get("description", ""),
        )


@dataclass
class CategoricalGroupConfig:
    """
    Categorical group definition from YAML.

    Categorical groups can impact premium as modifiers or be the basis of premium.
    """
    id: str
    name: str
    description: str
    impact: str  # "modifier" or "premium"
    inference_function: str
    values: List[CategoricalFeatureValue] = field(default_factory=list)

    @classmethod
    def from_yaml(
        cls,
        group_data: Dict[str, Any],
        values_data: List[Dict[str, Any]]
    ) -> 'CategoricalGroupConfig':
        """Create from YAML group and values definitions."""
        values = [CategoricalFeatureValue.from_yaml(v) for v in values_data]

        return cls(
            id=group_data["id"],
            name=group_data.get("name", group_data["id"]),
            description=group_data.get("description", ""),
            impact=group_data.get("impact", "modifier"),
            inference_function=group_data.get("inference_utility_function", ""),
            values=values,
        )

    def get_modifier(self, category: str) -> float:
        """Get modifier for a category value."""
        for v in self.values:
            if v.category == category:
                return v.modifier
        return 1.0


@dataclass
class TierConfig:
    """
    Score threshold to tier mapping.

    Defines score ranges for each tier and associated parameters.
    """
    tier: int
    label: str
    min_score: int
    max_score: int
    description: str = ""
    auto_approve: bool = False
    auto_decline: bool = False
    premium_method: PremiumMethod = PremiumMethod.PURE
    base_premium: Optional[float] = None      # For PURE method
    rate: Optional[float] = None              # For RATE_BASED method
    rate_basis: Optional[str] = None          # e.g., 'tiv', 'revenue'

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'TierConfig':
        """Create from YAML tier definition (v1.0 or v2.0 format)."""
        # v2.0: application block with method/applied/basis
        application = data.get("application", {})
        if application:
            method_str = application.get("method", "PREMIUM_BASE")
            method_map = {
                "PREMIUM_BASE": PremiumMethod.PREMIUM_BASE,
                "MULTIPLIER": PremiumMethod.MULTIPLIER,
                "CATEGORICAL": PremiumMethod.CATEGORICAL,
                "base": PremiumMethod.PURE,
                "rate": PremiumMethod.RATE_BASED,
            }
            method = method_map.get(method_str, PremiumMethod.PREMIUM_BASE)
            base_premium = application.get("applied", application.get("value"))
            rate = application.get("applied") if method == PremiumMethod.MULTIPLIER else None
            rate_basis = application.get("basis")
        else:
            # v1.0 fallback
            method_str = data.get("premium_generation_method", "base")
            method = PremiumMethod.RATE_BASED if method_str == "rate" else PremiumMethod.PURE
            base_premium = data.get("premium")
            rate = data.get("rate")
            rate_basis = data.get("rate_basis")

        return cls(
            tier=data.get("id", 1),
            label=data.get("label", f"TIER_{data.get('id', 1)}"),
            min_score=data.get("min_score", 0),
            max_score=data.get("max_score", 1000),
            description=data.get("description", ""),
            auto_approve=data.get("auto_approve", False),
            auto_decline=data.get("auto_decline", False),
            premium_method=method,
            base_premium=base_premium,
            rate=rate,
            rate_basis=rate_basis,
        )

    @property
    def decision(self) -> DecisionType:
        """Determine decision type for this tier."""
        if self.auto_decline:
            return DecisionType.DECLINE
        elif self.auto_approve:
            return DecisionType.APPROVE
        return DecisionType.REFER


@dataclass
class LimitBandConfig:
    """Limit band configuration for ILF calculations."""
    id: int
    limit: float
    deductible: float

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'LimitBandConfig':
        """Create from YAML limit band definition."""
        return cls(
            id=data.get("id", 1),
            limit=data.get("limit", 0),
            deductible=data.get("deductible", 0),
        )


@dataclass
class PricingConfig:
    """Pricing parameters from YAML (supports v2.0 and v2.2 schema)."""
    hull_ilf_base: float = 10_000_000
    hull_ilf_factors: List[Dict[str, float]] = field(default_factory=list)
    liability_ilf_base: float = 100_000_000
    liability_ilf_factors: List[Dict[str, float]] = field(default_factory=list)
    # Legacy v2.0: percentage-based deductible credits
    deductible_credits: List[Dict[str, Any]] = field(default_factory=list)
    # V2.2: fixed deductible amounts with factors (anchor = 1.00)
    deductible_factors: List[Dict[str, Any]] = field(default_factory=list)
    # V2.2 Pricing Anchors
    base_limit_reference: int = 1000000
    base_deductible_reference: int = 50000
    experience_modifiers: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'PricingConfig':
        """Create from YAML pricing definition."""
        hull_ilf = data.get("hull_ilf", {})
        liability_ilf = data.get("liability_ilf", {})

        return cls(
            hull_ilf_base=hull_ilf.get("base_value", 10_000_000),
            hull_ilf_factors=hull_ilf.get("factors", []),
            liability_ilf_base=liability_ilf.get("base_limit", 100_000_000),
            liability_ilf_factors=liability_ilf.get("factors", []),
            # Support both legacy and V2.2 structures
            deductible_credits=data.get("deductible_credits", []),
            deductible_factors=data.get("deductible_factors", []),
            base_limit_reference=data.get("base_limit_reference", 1000000),
            base_deductible_reference=data.get("base_deductible_reference", 50000),
            experience_modifiers=data.get("experience_modifiers", {}),
        )


@dataclass
class LossTierBand:
    """v2.0: Loss tier band with frequency/severity modifiers."""
    id: int
    label: str
    min_score: float
    max_score: float
    frequency_modifier: float = 1.0
    severity_modifier: float = 1.0

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'LossTierBand':
        """Create from v2.0 YAML loss tier band."""
        interp = data.get("interpretation", {})
        bands = interp.get("bands", {})
        app = interp.get("application", {})
        return cls(
            id=data.get("id", 1),
            label=data.get("label", ""),
            min_score=bands.get("min", 0),
            max_score=bands.get("max", 100),
            frequency_modifier=app.get("frequency_modifier", 1.0),
            severity_modifier=app.get("severity_modifier", 1.0),
        )


@dataclass
class LossTierConfig:
    """v2.0: Loss tier bands configuration with constraints."""
    bands: List[LossTierBand] = field(default_factory=list)
    floor: float = 0.55
    cap: float = 1.60

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'LossTierConfig':
        """Create from v2.0 YAML loss_tier_bands section."""
        bands = [LossTierBand.from_yaml(b) for b in data.get("bands", [])]
        constraints = data.get("constraints", {})
        return cls(
            bands=bands,
            floor=constraints.get("floor", 0.55),
            cap=constraints.get("cap", 1.60),
        )

    def get_band_for_score(self, score: float) -> Optional['LossTierBand']:
        """Get loss tier band for a given loss score."""
        for band in self.bands:
            if band.min_score <= score <= band.max_score:
                return band
        return None


@dataclass
class ExposureTierBand:
    """v2.0: Exposure tier band with method and applied modifier."""
    id: int
    label: str
    min_value: float
    max_value: Optional[float]  # None = unbounded
    method: str = "MODIFIER"
    applied: float = 1.0

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'ExposureTierBand':
        """Create from v2.0 YAML exposure tier band."""
        interp = data.get("interpretation", {})
        bands = interp.get("bands", {})
        app = interp.get("application", {})
        return cls(
            id=data.get("id", 1),
            label=data.get("label", ""),
            min_value=bands.get("min", 0),
            max_value=bands.get("max"),
            method=app.get("method", "MODIFIER"),
            applied=app.get("applied", 1.0),
        )


@dataclass
class ExposureTierConfig:
    """v2.0: Exposure tier bands configuration."""
    bands: List[ExposureTierBand] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'ExposureTierConfig':
        """Create from v2.0 YAML exposure_tier_bands section."""
        bands = [ExposureTierBand.from_yaml(b) for b in data.get("bands", [])]
        return cls(bands=bands)

    def get_band_for_value(self, value: float) -> Optional['ExposureTierBand']:
        """Get exposure tier band for a given exposure value."""
        for band in self.bands:
            if band.max_value is None:
                if value >= band.min_value:
                    return band
            elif band.min_value <= value <= band.max_value:
                return band
        return None


@dataclass
class ConfigMetadata:
    """Metadata for a configuration."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    coverage_types: List[str] = field(default_factory=list)
    applicable_markets: List[str] = field(default_factory=list)
    minimum_viable_input: List[str] = field(default_factory=list)
    min_premium: float = 0.0
    default_currency: str = "USD"

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'ConfigMetadata':
        """Create from YAML metadata definition."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            coverage_types=data.get("coverage_types", []),
            applicable_markets=data.get("applicable_markets", []),
            minimum_viable_input=data.get("minimum_viable_input", []),
            min_premium=data.get("min_premium", 0.0),
            default_currency=data.get("default_currency", "USD"),
        )


@dataclass
class CoverageConfig:
    """
    Complete coverage model configuration.

    This is the parsed representation of a YAML configuration file,
    providing all parameters needed to run the 14-step workflow.
    """
    coverage: str                 # e.g., "aerospace"
    configuration: str            # e.g., "aerospace_general"
    config_hash: str = ""         # SHA-256 hash of YAML content

    # Metadata
    metadata: ConfigMetadata = field(default_factory=ConfigMetadata)

    # Direct queries (Step 7)
    direct_queries: List[DirectQueryConfig] = field(default_factory=list)

    # Categorical features
    categorical_groups: List[CategoricalGroupConfig] = field(default_factory=list)

    # Signal architecture (Steps 4-6)
    signal_groups: List[SignalGroupConfig] = field(default_factory=list)

    # Tier definitions (Steps 8-9)
    tiers: List[TierConfig] = field(default_factory=list)

    # v2.0: Loss and Exposure tier bands
    loss_tier_config: Optional[LossTierConfig] = None
    exposure_tier_config: Optional[ExposureTierConfig] = None

    # Limit bands (Step 12)
    limit_bands: List[LimitBandConfig] = field(default_factory=list)

    # Pricing parameters (Steps 10-12)
    pricing: PricingConfig = field(default_factory=PricingConfig)

    # Test profiles
    test_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_tier_for_score(self, score: float) -> TierConfig:
        """Get tier configuration for a composite score."""
        for tier in sorted(self.tiers, key=lambda t: t.tier):
            if tier.min_score <= score <= tier.max_score:
                return tier
        # Default to worst tier if no match
        return max(self.tiers, key=lambda t: t.tier) if self.tiers else TierConfig(tier=5, label="DECLINE", min_score=0, max_score=1000)

    def get_signal_group(self, group_id: str) -> Optional[SignalGroupConfig]:
        """Get signal group by ID."""
        for group in self.signal_groups:
            if group.id == group_id:
                return group
        return None

    def get_categorical_group(self, group_id: str) -> Optional[CategoricalGroupConfig]:
        """Get categorical group by ID."""
        for group in self.categorical_groups:
            if group.id == group_id:
                return group
        return None

    def get_direct_query(self, query_id: str) -> Optional[DirectQueryConfig]:
        """Get direct query by ID."""
        for query in self.direct_queries:
            if query.id == query_id:
                return query
        return None

    def get_all_inference_functions(self) -> List[str]:
        """Get all inference function names referenced in config."""
        functions = []

        # From signal features
        for group in self.signal_groups:
            for feature in group.features:
                if feature.inference_function:
                    functions.append(feature.inference_function)

        # From categorical groups
        for group in self.categorical_groups:
            if group.inference_function:
                functions.append(group.inference_function)

        return functions


# =============================================================================
# MODEL DATA TYPES (for workflow tracking)
# =============================================================================

@dataclass
class SignalOutput:
    """
    Output from a single signal during Step 4.

    Tracks the result from running an inference function.
    """
    signal_id: str
    signal_name: str
    group_id: str
    raw_score: float
    confidence: float
    weighted_score: float        # raw_score * weight
    weight: float
    data_sources: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=utcnow)
    conditions_triggered: List[str] = field(default_factory=list)
    from_cache: bool = False
    execution_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class CategoricalOutput:
    """
    Output from a categorical inference function.

    Represents the inferred category for a categorical group.
    """
    group_id: str
    group_name: str
    category: str
    label: str
    modifier: float
    confidence: float
    extracted_at: datetime = field(default_factory=utcnow)
    error: Optional[str] = None


@dataclass
class DiscoveryOutput:
    """
    Output from Step 0: Website Discovery.

    Tracks the result of discovering the corporate website before
    signal extraction begins.
    """
    # Input
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = None

    # Primary result
    discovered_website: Optional[str] = None
    discovered_domain: Optional[str] = None
    confidence: DiscoveryConfidence = DiscoveryConfidence.UNVERIFIED
    confidence_score: float = 0.0

    # Corporate identity
    legal_name: Optional[str] = None
    parent_company: Optional[str] = None
    industry: Optional[str] = None

    # Method and timing
    discovery_method: Optional[str] = None
    discovery_methods_used: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=utcnow)
    execution_time_ms: float = 0.0

    # Validation
    requires_manual_review: bool = False
    review_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    candidates_found: int = 0

    # Error handling
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class TriggeredCondition:
    """
    A condition that was triggered during evaluation.

    Tracks conditions from Steps 6 and 7.
    """
    source_type: str           # "signal_feature", "signal_group", "direct_query"
    source_id: str
    source_name: str
    score: Optional[float]     # The score that triggered (for signals)
    response: Optional[bool]   # The response that triggered (for queries)
    action: ConditionAction
    action_value: Any
    note: str


@dataclass
class BasePremiumDerivation:
    """
    Captures exactly how base premium was derived.

    Provides full audit trail: method, input basis, rate, tier, and result.
    """
    method: str                         # "MULTIPLIER", "PREMIUM_BASE", or "DEFAULT"
    basis_field: Optional[str] = None   # "revenue", "tiv", "limit", etc.
    basis_value: Optional[float] = None # e.g. 96_000_000_000
    rate: Optional[float] = None        # e.g. 0.00008
    tier: int = 3
    tier_label: str = "STANDARD"
    result: float = 0.0


@dataclass
class AppliedModifier:
    """
    A modifier that was applied during pricing.

    Tracks the audit trail of premium modifications.
    """
    source: str               # "categorical", "direct_query", "experience"
    source_id: str
    name: str
    factor: float
    premium_before: float
    premium_after: float


@dataclass
class ModelVersion:
    """
    A complete model execution snapshot.

    This represents one complete run through the 14-step workflow,
    capturing all inputs, intermediate values, and outputs.
    """
    # Identifiers
    version_id: str
    model_id: str
    version_number: int
    version_type: str          # 'initial', 'referral_review', 'amendment'

    # Configuration reference
    config_hash: str
    coverage: str
    configuration: str

    # Inputs
    entity_id: str
    submission_data: Dict[str, Any] = field(default_factory=dict)
    direct_query_responses: Dict[str, bool] = field(default_factory=dict)
    categorical_selections: Dict[str, str] = field(default_factory=dict)

    # Discovery output (Step 0)
    discovery_output: Optional[DiscoveryOutput] = None

    # Signal outputs (Step 4)
    signal_outputs: List[SignalOutput] = field(default_factory=list)
    categorical_outputs: List[CategoricalOutput] = field(default_factory=list)
    group_scores: Dict[str, Any] = field(default_factory=dict)

    # Scoring (Step 5)
    pure_composite_score: float = 0.0

    # Conditions (Steps 6 & 7)
    signal_conditions: List[TriggeredCondition] = field(default_factory=list)
    query_conditions: List[TriggeredCondition] = field(default_factory=list)

    # Tier resolution (Steps 8 & 9)
    tier_overrides: List[int] = field(default_factory=list)
    score_based_tier: int = 3
    final_tier: int = 3
    tier_label: str = "STANDARD"
    tier_margin: Optional[Any] = None  # TierMarginContext

    # Pricing (Steps 10-12)
    base_premium: float = 0.0
    base_premium_method: str = "pure"
    base_premium_derivation: Optional[BasePremiumDerivation] = None
    modifiers_applied: List[AppliedModifier] = field(default_factory=list)
    premium_after_modifiers: float = 0.0
    final_premium: float = 0.0
    uncapped_premium: Optional[float] = None  # Pre-guardrail premium (set when capped)

    # Decision (Step 13)
    decision: DecisionType = DecisionType.REFER
    auto_approve: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # Loss Propensity Outputs (Phase 16)
    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    severity_propensity_band: Optional[str] = None
    loss_confidence: Optional[float] = None

    # Loss Cohort Assignment
    loss_cohort_code: Optional[str] = None
    loss_cohort_name: Optional[str] = None
    loss_cohort_confidence: Optional[float] = None

    # Loss Pricing Impact
    loss_frequency_multiplier: Optional[float] = None
    loss_severity_multiplier: Optional[float] = None
    loss_combined_modifier: Optional[float] = None

    # Loss Monitoring State
    loss_trend_direction: Optional[str] = None
    loss_previous_score: Optional[float] = None
    loss_score_velocity: Optional[float] = None
    loss_last_refresh: Optional[datetime] = None

    # Exposure Assessment Outputs
    exposure_value: Optional[float] = None              # Primary exposure metric (TIV, revenue)
    exposure_modifier: Optional[float] = None           # Actual pricing factor applied
    exposure_magnitude_score: Optional[float] = None    # 0-100 normalised size score
    exposure_complexity_score: Optional[float] = None   # 0-100 normalised complexity score
    exposure_assessment_method: Optional[str] = None    # "streamlined" or "full"
    exposure_band_id: Optional[int] = None
    exposure_band_label: Optional[str] = None
    exposure_band_boundaries: Optional[Dict[str, Any]] = None
    exposure_components: Optional[Dict[str, float]] = None  # size_factor, growth_factor, concentration_factor

    # Correlation Matrix Reference
    correlation_matrix_version: Optional[str] = None
    correlation_matrix_hash: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=utcnow)
    created_by: str = ""
    confidence: float = 1.0
    signal_coverage: float = 1.0


@dataclass
class ConfigVersion:
    """
    Metadata for a configuration version.

    Used by ConfigManager for content-addressable storage.
    """
    version_id: str              # UUID
    config_hash: str             # SHA-256 of YAML payload
    coverage: str
    configuration: str
    created_by: str
    created_at: datetime
    is_active: bool = False


# =============================================================================
# RESULT TYPES (for workflow step outputs)
# =============================================================================

@dataclass
class ScoringResult:
    """
    Output from scoring pipeline (Steps 4-6).

    Contains all signal outputs, composite score, and triggered conditions.
    """
    # Step 4: Signal extraction
    signal_outputs: List[SignalOutput] = field(default_factory=list)
    categorical_outputs: List[CategoricalOutput] = field(default_factory=list)
    # group_scores: Dict[group_id, GroupScoreDetail] where GroupScoreDetail is:
    #   risk_score: float          - weighted average of signal scores in group (0-100)
    #   risk_weight: float         - group weight toward composite (from config)
    #   risk_contribution: float   - risk_score * risk_weight * 10 (contribution to 0-1000 composite)
    #   signal_count: int          - number of signals extracted for this group
    #   expected_signal_count: int - total signals defined in config for this group
    #   coverage_ratio: float      - signal_count / expected_signal_count
    #   loss_weight: float|None    - group weight in loss dimension (if configured)
    #   exposure_weight: float|None - group weight in exposure dimension (if configured)
    group_scores: Dict[str, Any] = field(default_factory=dict)

    # Step 5: Pure composite
    pure_composite_score: float = 0.0
    confidence: float = 1.0
    signal_coverage: float = 1.0

    # Step 6: Signal conditions
    conditions_triggered: List[TriggeredCondition] = field(default_factory=list)
    tier_overrides: List[int] = field(default_factory=list)
    referrals: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    modifiers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class QueryEvaluationResult:
    """
    Output from query evaluation (Step 7).

    Contains all impacts from direct query responses.
    """
    conditions_triggered: List[TriggeredCondition] = field(default_factory=list)
    tier_overrides: List[int] = field(default_factory=list)
    referrals: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    modifiers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TierMarginContext:
    """
    Context about how close a score is to tier boundaries.

    Helps underwriters understand if a risk is marginally in its tier
    (e.g., "barely Tier 3, close to Tier 2 boundary").
    """
    score: float                       # The composite score
    tier_id: int                       # Current tier
    tier_min: float                    # Current tier's lower bound
    tier_max: float                    # Current tier's upper bound
    percentile_in_tier: float          # 0.0 = at min, 1.0 = at max
    distance_to_better_tier: float = 0.0               # Points from lower tier boundary (headroom in best tier)
    distance_to_worse_tier: float = 0.0                # Points from upper tier boundary (headroom in worst tier)
    adjacent_better_tier: Optional[int] = None         # Tier ID of next better tier
    adjacent_worse_tier: Optional[int] = None          # Tier ID of next worse tier


@dataclass
class LimitPremiumDetail:
    """
    Detailed pricing breakdown for a single limit option.

    Stores component factors discretely (not just computed premium) to enable
    future tower/layer pricing via ILF(attachment + limit) - ILF(attachment).
    """
    limit: int
    deductible: int = 0
    attachment_point: Optional[int] = None  # None = ground-up; set for tower layers
    ilf_factor: float = 1.0
    deductible_factor: float = 1.0
    premium_before_scaling: float = 0.0  # premium_after_modifiers
    premium_after_scaling: float = 0.0   # premium × ilf × ded_factor
    uncapped_premium: Optional[float] = None  # pre-guardrail value if capped


@dataclass
class LayerPremiumDetail:
    """Pricing breakdown for a single tower/subscription layer.

    Captures both the order-level (100%) premium and the insurer's line-level
    premium, with lead/follow role and loading applied.
    """
    layer_id: int = 0
    layer_label: str = ""
    attachment: int = 0
    limit: int = 0
    order_premium: float = 0.0      # 100% premium for the layer
    signed_line: float = 1.0        # participation (1.0 = ground-up / 100%)
    role: str = "FOLLOW"            # LEAD or FOLLOW
    lead_loading: float = 1.0       # applied multiplier (1.0 for follow)
    line_premium: float = 0.0       # signed_line x order_premium x lead_loading
    rol: float = 0.0                # order_premium / limit (always at 100%)
    ilf_top: float = 0.0            # ILF(attachment + limit)
    ilf_bottom: float = 0.0         # ILF(attachment)
    layer_ilf: float = 0.0          # ilf_top - ilf_bottom


@dataclass
class PricingResult:
    """
    Output from pricing calculation (Steps 8-12).

    Contains complete pricing breakdown and audit trail.
    """
    # Step 8: Tier override resolution
    tier_overrides_considered: List[int] = field(default_factory=list)
    max_tier_override: Optional[int] = None

    # Step 9: Final tier
    score_based_tier: int = 3
    final_tier: int = 3
    tier_label: str = "STANDARD"
    tier_config: Optional[Any] = None  # RiskTierBand from config_schema (or legacy TierConfig)
    tier_margin: Optional[TierMarginContext] = None

    # Step 10: Base premium
    base_premium: float = 0.0
    base_premium_method: str = "pure"
    base_premium_derivation: Optional[BasePremiumDerivation] = None

    # Step 11: Modifiers
    modifiers_applied: List[AppliedModifier] = field(default_factory=list)
    total_modifier: float = 1.0
    premium_after_modifiers: float = 0.0

    # Step 12: Limit bands
    limit_premiums: Dict[str, float] = field(default_factory=dict)
    limit_premium_details: List[Any] = field(default_factory=list)  # List[LimitPremiumDetail]
    final_premium: float = 0.0

    # Guardrail outputs
    uncapped_premium: Optional[float] = None  # Pre-guardrail premium (set when premium_was_capped=True)
    guardrail_warnings: List[str] = field(default_factory=list)
    modifier_was_clamped: bool = False
    premium_was_capped: bool = False


@dataclass
class WorkflowResult:
    """
    Complete workflow output (Step 13).

    The final result of running an entity through the 14-step workflow.
    """
    # Identifiers
    entity_id: str = ""
    coverage: str = ""

    # Complete model version for audit trail
    model_version: Optional[ModelVersion] = None

    # Decision
    decision: DecisionType = DecisionType.REFER
    auto_approve: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # For API response
    recommended_limit: float = 0.0
    recommended_premium: float = 0.0

    # Summary
    composite_score: float = 0.0
    tier: int = 3
    tier_label: str = "STANDARD"
    confidence: float = 1.0

    # Signal completeness (Phase V4 - Multiplexer support)
    # Ratio of signals returned non-null to signals defined in registry
    signal_completeness: float = 1.0
    signals_returned: int = 0
    signals_defined: int = 0

    # Discovery summary (Step 0)
    discovered_domain: Optional[str] = None
    discovery_confidence: Optional[str] = None
    discovery_warnings: List[str] = field(default_factory=list)

    # Missing inputs (if Step 3 fails)
    missing_inputs: List[str] = field(default_factory=list)
    is_valid: bool = True


# Backward compatibility aliases
LimitBand = LimitBandConfig
ModifierApplication = AppliedModifier
SignalConfig = SignalFeatureConfig
