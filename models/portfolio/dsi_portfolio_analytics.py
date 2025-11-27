"""
Digital Signal Intelligence (DSI) - Portfolio Management Module
================================================================

This module provides the unified interface for analysing and managing
complete portfolios of risks across multiple coverage lines. It serves
as the primary human interaction layer, consolidating all underlying
DSI functionality.

Key Capabilities:
1. Multi-line portfolio analysis (Cyber, FI, Energy, Marine, D&O, etc.)
2. Portfolio-level risk aggregation and concentration monitoring
3. Variance detection and anomaly alerting
4. Drill-down capability for detailed risk analysis
5. Error catching and data quality monitoring
6. Extensible architecture for new coverage lines

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Set, Union
from enum import Enum
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging
import json
import statistics
from collections import defaultdict
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class CoverageType(Enum):
    """Insurance coverage types - extensible for new lines"""
    # Currently implemented
    CYBER = "cyber"
    FINANCIAL_INSTITUTIONS = "financial_institutions"
    ENERGY = "energy"
    MARINE = "marine"
    DIRECTORS_OFFICERS = "directors_officers"
    
    # Future coverage lines (placeholders)
    CASUALTY = "casualty"
    PROPERTY = "property"
    PROFESSIONAL_INDEMNITY = "professional_indemnity"
    ENVIRONMENTAL = "environmental"
    POLITICAL_RISK = "political_risk"
    TRADE_CREDIT = "trade_credit"
    
    # Generic fallback
    GENERAL = "general"


class RiskStatus(Enum):
    """Status of a risk in the portfolio"""
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    REFERRED = "referred"
    DECLINED = "declined"
    EXPIRED = "expired"
    RENEWED = "renewed"
    CANCELLED = "cancelled"


class AlertSeverity(Enum):
    """Severity levels for portfolio alerts"""
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"            # Action required within 24 hours
    MEDIUM = "medium"        # Review within 1 week
    LOW = "low"              # Informational
    INFO = "info"            # FYI only


class AlertType(Enum):
    """Types of portfolio alerts"""
    # Concentration alerts
    CONCENTRATION_SECTOR = "concentration_sector"
    CONCENTRATION_GEOGRAPHY = "concentration_geography"
    CONCENTRATION_VENDOR = "concentration_vendor"
    CONCENTRATION_SINGLE_RISK = "concentration_single_risk"
    
    # Score alerts
    SCORE_DETERIORATION = "score_deterioration"
    SCORE_THRESHOLD_BREACH = "score_threshold_breach"
    TIER_MIGRATION = "tier_migration"
    
    # Data quality alerts
    DATA_QUALITY_LOW = "data_quality_low"
    SIGNAL_MISSING = "signal_missing"
    STALE_DATA = "stale_data"
    
    # Variance alerts
    VARIANCE_FROM_BENCHMARK = "variance_from_benchmark"
    VARIANCE_FROM_PEER = "variance_from_peer"
    OUTLIER_DETECTED = "outlier_detected"
    
    # Operational alerts
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    ERROR_DETECTED = "error_detected"
    SYSTEM_WARNING = "system_warning"


class AnalysisDepth(Enum):
    """Depth of analysis requested"""
    SUMMARY = "summary"          # High-level overview only
    STANDARD = "standard"        # Normal detail level
    DETAILED = "detailed"        # Full signal-level detail
    DIAGNOSTIC = "diagnostic"    # Include debug information


class TimeFrame(Enum):
    """Time frames for analysis"""
    POINT_IN_TIME = "point_in_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class RiskIdentifier:
    """Unique identifier for a risk"""
    risk_id: str
    entity_name: str
    coverage_type: CoverageType
    policy_reference: Optional[str] = None
    inception_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


@dataclass
class RiskMetadata:
    """Metadata about a risk"""
    # Classification
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    geography: Optional[str] = None
    region: Optional[str] = None
    size_band: Optional[str] = None
    
    # Financial
    premium: Optional[float] = None
    limit: Optional[float] = None
    retention: Optional[float] = None
    currency: str = "USD"
    
    # Underwriting
    underwriter: Optional[str] = None
    broker: Optional[str] = None
    lead_follow: Optional[str] = None  # "lead", "follow"
    share_percentage: Optional[float] = None
    
    # Custom attributes
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DSIAssessment:
    """DSI assessment results for a risk"""
    # Scores
    overall_score: float  # 0-1000
    tier: int  # 1-5
    
    # Type scores
    type_scores: Dict[str, float] = field(default_factory=dict)
    
    # Signals summary
    signal_count: int = 0
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    
    # Quality metrics
    data_quality_score: float = 0.0  # 0-100
    signal_coverage: float = 0.0  # 0-100
    confidence_level: str = "medium"
    
    # Recommendations
    recommended_action: str = ""
    recommended_premium_adjustment: Optional[float] = None
    manual_review_required: bool = False
    review_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    assessment_timestamp: datetime = field(default_factory=datetime.now)
    assessment_version: str = "2.0"
    sources_used: List[str] = field(default_factory=list)


@dataclass
class HistoricalAssessment:
    """Historical assessment for tracking changes"""
    assessment_date: datetime
    overall_score: float
    tier: int
    key_changes: List[str] = field(default_factory=list)


@dataclass
class PortfolioRisk:
    """Complete risk record in the portfolio"""
    # Identity
    identifier: RiskIdentifier
    metadata: RiskMetadata
    
    # DSI Assessment
    current_assessment: Optional[DSIAssessment] = None
    assessment_history: List[HistoricalAssessment] = field(default_factory=list)
    
    # Status
    status: RiskStatus = RiskStatus.ACTIVE
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Domain/Website
    primary_domain: Optional[str] = None
    website_confidence: Optional[str] = None
    
    # Notes and overrides
    underwriter_notes: List[str] = field(default_factory=list)
    manual_overrides: Dict[str, Any] = field(default_factory=dict)
    
    # Alerts
    active_alerts: List['PortfolioAlert'] = field(default_factory=list)


@dataclass
class PortfolioAlert:
    """Alert raised by the portfolio monitoring system"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    
    # Context
    risk_id: Optional[str] = None  # None for portfolio-level alerts
    coverage_type: Optional[CoverageType] = None
    
    # Details
    title: str = ""
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Thresholds
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    
    # Status
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class ConcentrationMetric:
    """Concentration measurement"""
    dimension: str  # "sector", "geography", "vendor", etc.
    value: str  # The specific sector/geography/vendor
    exposure: float  # Total exposure (premium or limit)
    percentage: float  # Percentage of portfolio
    risk_count: int
    average_score: float
    threshold: float  # Concentration limit
    is_breached: bool


