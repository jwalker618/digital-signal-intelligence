"""
DSI Integrated Workflow with Persistence
=========================================

Complete workflow integration that:
1. Manages signal extraction with intelligent caching
2. Handles model versioning and selection
3. Persists quotes with full audit trail
4. Supports requotes and modifications

This module demonstrates production-ready integration
of the DSI persistence layer with pricing models.

Author: John Walker
Version: 1.0.0
"""

import argparse 
import json 
import yaml 
import os 
import sys 
from pathlib import Path 
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dsi_persistence import (
    DSIPersistenceService,
    SignalCache,
    ModelRegistry,
    QuoteRepository,
    Signal,
    SignalBundle,
    ModelVersion,
    Quote,
    SignalCategory,
    ModelStatus,
    QuoteStatus,
    InMemoryStorage,
    DEFAULT_TTL,
)

logger = logging.getLogger("dsi.workflow")


# =============================================================================
# CONFIGURATION LOADING FOR ENTITY ONLY QUOTE GENERATION
# =============================================================================

@dataclass
class LimitBand:
    """Represents a single limit band."""
    limit: float
    label: str
    standard_deductible: Optional[float] = None


@dataclass
class CoverageConfig:
    """Configuration for a coverage type."""
    enabled: bool
    currency: str
    bands: List[LimitBand]
    name: Optional[str] = None


