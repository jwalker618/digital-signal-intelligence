"""
Digital Signal Intelligence (DSI) - Config-Driven Pricing Model
================================================================

A unified pricing model that loads its structure, signals, weights, and
pricing parameters from a YAML configuration file. This enables:

1. Single source of truth for model definition
2. Easy model updates without code changes
3. Consistent test data generation from config
4. Audit trail of configuration changes

This replaces individual coverage-specific models with a generic engine
that adapts based on configuration.

Author: John Walker
Version: 2.0.0
Date: January 2025
"""

import yaml
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Type

logger = logging.getLogger("dsi.pricing")


# =============================================================================
# DYNAMIC ENUM FACTORY
# =============================================================================

def create_enum_from_config(name: str, values: List[Dict]) -> Type[Enum]:
    """
    Dynamically create an Enum class from configuration values.
    
    Args:
        name: Name of the enum class
        values: List of dicts with 'id' and optional 'label' keys
        
    Returns:
        Dynamically created Enum class
    """
    enum_values = {v['id']: v['id'].lower() for v in values}
    return Enum(name, enum_values)


# =============================================================================
# STANDARD ENUMS (Always present across models)
# =============================================================================

class RiskTier(Enum):
    """Risk tier classification."""
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4
    TIER_5 = 5


class SignalCategory(Enum):
    """TTL categories for signals."""
    REAL_TIME = "real_time"      # < 1 hour
    DYNAMIC = "dynamic"          # 1-24 hours
    SEMI_STATIC = "semi_static"  # 1-30 days
    STATIC = "static"            # > 30 days


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Signal:
    """Individual signal value."""
    signal_id: str
    signal_type: str
    value: float
    confidence: float = 1.0
    source: Optional[str] = None
    extracted_at: Optional[datetime] = None
    
    @property
    def weighted_value(self) -> float:
        return self.value * self.confidence