@dataclass
class PortfolioMetrics:
    """Aggregated portfolio metrics"""
    # Totals
    total_risks: int = 0
    total_premium: float = 0.0
    total_limit: float = 0.0
    
    # By coverage type
    risks_by_coverage: Dict[str, int] = field(default_factory=dict)
    premium_by_coverage: Dict[str, float] = field(default_factory=dict)
    
    # By tier
    risks_by_tier: Dict[int, int] = field(default_factory=dict)
    premium_by_tier: Dict[int, float] = field(default_factory=dict)
    
    # Score distribution
    average_score: float = 0.0
    median_score: float = 0.0
    score_std_dev: float = 0.0
    score_percentiles: Dict[int, float] = field(default_factory=dict)
    
    # Quality metrics
    average_data_quality: float = 0.0
    risks_requiring_review: int = 0
    risks_with_red_flags: int = 0
    
    # Concentration metrics
    concentrations: List[ConcentrationMetric] = field(default_factory=list)
    
    # Alerts summary
    active_alerts_by_severity: Dict[str, int] = field(default_factory=dict)
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class VarianceAnalysis:
    """Analysis of variance from benchmarks or expectations"""
    metric_name: str
    expected_value: float
    actual_value: float
    variance: float
    variance_percentage: float
    is_significant: bool
    explanation: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result of a portfolio query"""
    query_id: str
    query_description: str
    
    # Results
    matching_risks: List[PortfolioRisk] = field(default_factory=list)
    result_count: int = 0
    
    # Aggregations
    aggregations: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    execution_time_ms: float = 0.0
    query_timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ConcentrationLimits:
    """Concentration limits for the portfolio"""
    # By dimension
    max_single_risk_percentage: float = 5.0
    max_sector_percentage: float = 25.0
    max_geography_percentage: float = 30.0
    max_vendor_percentage: float = 10.0
    
    # By tier
    max_tier_4_percentage: float = 15.0
    max_tier_5_percentage: float = 5.0
    
    # Custom limits
    custom_limits: Dict[str, float] = field(default_factory=dict)


@dataclass
class AlertThresholds:
    """Thresholds for generating alerts"""
    # Score deterioration
    score_deterioration_threshold: float = 50.0  # Points drop
    score_deterioration_period_days: int = 90
    
    # Tier migration
    tier_downgrade_alert: bool = True
    
    # Data quality
    min_data_quality_score: float = 60.0
    max_stale_days: int = 180
    min_signal_coverage: float = 50.0
    
    # Variance
    variance_threshold_percentage: float = 20.0


@dataclass 
class PortfolioConfig:
    """Configuration for the portfolio manager"""
    # Limits
    concentration_limits: ConcentrationLimits = field(default_factory=ConcentrationLimits)
    alert_thresholds: AlertThresholds = field(default_factory=AlertThresholds)
    
    # Coverage types enabled
    enabled_coverage_types: List[CoverageType] = field(default_factory=lambda: [
        CoverageType.CYBER,
        CoverageType.FINANCIAL_INSTITUTIONS,
        CoverageType.ENERGY,
        CoverageType.MARINE,
        CoverageType.DIRECTORS_OFFICERS,
    ])
    
    # Tier definitions (consistent across coverage types)
    tier_thresholds: Dict[int, Tuple[float, float]] = field(default_factory=lambda: {
        1: (800, 1000),
        2: (650, 799),
        3: (500, 649),
        4: (350, 499),
        5: (0, 349)
    })
    
    # Benchmarks
    industry_benchmarks: Dict[str, Dict[str, float]] = field(default_factory=dict)


# =============================================================================
# COVERAGE LINE REGISTRY
# =============================================================================

class CoverageLineRegistry:
    """
    Registry for coverage line configurations.
    Allows new coverage types to be registered dynamically.
    """
    
    _registry: Dict[CoverageType, Dict[str, Any]] = {}
    
    @classmethod
    def register(
        cls,
        coverage_type: CoverageType,
        name: str,
        signal_weights: Dict[str, float],
        sector_adjustments: Optional[Dict[str, float]] = None,
        custom_signals: Optional[List[str]] = None,
        engine_class: Optional[type] = None
    ):
        """
        Register a new coverage line configuration.
        
        Args:
            coverage_type: The coverage type enum value
            name: Human-readable name
            signal_weights: Weights for signal types
            sector_adjustments: Optional sector-specific adjustments
            custom_signals: Optional list of custom signal IDs
            engine_class: Optional custom signal engine class
        """
        cls._registry[coverage_type] = {
            'name': name,
            'signal_weights': signal_weights,
            'sector_adjustments': sector_adjustments or {},
            'custom_signals': custom_signals or [],
            'engine_class': engine_class,
            'registered_at': datetime.now()
        }
        logger.info(f"Registered coverage line: {name} ({coverage_type.value})")
    
    @classmethod
    def get(cls, coverage_type: CoverageType) -> Optional[Dict[str, Any]]:
        """Get configuration for a coverage type"""
        return cls._registry.get(coverage_type)
    
    @classmethod
    def list_registered(cls) -> List[CoverageType]:
        """List all registered coverage types"""
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, coverage_type: CoverageType) -> bool:
        """Check if a coverage type is registered"""
        return coverage_type in cls._registry


# Register default coverage lines
def _register_default_coverage_lines():
    """Register the default DSI coverage lines"""
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.CYBER,
        name="Cyber Insurance",
        signal_weights={
            'network_authority': 0.15,
            'technical_infrastructure': 0.25,
            'asset_telemetry': 0.15,
            'structured_data': 0.10,
            'corporate_footprint': 0.20,
            'public_records': 0.15,
        },
        sector_adjustments={
            'healthcare': -0.10,
            'financial_services': -0.05,
            'retail': -0.05,
            'energy': -0.08,
        }
    )
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.FINANCIAL_INSTITUTIONS,
        name="Financial Institutions",
        signal_weights={
            'network_authority': 0.20,
            'technical_infrastructure': 0.15,
            'asset_telemetry': 0.15,
            'structured_data': 0.20,
            'corporate_footprint': 0.15,
            'public_records': 0.15,
        },
        sector_adjustments={
            'banking': 0.0,
            'asset_management': 0.05,
            'fintech': -0.05,
            'crypto': -0.15,
        }
    )
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.ENERGY,
        name="Energy",
        signal_weights={
            'network_authority': 0.15,
            'technical_infrastructure': 0.20,
            'asset_telemetry': 0.15,
            'structured_data': 0.15,
            'corporate_footprint': 0.20,
            'public_records': 0.15,
        },
        sector_adjustments={
            'upstream': -0.05,
            'midstream': -0.08,
            'downstream': -0.03,
            'renewables': 0.05,
        }
    )
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.MARINE,
        name="Marine",
        signal_weights={
            'network_authority': 0.20,
            'technical_infrastructure': 0.15,
            'asset_telemetry': 0.15,
            'structured_data': 0.20,
            'corporate_footprint': 0.15,
            'public_records': 0.15,
        }
    )
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.DIRECTORS_OFFICERS,
        name="Directors & Officers",
        signal_weights={
            'network_authority': 0.20,
            'technical_infrastructure': 0.05,
            'asset_telemetry': 0.10,
            'structured_data': 0.25,
            'corporate_footprint': 0.20,
            'public_records': 0.20,
        }
    )
    
    # Placeholder for future coverage lines
    CoverageLineRegistry.register(
        coverage_type=CoverageType.CASUALTY,
        name="Casualty (Placeholder)",
        signal_weights={
            'network_authority': 0.15,
            'technical_infrastructure': 0.10,
            'asset_telemetry': 0.15,
            'structured_data': 0.20,
            'corporate_footprint': 0.20,
            'public_records': 0.20,
        }
    )
    
    CoverageLineRegistry.register(
        coverage_type=CoverageType.PROPERTY,
        name="Property (Placeholder)",
        signal_weights={
            'network_authority': 0.15,
            'technical_infrastructure': 0.10,
            'asset_telemetry': 0.20,
            'structured_data': 0.20,
            'corporate_footprint': 0.15,
            'public_records': 0.20,
        }
    )

# Initialize default registrations
_register_default_coverage_lines()

# Part 2: Portfolio Manager Core
# In production, import from part 1
# from portfolio_management_part1 import *

logger = logging.getLogger(__name__)


# =============================================================================
# PORTFOLIO MANAGER
# =============================================================================

class PortfolioManager:
    """
    Main portfolio management class.
    
    This is the primary interface for human users to interact with the
    DSI system. It provides portfolio-level views, drill-down capabilities,
    alerting, and analysis across all coverage lines.
    
    Usage:
        manager = PortfolioManager()
        manager.add_risk(risk)
        metrics = manager.calculate_metrics()
        alerts = manager.get_active_alerts()
    """
    
    def __init__(self, config: Optional[PortfolioConfig] = None):
        """
        Initialize the portfolio manager.
        
        Args:
            config: Optional portfolio configuration
        """
        self.config = config or PortfolioConfig()
        
        # Risk storage
        self._risks: Dict[str, PortfolioRisk] = {}
        
        # Indices for fast lookup
        self._by_coverage: Dict[CoverageType, Set[str]] = defaultdict(set)
        self._by_sector: Dict[str, Set[str]] = defaultdict(set)
        self._by_geography: Dict[str, Set[str]] = defaultdict(set)
        self._by_tier: Dict[int, Set[str]] = defaultdict(set)
        self._by_status: Dict[RiskStatus, Set[str]] = defaultdict(set)
        
        # Alerts
        self._alerts: Dict[str, PortfolioAlert] = {}
        
        # Metrics cache
        self._metrics_cache: Optional[PortfolioMetrics] = None
        self._metrics_cache_time: Optional[datetime] = None
        self._metrics_cache_ttl = timedelta(minutes=5)
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        
        logger.info("PortfolioManager initialized")
    
    # =========================================================================
    # RISK MANAGEMENT
    # =========================================================================
    
    def add_risk(
        self,
        entity_name: str,
        coverage_type: CoverageType,
        metadata: Optional[RiskMetadata] = None,
        assessment: Optional[DSIAssessment] = None,
        risk_id: Optional[str] = None,
        **kwargs
    ) -> PortfolioRisk:
        """
        Add a new risk to the portfolio.
        
        Args:
            entity_name: Name of the insured entity
            coverage_type: Type of coverage
            metadata: Risk metadata (sector, premium, etc.)
            assessment: DSI assessment if already performed
            risk_id: Optional custom risk ID
            **kwargs: Additional risk attributes
            
        Returns:
            The created PortfolioRisk
        """
        # Generate ID if not provided
        risk_id = risk_id or str(uuid.uuid4())[:12]
        
        # Check for duplicates
        if risk_id in self._risks:
            raise ValueError(f"Risk ID {risk_id} already exists")
        
        # Create identifier
        identifier = RiskIdentifier(
            risk_id=risk_id,
            entity_name=entity_name,
            coverage_type=coverage_type,
            policy_reference=kwargs.get('policy_reference'),
            inception_date=kwargs.get('inception_date'),
            expiry_date=kwargs.get('expiry_date')
        )
        
        # Create risk
        risk = PortfolioRisk(
            identifier=identifier,
            metadata=metadata or RiskMetadata(),
            current_assessment=assessment,
            status=kwargs.get('status', RiskStatus.ACTIVE),
            primary_domain=kwargs.get('primary_domain'),
            website_confidence=kwargs.get('website_confidence')
        )
        
        # Store and index
        self._risks[risk_id] = risk
        self._index_risk(risk)
        
        # Invalidate cache
        self._invalidate_cache()
        
        # Audit
        self._log_action('add_risk', risk_id, {'entity': entity_name, 'coverage': coverage_type.value})
        
        # Check for alerts on new risk
        self._check_risk_alerts(risk)
        
        logger.info(f"Added risk: {entity_name} ({coverage_type.value}) - ID: {risk_id}")
        return risk
    
    def update_risk(
        self,
        risk_id: str,
        updates: Dict[str, Any]
    ) -> PortfolioRisk:
        """
        Update an existing risk.
        
        Args:
            risk_id: ID of risk to update
            updates: Dict of fields to update
            
        Returns:
            Updated PortfolioRisk
        """
        if risk_id not in self._risks:
            raise ValueError(f"Risk ID {risk_id} not found")
        
        risk = self._risks[risk_id]
        old_values = {}
        
        # Track historical assessment if score changing
        if 'assessment' in updates and risk.current_assessment:
            historical = HistoricalAssessment(
                assessment_date=risk.current_assessment.assessment_timestamp,
                overall_score=risk.current_assessment.overall_score,
                tier=risk.current_assessment.tier
            )
            risk.assessment_history.append(historical)
        
        # Apply updates
        for key, value in updates.items():
            if key == 'assessment':
                old_values['assessment'] = risk.current_assessment
                risk.current_assessment = value
            elif key == 'metadata':
                old_values['metadata'] = risk.metadata
                risk.metadata = value
            elif key == 'status':
                old_values['status'] = risk.status
                risk.status = value
            elif hasattr(risk, key):
                old_values[key] = getattr(risk, key)
                setattr(risk, key, value)
        
        risk.last_updated = datetime.now()
        
        # Re-index
        self._unindex_risk(risk)
        self._index_risk(risk)
        
        # Invalidate cache
        self._invalidate_cache()
        
        # Audit
        self._log_action('update_risk', risk_id, {'updates': list(updates.keys())})
        
        # Check for alerts
        self._check_risk_alerts(risk)
        self._check_score_deterioration(risk, old_values.get('assessment'))
        
        return risk
    
    def remove_risk(self, risk_id: str) -> bool:
        """
        Remove a risk from the portfolio.
        
        Args:
            risk_id: ID of risk to remove
            
        Returns:
            True if removed, False if not found
        """
        if risk_id not in self._risks:
            return False
        
        risk = self._risks[risk_id]
        
        # Remove from indices
        self._unindex_risk(risk)
        
        # Remove from storage
        del self._risks[risk_id]
        
        # Invalidate cache
        self._invalidate_cache()
        
        # Audit
        self._log_action('remove_risk', risk_id, {'entity': risk.identifier.entity_name})
        
        logger.info(f"Removed risk: {risk_id}")
        return True
    
    def get_risk(self, risk_id: str) -> Optional[PortfolioRisk]:
        """Get a risk by ID"""
        return self._risks.get(risk_id)
    
    def get_risks(
        self,
        coverage_type: Optional[CoverageType] = None,
        sector: Optional[str] = None,
        geography: Optional[str] = None,
        tier: Optional[int] = None,
        status: Optional[RiskStatus] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[PortfolioRisk]:
        """
        Get risks matching criteria.
        
        Args:
            coverage_type: Filter by coverage type
            sector: Filter by sector
            geography: Filter by geography
            tier: Filter by tier
            status: Filter by status
            min_score: Minimum DSI score
            max_score: Maximum DSI score
            
        Returns:
            List of matching PortfolioRisk objects
        """
        # Start with all risks or filtered set
        if coverage_type:
            candidate_ids = self._by_coverage.get(coverage_type, set())
        else:
            candidate_ids = set(self._risks.keys())
        
        # Apply additional filters
        if sector:
            candidate_ids &= self._by_sector.get(sector, set())
        if geography:
            candidate_ids &= self._by_geography.get(geography, set())
        if tier:
            candidate_ids &= self._by_tier.get(tier, set())
        if status:
            candidate_ids &= self._by_status.get(status, set())
        
        # Get risk objects
        risks = [self._risks[rid] for rid in candidate_ids]
        
        # Apply score filters
        if min_score is not None:
            risks = [r for r in risks if r.current_assessment and r.current_assessment.overall_score >= min_score]
        if max_score is not None:
            risks = [r for r in risks if r.current_assessment and r.current_assessment.overall_score <= max_score]
        
        return risks
    
    # =========================================================================
    # INDEXING
    # =========================================================================
    
    def _index_risk(self, risk: PortfolioRisk):
        """Add risk to lookup indices"""
        rid = risk.identifier.risk_id
        
        # Coverage type
        self._by_coverage[risk.identifier.coverage_type].add(rid)
        
        # Sector
        if risk.metadata.sector:
            self._by_sector[risk.metadata.sector].add(rid)
        
        # Geography
        if risk.metadata.geography:
            self._by_geography[risk.metadata.geography].add(rid)
        
        # Tier
        if risk.current_assessment:
            self._by_tier[risk.current_assessment.tier].add(rid)
        
        # Status
        self._by_status[risk.status].add(rid)
    
    def _unindex_risk(self, risk: PortfolioRisk):
        """Remove risk from lookup indices"""
        rid = risk.identifier.risk_id
        
        # Remove from all indices
        self._by_coverage[risk.identifier.coverage_type].discard(rid)
        
        if risk.metadata.sector:
            self._by_sector[risk.metadata.sector].discard(rid)
        
        if risk.metadata.geography:
            self._by_geography[risk.metadata.geography].discard(rid)
        
        if risk.current_assessment:
            self._by_tier[risk.current_assessment.tier].discard(rid)
        
        self._by_status[risk.status].discard(rid)
    
    # =========================================================================
    # METRICS CALCULATION
    # =========================================================================
    
    def calculate_metrics(
        self,
        force_refresh: bool = False
    ) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics.
        
        Args:
            force_refresh: Force recalculation even if cached
            
        Returns:
            PortfolioMetrics object
        """
        # Check cache
        if not force_refresh and self._metrics_cache:
            if datetime.now() - self._metrics_cache_time < self._metrics_cache_ttl:
                return self._metrics_cache
        
        metrics = PortfolioMetrics()
        
        # Get all active risks
        active_risks = [r for r in self._risks.values() if r.status == RiskStatus.ACTIVE]
        
        if not active_risks:
            self._metrics_cache = metrics
            self._metrics_cache_time = datetime.now()
            return metrics
        
        # Basic counts
        metrics.total_risks = len(active_risks)
        metrics.total_premium = sum(r.metadata.premium or 0 for r in active_risks)
        metrics.total_limit = sum(r.metadata.limit or 0 for r in active_risks)
        
        # By coverage type
        for coverage in CoverageType:
            risks = [r for r in active_risks if r.identifier.coverage_type == coverage]
            if risks:
                metrics.risks_by_coverage[coverage.value] = len(risks)
                metrics.premium_by_coverage[coverage.value] = sum(r.metadata.premium or 0 for r in risks)
        
        # By tier
        for tier in range(1, 6):
            risks = [r for r in active_risks if r.current_assessment and r.current_assessment.tier == tier]
            if risks:
                metrics.risks_by_tier[tier] = len(risks)
                metrics.premium_by_tier[tier] = sum(r.metadata.premium or 0 for r in risks)
        
        # Score statistics
        scores = [r.current_assessment.overall_score for r in active_risks if r.current_assessment]
        if scores:
            metrics.average_score = statistics.mean(scores)
            metrics.median_score = statistics.median(scores)
            metrics.score_std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            
            # Percentiles
            sorted_scores = sorted(scores)
            n = len(sorted_scores)
            for p in [10, 25, 50, 75, 90]:
                idx = int(n * p / 100)
                metrics.score_percentiles[p] = sorted_scores[min(idx, n-1)]
        
        # Quality metrics
        quality_scores = [r.current_assessment.data_quality_score for r in active_risks if r.current_assessment]
        if quality_scores:
            metrics.average_data_quality = statistics.mean(quality_scores)
        
        metrics.risks_requiring_review = len([
            r for r in active_risks 
            if r.current_assessment and r.current_assessment.manual_review_required
        ])
        
        metrics.risks_with_red_flags = len([
            r for r in active_risks 
            if r.current_assessment and r.current_assessment.red_flags
        ])
        
        # Concentration metrics
        metrics.concentrations = self._calculate_concentrations(active_risks)
        
        # Alert summary
        for severity in AlertSeverity:
            count = len([a for a in self._alerts.values() if a.severity == severity and not a.is_resolved])
            if count > 0:
                metrics.active_alerts_by_severity[severity.value] = count
        
        metrics.calculated_at = datetime.now()
        
        # Cache
        self._metrics_cache = metrics
        self._metrics_cache_time = datetime.now()
        
        return metrics
    
    def _calculate_concentrations(
        self, 
        risks: List[PortfolioRisk]
    ) -> List[ConcentrationMetric]:
        """Calculate concentration metrics"""
        concentrations = []
        total_premium = sum(r.metadata.premium or 0 for r in risks)
        
        if total_premium == 0:
            return concentrations
        
        # Sector concentration
        sector_exposure = defaultdict(lambda: {'premium': 0, 'count': 0, 'scores': []})
        for risk in risks:
            sector = risk.metadata.sector or 'Unknown'
            sector_exposure[sector]['premium'] += risk.metadata.premium or 0
            sector_exposure[sector]['count'] += 1
            if risk.current_assessment:
                sector_exposure[sector]['scores'].append(risk.current_assessment.overall_score)
        
        for sector, data in sector_exposure.items():
            pct = (data['premium'] / total_premium) * 100 if total_premium > 0 else 0
            avg_score = statistics.mean(data['scores']) if data['scores'] else 0
            threshold = self.config.concentration_limits.max_sector_percentage
            
            concentrations.append(ConcentrationMetric(
                dimension='sector',
                value=sector,
                exposure=data['premium'],
                percentage=pct,
                risk_count=data['count'],
                average_score=avg_score,
                threshold=threshold,
                is_breached=pct > threshold
            ))
        
        # Geography concentration
        geo_exposure = defaultdict(lambda: {'premium': 0, 'count': 0, 'scores': []})
        for risk in risks:
            geo = risk.metadata.geography or 'Unknown'
            geo_exposure[geo]['premium'] += risk.metadata.premium or 0
            geo_exposure[geo]['count'] += 1
            if risk.current_assessment:
                geo_exposure[geo]['scores'].append(risk.current_assessment.overall_score)
        
        for geo, data in geo_exposure.items():
            pct = (data['premium'] / total_premium) * 100 if total_premium > 0 else 0
            avg_score = statistics.mean(data['scores']) if data['scores'] else 0
            threshold = self.config.concentration_limits.max_geography_percentage
            
            concentrations.append(ConcentrationMetric(
                dimension='geography',
                value=geo,
                exposure=data['premium'],
                percentage=pct,
                risk_count=data['count'],
                average_score=avg_score,
                threshold=threshold,
                is_breached=pct > threshold
            ))
        
        # Single risk concentration
        for risk in risks:
            if risk.metadata.premium:
                pct = (risk.metadata.premium / total_premium) * 100
                threshold = self.config.concentration_limits.max_single_risk_percentage
                if pct > threshold * 0.8:  # Alert at 80% of threshold
                    concentrations.append(ConcentrationMetric(
                        dimension='single_risk',
                        value=risk.identifier.entity_name,
                        exposure=risk.metadata.premium,
                        percentage=pct,
                        risk_count=1,
                        average_score=risk.current_assessment.overall_score if risk.current_assessment else 0,
                        threshold=threshold,
                        is_breached=pct > threshold
                    ))
        
        return concentrations
    
    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================
    
    def _invalidate_cache(self):
        """Invalidate metrics cache"""
        self._metrics_cache = None
        self._metrics_cache_time = None
    
    # =========================================================================
    # AUDIT LOGGING
    # =========================================================================
    
    def _log_action(self, action: str, risk_id: Optional[str], details: Dict[str, Any]):
        """Log an action for audit purposes"""
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'risk_id': risk_id,
            'details': details
        })
        
        # Keep last 10000 entries
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-10000:]
    
    def get_audit_log(
        self,
        since: Optional[datetime] = None,
        action_type: Optional[str] = None,
        risk_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log entries matching criteria"""
        entries = self._audit_log
        
        if since:
            entries = [e for e in entries if datetime.fromisoformat(e['timestamp']) >= since]
        if action_type:
            entries = [e for e in entries if e['action'] == action_type]
        if risk_id:
            entries = [e for e in entries if e['risk_id'] == risk_id]
        
        return entries

# Part 3: Alerting, Analysis, and Queries

logger = logging.getLogger(__name__)


# =============================================================================
# ALERTING SYSTEM (Extension to PortfolioManager)
# =============================================================================

class AlertingMixin:
    """Mixin class providing alerting functionality"""
    
    def _check_risk_alerts(self, risk: 'PortfolioRisk'):
        """Check and generate alerts for a single risk"""
        alerts_to_create = []
        
        if not risk.current_assessment:
            # No assessment - data quality alert
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.DATA_QUALITY_LOW,
                severity=AlertSeverity.MEDIUM,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"No DSI assessment for {risk.identifier.entity_name}",
                description="Risk has no DSI assessment. Signal collection required.",
                details={'entity': risk.identifier.entity_name}
            ))
            return
        
        assessment = risk.current_assessment
        
        # Check for red flags
        if assessment.red_flags:
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.SCORE_THRESHOLD_BREACH,
                severity=AlertSeverity.HIGH if len(assessment.red_flags) > 2 else AlertSeverity.MEDIUM,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"Red flags detected for {risk.identifier.entity_name}",
                description=f"{len(assessment.red_flags)} red flag(s) identified",
                details={'red_flags': assessment.red_flags}
            ))
        
        # Check for Tier 4/5 risks
        if assessment.tier >= 4:
            severity = AlertSeverity.HIGH if assessment.tier == 5 else AlertSeverity.MEDIUM
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.SCORE_THRESHOLD_BREACH,
                severity=severity,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"High-risk tier for {risk.identifier.entity_name}",
                description=f"Risk classified as Tier {assessment.tier} (score: {assessment.overall_score:.0f})",
                details={'score': assessment.overall_score, 'tier': assessment.tier}
            ))
        
        # Check data quality
        if assessment.data_quality_score < self.config.alert_thresholds.min_data_quality_score:
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.DATA_QUALITY_LOW,
                severity=AlertSeverity.LOW,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"Low data quality for {risk.identifier.entity_name}",
                description=f"Data quality score ({assessment.data_quality_score:.0f}) below threshold",
                details={'quality_score': assessment.data_quality_score}
            ))
        
        # Check signal coverage
        if assessment.signal_coverage < self.config.alert_thresholds.min_signal_coverage:
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.SIGNAL_MISSING,
                severity=AlertSeverity.LOW,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"Low signal coverage for {risk.identifier.entity_name}",
                description=f"Only {assessment.signal_coverage:.0f}% of expected signals collected",
                details={'coverage': assessment.signal_coverage}
            ))
        
        # Check if manual review required
        if assessment.manual_review_required:
            alerts_to_create.append(self._create_alert(
                alert_type=AlertType.MANUAL_REVIEW_REQUIRED,
                severity=AlertSeverity.MEDIUM,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"Manual review required for {risk.identifier.entity_name}",
                description=f"Review reasons: {', '.join(assessment.review_reasons)}",
                details={'reasons': assessment.review_reasons}
            ))
        
        # Add alerts
        for alert in alerts_to_create:
            self._alerts[alert.alert_id] = alert
            risk.active_alerts.append(alert)
    
    def _check_score_deterioration(
        self, 
        risk: 'PortfolioRisk',
        previous_assessment: Optional['DSIAssessment']
    ):
        """Check for significant score deterioration"""
        if not previous_assessment or not risk.current_assessment:
            return
        
        score_change = risk.current_assessment.overall_score - previous_assessment.overall_score
        
        # Check for significant deterioration
        if score_change < -self.config.alert_thresholds.score_deterioration_threshold:
            alert = self._create_alert(
                alert_type=AlertType.SCORE_DETERIORATION,
                severity=AlertSeverity.HIGH,
                risk_id=risk.identifier.risk_id,
                coverage_type=risk.identifier.coverage_type,
                title=f"Score deterioration for {risk.identifier.entity_name}",
                description=f"Score dropped by {abs(score_change):.0f} points",
                details={
                    'previous_score': previous_assessment.overall_score,
                    'current_score': risk.current_assessment.overall_score,
                    'change': score_change
                }
            )
            self._alerts[alert.alert_id] = alert
            risk.active_alerts.append(alert)
        
        # Check for tier migration
        if self.config.alert_thresholds.tier_downgrade_alert:
            if risk.current_assessment.tier > previous_assessment.tier:
                alert = self._create_alert(
                    alert_type=AlertType.TIER_MIGRATION,
                    severity=AlertSeverity.MEDIUM,
                    risk_id=risk.identifier.risk_id,
                    coverage_type=risk.identifier.coverage_type,
                    title=f"Tier downgrade for {risk.identifier.entity_name}",
                    description=f"Risk migrated from Tier {previous_assessment.tier} to Tier {risk.current_assessment.tier}",
                    details={
                        'previous_tier': previous_assessment.tier,
                        'current_tier': risk.current_assessment.tier
                    }
                )
                self._alerts[alert.alert_id] = alert
                risk.active_alerts.append(alert)
    
    def check_concentration_alerts(self):
        """Check and generate concentration-related alerts"""
        metrics = self.calculate_metrics()
        
        for conc in metrics.concentrations:
            if conc.is_breached:
                severity = AlertSeverity.HIGH if conc.percentage > conc.threshold * 1.5 else AlertSeverity.MEDIUM
                
                alert_type_map = {
                    'sector': AlertType.CONCENTRATION_SECTOR,
                    'geography': AlertType.CONCENTRATION_GEOGRAPHY,
                    'vendor': AlertType.CONCENTRATION_VENDOR,
                    'single_risk': AlertType.CONCENTRATION_SINGLE_RISK
                }
                
                alert = self._create_alert(
                    alert_type=alert_type_map.get(conc.dimension, AlertType.CONCENTRATION_SECTOR),
                    severity=severity,
                    title=f"Concentration limit breached: {conc.dimension}",
                    description=f"{conc.value}: {conc.percentage:.1f}% (limit: {conc.threshold:.1f}%)",
                    details={
                        'dimension': conc.dimension,
                        'value': conc.value,
                        'percentage': conc.percentage,
                        'threshold': conc.threshold,
                        'exposure': conc.exposure
                    },
                    threshold_value=conc.threshold,
                    actual_value=conc.percentage
                )
                self._alerts[alert.alert_id] = alert
    
    def _create_alert(
        self,
        alert_type: 'AlertType',
        severity: 'AlertSeverity',
        title: str,
        description: str,
        risk_id: Optional[str] = None,
        coverage_type: Optional['CoverageType'] = None,
        details: Optional[Dict] = None,
        threshold_value: Optional[float] = None,
        actual_value: Optional[float] = None
    ) -> 'PortfolioAlert':
        """Create a new alert"""
        return PortfolioAlert(
            alert_id=str(uuid.uuid4())[:12],
            alert_type=alert_type,
            severity=severity,
            risk_id=risk_id,
            coverage_type=coverage_type,
            title=title,
            description=description,
            details=details or {},
            threshold_value=threshold_value,
            actual_value=actual_value
        )
    
    def get_active_alerts(
        self,
        severity: Optional['AlertSeverity'] = None,
        alert_type: Optional['AlertType'] = None,
        coverage_type: Optional['CoverageType'] = None
    ) -> List['PortfolioAlert']:
        """Get active (unresolved) alerts matching criteria"""
        alerts = [a for a in self._alerts.values() if not a.is_resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if coverage_type:
            alerts = [a for a in alerts if a.coverage_type == coverage_type]
        
        # Sort by severity (critical first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        alerts.sort(key=lambda a: (severity_order.get(a.severity, 5), a.created_at))
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self._alerts:
            return False
        
        alert = self._alerts[alert_id]
        alert.is_acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        self._log_action('acknowledge_alert', alert.risk_id, {'alert_id': alert_id})
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        if alert_id not in self._alerts:
            return False
        
        alert = self._alerts[alert_id]
        alert.is_resolved = True
        alert.resolved_at = datetime.now()
        
        self._log_action('resolve_alert', alert.risk_id, {'alert_id': alert_id})
        return True


# =============================================================================
# ANALYSIS SYSTEM
# =============================================================================

class AnalysisMixin:
    """Mixin class providing analysis functionality"""
    
    def analyze_risk(
        self,
        risk_id: str,
        depth: 'AnalysisDepth' = AnalysisDepth.STANDARD
    ) -> Dict[str, Any]:
        """
        Perform detailed analysis of a single risk.
        
        Args:
            risk_id: ID of risk to analyze
            depth: Level of detail required
            
        Returns:
            Analysis results dict
        """
        risk = self.get_risk(risk_id)
        if not risk:
            raise ValueError(f"Risk {risk_id} not found")
        
        analysis = {
            'risk_id': risk_id,
            'entity_name': risk.identifier.entity_name,
            'coverage_type': risk.identifier.coverage_type.value,
            'analysis_depth': depth.value,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Basic info
        analysis['basic'] = {
            'status': risk.status.value,
            'domain': risk.primary_domain,
            'sector': risk.metadata.sector,
            'geography': risk.metadata.geography,
            'premium': risk.metadata.premium,
            'limit': risk.metadata.limit
        }
        
        # Assessment summary
        if risk.current_assessment:
            assessment = risk.current_assessment
            analysis['assessment'] = {
                'overall_score': assessment.overall_score,
                'tier': assessment.tier,
                'tier_description': self._get_tier_description(assessment.tier),
                'recommended_action': assessment.recommended_action,
                'data_quality': assessment.data_quality_score,
                'signal_coverage': assessment.signal_coverage,
                'red_flags': assessment.red_flags,
                'green_flags': assessment.green_flags
            }
            
            if depth in [AnalysisDepth.DETAILED, AnalysisDepth.DIAGNOSTIC]:
                analysis['assessment']['type_scores'] = assessment.type_scores
                analysis['assessment']['sources_used'] = assessment.sources_used
        
        # Historical analysis
        if risk.assessment_history:
            history = risk.assessment_history
            analysis['history'] = {
                'assessment_count': len(history),
                'score_trend': self._calculate_trend([h.overall_score for h in history]),
                'tier_migrations': self._count_tier_migrations(history)
            }
            
            if depth in [AnalysisDepth.DETAILED, AnalysisDepth.DIAGNOSTIC]:
                analysis['history']['assessments'] = [
                    {
                        'date': h.assessment_date.isoformat(),
                        'score': h.overall_score,
                        'tier': h.tier,
                        'changes': h.key_changes
                    }
                    for h in history[-10:]  # Last 10
                ]
        
        # Peer comparison
        peers = self._find_peer_risks(risk)
        if peers:
            peer_scores = [p.current_assessment.overall_score for p in peers if p.current_assessment]
            if peer_scores:
                analysis['peer_comparison'] = {
                    'peer_count': len(peers),
                    'peer_average_score': statistics.mean(peer_scores),
                    'peer_median_score': statistics.median(peer_scores),
                    'percentile_rank': self._calculate_percentile(
                        risk.current_assessment.overall_score if risk.current_assessment else 0,
                        peer_scores
                    )
                }
        
        # Active alerts
        analysis['alerts'] = [
            {
                'alert_id': a.alert_id,
                'type': a.alert_type.value,
                'severity': a.severity.value,
                'title': a.title,
                'acknowledged': a.is_acknowledged
            }
            for a in risk.active_alerts if not a.is_resolved
        ]
        
        # Variance analysis
        if depth in [AnalysisDepth.DETAILED, AnalysisDepth.DIAGNOSTIC]:
            analysis['variance'] = self._analyze_variance(risk)
        
        # Diagnostic info
        if depth == AnalysisDepth.DIAGNOSTIC:
            analysis['diagnostic'] = {
                'last_updated': risk.last_updated.isoformat(),
                'manual_overrides': risk.manual_overrides,
                'underwriter_notes': risk.underwriter_notes,
                'assessment_version': risk.current_assessment.assessment_version if risk.current_assessment else None
            }
        
        return analysis
    
    def analyze_portfolio(
        self,
        coverage_types: Optional[List['CoverageType']] = None,
        depth: 'AnalysisDepth' = AnalysisDepth.STANDARD
    ) -> Dict[str, Any]:
        """
        Perform comprehensive portfolio analysis.
        
        Args:
            coverage_types: Optional filter for specific coverage types
            depth: Level of detail required
            
        Returns:
            Portfolio analysis results
        """
        metrics = self.calculate_metrics(force_refresh=True)
        
        # Get relevant risks
        if coverage_types:
            risks = []
            for ct in coverage_types:
                risks.extend(self.get_risks(coverage_type=ct, status=RiskStatus.ACTIVE))
        else:
            risks = self.get_risks(status=RiskStatus.ACTIVE)
        
        analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_depth': depth.value,
            'coverage_types': [ct.value for ct in coverage_types] if coverage_types else ['all']
        }
        
        # Portfolio summary
        analysis['summary'] = {
            'total_risks': metrics.total_risks,
            'total_premium': metrics.total_premium,
            'total_limit': metrics.total_limit,
            'average_score': metrics.average_score,
            'median_score': metrics.median_score,
            'score_std_dev': metrics.score_std_dev
        }
        
        # Distribution analysis
        analysis['distribution'] = {
            'by_coverage': metrics.risks_by_coverage,
            'premium_by_coverage': metrics.premium_by_coverage,
            'by_tier': metrics.risks_by_tier,
            'premium_by_tier': metrics.premium_by_tier,
            'score_percentiles': metrics.score_percentiles
        }
        
        # Quality metrics
        analysis['quality'] = {
            'average_data_quality': metrics.average_data_quality,
            'risks_requiring_review': metrics.risks_requiring_review,
            'risks_with_red_flags': metrics.risks_with_red_flags,
            'review_rate': (metrics.risks_requiring_review / metrics.total_risks * 100) if metrics.total_risks > 0 else 0
        }
        
        # Concentration analysis
        analysis['concentrations'] = {
            'breached': [
                {
                    'dimension': c.dimension,
                    'value': c.value,
                    'percentage': c.percentage,
                    'threshold': c.threshold
                }
                for c in metrics.concentrations if c.is_breached
            ],
            'approaching': [
                {
                    'dimension': c.dimension,
                    'value': c.value,
                    'percentage': c.percentage,
                    'threshold': c.threshold
                }
                for c in metrics.concentrations 
                if not c.is_breached and c.percentage > c.threshold * 0.8
            ]
        }
        
        # Alert summary
        analysis['alerts'] = {
            'by_severity': metrics.active_alerts_by_severity,
            'total_active': sum(metrics.active_alerts_by_severity.values())
        }
        
        # Detailed analysis
        if depth in [AnalysisDepth.DETAILED, AnalysisDepth.DIAGNOSTIC]:
            # Top risks by premium
            sorted_by_premium = sorted(risks, key=lambda r: r.metadata.premium or 0, reverse=True)
            analysis['top_risks_by_premium'] = [
                {
                    'entity': r.identifier.entity_name,
                    'premium': r.metadata.premium,
                    'score': r.current_assessment.overall_score if r.current_assessment else None,
                    'tier': r.current_assessment.tier if r.current_assessment else None
                }
                for r in sorted_by_premium[:10]
            ]
            
            # Lowest scoring risks
            scored_risks = [r for r in risks if r.current_assessment]
            sorted_by_score = sorted(scored_risks, key=lambda r: r.current_assessment.overall_score)
            analysis['lowest_scoring_risks'] = [
                {
                    'entity': r.identifier.entity_name,
                    'score': r.current_assessment.overall_score,
                    'tier': r.current_assessment.tier,
                    'red_flags': len(r.current_assessment.red_flags)
                }
                for r in sorted_by_score[:10]
            ]
            
            # Score distribution histogram
            if scored_risks:
                scores = [r.current_assessment.overall_score for r in scored_risks]
                analysis['score_histogram'] = self._create_histogram(scores, bins=10, min_val=0, max_val=1000)
        
        return analysis
    
    def compare_risks(
        self,
        risk_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple risks side by side.
        
        Args:
            risk_ids: List of risk IDs to compare
            
        Returns:
            Comparison results
        """
        risks = [self.get_risk(rid) for rid in risk_ids]
        risks = [r for r in risks if r is not None]
        
        if len(risks) < 2:
            raise ValueError("At least 2 valid risks required for comparison")
        
        comparison = {
            'risk_count': len(risks),
            'comparison_timestamp': datetime.now().isoformat()
        }
        
        # Basic comparison
        comparison['risks'] = []
        for risk in risks:
            risk_data = {
                'risk_id': risk.identifier.risk_id,
                'entity_name': risk.identifier.entity_name,
                'coverage_type': risk.identifier.coverage_type.value,
                'sector': risk.metadata.sector,
                'geography': risk.metadata.geography,
                'premium': risk.metadata.premium,
                'score': risk.current_assessment.overall_score if risk.current_assessment else None,
                'tier': risk.current_assessment.tier if risk.current_assessment else None,
                'red_flags': len(risk.current_assessment.red_flags) if risk.current_assessment else 0,
                'data_quality': risk.current_assessment.data_quality_score if risk.current_assessment else None
            }
            comparison['risks'].append(risk_data)
        
        # Statistical comparison
        scores = [r['score'] for r in comparison['risks'] if r['score'] is not None]
        if scores:
            comparison['statistics'] = {
                'average_score': statistics.mean(scores),
                'score_range': max(scores) - min(scores),
                'highest_scoring': max(comparison['risks'], key=lambda r: r['score'] or 0)['entity_name'],
                'lowest_scoring': min(comparison['risks'], key=lambda r: r['score'] or 1000)['entity_name']
            }
        
        # Type score comparison
        type_scores_comparison = defaultdict(list)
        for risk in risks:
            if risk.current_assessment and risk.current_assessment.type_scores:
                for type_name, score in risk.current_assessment.type_scores.items():
                    type_scores_comparison[type_name].append({
                        'entity': risk.identifier.entity_name,
                        'score': score
                    })
        
        comparison['type_scores'] = dict(type_scores_comparison)
        
        return comparison
    
    def _find_peer_risks(self, risk: 'PortfolioRisk') -> List['PortfolioRisk']:
        """Find peer risks for comparison"""
        return self.get_risks(
            coverage_type=risk.identifier.coverage_type,
            sector=risk.metadata.sector,
            status=RiskStatus.ACTIVE
        )
    
    def _calculate_percentile(self, value: float, population: List[float]) -> float:
        """Calculate percentile rank of value in population"""
        if not population:
            return 0
        below = sum(1 for v in population if v < value)
        return (below / len(population)) * 100
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"
        
        recent = values[-3:] if len(values) >= 3 else values
        earlier = values[:3] if len(values) >= 3 else values
        
        recent_avg = statistics.mean(recent)
        earlier_avg = statistics.mean(earlier)
        
        diff = recent_avg - earlier_avg
        if diff > 20:
            return "improving"
        elif diff < -20:
            return "deteriorating"
        else:
            return "stable"
    
    def _count_tier_migrations(self, history: List['HistoricalAssessment']) -> Dict[str, int]:
        """Count tier migrations in assessment history"""
        upgrades = 0
        downgrades = 0
        
        for i in range(1, len(history)):
            tier_change = history[i].tier - history[i-1].tier
            if tier_change > 0:
                downgrades += 1
            elif tier_change < 0:
                upgrades += 1
        
        return {'upgrades': upgrades, 'downgrades': downgrades}
    
    def _analyze_variance(self, risk: 'PortfolioRisk') -> List[Dict[str, Any]]:
        """Analyze variance from expectations/benchmarks"""
        variances = []
        
        if not risk.current_assessment:
            return variances
        
        # Compare to sector benchmark
        peers = self._find_peer_risks(risk)
        if peers:
            peer_scores = [p.current_assessment.overall_score for p in peers if p.current_assessment]
            if peer_scores:
                peer_avg = statistics.mean(peer_scores)
                variance = risk.current_assessment.overall_score - peer_avg
                variance_pct = (variance / peer_avg) * 100 if peer_avg > 0 else 0
                
                variances.append({
                    'metric': 'sector_peer_comparison',
                    'expected': peer_avg,
                    'actual': risk.current_assessment.overall_score,
                    'variance': variance,
                    'variance_percentage': variance_pct,
                    'is_significant': abs(variance_pct) > 20
                })
        
        return variances
    
    def _get_tier_description(self, tier: int) -> str:
        """Get description for a tier"""
        descriptions = {
            1: "Preferred - Auto-approve with potential discount",
            2: "Standard - Auto-approve at standard pricing",
            3: "Elevated - Manual review, +15-30% loading",
            4: "High Risk - Manual review required, +30-60% loading",
            5: "Critical - Decline or special terms only"
        }
        return descriptions.get(tier, "Unknown tier")
    
    def _create_histogram(
        self, 
        values: List[float], 
        bins: int = 10,
        min_val: float = 0,
        max_val: float = 1000
    ) -> List[Dict[str, Any]]:
        """Create histogram data from values"""
        bin_width = (max_val - min_val) / bins
        histogram = []
        
        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            count = sum(1 for v in values if bin_start <= v < bin_end)
            histogram.append({
                'bin_start': bin_start,
                'bin_end': bin_end,
                'count': count,
                'percentage': (count / len(values)) * 100 if values else 0
            })
        
        return histogram


# =============================================================================
# QUERY SYSTEM
# =============================================================================

class QueryMixin:
    """Mixin class providing query functionality"""
    
    def query(
        self,
        query_string: str,
        max_results: int = 100
    ) -> 'QueryResult':
        """
        Execute a natural language query against the portfolio.
        
        Args:
            query_string: Natural language query
            max_results: Maximum results to return
            
        Returns:
            QueryResult with matching risks
        """
        query_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        # Parse query into filters
        filters = self._parse_query(query_string)
        
        # Execute query
        risks = self.get_risks(**filters)
        
        # Apply result limit
        risks = risks[:max_results]
        
        # Calculate aggregations
        aggregations = self._calculate_query_aggregations(risks)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            query_id=query_id,
            query_description=query_string,
            matching_risks=risks,
            result_count=len(risks),
            aggregations=aggregations,
            execution_time_ms=execution_time
        )
    
    def _parse_query(self, query_string: str) -> Dict[str, Any]:
        """Parse natural language query into filters"""
        filters = {}
        query_lower = query_string.lower()
        
        # Coverage type keywords
        coverage_keywords = {
            'cyber': CoverageType.CYBER,
            'financial': CoverageType.FINANCIAL_INSTITUTIONS,
            'fi': CoverageType.FINANCIAL_INSTITUTIONS,
            'energy': CoverageType.ENERGY,
            'marine': CoverageType.MARINE,
            'd&o': CoverageType.DIRECTORS_OFFICERS,
            'directors': CoverageType.DIRECTORS_OFFICERS,
            'casualty': CoverageType.CASUALTY,
            'property': CoverageType.PROPERTY
        }
        
        for keyword, coverage in coverage_keywords.items():
            if keyword in query_lower:
                filters['coverage_type'] = coverage
                break
        
        # Tier keywords
        tier_patterns = {
            'tier 1': 1, 'tier1': 1, 'preferred': 1,
            'tier 2': 2, 'tier2': 2, 'standard': 2,
            'tier 3': 3, 'tier3': 3, 'elevated': 3,
            'tier 4': 4, 'tier4': 4, 'high risk': 4,
            'tier 5': 5, 'tier5': 5, 'critical': 5
        }
        
        for pattern, tier in tier_patterns.items():
            if pattern in query_lower:
                filters['tier'] = tier
                break
        
        # Score filters
        if 'low score' in query_lower or 'lowest' in query_lower:
            filters['max_score'] = 500
        elif 'high score' in query_lower or 'highest' in query_lower:
            filters['min_score'] = 700
        
        # Status keywords
        status_keywords = {
            'active': RiskStatus.ACTIVE,
            'pending': RiskStatus.PENDING_REVIEW,
            'declined': RiskStatus.DECLINED,
            'expired': RiskStatus.EXPIRED
        }
        
        for keyword, status in status_keywords.items():
            if keyword in query_lower:
                filters['status'] = status
                break
        
        # If no status specified, default to active
        if 'status' not in filters:
            filters['status'] = RiskStatus.ACTIVE
        
        return filters
    
    def _calculate_query_aggregations(
        self, 
        risks: List['PortfolioRisk']
    ) -> Dict[str, Any]:
        """Calculate aggregations for query results"""
        if not risks:
            return {}
        
        aggregations = {
            'total_count': len(risks),
            'total_premium': sum(r.metadata.premium or 0 for r in risks),
            'total_limit': sum(r.metadata.limit or 0 for r in risks)
        }
        
        # Score statistics
        scores = [r.current_assessment.overall_score for r in risks if r.current_assessment]
        if scores:
            aggregations['score_stats'] = {
                'average': statistics.mean(scores),
                'median': statistics.median(scores),
                'min': min(scores),
                'max': max(scores)
            }
        
        # Tier distribution
        tier_counts = defaultdict(int)
        for risk in risks:
            if risk.current_assessment:
                tier_counts[risk.current_assessment.tier] += 1
        aggregations['tier_distribution'] = dict(tier_counts)
        
        return aggregations
    
    def find_outliers(
        self,
        coverage_type: Optional['CoverageType'] = None,
        std_dev_threshold: float = 2.0
    ) -> List['PortfolioRisk']:
        """
        Find statistical outliers in the portfolio.
        
        Args:
            coverage_type: Optional filter for coverage type
            std_dev_threshold: Number of standard deviations for outlier detection
            
        Returns:
            List of outlier risks
        """
        risks = self.get_risks(coverage_type=coverage_type, status=RiskStatus.ACTIVE)
        scored_risks = [r for r in risks if r.current_assessment]
        
        if len(scored_risks) < 10:
            return []  # Not enough data for outlier detection
        
        scores = [r.current_assessment.overall_score for r in scored_risks]
        mean = statistics.mean(scores)
        std_dev = statistics.stdev(scores)
        
        outliers = []
        for risk in scored_risks:
            score = risk.current_assessment.overall_score
            z_score = (score - mean) / std_dev if std_dev > 0 else 0
            
            if abs(z_score) > std_dev_threshold:
                outliers.append(risk)
        
        return outliers
    
    def find_stale_assessments(
        self,
        days_threshold: Optional[int] = None
    ) -> List['PortfolioRisk']:
        """
        Find risks with stale (outdated) assessments.
        
        Args:
            days_threshold: Days after which assessment is considered stale
            
        Returns:
            List of risks with stale assessments
        """
        threshold = days_threshold or self.config.alert_thresholds.max_stale_days
        cutoff = datetime.now() - timedelta(days=threshold)
        
        stale = []
        for risk in self._risks.values():
            if risk.status != RiskStatus.ACTIVE:
                continue
            
            if not risk.current_assessment:
                stale.append(risk)
            elif risk.current_assessment.assessment_timestamp < cutoff:
                stale.append(risk)
        
        return stale

