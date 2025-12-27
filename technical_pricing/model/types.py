"""
DSI Model Layer - Type Definitions

All dataclasses used across the model layer for configuration,
scoring, pricing, and workflow management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# ENUMS
# =============================================================================

class DecisionType(Enum):
    """Possible model decisions (Step 13)"""
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class VersionType(Enum):
    """Model version types (Step 2)"""
    INITIAL = "initial"
    REFERRAL_REVIEW = "referral_review"
    AMENDMENT = "amendment"


class ConditionAction(Enum):
    """Actions that can be triggered by conditions (Steps 6 & 7)"""
    TIER_OVERRIDE = "tier_override"
    REFERRAL = "referral"
    NOTE = "note"
    MODIFIER = "modifier"  # Only valid for direct queries (Step 7)


class PremiumMethod(Enum):
    """Base premium calculation method (Step 10)"""
    PURE = "pure"           # Fixed premium per tier
    RATE_BASED = "rate_based"  # Metric * rate


# =============================================================================
# CONFIGURATION TYPES
# =============================================================================

@dataclass
class SignalCondition:
    """
    Condition that can trigger tier override, referral, or note.
    Used at both signal_group and signal_feature levels.
    
    Note: Signal conditions CANNOT trigger modifiers (only direct queries can).
    """
    condition_type: str       # 'threshold_below', 'threshold_above', 'equals', 'in_list'
    condition_value: Any      # The value to compare against
    action: ConditionAction   # What to do when triggered
    action_value: Any         # tier number, referral reason, or note text
    
    def __post_init__(self):
        if isinstance(self.action, str):
            self.action = ConditionAction(self.action)
        # Signal conditions cannot define modifiers
        if self.action == ConditionAction.MODIFIER:
            raise ValueError("Signal conditions cannot define modifiers - only direct queries can")


@dataclass
class SignalConfig:
    """Single signal definition from YAML signal_features section"""
    name: str
    weight: float
    inference_function: str
    categorizer_type: str
    categorizer_params: dict = field(default_factory=dict)
    conditions: list[SignalCondition] = field(default_factory=list)
    
    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Signal weight must be 0-1, got {self.weight}")
        # Convert dict conditions to SignalCondition objects
        self.conditions = [
            c if isinstance(c, SignalCondition) else SignalCondition(**c)
            for c in self.conditions
        ]


@dataclass
class SignalGroupConfig:
    """Group of signals with collective weight"""
    name: str
    weight: float
    signals: list[SignalConfig] = field(default_factory=list)
    conditions: list[SignalCondition] = field(default_factory=list)
    
    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError(f"Group weight must be 0-1, got {self.weight}")
        # Convert dicts to proper types
        self.signals = [
            s if isinstance(s, SignalConfig) else SignalConfig(**s)
            for s in self.signals
        ]
        self.conditions = [
            c if isinstance(c, SignalCondition) else SignalCondition(**c)
            for c in self.conditions
        ]
    
    def validate_signal_weights(self) -> bool:
        """Check that signal weights within group sum to 1.0"""
        total = sum(s.weight for s in self.signals)
        return abs(total - 1.0) < 0.001  # Allow small floating point variance


@dataclass
class DirectQueryImpact:
    """Single impact from a direct query response"""
    impact_type: ConditionAction  # tier_override, referral, note, modifier
    value: Any                     # tier number, reason text, note text, or modifier factor
    trigger_on: bool = True        # True = impact when answer is True
    
    def __post_init__(self):
        if isinstance(self.impact_type, str):
            self.impact_type = ConditionAction(self.impact_type)


@dataclass
class DirectQueryConfig:
    """Direct query (boolean question) definition from YAML"""
    id: str
    question: str
    impacts: list[DirectQueryImpact] = field(default_factory=list)
    
    def __post_init__(self):
        self.impacts = [
            i if isinstance(i, DirectQueryImpact) else DirectQueryImpact(**i)
            for i in self.impacts
        ]


@dataclass
class TierConfig:
    """Score threshold to tier mapping with premium basis"""
    tier: int
    min_score: int
    max_score: int
    decision: DecisionType = DecisionType.APPROVE
    
    # Premium calculation - one of these must be set
    base_premium: float | None = None      # Option A: pure premium
    rate: float | None = None              # Option B: metric-based
    rate_basis: str | None = None          # e.g., 'tiv', 'revenue', 'payroll'
    
    def __post_init__(self):
        if isinstance(self.decision, str):
            self.decision = DecisionType(self.decision)
        
        # Validate that either pure premium or rate is specified
        has_pure = self.base_premium is not None
        has_rate = self.rate is not None
        
        if not has_pure and not has_rate:
            raise ValueError(f"Tier {self.tier} must specify either base_premium or rate")
        if has_rate and not self.rate_basis:
            raise ValueError(f"Tier {self.tier} has rate but no rate_basis")
    
    @property
    def premium_method(self) -> PremiumMethod:
        return PremiumMethod.PURE if self.base_premium is not None else PremiumMethod.RATE_BASED
    
    def contains_score(self, score: float) -> bool:
        """Check if a score falls within this tier's range"""
        return self.min_score <= score <= self.max_score