@dataclass
class SignalGroup:
    """Group of related signals with collective weight."""
    group_id: str
    name: str
    weight: float
    signals: Dict[str, Signal] = field(default_factory=dict)
    
    @property
    def score(self) -> float:
        """Calculate group score as average of signal values."""
        if not self.signals:
            return 0.0
        values = [s.weighted_value for s in self.signals.values() if s.value > 0]
        return sum(values) / len(values) if values else 0.0
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted contribution to composite score."""
        return self.score * self.weight
    
    @property
    def coverage(self) -> float:
        """Fraction of signals with values."""
        if not self.signals:
            return 0.0
        populated = len([s for s in self.signals.values() if s.value > 0])
        return populated / len(self.signals)


@dataclass
class CategoryScore:
    """Score for a signal category/group."""
    category_name: str
    category_id: str
    score: float
    weight: float
    weighted_contribution: float
    signal_count: int
    coverage: float


@dataclass
class PricingResult:
    """Result of pricing calculation."""
    base_premium: float
    risk_adjusted_premium: float
    total_modifier: float
    hull_premium: float
    liability_premium: float
    deductible_credit: float
    taxes_fees: float
    rate_components: Dict[str, float] = field(default_factory=dict)


@dataclass 
class DSIAssessment:
    """Complete assessment result."""
    # Entity info
    entity_name: str
    entity_id: Optional[str] = None
    
    # Classification
    operator_type: str = ""
    fleet_category: str = ""
    fleet_size: str = ""
    regulatory_framework: str = ""
    iosa_status: str = ""
    
    # Scoring
    category_scores: List[CategoryScore] = field(default_factory=list)
    composite_score: float = 0.0
    tier: RiskTier = RiskTier.TIER_3
    tier_label: str = "STANDARD"
    confidence: float = 0.0
    signal_coverage: float = 0.0
    
    # Flags
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    amber_flags: List[str] = field(default_factory=list)
    
    # Decision
    decision: str = "REVIEW"
    decision_rationale: str = ""
    decision_path: str = "referred"
    
    # Pricing
    base_premium: float = 0.0
    risk_adjusted_premium: float = 0.0
    premium_modifier: float = 1.0
    hull_value: float = 0.0
    liability_limit: float = 0.0
    rate_per_million: float = 0.0
    
    # Metadata
    model_version: str = ""
    coverage_type: str = ""
    assessment_date: datetime = field(default_factory=datetime.utcnow)
    config_checksum: str = ""


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

class ModelConfig:
    """
    Loads and provides access to model configuration from YAML.
    """
    
    def __init__(self, config_path: str):
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self._raw_config = self._load_yaml()
        
        # Extract coverage type (first key in YAML)
        self.coverage_type = list(self._raw_config.keys())[0]
        self._config = self._raw_config[self.coverage_type]
        
        # Parse configuration sections
        self.metadata = self._config.get('metadata', {})
        self.direct_queries = self._config.get('direct_queries', [])
        self.categorical_features = self._config.get('categorical_features', {})
        self.signal_groups = self._config.get('signal_groups', [])
        self.signal_features = self._config.get('signal_features', {})
        self.tier_thresholds = self._config.get('tier_thresholds', {})
        self.pricing = self._config.get('pricing', {})
        self.test_profiles = self._config.get('test_profiles', {})
        self.red_flag_rules = self._config.get('red_flags', {})
        self.green_flag_rules = self._config.get('green_flags', [])
        
        # Build dynamic enums
        self._enums = self._build_enums()
        
        # Build signal group lookup
        self._signal_group_map = {g['id']: g for g in self.signal_groups}
        
        # Validate configuration
        self._validate()
        
        logger.info(f"Loaded config for {self.coverage_type} v{self.version}")
    
    def _load_yaml(self) -> Dict:
        """Load YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _build_enums(self) -> Dict[str, Type[Enum]]:
        """Build dynamic enums from categorical features."""
        enums = {}
        for feature_name, feature_config in self.categorical_features.items():
            enum_name = ''.join(word.title() for word in feature_name.split('_'))
            enums[feature_name] = create_enum_from_config(
                enum_name, 
                feature_config.get('values', [])
            )
        return enums
    
    def _validate(self):
        """Validate configuration integrity."""
        # Check signal group weights sum to 1.0
        total_weight = sum(g.get('weight', 0) for g in self.signal_groups)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Signal group weights sum to {total_weight}, expected 1.0")
        
        # Check all signal groups have features defined
        for group in self.signal_groups:
            group_id = group['id']
            if group_id not in self.signal_features:
                logger.warning(f"Signal group '{group_id}' has no features defined")
    
    @property
    def version(self) -> str:
        """Get model version."""
        return self.metadata.get('version', '1.0.0')
    
    @property
    def name(self) -> str:
        """Get model name."""
        return self.metadata.get('name', self.coverage_type.title())
    
    @property
    def min_premium(self) -> float:
        """Get minimum premium."""
        return self.metadata.get('min_premium', 5000)
    
    def get_enum(self, feature_name: str) -> Optional[Type[Enum]]:
        """Get enum class for a categorical feature."""
        return self._enums.get(feature_name)
    
    def get_modifier(self, feature_name: str, value: str) -> float:
        """Get pricing modifier for a categorical value."""
        feature = self.categorical_features.get(feature_name, {})
        for v in feature.get('values', []):
            if v['id'] == value:
                return v.get('modifier', 1.0)
        return 1.0
    
    def get_tier_for_score(self, score: float) -> Tuple[RiskTier, str, float]:
        """
        Get tier, label, and modifier for a composite score.
        
        Returns:
            Tuple of (RiskTier, tier_label, tier_modifier)
        """
        for tier_key in ['tier_1', 'tier_2', 'tier_3', 'tier_4', 'tier_5']:
            tier_config = self.tier_thresholds.get(tier_key, {})
            min_score = tier_config.get('min_score', 0)
            max_score = tier_config.get('max_score', 1000)
            
            if min_score <= score <= max_score:
                tier_num = int(tier_key.split('_')[1])
                return (
                    RiskTier(tier_num),
                    tier_config.get('label', f'TIER_{tier_num}'),
                    tier_config.get('modifier', 1.0)
                )
        
        # Default to tier 5 if no match
        return RiskTier.TIER_5, "DECLINE", 2.75
    
    def get_signal_config(self, group_id: str, signal_id: str) -> Optional[Dict]:
        """Get configuration for a specific signal."""
        group_signals = self.signal_features.get(group_id, [])
        for signal in group_signals:
            if signal['id'] == signal_id:
                return signal
        return None
    
    def get_signal_ttl(self, group_id: str, signal_id: str) -> int:
        """Get TTL in seconds for a signal."""
        config = self.get_signal_config(group_id, signal_id)
        if config:
            return config.get('ttl_seconds', 86400)  # Default 24h
        return 86400
    
    def get_test_profile(self, profile_name: str) -> Optional[Dict]:
        """Get test profile configuration."""
        return self.test_profiles.get(profile_name)
    
    def get_all_signal_types(self) -> List[str]:
        """Get list of all signal type IDs."""
        signals = []
        for group_id, group_signals in self.signal_features.items():
            for signal in group_signals:
                signals.append(signal['id'])
        return signals
    
    def get_group_weight(self, group_id: str) -> float:
        """Get weight for a signal group."""
        group = self._signal_group_map.get(group_id, {})
        return group.get('weight', 0.0)


