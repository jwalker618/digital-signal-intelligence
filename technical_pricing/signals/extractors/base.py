"""
Signal Data Extraction Framework
"""

from __future__ import annotations

import hashlib
import logging
import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# TTL CONFIGURATION
# =============================================================================

class TTLCategory(Enum):
    """Time-to-live categories for signal freshness requirements."""
    REAL_TIME = "real_time"      # 1 hour - sanctions, breaking events
    DYNAMIC = "dynamic"          # 24 hours - inspections, incidents, violations
    SEMI_STATIC = "semi_static"  # 7 days - ratings, certifications, fleet data
    STATIC = "static"            # 90 days - registrations, long-term relationships


@dataclass
class TTLConfig:
    """TTL configuration for an extractor or signal."""
    category: TTLCategory
    ttl_seconds: int
    description: str = ""
    
    @classmethod
    def real_time(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.REAL_TIME, 3600, description)
    
    @classmethod
    def dynamic(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.DYNAMIC, 86400, description)
    
    @classmethod
    def semi_static(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.SEMI_STATIC, 604800, description)
    
    @classmethod
    def static(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.STATIC, 7776000, description)
    
    def is_stale(self, last_fetched: datetime) -> bool:
        """Check if data needs refresh based on TTL."""
        age_seconds = (datetime.now() - last_fetched).total_seconds()
        return age_seconds > self.ttl_seconds


@dataclass
class DataSource:
    """Represents a single data source for a signal."""
    source_type: str  # api, scrape, filing, dns, scan, satellite, correlation, registry
    provider: str
    endpoint: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Lower = higher priority for fallback
    
    def __str__(self) -> str:
        return f"{self.source_type}:{self.provider}" + (f"/{self.endpoint}" if self.endpoint else "")


# =============================================================================
# SIGNAL RESULT HANDLING
# =============================================================================

@dataclass
class SignalResult:
    """Result from extracting a single signal."""
    signal_id: str
    value: Optional[Any]
    confidence: float  # 0.0 to 1.0
    source_used: Optional[DataSource]
    ttl_config: TTLConfig
    fetched_at: datetime
    is_missing: bool = False
    error: Optional[str] = None
    all_sources_tried: List[str] = field(default_factory=list)
    
    @classmethod
    def missing(cls, signal_id: str, ttl: TTLConfig, error: str = "Signal not available") -> "SignalResult":
        """Create a missing signal result."""
        return cls(
            signal_id=signal_id,
            value=None,
            confidence=0.0,
            source_used=None,
            ttl_config=ttl,
            fetched_at=datetime.now(),
            is_missing=True,
            error=error
        )