# Part 4: Dashboard and Exports

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLETE PORTFOLIO MANAGER CLASS
# =============================================================================

class DSIPortfolioManager(AlertingMixin, AnalysisMixin, QueryMixin, PortfolioManager):
    """
    Complete DSI Portfolio Manager with all functionality.
    
    This is the primary interface for portfolio management, combining:
    - Risk management (add, update, remove, query)
    - Metrics calculation and caching
    - Alerting and monitoring
    - Analysis and comparison
    - Natural language queries
    - Dashboard generation
    - Export capabilities
    
    Usage:
        # Initialize
        manager = DSIPortfolioManager()
        
        # Add risks
        risk = manager.add_risk(
            entity_name="Acme Corp",
            coverage_type=CoverageType.CYBER,
            metadata=RiskMetadata(sector="technology", premium=500000)
        )
        
        # Get portfolio metrics
        metrics = manager.calculate_metrics()
        
        # Check alerts
        alerts = manager.get_active_alerts(severity=AlertSeverity.HIGH)
        
        # Analyze risk
        analysis = manager.analyze_risk(risk.identifier.risk_id)
        
        # Query portfolio
        results = manager.query("show me tier 4 cyber risks")
        
        # Generate dashboard
        dashboard = manager.generate_dashboard()
    """
    
    def __init__(self, config: Optional[PortfolioConfig] = None):
        super().__init__(config)
        logger.info("DSIPortfolioManager fully initialized")
    
    # =========================================================================
    # DASHBOARD GENERATION
    # =========================================================================
    
    def generate_dashboard(
        self,
        include_risks: bool = True,
        include_alerts: bool = True,
        include_concentrations: bool = True,
        time_frame: TimeFrame = TimeFrame.POINT_IN_TIME
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive dashboard view.
        
        Args:
            include_risks: Include risk details
            include_alerts: Include active alerts
            include_concentrations: Include concentration analysis
            time_frame: Time frame for historical metrics
            
        Returns:
            Dashboard data structure
        """
        metrics = self.calculate_metrics(force_refresh=True)
        
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'time_frame': time_frame.value
        }
        
        # Executive Summary
        dashboard['executive_summary'] = {
            'total_risks': metrics.total_risks,
            'total_premium': f"${metrics.total_premium:,.0f}",
            'total_limit': f"${metrics.total_limit:,.0f}",
            'average_score': f"{metrics.average_score:.0f}",
            'portfolio_health': self._calculate_health_score(metrics)
        }
        
        # Score Distribution
        dashboard['score_distribution'] = {
            'average': metrics.average_score,
            'median': metrics.median_score,
            'std_dev': metrics.score_std_dev,
            'percentiles': metrics.score_percentiles
        }
        
        # Tier Distribution
        dashboard['tier_distribution'] = {
            'by_count': metrics.risks_by_tier,
            'by_premium': {
                tier: f"${premium:,.0f}" 
                for tier, premium in metrics.premium_by_tier.items()
            }
        }
        
        # Coverage Distribution
        dashboard['coverage_distribution'] = {
            'by_count': metrics.risks_by_coverage,
            'by_premium': {
                cov: f"${premium:,.0f}" 
                for cov, premium in metrics.premium_by_coverage.items()
            }
        }
        
        # Quality Metrics
        dashboard['quality_metrics'] = {
            'average_data_quality': f"{metrics.average_data_quality:.1f}%",
            'risks_requiring_review': metrics.risks_requiring_review,
            'risks_with_red_flags': metrics.risks_with_red_flags,
            'review_rate': f"{(metrics.risks_requiring_review / max(1, metrics.total_risks) * 100):.1f}%"
        }
        
        # Alerts
        if include_alerts:
            active_alerts = self.get_active_alerts()
            dashboard['alerts'] = {
                'summary': metrics.active_alerts_by_severity,
                'total_active': len(active_alerts),
                'critical': [
                    {
                        'title': a.title,
                        'description': a.description,
                        'risk': a.risk_id,
                        'created': a.created_at.isoformat()
                    }
                    for a in active_alerts if a.severity == AlertSeverity.CRITICAL
                ][:5],  # Top 5 critical
                'high': [
                    {
                        'title': a.title,
                        'risk': a.risk_id
                    }
                    for a in active_alerts if a.severity == AlertSeverity.HIGH
                ][:10]  # Top 10 high
            }
        
        # Concentrations
        if include_concentrations:
            dashboard['concentrations'] = {
                'breached': [
                    {
                        'dimension': c.dimension,
                        'value': c.value,
                        'exposure': f"${c.exposure:,.0f}",
                        'percentage': f"{c.percentage:.1f}%",
                        'threshold': f"{c.threshold:.1f}%"
                    }
                    for c in metrics.concentrations if c.is_breached
                ],
                'approaching': [
                    {
                        'dimension': c.dimension,
                        'value': c.value,
                        'percentage': f"{c.percentage:.1f}%",
                        'threshold': f"{c.threshold:.1f}%"
                    }
                    for c in metrics.concentrations 
                    if not c.is_breached and c.percentage > c.threshold * 0.8
                ]
            }
        
        # Top risks
        if include_risks:
            risks = list(self._risks.values())
            active_risks = [r for r in risks if r.status == RiskStatus.ACTIVE]
            
            # Highest premium
            by_premium = sorted(active_risks, key=lambda r: r.metadata.premium or 0, reverse=True)
            dashboard['top_risks_by_premium'] = [
                {
                    'entity': r.identifier.entity_name,
                    'coverage': r.identifier.coverage_type.value,
                    'premium': f"${r.metadata.premium:,.0f}" if r.metadata.premium else "N/A",
                    'score': r.current_assessment.overall_score if r.current_assessment else None,
                    'tier': r.current_assessment.tier if r.current_assessment else None
                }
                for r in by_premium[:10]
            ]
            
            # Lowest scoring
            scored = [r for r in active_risks if r.current_assessment]
            by_score = sorted(scored, key=lambda r: r.current_assessment.overall_score)
            dashboard['lowest_scoring_risks'] = [
                {
                    'entity': r.identifier.entity_name,
                    'coverage': r.identifier.coverage_type.value,
                    'score': r.current_assessment.overall_score,
                    'tier': r.current_assessment.tier,
                    'red_flags': len(r.current_assessment.red_flags)
                }
                for r in by_score[:10]
            ]
            
            # Recently updated
            by_update = sorted(active_risks, key=lambda r: r.last_updated, reverse=True)
            dashboard['recently_updated'] = [
                {
                    'entity': r.identifier.entity_name,
                    'updated': r.last_updated.isoformat(),
                    'score': r.current_assessment.overall_score if r.current_assessment else None
                }
                for r in by_update[:10]
            ]
        
        return dashboard
    
    def _calculate_health_score(self, metrics: PortfolioMetrics) -> Dict[str, Any]:
        """Calculate overall portfolio health score"""
        # Start with 100
        health = 100.0
        issues = []
        
        # Deduct for tier distribution
        tier_4_5_pct = (
            (metrics.risks_by_tier.get(4, 0) + metrics.risks_by_tier.get(5, 0)) / 
            max(1, metrics.total_risks) * 100
        )
        if tier_4_5_pct > 20:
            health -= 15
            issues.append(f"High-risk tier concentration: {tier_4_5_pct:.1f}%")
        elif tier_4_5_pct > 10:
            health -= 8
            issues.append(f"Elevated high-risk tier concentration: {tier_4_5_pct:.1f}%")
        
        # Deduct for concentration breaches
        breached = sum(1 for c in metrics.concentrations if c.is_breached)
        if breached > 0:
            health -= breached * 10
            issues.append(f"{breached} concentration limit(s) breached")
        
        # Deduct for data quality
        if metrics.average_data_quality < 70:
            health -= 10
            issues.append("Below-target data quality")
        
        # Deduct for review backlog
        review_pct = metrics.risks_requiring_review / max(1, metrics.total_risks) * 100
        if review_pct > 15:
            health -= 10
            issues.append(f"High review backlog: {review_pct:.1f}%")
        
        # Deduct for alerts
        critical_alerts = metrics.active_alerts_by_severity.get('critical', 0)
        if critical_alerts > 0:
            health -= critical_alerts * 10
            issues.append(f"{critical_alerts} critical alert(s)")
        
        health = max(0, min(100, health))
        
        if health >= 80:
            status = "Healthy"
            color = "green"
        elif health >= 60:
            status = "Attention Needed"
            color = "amber"
        else:
            status = "Action Required"
            color = "red"
        
        return {
            'score': health,
            'status': status,
            'color': color,
            'issues': issues
        }
    
    # =========================================================================
    # EXPORT FUNCTIONALITY
    # =========================================================================
    
    def export_portfolio(
        self,
        format: str = 'json',
        include_history: bool = False,
        coverage_types: Optional[List[CoverageType]] = None
    ) -> Any:
        """
        Export portfolio data.
        
        Args:
            format: 'json', 'csv', or 'dict'
            include_history: Include assessment history
            coverage_types: Filter by coverage types
            
        Returns:
            Exported data in requested format
        """
        # Get risks
        if coverage_types:
            risks = []
            for ct in coverage_types:
                risks.extend(self.get_risks(coverage_type=ct))
        else:
            risks = list(self._risks.values())
        
        # Build export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_risks': len(risks),
            'risks': []
        }
        
        for risk in risks:
            risk_data = {
                'risk_id': risk.identifier.risk_id,
                'entity_name': risk.identifier.entity_name,
                'coverage_type': risk.identifier.coverage_type.value,
                'policy_reference': risk.identifier.policy_reference,
                'inception_date': risk.identifier.inception_date.isoformat() if risk.identifier.inception_date else None,
                'expiry_date': risk.identifier.expiry_date.isoformat() if risk.identifier.expiry_date else None,
                'status': risk.status.value,
                'primary_domain': risk.primary_domain,
                'metadata': {
                    'sector': risk.metadata.sector,
                    'sub_sector': risk.metadata.sub_sector,
                    'geography': risk.metadata.geography,
                    'size_band': risk.metadata.size_band,
                    'premium': risk.metadata.premium,
                    'limit': risk.metadata.limit,
                    'retention': risk.metadata.retention,
                    'currency': risk.metadata.currency,
                    'underwriter': risk.metadata.underwriter,
                    'broker': risk.metadata.broker
                }
            }
            
            if risk.current_assessment:
                a = risk.current_assessment
                risk_data['assessment'] = {
                    'overall_score': a.overall_score,
                    'tier': a.tier,
                    'type_scores': a.type_scores,
                    'signal_count': a.signal_count,
                    'red_flags': a.red_flags,
                    'green_flags': a.green_flags,
                    'data_quality_score': a.data_quality_score,
                    'signal_coverage': a.signal_coverage,
                    'recommended_action': a.recommended_action,
                    'manual_review_required': a.manual_review_required,
                    'assessment_timestamp': a.assessment_timestamp.isoformat()
                }
            
            if include_history and risk.assessment_history:
                risk_data['history'] = [
                    {
                        'date': h.assessment_date.isoformat(),
                        'score': h.overall_score,
                        'tier': h.tier
                    }
                    for h in risk.assessment_history
                ]
            
            export_data['risks'].append(risk_data)
        
        # Format output
        if format == 'dict':
            return export_data
        elif format == 'json':
            return json.dumps(export_data, indent=2)
        elif format == 'csv':
            return self._export_to_csv(export_data['risks'])
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _export_to_csv(self, risks: List[Dict]) -> str:
        """Convert risks to CSV format"""
        if not risks:
            return ""
        
        # Flatten structure
        rows = []
        for risk in risks:
            row = {
                'risk_id': risk['risk_id'],
                'entity_name': risk['entity_name'],
                'coverage_type': risk['coverage_type'],
                'status': risk['status'],
                'sector': risk['metadata'].get('sector'),
                'geography': risk['metadata'].get('geography'),
                'premium': risk['metadata'].get('premium'),
                'limit': risk['metadata'].get('limit'),
            }
            
            if 'assessment' in risk:
                row['score'] = risk['assessment']['overall_score']
                row['tier'] = risk['assessment']['tier']
                row['data_quality'] = risk['assessment']['data_quality_score']
                row['red_flag_count'] = len(risk['assessment']['red_flags'])
            
            rows.append(row)
        
        # Generate CSV
        if not rows:
            return ""
        
        headers = list(rows[0].keys())
        lines = [','.join(headers)]
        
        for row in rows:
            values = [str(row.get(h, '')) for h in headers]
            lines.append(','.join(values))
        
        return '\n'.join(lines)
    
    def export_alerts(self, format: str = 'json') -> Any:
        """Export all active alerts"""
        alerts = self.get_active_alerts()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_alerts': len(alerts),
            'alerts': [
                {
                    'alert_id': a.alert_id,
                    'type': a.alert_type.value,
                    'severity': a.severity.value,
                    'title': a.title,
                    'description': a.description,
                    'risk_id': a.risk_id,
                    'coverage_type': a.coverage_type.value if a.coverage_type else None,
                    'created_at': a.created_at.isoformat(),
                    'is_acknowledged': a.is_acknowledged,
                    'details': a.details
                }
                for a in alerts
            ]
        }
        
        if format == 'dict':
            return export_data
        elif format == 'json':
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    def refresh_all_assessments(
        self,
        signal_engine: Any = None,
        coverage_types: Optional[List[CoverageType]] = None
    ) -> Dict[str, Any]:
        """
        Refresh DSI assessments for all risks.
        
        Args:
            signal_engine: Signal collection engine to use
            coverage_types: Optional filter for coverage types
            
        Returns:
            Summary of refresh operation
        """
        if signal_engine is None:
            return {'error': 'Signal engine required for assessment refresh'}
        
        # Get risks to refresh
        if coverage_types:
            risks = []
            for ct in coverage_types:
                risks.extend(self.get_risks(coverage_type=ct, status=RiskStatus.ACTIVE))
        else:
            risks = self.get_risks(status=RiskStatus.ACTIVE)
        
        results = {
            'total_risks': len(risks),
            'refreshed': 0,
            'errors': [],
            'score_changes': []
        }
        
        for risk in risks:
            try:
                # Collect new signals
                signal_result = signal_engine.collect(
                    entity_name=risk.identifier.entity_name,
                    domain_hint=risk.primary_domain
                )
                
                # Create new assessment
                new_assessment = DSIAssessment(
                    overall_score=signal_result.overall_score,
                    tier=signal_result.tier,
                    type_scores={
                        t.value: signal_result.get_signal_group(t).aggregate_score
                        for t in SignalType
                    },
                    signal_count=sum(
                        len(signal_result.get_signal_group(t).signals)
                        for t in SignalType
                    ),
                    red_flags=[
                        s.red_flag_reason
                        for g in [signal_result.get_signal_group(t) for t in SignalType]
                        for s in g.signals if s.is_red_flag
                    ],
                    green_flags=[
                        s.green_flag_reason
                        for g in [signal_result.get_signal_group(t) for t in SignalType]
                        for s in g.signals if s.is_green_flag
                    ],
                    sources_used=[s.value for s in signal_result.sources_used]
                )
                
                # Track score change
                if risk.current_assessment:
                    old_score = risk.current_assessment.overall_score
                    new_score = new_assessment.overall_score
                    if abs(new_score - old_score) > 50:
                        results['score_changes'].append({
                            'entity': risk.identifier.entity_name,
                            'old_score': old_score,
                            'new_score': new_score,
                            'change': new_score - old_score
                        })
                
                # Update risk
                self.update_risk(risk.identifier.risk_id, {'assessment': new_assessment})
                results['refreshed'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'entity': risk.identifier.entity_name,
                    'error': str(e)
                })
        
        return results
    
    # =========================================================================
    # SCENARIO ANALYSIS
    # =========================================================================
    
    def run_scenario(
        self,
        scenario_name: str,
        adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a what-if scenario analysis.
        
        Args:
            scenario_name: Name of the scenario
            adjustments: Dict of adjustments to apply
                - score_adjustment: Adjust all scores by this amount
                - tier_shift: Shift all tiers by this amount
                - sector_filter: Only affect this sector
                
        Returns:
            Scenario analysis results
        """
        # Get current metrics
        current_metrics = self.calculate_metrics(force_refresh=True)
        
        # Get risks
        risks = self.get_risks(status=RiskStatus.ACTIVE)
        if adjustments.get('sector_filter'):
            risks = [r for r in risks if r.metadata.sector == adjustments['sector_filter']]
        
        # Apply scenario adjustments
        scenario_scores = []
        scenario_tiers = defaultdict(int)
        
        for risk in risks:
            if not risk.current_assessment:
                continue
            
            score = risk.current_assessment.overall_score
            tier = risk.current_assessment.tier
            
            # Apply adjustments
            if 'score_adjustment' in adjustments:
                score = max(0, min(1000, score + adjustments['score_adjustment']))
            
            if 'tier_shift' in adjustments:
                tier = max(1, min(5, tier + adjustments['tier_shift']))
            
            # Recalculate tier from score if score was adjusted
            if 'score_adjustment' in adjustments:
                for t, (low, high) in self.config.tier_thresholds.items():
                    if low <= score <= high:
                        tier = t
                        break
            
            scenario_scores.append(score)
            scenario_tiers[tier] += 1
        
        # Calculate scenario metrics
        scenario = {
            'scenario_name': scenario_name,
            'adjustments': adjustments,
            'risks_affected': len(scenario_scores),
            'current_state': {
                'average_score': current_metrics.average_score,
                'tier_distribution': dict(current_metrics.risks_by_tier)
            },
            'scenario_state': {
                'average_score': statistics.mean(scenario_scores) if scenario_scores else 0,
                'tier_distribution': dict(scenario_tiers)
            },
            'impact': {}
        }
        
        # Calculate impact
        if scenario_scores:
            scenario['impact']['score_change'] = scenario['scenario_state']['average_score'] - current_metrics.average_score
            
            # Calculate premium impact (simplified)
            tier_premium_factors = {1: 0.9, 2: 1.0, 3: 1.2, 4: 1.5, 5: 2.0}
            current_weighted = sum(
                current_metrics.risks_by_tier.get(t, 0) * tier_premium_factors.get(t, 1.0)
                for t in range(1, 6)
            )
            scenario_weighted = sum(
                scenario_tiers.get(t, 0) * tier_premium_factors.get(t, 1.0)
                for t in range(1, 6)
            )
            scenario['impact']['premium_factor_change'] = scenario_weighted - current_weighted
        
        return scenario


# =============================================================================
# FACTORY AND CONVENIENCE FUNCTIONS
# =============================================================================

def create_portfolio_manager(
    config: Optional[PortfolioConfig] = None
) -> DSIPortfolioManager:
    """Factory function to create a portfolio manager"""
    return DSIPortfolioManager(config)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DSI Portfolio Management Demo")
    print("=" * 70)
    
    # Create manager
    manager = DSIPortfolioManager()
    
    # Add sample risks
    sample_risks = [
        {
            'entity_name': 'Acme Technology Corp',
            'coverage_type': CoverageType.CYBER,
            'metadata': RiskMetadata(
                sector='technology',
                geography='US',
                premium=500000,
                limit=10000000
            ),
            'assessment': DSIAssessment(
                overall_score=720,
                tier=2,
                data_quality_score=85,
                signal_coverage=80
            )
        },
        {
            'entity_name': 'Global Energy Partners',
            'coverage_type': CoverageType.ENERGY,
            'metadata': RiskMetadata(
                sector='energy',
                geography='UK',
                premium=1200000,
                limit=50000000
            ),
            'assessment': DSIAssessment(
                overall_score=450,
                tier=4,
                red_flags=['Prior incident history', 'Low security investment'],
                data_quality_score=75,
                manual_review_required=True,
                review_reasons=['High risk tier', 'Red flags detected']
            )
        },
        {
            'entity_name': 'First National Bank',
            'coverage_type': CoverageType.FINANCIAL_INSTITUTIONS,
            'metadata': RiskMetadata(
                sector='banking',
                geography='US',
                premium=800000,
                limit=25000000
            ),
            'assessment': DSIAssessment(
                overall_score=680,
                tier=2,
                data_quality_score=90,
                signal_coverage=85
            )
        },
    ]
    
    for risk_data in sample_risks:
        manager.add_risk(
            entity_name=risk_data['entity_name'],
            coverage_type=risk_data['coverage_type'],
            metadata=risk_data['metadata'],
            assessment=risk_data['assessment']
        )
    
    # Calculate metrics
    print("\n📊 Portfolio Metrics:")
    print("-" * 40)
    metrics = manager.calculate_metrics()
    print(f"Total Risks: {metrics.total_risks}")
    print(f"Total Premium: ${metrics.total_premium:,.0f}")
    print(f"Average Score: {metrics.average_score:.0f}")
    print(f"By Tier: {dict(metrics.risks_by_tier)}")
    
    # Check alerts
    print("\n🚨 Active Alerts:")
    print("-" * 40)
    alerts = manager.get_active_alerts()
    for alert in alerts:
        print(f"[{alert.severity.value.upper()}] {alert.title}")
    
    # Generate dashboard
    print("\n📈 Dashboard Summary:")
    print("-" * 40)
    dashboard = manager.generate_dashboard()
    health = dashboard['executive_summary']['portfolio_health']
    print(f"Portfolio Health: {health['score']:.0f}/100 ({health['status']})")
    if health['issues']:
        print("Issues:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    # Run query
    print("\n🔍 Query: 'tier 4 risks'")
    print("-" * 40)
    result = manager.query("tier 4 risks")
    print(f"Found {result.result_count} matching risks")
    for risk in result.matching_risks:
        print(f"  - {risk.identifier.entity_name}")
    
    # Scenario analysis
    print("\n📊 Scenario: Score deterioration of 100 points")
    print("-" * 40)
    scenario = manager.run_scenario(
        "Score Deterioration",
        {'score_adjustment': -100}
    )
    print(f"Current avg score: {scenario['current_state']['average_score']:.0f}")
    print(f"Scenario avg score: {scenario['scenario_state']['average_score']:.0f}")
    print(f"Tier distribution change: {scenario['current_state']['tier_distribution']} → {scenario['scenario_state']['tier_distribution']}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