# =============================================================================
# SIGNAL COLLECTION
# =============================================================================

@dataclass
class SignalInput:
    """Input signals organized by group."""
    network_authority: Dict[str, float] = field(default_factory=dict)
    safety_record: Dict[str, float] = field(default_factory=dict)
    regulatory_compliance: Dict[str, float] = field(default_factory=dict)
    operational_quality: Dict[str, float] = field(default_factory=dict)
    fleet_quality: Dict[str, float] = field(default_factory=dict)
    financial_stability: Dict[str, float] = field(default_factory=dict)
    route_risk: Dict[str, float] = field(default_factory=dict)
    corporate_governance: Dict[str, float] = field(default_factory=dict)
    
    def get_group(self, group_id: str) -> Dict[str, float]:
        """Get signals for a group by ID."""
        return getattr(self, group_id, {})
    
    def to_dict(self) -> Dict[str, Dict[str, float]]:
        """Convert to dictionary."""
        return {
            'network_authority': self.network_authority,
            'safety_record': self.safety_record,
            'regulatory_compliance': self.regulatory_compliance,
            'operational_quality': self.operational_quality,
            'fleet_quality': self.fleet_quality,
            'financial_stability': self.financial_stability,
            'route_risk': self.route_risk,
            'corporate_governance': self.corporate_governance,
        }


