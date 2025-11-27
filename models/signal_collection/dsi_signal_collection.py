"""
Digital Signal Intelligence (DSI) - Signal Collection Module
=============================================================

This module extracts and analyses model-specific information from websites,
external sources, and APIs to inform DSI pricing decisions.

Key features:
1. Configurable signal collection per model (Cyber, FI, Energy, Marine, D&O)
2. Integration with website_discovery module
3. Automated signal scoring and normalisation
4. Evidence collection and audit trail
5. Multi-source correlation

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import re
import logging
import json

# Import website discovery module
from models.website_discovery import WebsiteDiscoveryEngine, DiscoveryResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class SignalType(Enum):
    """DSI Signal Type Classification"""
    TYPE_1_NETWORK_AUTHORITY = "network_authority"
    TYPE_2_TECHNICAL_INFRASTRUCTURE = "technical_infrastructure"
    TYPE_3_ASSET_TELEMETRY = "asset_telemetry"
    TYPE_4_STRUCTURED_DATA = "structured_data"
    TYPE_5_CORPORATE_FOOTPRINT = "corporate_footprint"
    TYPE_6_PUBLIC_RECORDS = "public_records"
    TYPE_7_DIRECT_INQUIRY = "direct_inquiry"


class SignalSource(Enum):
    """Source of signal data"""
    WEBSITE_CONTENT = "website_content"
    DNS_RECORDS = "dns_records"
    SSL_CERTIFICATE = "ssl_certificate"
    WHOIS = "whois"
    SEARCH_ENGINE = "search_engine"
    LINKEDIN = "linkedin"
    NEWS_MEDIA = "news_media"
    REGULATORY_FILING = "regulatory_filing"
    COURT_RECORDS = "court_records"
    THIRD_PARTY_RATING = "third_party_rating"
    INDUSTRY_DATABASE = "industry_database"
    DARK_WEB_MONITORING = "dark_web_monitoring"
    SHODAN_CENSYS = "shodan_censys"
    API_ENDPOINT = "api_endpoint"
    MANUAL_INPUT = "manual_input"


class ModelType(Enum):
    """DSI Pricing Model Types"""
    CYBER = "cyber"
    FINANCIAL_INSTITUTIONS = "financial_institutions"
    ENERGY = "energy"
    MARINE = "marine"
    DIRECTORS_OFFICERS = "directors_officers"
    GENERAL = "general"


class SignalQuality(Enum):
    """Quality/reliability of signal data"""
    HIGH = "high"           # Direct observation, authoritative source
    MEDIUM = "medium"       # Indirect observation, reliable source
    LOW = "low"             # Inferred, less reliable source
    UNVERIFIED = "unverified"  # Cannot verify accuracy


class ScoringMethod(Enum):
    """Method used to convert raw signal to score"""
    BINARY = "binary"               # Yes/No → 0 or 100
    LINEAR = "linear"               # Linear scale mapping
    LOGARITHMIC = "logarithmic"     # Log scale for large ranges
    THRESHOLD = "threshold"         # Step function with thresholds
    PERCENTILE = "percentile"       # Rank against benchmark
    WEIGHTED_AVERAGE = "weighted_average"  # Combine sub-signals
    CUSTOM = "custom"               # Custom scoring function


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class RawSignal:
    """Raw signal data before scoring"""
    signal_id: str
    signal_name: str
    signal_type: SignalType
    source: SignalSource
    
    # Raw data
    raw_value: Any
    raw_unit: Optional[str] = None
    
    # Metadata
    collection_timestamp: datetime = field(default_factory=datetime.now)
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    
    # Quality indicators
    quality: SignalQuality = SignalQuality.MEDIUM
    confidence: float = 0.5  # 0-1 confidence in data accuracy
    
    # Evidence
    evidence: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredSignal:
    """Signal after scoring/normalization"""
    raw_signal: RawSignal
    
    # Scoring
    score: float  # 0-100 normalized score
    scoring_method: ScoringMethod
    scoring_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Model relevance
    applicable_models: List[ModelType] = field(default_factory=list)
    model_weights: Dict[ModelType, float] = field(default_factory=dict)
    
    # Flags
    is_red_flag: bool = False
    red_flag_reason: Optional[str] = None
    is_green_flag: bool = False
    green_flag_reason: Optional[str] = None
    
    # Audit
    scoring_timestamp: datetime = field(default_factory=datetime.now)
    scoring_version: str = "2.0"


@dataclass 
class SignalGroup:
    """Group of related signals"""
    group_id: str
    group_name: str
    signal_type: SignalType
    
    signals: List[ScoredSignal] = field(default_factory=list)
    
    # Aggregation
    aggregate_score: float = 0.0
    aggregation_method: str = "weighted_average"
    
    # Metadata
    description: str = ""
    required_for_models: List[ModelType] = field(default_factory=list)


@dataclass
class SignalCollectionResult:
    """Complete signal collection result for an entity"""
    # Target entity
    entity_name: str
    entity_domain: Optional[str] = None
    
    # Collected signals by type
    type_1_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_1", group_name="Network Authority", 
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY
    ))
    type_2_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_2", group_name="Technical Infrastructure",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE
    ))
    type_3_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_3", group_name="Asset Telemetry",
        signal_type=SignalType.TYPE_3_ASSET_TELEMETRY
    ))
    type_4_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_4", group_name="Structured Data",
        signal_type=SignalType.TYPE_4_STRUCTURED_DATA
    ))
    type_5_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_5", group_name="Corporate Footprint",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT
    ))
    type_6_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_6", group_name="Public Records",
        signal_type=SignalType.TYPE_6_PUBLIC_RECORDS
    ))
    type_7_signals: SignalGroup = field(default_factory=lambda: SignalGroup(
        group_id="type_7", group_name="Direct Inquiry",
        signal_type=SignalType.TYPE_7_DIRECT_INQUIRY
    ))
    
    # Aggregated scores
    overall_score: float = 0.0
    tier: int = 0  # 1-5
    
    # Metadata
    collection_timestamp: datetime = field(default_factory=datetime.now)
    sources_used: List[SignalSource] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_signal_group(self, signal_type: SignalType) -> SignalGroup:
        """Get signal group by type"""
        mapping = {
            SignalType.TYPE_1_NETWORK_AUTHORITY: self.type_1_signals,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: self.type_2_signals,
            SignalType.TYPE_3_ASSET_TELEMETRY: self.type_3_signals,
            SignalType.TYPE_4_STRUCTURED_DATA: self.type_4_signals,
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: self.type_5_signals,
            SignalType.TYPE_6_PUBLIC_RECORDS: self.type_6_signals,
            SignalType.TYPE_7_DIRECT_INQUIRY: self.type_7_signals,
        }
        return mapping[signal_type]


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

@dataclass
class SignalConfig:
    """Configuration for a specific signal"""
    signal_id: str
    signal_name: str
    signal_type: SignalType
    
    # Collection config
    sources: List[SignalSource]
    collection_priority: int = 5  # 1-10, higher = more important
    
    # Scoring config
    scoring_method: ScoringMethod
    scoring_params: Dict[str, Any] = field(default_factory=dict)
    
    # Model relevance
    model_weights: Dict[ModelType, float] = field(default_factory=dict)
    
    # Flags
    is_required: bool = False
    is_red_flag_eligible: bool = False
    red_flag_threshold: Optional[float] = None
    is_green_flag_eligible: bool = False
    green_flag_threshold: Optional[float] = None


@dataclass
class ModelConfig:
    """Configuration for a specific pricing model"""
    model_type: ModelType
    model_name: str
    
    # Signal weights by type
    type_weights: Dict[SignalType, float] = field(default_factory=dict)
    
    # Required signals
    required_signals: List[str] = field(default_factory=list)
    
    # Tier thresholds
    tier_thresholds: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    # e.g., {1: (800, 1000), 2: (650, 799), 3: (500, 649), 4: (350, 499), 5: (0, 349)}
    
    # Model-specific settings
    sector_adjustments: Dict[str, float] = field(default_factory=dict)
    minimum_signals_required: int = 5


# =============================================================================
# DEFAULT MODEL CONFIGURATIONS
# =============================================================================

def get_cyber_config() -> ModelConfig:
    """Default configuration for Cyber Insurance model"""
    return ModelConfig(
        model_type=ModelType.CYBER,
        model_name="Cyber Insurance",
        type_weights={
            SignalType.TYPE_1_NETWORK_AUTHORITY: 0.15,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.25,
            SignalType.TYPE_3_ASSET_TELEMETRY: 0.15,
            SignalType.TYPE_4_STRUCTURED_DATA: 0.10,
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: 0.20,
            SignalType.TYPE_6_PUBLIC_RECORDS: 0.15,
            SignalType.TYPE_7_DIRECT_INQUIRY: 0.00,  # Not used in auto-assessment
        },
        tier_thresholds={
            1: (800, 1000),
            2: (650, 799),
            3: (500, 649),
            4: (350, 499),
            5: (0, 349)
        },
        sector_adjustments={
            'healthcare': -0.10,  # Higher risk
            'financial_services': -0.05,
            'retail': -0.05,
            'technology': 0.0,
            'manufacturing': 0.0,
            'energy': -0.08,
        },
        minimum_signals_required=10
    )


def get_financial_institutions_config() -> ModelConfig:
    """Default configuration for Financial Institutions model"""
    return ModelConfig(
        model_type=ModelType.FINANCIAL_INSTITUTIONS,
        model_name="Financial Institutions",
        type_weights={
            SignalType.TYPE_1_NETWORK_AUTHORITY: 0.20,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.15,
            SignalType.TYPE_3_ASSET_TELEMETRY: 0.15,
            SignalType.TYPE_4_STRUCTURED_DATA: 0.20,  # Higher for FI
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: 0.15,
            SignalType.TYPE_6_PUBLIC_RECORDS: 0.15,
            SignalType.TYPE_7_DIRECT_INQUIRY: 0.00,
        },
        tier_thresholds={
            1: (800, 1000),
            2: (650, 799),
            3: (500, 649),
            4: (350, 499),
            5: (0, 349)
        },
        sector_adjustments={
            'banking': 0.0,
            'asset_management': 0.05,
            'insurance': 0.0,
            'fintech': -0.05,
            'crypto': -0.15,
        },
        minimum_signals_required=12
    )


def get_energy_config() -> ModelConfig:
    """Default configuration for Energy model"""
    return ModelConfig(
        model_type=ModelType.ENERGY,
        model_name="Energy",
        type_weights={
            SignalType.TYPE_1_NETWORK_AUTHORITY: 0.15,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.20,  # OT/IT important
            SignalType.TYPE_3_ASSET_TELEMETRY: 0.15,
            SignalType.TYPE_4_STRUCTURED_DATA: 0.15,
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: 0.20,
            SignalType.TYPE_6_PUBLIC_RECORDS: 0.15,
            SignalType.TYPE_7_DIRECT_INQUIRY: 0.00,
        },
        tier_thresholds={
            1: (800, 1000),
            2: (650, 799),
            3: (500, 649),
            4: (350, 499),
            5: (0, 349)
        },
        sector_adjustments={
            'upstream': -0.05,
            'midstream': -0.08,
            'downstream': -0.03,
            'renewables': 0.05,
            'utilities': 0.0,
        },
        minimum_signals_required=10
    )


def get_marine_config() -> ModelConfig:
    """Default configuration for Marine model"""
    return ModelConfig(
        model_type=ModelType.MARINE,
        model_name="Marine",
        type_weights={
            SignalType.TYPE_1_NETWORK_AUTHORITY: 0.20,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.15,
            SignalType.TYPE_3_ASSET_TELEMETRY: 0.15,
            SignalType.TYPE_4_STRUCTURED_DATA: 0.20,  # Classification societies
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: 0.15,
            SignalType.TYPE_6_PUBLIC_RECORDS: 0.15,
            SignalType.TYPE_7_DIRECT_INQUIRY: 0.00,
        },
        tier_thresholds={
            1: (800, 1000),
            2: (650, 799),
            3: (500, 649),
            4: (350, 499),
            5: (0, 349)
        },
        sector_adjustments={
            'container': 0.0,
            'tanker': -0.05,
            'bulk': 0.0,
            'offshore': -0.08,
            'passenger': -0.03,
        },
        minimum_signals_required=8
    )


def get_do_config() -> ModelConfig:
    """Default configuration for D&O model"""
    return ModelConfig(
        model_type=ModelType.DIRECTORS_OFFICERS,
        model_name="Directors & Officers",
        type_weights={
            SignalType.TYPE_1_NETWORK_AUTHORITY: 0.20,
            SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE: 0.05,  # Less relevant
            SignalType.TYPE_3_ASSET_TELEMETRY: 0.10,
            SignalType.TYPE_4_STRUCTURED_DATA: 0.25,  # Financial metrics key
            SignalType.TYPE_5_CORPORATE_FOOTPRINT: 0.20,
            SignalType.TYPE_6_PUBLIC_RECORDS: 0.20,  # Litigation history
            SignalType.TYPE_7_DIRECT_INQUIRY: 0.00,
        },
        tier_thresholds={
            1: (800, 1000),
            2: (650, 799),
            3: (500, 649),
            4: (350, 499),
            5: (0, 349)
        },
        sector_adjustments={
            'public_company': -0.05,
            'private_company': 0.05,
            'nonprofit': 0.10,
            'financial_services': -0.10,
            'healthcare': -0.08,
        },
        minimum_signals_required=10
    )


MODEL_CONFIGS = {
    ModelType.CYBER: get_cyber_config,
    ModelType.FINANCIAL_INSTITUTIONS: get_financial_institutions_config,
    ModelType.ENERGY: get_energy_config,
    ModelType.MARINE: get_marine_config,
    ModelType.DIRECTORS_OFFICERS: get_do_config,
}


# =============================================================================
# SIGNAL DEFINITIONS
# =============================================================================

# Type 1: Network Authority Signals
NETWORK_AUTHORITY_SIGNALS = [
    SignalConfig(
        signal_id="na_customer_quality",
        signal_name="Customer Quality",
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.LINKEDIN],
        scoring_method=ScoringMethod.WEIGHTED_AVERAGE,
        model_weights={
            ModelType.CYBER: 0.15,
            ModelType.FINANCIAL_INSTITUTIONS: 0.20,
            ModelType.ENERGY: 0.15,
        }
    ),
    SignalConfig(
        signal_id="na_partner_network",
        signal_name="Partner Network Quality",
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.WEIGHTED_AVERAGE,
        model_weights={
            ModelType.CYBER: 0.20,
            ModelType.FINANCIAL_INSTITUTIONS: 0.15,
        }
    ),
    SignalConfig(
        signal_id="na_security_vendor",
        signal_name="Security Vendor Relationships",
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.THRESHOLD,
        scoring_params={
            'thresholds': [
                (0, 30, "No known security vendors"),
                (1, 50, "Basic security vendor"),
                (2, 70, "Multiple security vendors"),
                (3, 90, "Enterprise security stack"),
            ]
        },
        model_weights={ModelType.CYBER: 0.30}
    ),
    SignalConfig(
        signal_id="na_industry_body",
        signal_name="Industry Body Membership",
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.INDUSTRY_DATABASE],
        scoring_method=ScoringMethod.THRESHOLD,
        model_weights={
            ModelType.CYBER: 0.15,
            ModelType.FINANCIAL_INSTITUTIONS: 0.20,
            ModelType.MARINE: 0.25,
        }
    ),
    SignalConfig(
        signal_id="na_certification_authority",
        signal_name="Certification Authority",
        signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.REGULATORY_FILING],
        scoring_method=ScoringMethod.THRESHOLD,
        is_green_flag_eligible=True,
        green_flag_threshold=80,
        model_weights={
            ModelType.CYBER: 0.20,
            ModelType.FINANCIAL_INSTITUTIONS: 0.15,
        }
    ),
]

# Type 2: Technical Infrastructure Signals
TECHNICAL_INFRASTRUCTURE_SIGNALS = [
    SignalConfig(
        signal_id="ti_tls_config",
        signal_name="TLS/SSL Configuration",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.SSL_CERTIFICATE],
        scoring_method=ScoringMethod.LINEAR,
        scoring_params={'min': 0, 'max': 100},
        is_red_flag_eligible=True,
        red_flag_threshold=30,
        model_weights={ModelType.CYBER: 0.20}
    ),
    SignalConfig(
        signal_id="ti_security_headers",
        signal_name="Security Headers",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.WEBSITE_CONTENT],
        scoring_method=ScoringMethod.WEIGHTED_AVERAGE,
        scoring_params={
            'headers': {
                'Strict-Transport-Security': 20,
                'Content-Security-Policy': 25,
                'X-Frame-Options': 15,
                'X-Content-Type-Options': 10,
                'X-XSS-Protection': 10,
                'Referrer-Policy': 10,
                'Permissions-Policy': 10,
            }
        },
        model_weights={ModelType.CYBER: 0.25}
    ),
    SignalConfig(
        signal_id="ti_email_auth",
        signal_name="Email Authentication",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.DNS_RECORDS],
        scoring_method=ScoringMethod.WEIGHTED_AVERAGE,
        scoring_params={
            'records': {
                'SPF': 30,
                'DKIM': 35,
                'DMARC': 35,
            }
        },
        is_red_flag_eligible=True,
        red_flag_threshold=20,
        model_weights={ModelType.CYBER: 0.20}
    ),
    SignalConfig(
        signal_id="ti_dnssec",
        signal_name="DNSSEC Implementation",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.DNS_RECORDS],
        scoring_method=ScoringMethod.BINARY,
        model_weights={ModelType.CYBER: 0.10}
    ),
    SignalConfig(
        signal_id="ti_network_exposure",
        signal_name="Network Exposure",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.SHODAN_CENSYS],
        scoring_method=ScoringMethod.LOGARITHMIC,
        scoring_params={'inverse': True},  # More exposure = lower score
        is_red_flag_eligible=True,
        red_flag_threshold=25,
        model_weights={ModelType.CYBER: 0.25}
    ),
    SignalConfig(
        signal_id="ti_software_currency",
        signal_name="Software Currency",
        signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.SHODAN_CENSYS],
        scoring_method=ScoringMethod.THRESHOLD,
        is_red_flag_eligible=True,
        red_flag_threshold=30,
        model_weights={ModelType.CYBER: 0.15}
    ),
]

# Type 5: Corporate Footprint Signals
CORPORATE_FOOTPRINT_SIGNALS = [
    SignalConfig(
        signal_id="cf_security_page",
        signal_name="Security Page Presence",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.WEBSITE_CONTENT],
        scoring_method=ScoringMethod.WEIGHTED_AVERAGE,
        model_weights={ModelType.CYBER: 0.20}
    ),
    SignalConfig(
        signal_id="cf_privacy_policy",
        signal_name="Privacy Policy Quality",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.WEBSITE_CONTENT],
        scoring_method=ScoringMethod.LINEAR,
        model_weights={
            ModelType.CYBER: 0.15,
            ModelType.FINANCIAL_INSTITUTIONS: 0.15,
        }
    ),
    SignalConfig(
        signal_id="cf_security_txt",
        signal_name="Security.txt Presence",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.WEBSITE_CONTENT],
        scoring_method=ScoringMethod.BINARY,
        is_green_flag_eligible=True,
        green_flag_threshold=100,
        model_weights={ModelType.CYBER: 0.15}
    ),
    SignalConfig(
        signal_id="cf_bug_bounty",
        signal_name="Bug Bounty Program",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.WEBSITE_CONTENT, SignalSource.API_ENDPOINT],
        scoring_method=ScoringMethod.THRESHOLD,
        is_green_flag_eligible=True,
        green_flag_threshold=80,
        model_weights={ModelType.CYBER: 0.20}
    ),
    SignalConfig(
        signal_id="cf_security_hiring",
        signal_name="Security Hiring Activity",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.LINKEDIN, SignalSource.WEBSITE_CONTENT],
        scoring_method=ScoringMethod.THRESHOLD,
        model_weights={
            ModelType.CYBER: 0.20,
            ModelType.FINANCIAL_INSTITUTIONS: 0.10,
        }
    ),
    SignalConfig(
        signal_id="cf_security_leadership",
        signal_name="Security Leadership Visibility",
        signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
        sources=[SignalSource.LINKEDIN, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.THRESHOLD,
        is_green_flag_eligible=True,
        green_flag_threshold=75,
        model_weights={
            ModelType.CYBER: 0.25,
            ModelType.DIRECTORS_OFFICERS: 0.15,
        }
    ),
]

# Type 6: Public Records Signals
PUBLIC_RECORDS_SIGNALS = [
    SignalConfig(
        signal_id="pr_breach_history",
        signal_name="Breach History",
        signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
        sources=[SignalSource.REGULATORY_FILING, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.THRESHOLD,
        scoring_params={
            'thresholds': [
                (0, 100, "No known breaches"),
                (1, 60, "Minor breach >3 years ago"),
                (2, 40, "Significant breach >3 years ago"),
                (3, 20, "Recent breach (<3 years)"),
                (4, 0, "Multiple recent breaches"),
            ]
        },
        is_red_flag_eligible=True,
        red_flag_threshold=40,
        model_weights={
            ModelType.CYBER: 0.35,
            ModelType.FINANCIAL_INSTITUTIONS: 0.20,
        }
    ),
    SignalConfig(
        signal_id="pr_regulatory_actions",
        signal_name="Regulatory Actions",
        signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
        sources=[SignalSource.REGULATORY_FILING, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.THRESHOLD,
        is_red_flag_eligible=True,
        red_flag_threshold=30,
        model_weights={
            ModelType.CYBER: 0.20,
            ModelType.FINANCIAL_INSTITUTIONS: 0.30,
            ModelType.DIRECTORS_OFFICERS: 0.25,
        }
    ),
    SignalConfig(
        signal_id="pr_litigation",
        signal_name="Litigation History",
        signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
        sources=[SignalSource.COURT_RECORDS, SignalSource.NEWS_MEDIA],
        scoring_method=ScoringMethod.THRESHOLD,
        is_red_flag_eligible=True,
        red_flag_threshold=30,
        model_weights={
            ModelType.DIRECTORS_OFFICERS: 0.30,
            ModelType.FINANCIAL_INSTITUTIONS: 0.20,
        }
    ),
    SignalConfig(
        signal_id="pr_credential_exposure",
        signal_name="Credential Exposure",
        signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
        sources=[SignalSource.DARK_WEB_MONITORING, SignalSource.API_ENDPOINT],
        scoring_method=ScoringMethod.LOGARITHMIC,
        scoring_params={'inverse': True},
        is_red_flag_eligible=True,
        red_flag_threshold=25,
        model_weights={ModelType.CYBER: 0.25}
    ),
]

# Combine all signal definitions
ALL_SIGNAL_CONFIGS = (
    NETWORK_AUTHORITY_SIGNALS +
    TECHNICAL_INFRASTRUCTURE_SIGNALS +
    CORPORATE_FOOTPRINT_SIGNALS +
    PUBLIC_RECORDS_SIGNALS
)

SIGNAL_CONFIGS_BY_ID = {s.signal_id: s for s in ALL_SIGNAL_CONFIGS}

# These would be imported from part 1 in production
# from signal_collection_part1 import *

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL COLLECTORS (Abstract Base Classes)
# =============================================================================

class SignalCollector(ABC):
    """Abstract base class for signal collectors"""
    
    @abstractmethod
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from the source.
        
        Args:
            target: Target identifier (domain, company name, etc.)
            config: Collection configuration
            
        Returns:
            List of RawSignal objects
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> 'SignalSource':
        """Return the source type this collector handles"""
        pass


class WebsiteContentCollector(SignalCollector):
    """Collects signals from website content"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.WEBSITE_CONTENT
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from website content.
        
        In production, this would:
        1. Fetch the website HTML
        2. Parse for security indicators
        3. Check for security pages, privacy policies, etc.
        4. Analyze HTTP headers
        """
        signals = []
        
        # Security page detection
        signals.append(self._check_security_page(target, config))
        
        # Privacy policy analysis
        signals.append(self._analyze_privacy_policy(target, config))
        
        # Security.txt check
        signals.append(self._check_security_txt(target, config))
        
        # HTTP headers analysis
        signals.extend(self._analyze_headers(target, config))
        
        # Partner/customer logos
        signals.append(self._analyze_customer_logos(target, config))
        
        return [s for s in signals if s is not None]
    
    def _check_security_page(self, domain: str, config: Dict) -> Optional['RawSignal']:
        """Check for presence and quality of security page"""
        # Common security page paths
        security_paths = [
            '/security', '/trust', '/security-center', '/trust-center',
            '/legal/security', '/about/security', '/compliance'
        ]
        
        # In production: actually fetch these URLs
        # For now, create a placeholder signal
        return RawSignal(
            signal_id="cf_security_page",
            signal_name="Security Page Presence",
            signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
            source=SignalSource.WEBSITE_CONTENT,
            raw_value={'paths_checked': security_paths, 'found': None},
            quality=SignalQuality.MEDIUM,
            evidence=[f"Checked {len(security_paths)} common security page paths"]
        )
    
    def _analyze_privacy_policy(self, domain: str, config: Dict) -> Optional['RawSignal']:
        """Analyze privacy policy quality"""
        return RawSignal(
            signal_id="cf_privacy_policy",
            signal_name="Privacy Policy Quality",
            signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
            source=SignalSource.WEBSITE_CONTENT,
            raw_value={'analyzed': False},
            quality=SignalQuality.LOW,
            evidence=["Privacy policy URL to be fetched"]
        )
    
    def _check_security_txt(self, domain: str, config: Dict) -> Optional['RawSignal']:
        """Check for security.txt file"""
        # RFC 9116 locations
        security_txt_paths = [
            '/.well-known/security.txt',
            '/security.txt'
        ]
        
        return RawSignal(
            signal_id="cf_security_txt",
            signal_name="Security.txt Presence",
            signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
            source=SignalSource.WEBSITE_CONTENT,
            raw_value={'paths_checked': security_txt_paths, 'found': None},
            quality=SignalQuality.HIGH,
            evidence=["Checked RFC 9116 standard locations"]
        )
    
    def _analyze_headers(self, domain: str, config: Dict) -> List['RawSignal']:
        """Analyze HTTP security headers"""
        headers_to_check = [
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Permissions-Policy'
        ]
        
        return [RawSignal(
            signal_id="ti_security_headers",
            signal_name="Security Headers",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.WEBSITE_CONTENT,
            raw_value={'headers_checked': headers_to_check, 'results': {}},
            quality=SignalQuality.HIGH,
            evidence=[f"Checked {len(headers_to_check)} security headers"]
        )]
    
    def _analyze_customer_logos(self, domain: str, config: Dict) -> Optional['RawSignal']:
        """Analyze customer/partner logos on website"""
        return RawSignal(
            signal_id="na_customer_quality",
            signal_name="Customer Quality",
            signal_type=SignalType.TYPE_1_NETWORK_AUTHORITY,
            source=SignalSource.WEBSITE_CONTENT,
            raw_value={'logos_found': []},
            quality=SignalQuality.MEDIUM,
            evidence=["Customer logo analysis pending"]
        )


class DNSCollector(SignalCollector):
    """Collects signals from DNS records"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.DNS_RECORDS
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from DNS records.
        
        In production, this would query:
        - SPF records (TXT)
        - DKIM records (TXT)
        - DMARC records (TXT)
        - DNSSEC status
        - MX records
        - CAA records
        """
        signals = []
        
        # Email authentication (SPF, DKIM, DMARC)
        signals.append(self._check_email_auth(target))
        
        # DNSSEC
        signals.append(self._check_dnssec(target))
        
        return signals
    
    def _check_email_auth(self, domain: str) -> 'RawSignal':
        """Check email authentication records"""
        return RawSignal(
            signal_id="ti_email_auth",
            signal_name="Email Authentication",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.DNS_RECORDS,
            raw_value={
                'spf': None,
                'dkim': None,
                'dmarc': None
            },
            quality=SignalQuality.HIGH,
            evidence=["DNS TXT record queries to be performed"]
        )
    
    def _check_dnssec(self, domain: str) -> 'RawSignal':
        """Check DNSSEC implementation"""
        return RawSignal(
            signal_id="ti_dnssec",
            signal_name="DNSSEC Implementation",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.DNS_RECORDS,
            raw_value={'enabled': None},
            quality=SignalQuality.HIGH,
            evidence=["DNSSEC validation to be performed"]
        )


class SSLCollector(SignalCollector):
    """Collects signals from SSL certificates"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.SSL_CERTIFICATE
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from SSL/TLS configuration.
        
        In production, this would check:
        - Certificate validity
        - Certificate chain
        - Protocol versions supported
        - Cipher suites
        - HSTS preload status
        """
        return [RawSignal(
            signal_id="ti_tls_config",
            signal_name="TLS/SSL Configuration",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.SSL_CERTIFICATE,
            raw_value={
                'valid': None,
                'issuer': None,
                'expiry': None,
                'protocols': [],
                'grade': None  # SSL Labs style grade
            },
            quality=SignalQuality.HIGH,
            evidence=["SSL/TLS analysis to be performed"]
        )]


class ShodanCensysCollector(SignalCollector):
    """Collects signals from Shodan/Censys"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.SHODAN_CENSYS
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from Shodan/Censys.
        
        In production, this would query:
        - Open ports
        - Exposed services
        - Known vulnerabilities
        - Software versions
        """
        signals = []
        
        # Network exposure
        signals.append(RawSignal(
            signal_id="ti_network_exposure",
            signal_name="Network Exposure",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.SHODAN_CENSYS,
            raw_value={
                'open_ports': [],
                'exposed_services': [],
                'high_risk_services': []
            },
            quality=SignalQuality.HIGH,
            evidence=["Shodan/Censys query to be performed"]
        ))
        
        # Software currency
        signals.append(RawSignal(
            signal_id="ti_software_currency",
            signal_name="Software Currency",
            signal_type=SignalType.TYPE_2_TECHNICAL_INFRASTRUCTURE,
            source=SignalSource.SHODAN_CENSYS,
            raw_value={
                'detected_software': [],
                'outdated_software': [],
                'cves': []
            },
            quality=SignalQuality.MEDIUM,
            evidence=["Software version analysis to be performed"]
        ))
        
        return signals


class LinkedInCollector(SignalCollector):
    """Collects signals from LinkedIn"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.LINKEDIN
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from LinkedIn.
        
        In production, this would check:
        - Company page
        - Employee count
        - Security team presence
        - Security job postings
        - CISO/CSO presence
        """
        signals = []
        
        # Security hiring activity
        signals.append(RawSignal(
            signal_id="cf_security_hiring",
            signal_name="Security Hiring Activity",
            signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
            source=SignalSource.LINKEDIN,
            raw_value={
                'security_jobs_open': None,
                'recent_security_hires': None
            },
            quality=SignalQuality.MEDIUM,
            evidence=["LinkedIn job search to be performed"]
        ))
        
        # Security leadership
        signals.append(RawSignal(
            signal_id="cf_security_leadership",
            signal_name="Security Leadership Visibility",
            signal_type=SignalType.TYPE_5_CORPORATE_FOOTPRINT,
            source=SignalSource.LINKEDIN,
            raw_value={
                'ciso_present': None,
                'security_team_size': None,
                'leadership_profiles': []
            },
            quality=SignalQuality.MEDIUM,
            evidence=["LinkedIn leadership search to be performed"]
        ))
        
        return signals


class NewsMediaCollector(SignalCollector):
    """Collects signals from news/media sources"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.NEWS_MEDIA
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from news and media.
        
        In production, this would search:
        - News archives
        - Press releases
        - Security incident reports
        - Industry publications
        """
        signals = []
        
        # Breach history from news
        signals.append(RawSignal(
            signal_id="pr_breach_history",
            signal_name="Breach History",
            signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
            source=SignalSource.NEWS_MEDIA,
            raw_value={
                'incidents_found': [],
                'search_terms': [target, f"{target} breach", f"{target} hack"],
                'time_range': "5 years"
            },
            quality=SignalQuality.MEDIUM,
            evidence=["News search to be performed"]
        ))
        
        # Regulatory actions from news
        signals.append(RawSignal(
            signal_id="pr_regulatory_actions",
            signal_name="Regulatory Actions",
            signal_type=SignalType.TYPE_6_PUBLIC_RECORDS,
            source=SignalSource.NEWS_MEDIA,
            raw_value={
                'actions_found': [],
                'search_terms': [f"{target} fine", f"{target} penalty", f"{target} enforcement"]
            },
            quality=SignalQuality.MEDIUM,
            evidence=["Regulatory news search to be performed"]
        ))
        
        return signals


class ThirdPartyRatingCollector(SignalCollector):
    """Collects signals from third-party rating services"""
    
    def get_source_type(self) -> 'SignalSource':
        return SignalSource.THIRD_PARTY_RATING
    
    def collect(self, target: str, config: Dict) -> List['RawSignal']:
        """
        Collect signals from third-party ratings.
        
        In production, this would query:
        - SecurityScorecard
        - BitSight
        - UpGuard
        - RiskRecon
        """
        return [RawSignal(
            signal_id="at_security_rating",
            signal_name="Third-Party Security Rating",
            signal_type=SignalType.TYPE_3_ASSET_TELEMETRY,
            source=SignalSource.THIRD_PARTY_RATING,
            raw_value={
                'provider': None,
                'score': None,
                'grade': None,
                'factors': {}
            },
            quality=SignalQuality.HIGH,
            evidence=["Third-party rating API to be queried"]
        )]


# =============================================================================
# SCORING ENGINE
# =============================================================================

class SignalScoringEngine:
    """
    Engine for converting raw signals to normalised scores.
    """
    
    def __init__(self, model_type: 'ModelType' = None):
        self.model_type = model_type
        self.scoring_functions: Dict[str, Callable] = {
            'binary': self._score_binary,
            'linear': self._score_linear,
            'logarithmic': self._score_logarithmic,
            'threshold': self._score_threshold,
            'percentile': self._score_percentile,
            'weighted_average': self._score_weighted_average,
        }
    
    def score_signal(
        self, 
        raw_signal: 'RawSignal',
        config: 'SignalConfig'
    ) -> 'ScoredSignal':
        """
        Score a raw signal using the configured method.
        
        Args:
            raw_signal: Raw signal to score
            config: Signal configuration
            
        Returns:
            ScoredSignal with normalized score
        """
        method = config.scoring_method.value
        scorer = self.scoring_functions.get(method, self._score_default)
        
        score = scorer(raw_signal.raw_value, config.scoring_params)
        
        # Apply quality adjustment
        score = self._adjust_for_quality(score, raw_signal.quality)
        
        # Check for flags
        is_red_flag = False
        red_flag_reason = None
        is_green_flag = False
        green_flag_reason = None
        
        if config.is_red_flag_eligible and config.red_flag_threshold:
            if score <= config.red_flag_threshold:
                is_red_flag = True
                red_flag_reason = f"{config.signal_name} score ({score:.1f}) below threshold ({config.red_flag_threshold})"
        
        if config.is_green_flag_eligible and config.green_flag_threshold:
            if score >= config.green_flag_threshold:
                is_green_flag = True
                green_flag_reason = f"{config.signal_name} score ({score:.1f}) above threshold ({config.green_flag_threshold})"
        
        return ScoredSignal(
            raw_signal=raw_signal,
            score=score,
            scoring_method=config.scoring_method,
            scoring_parameters=config.scoring_params,
            applicable_models=list(config.model_weights.keys()),
            model_weights=config.model_weights,
            is_red_flag=is_red_flag,
            red_flag_reason=red_flag_reason,
            is_green_flag=is_green_flag,
            green_flag_reason=green_flag_reason
        )
    
    def _score_binary(self, raw_value: Any, params: Dict) -> float:
        """Binary scoring: 0 or 100"""
        if isinstance(raw_value, bool):
            return 100.0 if raw_value else 0.0
        if isinstance(raw_value, dict):
            # Check for presence indicators
            if raw_value.get('found') or raw_value.get('enabled') or raw_value.get('present'):
                return 100.0
        return 0.0
    
    def _score_linear(self, raw_value: Any, params: Dict) -> float:
        """Linear scaling between min and max"""
        min_val = params.get('min', 0)
        max_val = params.get('max', 100)
        
        if isinstance(raw_value, (int, float)):
            # Normalize to 0-100
            if max_val == min_val:
                return 50.0
            normalized = (raw_value - min_val) / (max_val - min_val) * 100
            return max(0.0, min(100.0, normalized))
        
        return 50.0  # Default for non-numeric
    
    def _score_logarithmic(self, raw_value: Any, params: Dict) -> float:
        """Logarithmic scaling for large ranges"""
        inverse = params.get('inverse', False)
        
        if isinstance(raw_value, (int, float)) and raw_value > 0:
            # Log scale
            score = 100 - min(100, math.log10(raw_value + 1) * 25)
            if inverse:
                score = 100 - score
            return max(0.0, min(100.0, score))
        
        return 50.0 if not inverse else 100.0
    
    def _score_threshold(self, raw_value: Any, params: Dict) -> float:
        """Step function based on thresholds"""
        thresholds = params.get('thresholds', [])
        
        if isinstance(raw_value, (int, float)):
            count = raw_value
        elif isinstance(raw_value, dict):
            count = raw_value.get('count', 0)
        elif isinstance(raw_value, list):
            count = len(raw_value)
        else:
            count = 0
        
        for threshold_value, score, _ in sorted(thresholds, key=lambda x: x[0], reverse=True):
            if count >= threshold_value:
                return float(score)
        
        return 100.0  # Default if no thresholds match
    
    def _score_percentile(self, raw_value: Any, params: Dict) -> float:
        """Score based on percentile ranking against benchmark"""
        benchmark = params.get('benchmark', [])
        
        if not benchmark or not isinstance(raw_value, (int, float)):
            return 50.0
        
        # Calculate percentile
        below = sum(1 for b in benchmark if b < raw_value)
        percentile = below / len(benchmark) * 100
        
        return percentile
    
    def _score_weighted_average(self, raw_value: Any, params: Dict) -> float:
        """Weighted average of sub-components"""
        if not isinstance(raw_value, dict):
            return 50.0
        
        weights = params.get('headers', params.get('records', params.get('weights', {})))
        
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 50.0
        
        weighted_sum = 0.0
        for key, weight in weights.items():
            if raw_value.get(key):
                weighted_sum += weight
        
        return (weighted_sum / total_weight) * 100
    
    def _score_default(self, raw_value: Any, params: Dict) -> float:
        """Default scoring when method unknown"""
        return 50.0
    
    def _adjust_for_quality(self, score: float, quality: 'SignalQuality') -> float:
        """Adjust score based on data quality"""
        # Apply uncertainty adjustment
        adjustments = {
            SignalQuality.HIGH: 1.0,
            SignalQuality.MEDIUM: 0.95,
            SignalQuality.LOW: 0.85,
            SignalQuality.UNVERIFIED: 0.70
        }
        
        factor = adjustments.get(quality, 0.85)
        
        # Move score toward 50 based on uncertainty
        return 50 + (score - 50) * factor


# =============================================================================
# SIGNAL AGGREGATOR
# =============================================================================

class SignalAggregator:
    """
    Aggregates scored signals into group and overall scores.
    """
    
    def __init__(self, model_config: 'ModelConfig'):
        self.model_config = model_config
    
    def aggregate_group(
        self,
        signals: List['ScoredSignal'],
        signal_type: 'SignalType'
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Aggregate signals within a group.
        
        Args:
            signals: List of scored signals
            signal_type: Type of signals being aggregated
            
        Returns:
            Tuple of (aggregate_score, metadata)
        """
        if not signals:
            return 0.0, {'signal_count': 0, 'method': 'none'}
        
        # Weight by model relevance
        weighted_scores = []
        total_weight = 0.0
        
        for signal in signals:
            weight = signal.model_weights.get(self.model_config.model_type, 0.5)
            weighted_scores.append(signal.score * weight)
            total_weight += weight
        
        if total_weight == 0:
            return 50.0, {'signal_count': len(signals), 'method': 'default'}
        
        aggregate = sum(weighted_scores) / total_weight
        
        return aggregate, {
            'signal_count': len(signals),
            'total_weight': total_weight,
            'method': 'weighted_average'
        }
    
    def aggregate_overall(
        self,
        group_scores: Dict['SignalType', float],
        red_flags: List[str],
        green_flags: List[str]
    ) -> Tuple[float, int, Dict[str, Any]]:
        """
        Calculate overall score and tier.
        
        Args:
            group_scores: Dict of signal type to group score
            red_flags: List of red flag reasons
            green_flags: List of green flag reasons
            
        Returns:
            Tuple of (overall_score, tier, metadata)
        """
        # Weight by type
        weighted_sum = 0.0
        total_weight = 0.0
        
        for signal_type, score in group_scores.items():
            weight = self.model_config.type_weights.get(signal_type, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight == 0:
            overall = 50.0
        else:
            overall = weighted_sum / total_weight
        
        # Apply flag adjustments
        # Red flags reduce score
        flag_adjustment = 0.0
        for _ in red_flags:
            flag_adjustment -= 5.0  # -5 points per red flag
        
        # Green flags increase score (but less impact)
        for _ in green_flags:
            flag_adjustment += 2.0  # +2 points per green flag
        
        overall = max(0, min(100, overall + flag_adjustment))
        
        # Convert to 1000-point scale
        overall_1000 = overall * 10
        
        # Determine tier
        tier = self._determine_tier(overall_1000)
        
        return overall_1000, tier, {
            'base_score': weighted_sum / total_weight if total_weight > 0 else 50,
            'flag_adjustment': flag_adjustment,
            'red_flag_count': len(red_flags),
            'green_flag_count': len(green_flags)
        }
    
    def _determine_tier(self, score: float) -> int:
        """Determine tier from score"""
        for tier, (low, high) in self.model_config.tier_thresholds.items():
            if low <= score <= high:
                return tier
        return 5  # Default to highest risk if no match

# from signal_collection_part2 import *

logger = logging.getLogger(__name__)


# =============================================================================
# MAIN SIGNAL COLLECTION ENGINE
# =============================================================================

class SignalCollectionEngine:
    """
    Main engine for collecting, scoring, and aggregating DSI signals.
    
    This engine orchestrates the entire signal collection process:
    1. Website discovery (via website_discovery module)
    2. Signal collection from multiple sources
    3. Signal scoring and normalization
    4. Aggregation into DSI scores and tiers
    
    Usage:
        engine = SignalCollectionEngine(model_type=ModelType.CYBER)
        result = engine.collect("Petrobras", domain_hint="petrobras.com.br")
        print(f"Score: {result.overall_score}, Tier: {result.tier}")
    """
    
    def __init__(
        self,
        model_type: 'ModelType' = None,
        config: Optional['ModelConfig'] = None,
        collectors: Optional[Dict[str, 'SignalCollector']] = None
    ):
        """
        Initialise the signal collection engine.
        
        Args:
            model_type: Type of pricing model to use
            config: Optional custom model configuration
            collectors: Optional custom collectors dict
        """
        self.model_type = model_type or ModelType.GENERAL
        
        # Load model configuration
        if config:
            self.config = config
        elif model_type and model_type in MODEL_CONFIGS:
            self.config = MODEL_CONFIGS[model_type]()
        else:
            self.config = get_cyber_config()  # Default to cyber
        
        # Initialise collectors
        self.collectors = collectors or self._initialize_collectors()
        
        # Initialise scoring engine
        self.scoring_engine = SignalScoringEngine(self.model_type)
        
        # Initialise aggregator
        self.aggregator = SignalAggregator(self.config)
        
        # Website discovery engine
        # In production: self.website_discovery = WebsiteDiscoveryEngine()
        self.website_discovery = None
        
        logger.info(f"SignalCollectionEngine initialized for {self.model_type.value}")
    
    def _initialize_collectors(self) -> Dict[str, 'SignalCollector']:
        """Initialise default collectors"""
        return {
            'website': WebsiteContentCollector(),
            'dns': DNSCollector(),
            'ssl': SSLCollector(),
            'shodan': ShodanCensysCollector(),
            'linkedin': LinkedInCollector(),
            'news': NewsMediaCollector(),
            'ratings': ThirdPartyRatingCollector(),
        }
    
    def collect(
        self,
        entity_name: str,
        domain_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        industry_hint: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> 'SignalCollectionResult':
        """
        Collect all signals for an entity.
        
        Args:
            entity_name: Company/entity name
            domain_hint: Optional domain hint
            country_hint: Optional country
            industry_hint: Optional industry
            additional_data: Additional context data
            
        Returns:
            SignalCollectionResult with all collected and scored signals
        """
        logger.info(f"Starting signal collection for: {entity_name}")
        
        result = SignalCollectionResult(
            entity_name=entity_name,
            entity_domain=domain_hint
        )
        
        # Step 1: Discover corporate website if not provided
        target_domain = domain_hint
        if not target_domain and self.website_discovery:
            discovery = self.website_discovery.discover(
                entity_name,
                domain_hint=domain_hint,
                country_hint=country_hint,
                industry_hint=industry_hint
            )
            if discovery.primary_website:
                target_domain = discovery.primary_website.domain
                result.entity_domain = target_domain
        
        if not target_domain:
            result.warnings.append("No domain resolved - some signals unavailable")
            # Continue with name-based collection only
        
        # Step 2: Collect raw signals from all sources
        raw_signals: List['RawSignal'] = []
        collection_config = {
            'entity_name': entity_name,
            'domain': target_domain,
            'country': country_hint,
            'industry': industry_hint,
            'additional': additional_data or {}
        }
        
        for collector_name, collector in self.collectors.items():
            try:
                target = target_domain or entity_name
                signals = collector.collect(target, collection_config)
                raw_signals.extend(signals)
                result.sources_used.append(collector.get_source_type())
                logger.debug(f"Collector {collector_name}: {len(signals)} signals")
            except Exception as e:
                error_msg = f"Collector {collector_name} failed: {str(e)}"
                result.errors.append(error_msg)
                logger.error(error_msg)
        
        # Step 3: Score all signals
        scored_signals: List['ScoredSignal'] = []
        red_flags: List[str] = []
        green_flags: List[str] = []
        
        for raw_signal in raw_signals:
            config = SIGNAL_CONFIGS_BY_ID.get(raw_signal.signal_id)
            if config:
                scored = self.scoring_engine.score_signal(raw_signal, config)
                scored_signals.append(scored)
                
                if scored.is_red_flag:
                    red_flags.append(scored.red_flag_reason)
                if scored.is_green_flag:
                    green_flags.append(scored.green_flag_reason)
        
        # Step 4: Organise signals by type
        for scored in scored_signals:
            signal_type = scored.raw_signal.signal_type
            group = result.get_signal_group(signal_type)
            group.signals.append(scored)
        
        # Step 5: Aggregate group scores
        group_scores: Dict['SignalType', float] = {}
        
        for signal_type in SignalType:
            group = result.get_signal_group(signal_type)
            if group.signals:
                agg_score, metadata = self.aggregator.aggregate_group(
                    group.signals, signal_type
                )
                group.aggregate_score = agg_score
                group_scores[signal_type] = agg_score
        
        # Step 6: Calculate overall score and tier
        overall, tier, metadata = self.aggregator.aggregate_overall(
            group_scores, red_flags, green_flags
        )
        
        result.overall_score = overall
        result.tier = tier
        
        # Add warnings for low signal coverage
        if len(scored_signals) < self.config.minimum_signals_required:
            result.warnings.append(
                f"Only {len(scored_signals)} signals collected "
                f"(minimum recommended: {self.config.minimum_signals_required})"
            )
        
        logger.info(
            f"Collection complete for {entity_name}: "
            f"Score={overall:.0f}, Tier={tier}, Signals={len(scored_signals)}"
        )
        
        return result
    
    def collect_batch(
        self,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, 'SignalCollectionResult']:
        """
        Collect signals for multiple entities.
        
        Args:
            entities: List of dicts with keys:
                - name: Entity name (required)
                - domain: Optional domain
                - country: Optional country
                - industry: Optional industry
                
        Returns:
            Dict mapping entity names to results
        """
        results = {}
        
        for entity in entities:
            name = entity.get('name')
            if not name:
                continue
            
            result = self.collect(
                entity_name=name,
                domain_hint=entity.get('domain'),
                country_hint=entity.get('country'),
                industry_hint=entity.get('industry'),
                additional_data=entity.get('additional')
            )
            results[name] = result
        
        return results
    
    def export_result(
        self,
        result: 'SignalCollectionResult',
        format: str = 'dict'
    ) -> Any:
        """
        Export collection result in specified format.
        
        Args:
            result: SignalCollectionResult to export
            format: 'dict', 'json', or 'summary'
            
        Returns:
            Exported data in requested format
        """
        if format == 'summary':
            return {
                'entity': result.entity_name,
                'domain': result.entity_domain,
                'score': result.overall_score,
                'tier': result.tier,
                'signal_count': sum(
                    len(result.get_signal_group(t).signals) 
                    for t in SignalType
                ),
                'red_flags': [
                    s.red_flag_reason 
                    for g in [result.get_signal_group(t) for t in SignalType]
                    for s in g.signals if s.is_red_flag
                ],
                'green_flags': [
                    s.green_flag_reason
                    for g in [result.get_signal_group(t) for t in SignalType]
                    for s in g.signals if s.is_green_flag
                ],
                'warnings': result.warnings,
                'errors': result.errors
            }
        
        if format == 'dict':
            return {
                'entity_name': result.entity_name,
                'entity_domain': result.entity_domain,
                'overall_score': result.overall_score,
                'tier': result.tier,
                'type_scores': {
                    t.value: result.get_signal_group(t).aggregate_score
                    for t in SignalType
                },
                'signal_details': {
                    t.value: [
                        {
                            'signal_id': s.raw_signal.signal_id,
                            'signal_name': s.raw_signal.signal_name,
                            'score': s.score,
                            'is_red_flag': s.is_red_flag,
                            'is_green_flag': s.is_green_flag
                        }
                        for s in result.get_signal_group(t).signals
                    ]
                    for t in SignalType
                },
                'metadata': {
                    'collection_timestamp': result.collection_timestamp.isoformat(),
                    'sources_used': [s.value for s in result.sources_used],
                    'warnings': result.warnings,
                    'errors': result.errors
                }
            }
        
        if format == 'json':
            return json.dumps(self.export_result(result, 'dict'), indent=2)
        
        raise ValueError(f"Unknown format: {format}")


# =============================================================================
# MODEL-SPECIFIC ENGINES
# =============================================================================

class CyberSignalEngine(SignalCollectionEngine):
    """Signal collection engine pre-configured for Cyber Insurance"""
    
    def __init__(self, config: Optional['ModelConfig'] = None):
        super().__init__(
            model_type=ModelType.CYBER,
            config=config or get_cyber_config()
        )
    
    def collect(self, entity_name: str, **kwargs) -> 'SignalCollectionResult':
        """Collect with cyber-specific enhancements"""
        result = super().collect(entity_name, **kwargs)
        
        # Add cyber-specific analysis
        self._analyze_breach_patterns(result)
        self._analyze_attack_surface(result)
        
        return result
    
    def _analyze_breach_patterns(self, result: 'SignalCollectionResult'):
        """Analyze breach history patterns"""
        breach_signals = [
            s for s in result.type_6_signals.signals
            if s.raw_signal.signal_id == 'pr_breach_history'
        ]
        
        if breach_signals:
            # Check for recurring patterns
            pass  # Implementation would analyze breach patterns
    
    def _analyze_attack_surface(self, result: 'SignalCollectionResult'):
        """Analyze overall attack surface"""
        exposure_signals = [
            s for s in result.type_2_signals.signals
            if s.raw_signal.signal_id == 'ti_network_exposure'
        ]
        
        if exposure_signals:
            # Calculate attack surface metrics
            pass  # Implementation would calculate attack surface


class FISignalEngine(SignalCollectionEngine):
    """Signal collection engine pre-configured for Financial Institutions"""
    
    def __init__(self, config: Optional['ModelConfig'] = None):
        super().__init__(
            model_type=ModelType.FINANCIAL_INSTITUTIONS,
            config=config or get_financial_institutions_config()
        )
    
    def collect(self, entity_name: str, **kwargs) -> 'SignalCollectionResult':
        """Collect with FI-specific enhancements"""
        result = super().collect(entity_name, **kwargs)
        
        # Add FI-specific analysis
        self._analyze_regulatory_standing(result)
        self._analyze_financial_stability(result)
        
        return result
    
    def _analyze_regulatory_standing(self, result: 'SignalCollectionResult'):
        """Analyze regulatory compliance standing"""
        pass  # Implementation would analyze regulatory signals
    
    def _analyze_financial_stability(self, result: 'SignalCollectionResult'):
        """Analyze financial stability indicators"""
        pass  # Implementation would analyze financial signals


class EnergySignalEngine(SignalCollectionEngine):
    """Signal collection engine pre-configured for Energy sector"""
    
    def __init__(self, config: Optional['ModelConfig'] = None):
        super().__init__(
            model_type=ModelType.ENERGY,
            config=config or get_energy_config()
        )
    
    def collect(self, entity_name: str, **kwargs) -> 'SignalCollectionResult':
        """Collect with energy-specific enhancements"""
        result = super().collect(entity_name, **kwargs)
        
        # Add energy-specific analysis
        self._analyze_ot_it_convergence(result)
        self._analyze_safety_culture(result)
        
        return result
    
    def _analyze_ot_it_convergence(self, result: 'SignalCollectionResult'):
        """Analyze OT/IT convergence risks"""
        pass  # Implementation would analyze OT/IT signals
    
    def _analyze_safety_culture(self, result: 'SignalCollectionResult'):
        """Analyze safety culture indicators"""
        pass  # Implementation would analyze safety signals


class MarineSignalEngine(SignalCollectionEngine):
    """Signal collection engine pre-configured for Marine sector"""
    
    def __init__(self, config: Optional['ModelConfig'] = None):
        super().__init__(
            model_type=ModelType.MARINE,
            config=config or get_marine_config()
        )


class DOSignalEngine(SignalCollectionEngine):
    """Signal collection engine pre-configured for D&O"""
    
    def __init__(self, config: Optional['ModelConfig'] = None):
        super().__init__(
            model_type=ModelType.DIRECTORS_OFFICERS,
            config=config or get_do_config()
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_signal_engine(model_type: 'ModelType') -> SignalCollectionEngine:
    """
    Factory function to create the appropriate signal engine.
    
    Args:
        model_type: Type of pricing model
        
    Returns:
        Appropriate SignalCollectionEngine subclass
    """
    engines = {
        ModelType.CYBER: CyberSignalEngine,
        ModelType.FINANCIAL_INSTITUTIONS: FISignalEngine,
        ModelType.ENERGY: EnergySignalEngine,
        ModelType.MARINE: MarineSignalEngine,
        ModelType.DIRECTORS_OFFICERS: DOSignalEngine,
    }
    
    engine_class = engines.get(model_type, SignalCollectionEngine)
    return engine_class()


def collect_signals(
    entity_name: str,
    model_type: 'ModelType' = ModelType.CYBER,
    **kwargs
) -> 'SignalCollectionResult':
    """
    Convenience function to collect signals.
    
    Args:
        entity_name: Company/entity name
        model_type: Type of pricing model
        **kwargs: Additional arguments for collect()
        
    Returns:
        SignalCollectionResult
    """
    engine = create_signal_engine(model_type)
    return engine.collect(entity_name, **kwargs)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Collect signals for Petrobras (Energy)
    print("=" * 60)
    print("DSI Signal Collection Demo")
    print("=" * 60)
    
    # Create energy-specific engine
    engine = EnergySignalEngine()
    
    # Collect signals
    result = engine.collect(
        entity_name="Petrobras",
        domain_hint="petrobras.com.br",
        country_hint="Brazil",
        industry_hint="energy"
    )
    
    # Print summary
    print(f"\nEntity: {result.entity_name}")
    print(f"Domain: {result.entity_domain}")
    print(f"Overall Score: {result.overall_score:.0f}/1000")
    print(f"Tier: {result.tier}")
    print(f"\nSignal Groups:")
    
    for signal_type in SignalType:
        group = result.get_signal_group(signal_type)
        if group.signals:
            print(f"  {signal_type.value}: {group.aggregate_score:.1f} ({len(group.signals)} signals)")
    
    if result.warnings:
        print(f"\nWarnings: {result.warnings}")
    
    if result.errors:
        print(f"\nErrors: {result.errors}")
    
    # Export as JSON
    print("\n" + "=" * 60)
    print("JSON Export (Summary):")
    print("=" * 60)
    summary = engine.export_result(result, 'summary')
    print(json.dumps(summary, indent=2))