@dataclass
class LimitBand:
    """ILF table entry for limit band scaling (Step 12)"""
    limit: float
    ilf: float  # Increased Limit Factor
    
    def __post_init__(self):
        if self.ilf < 0:
            raise ValueError(f"ILF cannot be negative: {self.ilf}")


@dataclass
class CoverageConfig:
    """
    Complete coverage model configuration.
    Parsed from YAML and validated.
    """
    # Identity
    coverage: str              # e.g., 'aerospace', 'cyber'
    configuration: str         # e.g., 'aerospace_general'
    version: str               # Semantic version
    config_hash: str           # SHA-256 of source YAML
    
    # Required inputs (Step 3)
    required_inputs: list[str] = field(default_factory=list)
    
    # Signal architecture
    signal_groups: list[SignalGroupConfig] = field(default_factory=list)
    
    # Direct queries (Step 7)
    direct_queries: list[DirectQueryConfig] = field(default_factory=list)
    
    # Categorical features
    categorical_groups: list[str] = field(default_factory=list)
    categorical_features: dict[str, dict[str, float]] = field(default_factory=dict)
    
    # Tier and pricing
    tier_thresholds: list[TierConfig] = field(default_factory=list)
    limit_bands: list[LimitBand] = field(default_factory=list)
    deductible_credits: dict[float, float] = field(default_factory=dict)  # deductible -> credit
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Convert nested dicts to proper types
        self.signal_groups = [
            g if isinstance(g, SignalGroupConfig) else SignalGroupConfig(**g)
            for g in self.signal_groups
        ]
        self.direct_queries = [
            q if isinstance(q, DirectQueryConfig) else DirectQueryConfig(**q)
            for q in self.direct_queries
        ]
        self.tier_thresholds = [
            t if isinstance(t, TierConfig) else TierConfig(**t)
            for t in self.tier_thresholds
        ]
        self.limit_bands = [
            b if isinstance(b, LimitBand) else LimitBand(**b)
            for b in self.limit_bands
        ]
    
    def validate(self) -> list[str]:
        """
        Validate configuration integrity.
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        # Group weights must sum to 1.0
        group_weight_sum = sum(g.weight for g in self.signal_groups)
        if abs(group_weight_sum - 1.0) > 0.001:
            errors.append(f"Signal group weights sum to {group_weight_sum}, expected 1.0")
        
        # Each group's signal weights must sum to 1.0
        for group in self.signal_groups:
            if not group.validate_signal_weights():
                signal_sum = sum(s.weight for s in group.signals)
                errors.append(f"Group '{group.name}' signal weights sum to {signal_sum}, expected 1.0")
        
        # Tier thresholds must be contiguous
        sorted_tiers = sorted(self.tier_thresholds, key=lambda t: t.min_score)
        for i in range(len(sorted_tiers) - 1):
            current = sorted_tiers[i]
            next_tier = sorted_tiers[i + 1]
            if current.max_score + 1 != next_tier.min_score:
                errors.append(
                    f"Gap between tier {current.tier} (max={current.max_score}) "
                    f"and tier {next_tier.tier} (min={next_tier.min_score})"
                )
        
        # Categorical features must reference valid groups
        for group_name in self.categorical_features:
            if group_name not in self.categorical_groups:
                errors.append(f"Categorical feature '{group_name}' not in categorical_groups")
        
        return errors
    
    def get_tier_for_score(self, score: float) -> TierConfig | None:
        """Map a composite score (0-1000) to a tier"""
        for tier in self.tier_thresholds:
            if tier.contains_score(score):
                return tier
        return None
    
    def get_signal_config(self, signal_name: str) -> SignalConfig | None:
        """Look up a signal by name"""
        for group in self.signal_groups:
            for signal in group.signals:
                if signal.name == signal_name:
                    return signal
        return None
    
    def get_group_for_signal(self, signal_name: str) -> SignalGroupConfig | None:
        """Find which group a signal belongs to"""
        for group in self.signal_groups:
            for signal in group.signals:
                if signal.name == signal_name:
                    return group
        return None


# =============================================================================
# CONFIG VERSION TRACKING (Step 1)
# =============================================================================

@dataclass
class ConfigVersion:
    """
    Metadata for a configuration version.
    Supports content-addressable storage pattern.
    """
    version_id: str           # UUID
    config_hash: str          # SHA-256 of YAML payload
    coverage: str
    configuration: str
    created_by: str
    created_at: datetime
    is_active: bool = False
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


# =============================================================================
# SIGNAL OUTPUT TYPES (Step 4)
# =============================================================================

@dataclass
class SignalOutput:
    """Output from a single signal evaluation"""
    signal_id: str            # Unique identifier
    signal_name: str          # Human-readable name
    group_name: str           # Parent group
    
    # Scores
    raw_score: float          # 0-100 from categorizer
    confidence: float         # 0-1 data quality/availability
    signal_weight: float      # Weight within group (from config)
    group_weight: float       # Group's weight (from config)
    weighted_score: float     # raw_score * signal_weight * group_weight * 10
    
    # Provenance
    data_sources: list[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    # Conditions triggered by this signal
    conditions_triggered: list[dict] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.extracted_at, str):
            self.extracted_at = datetime.fromisoformat(self.extracted_at)


# =============================================================================
# SCORING RESULT (Steps 4-6)
# =============================================================================

@dataclass
class ScoringResult:
    """Complete output from scoring pipeline (Steps 4-6)"""
    entity_id: str
    coverage: str
    
    # Step 4: Signal extraction
    signal_outputs: list[SignalOutput] = field(default_factory=list)
    group_scores: dict[str, float] = field(default_factory=dict)  # group_name -> weighted score
    
    # Step 5: Pure composite
    pure_composite_score: float = 0.0  # 0-1000
    aggregate_confidence: float = 0.0  # 0-1
    
    # Step 6: Signal conditions evaluation
    signal_conditions_triggered: list[dict] = field(default_factory=list)
    tier_overrides_from_signals: list[int] = field(default_factory=list)
    referrals_from_signals: list[str] = field(default_factory=list)
    notes_from_signals: list[str] = field(default_factory=list)
    
    # Timing
    extraction_started_at: datetime = field(default_factory=datetime.utcnow)
    extraction_completed_at: datetime | None = None
    duration_ms: float = 0.0


# =============================================================================
# QUERY EVALUATION RESULT (Step 7)
# =============================================================================

@dataclass
class QueryEvaluationResult:
    """Output from direct query evaluation (Step 7)"""
    # Impacts identified
    tier_overrides: list[int] = field(default_factory=list)
    referrals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    modifiers: list[dict] = field(default_factory=list)  # {name, factor}
    
    # Audit trail
    queries_evaluated: list[dict] = field(default_factory=list)  # {id, response, impacts_triggered}


# =============================================================================
# PRICING RESULT (Steps 8-12)
# =============================================================================

@dataclass
class ModifierApplication:
    """Record of a single modifier being applied"""
    name: str
    factor: float
    premium_before: float
    premium_after: float
    source: str  # 'categorical', 'direct_query', 'experience'


@dataclass
class PricingResult:
    """Complete output from pricing calculation (Steps 8-12)"""
    # Step 8: Tier override resolution
    score_based_tier: int
    tier_overrides_considered: list[int] = field(default_factory=list)
    max_tier_override: int | None = None
    
    # Step 9: Final tier
    final_tier: int = 0
    
    # Step 10: Base premium
    base_premium: float = 0.0
    base_premium_method: PremiumMethod = PremiumMethod.PURE
    rate_basis_value: float | None = None  # e.g., actual TIV used
    
    # Step 11: Modifiers
    modifiers_applied: list[ModifierApplication] = field(default_factory=list)
    premium_after_modifiers: float = 0.0
    
    # Step 12: Limit bands
    limit_premiums: dict[float, float] = field(default_factory=dict)  # limit -> premium
    
    def __post_init__(self):
        if isinstance(self.base_premium_method, str):
            self.base_premium_method = PremiumMethod(self.base_premium_method)


# =============================================================================
# MODEL VERSION (Step 2 - Complete Snapshot)
# =============================================================================

@dataclass
class ModelVersion:
    """
    A complete model execution snapshot.
    Each interaction creates a new version for full audit trail.
    """
    # Identity
    version_id: str
    model_id: str
    version_number: int
    version_type: VersionType
    
    # Inputs
    entity_id: str
    submission_data: dict = field(default_factory=dict)
    direct_query_responses: dict[str, bool] = field(default_factory=dict)
    categorical_selections: dict[str, str] = field(default_factory=dict)
    
    # Scoring (Steps 4-6)
    signal_outputs: list[SignalOutput] = field(default_factory=list)
    group_scores: dict[str, float] = field(default_factory=dict)
    pure_composite_score: float = 0.0
    aggregate_confidence: float = 0.0
    
    # Conditions (Steps 6-7)
    signal_conditions: list[dict] = field(default_factory=list)
    query_conditions: list[dict] = field(default_factory=list)
    tier_overrides: list[int] = field(default_factory=list)
    
    # Tier (Steps 8-9)
    score_based_tier: int = 0
    final_tier: int = 0
    
    # Pricing (Steps 10-12)
    base_premium: float = 0.0
    modifiers_applied: list[ModifierApplication] = field(default_factory=list)
    limit_premiums: dict[float, float] = field(default_factory=dict)
    final_premium: float = 0.0  # At selected/default limit
    
    # Decision (Step 13)
    decision: DecisionType = DecisionType.REFER
    auto_approve: bool = False
    referral_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    
    # Metadata
    config_hash: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    
    def __post_init__(self):
        if isinstance(self.version_type, str):
            self.version_type = VersionType(self.version_type)
        if isinstance(self.decision, str):
            self.decision = DecisionType(self.decision)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        # Convert modifier dicts to objects
        self.modifiers_applied = [
            m if isinstance(m, ModifierApplication) else ModifierApplication(**m)
            for m in self.modifiers_applied
        ]
        # Convert signal output dicts to objects
        self.signal_outputs = [
            s if isinstance(s, SignalOutput) else SignalOutput(**s)
            for s in self.signal_outputs
        ]


# =============================================================================
# WORKFLOW RESULT (Step 13 - Final Output)
# =============================================================================

@dataclass
class WorkflowResult:
    """Complete workflow output for API response"""
    # Core result
    model_version: ModelVersion
    decision: DecisionType
    auto_approve: bool
    
    # Details
    referral_reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    
    # Pricing options
    premium_options: dict[float, float] = field(default_factory=dict)  # limit -> premium
    recommended_limit: float = 0.0
    recommended_premium: float = 0.0
    
    # Validation
    missing_inputs: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.decision, str):
            self.decision = DecisionType(self.decision)
    
    @property
    def is_valid(self) -> bool:
        """Check if workflow completed successfully"""
        return len(self.missing_inputs) == 0 and len(self.validation_errors) == 0


# =============================================================================
# SUBMISSION REQUEST
# =============================================================================

@dataclass
class SubmissionRequest:
    """Input for running the workflow"""
    entity_id: str
    coverage: str
    
    # Submission data (includes rate basis values like TIV, revenue, etc.)
    submission_data: dict = field(default_factory=dict)
    
    # Direct query responses (Step 7)
    direct_query_responses: dict[str, bool] = field(default_factory=dict)
    
    # Categorical selections (Step 11)
    categorical_selections: dict[str, str] = field(default_factory=dict)
    
    # Pricing options
    requested_limit: float | None = None
    requested_deductible: float | None = None
    
    # Metadata
    user: str = ""
    
    def get_rate_basis_value(self, basis: str) -> float | None:
        """Extract a rate basis value from submission data"""
        return self.submission_data.get(basis)