@dataclass
class DirectInquiryInput:
    """Direct inquiry responses."""
    pending_claims: bool = False
    regulatory_action: bool = False
    coverage_declined: bool = False
    fleet_change: bool = False
    route_expansion: bool = False
    ownership_change: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary."""
        return {
            'pending_claims': self.pending_claims,
            'regulatory_action': self.regulatory_action,
            'coverage_declined': self.coverage_declined,
            'fleet_change': self.fleet_change,
            'route_expansion': self.route_expansion,
            'ownership_change': self.ownership_change,
        }
    
    def has_critical_flags(self) -> bool:
        """Check if any critical flags are set."""
        return self.pending_claims or self.regulatory_action or self.coverage_declined


# =============================================================================
# CONFIG-DRIVEN PRICING ENGINE
# =============================================================================

class DSIPricingEngine:
    """
    Config-driven pricing engine that loads behavior from YAML.
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize engine with configuration.
        
        Args:
            config: Loaded ModelConfig instance
        """
        self.config = config
        logger.info(f"Initialized {config.name} pricing engine")
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'DSIPricingEngine':
        """
        Factory method to create engine from YAML path.
        
        Args:
            config_path: Path to YAML configuration
            
        Returns:
            Configured DSIPricingEngine instance
        """
        config = ModelConfig(config_path)
        return cls(config)
    
    def calculate_category_scores(self, signals: SignalInput) -> List[CategoryScore]:
        """
        Calculate scores for each signal category/group.
        
        Args:
            signals: Input signals organized by group
            
        Returns:
            List of CategoryScore objects
        """
        category_scores = []
        
        for group_config in self.config.signal_groups:
            group_id = group_config['id']
            group_name = group_config['name']
            weight = group_config['weight']
            
            # Get signals for this group
            group_signals = signals.get_group(group_id)
            
            # Calculate average score from populated signals
            if group_signals:
                populated = [(k, v) for k, v in group_signals.items() if v > 0]
                if populated:
                    avg_score = sum(v for _, v in populated) / len(populated)
                else:
                    avg_score = 0.0
                coverage = len(populated) / len(group_signals) if group_signals else 0.0
            else:
                avg_score = 0.0
                coverage = 0.0
            
            category_scores.append(CategoryScore(
                category_name=group_name,
                category_id=group_id,
                score=avg_score,
                weight=weight,
                weighted_contribution=avg_score * weight,
                signal_count=len(group_signals) if group_signals else 0,
                coverage=coverage,
            ))
        
        return category_scores
    
    def calculate_composite_score(self, category_scores: List[CategoryScore]) -> float:
        """
        Calculate composite score from category scores.
        
        Args:
            category_scores: List of category scores
            
        Returns:
            Composite score (0-1000 scale)
        """
        total_weighted = sum(cs.weighted_contribution for cs in category_scores)
        total_weight = sum(cs.weight for cs in category_scores)
        
        if total_weight > 0:
            # Average score on 0-100 scale, convert to 0-1000
            return (total_weighted / total_weight) * 10
        return 0.0
    
    def identify_red_flags(
        self, 
        signals: SignalInput, 
        direct: DirectInquiryInput
    ) -> List[str]:
        """
        Identify red flag conditions from signals and direct inquiry.
        
        Args:
            signals: Signal inputs
            direct: Direct inquiry responses
            
        Returns:
            List of red flag messages
        """
        flags = []
        
        # Check signal-based red flags
        for group_id, group_signals in signals.to_dict().items():
            group_features = self.config.signal_features.get(group_id, [])
            
            for signal_config in group_features:
                signal_id = signal_config['id']
                signal_value = group_signals.get(signal_id, 0)
                
                if signal_value > 0:
                    # Check critical threshold
                    threshold = signal_config.get('red_flag_threshold')
                    if threshold and signal_value < threshold:
                        flags.append(f"Low {signal_config.get('name', signal_id)}: {signal_value}")
        
        # Check direct inquiry flags
        if direct.pending_claims:
            flags.append("Pending aviation liability claims")
        if direct.regulatory_action:
            flags.append("Pending regulatory enforcement action")
        if direct.coverage_declined:
            flags.append("Prior coverage declined or non-renewed")
        
        return flags
    
    def identify_green_flags(self, signals: SignalInput) -> List[str]:
        """
        Identify positive indicators from signals.
        
        Args:
            signals: Signal inputs
            
        Returns:
            List of green flag messages
        """
        flags = []
        
        # Check configured green flag rules
        for rule in self.config.green_flag_rules:
            condition = rule.get('condition', '')
            message = rule.get('message', '')
            
            # Parse simple conditions like "alliance_membership_score >= 80"
            if '>=' in condition:
                parts = condition.split('>=')
                if len(parts) == 2:
                    signal_id = parts[0].strip()
                    threshold = float(parts[1].strip())
                    
                    # Find signal value
                    for group_id, group_signals in signals.to_dict().items():
                        if signal_id in group_signals:
                            if group_signals[signal_id] >= threshold:
                                flags.append(message)
                            break
        
        return flags
    
    def determine_decision(
        self, 
        tier: RiskTier, 
        red_flags: List[str],
        direct: DirectInquiryInput
    ) -> Tuple[str, str, str]:
        """
        Determine underwriting decision based on tier and flags.
        
        Args:
            tier: Risk tier
            red_flags: List of red flags
            direct: Direct inquiry responses
            
        Returns:
            Tuple of (decision, rationale, decision_path)
        """
        # Auto-decline conditions
        tier_config = self.config.tier_thresholds.get(f'tier_{tier.value}', {})
        
        if tier_config.get('auto_decline') or direct.coverage_declined:
            return "DECLINE", "Risk outside appetite", "declined"
        
        if direct.regulatory_action:
            return "DECLINE", "Pending regulatory action", "declined"
        
        # Critical red flags
        critical_flags = [f for f in red_flags if any(
            x in f.lower() for x in ['fatal', 'certificate', 'eu safety', 'declined']
        )]
        
        if critical_flags:
            return "DECLINE", f"Critical: {critical_flags[0]}", "declined"
        
        # Auto-approve conditions
        if tier_config.get('auto_approve') and len(red_flags) == 0:
            return "APPROVE", f"{tier_config.get('label')} risk - auto-approve", "straight_through"
        
        # Default to referral
        if tier.value <= 2 and len(red_flags) <= 1:
            return "APPROVE", "Low risk with minor concerns", "referred"
        elif tier.value <= 3:
            return "REVIEW", "Requires underwriter review", "referred"
        else:
            return "REVIEW", "High risk - senior review required", "referred"
    
    def calculate_premium(
        self,
        operator_type: str,
        fleet_category: str,
        fleet_size: str,
        regulatory_framework: str,
        iosa_status: str,
        tier: RiskTier,
        tier_modifier: float,
        hull_value: float,
        liability_limit: float,
        deductible: Optional[float] = None
    ) -> PricingResult:
        """
        Calculate premium based on configuration.
        
        Args:
            operator_type: Operator type ID
            fleet_category: Fleet category ID
            fleet_size: Fleet size ID
            regulatory_framework: Regulatory framework ID
            iosa_status: IOSA status ID
            tier: Risk tier
            tier_modifier: Tier-based modifier
            hull_value: Hull insured value
            liability_limit: Liability limit
            deductible: Optional deductible amount
            
        Returns:
            PricingResult with premium breakdown
        """
        pricing = self.config.pricing
        
        # Get base rates
        hull_rates = pricing.get('hull_rates', {})
        liability_rates = pricing.get('liability_rates', {})
        
        hull_rate = hull_rates.get(operator_type, 2000)
        liability_rate = liability_rates.get(liability_limit, 1000)
        
        # Calculate hull premium
        hull_factor = hull_value / 1_000_000
        hull_premium = hull_rate * hull_factor
        
        # Calculate liability premium with ILF
        ilf = self._get_ilf(liability_limit, pricing.get('ilf_curve', {}))
        liability_premium = liability_rate * ilf
        
        # Base premium
        base_premium = hull_premium + liability_premium
        
        # Apply modifiers
        fleet_mod = self.config.get_modifier('fleet_category', fleet_category)
        size_mod = self.config.get_modifier('fleet_size', fleet_size)
        reg_mod = self.config.get_modifier('regulatory_framework', regulatory_framework)
        iosa_mod = self.config.get_modifier('iosa_status', iosa_status)
        
        total_modifier = fleet_mod * size_mod * reg_mod * iosa_mod * tier_modifier
        
        # Apply deductible credit
        deductible_credit = 0.0
        if deductible and hull_value > 0:
            deductible_pct = deductible / hull_value
            for credit_band in pricing.get('deductible_credits', []):
                min_pct = credit_band.get('min_pct', 0)
                max_pct = credit_band.get('max_pct', float('inf'))
                if min_pct <= deductible_pct < (max_pct or float('inf')):
                    deductible_credit = credit_band.get('credit', 0)
                    break
        
        # Calculate final premium
        risk_adjusted = base_premium * total_modifier * (1 - deductible_credit)
        risk_adjusted = max(risk_adjusted, self.config.min_premium)
        
        # Taxes and fees
        taxes_fees_rate = pricing.get('taxes_fees_rate', 0.05)
        taxes_fees = risk_adjusted * taxes_fees_rate
        
        return PricingResult(
            base_premium=base_premium,
            risk_adjusted_premium=risk_adjusted,
            total_modifier=total_modifier,
            hull_premium=hull_premium,
            liability_premium=liability_premium,
            deductible_credit=deductible_credit,
            taxes_fees=taxes_fees,
            rate_components={
                'hull_rate': hull_rate,
                'liability_rate': liability_rate,
                'fleet_modifier': fleet_mod,
                'size_modifier': size_mod,
                'regulatory_modifier': reg_mod,
                'iosa_modifier': iosa_mod,
                'tier_modifier': tier_modifier,
                'ilf': ilf,
            }
        )
    
    def _get_ilf(self, limit: float, ilf_curve: Dict) -> float:
        """Get Increased Limit Factor for a liability limit."""
        factors = ilf_curve.get('factors', [])
        if not factors:
            return 1.0
        
        # Find appropriate factor
        for i, factor_def in enumerate(factors):
            if limit <= factor_def['limit']:
                if i == 0:
                    return factor_def['factor']
                # Interpolate between brackets
                prev = factors[i-1]
                ratio = (limit - prev['limit']) / (factor_def['limit'] - prev['limit'])
                return prev['factor'] + ratio * (factor_def['factor'] - prev['factor'])
        
        # Above highest bracket - extrapolate
        return factors[-1]['factor']
    
    def assess(
        self,
        entity_name: str,
        operator_type: str,
        fleet_category: str,
        fleet_size: str,
        regulatory_framework: str,
        iosa_status: str,
        signals: SignalInput,
        direct: DirectInquiryInput,
        hull_value: float = 50_000_000,
        liability_limit: float = 500_000_000,
        deductible: Optional[float] = None,
        entity_id: Optional[str] = None,
    ) -> DSIAssessment:
        """
        Perform complete assessment for an entity.
        
        Args:
            entity_name: Entity/company name
            operator_type: Operator type ID
            fleet_category: Fleet category ID
            fleet_size: Fleet size ID
            regulatory_framework: Regulatory framework ID
            iosa_status: IOSA status ID
            signals: Signal inputs
            direct: Direct inquiry responses
            hull_value: Hull insured value
            liability_limit: Liability limit
            deductible: Optional deductible
            entity_id: Optional entity identifier
            
        Returns:
            Complete DSIAssessment
        """
        # Calculate category scores
        category_scores = self.calculate_category_scores(signals)
        
        # Calculate composite score
        composite_score = self.calculate_composite_score(category_scores)
        
        # Apply critical overrides
        safety_signals = signals.safety_record
        reg_signals = signals.regulatory_compliance
        
        if safety_signals.get('fatality_history_score', 100) < 50:
            composite_score = min(composite_score, 450)
        if reg_signals.get('eu_safety_list_score', 100) < 30:
            composite_score = min(composite_score, 200)
        
        # Determine tier
        tier, tier_label, tier_modifier = self.config.get_tier_for_score(composite_score)
        
        # Identify flags
        red_flags = self.identify_red_flags(signals, direct)
        green_flags = self.identify_green_flags(signals)
        
        # Determine decision
        decision, rationale, decision_path = self.determine_decision(tier, red_flags, direct)
        
        # Calculate premium
        pricing_result = self.calculate_premium(
            operator_type=operator_type,
            fleet_category=fleet_category,
            fleet_size=fleet_size,
            regulatory_framework=regulatory_framework,
            iosa_status=iosa_status,
            tier=tier,
            tier_modifier=tier_modifier,
            hull_value=hull_value,
            liability_limit=liability_limit,
            deductible=deductible,
        )
        
        # Calculate signal coverage
        total_signals = sum(cs.signal_count for cs in category_scores)
        populated_signals = sum(
            cs.signal_count * cs.coverage for cs in category_scores
        )
        signal_coverage = populated_signals / total_signals if total_signals > 0 else 0.0
        
        # Build assessment
        return DSIAssessment(
            entity_name=entity_name,
            entity_id=entity_id,
            operator_type=operator_type,
            fleet_category=fleet_category,
            fleet_size=fleet_size,
            regulatory_framework=regulatory_framework,
            iosa_status=iosa_status,
            category_scores=category_scores,
            composite_score=composite_score,
            tier=tier,
            tier_label=tier_label,
            confidence=min(0.95, signal_coverage * 0.9 + 0.1),
            signal_coverage=signal_coverage,
            red_flags=red_flags,
            green_flags=green_flags,
            decision=decision,
            decision_rationale=rationale,
            decision_path=decision_path,
            base_premium=pricing_result.base_premium,
            risk_adjusted_premium=pricing_result.risk_adjusted_premium,
            premium_modifier=pricing_result.total_modifier,
            hull_value=hull_value,
            liability_limit=liability_limit,
            rate_per_million=pricing_result.rate_components.get('hull_rate', 0),
            model_version=self.config.version,
            coverage_type=self.config.coverage_type,
            assessment_date=datetime.utcnow(),
        )


# =============================================================================
# TEST DATA GENERATOR (Uses Config)
# =============================================================================

class ConfigTestDataGenerator:
    """
    Generates test data from configuration test profiles.
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize with configuration.
        
        Args:
            config: Loaded ModelConfig
        """
        self.config = config
    
    def generate_signal_input(self, profile_name: str) -> SignalInput:
        """
        Generate SignalInput from a test profile.
        
        Args:
            profile_name: Name of test profile (e.g., 'excellent_safety')
            
        Returns:
            SignalInput populated from profile
        """
        profile = self.config.get_test_profile(profile_name)
        if not profile:
            raise ValueError(f"Unknown test profile: {profile_name}")
        
        signals = profile.get('signals', {})
        
        return SignalInput(
            network_authority=signals.get('network_authority', {}),
            safety_record=signals.get('safety_record', {}),
            regulatory_compliance=signals.get('regulatory_compliance', {}),
            operational_quality=signals.get('operational_quality', {}),
            fleet_quality=signals.get('fleet_quality', {}),
            financial_stability=signals.get('financial_stability', {}),
            route_risk=signals.get('route_risk', {}),
            corporate_governance=signals.get('corporate_governance', {}),
        )
    
    def get_expected_tier_range(self, profile_name: str) -> Tuple[int, int]:
        """Get expected tier range for a profile."""
        profile = self.config.get_test_profile(profile_name)
        if not profile:
            return (1, 5)
        return tuple(profile.get('expected_tier', [1, 5]))
    
    def get_expected_score_range(self, profile_name: str) -> Tuple[int, int]:
        """Get expected score range for a profile."""
        profile = self.config.get_test_profile(profile_name)
        if not profile:
            return (0, 1000)
        return tuple(profile.get('expected_score_range', [0, 1000]))
    
    def get_categorical_values(self, profile_name: str) -> Dict[str, str]:
        """Get categorical feature values for a profile."""
        profile = self.config.get_test_profile(profile_name)
        if not profile:
            return {}
        
        return {
            'operator_type': profile.get('operator_type', 'REGIONAL_AIRLINE'),
            'fleet_category': profile.get('fleet_category', 'NARROWBODY'),
            'fleet_size': profile.get('fleet_size', 'MEDIUM'),
            'regulatory_framework': profile.get('regulatory_framework', 'FAA'),
            'iosa_status': profile.get('iosa_status', 'REGISTERED'),
        }
    
    def list_profiles(self) -> List[str]:
        """List available test profile names."""
        return list(self.config.test_profiles.keys())


# =============================================================================
# BACKWARD COMPATIBILITY LAYER
# =============================================================================
# These provide the same interface as the original aerospace model

class DSIAerospaceEngine(DSIPricingEngine):
    """
    Backward-compatible wrapper for aerospace pricing.
    
    Provides the same interface as the original dsi_aerospace_pricing.py
    but uses the config-driven engine internally.
    """
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize aerospace engine.
        
        Args:
            config_path: Path to config YAML (uses default if None)
        """
        if config_path is None:
            config_path = str(self.DEFAULT_CONFIG_PATH)
        
        config = ModelConfig(config_path)
        super().__init__(config)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_assessment(assessment: DSIAssessment):
    """Print formatted assessment report."""
    print("=" * 70)
    print("DSI ASSESSMENT REPORT")
    print("=" * 70)
    print(f"\nEntity: {assessment.entity_name}")
    print(f"Coverage: {assessment.coverage_type}")
    print(f"Model Version: {assessment.model_version}")
    print(f"\nClassification:")
    print(f"  Operator: {assessment.operator_type}")
    print(f"  Fleet: {assessment.fleet_category} | Size: {assessment.fleet_size}")
    print(f"  Regulatory: {assessment.regulatory_framework} | IOSA: {assessment.iosa_status}")
    
    print(f"\n{'─' * 70}")
    print(f"COMPOSITE SCORE: {assessment.composite_score:.0f}/1000")
    print(f"TIER: {assessment.tier_label} ({assessment.tier.name})")
    print(f"CONFIDENCE: {assessment.confidence:.0%}")
    print(f"SIGNAL COVERAGE: {assessment.signal_coverage:.0%}")
    print(f"{'─' * 70}")
    
    print("\nCATEGORY SCORES:")
    for cat in assessment.category_scores:
        bar_len = int(cat.score / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {cat.category_name:25} {cat.score:5.1f}/100 {bar} (w={cat.weight:.2f})")
    
    if assessment.green_flags:
        print(f"\n✓ GREEN FLAGS: {', '.join(assessment.green_flags[:3])}")
    if assessment.red_flags:
        print(f"⚠ RED FLAGS: {', '.join(assessment.red_flags[:3])}")
    
    print(f"\n{'─' * 70}")
    print(f"DECISION: {assessment.decision}")
    print(f"PATH: {assessment.decision_path}")
    print(f"RATIONALE: {assessment.decision_rationale}")
    
    print(f"\n{'─' * 70}")
    print(f"PRICING:")
    print(f"  Hull Value: ${assessment.hull_value:,.0f}")
    print(f"  Liability Limit: ${assessment.liability_limit:,.0f}")
    print(f"  Base Premium: ${assessment.base_premium:,.0f}")
    print(f"  Modifier: {assessment.premium_modifier:.2f}x")
    print(f"  Final Premium: ${assessment.risk_adjusted_premium:,.0f}")
    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Find config file
    config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        print(f"Config not found at {config_path}")
        print("Please ensure config.yaml exists in the same directory")
        sys.exit(1)
    
    # Create engine
    engine = DSIPricingEngine.from_yaml(str(config_path))
    
    # Create test data generator
    test_gen = ConfigTestDataGenerator(engine.config)
    
    print("Available test profiles:", test_gen.list_profiles())
    
    # Run assessment with excellent profile
    print("\n" + "=" * 70)
    print("TESTING: Excellent Safety Profile")
    print("=" * 70)
    
    signals = test_gen.generate_signal_input('excellent_safety')
    categoricals = test_gen.get_categorical_values('excellent_safety')
    
    assessment = engine.assess(
        entity_name="SkyExcellence Airlines",
        signals=signals,
        direct=DirectInquiryInput(),
        hull_value=500_000_000,
        liability_limit=1_000_000_000,
        **categoricals
    )
    
    print_assessment(assessment)
    
    expected_tier = test_gen.get_expected_tier_range('excellent_safety')
    expected_score = test_gen.get_expected_score_range('excellent_safety')
    
    print(f"\nValidation:")
    print(f"  Expected Tier: {expected_tier} -> Actual: {assessment.tier.value}")
    print(f"  Expected Score: {expected_score} -> Actual: {assessment.composite_score:.0f}")
    
    tier_ok = expected_tier[0] <= assessment.tier.value <= expected_tier[1]
    score_ok = expected_score[0] <= assessment.composite_score <= expected_score[1]
    
    print(f"  Tier Check: {'✓ PASS' if tier_ok else '✗ FAIL'}")
    print(f"  Score Check: {'✓ PASS' if score_ok else '✗ FAIL'}")
