"""
Technical Pricing Data Extraction Framework (v2.0)

REDESIGN OBJECTIVES:
1. Complete coverage of ALL signals from config YAML specification
2. TTL (Time-To-Live) configuration for every signal/extractor
3. Multi-source notation where multiple data providers exist
4. Robust handling of missing/failed signals in composite scoring

Coverage Lines & Signal Groups:
- Marine: 8 signal groups:
  - safety_compliance, 
  - operational_telemetry, 
  - sanctions_compliance, 
  - fleet_profile, 
  - network_authority, 
  - environmental, 
  - corporate_footprint, 
  - structured_data
- Aerospace: 8 signal groups:
  - safety_record, 
  - regulatory_compliance, 
  - operational_quality,
  - fleet_quality, 
  - financial_stability, 
  - network_authority, 
  - route_risk, 
  - corporate_governance
- Cyber: 5 signal groups: 
  - technical_infrastructure, 
  - corporate_footprint, 
  - public_record,
  - structured_data, 
  - network_authority
- D&O: 7 signal groups:
  - governance, 
  - financial, 
  - litigation, 
  - executive, 
  - network_authority,
  - corporate_footprint, 
  - structured_data
- Financial Institutions: 7 signal groups:
  - regulatory_compliance, 
  - financial_condition,
  - governance, 
  - operational_risk, 
  - cyber_security, 
  - corporate_footprint, 
  - structured_data
- Energy: 7 signal groups:
  - safety_performance, 
  - environmental_compliance, 
  - operational_telemetry,
  - financial_stability, 
  - asset_portfolio, 
  - corporate_footprint, 
  - structured_data
- Professional Indemnity: 7 signal groups:
  - regulatory_standing, 
  - network_authority, 
  - firm_stability,
  - practice_quality, 
  - technical_infrastructure, 
  - corporate_footprint, 
  - litigation_history
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
# MARINE EXTRACTORS
# =============================================================================

@register_extractor
class EquasisOperatorExtractor(DataExtractor):
    """
    Equasis API - Fleet composition, ISM compliance, company details.
    
    Signals: operator_type, vessel_category, fleet_stability, management_consistency
    
    Alternative Sources:
    - IHS Markit: ownership/search
    - Clarksons: owners/profile
    - Lloyd's List: companies/search
    """
    source_name = "equasis"
    coverage = "marine"
    signals = ["operator_type", "vessel_category", "fleet_stability", "management_consistency", "fleet_age"]
    ttl_config = TTLConfig.dynamic("Fleet and company data refreshed daily")
    
    alternative_sources = [
        DataSource("api", "ihs_markit", "ownership/search", priority=2),
        DataSource("api", "clarksons", "owners/profile", priority=3),
        DataSource("api", "lloyd_list", "companies/search", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        fleet_size = self._weighted_choice([
            (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 20), 0.35),
            (self._rng.randint(21, 50), 0.20), (self._rng.randint(51, 200), 0.15),
        ])
        vessels = []
        for i in range(fleet_size):
            build_year = self._rng.randint(1995, 2024)
            vessels.append({
                "imo_number": str(self._rng.randint(9000000, 9999999)),
                "vessel_type": self._weighted_choice([
                    ("Container Ship", 0.25), ("Oil Tanker", 0.20), ("Bulk Carrier", 0.20),
                    ("Chemical Tanker", 0.12), ("LNG Carrier", 0.08), ("General Cargo", 0.10), ("Other", 0.05)
                ]),
                "gross_tonnage": self._rng.randint(5000, 180000),
                "build_year": build_year,
                "age_years": 2024 - build_year,
                "flag_state": self._weighted_choice([
                    ("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14),
                    ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08), ("Bahamas", 0.07), ("Other", 0.18)
                ]),
                "classification_society": self._weighted_choice([
                    ("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15),
                    ("ABS", 0.15), ("ClassNK", 0.12), ("Other", 0.16)
                ]),
            })
        
        # Determine operator type based on fleet characteristics
        avg_age = sum(v["age_years"] for v in vessels) / len(vessels) if vessels else 0
        type_counts = {}
        for v in vessels:
            t = v["vessel_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        majority_type = max(type_counts, key=type_counts.get) if type_counts else "Unknown"
        
        # Operator classification logic
        if majority_type == "Container Ship" and fleet_size >= 50:
            operator_type = "major_liner"
        elif majority_type == "Oil Tanker" and fleet_size >= 30:
            operator_type = "major_tanker"
        elif majority_type == "Bulk Carrier" and fleet_size >= 40:
            operator_type = "major_bulk"
        elif fleet_size >= 10:
            operator_type = "regional_operator"
        else:
            operator_type = "tramp_operator"
        
        raw_data = {
            "company": {
                "imo_company_number": self.kwargs.get("company_id", self._random_id("IMO", 7)),
                "company_name": self.kwargs.get("company_name", self._random_company_name("Shipping")),
                "company_status": self._weighted_choice([("Active", 0.95), ("Inactive", 0.05)]),
                "role": self._weighted_choice([("Owner", 0.40), ("Operator", 0.35), ("Manager", 0.25)]),
                "year_established": self._rng.randint(1950, 2020),
            },
            "fleet": {
                "total_vessels": fleet_size,
                "vessels": vessels[:30],
                "average_age": round(avg_age, 1),
                "majority_type": majority_type,
                "type_distribution": type_counts,
            },
            "classification": {
                "operator_type": operator_type,
                "vessel_category": majority_type.lower().replace(" ", "_"),
            },
            "management_history": {
                "years_operating": self._rng.randint(5, 50),
                "manager_changes_5yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "fleet_size": fleet_size,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PSCInspectionExtractor(DataExtractor):
    """
    Port State Control Database - Inspection history, deficiencies, detentions.
    
    Signals: psc_detention, psc_deficiency, safety_compliance
    
    Alternative Sources:
    - Paris MoU: inspections/search
    - Tokyo MoU: inspections/search  
    - US Coast Guard: psc/search
    """
    source_name = "psc_database"
    coverage = "marine"
    signals = ["psc_detention", "psc_deficiency", "safety_compliance"]
    ttl_config = TTLConfig.dynamic("PSC inspections updated daily")
    
    alternative_sources = [
        DataSource("api", "paris_mou", "inspections/search", priority=1),
        DataSource("api", "tokyo_mou", "inspections/search", priority=2),
        DataSource("api", "uscg", "psc/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_inspections = self._rng.randint(3, 15)
        inspections = []
        total_deficiencies = 0
        total_detentions = 0
        
        for _ in range(num_inspections):
            deficiency_count = self._weighted_choice([
                (0, 0.35), (self._rng.randint(1, 3), 0.35),
                (self._rng.randint(4, 8), 0.20), (self._rng.randint(9, 15), 0.10)
            ])
            detained = deficiency_count > 5 and self._rng.random() < 0.15
            total_deficiencies += deficiency_count
            total_detentions += 1 if detained else 0
            
            inspections.append({
                "inspection_date": self._random_date(1095, 0),
                "port": self._weighted_choice([
                    ("Rotterdam", 0.08), ("Singapore", 0.10), ("Shanghai", 0.08),
                    ("Houston", 0.07), ("Antwerp", 0.06), ("Other", 0.61)
                ]),
                "psc_regime": self._weighted_choice([
                    ("Paris MoU", 0.30), ("Tokyo MoU", 0.25),
                    ("US Coast Guard", 0.20), ("Indian Ocean MoU", 0.10), ("Other", 0.15)
                ]),
                "deficiency_count": deficiency_count,
                "deficiency_categories": self._generate_deficiencies(deficiency_count),
                "detained": detained,
                "detention_days": self._rng.randint(1, 10) if detained else 0,
            })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "inspection_summary": {
                "total_inspections_3yr": num_inspections,
                "total_deficiencies_3yr": total_deficiencies,
                "total_detentions_3yr": total_detentions,
                "deficiency_ratio": round(total_deficiencies / num_inspections, 2) if num_inspections > 0 else 0,
                "detention_rate": round(total_detentions / num_inspections, 3) if num_inspections > 0 else 0,
            },
            "inspections": sorted(inspections, key=lambda x: x["inspection_date"], reverse=True),
            "banned": total_detentions >= 3 and self._rng.random() < 0.10,
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="database",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "inspections": num_inspections,
                "detentions": total_detentions,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )
    
    def _generate_deficiencies(self, count: int) -> List[str]:
        categories = [
            "Fire Safety", "Life-Saving Appliances", "Navigation",
            "Radio Communications", "Cargo Operations", "MARPOL Annex I",
            "MARPOL Annex II", "ISM", "ISPS", "MLC", "Structural", "Propulsion"
        ]
        return self._rng.sample(categories, min(count, len(categories)))


@register_extractor
class AISTrackingExtractor(DataExtractor):
    """
    AIS Tracking Data - Position history, port calls, dark activity, STS events.
    
    Signals: ais_compliance, dark_activity, route_risk, operational_efficiency
    
    Alternative Sources:
    - MarineTraffic: vessels/ais_quality, vessels/dark_events
    - Spire: vessels/transmission
    - Windward: risk/dark_activity
    - ExactEarth: coverage/analysis
    """
    source_name = "ais_tracking"
    coverage = "marine"
    signals = ["ais_compliance", "dark_activity", "route_risk", "operational_efficiency", "psc_region_exposure"]
    ttl_config = TTLConfig.dynamic("AIS data updated daily for pattern analysis")
    
    alternative_sources = [
        DataSource("api", "marinetraffic", "vessels/ais_quality", priority=1),
        DataSource("api", "spire", "vessels/transmission", priority=2),
        DataSource("api", "windward", "risk/dark_activity", priority=3),
        DataSource("api", "exactearth", "coverage/analysis", priority=4),
        DataSource("api", "pole_star", "ais_gaps/analysis", priority=5),
    ]

    def extract(self) -> ExtractionResult:
        num_port_calls = self._rng.randint(10, 40)
        countries = ["China", "Singapore", "USA", "Netherlands", "UAE", "South Korea", 
                    "Japan", "Germany", "Belgium", "UK", "Brazil", "India"]
        
        port_calls = []
        for _ in range(num_port_calls):
            port_calls.append({
                "port": f"Port_{self._random_id('', 4)}",
                "country": self._weighted_choice([(c, 1/len(countries)) for c in countries]),
                "arrival_date": self._random_date(365, 0),
                "departure_date": self._random_date(365, 0),
                "days_in_port": self._rng.randint(1, 7),
            })
        
        # AIS Gap Analysis
        ais_gaps = []
        num_gaps = self._weighted_choice([(0, 0.70), (1, 0.15), (2, 0.10), (self._rng.randint(3, 5), 0.05)])
        for _ in range(num_gaps):
            ais_gaps.append({
                "start_date": self._random_date(365, 30),
                "duration_hours": self._rng.randint(6, 168),
                "location_type": self._weighted_choice([("Coastal", 0.50), ("Open Ocean", 0.35), ("Anchorage", 0.15)]),
                "last_known_position": {"lat": round(self._rng.uniform(-60, 60), 4), "lon": round(self._rng.uniform(-180, 180), 4)},
                "risk_level": self._weighted_choice([("Low", 0.60), ("Medium", 0.25), ("High", 0.12), ("Critical", 0.03)]),
            })
        
        # STS (Ship-to-Ship) Transfer Events
        sts_events = []
        num_sts = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.05)])
        for _ in range(num_sts):
            sts_events.append({
                "event_date": self._random_date(365, 0),
                "location": {"lat": round(self._rng.uniform(-60, 60), 4), "lon": round(self._rng.uniform(-180, 180), 4)},
                "location_risk": self._weighted_choice([("Low", 0.70), ("Medium", 0.20), ("High", 0.10)]),
                "counterparty_known": self._rng.random() > 0.3,
            })
        
        # Sanctions exposure
        high_risk_countries = ["Iran", "North Korea", "Syria", "Venezuela", "Russia"]
        sanctioned_exposure = self._rng.random() < 0.03
        high_risk_transits = self._rng.randint(0, 5)
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "port_calls": {
                "total_12mo": num_port_calls,
                "unique_countries": len(set(p["country"] for p in port_calls)),
                "calls": port_calls[:20],
            },
            "ais_gaps": {
                "total_gaps_12mo": num_gaps,
                "high_risk_gaps": sum(1 for g in ais_gaps if g["risk_level"] in ("High", "Critical")),
                "total_dark_hours": sum(g["duration_hours"] for g in ais_gaps),
                "gaps": ais_gaps,
            },
            "sts_events": {
                "total_12mo": num_sts,
                "high_risk_events": sum(1 for s in sts_events if s["location_risk"] == "High"),
                "events": sts_events,
            },
            "sanctions_exposure": {
                "sanctioned_area_visit": sanctioned_exposure,
                "high_risk_area_transits": high_risk_transits,
                "high_risk_countries_visited": self._rng.sample(high_risk_countries, min(high_risk_transits, len(high_risk_countries))) if high_risk_transits > 0 else [],
            },
            "operational_patterns": {
                "avg_speed_kts": round(self._rng.uniform(10, 18), 1),
                "utilization_pct": round(self._rng.uniform(60, 95), 1),
                "weather_routing_detected": self._rng.random() > 0.4,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "gaps": num_gaps,
                "sts": num_sts,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class SanctionsScreeningExtractor(DataExtractor):
    """
    Sanctions Screening - OFAC, EU, UN sanctions list checking.
    
    Signals: sanctions_status, ownership_transparency, jurisdiction_risk, historical_sanctions
    
    Alternative Sources:
    - OFAC: sdn/search
    - EU Sanctions: search
    - UN Sanctions: search
    - Windward: sanctions/check
    - Refinitiv: world_check
    """
    source_name = "sanctions_screening"
    coverage = "marine"
    signals = ["sanctions_status", "ownership_transparency", "jurisdiction_risk", "historical_sanctions"]
    ttl_config = TTLConfig.real_time("Sanctions data requires hourly refresh")
    
    alternative_sources = [
        DataSource("api", "ofac", "sdn/search", priority=1),
        DataSource("api", "eu_sanctions", "search", priority=1),
        DataSource("api", "un_sanctions", "search", priority=1),
        DataSource("api", "windward", "sanctions/check", priority=2),
        DataSource("api", "refinitiv", "world_check", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        # Sanctions screening results
        is_sanctioned = self._rng.random() < 0.02
        has_historical = self._rng.random() < 0.05
        
        hits = []
        if is_sanctioned or has_historical:
            num_hits = self._rng.randint(1, 3)
            for _ in range(num_hits):
                hits.append({
                    "list_name": self._weighted_choice([
                        ("OFAC SDN", 0.40), ("EU Consolidated", 0.30),
                        ("UN Security Council", 0.20), ("Other", 0.10)
                    ]),
                    "match_type": self._weighted_choice([("Exact", 0.30), ("Fuzzy", 0.50), ("Associated", 0.20)]),
                    "match_score": round(self._rng.uniform(0.75, 0.99), 2),
                    "status": "Active" if is_sanctioned else "Delisted",
                    "listed_date": self._random_date(2000, 365),
                    "reason": self._weighted_choice([
                        ("WMD Proliferation", 0.15), ("Terrorism", 0.20),
                        ("Narcotics", 0.15), ("Human Rights", 0.20),
                        ("Regional Sanctions", 0.30)
                    ]),
                })
        
        # Ownership transparency
        ownership_layers = self._weighted_choice([(1, 0.30), (2, 0.35), (3, 0.20), (4, 0.10), (5, 0.05)])
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "screening_result": {
                "status": "HIT" if is_sanctioned else ("CLEARED_HISTORICAL" if has_historical else "CLEAR"),
                "total_hits": len(hits),
                "active_hits": sum(1 for h in hits if h["status"] == "Active"),
                "hits": hits,
                "screened_lists": ["OFAC SDN", "EU Consolidated", "UN Security Council", "OFAC Non-SDN"],
                "screening_date": datetime.now().isoformat(),
            },
            "ownership_flags": {
                "high_risk_jurisdiction": self._rng.random() < 0.10,
                "complex_structure": ownership_layers >= 4,
                "ownership_layers": ownership_layers,
                "pep_connection": self._rng.random() < 0.05,
                "beneficial_owner_identified": ownership_layers <= 2,
            },
            "jurisdiction_analysis": {
                "registration_country": self._weighted_choice([
                    ("Panama", 0.15), ("Liberia", 0.12), ("Marshall Islands", 0.12),
                    ("British Virgin Islands", 0.08), ("Cyprus", 0.06), ("Other", 0.47)
                ]),
                "jurisdiction_risk_level": self._weighted_choice([("Low", 0.60), ("Medium", 0.25), ("High", 0.12), ("Very High", 0.03)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "is_sanctioned": is_sanctioned,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ClassificationSocietyExtractor(DataExtractor):
    """
    Classification Society Data - Class status, survey compliance, notations.
    
    Signals: class_status, classification_society, vessel_quality, survey_compliance
    
    Alternative Sources:
    - DNV: vessels/search
    - Lloyd's Register: vessels/search
    - Bureau Veritas: vessels/search
    - ABS: vessels/search
    - ClassNK: vessels/search
    - IACS: members/search
    """
    source_name = "classification_society"
    coverage = "marine"
    signals = ["class_status", "classification_society", "vessel_quality", "survey_compliance"]
    ttl_config = TTLConfig.dynamic("Class status updated daily")
    
    alternative_sources = [
        DataSource("api", "dnv", "vessels/search", priority=1),
        DataSource("api", "lloyd_register", "vessels/search", priority=1),
        DataSource("api", "bureau_veritas", "vessels/search", priority=2),
        DataSource("api", "abs", "vessels/search", priority=2),
        DataSource("api", "class_nk", "vessels/search", priority=3),
        DataSource("api", "iacs", "members/search", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        society = self._weighted_choice([
            ("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15),
            ("ABS", 0.15), ("ClassNK", 0.12), ("RINA", 0.05),
            ("Korean Register", 0.05), ("CCS", 0.04), ("Indian Register", 0.02)
        ])
        
        is_iacs = society in ["DNV", "Lloyd's Register", "Bureau Veritas", "ABS", "ClassNK", "RINA", "Korean Register", "CCS", "Indian Register"]
        
        class_status = self._weighted_choice([
            ("In Class", 0.92), ("Suspended", 0.04), ("Withdrawn", 0.03), ("Expired", 0.01)
        ])
        
        conditions = self._rng.randint(0, 5) if class_status == "In Class" else 0
        overdue = self._rng.randint(0, min(conditions, 2)) if conditions > 0 else 0
        
        surveys = []
        survey_types = ["Annual", "Intermediate", "Special", "Bottom", "Docking", "Class Renewal"]
        for stype in survey_types:
            if self._rng.random() > 0.3:
                surveys.append({
                    "survey_type": stype,
                    "due_date": self._random_date(-180, 365),
                    "completed_date": self._random_date(365, 0) if self._rng.random() > 0.15 else None,
                    "status": self._weighted_choice([("Completed", 0.85), ("Due", 0.10), ("Overdue", 0.05)]),
                })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "classification": {
                "society_name": society,
                "society_code": society[:3].upper(),
                "is_iacs_member": is_iacs,
                "class_status": class_status,
                "class_notation": f"+{self._rng.randint(1, 100)}A1" if class_status == "In Class" else None,
                "machinery_notation": self._weighted_choice([("+MC", 0.80), ("+UMS", 0.15), (None, 0.05)]),
            },
            "conditions_of_class": {
                "total": conditions,
                "outstanding": conditions - overdue,
                "overdue": overdue,
                "categories": self._rng.sample(["Hull", "Machinery", "Navigation", "Safety", "Environmental"], min(conditions, 5)) if conditions > 0 else [],
            },
            "survey_history": {
                "surveys": surveys,
                "compliance_rate": round(1 - (overdue / max(len(surveys), 1)), 2),
                "last_survey_date": surveys[0]["completed_date"] if surveys and surveys[0]["completed_date"] else None,
            },
            "additional_notations": {
                "ice_class": self._weighted_choice([(None, 0.85), ("1A", 0.08), ("1A Super", 0.04), ("1B", 0.03)]),
                "dynamic_positioning": self._weighted_choice([(None, 0.90), ("DP1", 0.05), ("DP2", 0.04), ("DP3", 0.01)]),
                "green_passport": self._rng.random() > 0.60,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "society": society,
                "is_iacs": is_iacs,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ISMComplianceExtractor(DataExtractor):
    """
    ISM Compliance Data - DOC status, SMS audits, safety management.
    
    Signals: ism_compliance, safety_management
    
    Alternative Sources:
    - IMO GISIS: ism/search
    - Flag State Databases
    """
    source_name = "ism_compliance"
    coverage = "marine"
    signals = ["ism_compliance", "safety_management"]
    ttl_config = TTLConfig.semi_static("ISM audits occur periodically")
    
    alternative_sources = [
        DataSource("api", "imo_gisis", "ism/search", priority=1),
        DataSource("registry", "flag_state_databases", "ism/status", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        doc_status = self._weighted_choice([
            ("Valid", 0.94), ("Expired", 0.03), ("Suspended", 0.02), ("Withdrawn", 0.01)
        ])
        
        # Audit history
        num_audits = self._rng.randint(2, 6)
        audits = []
        total_findings = 0
        major_nc = 0
        
        for i in range(num_audits):
            audit_type = "Initial" if i == 0 else self._weighted_choice([
                ("Annual", 0.50), ("Intermediate", 0.30), ("Additional", 0.20)
            ])
            findings = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.15)])
            major = self._rng.randint(0, min(2, findings)) if findings > 2 else 0
            
            total_findings += findings
            major_nc += major
            
            audits.append({
                "audit_type": audit_type,
                "audit_date": self._random_date(1095, 30 * i),
                "findings": findings,
                "major_nonconformities": major,
                "observations": self._rng.randint(0, 5),
                "result": "Satisfactory" if major == 0 else "Conditional",
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "doc_status": {
                "status": doc_status,
                "issue_date": self._random_date(1825, 365),
                "expiry_date": self._random_date(-365, -30) if doc_status == "Expired" else self._random_date(-30, 730),
                "issuing_authority": self._weighted_choice([
                    ("Panama Maritime Authority", 0.20), ("Liberia Maritime Authority", 0.15),
                    ("Marshall Islands Maritime", 0.15), ("Other", 0.50)
                ]),
            },
            "audit_history": {
                "total_audits_3yr": num_audits,
                "total_findings": total_findings,
                "major_nonconformities": major_nc,
                "audits": sorted(audits, key=lambda x: x["audit_date"], reverse=True),
            },
            "sms_status": {
                "documented": True,
                "last_review_date": self._random_date(365, 0),
                "drills_conducted_12mo": self._rng.randint(6, 24),
                "near_miss_reports_12mo": self._rng.randint(0, 15),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "doc_status": doc_status,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FlagStatePerformanceExtractor(DataExtractor):
    """
    Flag State Performance - Paris/Tokyo MoU white/grey/black lists.
    
    Signals: flag_state, flag_state_quality
    
    Alternative Sources:
    - Paris MoU: performance/flags
    - Tokyo MoU: performance/flags
    - US Coast Guard: qualship21
    """
    source_name = "flag_state_performance"
    coverage = "marine"
    signals = ["flag_state", "flag_state_quality"]
    ttl_config = TTLConfig.semi_static("Flag state lists updated periodically")
    
    alternative_sources = [
        DataSource("api", "paris_mou", "performance/flags", priority=1),
        DataSource("api", "tokyo_mou", "performance/flags", priority=2),
        DataSource("api", "uscg", "qualship21", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        flag_state = self.kwargs.get("flag_state", self._weighted_choice([
            ("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14),
            ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08),
            ("Bahamas", 0.07), ("Cyprus", 0.05), ("Other", 0.13)
        ]))
        
        # Determine list color based on flag state
        white_list_flags = ["Singapore", "Hong Kong", "Denmark", "Norway", "Japan", "UK", "Germany", "Netherlands"]
        black_list_flags = ["Comoros", "Palau", "Togo", "Moldova", "Sierra Leone"]
        
        if flag_state in white_list_flags:
            list_color = "WHITE"
            detention_rate = round(self._rng.uniform(0.5, 2.5), 2)
        elif flag_state in black_list_flags:
            list_color = "BLACK"
            detention_rate = round(self._rng.uniform(8.0, 20.0), 2)
        else:
            list_color = self._weighted_choice([("WHITE", 0.50), ("GREY", 0.40), ("BLACK", 0.10)])
            detention_rate = round(self._rng.uniform(1.0, 8.0), 2)
        
        raw_data = {
            "flag_state": flag_state,
            "flag_code": flag_state[:3].upper(),
            "paris_mou_status": {
                "list_color": list_color,
                "detention_rate_pct": detention_rate,
                "deficiency_ratio": round(detention_rate * 1.5, 2),
                "inspection_count_3yr": self._rng.randint(100, 5000),
            },
            "tokyo_mou_status": {
                "list_color": list_color,
                "detention_rate_pct": detention_rate * self._rng.uniform(0.8, 1.2),
            },
            "qualship_21": {
                "eligible": list_color == "WHITE" and self._rng.random() > 0.3,
            },
            "imo_audit_status": {
                "audited": True,
                "last_audit_date": self._random_date(1825, 365),
                "significant_findings": self._rng.randint(0, 5),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "flag_state": flag_state,
                "list_color": list_color,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PIClubExtractor(DataExtractor):
    """
    P&I Club Data - Club membership, claims history, coverage.
    
    Signals: pi_club, insurance_history
    
    Alternative Sources:
    - International Group: members/search
    - Individual P&I Club APIs
    """
    source_name = "pi_club"
    coverage = "marine"
    signals = ["pi_club", "insurance_history"]
    ttl_config = TTLConfig.semi_static("P&I membership updated weekly")
    
    alternative_sources = [
        DataSource("api", "ig_clubs", "members/search", priority=1),
        DataSource("scrape", "pi_club_websites", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        ig_clubs = [
            "Gard", "Britannia", "North P&I", "Standard Club", "UK P&I Club",
            "West of England", "Skuld", "American Club", "Japan P&I", "London P&I Club",
            "Swedish Club", "Steamship Mutual", "Shipowners' Club"
        ]
        
        is_ig_member = self._rng.random() > 0.15
        club_name = self._rng.choice(ig_clubs) if is_ig_member else f"Fixed Premium Insurer {self._random_id()}"
        club_type = "International Group" if is_ig_member else "Fixed Premium"
        
        # Claims history
        num_claims = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 10), 0.15)])
        total_incurred = 0
        claims = []
        
        for _ in range(num_claims):
            claim_amount = self._weighted_choice([
                (self._rng.randint(10000, 100000), 0.60),
                (self._rng.randint(100000, 500000), 0.25),
                (self._rng.randint(500000, 2000000), 0.10),
                (self._rng.randint(2000000, 10000000), 0.05),
            ])
            total_incurred += claim_amount
            claims.append({
                "claim_type": self._weighted_choice([
                    ("Cargo", 0.30), ("Personal Injury", 0.25), ("Collision", 0.15),
                    ("Pollution", 0.10), ("Wreck Removal", 0.08), ("Other", 0.12)
                ]),
                "claim_date": self._random_date(1825, 0),
                "incurred_amount_usd": claim_amount,
                "status": self._weighted_choice([("Open", 0.30), ("Closed", 0.70)]),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "membership": {
                "club_name": club_name,
                "club_type": club_type,
                "is_ig_member": is_ig_member,
                "member_since": self._random_date(7300, 365),
                "tonnage_entered": self._rng.randint(100000, 5000000),
            },
            "claims_history": {
                "total_claims_5yr": num_claims,
                "total_incurred_usd": total_incurred,
                "claims": sorted(claims, key=lambda x: x["claim_date"], reverse=True)[:10],
                "loss_ratio": round(total_incurred / max(self._rng.randint(500000, 5000000), 1), 3),
            },
            "coverage": {
                "p_and_i_limit_usd": 3_000_000_000 if is_ig_member else self._rng.randint(100_000_000, 500_000_000),
                "fdp_limit_usd": self._rng.randint(50_000_000, 500_000_000),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "is_ig_member": is_ig_member,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MarineFinancialExtractor(DataExtractor):
    """
    Marine Financial Data - Revenue, leverage, credit metrics.
    
    Signals: credit_rating, leverage, financial_stability
    
    Alternative Sources:
    - SEC Edgar (if public)
    - Bloomberg
    - D&B
    - Marine Money
    """
    source_name = "marine_financial"
    coverage = "marine"
    signals = ["credit_rating", "leverage", "financial_stability"]
    ttl_config = TTLConfig.semi_static("Financial data updated weekly")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "10-K", priority=1),
        DataSource("api", "bloomberg", "financials", priority=2),
        DataSource("api", "dnb", "company/financials", priority=3),
        DataSource("api", "marine_money", "transactions", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([
            (self._rng.randint(10, 100) * 1_000_000, 0.40),
            (self._rng.randint(100, 500) * 1_000_000, 0.35),
            (self._rng.randint(500, 2000) * 1_000_000, 0.20),
            (self._rng.randint(2000, 10000) * 1_000_000, 0.05),
        ])
        
        ebitda_margin = self._rng.uniform(0.15, 0.45)
        ebitda = revenue * ebitda_margin
        
        debt_to_ebitda = self._weighted_choice([
            (self._rng.uniform(1.0, 3.0), 0.40),
            (self._rng.uniform(3.0, 5.0), 0.35),
            (self._rng.uniform(5.0, 8.0), 0.20),
            (self._rng.uniform(8.0, 12.0), 0.05),
        ])
        
        total_debt = ebitda * debt_to_ebitda
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "financials": {
                "revenue_usd": revenue,
                "ebitda_usd": ebitda,
                "ebitda_margin_pct": round(ebitda_margin * 100, 1),
                "net_income_usd": ebitda * self._rng.uniform(0.3, 0.7),
                "total_assets_usd": revenue * self._rng.uniform(2, 5),
                "fiscal_year_end": "2024-12-31",
            },
            "leverage": {
                "total_debt_usd": total_debt,
                "cash_usd": revenue * self._rng.uniform(0.05, 0.20),
                "net_debt_usd": total_debt - (revenue * self._rng.uniform(0.05, 0.20)),
            },
            "ratios": {
                "debt_to_ebitda": round(debt_to_ebitda, 2),
                "interest_coverage": round(self._rng.uniform(1.5, 8.0), 2),
                "current_ratio": round(self._rng.uniform(0.8, 2.5), 2),
            },
            "credit_profile": {
                "is_public": self._rng.random() > 0.70,
                "has_rating": self._rng.random() > 0.50,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class VesselValuationExtractor(DataExtractor):
    """
    Vessel Valuation Data - Market values, LTV ratios.
    
    Signals: fleet_value, ltv_ratio
    
    Alternative Sources:
    - VesselsValue
    - Clarksons: valuations
    - Baltic Exchange
    """
    source_name = "vessel_valuation"
    coverage = "marine"
    signals = ["fleet_value", "ltv_ratio"]
    ttl_config = TTLConfig.semi_static("Valuations updated weekly")
    
    alternative_sources = [
        DataSource("api", "vesselsvalue", "valuations/fleet", priority=1),
        DataSource("api", "clarksons", "valuations", priority=2),
        DataSource("api", "baltic_exchange", "indices", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_vessels = self._rng.randint(1, 50)
        vessels = []
        total_value = 0
        total_debt = 0
        
        for _ in range(num_vessels):
            vessel_type = self._weighted_choice([
                ("Container Ship", 0.25), ("Oil Tanker", 0.20), ("Bulk Carrier", 0.20),
                ("Chemical Tanker", 0.15), ("LNG Carrier", 0.10), ("Other", 0.10)
            ])
            
            # Value based on vessel type and age
            base_values = {
                "Container Ship": (30, 150), "Oil Tanker": (25, 120),
                "Bulk Carrier": (15, 60), "Chemical Tanker": (20, 80),
                "LNG Carrier": (150, 300), "Other": (10, 50)
            }
            low, high = base_values.get(vessel_type, (20, 80))
            market_value = self._rng.randint(low, high) * 1_000_000
            
            debt_pct = self._rng.uniform(0.40, 0.85)
            vessel_debt = market_value * debt_pct
            
            total_value += market_value
            total_debt += vessel_debt
            
            vessels.append({
                "vessel_type": vessel_type,
                "market_value_usd": market_value,
                "debt_usd": vessel_debt,
                "ltv_ratio": round(debt_pct, 3),
                "last_valuation_date": self._random_date(90, 0),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "fleet_valuation": {
                "total_vessels": num_vessels,
                "total_fleet_value_usd": total_value,
                "average_vessel_value_usd": total_value // num_vessels,
                "valuation_date": self._random_date(30, 0),
            },
            "leverage": {
                "total_fleet_debt_usd": total_debt,
                "ltv_ratio": round(total_debt / total_value, 3) if total_value > 0 else 0,
            },
            "vessels": vessels[:20],
            "market_outlook": {
                "market_trend": self._weighted_choice([("Improving", 0.30), ("Stable", 0.45), ("Declining", 0.25)]),
                "value_change_12mo_pct": round(self._rng.uniform(-20, 30), 1),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "num_vessels": num_vessels,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class TradingPatternExtractor(DataExtractor):
    """
    Trading Pattern Analysis - Routes, regions, cargo types.
    
    Signals: trading_pattern, route_risk, geographic_exposure
    
    Alternative Sources:
    - MarineTraffic: routes/analysis
    - Spire: vessels/routes
    - ExactEarth: patterns/analysis
    """
    source_name = "trading_pattern"
    coverage = "marine"
    signals = ["trading_pattern", "route_risk", "geographic_exposure"]
    ttl_config = TTLConfig.dynamic("Trading patterns analyzed daily")
    
    alternative_sources = [
        DataSource("api", "marinetraffic", "routes/analysis", priority=1),
        DataSource("api", "spire", "vessels/routes", priority=2),
        DataSource("api", "exactearth", "patterns/analysis", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        trading_regions = ["Asia-Pacific", "Europe", "Americas", "Middle East", "Africa", "Global"]
        primary_region = self._weighted_choice([
            ("Asia-Pacific", 0.30), ("Europe", 0.20), ("Global", 0.20),
            ("Americas", 0.15), ("Middle East", 0.10), ("Africa", 0.05)
        ])
        
        route_types = ["Liner", "Tramp", "Industrial", "Mixed"]
        primary_route = self._weighted_choice([
            ("Liner", 0.25), ("Tramp", 0.40), ("Industrial", 0.20), ("Mixed", 0.15)
        ])
        
        # High risk area exposure
        high_risk_areas = ["Gulf of Aden", "Gulf of Guinea", "Strait of Malacca", "South China Sea"]
        exposed_areas = self._rng.sample(high_risk_areas, self._rng.randint(0, 3))
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "trading_pattern": {
                "primary_region": primary_region,
                "secondary_regions": self._rng.sample([r for r in trading_regions if r != primary_region], 2),
                "route_type": primary_route,
                "seasonal_pattern": self._weighted_choice([("Consistent", 0.60), ("Seasonal", 0.30), ("Opportunistic", 0.10)]),
            },
            "geographic_exposure": {
                "high_risk_areas": exposed_areas,
                "sanctioned_country_exposure": self._rng.random() < 0.05,
                "piracy_zone_transits_12mo": self._rng.randint(0, 20) if exposed_areas else 0,
            },
            "cargo_profile": {
                "primary_cargo": self._weighted_choice([
                    ("Containers", 0.25), ("Crude Oil", 0.15), ("Dry Bulk", 0.20),
                    ("Chemicals", 0.15), ("LNG", 0.10), ("General Cargo", 0.15)
                ]),
                "cargo_diversity": self._weighted_choice([("Single", 0.30), ("Diverse", 0.50), ("Specialized", 0.20)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "primary_region": primary_region,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor  
class MarineVettingExtractor(DataExtractor):
    """
    Third-Party Vetting Data - RightShip, SIRE, CDI.
    
    Signals: vetting_score, inspection_quality
    
    Alternative Sources:
    - RightShip: vessels/score
    - OCIMF SIRE: reports/search
    - CDI: vessel_inspection/search
    """
    source_name = "vetting_scores"
    coverage = "marine"
    signals = ["vetting_score", "inspection_quality"]
    ttl_config = TTLConfig.semi_static("Vetting scores updated weekly")
    
    alternative_sources = [
        DataSource("api", "rightship", "vessels/score", priority=1),
        DataSource("api", "ocimf_sire", "reports/search", priority=2),
        DataSource("api", "cdp", "vessel_inspection/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        # RightShip score (0.5 to 5.0 stars)
        rightship_score = round(self._weighted_choice([
            (self._rng.uniform(4.0, 5.0), 0.30), (self._rng.uniform(3.0, 4.0), 0.40),
            (self._rng.uniform(2.0, 3.0), 0.20), (self._rng.uniform(0.5, 2.0), 0.10)
        ]), 1)
        
        # SIRE inspection
        sire_inspected = self._rng.random() > 0.30
        sire_observations = self._rng.randint(0, 25) if sire_inspected else None
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "rightship": {
                "score": rightship_score,
                "star_rating": int(rightship_score),
                "last_update": self._random_date(90, 0),
                "ghg_rating": self._weighted_choice([("A", 0.15), ("B", 0.25), ("C", 0.35), ("D", 0.20), ("E", 0.05)]),
            },
            "sire": {
                "inspected": sire_inspected,
                "last_inspection_date": self._random_date(365, 0) if sire_inspected else None,
                "total_observations": sire_observations,
                "negative_observations": self._rng.randint(0, min(10, sire_observations or 0)) if sire_observations else None,
            },
            "cdi": {
                "inspected": self._rng.random() > 0.50,
                "last_inspection_date": self._random_date(365, 0),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "rightship_score": rightship_score,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MarineEnvironmentalExtractor(DataExtractor):
    """
    Environmental Compliance Data - CII, BWM, IMO 2020.
    
    Signals: cii_rating, bwm_compliance, imo2020_compliance, environmental_incident
    
    Alternative Sources:
    - IMO DCS: emissions/cii
    - Class Societies: vessels/cii
    - PSC databases
    """
    source_name = "marine_environmental"
    coverage = "marine"
    signals = ["cii_rating", "bwm_compliance", "imo2020_compliance", "environmental_incident"]
    ttl_config = TTLConfig.semi_static("Environmental data updated weekly")
    
    alternative_sources = [
        DataSource("api", "imo_dcs", "emissions/cii", priority=1),
        DataSource("api", "class_societies", "vessels/cii", priority=2),
        DataSource("api", "psc_databases", "deficiencies/marpol", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        cii_rating = self._weighted_choice([("A", 0.15), ("B", 0.25), ("C", 0.35), ("D", 0.20), ("E", 0.05)])
        
        bwm_compliant = self._rng.random() > 0.15
        imo2020_compliant = self._rng.random() > 0.05
        
        num_incidents = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.04), (3, 0.01)])
        incidents = []
        for _ in range(num_incidents):
            incidents.append({
                "incident_date": self._random_date(1825, 0),
                "type": self._weighted_choice([
                    ("Oil Spill", 0.40), ("Chemical Discharge", 0.20),
                    ("Garbage Violation", 0.25), ("Air Emission", 0.15)
                ]),
                "severity": self._weighted_choice([("Minor", 0.60), ("Moderate", 0.30), ("Major", 0.10)]),
                "fine_usd": self._rng.randint(0, 500000) if self._rng.random() > 0.50 else 0,
            })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "cii": {
                "rating": cii_rating,
                "attained_cii": round(self._rng.uniform(3, 15), 2),
                "required_cii": round(self._rng.uniform(5, 12), 2),
                "year": 2024,
                "trajectory": self._weighted_choice([("Improving", 0.40), ("Stable", 0.40), ("Declining", 0.20)]),
            },
            "bwm_compliance": {
                "compliant": bwm_compliant,
                "system_type": self._weighted_choice([("UV", 0.40), ("Electrochlorination", 0.35), ("Filtration", 0.25)]) if bwm_compliant else None,
                "compliance_date": self._random_date(1825, 365) if bwm_compliant else None,
            },
            "imo2020_compliance": {
                "compliant": imo2020_compliant,
                "method": self._weighted_choice([("LSFO", 0.70), ("Scrubber", 0.20), ("LNG", 0.10)]) if imo2020_compliant else "Non-compliant",
            },
            "environmental_incidents": {
                "total_5yr": num_incidents,
                "total_fines_usd": sum(i["fine_usd"] for i in incidents),
                "incidents": incidents,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "cii_rating": cii_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class IndustryAssociationExtractor(DataExtractor):
    """
    Industry Association Membership - BIMCO, Intertanko, Intercargo.
    
    Signals: industry_association, charterer_quality
    
    Alternative Sources:
    - BIMCO: members
    - Intertanko: members
    - Intercargo: members
    """
    source_name = "industry_associations"
    coverage = "marine"
    signals = ["industry_association", "charterer_quality"]
    ttl_config = TTLConfig.static("Association membership changes rarely")
    
    alternative_sources = [
        DataSource("api", "bimco", "members", priority=1),
        DataSource("api", "intertanko", "members", priority=2),
        DataSource("api", "intercargo", "members", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        associations = ["BIMCO", "Intertanko", "Intercargo", "IMCA", "ICS"]
        member_of = [a for a in associations if self._rng.random() > 0.60]
        
        # Charterer relationships
        oil_majors = ["Shell", "BP", "ExxonMobil", "Chevron", "TotalEnergies", "Equinor"]
        commodity_traders = ["Trafigura", "Vitol", "Glencore", "Cargill", "Louis Dreyfus"]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "memberships": {
                "associations": member_of,
                "total_memberships": len(member_of),
                "years_member": {a: self._rng.randint(1, 30) for a in member_of},
            },
            "charterer_relationships": {
                "oil_major_approved": self._rng.random() > 0.40,
                "approved_by": self._rng.sample(oil_majors, self._rng.randint(0, 3)),
                "commodity_trader_contracts": self._rng.sample(commodity_traders, self._rng.randint(0, 2)),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "memberships": len(member_of),
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CasualtyHistoryExtractor(DataExtractor):
    """
    Casualty and Incident History - Total losses, major incidents.
    
    Signals: casualty_history, total_loss
    
    Alternative Sources:
    - IHS Markit: casualties/search
    - Lloyd's List: casualties/search
    - IMO GISIS: casualties/search
    """
    source_name = "casualty_history"
    coverage = "marine"
    signals = ["casualty_history", "total_loss"]
    ttl_config = TTLConfig.dynamic("Casualty data updated daily")
    
    alternative_sources = [
        DataSource("api", "ihs_markit", "casualties/search", priority=1),
        DataSource("api", "lloyd_list", "casualties/search", priority=2),
        DataSource("api", "imo_gisis", "casualties/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_casualties = self._weighted_choice([(0, 0.75), (1, 0.15), (2, 0.07), (3, 0.03)])
        casualties = []
        
        casualty_types = [
            "Collision", "Grounding", "Fire/Explosion", "Machinery Failure",
            "Hull Failure", "Contact", "Flooding", "Foundering"
        ]
        
        for _ in range(num_casualties):
            severity = self._weighted_choice([("Minor", 0.50), ("Serious", 0.35), ("Very Serious", 0.12), ("Total Loss", 0.03)])
            casualties.append({
                "date": self._random_date(3650, 0),
                "type": self._rng.choice(casualty_types),
                "severity": severity,
                "location": f"{self._rng.uniform(-60, 60):.2f}, {self._rng.uniform(-180, 180):.2f}",
                "fatalities": self._rng.randint(0, 5) if severity in ("Very Serious", "Total Loss") else 0,
                "flag_state_investigation": severity != "Minor",
            })
        
        total_losses = sum(1 for c in casualties if c["severity"] == "Total Loss")
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "casualty_summary": {
                "total_casualties_10yr": num_casualties,
                "total_losses": total_losses,
                "fatalities": sum(c["fatalities"] for c in casualties),
                "by_severity": {s: sum(1 for c in casualties if c["severity"] == s) 
                              for s in ["Minor", "Serious", "Very Serious", "Total Loss"]},
            },
            "casualties": sorted(casualties, key=lambda x: x["date"], reverse=True),
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "casualties": num_casualties,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class AircraftFleetExtractor(DataExtractor):
    """
    Aircraft Fleet Data - Fleet composition, age, ownership.
    
    Signals: fleet_size, fleet_age, fleet_homogeneity, aircraft_generation, order_backlog
    
    Alternative Sources:
    - Cirium: fleets/aircraft
    - ch-aviation: fleets/list
    - Planespotters: operators/fleet
    - FAA Registry: aircraft/by_owner
    """
    source_name = "aircraft_fleet"
    coverage = "aerospace"
    signals = ["fleet_size", "fleet_age", "fleet_homogeneity", "aircraft_generation", "order_backlog"]
    ttl_config = TTLConfig.semi_static("Fleet composition changes weekly")
    
    alternative_sources = [
        DataSource("api", "cirium", "fleets/aircraft", priority=1),
        DataSource("api", "ch_aviation", "fleets/list", priority=2),
        DataSource("api", "planespotters", "operators/fleet", priority=3),
        DataSource("registry", "faa_registry", "aircraft/by_owner", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        fleet_size = self._weighted_choice([
            (self._rng.randint(1, 10), 0.30), (self._rng.randint(11, 50), 0.35),
            (self._rng.randint(51, 200), 0.25), (self._rng.randint(201, 800), 0.10)
        ])
        
        aircraft_types = ["B737", "A320", "B777", "A350", "B787", "A330", "E190", "CRJ", "ATR"]
        primary_type = self._rng.choice(aircraft_types[:4])
        
        aircraft = []
        type_counts = {}
        total_age = 0
        
        for i in range(fleet_size):
            if i < fleet_size * 0.6:
                ac_type = primary_type
            else:
                ac_type = self._rng.choice(aircraft_types)
            
            type_counts[ac_type] = type_counts.get(ac_type, 0) + 1
            age = self._rng.randint(0, 25)
            total_age += age
            
            aircraft.append({
                "registration": self._random_id("N", 5) if self._rng.random() > 0.50 else self._random_id("G-", 4),
                "type": ac_type,
                "age_years": age,
                "build_year": 2024 - age,
                "ownership": self._weighted_choice([("Owned", 0.35), ("Finance Lease", 0.30), ("Operating Lease", 0.35)]),
                "lessor": self._rng.choice(["AerCap", "SMBC", "Avolon", "BOC Aviation", "GECAS", None]) if self._rng.random() > 0.35 else None,
            })
        
        avg_age = total_age / fleet_size if fleet_size > 0 else 0
        homogeneity = max(type_counts.values()) / fleet_size if fleet_size > 0 else 0
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "fleet_summary": {
                "total_aircraft": fleet_size,
                "average_age_years": round(avg_age, 1),
                "newest_aircraft_age": min(a["age_years"] for a in aircraft) if aircraft else 0,
                "oldest_aircraft_age": max(a["age_years"] for a in aircraft) if aircraft else 0,
                "type_count": len(type_counts),
                "primary_type": primary_type,
                "homogeneity_score": round(homogeneity, 2),
            },
            "type_distribution": type_counts,
            "ownership_breakdown": {
                "owned": sum(1 for a in aircraft if a["ownership"] == "Owned"),
                "finance_lease": sum(1 for a in aircraft if a["ownership"] == "Finance Lease"),
                "operating_lease": sum(1 for a in aircraft if a["ownership"] == "Operating Lease"),
            },
            "order_backlog": {
                "total_orders": self._rng.randint(0, 100),
                "deliveries_next_12mo": self._rng.randint(0, 20),
                "types_ordered": self._rng.sample(["B737 MAX", "A320neo", "A350", "B787"], self._rng.randint(0, 3)),
            },
            "aircraft": aircraft[:50],
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "fleet_size": fleet_size,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class OperationalPerformanceExtractor(DataExtractor):
    """
    Operational Performance - OTP, dispatch reliability, completion factor.
    
    Signals: otp_score, dispatch_reliability, operational_complexity, growth_rate
    
    Alternative Sources:
    - OAG: performance/otp
    - Cirium: performance/punctuality
    """
    source_name = "operational_performance"
    coverage = "aerospace"
    signals = ["otp_score", "dispatch_reliability", "operational_complexity", "growth_rate"]
    ttl_config = TTLConfig.dynamic("Performance metrics updated daily")
    
    alternative_sources = [
        DataSource("api", "oag", "performance/otp", priority=1),
        DataSource("api", "cirium", "performance/punctuality", priority=2),
        DataSource("api", "cirium", "performance/dispatch", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        otp = round(self._rng.uniform(65, 92), 1)
        dispatch = round(self._rng.uniform(97, 99.9), 2)
        completion = round(self._rng.uniform(96, 99.5), 2)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "performance_metrics": {
                "on_time_performance_pct": otp,
                "dispatch_reliability_pct": dispatch,
                "completion_factor_pct": completion,
                "average_delay_minutes": self._rng.randint(5, 45),
                "cancellation_rate_pct": round(100 - completion, 2),
            },
            "benchmark_comparison": {
                "otp_vs_industry": round(otp - 78, 1),
                "dispatch_vs_industry": round(dispatch - 98.5, 2),
                "ranking_percentile": self._rng.randint(10, 95),
            },
            "operational_complexity": {
                "fleet_types": self._rng.randint(1, 8),
                "destinations": self._rng.randint(20, 300),
                "daily_departures": self._rng.randint(50, 2000),
                "hub_count": self._rng.randint(1, 10),
                "complexity_score": self._weighted_choice([("Low", 0.20), ("Medium", 0.50), ("High", 0.30)]),
            },
            "growth_metrics": {
                "asm_growth_yoy_pct": round(self._rng.uniform(-10, 25), 1),
                "passenger_growth_yoy_pct": round(self._rng.uniform(-5, 20), 1),
                "route_additions_12mo": self._rng.randint(0, 30),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "otp": otp,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MROProviderExtractor(DataExtractor):
    """
    MRO Provider Data - Maintenance quality, approvals, capabilities.
    
    Signals: mro_quality, maintenance_indicators
    
    Alternative Sources:
    - FAA: repair_stations/145
    - EASA: part_145_approvals
    """
    source_name = "mro_provider"
    coverage = "aerospace"
    signals = ["mro_quality", "maintenance_indicators"]
    ttl_config = TTLConfig.semi_static("MRO relationships change infrequently")
    
    alternative_sources = [
        DataSource("registry", "faa", "repair_stations/145", priority=1),
        DataSource("registry", "easa", "part_145_approvals", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        mro_tier = self._weighted_choice([
            ("OEM Affiliated", 0.20), ("Major Independent", 0.30),
            ("Regional", 0.30), ("In-House", 0.20)
        ])
        
        capabilities = ["Airframe", "Engine", "Component", "Line Maintenance", "Base Maintenance"]
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "primary_mro": {
                "provider_name": self._random_company_name("Aviation Services"),
                "tier": mro_tier,
                "faa_145_certified": True,
                "easa_145_certified": self._rng.random() > 0.20,
                "capabilities": self._rng.sample(capabilities, self._rng.randint(2, 5)),
            },
            "maintenance_quality": {
                "audit_findings_12mo": self._rng.randint(0, 15),
                "repeat_findings": self._rng.randint(0, 5),
                "ad_compliance_rate_pct": round(self._rng.uniform(98, 100), 1),
                "unscheduled_maintenance_rate": round(self._rng.uniform(0.5, 5), 2),
            },
            "mro_relationship": {
                "years_with_provider": self._rng.randint(1, 20),
                "contract_type": self._weighted_choice([("Flight Hour", 0.40), ("Fixed Price", 0.35), ("Time & Materials", 0.25)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "mro_tier": mro_tier,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CrewTrainingExtractor(DataExtractor):
    """
    Crew Training Data - Training programs, experience levels.
    
    Signals: crew_experience, training_indicators
    
    Alternative Sources:
    - CAE: training/customers
    - FlightSafety: clients
    - LinkedIn: people/search
    """
    source_name = "crew_training"
    coverage = "aerospace"
    signals = ["crew_experience", "training_indicators"]
    ttl_config = TTLConfig.semi_static("Training data updated weekly")
    
    alternative_sources = [
        DataSource("api", "cae", "training/customers", priority=1),
        DataSource("api", "flightsafety", "clients", priority=2),
        DataSource("api", "linkedin", "people/search", {"title": ["Captain", "First Officer"]}, priority=3),
    ]

    def extract(self) -> ExtractionResult:
        avg_captain_hours = self._rng.randint(5000, 20000)
        avg_fo_hours = self._rng.randint(2000, 8000)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "crew_experience": {
                "average_captain_hours": avg_captain_hours,
                "average_fo_hours": avg_fo_hours,
                "min_hiring_hours": self._rng.choice([500, 1000, 1500, 2500]),
                "captain_upgrade_hours": self._rng.choice([3000, 4000, 5000]),
            },
            "training_program": {
                "simulator_provider": self._weighted_choice([("CAE", 0.35), ("FlightSafety", 0.30), ("In-House", 0.25), ("Other", 0.10)]),
                "recurrent_frequency_months": 6,
                "advanced_training": {
                    "upset_recovery": self._rng.random() > 0.20,
                    "aqa_program": self._rng.random() > 0.30,
                    "losa_program": self._rng.random() > 0.40,
                },
                "training_hours_per_pilot_annual": self._rng.randint(40, 120),
            },
            "crew_metrics": {
                "total_pilots": self._rng.randint(50, 5000),
                "turnover_rate_pct": round(self._rng.uniform(3, 20), 1),
                "check_airman_ratio": round(self._rng.uniform(0.05, 0.15), 3),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "avg_captain_hours": avg_captain_hours,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class AviationFinancialExtractor(DataExtractor):
    """
    Aviation Financial Data - Revenue, EBITDAR, leverage.
    
    Signals: credit_rating, public_financials, market_position
    
    Alternative Sources:
    - SEC Edgar: 10-K, 10-Q, 20-F
    - Bloomberg: financials
    """
    source_name = "aviation_financial"
    coverage = "aerospace"
    signals = ["credit_rating", "public_financials", "market_position", "government_support"]
    ttl_config = TTLConfig.semi_static("Financial data updated weekly")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "10-K", priority=1),
        DataSource("api", "bloomberg", "financials", priority=2),
        DataSource("api", "sp_global", "ratings", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([
            (self._rng.randint(100, 500) * 1_000_000, 0.30),
            (self._rng.randint(500, 2000) * 1_000_000, 0.35),
            (self._rng.randint(2000, 10000) * 1_000_000, 0.25),
            (self._rng.randint(10000, 50000) * 1_000_000, 0.10),
        ])
        
        ebitdar_margin = self._rng.uniform(0.10, 0.30)
        ebitdar = revenue * ebitdar_margin
        
        debt_to_ebitdar = self._weighted_choice([
            (self._rng.uniform(1.0, 3.0), 0.30),
            (self._rng.uniform(3.0, 5.0), 0.40),
            (self._rng.uniform(5.0, 8.0), 0.25),
            (self._rng.uniform(8.0, 15.0), 0.05),
        ])
        
        ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
        rating_idx = self._weighted_choice([
            (2, 0.10), (3, 0.25), (4, 0.35), (5, 0.20), (6, 0.10)
        ])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "financials": {
                "revenue_usd": revenue,
                "ebitdar_usd": ebitdar,
                "ebitdar_margin_pct": round(ebitdar_margin * 100, 1),
                "net_income_usd": ebitdar * self._rng.uniform(-0.2, 0.5),
                "total_assets_usd": revenue * self._rng.uniform(1.5, 4),
                "is_public": self._rng.random() > 0.40,
            },
            "leverage": {
                "total_debt_usd": ebitdar * debt_to_ebitdar,
                "debt_to_ebitdar": round(debt_to_ebitdar, 2),
                "lease_adjusted_debt_usd": ebitdar * debt_to_ebitdar * 1.3,
                "cash_usd": revenue * self._rng.uniform(0.05, 0.25),
            },
            "credit_rating": {
                "has_rating": self._rng.random() > 0.30,
                "rating": ratings[rating_idx] if self._rng.random() > 0.30 else None,
                "outlook": self._weighted_choice([("Stable", 0.50), ("Positive", 0.20), ("Negative", 0.30)]),
            },
            "market_position": {
                "domestic_market_share_pct": round(self._rng.uniform(1, 40), 1),
                "primary_hub_slot_share_pct": round(self._rng.uniform(5, 60), 1),
            },
            "government_support": {
                "state_owned_pct": self._rng.randint(0, 100) if self._rng.random() < 0.20 else 0,
                "received_bailout": self._rng.random() < 0.15,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "revenue": revenue,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class RouteRiskExtractor(DataExtractor):
    """
    Route Risk Analysis - Conflict zones, challenging airports, weather exposure.
    
    Signals: conflict_zone_exposure, challenging_airports, high_risk_destinations, weather_exposure
    
    Alternative Sources:
    - OAG: schedules/routes
    - Osprey Flight Solutions: risk_zones
    - Eurocontrol: notams/conflict
    """
    source_name = "route_risk"
    coverage = "aerospace"
    signals = ["conflict_zone_exposure", "challenging_airports", "high_risk_destinations", "weather_exposure"]
    ttl_config = TTLConfig.real_time("Conflict zone data requires hourly updates")
    
    alternative_sources = [
        DataSource("api", "oag", "schedules/routes", priority=1),
        DataSource("api", "osprey_flight_solutions", "risk_zones", priority=2),
        DataSource("api", "eurocontrol", "notams/conflict", priority=3),
        DataSource("api", "jeppesen", "airport/special_procedures", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        conflict_zones = ["Ukraine/Russia", "Middle East", "Horn of Africa", "Myanmar", "Sahel"]
        high_risk_airports = ["Kathmandu", "Tegucigalpa", "Paro", "Funchal", "Gibraltar"]
        
        exposed_conflicts = self._rng.sample(conflict_zones, self._rng.randint(0, 2))
        challenging_destinations = self._rng.sample(high_risk_airports, self._rng.randint(0, 3))
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "conflict_exposure": {
                "active_conflict_zones": exposed_conflicts,
                "overfly_restrictions": len(exposed_conflicts) > 0,
                "rerouting_cost_impact_pct": len(exposed_conflicts) * self._rng.uniform(0.5, 2),
            },
            "airport_risk": {
                "challenging_airports_served": challenging_destinations,
                "special_qualification_required": len(challenging_destinations) > 0,
                "terrain_exposure_score": self._weighted_choice([("Low", 0.50), ("Medium", 0.35), ("High", 0.15)]),
            },
            "destination_risk": {
                "high_risk_countries": self._rng.sample(
                    ["Iran", "Iraq", "Afghanistan", "Yemen", "Libya", "Syria"],
                    self._rng.randint(0, 3)
                ),
                "cat_2_3_countries": self._rng.randint(0, 5),
            },
            "weather_exposure": {
                "hurricane_exposed_routes_pct": round(self._rng.uniform(0, 30), 1),
                "monsoon_exposed_routes_pct": round(self._rng.uniform(0, 40), 1),
                "winter_weather_hub": self._rng.random() > 0.60,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "conflict_zones": len(exposed_conflicts),
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


# =============================================================================
# CYBER EXTRACTORS
# =============================================================================

@register_extractor
class SecurityScorecardExtractor(DataExtractor):
    """
    SecurityScorecard/BitSight - External security ratings.
    
    Signals: security_rating, tls_score, email_auth, exposure
    
    Alternative Sources:
    - BitSight: ratings/company
    - SecurityScorecard: companies/score
    - RiskRecon: ratings
    """
    source_name = "security_scorecard"
    coverage = "cyber"
    signals = ["security_rating", "tls_score", "email_auth", "exposure", "software_currency"]
    ttl_config = TTLConfig.semi_static("Security ratings updated weekly")
    
    alternative_sources = [
        DataSource("api", "bitsight", "ratings/company", priority=1),
        DataSource("api", "securityscorecard", "companies/score", priority=1),
        DataSource("api", "riskrecon", "ratings", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        overall_score = self._weighted_choice([
            (self._rng.randint(85, 100), 0.20), (self._rng.randint(70, 84), 0.40),
            (self._rng.randint(55, 69), 0.25), (self._rng.randint(30, 54), 0.15)
        ])
        
        grade_map = {range(90, 101): "A", range(80, 90): "B", range(70, 80): "C", 
                    range(60, 70): "D", range(0, 60): "F"}
        grade = next((g for r, g in grade_map.items() if overall_score in r), "F")
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "overall_rating": {
                "score": overall_score,
                "grade": grade,
                "trend": self._weighted_choice([("Improving", 0.30), ("Stable", 0.50), ("Declining", 0.20)]),
                "last_updated": self._random_date(7, 0),
            },
            "factor_scores": {
                "network_security": self._rng.randint(50, 100),
                "dns_health": self._rng.randint(60, 100),
                "patching_cadence": self._rng.randint(40, 100),
                "endpoint_security": self._rng.randint(50, 100),
                "ip_reputation": self._rng.randint(60, 100),
                "application_security": self._rng.randint(50, 100),
                "cubit_score": self._rng.randint(50, 100),
                "hacker_chatter": self._rng.randint(70, 100),
                "information_leak": self._rng.randint(60, 100),
                "social_engineering": self._rng.randint(60, 100),
            },
            "issues": {
                "critical": self._rng.randint(0, 5),
                "high": self._rng.randint(0, 15),
                "medium": self._rng.randint(0, 30),
                "low": self._rng.randint(0, 50),
            },
            "peer_comparison": {
                "industry_rank_pct": self._rng.randint(10, 90),
                "industry_average_score": self._rng.randint(65, 80),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "score": overall_score,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class TechnicalScanExtractor(DataExtractor):
    """
    Technical Security Scans - TLS, headers, DNS, exposed services.
    
    Signals: tls_score, security_headers, dnssec, waf_presence, cdn_usage
    
    Alternative Sources:
    - SSL Labs: analyze
    - SecurityHeaders.com: scan
    - Shodan: host/search
    - Censys: hosts/search
    """
    source_name = "technical_scan"
    coverage = "cyber"
    signals = ["tls_score", "security_headers", "dnssec", "waf_presence", "cdn_usage", "cloud_infrastructure"]
    ttl_config = TTLConfig.dynamic("Technical scans refreshed daily")
    
    alternative_sources = [
        DataSource("scan", "ssllabs", "analyze", priority=1),
        DataSource("scan", "securityheaders.com", "scan", priority=1),
        DataSource("api", "shodan", "host/search", priority=2),
        DataSource("api", "censys", "hosts/search", priority=2),
        DataSource("dns", "internal", "dnssec_validator", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        tls_grade = self._weighted_choice([
            ("A+", 0.15), ("A", 0.30), ("A-", 0.15), ("B", 0.20), ("C", 0.12), ("D", 0.05), ("F", 0.03)
        ])
        
        headers_present = []
        all_headers = ["HSTS", "X-Content-Type-Options", "X-Frame-Options", "CSP", "X-XSS-Protection", "Referrer-Policy"]
        for h in all_headers:
            if self._rng.random() > 0.30:
                headers_present.append(h)
        
        raw_data = {
            "domain": self.kwargs.get("domain", f"example-{self._random_id().lower()}.com"),
            "tls_analysis": {
                "grade": tls_grade,
                "protocol_support": {
                    "tls13": self._rng.random() > 0.30,
                    "tls12": True,
                    "tls11": self._rng.random() < 0.20,
                    "tls10": self._rng.random() < 0.10,
                },
                "certificate": {
                    "valid": True,
                    "days_to_expiry": self._rng.randint(10, 365),
                    "issuer": self._weighted_choice([
                        ("Let's Encrypt", 0.40), ("DigiCert", 0.20), ("Comodo", 0.15),
                        ("GlobalSign", 0.10), ("Other", 0.15)
                    ]),
                },
                "vulnerabilities": {
                    "heartbleed": False,
                    "poodle": self._rng.random() < 0.05,
                    "beast": self._rng.random() < 0.08,
                },
            },
            "security_headers": {
                "present": headers_present,
                "missing": [h for h in all_headers if h not in headers_present],
                "score": len(headers_present) / len(all_headers) * 100,
            },
            "dns_security": {
                "dnssec_enabled": self._rng.random() > 0.60,
                "caa_record": self._rng.random() > 0.50,
            },
            "email_security": {
                "spf": self._weighted_choice([("Pass", 0.80), ("Softfail", 0.10), ("Fail", 0.05), ("None", 0.05)]),
                "dkim": self._rng.random() > 0.70,
                "dmarc": self._weighted_choice([("Reject", 0.25), ("Quarantine", 0.30), ("None", 0.30), ("Not Set", 0.15)]),
            },
            "infrastructure": {
                "waf_detected": self._rng.random() > 0.40,
                "waf_vendor": self._weighted_choice([
                    ("Cloudflare", 0.30), ("AWS WAF", 0.20), ("Akamai", 0.15),
                    ("Imperva", 0.10), ("Other", 0.15), (None, 0.10)
                ]) if self._rng.random() > 0.40 else None,
                "cdn_detected": self._rng.random() > 0.50,
                "cdn_vendor": self._weighted_choice([
                    ("Cloudflare", 0.35), ("AWS CloudFront", 0.25), ("Akamai", 0.15),
                    ("Fastly", 0.10), ("Other", 0.15)
                ]) if self._rng.random() > 0.50 else None,
                "cloud_provider": self._weighted_choice([
                    ("AWS", 0.40), ("Azure", 0.25), ("GCP", 0.15),
                    ("On-Premise", 0.15), ("Other", 0.05)
                ]),
            },
            "exposed_services": {
                "total_open_ports": self._rng.randint(2, 20),
                "high_risk_ports": self._rng.randint(0, 3),
                "exposed_admin_panels": self._rng.random() < 0.10,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="scan",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "tls_grade": tls_grade,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CVEExposureExtractor(DataExtractor):
    """
    CVE Exposure Analysis - Known vulnerabilities in detected software.
    
    Signals: cve_exposure, software_currency
    
    Alternative Sources:
    - NVD: cves/search
    - VulnDB: vulnerabilities/by_product
    - Wappalyzer: lookup
    """
    source_name = "cve_exposure"
    coverage = "cyber"
    signals = ["cve_exposure", "software_currency"]
    ttl_config = TTLConfig.dynamic("CVE data updated daily")
    
    alternative_sources = [
        DataSource("api", "nvd", "cves/search", priority=1),
        DataSource("api", "vulndb", "vulnerabilities/by_product", priority=2),
        DataSource("api", "wappalyzer", "lookup", priority=3),
        DataSource("correlation", "internal", "version_to_cve_mapper", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        num_critical = self._weighted_choice([(0, 0.60), (1, 0.20), (2, 0.12), (self._rng.randint(3, 8), 0.08)])
        num_high = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.25)])
        
        technologies = [
            {"name": "Apache", "version": f"2.4.{self._rng.randint(40, 58)}", "category": "Web Server"},
            {"name": "nginx", "version": f"1.{self._rng.randint(18, 25)}.{self._rng.randint(0, 5)}", "category": "Web Server"},
            {"name": "PHP", "version": f"{self._rng.choice([7, 8])}.{self._rng.randint(0, 4)}.{self._rng.randint(0, 30)}", "category": "Runtime"},
            {"name": "WordPress", "version": f"6.{self._rng.randint(0, 4)}", "category": "CMS"},
            {"name": "jQuery", "version": f"3.{self._rng.randint(5, 7)}.{self._rng.randint(0, 1)}", "category": "JavaScript"},
        ]
        
        detected = self._rng.sample(technologies, self._rng.randint(2, 5))
        
        raw_data = {
            "domain": self.kwargs.get("domain", f"example-{self._random_id().lower()}.com"),
            "vulnerability_summary": {
                "critical": num_critical,
                "high": num_high,
                "medium": self._rng.randint(0, 20),
                "low": self._rng.randint(0, 50),
                "total": num_critical + num_high + self._rng.randint(0, 70),
            },
            "detected_technologies": detected,
            "outdated_software": {
                "count": self._rng.randint(0, len(detected)),
                "components": [t["name"] for t in detected if self._rng.random() < 0.30],
            },
            "patching_analysis": {
                "mean_time_to_patch_days": self._rng.randint(7, 90),
                "unpatched_critical_days": self._rng.randint(0, 60) if num_critical > 0 else 0,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "critical_cves": num_critical,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class BreachDatabaseExtractor(DataExtractor):
    """
    Breach Database - Historical breaches, regulatory notifications.
    
    Signals: breach_history, regulatory_action, credential_exposure
    
    Alternative Sources:
    - HHS Breach Portal: breaches/search
    - PrivacyRights: breaches/search
    - HaveIBeenPwned: breaches/domain
    - GDPR Tracker: fines/search
    """
    source_name = "breach_database"
    coverage = "cyber"
    signals = ["breach_history", "regulatory_action", "credential_exposure"]
    ttl_config = TTLConfig.dynamic("Breach data updated daily")
    
    alternative_sources = [
        DataSource("api", "hhs_breach_portal", "breaches/search", priority=1),
        DataSource("api", "privacyrights", "breaches/search", priority=1),
        DataSource("api", "haveibeenpwned", "breaches/domain", priority=2),
        DataSource("api", "gdpr_tracker", "fines/search", priority=3),
        DataSource("news", "gdelt", "data breach {company}", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        num_breaches = self._weighted_choice([(0, 0.70), (1, 0.18), (2, 0.08), (self._rng.randint(3, 5), 0.04)])
        
        breaches = []
        total_records = 0
        
        for _ in range(num_breaches):
            records = self._weighted_choice([
                (self._rng.randint(100, 10000), 0.50),
                (self._rng.randint(10000, 100000), 0.30),
                (self._rng.randint(100000, 1000000), 0.15),
                (self._rng.randint(1000000, 10000000), 0.05),
            ])
            total_records += records
            
            breaches.append({
                "date": self._random_date(1825, 30),
                "records_exposed": records,
                "data_types": self._rng.sample(
                    ["Email", "Password", "SSN", "Credit Card", "Medical", "Financial", "PII"],
                    self._rng.randint(1, 4)
                ),
                "cause": self._weighted_choice([
                    ("External Attack", 0.50), ("Insider", 0.15),
                    ("Lost Device", 0.10), ("Misconfiguration", 0.15), ("Vendor", 0.10)
                ]),
                "notification_required": self._rng.random() > 0.30,
                "regulatory_fine_usd": self._rng.randint(0, 5000000) if self._rng.random() < 0.20 else 0,
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "breach_history": {
                "total_breaches_5yr": num_breaches,
                "total_records_exposed": total_records,
                "breaches": sorted(breaches, key=lambda x: x["date"], reverse=True),
            },
            "regulatory_actions": {
                "total_fines_usd": sum(b["regulatory_fine_usd"] for b in breaches),
                "consent_decrees": sum(1 for b in breaches if b["regulatory_fine_usd"] > 100000),
                "ftc_actions": self._rng.randint(0, 1) if num_breaches > 0 else 0,
                "state_ag_actions": self._rng.randint(0, 2) if num_breaches > 0 else 0,
            },
            "credential_exposure": {
                "domain_in_breach": self._rng.random() < 0.40,
                "exposed_accounts": self._rng.randint(0, 500) if self._rng.random() < 0.40 else 0,
                "password_exposure": self._rng.random() < 0.20,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "breaches": num_breaches,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CyberGovernanceExtractor(DataExtractor):
    """
    Cyber Governance Data - CISO, certifications, policies.
    
    Signals: security_leadership, compliance_badges, security_page, bug_bounty
    
    Alternative Sources:
    - LinkedIn: people/search (CISO)
    - SOC2 Registry: reports/search
    - HackerOne: programs/search
    - Bugcrowd: programs/search
    - Company website scraping
    """
    source_name = "cyber_governance"
    coverage = "cyber"
    signals = ["security_leadership", "compliance_badges", "security_page", "bug_bounty"]
    ttl_config = TTLConfig.semi_static("Governance data updated weekly")
    
    alternative_sources = [
        DataSource("api", "linkedin", "people/search", {"title": ["CISO", "VP Security"]}, priority=1),
        DataSource("api", "soc2_registry", "reports/search", priority=2),
        DataSource("api", "hackerone", "programs/search", priority=3),
        DataSource("api", "bugcrowd", "programs/search", priority=3),
        DataSource("scrape", "company_website", "/security", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        has_ciso = self._rng.random() > 0.35
        
        certifications = []
        all_certs = ["SOC 2 Type II", "SOC 2 Type I", "ISO 27001", "PCI DSS", "HIPAA", "FedRAMP", "GDPR"]
        for cert in all_certs:
            if self._rng.random() > 0.60:
                certifications.append({
                    "certification": cert,
                    "status": self._weighted_choice([("Current", 0.85), ("Expired", 0.10), ("In Progress", 0.05)]),
                    "scope": self._weighted_choice([("Enterprise-wide", 0.60), ("Product/Service", 0.30), ("Partial", 0.10)]),
                    "last_audit": self._random_date(365, 0),
                })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "leadership": {
                "has_ciso": has_ciso,
                "ciso_tenure_years": self._rng.randint(1, 10) if has_ciso else None,
                "ciso_reports_to": self._weighted_choice([("CEO", 0.40), ("CIO", 0.35), ("CFO", 0.15), ("Board", 0.10)]) if has_ciso else None,
                "board_cyber_oversight": self._rng.random() > 0.50,
                "security_team_size": self._rng.randint(1, 50) if has_ciso else self._rng.randint(0, 5),
            },
            "certifications": certifications,
            "policies": {
                "security_page_exists": self._rng.random() > 0.40,
                "privacy_policy_comprehensive": self._rng.random() > 0.60,
                "security_txt_present": self._rng.random() > 0.25,
                "bug_bounty_program": self._rng.random() > 0.20,
                "bug_bounty_platform": self._weighted_choice([
                    ("HackerOne", 0.40), ("Bugcrowd", 0.30), ("Internal", 0.30)
                ]) if self._rng.random() > 0.20 else None,
                "incident_response_plan": self._rng.random() > 0.65,
                "business_continuity_plan": self._rng.random() > 0.70,
                "security_awareness_training": self._rng.random() > 0.75,
            },
            "maturity": {
                "level": self._weighted_choice([(1, 0.10), (2, 0.25), (3, 0.40), (4, 0.20), (5, 0.05)]),
                "framework": self._weighted_choice([
                    ("NIST CSF", 0.40), ("ISO 27001", 0.25), ("CIS", 0.15), ("Custom", 0.15), ("None", 0.05)
                ]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_ciso": has_ciso,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class VendorSecurityExtractor(DataExtractor):
    """
    Vendor Security / Third-Party Risk - VRM program, vendor assessment.
    
    Signals: vendor_risk_program, second_degree risk
    
    Alternative Sources:
    - Company disclosures
    - Security questionnaires
    """
    source_name = "vendor_security"
    coverage = "cyber"
    signals = ["vendor_risk_program", "second_degree_risk"]
    ttl_config = TTLConfig.semi_static("Vendor risk data updated weekly")
    
    alternative_sources = [
        DataSource("scrape", "company_website", "/security", priority=1),
        DataSource("api", "clearbit", "company/customers", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        vrm_exists = self._rng.random() > 0.40
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "program_maturity": {
                "vrm_program_exists": vrm_exists,
                "dedicated_vrm_team": vrm_exists and self._rng.random() > 0.50,
                "automated_monitoring": vrm_exists and self._rng.random() > 0.30,
                "continuous_monitoring": vrm_exists and self._rng.random() > 0.25,
            },
            "assessment_coverage": {
                "vendors_with_data_access": self._rng.randint(20, 200),
                "assessed_12mo_pct": self._rng.randint(40, 100) if vrm_exists else self._rng.randint(0, 30),
                "critical_assessed_pct": self._rng.randint(70, 100) if vrm_exists else self._rng.randint(20, 60),
            },
            "vendor_inventory": {
                "total": self._rng.randint(50, 500),
                "critical": self._rng.randint(5, 30),
                "high_risk": self._rng.randint(10, 50),
                "by_category": {
                    "Cloud/SaaS": self._rng.randint(20, 100),
                    "Data Processors": self._rng.randint(5, 30),
                    "Professional Services": self._rng.randint(10, 50),
                    "Other": self._rng.randint(15, 100),
                },
            },
            "incident_history": {
                "vendor_breaches_3yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
                "supply_chain_incidents": self._weighted_choice([(0, 0.80), (1, 0.15), (2, 0.05)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "vrm_exists": vrm_exists,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class IncidentResponseExtractor(DataExtractor):
    """
    Incident Response Capabilities - IR plan, SOC, retainers.
    
    Signals: ir_capabilities, soc_capabilities
    """
    source_name = "incident_response"
    coverage = "cyber"
    signals = ["ir_capabilities", "soc_capabilities"]
    ttl_config = TTLConfig.semi_static("IR capabilities assessed periodically")
    
    alternative_sources = [
        DataSource("scrape", "company_website", "/security", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        has_soc = self._rng.random() > 0.45
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "ir_capabilities": {
                "ir_plan_documented": self._rng.random() > 0.60,
                "ir_plan_tested_12mo": self._rng.random() > 0.40,
                "tabletop_exercises_12mo": self._rng.randint(0, 4),
                "ir_retainer": self._rng.random() > 0.35,
                "ir_provider": self._weighted_choice([
                    ("CrowdStrike", 0.25), ("Mandiant", 0.20), ("Secureworks", 0.15),
                    ("Kroll", 0.15), ("Other", 0.20), (None, 0.05)
                ]) if self._rng.random() > 0.35 else None,
            },
            "soc_capabilities": {
                "has_soc": has_soc,
                "soc_type": self._weighted_choice([
                    ("In-House", 0.30), ("Managed (MSSP)", 0.50), ("Hybrid", 0.20)
                ]) if has_soc else None,
                "24x7_coverage": has_soc and self._rng.random() > 0.40,
                "siem_deployed": has_soc and self._rng.random() > 0.80,
                "edr_deployed": self._rng.random() > 0.60,
                "xdr_deployed": self._rng.random() > 0.25,
            },
            "response_metrics": {
                "mttd_hours": self._rng.randint(1, 168),
                "mttr_hours": self._rng.randint(4, 336),
                "incidents_12mo": self._rng.randint(0, 50),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_soc": has_soc,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ThreatIntelligenceExtractor(DataExtractor):
    """
    Threat Intelligence - Dark web monitoring, credential exposure.
    
    Signals: dark_web, credential_exposure
    
    Alternative Sources:
    - Recorded Future: darkweb/search
    - Flashpoint: exposure/search
    - SpyCloud: breach/domain
    """
    source_name = "threat_intelligence"
    coverage = "cyber"
    signals = ["dark_web", "credential_exposure"]
    ttl_config = TTLConfig.dynamic("Threat intel updated daily")
    
    alternative_sources = [
        DataSource("api", "recorded_future", "darkweb/search", priority=1),
        DataSource("api", "flashpoint", "exposure/search", priority=2),
        DataSource("api", "spycloud", "breach/domain", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        mentions = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 20), 0.35), (self._rng.randint(21, 100), 0.15)])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "dark_web_monitoring": {
                "mentions_90d": mentions,
                "data_for_sale": self._rng.random() < 0.08,
                "credential_dumps": self._rng.randint(0, 5) if mentions > 10 else 0,
                "threat_actor_interest": self._weighted_choice([
                    ("Low", 0.70), ("Medium", 0.20), ("High", 0.08), ("Critical", 0.02)
                ]),
            },
            "credential_exposure": {
                "total_exposed_credentials": self._rng.randint(0, 1000),
                "executives_exposed": self._rng.randint(0, 10),
                "recent_exposure_30d": self._rng.random() < 0.15,
            },
            "brand_monitoring": {
                "phishing_domains_detected": self._rng.randint(0, 20),
                "lookalike_domains": self._rng.randint(0, 50),
                "social_media_impersonation": self._rng.random() < 0.10,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "mentions": mentions,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CyberInsuranceHistoryExtractor(DataExtractor):
    """
    Cyber Insurance History - Prior coverage, claims.
    
    Signals: insurance_history, claims_history
    """
    source_name = "cyber_insurance_history"
    coverage = "cyber"
    signals = ["insurance_history", "claims_history"]
    ttl_config = TTLConfig.semi_static("Insurance history updated periodically")
    
    alternative_sources = [
        DataSource("internal", "placement_history", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        years_coverage = self._weighted_choice([(0, 0.20), (self._rng.randint(1, 3), 0.40), (self._rng.randint(4, 10), 0.40)])
        
        claims = []
        num_claims = self._weighted_choice([(0, 0.75), (1, 0.15), (2, 0.07), (self._rng.randint(3, 5), 0.03)])
        
        for _ in range(num_claims):
            claims.append({
                "year": self._rng.randint(2018, 2024),
                "type": self._weighted_choice([
                    ("Ransomware", 0.35), ("Data Breach", 0.30),
                    ("BEC", 0.15), ("System Failure", 0.10), ("Other", 0.10)
                ]),
                "incurred_usd": self._weighted_choice([
                    (self._rng.randint(10000, 100000), 0.50),
                    (self._rng.randint(100000, 500000), 0.30),
                    (self._rng.randint(500000, 2000000), 0.15),
                    (self._rng.randint(2000000, 10000000), 0.05),
                ]),
                "status": self._weighted_choice([("Closed", 0.70), ("Open", 0.30)]),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "coverage_history": {
                "years_with_coverage": years_coverage,
                "current_limit_usd": self._rng.choice([1000000, 2000000, 5000000, 10000000, 25000000]) if years_coverage > 0 else 0,
                "current_retention_usd": self._rng.choice([10000, 25000, 50000, 100000, 250000]) if years_coverage > 0 else 0,
                "coverage_continuous": years_coverage > 2 and self._rng.random() > 0.10,
            },
            "claims_history": {
                "total_claims_5yr": num_claims,
                "total_incurred_usd": sum(c["incurred_usd"] for c in claims),
                "claims": claims,
                "loss_ratio": round(sum(c["incurred_usd"] for c in claims) / max(years_coverage * 50000, 1), 3),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="internal",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "claims": num_claims,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class BSAAMLExtractor(DataExtractor):
    """
    BSA/AML Compliance - Bank Secrecy Act, Anti-Money Laundering.
    
    Signals: bsa_aml, fair_lending, consumer_compliance
    """
    source_name = "bsa_aml"
    coverage = "financial_institutions"
    signals = ["bsa_aml", "fair_lending", "consumer_compliance"]
    ttl_config = TTLConfig.dynamic("BSA/AML monitored daily")
    
    alternative_sources = [
        DataSource("api", "fincen", "enforcement/actions", priority=1),
        DataSource("api", "occ", "enforcement/bsa", priority=2),
        DataSource("api", "ofac", "sanctions/search", priority=3),
        DataSource("api", "cfpb", "enforcement/fair_lending", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        bsa_rating = self._weighted_choice([
            ("Satisfactory", 0.85), ("Needs Improvement", 0.10), ("Deficient", 0.05)
        ])
        
        raw_data = {
            "institution_id": self.kwargs.get("rssd_id", self._random_id("", 10)),
            "bsa_aml": {
                "exam_rating": bsa_rating,
                "last_exam_date": self._random_date(365, 30),
                "sars_filed_12mo": self._rng.randint(10, 500),
                "ctrs_filed_12mo": self._rng.randint(50, 2000),
                "enforcement_actions": 1 if bsa_rating == "Deficient" else 0,
                "lookback_required": bsa_rating == "Deficient" and self._rng.random() < 0.50,
            },
            "ofac_compliance": {
                "screening_program": True,
                "violations_5yr": self._weighted_choice([(0, 0.95), (1, 0.04), (2, 0.01)]),
                "penalties_usd": self._rng.randint(0, 1000000) if self._rng.random() < 0.05 else 0,
            },
            "fair_lending": {
                "hmda_issues": self._rng.random() < 0.10,
                "fair_lending_exam_issues": self._rng.random() < 0.08,
                "doj_referrals": self._rng.random() < 0.02,
            },
            "consumer_compliance": {
                "cfpb_exams_3yr": self._rng.randint(0, 3),
                "mras_outstanding": self._rng.randint(0, 5),
                "udaap_issues": self._rng.random() < 0.08,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "bsa_rating": bsa_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FIGovernanceExtractor(DataExtractor):
    """
    FI Governance Data - Board, risk committee, audit.
    
    Signals: board_independence, board_expertise, risk_committee, audit_committee
    """
    source_name = "fi_governance"
    coverage = "financial_institutions"
    signals = ["board_independence", "board_expertise", "risk_committee", "audit_committee", 
               "executive_stability", "related_party"]
    ttl_config = TTLConfig.semi_static("Governance data updated periodically")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "DEF 14A", priority=1),
        DataSource("scrape", "company_website", "/governance", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        board_size = self._rng.randint(9, 18)
        
        raw_data = {
            "institution_id": self.kwargs.get("rssd_id", self._random_id("", 10)),
            "board_composition": {
                "total_directors": board_size,
                "independent_pct": self._rng.randint(70, 95),
                "banking_experience_pct": self._rng.randint(40, 80),
                "risk_expertise_pct": self._rng.randint(30, 60),
                "audit_expertise_pct": self._rng.randint(40, 70),
            },
            "committees": {
                "risk_committee_exists": True,
                "risk_committee_independent": self._rng.random() > 0.90,
                "cro_reports_to_board": self._rng.random() > 0.70,
                "audit_committee_independent": True,
                "audit_financial_expert": True,
            },
            "management": {
                "ceo_tenure_years": self._rng.randint(2, 20),
                "cfo_tenure_years": self._rng.randint(1, 15),
                "cro_exists": self._rng.random() > 0.80,
                "management_stability": self._weighted_choice([("High", 0.60), ("Medium", 0.30), ("Low", 0.10)]),
            },
            "risk_management": {
                "erm_framework": self._rng.random() > 0.85,
                "risk_appetite_statement": self._rng.random() > 0.90,
                "stress_testing_program": self._rng.random() > 0.80,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "board_size": board_size,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FIOperationalRiskExtractor(DataExtractor):
    """
    FI Operational Risk - CFPB complaints, incidents, litigation.
    
    Signals: cfpb_complaint, operational_incident, litigation
    """
    source_name = "fi_operational"
    coverage = "financial_institutions"
    signals = ["cfpb_complaint", "operational_incident", "litigation", "bbb_complaint"]
    ttl_config = TTLConfig.dynamic("Operational data monitored daily")
    
    alternative_sources = [
        DataSource("api", "cfpb", "complaints/company", priority=1),
        DataSource("api", "bbb", "business/search", priority=2),
        DataSource("api", "pacer", "cases/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        complaints_per_billion = self._weighted_choice([
            (self._rng.randint(10, 50), 0.50),
            (self._rng.randint(51, 100), 0.30),
            (self._rng.randint(101, 300), 0.20),
        ])
        
        raw_data = {
            "institution_id": self.kwargs.get("rssd_id", self._random_id("", 10)),
            "cfpb_complaints": {
                "total_12mo": self._rng.randint(50, 5000),
                "per_billion_deposits": complaints_per_billion,
                "vs_peer_average": round(self._rng.uniform(0.5, 2.0), 2),
                "timely_response_pct": self._rng.randint(90, 100),
                "top_issues": self._rng.sample([
                    "Mortgage", "Credit Card", "Bank Account", "Debt Collection",
                    "Credit Reporting", "Student Loans"
                ], 3),
            },
            "operational_incidents": {
                "system_outages_12mo": self._rng.randint(0, 10),
                "data_breaches_5yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
                "fraud_losses_bps": self._rng.randint(5, 50),
            },
            "litigation": {
                "active_class_actions": self._weighted_choice([(0, 0.75), (1, 0.15), (2, 0.10)]),
                "settlements_5yr_usd": self._rng.randint(0, 50) * 1_000_000,
            },
            "control_environment": {
                "sox_deficiencies": self._rng.randint(0, 3),
                "audit_findings": self._rng.randint(0, 10),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "complaints_per_billion": complaints_per_billion,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FICyberExtractor(DataExtractor):
    """
    FI Cybersecurity - FFIEC CAT, security program, incidents.
    
    Signals: cyber_maturity, security_program, breach_history
    """
    source_name = "fi_cyber"
    coverage = "financial_institutions"
    signals = ["cyber_maturity", "security_program", "breach_history", "tls_score", "email_auth"]
    ttl_config = TTLConfig.dynamic("Cyber posture monitored daily")
    
    alternative_sources = [
        DataSource("scan", "ssllabs", "analyze", priority=1),
        DataSource("api", "bitsight", "ratings/company", priority=2),
        DataSource("api", "privacyrights", "breaches/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        cat_level = self._weighted_choice([(1, 0.05), (2, 0.25), (3, 0.45), (4, 0.20), (5, 0.05)])
        
        raw_data = {
            "institution_id": self.kwargs.get("rssd_id", self._random_id("", 10)),
            "ffiec_cat": {
                "maturity_level": cat_level,
                "inherent_risk": self._weighted_choice([
                    ("Least", 0.10), ("Minimal", 0.25), ("Moderate", 0.40),
                    ("Significant", 0.20), ("Most", 0.05)
                ]),
                "last_assessment": self._random_date(365, 0),
            },
            "security_program": {
                "ciso_exists": self._rng.random() > 0.70,
                "24x7_monitoring": self._rng.random() > 0.60,
                "pen_test_frequency": self._weighted_choice([("Annual", 0.50), ("Semi-Annual", 0.30), ("Quarterly", 0.20)]),
                "vendor_risk_program": self._rng.random() > 0.75,
            },
            "incident_history": {
                "breaches_5yr": self._weighted_choice([(0, 0.75), (1, 0.18), (2, 0.07)]),
                "breach_notifications_required": self._rng.random() < 0.20,
                "regulatory_findings": self._rng.randint(0, 5),
            },
            "technical_security": {
                "tls_grade": self._weighted_choice([("A+", 0.20), ("A", 0.40), ("B", 0.25), ("C", 0.15)]),
                "mfa_deployed": self._rng.random() > 0.90,
                "encryption_at_rest": self._rng.random() > 0.95,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "cat_level": cat_level,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FILitigationExtractor(DataExtractor):
    """
    FI Litigation Data - Class actions, regulatory fines.
    
    Signals: litigation_history, regulatory_fines
    """
    source_name = "fi_litigation"
    coverage = "financial_institutions"
    signals = ["litigation_history", "regulatory_fines"]
    ttl_config = TTLConfig.dynamic("Litigation monitored daily")
    
    alternative_sources = [
        DataSource("api", "pacer", "cases/search", priority=1),
        DataSource("api", "courtlistener", "search", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        active_cases = self._weighted_choice([(0, 0.60), (self._rng.randint(1, 3), 0.30), (self._rng.randint(4, 10), 0.10)])
        
        raw_data = {
            "institution_id": self.kwargs.get("rssd_id", self._random_id("", 10)),
            "litigation": {
                "active_class_actions": active_cases,
                "total_cases_5yr": active_cases + self._rng.randint(0, 10),
                "total_settlements_usd": self._rng.randint(0, 100) * 1_000_000,
            },
            "regulatory_fines": {
                "total_5yr_usd": self._rng.randint(0, 50) * 1_000_000,
                "cfpb_penalties": self._rng.randint(0, 10) * 1_000_000,
                "occ_cmps": self._rng.randint(0, 5) * 1_000_000,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "active_cases": active_cases,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


# =============================================================================
# ENERGY EXTRACTORS
# =============================================================================

@register_extractor
class OSHASafetyExtractor(DataExtractor):
    """
    OSHA Safety Data - TRIR, violations, fatalities.
    
    Signals: osha_trir, osha_violations, fatality, process_safety
    """
    source_name = "osha_safety"
    coverage = "energy"
    signals = ["osha_trir", "osha_violations", "fatality", "near_miss"]
    ttl_config = TTLConfig.dynamic("Safety data monitored daily")
    
    alternative_sources = [
        DataSource("api", "osha", "iir/search", priority=1),
        DataSource("api", "osha", "violations/search", priority=2),
        DataSource("api", "bls", "industry_safety", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        trir = round(self._weighted_choice([
            (self._rng.uniform(0.3, 1.0), 0.30),
            (self._rng.uniform(1.0, 2.0), 0.40),
            (self._rng.uniform(2.0, 4.0), 0.25),
            (self._rng.uniform(4.0, 8.0), 0.05),
        ]), 2)
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "safety_metrics": {
                "trir": trir,
                "trir_vs_industry": round(trir / 1.5, 2),
                "dart_rate": round(trir * 0.6, 2),
                "lwcr": round(trir * 0.3, 2),
                "fatalities_5yr": self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.05)]),
                "hours_worked": self._rng.randint(1, 50) * 1_000_000,
            },
            "osha_violations": {
                "total_5yr": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 20), 0.15)]),
                "serious": self._rng.randint(0, 5),
                "willful": self._rng.randint(0, 1),
                "repeat": self._rng.randint(0, 2),
                "total_penalties_usd": self._rng.randint(0, 500000),
            },
            "process_safety": {
                "tier1_events_3yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
                "tier2_events_3yr": self._rng.randint(0, 5),
            },
            "safety_program": {
                "vpp_participant": self._rng.random() > 0.80,
                "iso_45001_certified": self._rng.random() > 0.60,
                "stop_work_authority": self._rng.random() > 0.95,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "trir": trir,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class EPAComplianceExtractor(DataExtractor):
    """
    EPA Compliance Data - Violations, spills, emissions.
    
    Signals: epa_violation, spill_history, emissions_compliance, flaring, methane
    """
    source_name = "epa_compliance"
    coverage = "energy"
    signals = ["epa_violation", "spill_history", "emissions_compliance", "flaring", "methane"]
    ttl_config = TTLConfig.dynamic("Environmental data monitored daily")
    
    alternative_sources = [
        DataSource("api", "epa_echo", "violations/search", priority=1),
        DataSource("api", "nrc", "reports/search", priority=2),
        DataSource("api", "epa", "ghgrp/methane", priority=3),
        DataSource("satellite", "viirs", "flaring_detector", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        violations = self._weighted_choice([(0, 0.60), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 20), 0.10)])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "violations": {
                "total_5yr": violations,
                "caa_violations": self._rng.randint(0, violations) if violations > 0 else 0,
                "cwa_violations": self._rng.randint(0, violations) if violations > 0 else 0,
                "rcra_violations": self._rng.randint(0, max(0, violations - 2)) if violations > 2 else 0,
                "total_penalties_usd": violations * self._rng.randint(10000, 100000),
                "consent_decrees_active": self._rng.random() < 0.10,
            },
            "spills": {
                "reportable_spills_5yr": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 20), 0.15)]),
                "total_volume_bbls": self._rng.randint(0, 5000),
                "significant_spills": self._rng.randint(0, 2),
            },
            "emissions": {
                "ghg_intensity_kg_co2e_boe": round(self._rng.uniform(15, 50), 1),
                "methane_intensity_pct": round(self._rng.uniform(0.1, 2.0), 2),
                "flaring_intensity_mcf_boe": round(self._rng.uniform(0.01, 0.20), 3),
                "routine_flaring": self._rng.random() < 0.30,
            },
            "remediation": {
                "active_remediation_sites": self._rng.randint(0, 10),
                "superfund_sites": self._rng.randint(0, 1),
                "aro_liability_usd": self._rng.randint(10, 500) * 1_000_000,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "violations": violations,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ProductionDataExtractor(DataExtractor):
    """
    Production Data - Volumes, efficiency, trends.
    
    Signals: production_consistency, operational_efficiency
    """
    source_name = "production_data"
    coverage = "energy"
    signals = ["production_consistency", "operational_efficiency"]
    ttl_config = TTLConfig.semi_static("Production data updated monthly")
    
    alternative_sources = [
        DataSource("api", "enverus", "production/history", priority=1),
        DataSource("api", "state_commissions", "production/operator", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        boed = self._weighted_choice([
            (self._rng.randint(5000, 25000), 0.40),
            (self._rng.randint(25000, 100000), 0.35),
            (self._rng.randint(100000, 500000), 0.20),
            (self._rng.randint(500000, 2000000), 0.05),
        ])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "production": {
                "total_boed": boed,
                "oil_pct": self._rng.randint(30, 80),
                "gas_pct": 100 - self._rng.randint(30, 80),
                "yoy_change_pct": round(self._rng.uniform(-15, 25), 1),
                "production_volatility": self._weighted_choice([("Low", 0.40), ("Medium", 0.40), ("High", 0.20)]),
            },
            "efficiency": {
                "loe_per_boe": round(self._rng.uniform(5, 20), 2),
                "loe_vs_peers": round(self._rng.uniform(0.7, 1.3), 2),
                "uptime_pct": round(self._rng.uniform(90, 99), 1),
            },
            "wells": {
                "total_operated": self._rng.randint(100, 5000),
                "active_pct": self._rng.randint(70, 95),
                "avg_age_years": self._rng.randint(3, 15),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "boed": boed,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ReserveDataExtractor(DataExtractor):
    """
    Reserve Data - Proved reserves, reserve life, quality.
    
    Signals: reserve_life, reserve_quality, decommissioning
    """
    source_name = "reserve_data"
    coverage = "energy"
    signals = ["reserve_life", "reserve_quality", "decommissioning"]
    ttl_config = TTLConfig.semi_static("Reserve data updated annually")
    
    alternative_sources = [
        DataSource("api", "enverus", "assets/reserves", priority=1),
        DataSource("filing", "sec_edgar", "10-K", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        proved_reserves = self._rng.randint(50, 2000) * 1_000_000
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "reserves": {
                "proved_reserves_mmboe": proved_reserves // 1_000_000,
                "proved_developed_pct": self._rng.randint(50, 85),
                "proved_undeveloped_pct": 100 - self._rng.randint(50, 85),
                "pv10_usd": proved_reserves * self._rng.uniform(8, 20),
            },
            "reserve_life": {
                "years": round(self._rng.uniform(5, 25), 1),
                "reserve_replacement_ratio": round(self._rng.uniform(0.6, 1.5), 2),
            },
            "asset_quality": {
                "avg_well_productivity_boed": self._rng.randint(50, 500),
                "decline_rate_pct": self._rng.randint(15, 45),
            },
            "decommissioning": {
                "aro_liability_usd": self._rng.randint(50, 500) * 1_000_000,
                "wells_to_plug": self._rng.randint(100, 2000),
                "funded_pct": self._rng.randint(20, 80),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "proved_reserves": proved_reserves,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class EnergyFinancialExtractor(DataExtractor):
    """
    Energy Financial Data - Leverage, hedging, credit.
    
    Signals: credit_rating, leverage, aro_coverage, capex_trend
    """
    source_name = "energy_financial"
    coverage = "energy"
    signals = ["credit_rating", "leverage", "aro_coverage", "capex_trend", "restructuring"]
    ttl_config = TTLConfig.semi_static("Financial data updated quarterly")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "10-K", priority=1),
        DataSource("api", "sp_global", "ratings", priority=2),
        DataSource("api", "bloomberg", "fundamentals", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        debt_to_ebitdax = round(self._weighted_choice([
            (self._rng.uniform(0.5, 1.5), 0.25),
            (self._rng.uniform(1.5, 3.0), 0.40),
            (self._rng.uniform(3.0, 5.0), 0.25),
            (self._rng.uniform(5.0, 8.0), 0.10),
        ]), 2)
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "financials": {
                "revenue_usd": self._rng.randint(500, 20000) * 1_000_000,
                "ebitdax_usd": self._rng.randint(200, 8000) * 1_000_000,
                "capex_usd": self._rng.randint(100, 5000) * 1_000_000,
            },
            "leverage": {
                "total_debt_usd": self._rng.randint(500, 15000) * 1_000_000,
                "debt_to_ebitdax": debt_to_ebitdax,
                "interest_coverage": round(self._rng.uniform(2, 10), 1),
            },
            "hedging": {
                "oil_hedged_12mo_pct": self._rng.randint(20, 80),
                "gas_hedged_12mo_pct": self._rng.randint(20, 80),
                "hedge_floor_price_wti": self._rng.randint(50, 75),
            },
            "liquidity": {
                "rbl_availability_usd": self._rng.randint(100, 2000) * 1_000_000,
                "rbl_drawn_pct": self._rng.randint(20, 70),
                "cash_usd": self._rng.randint(50, 500) * 1_000_000,
            },
            "credit": {
                "has_rating": self._rng.random() > 0.40,
                "rating": self._weighted_choice([
                    ("BB+", 0.15), ("BB", 0.25), ("BB-", 0.20),
                    ("B+", 0.20), ("B", 0.15), ("B-", 0.05)
                ]) if self._rng.random() > 0.40 else None,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="filing",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "debt_to_ebitdax": debt_to_ebitdax,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ESGMetricsExtractor(DataExtractor):
    """
    ESG Metrics - Emissions, governance, targets.
    
    Signals: ghg_intensity, esg_governance, net_zero_commitment
    """
    source_name = "esg_metrics"
    coverage = "energy"
    signals = ["ghg_intensity", "esg_governance", "net_zero_commitment"]
    ttl_config = TTLConfig.semi_static("ESG data updated periodically")
    
    alternative_sources = [
        DataSource("api", "cdp", "responses/search", priority=1),
        DataSource("api", "msci", "esg/ratings", priority=2),
        DataSource("scrape", "company_website", "/sustainability", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        esg_score = self._weighted_choice([
            ("AAA", 0.05), ("AA", 0.10), ("A", 0.20), ("BBB", 0.30),
            ("BB", 0.20), ("B", 0.10), ("CCC", 0.05)
        ])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "emissions": {
                "scope1_mtco2e": self._rng.randint(100000, 5000000),
                "scope2_mtco2e": self._rng.randint(10000, 500000),
                "ghg_intensity_kg_co2e_boe": round(self._rng.uniform(15, 50), 1),
                "methane_intensity_pct": round(self._rng.uniform(0.1, 2.0), 2),
                "yoy_reduction_pct": round(self._rng.uniform(-5, 15), 1),
            },
            "governance": {
                "esg_committee": self._rng.random() > 0.60,
                "executive_esg_kpis": self._rng.random() > 0.50,
                "sustainability_report": self._rng.random() > 0.70,
                "tcfd_disclosure": self._rng.random() > 0.50,
                "cdp_participant": self._rng.random() > 0.40,
            },
            "targets": {
                "net_zero_commitment": self._rng.random() > 0.40,
                "net_zero_year": self._rng.choice([2040, 2050]) if self._rng.random() > 0.40 else None,
                "interim_targets": self._rng.random() > 0.50,
                "sbti_validated": self._rng.random() > 0.20,
            },
            "ratings": {
                "msci_esg": esg_score,
                "sustainalytics_risk": self._weighted_choice([
                    ("Low", 0.15), ("Medium", 0.45), ("High", 0.30), ("Severe", 0.10)
                ]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "esg_score": esg_score,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class StateRegulatoryExtractor(DataExtractor):
    """
    State Regulatory Data - Permits, NOVs, compliance.
    
    Signals: permit_status, regulatory_standing
    """
    source_name = "state_regulatory"
    coverage = "energy"
    signals = ["permit_status", "regulatory_standing"]
    ttl_config = TTLConfig.dynamic("Regulatory status monitored daily")
    
    alternative_sources = [
        DataSource("api", "state_commissions", "permits/status", priority=1),
        DataSource("api", "bsee", "permits/status", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        states_operated = self._rng.sample(
            ["Texas", "New Mexico", "Oklahoma", "Colorado", "North Dakota", "Louisiana", "Wyoming"],
            self._rng.randint(1, 5)
        )
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "operating_states": states_operated,
            "permit_status": {
                "active_permits": self._rng.randint(100, 2000),
                "pending_permits": self._rng.randint(10, 200),
                "denied_12mo": self._rng.randint(0, 10),
                "states_in_good_standing": len(states_operated) - self._rng.randint(0, 1),
            },
            "violations": {
                "novs_12mo": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 10), 0.35), (self._rng.randint(11, 50), 0.15)]),
                "administrative_orders": self._rng.randint(0, 3),
                "penalties_12mo_usd": self._rng.randint(0, 500000),
            },
            "bonding": {
                "total_bond_usd": self._rng.randint(1, 50) * 1_000_000,
                "bond_adequacy": self._weighted_choice([("Adequate", 0.80), ("Under Review", 0.15), ("Deficient", 0.05)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "states": len(states_operated),
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class WellIntegrityExtractor(DataExtractor):
    """
    Well Integrity Data - Testing, workovers, P&A.
    
    Signals: well_integrity, maintenance_pattern
    """
    source_name = "well_integrity"
    coverage = "energy"
    signals = ["well_integrity", "maintenance_pattern"]
    ttl_config = TTLConfig.semi_static("Well data updated monthly")
    
    alternative_sources = [
        DataSource("api", "state_commissions", "wells/status", priority=1),
        DataSource("api", "enverus", "wells/integrity", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        total_wells = self._rng.randint(200, 5000)
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "well_inventory": {
                "total_operated": total_wells,
                "producing": int(total_wells * self._rng.uniform(0.60, 0.85)),
                "shut_in": int(total_wells * self._rng.uniform(0.05, 0.20)),
                "plugged": int(total_wells * self._rng.uniform(0.05, 0.15)),
            },
            "integrity_testing": {
                "mit_compliance_pct": self._rng.randint(90, 100),
                "failed_tests_12mo": self._rng.randint(0, total_wells // 50),
                "remediation_backlog": self._rng.randint(0, total_wells // 100),
            },
            "workover_activity": {
                "workovers_12mo": self._rng.randint(total_wells // 50, total_wells // 10),
                "avg_workover_cost_usd": self._rng.randint(50000, 500000),
            },
            "p_and_a": {
                "wells_awaiting_pa": self._rng.randint(0, total_wells // 20),
                "orphan_well_liability": self._rng.random() < 0.05,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "total_wells": total_wells,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


# =============================================================================
# PROFESSIONAL INDEMNITY EXTRACTORS
# =============================================================================

@register_extractor
class StateBarExtractor(DataExtractor):
    """
    State Bar Data - License status, disciplinary history, CLE compliance.
    
    Signals: license_status, disciplinary_history, ce_compliance, specialty_certification
    """
    source_name = "state_bar"
    coverage = "professional_indemnity"
    signals = ["license_status", "disciplinary_history", "ce_compliance", "specialty_certification"]
    ttl_config = TTLConfig.dynamic("License status monitored daily")
    
    alternative_sources = [
        DataSource("api", "state_bar", "attorney/status", priority=1),
        DataSource("api", "state_bar", "discipline/search", priority=2),
        DataSource("api", "state_bar", "cle/status", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_attorneys = self._rng.randint(5, 500)
        
        license_statuses = {
            "active": int(num_attorneys * self._rng.uniform(0.90, 0.98)),
            "inactive": int(num_attorneys * self._rng.uniform(0.01, 0.05)),
            "suspended": int(num_attorneys * self._rng.uniform(0, 0.02)),
        }
        
        disciplinary = self._weighted_choice([(0, 0.80), (1, 0.12), (2, 0.05), (self._rng.randint(3, 5), 0.03)])
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "license_summary": {
                "total_attorneys": num_attorneys,
                "by_status": license_statuses,
                "jurisdictions": self._rng.randint(1, 15),
                "good_standing_pct": round(license_statuses["active"] / num_attorneys * 100, 1),
            },
            "disciplinary_history": {
                "total_actions_10yr": disciplinary,
                "by_severity": {
                    "public_reprimand": self._rng.randint(0, disciplinary),
                    "suspension": self._rng.randint(0, max(0, disciplinary - 1)),
                    "disbarment": 0 if disciplinary < 3 else self._rng.randint(0, 1),
                },
                "pending_matters": self._rng.randint(0, 1),
            },
            "cle_compliance": {
                "compliance_rate_pct": self._rng.randint(95, 100),
                "avg_hours_per_attorney": self._rng.randint(20, 40),
                "delinquent_count": self._rng.randint(0, max(1, num_attorneys // 50)),
            },
            "certifications": {
                "board_certified": self._rng.randint(0, num_attorneys // 10),
                "specializations": self._rng.sample([
                    "Civil Trial", "Criminal", "Family", "Real Estate",
                    "Tax", "Estate Planning", "IP", "Labor", "Health"
                ], self._rng.randint(1, 5)),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "attorneys": num_attorneys,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MalpracticeClaimsExtractor(DataExtractor):
    """
    Malpractice Claims Data - Claims history, settlements, frequency.
    
    Signals: malpractice_record, claims_frequency
    """
    source_name = "malpractice_claims"
    coverage = "professional_indemnity"
    signals = ["malpractice_record", "claims_frequency"]
    ttl_config = TTLConfig.dynamic("Claims data monitored daily")
    
    alternative_sources = [
        DataSource("api", "pacer", "cases/search", priority=1),
        DataSource("api", "state_courts", "judgments/search", priority=2),
        DataSource("api", "westlaw", "verdicts/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_professionals = self._rng.randint(10, 200)
        claims_5yr = self._weighted_choice([
            (0, 0.50), (1, 0.25), (2, 0.12), (self._rng.randint(3, 5), 0.08), (self._rng.randint(6, 10), 0.05)
        ])
        
        claims = []
        for _ in range(claims_5yr):
            with_payment = self._rng.random() > 0.40
            claims.append({
                "claim_date": self._random_date(1825, 0),
                "status": self._weighted_choice([("Closed", 0.70), ("Open", 0.30)]),
                "with_payment": with_payment,
                "payment_usd": self._rng.randint(25000, 500000) if with_payment else 0,
                "claim_type": self._weighted_choice([
                    ("Legal Malpractice", 0.40), ("Accounting Malpractice", 0.25),
                    ("E&O", 0.20), ("Breach of Fiduciary", 0.15)
                ]),
            })
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "claims_summary_5yr": {
                "total_claims": claims_5yr,
                "claims_with_payment": sum(1 for c in claims if c["with_payment"]),
                "claims_no_payment": sum(1 for c in claims if not c["with_payment"]),
                "total_paid_usd": sum(c["payment_usd"] for c in claims),
                "open_claims": sum(1 for c in claims if c["status"] == "Open"),
            },
            "claims": sorted(claims, key=lambda x: x["claim_date"], reverse=True),
            "frequency_metrics": {
                "claims_per_professional": round(claims_5yr / num_professionals, 3),
                "vs_industry_average": round(self._rng.uniform(0.5, 2.0), 2),
            },
            "loss_history": {
                "largest_claim_usd": max((c["payment_usd"] for c in claims), default=0),
                "avg_claim_usd": sum(c["payment_usd"] for c in claims) // max(len([c for c in claims if c["with_payment"]]), 1) if claims else 0,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "claims": claims_5yr,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PeerReviewExtractor(DataExtractor):
    """
    Peer Review Data - AICPA peer review, PCAOB inspection.
    
    Signals: peer_review, pcaob_standing
    """
    source_name = "peer_review"
    coverage = "professional_indemnity"
    signals = ["peer_review", "pcaob_standing"]
    ttl_config = TTLConfig.semi_static("Peer review results updated periodically")
    
    alternative_sources = [
        DataSource("api", "aicpa", "peerreview/search", priority=1),
        DataSource("api", "pcaob", "firms/search", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        peer_review_rating = self._weighted_choice([
            ("Pass", 0.75), ("Pass with Deficiencies", 0.15),
            ("Fail", 0.05), ("Not Enrolled", 0.05)
        ])
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "aicpa_peer_review": {
                "enrolled": peer_review_rating != "Not Enrolled",
                "latest_rating": peer_review_rating if peer_review_rating != "Not Enrolled" else None,
                "review_date": self._random_date(1095, 0) if peer_review_rating != "Not Enrolled" else None,
                "next_review_due": self._random_date(-365, 365) if peer_review_rating != "Not Enrolled" else None,
                "findings_count": self._rng.randint(0, 5) if peer_review_rating in ("Pass with Deficiencies", "Fail") else 0,
            },
            "pcaob_status": {
                "registered": self._rng.random() > 0.70,
                "inspection_count": self._rng.randint(0, 3),
                "deficiencies_cited": self._rng.randint(0, 10) if self._rng.random() > 0.70 else 0,
                "quality_control_criticisms": self._rng.randint(0, 3),
            },
            "quality_control": {
                "qc_document_current": peer_review_rating in ("Pass", "Pass with Deficiencies"),
                "independence_monitoring": self._rng.random() > 0.85,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "rating": peer_review_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class QualityManagementExtractor(DataExtractor):
    """
    Quality Management Data - QMS, certifications, standards.
    
    Signals: quality_management_system, iso_certifications
    """
    source_name = "quality_management"
    coverage = "professional_indemnity"
    signals = ["quality_management_system", "iso_certifications"]
    ttl_config = TTLConfig.semi_static("QMS data updated periodically")
    
    alternative_sources = [
        DataSource("scrape", "company_website", "/about", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        has_qms = self._rng.random() > 0.40
        
        certifications = []
        possible_certs = ["ISO 9001", "ISO 27001", "ISO 14001", "Mansfield Certified"]
        for cert in possible_certs:
            if self._rng.random() > 0.70:
                certifications.append({
                    "certification": cert,
                    "status": "Current",
                    "expiry": self._random_date(-365, 730),
                })
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "qms": {
                "documented": has_qms,
                "framework": self._weighted_choice([
                    ("ISO 9001", 0.30), ("Custom", 0.50), ("None", 0.20)
                ]) if has_qms else "None",
                "last_internal_audit": self._random_date(365, 0) if has_qms else None,
                "continuous_improvement": has_qms and self._rng.random() > 0.60,
            },
            "certifications": certifications,
            "professional_standards": {
                "ethics_program": self._rng.random() > 0.70,
                "conflict_checking": self._rng.random() > 0.90,
                "document_retention": self._rng.random() > 0.85,
                "client_intake_process": self._rng.random() > 0.80,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="scrape",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_qms": has_qms,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PINetworkAuthorityExtractor(DataExtractor):
    """
    Network Authority Data - Rankings, panel memberships, reputation.
    
    Signals: peer_ranking, client_quality, panel_membership
    """
    source_name = "network_authority"
    coverage = "professional_indemnity"
    signals = ["peer_ranking", "client_quality", "panel_membership", "thought_leadership"]
    ttl_config = TTLConfig.static("Rankings updated annually")
    
    alternative_sources = [
        DataSource("api", "chambers", "rankings/search", priority=1),
        DataSource("api", "legal500", "rankings/search", priority=2),
        DataSource("api", "bestlawyers", "search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        firm_tier = self._weighted_choice([
            ("Am Law 100", 0.10), ("Am Law 200", 0.15), ("Regional Leader", 0.25),
            ("Boutique", 0.30), ("Small Firm", 0.20)
        ])
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "rankings": {
                "firm_tier": firm_tier,
                "chambers_ranked": self._rng.random() > 0.40,
                "chambers_bands": self._rng.randint(1, 6) if self._rng.random() > 0.40 else 0,
                "legal500_ranked": self._rng.random() > 0.35,
                "best_lawyers_count": self._rng.randint(0, 50),
                "super_lawyers_count": self._rng.randint(0, 30),
            },
            "panel_memberships": {
                "insurance_panels": self._rng.randint(0, 10),
                "bank_approved_lists": self._rng.randint(0, 5),
                "corporate_preferred": self._rng.randint(0, 15),
                "primary_panel_pct": self._rng.randint(20, 80),
            },
            "client_quality": {
                "fortune_500_clients": self._rng.randint(0, 30) if firm_tier in ("Am Law 100", "Am Law 200") else self._rng.randint(0, 5),
                "public_company_clients": self._rng.randint(0, 50),
                "institutional_clients_pct": self._rng.randint(20, 80),
            },
            "thought_leadership": {
                "publications_12mo": self._rng.randint(0, 100),
                "speaking_engagements": self._rng.randint(0, 50),
                "cle_presentations": self._rng.randint(0, 30),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "tier": firm_tier,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ClientQualityExtractor(DataExtractor):
    """
    Client Quality Data - Concentration, retention, risk profile.
    
    Signals: client_concentration, client_retention, high_risk_clients
    """
    source_name = "client_quality"
    coverage = "professional_indemnity"
    signals = ["client_concentration", "client_retention", "high_risk_clients"]
    ttl_config = TTLConfig.semi_static("Client data updated periodically")
    
    alternative_sources = [
        DataSource("internal", "client_management", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        top_client_pct = self._rng.randint(5, 40)
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "concentration": {
                "top_client_revenue_pct": top_client_pct,
                "top_5_clients_pct": min(top_client_pct * 3, 80),
                "top_10_clients_pct": min(top_client_pct * 5, 95),
                "single_client_dependency": top_client_pct > 25,
            },
            "retention": {
                "client_retention_rate_pct": self._rng.randint(70, 95),
                "avg_client_tenure_years": self._rng.randint(3, 15),
                "new_clients_12mo": self._rng.randint(10, 200),
                "lost_clients_12mo": self._rng.randint(5, 50),
            },
            "risk_profile": {
                "high_risk_industry_pct": self._rng.randint(5, 40),
                "contingency_fee_pct": self._rng.randint(0, 50),
                "class_action_exposure": self._rng.random() < 0.20,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="internal",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "concentration": top_client_pct,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ProfessionalDevelopmentExtractor(DataExtractor):
    """
    Professional Development Data - Training, CPE, specializations.
    
    Signals: cpe_compliance, specializations, training_program
    """
    source_name = "professional_development"
    coverage = "professional_indemnity"
    signals = ["cpe_compliance", "specializations", "training_program"]
    ttl_config = TTLConfig.semi_static("Development data updated periodically")
    
    alternative_sources = [
        DataSource("api", "nasba", "cpe/status", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        cpe_compliance = self._rng.randint(90, 100)
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "cpe_compliance": {
                "compliance_rate_pct": cpe_compliance,
                "avg_hours_per_professional": self._rng.randint(30, 60),
                "ethics_hours_completed": self._rng.randint(2, 8),
            },
            "specializations": {
                "board_certifications": self._rng.randint(0, 20),
                "specialty_areas": self._rng.randint(3, 15),
                "advanced_degrees": self._rng.randint(0, 30),
            },
            "training_program": {
                "internal_training_hours": self._rng.randint(20, 80),
                "mentorship_program": self._rng.random() > 0.60,
                "professional_development_budget": self._rng.random() > 0.70,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "cpe_compliance": cpe_compliance,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FirmStabilityExtractor(DataExtractor):
    """
    Firm Stability Data - Tenure, turnover, financial health.
    
    Signals: tenure, partner_stability, staff_retention, financial_stability
    """
    source_name = "firm_stability"
    coverage = "professional_indemnity"
    signals = ["tenure", "partner_stability", "staff_retention", "financial_stability"]
    ttl_config = TTLConfig.dynamic("Stability metrics monitored daily")
    
    alternative_sources = [
        DataSource("api", "dnb", "company/profile", priority=1),
        DataSource("api", "linkedin", "company/employees", priority=2),
        DataSource("api", "glassdoor", "reviews/company", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        years_established = self._rng.randint(5, 100)
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "tenure": {
                "years_established": years_established,
                "founding_partners_remaining": self._rng.randint(0, 5) if years_established < 30 else 0,
            },
            "partner_stability": {
                "partner_turnover_12mo_pct": self._rng.randint(2, 20),
                "lateral_departures_12mo": self._rng.randint(0, 10),
                "lateral_hires_12mo": self._rng.randint(0, 15),
                "avg_partner_tenure_years": self._rng.randint(5, 20),
            },
            "staff_metrics": {
                "associate_turnover_pct": self._rng.randint(10, 35),
                "staff_turnover_pct": self._rng.randint(8, 25),
                "glassdoor_rating": round(self._rng.uniform(2.5, 4.5), 1),
            },
            "financial_health": {
                "revenue_growth_yoy_pct": round(self._rng.uniform(-10, 20), 1),
                "rpp_growth_yoy_pct": round(self._rng.uniform(-5, 15), 1),
                "collection_rate_pct": self._rng.randint(85, 98),
                "wip_days": self._rng.randint(30, 120),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "years": years_established,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PIFinancialExtractor(DataExtractor):
    """
    PI Financial Data - Revenue, profitability, insurance history.
    
    Signals: revenue_size, financial_health, insurance_history
    """
    source_name = "pi_financial"
    coverage = "professional_indemnity"
    signals = ["revenue_size", "financial_health", "insurance_history"]
    ttl_config = TTLConfig.semi_static("Financial data updated periodically")
    
    alternative_sources = [
        DataSource("api", "dnb", "company/financials", priority=1),
        DataSource("internal", "placement_history", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([
            (self._rng.randint(1, 10) * 1_000_000, 0.40),
            (self._rng.randint(10, 50) * 1_000_000, 0.30),
            (self._rng.randint(50, 200) * 1_000_000, 0.20),
            (self._rng.randint(200, 1000) * 1_000_000, 0.10),
        ])
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FIRM", 8)),
            "revenue": {
                "total_revenue_usd": revenue,
                "revenue_per_lawyer_usd": revenue // self._rng.randint(5, 500),
                "revenue_growth_3yr_cagr_pct": round(self._rng.uniform(-5, 15), 1),
            },
            "profitability": {
                "profit_margin_pct": self._rng.randint(20, 50),
                "profit_per_equity_partner_usd": self._rng.randint(200000, 3000000),
                "realization_rate_pct": self._rng.randint(85, 98),
            },
            "insurance_history": {
                "years_continuous_coverage": self._rng.randint(3, 30),
                "current_limit_usd": self._rng.choice([1000000, 2000000, 5000000, 10000000]),
                "current_retention_usd": self._rng.choice([25000, 50000, 100000, 250000]),
                "claims_free_years": self._rng.randint(0, 10),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "revenue": revenue,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


# =============================================================================
# CROSS-COVERAGE EXTRACTORS
# =============================================================================

@register_extractor
class CreditRatingExtractor(DataExtractor):
    """
    Credit Rating Data - S&P, Moody's, Fitch ratings.
    
    Signals: credit_rating
    
    Used across: Marine, Aerospace, D&O, FI, Energy
    """
    source_name = "credit_rating"
    coverage = "cross_coverage"
    signals = ["credit_rating"]
    ttl_config = TTLConfig.semi_static("Credit ratings updated weekly")
    
    alternative_sources = [
        DataSource("api", "sp_global", "ratings", priority=1),
        DataSource("api", "moodys", "ratings", priority=1),
        DataSource("api", "fitch", "ratings", priority=2),
        DataSource("api", "kroll", "ratings", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        has_rating = self._rng.random() > 0.40
        
        sp_scale = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
                   "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
        moodys_scale = ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3",
                       "Ba1", "Ba2", "Ba3", "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"]
        
        rating_idx = self._weighted_choice([
            (self._rng.randint(0, 3), 0.10),   # AAA to AA-
            (self._rng.randint(4, 9), 0.35),   # A+ to BBB-
            (self._rng.randint(10, 15), 0.40), # BB+ to B-
            (self._rng.randint(16, 21), 0.15), # CCC+ to D
        ])
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "has_rating": has_rating,
            "ratings": {
                "sp": sp_scale[rating_idx] if has_rating else None,
                "moodys": moodys_scale[min(rating_idx, len(moodys_scale) - 1)] if has_rating else None,
                "fitch": sp_scale[rating_idx] if has_rating and self._rng.random() > 0.30 else None,
            },
            "outlook": self._weighted_choice([
                ("Stable", 0.55), ("Positive", 0.15), ("Negative", 0.25), ("Watch Negative", 0.05)
            ]) if has_rating else None,
            "investment_grade": rating_idx <= 9 if has_rating else None,
            "last_action": {
                "date": self._random_date(365, 0) if has_rating else None,
                "type": self._weighted_choice([("Affirmed", 0.60), ("Upgraded", 0.15), ("Downgraded", 0.20), ("New", 0.05)]) if has_rating else None,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_rating": has_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CompanyProfileExtractor(DataExtractor):
    """
    Company Profile Data - Basic company information, D&B data.
    
    Signals: company_type, size_band, geography, industry
    
    Used across all coverages
    """
    source_name = "company_profile"
    coverage = "cross_coverage"
    signals = ["company_type", "size_band", "geography", "industry"]
    ttl_config = TTLConfig.semi_static("Company profile updated weekly")
    
    alternative_sources = [
        DataSource("api", "dnb", "company/profile", priority=1),
        DataSource("api", "pitchbook", "companies/profile", priority=2),
        DataSource("api", "linkedin", "company/about", priority=3),
        DataSource("scrape", "company_website", "/about", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        company_type = self._weighted_choice([
            ("Public", 0.30), ("Private", 0.50), ("PE-Backed", 0.15), ("Non-Profit", 0.05)
        ])
        
        employees = self._weighted_choice([
            (self._rng.randint(10, 50), 0.25),
            (self._rng.randint(50, 250), 0.30),
            (self._rng.randint(250, 1000), 0.25),
            (self._rng.randint(1000, 10000), 0.15),
            (self._rng.randint(10000, 100000), 0.05),
        ])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "basic_info": {
                "company_name": self.kwargs.get("company_name", self._random_company_name("Corp")),
                "company_type": company_type,
                "year_founded": self._rng.randint(1900, 2020),
                "employees": employees,
            },
            "size_classification": {
                "size_band": self._classify_size(employees),
                "revenue_band": self._weighted_choice([
                    ("Under $10M", 0.25), ("$10M-$50M", 0.25), ("$50M-$250M", 0.25),
                    ("$250M-$1B", 0.15), ("Over $1B", 0.10)
                ]),
            },
            "geography": {
                "headquarters_country": self._weighted_choice([
                    ("United States", 0.40), ("United Kingdom", 0.10), ("Germany", 0.08),
                    ("Canada", 0.07), ("France", 0.05), ("Other", 0.30)
                ]),
                "headquarters_state": self._rng.choice(["California", "New York", "Texas", "Florida", "Illinois"]),
                "operating_countries": self._rng.randint(1, 50),
            },
            "industry": {
                "primary_sic": str(self._rng.randint(1000, 9999)),
                "primary_naics": str(self._rng.randint(100000, 999999)),
                "industry_description": self._weighted_choice([
                    "Technology", "Healthcare", "Financial Services", "Manufacturing",
                    "Retail", "Energy", "Professional Services", "Transportation"
                ]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "company_type": company_type,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )
    
    def _classify_size(self, employees: int) -> str:
        if employees < 50: return "Small"
        elif employees < 250: return "Medium"
        elif employees < 1000: return "Large"
        else: return "Enterprise"


@register_extractor  
class NewsMediaExtractor(DataExtractor):
    """
    News & Media Monitoring - GDELT, news APIs for reputation signals.
    
    Signals: media_sentiment, news_mentions
    
    Used across all coverages
    """
    source_name = "news_media"
    coverage = "cross_coverage"
    signals = ["media_sentiment", "news_mentions"]
    ttl_config = TTLConfig.dynamic("News monitored continuously")
    
    alternative_sources = [
        DataSource("news", "gdelt", "query", priority=1),
        DataSource("api", "businesswire", "releases/company", priority=2),
        DataSource("api", "prnewswire", "releases/company", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        mentions = self._rng.randint(0, 500)
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "news_coverage": {
                "mentions_30d": mentions,
                "mentions_90d": mentions * 3,
                "trend": self._weighted_choice([("Increasing", 0.30), ("Stable", 0.50), ("Decreasing", 0.20)]),
            },
            "sentiment": {
                "overall": self._weighted_choice([
                    ("Very Positive", 0.10), ("Positive", 0.30), ("Neutral", 0.40),
                    ("Negative", 0.15), ("Very Negative", 0.05)
                ]),
                "positive_pct": self._rng.randint(20, 60),
                "negative_pct": self._rng.randint(5, 30),
            },
            "key_topics": self._rng.sample([
                "Financial Results", "Product Launch", "Leadership Change",
                "Regulatory", "M&A", "Partnership", "Controversy", "Award"
            ], self._rng.randint(2, 5)),
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "mentions": mentions,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


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