class LimitBandingConfig:
    """Loads and manages limit banding configuration."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to file in same directory as this script
            config_path = Path(__file__).parent /"config" / "dsi_coverage_limit_bands.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.defaults = self.config.get("defaults", {})

    def _load_config(self) -> Dict:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_coverage_config(self, coverage_type: str) -> Optional[CoverageConfig]:
        """Get configuration for a coverage type."""
        config = self.config.get(coverage_type)

        if not config or not config.get("enabled", False):
            return None

        bands = [
            LimitBand(
                limit=b["limit"],
                label=b["label"],
                standard_deductible=b.get("standard_deductible")
            )
            for b in config.get("bands", [])
        ]

        return CoverageConfig(
            enabled=config.get("enabled", True),
            currency=config.get("currency", "USD"),
            name=config.get("name"),
            bands=bands,
        )

    def get_enabled_coverages(self) -> List[str]:
        """Get list of enabled coverage types."""
        enabled = []
        for key, value in self.config.items():
            if key not in ["defaults", "custom_bands"] and isinstance(value, dict):
                if value.get("enabled", False):
                    enabled.append(key)
        return enabled

# =============================================================================
# SIGNAL EXTRACTION INTERFACE
# =============================================================================

class SignalExtractor:
    """
    Base class for signal extraction.
    
    Subclass for each data source (SecurityScorecard, D&B, etc.)
    """
    
    def __init__(self, cache: SignalCache):
        self.cache = cache
    
    def extract(self, entity_id: str, signal_types: List[str]) -> List[Signal]:
        """
        Extract signals, checking cache first.
        
        Returns list of Signal objects (cached or freshly extracted).
        """
        results = []
        to_fetch = []
        
        # Check cache
        for signal_type in signal_types:
            cached = self.cache.get_signal(entity_id, signal_type)
            if cached:
                results.append(cached)
            else:
                to_fetch.append(signal_type)
        
        # Fetch missing signals
        if to_fetch:
            fresh = self._fetch_signals(entity_id, to_fetch)
            for signal in fresh:
                self.cache.store_signal(signal)
                results.append(signal)
        
        return results
    
    def _fetch_signals(self, entity_id: str, signal_types: List[str]) -> List[Signal]:
        """
        Actually fetch signals from external source.
        Override in subclasses.
        """
        raise NotImplementedError

# =============================================================================
# PRICING ENGINE INTERFACE
# =============================================================================

class PricingEngine:
    """
    Base class for pricing engines.
    
    Each coverage type has its own pricing implementation.
    """
    
    def calculate(self, 
                  signals: List[Signal],
                  limit: float,
                  deductible: Optional[float],
                  model_config: Dict,
                  thresholds: Dict) -> Dict:
        """
        Calculate pricing based on signals.
        
        Returns dict with:
        - composite_score
        - tier
        - tier_label
        - gross_premium
        - green_flags, red_flags, amber_flags
        - decision_reasons
        """
        raise NotImplementedError


class GeneralPricingEngine(PricingEngine):
    """
    General pricing engine for demonstration.
    
    Production implementations would be coverage etc specific.
    """
    
    TIER_LABELS = {
        1: "PREFERRED",
        2: "STANDARD_PLUS",
        3: "STANDARD",
        4: "SUBSTANDARD",
        5: "DECLINE",
    }
    
    TIER_MODIFIERS = {
        1: 0.75,
        2: 0.90,
        3: 1.00,
        4: 1.35,
        5: 2.50,
    }
    
    def calculate(self,
                  signals: List[Signal],
                  limit: float,
                  deductible: Optional[float],
                  model_config: Dict,
                  thresholds: Dict) -> Dict:
        """Calculate pricing from signals."""
        
        # Calculate composite score from signals
        scores = []
        green_flags = []
        red_flags = []
        amber_flags = []
        
        for signal in signals:
            # Extract numeric score from signal value
            if isinstance(signal.value, dict):
                score = signal.value.get("score", 70)
            elif isinstance(signal.value, (int, float)):
                score = signal.value
            else:
                score = 70  # Default
            
            # Weight by confidence
            weighted_score = score * signal.confidence
            scores.append(weighted_score)
            
            # Categorize flags
            if score >= 80:
                green_flags.append({
                    "signal": signal.signal_type,
                    "value": signal.value,
                    "source": signal.source,
                })
            elif score < 50:
                red_flags.append({
                    "signal": signal.signal_type,
                    "value": signal.value,
                    "source": signal.source,
                    "concern": f"Low {signal.signal_name}",
                })
            else:
                amber_flags.append({
                    "signal": signal.signal_type,
                    "value": signal.value,
                    "source": signal.source,
                })
        
        # Composite score
        composite = sum(scores) / len(scores) if scores else 50
        
        # Normalize to 0-1000 scale
        composite_score = int(composite * 10)
        
        # Determine tier
        if composite_score >= thresholds.get("tier_1", 800):
            tier = 1
        elif composite_score >= thresholds.get("tier_2", 650):
            tier = 2
        elif composite_score >= thresholds.get("tier_3", 500):
            tier = 3
        elif composite_score >= thresholds.get("tier_4", 350):
            tier = 4
        else:
            tier = 5
        
        # Calculate premium
        base_rate = model_config.get("base_rate", 2500)
        min_premium = model_config.get("min_premium", 5000)
        tier_modifier = self.TIER_MODIFIERS[tier]
        
        rate_per_million = base_rate * tier_modifier
        gross_premium = max(min_premium, (limit / 1_000_000) * rate_per_million)
        
        # Deductible credit
        if deductible:
            deductible_credit = min(0.15, deductible / limit)
            gross_premium *= (1 - deductible_credit)
        
        # Taxes and fees (simplified)
        taxes_fees = gross_premium * 0.05
        
        # Decision reasons
        decision_reasons = []
        if tier <= 2:
            decision_reasons.append("Strong signal profile supports automated approval")
        if red_flags:
            decision_reasons.append(f"{len(red_flags)} concerning signals identified")
        if len(green_flags) >= 3:
            decision_reasons.append(f"{len(green_flags)} positive indicators noted")
        
        return {
            "composite_score": composite_score,
            "tier": tier,
            "tier_label": self.TIER_LABELS[tier],
            "confidence": sum(s.confidence for s in signals) / len(signals) if signals else 0,
            "gross_premium": round(gross_premium, 2),
            "net_premium": round(gross_premium - taxes_fees, 2),
            "taxes_fees": round(taxes_fees, 2),
            "rate_per_million": round(rate_per_million, 2),
            "tier_modifier": tier_modifier,
            "green_flags": green_flags,
            "red_flags": red_flags,
            "amber_flags": amber_flags,
            "decision_reasons": decision_reasons,
            "critical_flags": len(red_flags) >= 3,  # Threshold for auto-decline
        }


# =============================================================================
# INTEGRATED WORKFLOW
# =============================================================================

@dataclass
class WorkflowRequest:
    """Input for pricing workflow."""
    entity_id: str
    entity_name: str
    coverage_type: str
    limit: float
    currency: str = "USD"
    effective_date: datetime = None
    term_months: int = 12
    deductible: Optional[float] = None
    market: str = "us"
    broker_code: Optional[str] = None
    submission_channel: str = "api"
    direct_inquiry: Optional[Dict[str, bool]] = None
    
    def __post_init__(self):
        if self.effective_date is None:
            self.effective_date = datetime.utcnow() + timedelta(days=30)
        if self.direct_inquiry is None:
            self.direct_inquiry = {}


@dataclass 
class WorkflowResponse:
    """Output from pricing workflow."""
    quote: Quote
    cache_stats: Dict
    processing_time_ms: float
    model_version: str
    signal_count: int
    decision_path: str
    
    @property
    def is_auto_approved(self) -> bool:
        return self.decision_path == "straight_through"
    
    @property
    def requires_referral(self) -> bool:
        return self.decision_path == "referred"
    
    @property
    def is_declined(self) -> bool:
        return self.decision_path == "declined"


class DSIWorkflow:
    """
    Production workflow orchestrating signal extraction, 
    pricing, and persistence.
    """
    
    def __init__(self,
                 persistence: DSIPersistenceService,
                 extractor: SignalExtractor,
                 pricing_engines: Optional[Dict[str, PricingEngine]] = None):
        """
        Initialize workflow.
        
        Args:
            persistence: DSI persistence service
            extractor: Signal extractor implementation
            pricing_engines: Dict mapping coverage type to pricing engine
        """
        self.persistence = persistence
        self.extractor = extractor
        self.pricing_engines = pricing_engines or {}
        self._default_engine = GenericPricingEngine()
    
    def get_engine(self, coverage_type: str) -> PricingEngine:
        """Get pricing engine for coverage type."""
        return self.pricing_engines.get(coverage_type, self._default_engine)
    
    def process(self, request: WorkflowRequest) -> WorkflowResponse:
        """
        Execute complete pricing workflow.
        
        Steps:
        1. Get active model for coverage type
        2. Check signal cache, extract missing signals
        3. Run pricing model
        4. Determine decision path
        5. Create and persist quote
        6. Return response
        """
        start_time = datetime.utcnow()
        
        # 1. Get active model
        model = self.persistence.model_registry.get_active_model(request.coverage_type)
        if not model:
            raise ValueError(f"No active model for coverage type: {request.coverage_type}")
        
        logger.info(f"Using model {request.coverage_type} v{model.version}")
        
        # 2. Extract signals with caching
        required_signals = model.signal_requirements
        signals = self.extractor.extract(request.entity_id, required_signals)
        
        # Calculate cache stats
        cache_stats = self.persistence.signal_cache.get_cache_stats(request.entity_id)
        
        # Create signal bundle
        bundle = SignalBundle(
            bundle_id=str(uuid.uuid4()),
            entity_id=request.entity_id,
            coverage_type=request.coverage_type,
            signals=signals,
            created_at=datetime.utcnow(),
            signal_coverage=len(signals) / len(required_signals) if required_signals else 0,
        )
        
        # Store bundle
        self.persistence.signal_cache.store_bundle(bundle)
        
        # 3. Run pricing
        engine = self.get_engine(request.coverage_type)
        pricing_result = engine.calculate(
            signals=signals,
            limit=request.limit,
            deductible=request.deductible,
            model_config=model.config,
            thresholds=model.thresholds,
        )
        
        # Update bundle with score
        bundle.composite_score = pricing_result["composite_score"]
        
        # 4. Determine decision path
        has_critical_inquiry = any(
            request.direct_inquiry.get(k) 
            for k in ["pending_claims", "pending_regulatory", "coverage_declined"]
        )
        
        if pricing_result["tier"] <= 2 and not pricing_result.get("red_flags") and not has_critical_inquiry:
            decision_path = "straight_through"
            status = QuoteStatus.QUOTED
        elif pricing_result["tier"] == 5 or pricing_result.get("critical_flags") or has_critical_inquiry:
            if pricing_result["tier"] == 5:
                decision_path = "declined"
                status = QuoteStatus.DECLINED
            else:
                decision_path = "referred"
                status = QuoteStatus.REFERRED
        else:
            decision_path = "referred"
            status = QuoteStatus.REFERRED
        
        # 5. Create quote
        quote = Quote(
            quote_id=str(uuid.uuid4()),
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            coverage_type=request.coverage_type,
            model_id=model.model_id,
            model_version=model.version,
            status=status,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            requested_limit=request.limit,
            requested_currency=request.currency,
            effective_date=request.effective_date,
            term_months=request.term_months,
            deductible=request.deductible,
            composite_score=pricing_result["composite_score"],
            tier=pricing_result["tier"],
            tier_label=pricing_result["tier_label"],
            confidence=pricing_result.get("confidence", 0.0),
            signal_coverage=bundle.signal_coverage,
            gross_premium=pricing_result.get("gross_premium"),
            net_premium=pricing_result.get("net_premium"),
            taxes_fees=pricing_result.get("taxes_fees"),
            rate_per_million=pricing_result.get("rate_per_million"),
            tier_modifier=pricing_result.get("tier_modifier"),
            decision_path=decision_path,
            decision_reasons=pricing_result.get("decision_reasons", []),
            green_flags=pricing_result.get("green_flags", []),
            red_flags=pricing_result.get("red_flags", []),
            amber_flags=pricing_result.get("amber_flags", []),
            signal_bundle_id=bundle.bundle_id,
            market=request.market,
            broker_code=request.broker_code,
            submission_channel=request.submission_channel,
            direct_inquiry=request.direct_inquiry,
        )
        
        # 6. Persist quote
        self.persistence.quote_repo.save(quote)
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"Quote {quote.quote_id[:8]} | "
            f"{request.entity_name} | "
            f"Score: {quote.composite_score} | "
            f"Tier: {quote.tier_label} | "
            f"Path: {decision_path} | "
            f"Premium: ${quote.gross_premium:,.0f} | "
            f"Time: {processing_ms:.0f}ms"
        )
        
        return WorkflowResponse(
            quote=quote,
            cache_stats=cache_stats,
            processing_time_ms=processing_ms,
            model_version=model.version,
            signal_count=len(signals),
            decision_path=decision_path,
        )
    
    def requote(self, 
                original_quote_id: str,
                limit: Optional[float] = None,
                deductible: Optional[float] = None,
                effective_date: Optional[datetime] = None) -> WorkflowResponse:
        """
        Create new quote based on existing one with modifications.
        
        Signals are reused from cache where valid.
        """
        original = self.persistence.quote_repo.get(original_quote_id)
        if not original:
            raise ValueError(f"Quote not found: {original_quote_id}")
        
        # Create new request with modifications
        request = WorkflowRequest(
            entity_id=original.entity_id,
            entity_name=original.entity_name,
            coverage_type=original.coverage_type,
            limit=limit if limit is not None else original.requested_limit,
            currency=original.requested_currency,
            effective_date=effective_date if effective_date is not None else original.effective_date,
            term_months=original.term_months,
            deductible=deductible if deductible is not None else original.deductible,
            market=original.market,
            broker_code=original.broker_code,
            submission_channel=original.submission_channel,
            direct_inquiry=original.direct_inquiry,
        )
        
        # Process (signals will come from cache if still valid)
        response = self.process(request)
        
        # Link to original
        response.quote.parent_quote_id = original_quote_id
        self.persistence.quote_repo.save(response.quote)
        
        logger.info(f"Requote {response.quote.quote_id[:8]} from {original_quote_id[:8]}")
        
        return response
    
    def bind_quote(self, quote_id: str, underwriter_id: Optional[str] = None) -> Quote:
        """Mark a quote as bound."""
        success = self.persistence.quote_repo.update_status(
            quote_id, 
            QuoteStatus.BOUND,
            underwriter_id=underwriter_id,
        )
        
        if not success:
            raise ValueError(f"Failed to bind quote: {quote_id}")
        
        quote = self.persistence.quote_repo.get(quote_id)
        logger.info(f"Quote {quote_id[:8]} BOUND")
        return quote
    
    def refer_quote(self, quote_id: str, underwriter_id: str, reason: str) -> Quote:
        """Manually refer a quote for review."""
        quote = self.persistence.quote_repo.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")
        
        quote.status = QuoteStatus.REFERRED
        quote.underwriter_id = underwriter_id
        quote.decision_reasons.append(f"Manual referral: {reason}")
        quote.decision_path = "referred"
        
        self.persistence.quote_repo.save(quote)
        logger.info(f"Quote {quote_id[:8]} REFERRED by {underwriter_id}")
        return quote
    
    def get_entity_history(self, entity_id: str) -> Dict:
        """Get complete history for an entity."""
        return self.persistence.get_entity_profile(entity_id)
    
    def get_analytics(self, days: int = 30, coverage_type: Optional[str] = None) -> Dict:
        """Get workflow analytics."""
        return self.persistence.quote_repo.get_analytics(coverage_type, days)


# =============================================================================
# FACTORY AND INITIALIZATION
# =============================================================================

def create_workflow(storage_type: str = "memory", 
                    storage_config: Optional[Dict] = None) -> DSIWorkflow:
    """
    Factory function to create a configured workflow.
    
    Args:
        storage_type: "memory", "redis", or "postgres"
        storage_config: Configuration for storage backend
    
    Returns:
        Configured DSIWorkflow instance
    """
    # Create storage backend
    if storage_type == "memory":
        storage = InMemoryStorage()
    elif storage_type == "redis":
        from redis_storage import create_redis_storage
        storage = create_redis_storage(storage_config or {})
    elif storage_type == "postgres":
        from postgres_storage import create_postgres_storage
        storage = create_postgres_storage(storage_config or {})
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
    
    # Create persistence service
    persistence = DSIPersistenceService(storage)
    
    # Create signal extractor
    extractor = MockSignalExtractor(persistence.signal_cache)
    
    # Create workflow
    return DSIWorkflow(persistence, extractor)


def initialize_models(workflow: DSIWorkflow):
    """Initialize default models for all coverage types."""
    
    coverage_configs = {
        "aerospace": {
            "name": "DSI Aerospace Model",
            "base_rate": 5000,
            "min_premium": 25000,
            "signal_requirements": [
                "safety_record", "environmental_violations", "equipment_age",
                "maintenance_record", "compliance_status", "financial_strength",
            ],
        },
        "cyber": {
            "name": "DSI Cyber Liability Model",
            "base_rate": 2500,
            "min_premium": 5000,
            "signal_requirements": [
                "security_rating", "vulnerability_count", "breach_history",
                "compliance_status", "technology_stack", "phishing_susceptibility",
                "patch_cadence", "endpoint_protection",
            ],
        },
        "do": {
            "name": "DSI Directors & Officers Model",
            "base_rate": 3500,
            "min_premium": 10000,
            "signal_requirements": [
                "financial_strength", "executive_turnover", "stock_volatility",
                "shareholder_activism", "board_composition", "litigation_history",
            ],
        },
        "energy": {
            "name": "DSI Energy Model",
            "base_rate": 5000,
            "min_premium": 25000,
            "signal_requirements": [
                "safety_record", "environmental_violations", "equipment_age",
                "maintenance_record", "compliance_status", "financial_strength",
            ],
        },
        "fi": {
            "name": "DSI Financial Institutions Model",
            "base_rate": 1800,
            "min_premium": 15000,
            "signal_requirements": [
                "financial_strength", "credit_rating", "regulatory_actions",
                "litigation_history", "compliance_status", "security_rating",
            ],
        },
        "marine": {
            "name": "DSI Marine Model",
            "base_rate": 5000,
            "min_premium": 25000,
            "signal_requirements": [
                "safety_record", "environmental_violations", "equipment_age",
                "maintenance_record", "compliance_status", "financial_strength",
            ],
        },
        "pi": {
            "name": "DSI Professional Indemnity Model",
            "base_rate": 2000,
            "min_premium": 3000,
            "signal_requirements": [
                "compliance_status", "litigation_history", "years_in_business",
                "employee_count", "revenue_trend",
            ],
        },
    }
    
    for coverage_type, config in coverage_configs.items():
        model = ModelVersion(
            model_id=str(uuid.uuid4()),
            version="2.0.0",
            coverage_type=coverage_type,
            name=config["name"],
            description=f"Production {config['name']} with DSI signals",
            status=ModelStatus.TESTING,
            created_at=datetime.utcnow(),
            created_by="system",
            config={
                "base_rate": config["base_rate"],
                "min_premium": config["min_premium"],
                "max_tier_modifier": 3.0,
            },
            signal_requirements=config["signal_requirements"],
            thresholds={
                "tier_1": 800,
                "tier_2": 650,
                "tier_3": 500,
                "tier_4": 350,
            },
            checksum="init",
        )
        
        workflow.persistence.model_registry.register_model(model)
        workflow.persistence.model_registry.activate_model(coverage_type, "2.0.0")
        logger.info(f"Initialized model: {coverage_type} v2.0.0")

# =============================================================================
# ENTITY ONLY ASSESSMENT GENERATOR
# =============================================================================

@dataclass
class AssessmentResult:
    """Result for a single coverage/limit combination."""
    entity_id: str
    entity_name: str
    coverage_type: str
    coverage_name: str
    limit: float
    limit_label: str
    currency: str
    deductible: Optional[float]

    # Assessment
    composite_score: float
    tier: int
    tier_label: str
    confidence: float
    signal_coverage: float

    # Pricing
    gross_premium: Optional[float]
    net_premium: Optional[float]
    rate_per_million: Optional[float]
    tier_modifier: Optional[float]

    # Decision
    decision_path: str
    status: str
    decision_reasons: List[str]

    # Flags
    green_flag_count: int
    red_flag_count: int
    amber_flag_count: int

    # Metadata
    quote_id: str
    model_version: str
    signal_count: int
    processing_time_ms: float
    cache_hit_rate: float
    created_at: str
    expires_at: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_summary(self) -> Dict:
        """Convert to summary format (less verbose)."""
        return {
            "coverage": self.coverage_type,
            "limit": f"${self.limit:,.0f}",
            "limit_label": self.limit_label,
            "deductible": f"${self.deductible:,.0f}" if self.deductible else "N/A",
            "score": f"{self.composite_score}/1000",
            "tier": self.tier_label,
            "premium": f"${self.gross_premium:,.2f}" if self.gross_premium else "N/A",
            "decision": self.decision_path,
            "status": self.status,
            "flags": {
                "green": self.green_flag_count,
                "amber": self.amber_flag_count,
                "red": self.red_flag_count,
            }
        }


class EntityAssessmentGenerator:
    """
    Generates comprehensive assessments for an entity across all coverages.
    """

    def __init__(self,
                 config_path: Optional[str] = None,
                 storage_type: str = "memory",
                 storage_config: Optional[Dict] = None):
        """
        Initialize generator.

        Args:
            config_path: Path to limit banding config (uses default if None)
            storage_type: "memory", "redis", or "postgres"
            storage_config: Configuration for storage backend
        """
        self.banding_config = LimitBandingConfig(config_path)
        self.workflow = create_workflow(storage_type, storage_config)

        # Initialize models
        initialize_models(self.workflow)

        logger.info("Entity Assessment Generator initialized")
        logger.info(f"Enabled coverages: {', '.join(self.banding_config.get_enabled_coverages())}")

    def generate_for_entity(self,
                            entity_name: str,
                            entity_id: Optional[str] = None,
                            coverage_types: Optional[List[str]] = None,
                            effective_date: Optional[datetime] = None,
                            term_months: int = 12,
                            market: str = "us") -> List[AssessmentResult]:
        """
        Generate assessments for all enabled coverages and limit bands.

        Args:
            entity_name: Company name (required)
            entity_id: Optional entity ID (generated from name if not provided)
            coverage_types: Specific coverage types (all enabled if None)
            effective_date: Policy effective date (30 days from now if None)
            term_months: Policy term in months (default 12)
            market: Market code (default "us")

        Returns:
            List of AssessmentResult objects
        """
        # Generate entity_id from name if not provided
        if entity_id is None:
            entity_id = self._generate_entity_id(entity_name)

        # Use all enabled coverages if not specified
        if coverage_types is None:
            coverage_types = self.banding_config.get_enabled_coverages()

        # Default effective date
        if effective_date is None:
            effective_date = datetime.utcnow() + timedelta(days=30)

        results = []

        logger.info(f"\n{'='*70}")
        logger.info(f"GENERATING ASSESSMENTS FOR: {entity_name}")
        logger.info(f"Entity ID: {entity_id}")
        logger.info(f"Coverage Types: {', '.join(coverage_types)}")
        logger.info(f"{'='*70}\n")

        for coverage_type in coverage_types:
            coverage_config = self.banding_config.get_coverage_config(coverage_type)

            if not coverage_config:
                logger.warning(f"Coverage {coverage_type} not enabled or not found")
                continue

            coverage_name = coverage_config.name or coverage_type.upper()

            logger.info(f"\n--- {coverage_name} ---")

            for band in coverage_config.bands:
                logger.info(f"Processing {band.label} (${band.limit:,.0f})...")

                # Create workflow request
                request = WorkflowRequest(
                    entity_id=entity_id,
                    entity_name=entity_name,
                    coverage_type=coverage_type,
                    limit=band.limit,
                    currency=coverage_config.currency,
                    effective_date=effective_date,
                    term_months=term_months,
                    deductible=band.standard_deductible,
                    market=market,
                    submission_channel="entity_assessment_generator",
                    direct_inquiry={
                        "pending_claims": False,
                        "pending_regulatory": False,
                        "coverage_declined": False,
                        "material_change": False,
                        "ownership_change": False,
                    },
                )

                try:
                    # Process through workflow
                    response = self.workflow.process(request)

                    # Convert to AssessmentResult
                    result = self._response_to_result(
                        response,
                        entity_name,
                        coverage_type,
                        coverage_name,
                        band,
                        coverage_config.currency,
                    )

                    results.append(result)

                    logger.info(
                        f"  ✓ Score: {result.composite_score}/1000 | "
                        f"Tier: {result.tier_label} | "
                        f"Premium: ${result.gross_premium:,.2f} | "
                        f"Path: {result.decision_path}"
                    )

                except Exception as e:
                    logger.error(f"  ✗ Error processing {band.label}: {e}")
                    continue

        logger.info(f"\n{'='*70}")
        logger.info(f"ASSESSMENT COMPLETE: {len(results)} quotes generated")
        logger.info(f"{'='*70}\n")

        return results

    def _generate_entity_id(self, entity_name: str) -> str:
        """Generate a consistent entity ID from entity name."""
        # Simple slug generation
        import re
        slug = re.sub(r'[^a-z0-9]+', '-', entity_name.lower()).strip('-')
        # Add timestamp suffix for uniqueness
        suffix = datetime.utcnow().strftime('%Y%m%d')
        return f"{slug}-{suffix}"

    def _response_to_result(self,
                            response: WorkflowResponse,
                            entity_name: str,
                            coverage_type: str,
                            coverage_name: str,
                            band: LimitBand,
                            currency: str) -> AssessmentResult:
        """Convert WorkflowResponse to AssessmentResult."""
        quote = response.quote

        return AssessmentResult(
            entity_id=quote.entity_id,
            entity_name=entity_name,
            coverage_type=coverage_type,
            coverage_name=coverage_name,
            limit=band.limit,
            limit_label=band.label,
            currency=currency,
            deductible=band.standard_deductible,
            composite_score=quote.composite_score,
            tier=quote.tier,
            tier_label=quote.tier_label,
            confidence=quote.confidence,
            signal_coverage=quote.signal_coverage,
            gross_premium=quote.gross_premium,
            net_premium=quote.net_premium,
            rate_per_million=quote.rate_per_million,
            tier_modifier=quote.tier_modifier,
            decision_path=quote.decision_path,
            status=quote.status.value,
            decision_reasons=quote.decision_reasons,
            green_flag_count=len(quote.green_flags),
            red_flag_count=len(quote.red_flags),
            amber_flag_count=len(quote.amber_flags),
            quote_id=quote.quote_id,
            model_version=response.model_version,
            signal_count=response.signal_count,
            processing_time_ms=response.processing_time_ms,
            cache_hit_rate=response.cache_stats.get("hit_rate", 0),
            created_at=quote.created_at.isoformat(),
            expires_at=quote.expires_at.isoformat(),
        )

    def export_results(self,
                       results: List[AssessmentResult],
                       output_format: str = "json",
                       output_file: Optional[str] = None) -> str:
        """
        Export results to file or return as string.

        Args:
            results: List of assessment results
            output_format: "json", "summary", or "csv"
            output_file: Optional file path to write to

        Returns:
            Formatted string output
        """
        if output_format == "json":
            data = {
                "entity": results[0].entity_name if results else "",
                "entity_id": results[0].entity_id if results else "",
                "generated_at": datetime.utcnow().isoformat(),
                "total_assessments": len(results),
                "assessments": [r.to_dict() for r in results],
            }
            output = json.dumps(data, indent=2)

        elif output_format == "summary":
            data = {
                "entity": results[0].entity_name if results else "",
                "entity_id": results[0].entity_id if results else "",
                "generated_at": datetime.utcnow().isoformat(),
                "total_assessments": len(results),
                "assessments": [r.to_summary() for r in results],
            }
            output = json.dumps(data, indent=2)

        elif output_format == "csv":
            import csv
            from io import StringIO

            buffer = StringIO()
            if results:
                writer = csv.DictWriter(buffer, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.to_dict())

            output = buffer.getvalue()

        else:
            raise ValueError(f"Unknown output format: {output_format}")

        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            logger.info(f"Results exported to: {output_file}")

        return output