@dataclass
class ExtractionResult:
    """Complete extraction result with all signals."""
    source: str
    source_type: str
    timestamp: str
    raw_data: Dict[str, Any]
    signals: Dict[str, SignalResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    ttl_config: Optional[TTLConfig] = None


# =============================================================================
# MISSING SIGNAL HANDLING STRATEGIES
# =============================================================================

class MissingSignalStrategy(Enum):
    """How to handle missing signals in composite calculations."""
    EXCLUDE = "exclude"           # Remove from weighted calculation
    USE_DEFAULT = "use_default"   # Use coverage-specific default value
    PENALIZE = "penalize"         # Apply penalty score
    REQUIRE = "require"           # Fail the entire calculation


@dataclass
class SignalWeightConfig:
    """Configuration for signal weighting in composites."""
    weight: float
    missing_strategy: MissingSignalStrategy = MissingSignalStrategy.EXCLUDE
    default_value: Optional[float] = None
    penalty_value: float = 25.0  # Score to use if PENALIZE strategy
    min_confidence: float = 0.5  # Minimum confidence to include signal


def calculate_weighted_score(
    signal_scores: Dict[str, Tuple[float, float, SignalWeightConfig]],  # signal_id -> (score, confidence, config)
    min_signals_required: int = 1,
    min_weight_coverage: float = 0.5
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Calculate weighted composite score with missing signal handling.
    
    Args:
        signal_scores: Dict mapping signal_id to (score, confidence, weight_config)
        min_signals_required: Minimum number of valid signals required
        min_weight_coverage: Minimum percentage of total weight that must be covered
    
    Returns:
        Tuple of (composite_score or None, metadata_dict)
    """
    valid_signals = []
    excluded_signals = []
    penalty_signals = []
    required_missing = []
    total_configured_weight = sum(cfg.weight for _, _, cfg in signal_scores.values())
    
    for signal_id, (score, confidence, config) in signal_scores.items():
        # Check if signal is missing or low confidence
        is_missing = score is None or confidence < config.min_confidence
        
        if is_missing:
            if config.missing_strategy == MissingSignalStrategy.REQUIRE:
                required_missing.append(signal_id)
            elif config.missing_strategy == MissingSignalStrategy.EXCLUDE:
                excluded_signals.append(signal_id)
            elif config.missing_strategy == MissingSignalStrategy.USE_DEFAULT:
                if config.default_value is not None:
                    valid_signals.append((signal_id, config.default_value, config.weight, 0.5))
                else:
                    excluded_signals.append(signal_id)
            elif config.missing_strategy == MissingSignalStrategy.PENALIZE:
                penalty_signals.append(signal_id)
                valid_signals.append((signal_id, config.penalty_value, config.weight, 0.3))
        else:
            valid_signals.append((signal_id, score, config.weight, confidence))
    
    # Check if required signals are missing
    if required_missing:
        return None, {
            "error": f"Required signals missing: {required_missing}",
            "valid_count": len(valid_signals),
            "excluded": excluded_signals,
            "required_missing": required_missing
        }
    
    # Check minimum signal count
    if len(valid_signals) < min_signals_required:
        return None, {
            "error": f"Insufficient signals: {len(valid_signals)} < {min_signals_required}",
            "valid_count": len(valid_signals),
            "excluded": excluded_signals
        }
    
    # Check minimum weight coverage
    covered_weight = sum(w for _, _, w, _ in valid_signals)
    weight_coverage = covered_weight / total_configured_weight if total_configured_weight > 0 else 0
    
    if weight_coverage < min_weight_coverage:
        return None, {
            "error": f"Insufficient weight coverage: {weight_coverage:.2%} < {min_weight_coverage:.2%}",
            "weight_coverage": weight_coverage,
            "excluded": excluded_signals
        }
    
    # Calculate weighted average (normalize weights to sum to 1)
    if covered_weight == 0:
        return None, {"error": "No valid weight coverage"}
    
    weighted_sum = sum(score * weight for _, score, weight, _ in valid_signals)
    composite_score = weighted_sum / covered_weight
    
    # Calculate confidence-weighted score (optional refinement)
    confidence_weighted_sum = sum(score * weight * conf for _, score, weight, conf in valid_signals)
    total_conf_weight = sum(weight * conf for _, _, weight, conf in valid_signals)
    confidence_adjusted_score = confidence_weighted_sum / total_conf_weight if total_conf_weight > 0 else composite_score
    
    return composite_score, {
        "composite_score": composite_score,
        "confidence_adjusted_score": confidence_adjusted_score,
        "valid_signals": len(valid_signals),
        "excluded_signals": excluded_signals,
        "penalty_signals": penalty_signals,
        "weight_coverage": weight_coverage,
        "signal_breakdown": {sid: {"score": s, "weight": w, "confidence": c} 
                           for sid, s, w, c in valid_signals}
    }

# =============================================================================
# REGISTRY & BASE CLASSES
# =============================================================================

EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}


def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    """Decorator to register extractor classes."""
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls


class DataExtractor(ABC):
    """
    Base class for all data extractors.
    
    Each extractor must define:
    - source_name: Primary data source identifier
    - coverage: Coverage line (marine, aerospace, cyber, etc.)
    - signals: List of signals this extractor provides
    - ttl_config: Time-to-live configuration
    - alternative_sources: List of alternative DataSource objects for fallback
    """
    
    def __init__(self, seed: Optional[str] = None, **kwargs: Any):
        self.seed = seed
        self.kwargs = kwargs
        self._rng = self._create_rng(seed)
        self._last_fetch: Optional[datetime] = None
    
    def _create_rng(self, seed: Optional[str]) -> random.Random:
        rng = random.Random()
        if seed:
            rng.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16))
        return rng
    
    def _random_date(self, start_days_ago: int = 365, end_days_ago: int = 0) -> str:
        days_ago = self._rng.randint(min(end_days_ago, start_days_ago), max(end_days_ago, start_days_ago))
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    def _weighted_choice(self, choices: List[Tuple[Any, float]]) -> Any:
        items, weights = zip(*choices)
        return self._rng.choices(items, weights=weights, k=1)[0]
    
    def _random_id(self, prefix: str = "", length: int = 8) -> str:
        chars = string.ascii_uppercase + string.digits
        return f"{prefix}{''.join(self._rng.choices(chars, k=length))}"
    
    def _random_company_name(self, industry: str = "Corp") -> str:
        prefixes = ["Global", "Premier", "Pacific", "Atlantic", "Continental", "United", "Allied", "National"]
        suffixes = ["Holdings", "Group", "Partners", "Corp", "Ltd", "Inc", "LLC"]
        return f"{self._rng.choice(prefixes)} {industry} {self._rng.choice(suffixes)}"
    
    def needs_refresh(self) -> bool:
        """Check if data needs refresh based on TTL."""
        if self._last_fetch is None:
            return True
        return self.ttl_config.is_stale(self._last_fetch)
    
    @abstractmethod
    def extract(self) -> ExtractionResult:
        """Extract data from source(s). Implement in subclasses."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Primary source identifier."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def coverage(self) -> str:
        """Coverage line this extractor serves."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def signals(self) -> List[str]:
        """List of signals this extractor provides."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def ttl_config(self) -> TTLConfig:
        """TTL configuration for this extractor."""
        raise NotImplementedError
    
    @property
    def alternative_sources(self) -> List[DataSource]:
        """Alternative data sources for fallback. Override in subclasses."""
        return []


# =============================================================================
# EXTRACTOR REGISTRY & UTILITIES
# =============================================================================

# Signal coverage mapping by coverage line
COVERAGE_SIGNAL_MAP: Dict[str, Dict[str, List[str]]] = {
    "marine": {
        "network_authority": ["classification_society", "pi_club", "charterer_quality", "banking_relationship", 
                            "flag_state", "industry_association", "technical_manager", "port_relationship"],
        "safety_compliance": ["psc_detention", "psc_deficiency", "class_status", "ism_compliance", 
                             "casualty_history", "total_loss"],
        "operational_telemetry": ["ais_compliance", "dark_activity", "route_risk", "psc_region_exposure",
                                 "operational_efficiency", "weather_routing"],
        "sanctions_compliance": ["sanctions_status", "ownership_transparency", "jurisdiction_risk",
                                "sts_pattern", "historical_sanctions"],
        "fleet_profile": ["fleet_age", "fleet_stability", "vessel_quality", "crew_certification",
                         "management_consistency"],
        "environmental": ["imo2020_compliance", "bwm_compliance", "cii_rating", "environmental_incident"],
        "corporate_footprint": ["website_quality", "fleet_disclosure", "sustainability_reporting",
                               "safety_communication", "crew_welfare", "industry_presence"],
        "structured_data": ["vetting_score", "esg_rating", "credit_rating"],
    },
    "aerospace": {
        "safety_record": ["accident_history", "incident_history", "accident_rate", "fatality_history",
                         "investigation_findings"],
        "regulatory_compliance": ["certificate_status", "enforcement_actions", "iosa_audit_status",
                                 "ramp_inspection", "eu_safety_list", "state_safety_rating"],
        "operational_quality": ["otp_score", "dispatch_reliability", "crew_experience",
                               "training_indicators", "operational_complexity", "growth_rate"],
        "fleet_quality": ["fleet_age", "fleet_homogeneity", "aircraft_generation", "order_backlog",
                         "maintenance_indicators"],
        "financial_stability": ["credit_rating", "public_financials", "market_position", "government_support"],
        "network_authority": ["alliance_membership", "codeshare_quality", "lessor_quality",
                             "oem_relationship", "mro_quality"],
        "route_risk": ["conflict_zone_exposure", "challenging_airports", "high_risk_destinations",
                      "weather_exposure", "terrain_exposure"],
        "corporate_governance": ["management_stability", "safety_leadership", "safety_reporting",
                                "corporate_structure", "industry_engagement"],
    },
    "cyber": {
        "technical_infrastructure": ["tls_score", "security_headers", "email_auth", "dnssec", "exposure",
                                    "software_currency", "cve_exposure", "cloud_infrastructure",
                                    "waf_presence", "cdn_usage"],
        "corporate_footprint": ["security_page", "privacy_policy", "security_txt", "bug_bounty",
                               "security_hiring", "technical_content", "developer_resources",
                               "security_leadership", "compliance_badges"],
        "public_record": ["breach_history", "regulatory_action", "litigation_history",
                         "credential_exposure", "dark_web"],
        "structured_data": ["security_rating", "esg_cyber", "credit_rating"],
        "network_authority": ["customer_quality", "partner_quality", "security_vendor",
                             "industry_body", "certification_authority", "financial_relationship",
                             "network_centrality", "second_degree"],
    },
    "d_and_o": {
        "governance": ["board_independence", "board_diversity", "ceo_chair_separation",
                      "committee_structure", "board_refreshment", "related_party",
                      "compensation_structure", "shareholder_rights"],
        "financial": ["audit_opinion", "internal_controls", "restatement", "filing_timeliness",
                     "revenue_recognition", "debt_covenant", "stock_volatility", "short_interest"],
        "litigation": ["securities_litigation", "derivative_litigation", "sec_enforcement",
                      "regulatory_action", "pending_litigation", "whistleblower"],
        "executive": ["executive_stability", "cfo_quality", "insider_trading",
                     "executive_background", "trading_plan"],
        "network_authority": ["auditor_quality", "legal_counsel", "banking_relationship",
                             "investor_quality", "board_network", "index_inclusion", "analyst_coverage"],
        "corporate_footprint": ["investor_relations", "governance_page", "esg_reporting",
                               "press_release", "leadership_visibility", "hiring_signals"],
        "structured_data": ["credit_rating", "esg_rating", "governance_rating", "iss_governance"],
    },
    "financial_institutions": {
        "regulatory_compliance": ["examination_rating", "enforcement_action", "informal_action",
                                 "cra_rating", "bsa_aml", "fair_lending", "consumer_compliance"],
        "financial_condition": ["capital_ratio", "asset_quality", "liquidity", "earnings",
                               "concentration", "interest_rate_risk", "growth_rate"],
        "governance": ["board_independence", "board_expertise", "executive_stability",
                      "risk_committee", "audit_committee", "related_party"],
        "operational_risk": ["cfpb_complaint", "bbb_complaint", "litigation", "breach_history",
                            "operational_incident"],
        "cyber_security": ["tls_score", "email_auth", "security_headers", "network_exposure",
                          "vulnerability", "security_rating"],
        "corporate_footprint": ["investor_relations", "disclosure_quality", "security_page",
                               "hiring_signals", "esg_reporting", "community_presence"],
        "structured_data": ["credit_rating", "esg_rating", "peer_benchmark"],
        "network_authority": ["correspondent_quality", "fhlb_membership", "clearing_relationship",
                             "auditor_quality", "legal_counsel", "industry_association"],
    },
    "energy": {
        "safety_performance": ["osha_trir", "osha_violations", "bsee_incident", "process_safety",
                              "fatality", "major_incident", "near_miss"],
        "environmental_compliance": ["epa_violation", "spill_history", "emissions_compliance",
                                    "flaring", "methane", "remediation"],
        "operational_telemetry": ["production_consistency", "facility_activity", "well_integrity",
                                 "maintenance_pattern", "operational_efficiency"],
        "financial_stability": ["credit_rating", "leverage", "aro_coverage", "capex_trend",
                               "restructuring"],
        "asset_portfolio": ["asset_age", "concentration", "complexity", "decommissioning",
                           "permit_status"],
        "corporate_footprint": ["safety_communication", "esg_reporting", "technical_hiring",
                               "industry_presence", "disclosure_quality", "hse_leadership"],
        "structured_data": ["esg_rating", "benchmark", "credit_rating"],
        "network_authority": ["partner_quality", "contractor_quality", "banking_relationship",
                             "insurance_history", "industry_association", "regulator_relationship",
                             "customer_quality"],
    },
    "professional_indemnity": {
        "regulatory_standing": ["license_status", "disciplinary_history", "malpractice_record",
                               "ce_compliance", "specialty_certification", "peer_review", "pcaob_standing"],
        "network_authority": ["peer_ranking", "client_quality", "referral_network",
                             "association_leadership", "thought_leadership", "panel_membership"],
        "firm_stability": ["tenure", "partner_stability", "staff_retention", "office_stability",
                          "financial_stability", "succession_planning"],
        "practice_quality": ["outcome_patterns", "client_reviews", "work_quality",
                            "fee_dispute", "complaint_history"],
        "technical_infrastructure": ["tls_score", "email_auth", "security_headers",
                                    "portal_security", "breach_history"],
        "corporate_footprint": ["website_quality", "bio_completeness", "practice_clarity",
                               "publications", "community_involvement", "diversity"],
        "litigation_history": ["malpractice_suits", "fee_disputes_litigation", "regulatory_enforcement",
                              "civil_litigation", "bankruptcy"],
    },
}


def get_extractors_for_coverage(coverage: str) -> List[Type[DataExtractor]]:
    """Get all registered extractors for a coverage line."""
    return [
        ext_class for ext_class in EXTRACTOR_REGISTRY.values()
        if ext_class.coverage == coverage or ext_class.coverage == "cross_coverage"
    ]


def get_extractor_by_signal(signal: str) -> Optional[Type[DataExtractor]]:
    """Find extractor that provides a specific signal."""
    for ext_class in EXTRACTOR_REGISTRY.values():
        if signal in ext_class.signals:
            return ext_class
    return None


def list_all_signals() -> Dict[str, List[str]]:
    """List all signals grouped by coverage."""
    return COVERAGE_SIGNAL_MAP.copy()


def get_ttl_summary() -> Dict[str, Dict[str, Any]]:
    """Get TTL configuration summary for all extractors."""
    summary = {}
    for name, ext_class in EXTRACTOR_REGISTRY.items():
        summary[name] = {
            "coverage": ext_class.coverage,
            "signals": ext_class.signals,
            "ttl_category": ext_class.ttl_config.category.value,
            "ttl_seconds": ext_class.ttl_config.ttl_seconds,
            "alternative_sources": len(ext_class.alternative_sources) if hasattr(ext_class, 'alternative_sources') else 0,
        }
    return summary


def print_coverage_report():
    """Print comprehensive coverage report."""
    print("\n" + "=" * 80)
    print("DSI EXTRACTOR COVERAGE REPORT")
    print("=" * 80)
    
    for coverage, signal_groups in COVERAGE_SIGNAL_MAP.items():
        print(f"\n{coverage.upper().replace('_', ' ')}")
        print("-" * 40)
        
        extractors = get_extractors_for_coverage(coverage)
        print(f"  Extractors: {len(extractors)}")
        
        total_signals = sum(len(signals) for signals in signal_groups.values())
        print(f"  Signal Groups: {len(signal_groups)}")
        print(f"  Total Signals: {total_signals}")
        
        for group, signals in signal_groups.items():
            print(f"    • {group}: {len(signals)} signals")
    
    print("\n" + "=" * 80)
    print("TTL DISTRIBUTION")
    print("-" * 40)
    
    ttl_counts = {"real_time": 0, "dynamic": 0, "semi_static": 0, "static": 0}
    for ext_class in EXTRACTOR_REGISTRY.values():
        ttl_counts[ext_class.ttl_config.category.value] += 1
    
    for category, count in ttl_counts.items():
        print(f"  {category}: {count} extractors")
    
    print("\n" + "=" * 80)


# =============================================================================
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print_coverage_report()
    
    # Example: Run marine extractors
    print("\n" + "=" * 80)
    print("SAMPLE EXTRACTION - Marine Coverage")
    print("=" * 80)
    
    marine_extractors = get_extractors_for_coverage("marine")
    print(f"\nFound {len(marine_extractors)} extractors for marine coverage")
    
    # Run first 3 extractors as demo
    for ext_class in marine_extractors[:3]:
        extractor = ext_class(seed="demo_company_123")
        result = extractor.extract()
        print(f"\n{ext_class.__name__}:")
        print(f"  Source: {result.source}")
        print(f"  TTL: {extractor.ttl_config.category.value} ({extractor.ttl_config.ttl_seconds}s)")
        print(f"  Signals: {extractor.signals}")
        print(f"  Alternative Sources: {len(extractor.alternative_sources)}")
