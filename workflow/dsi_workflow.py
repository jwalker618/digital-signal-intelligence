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

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum

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


class MockSignalExtractor(SignalExtractor):
    """
    Mock extractor for testing/demonstration.
    """
    
    # Signal definitions with category mappings
    SIGNAL_DEFS = {
        # Cyber signals
        "security_rating": (SignalCategory.DYNAMIC, "Security Scorecard"),
        "vulnerability_count": (SignalCategory.DYNAMIC, "Vulnerability Scanner"),
        "breach_history": (SignalCategory.SEMI_STATIC, "Breach Database"),
        "compliance_status": (SignalCategory.SEMI_STATIC, "Compliance Registry"),
        "technology_stack": (SignalCategory.SEMI_STATIC, "Tech Analyzer"),
        "phishing_susceptibility": (SignalCategory.DYNAMIC, "Phishing Test"),
        "patch_cadence": (SignalCategory.DYNAMIC, "Patch Monitor"),
        "endpoint_protection": (SignalCategory.SEMI_STATIC, "EDR Status"),
        
        # Financial signals
        "financial_strength": (SignalCategory.SEMI_STATIC, "D&B"),
        "credit_rating": (SignalCategory.SEMI_STATIC, "S&P/Moody's"),
        "revenue_trend": (SignalCategory.SEMI_STATIC, "Financial Filings"),
        "litigation_history": (SignalCategory.SEMI_STATIC, "Court Records"),
        "regulatory_actions": (SignalCategory.DYNAMIC, "Regulatory DB"),
        
        # Operational signals
        "employee_count": (SignalCategory.SEMI_STATIC, "LinkedIn/D&B"),
        "years_in_business": (SignalCategory.STATIC, "Company Registry"),
        "geographic_footprint": (SignalCategory.SEMI_STATIC, "Location Data"),
        "industry_classification": (SignalCategory.STATIC, "SIC/NAICS"),
        
        # D&O specific
        "executive_turnover": (SignalCategory.DYNAMIC, "News/LinkedIn"),
        "stock_volatility": (SignalCategory.REAL_TIME, "Market Data"),
        "shareholder_activism": (SignalCategory.DYNAMIC, "SEC Filings"),
        "board_composition": (SignalCategory.SEMI_STATIC, "SEC Filings"),
        
        # Energy specific
        "safety_record": (SignalCategory.SEMI_STATIC, "OSHA/Industry DB"),
        "environmental_violations": (SignalCategory.SEMI_STATIC, "EPA/State"),
        "equipment_age": (SignalCategory.SEMI_STATIC, "Asset Registry"),
        "maintenance_record": (SignalCategory.DYNAMIC, "Inspection Reports"),
    }
    
    def _fetch_signals(self, entity_id: str, signal_types: List[str]) -> List[Signal]:
        """Generate mock signals for testing."""
        import random
        
        signals = []
        now = datetime.utcnow()
        
        for signal_type in signal_types:
            if signal_type not in self.SIGNAL_DEFS:
                logger.warning(f"Unknown signal type: {signal_type}")
                continue
            
            category, source = self.SIGNAL_DEFS[signal_type]
            ttl_seconds = DEFAULT_TTL.get(category, 3600)
            
            # Generate mock value based on signal type
            if "rating" in signal_type or "score" in signal_type:
                value = {"score": random.randint(60, 95), "grade": random.choice(["A", "B", "C"])}
            elif "count" in signal_type:
                value = random.randint(0, 50)
            elif "history" in signal_type:
                value = {"incidents": random.randint(0, 3), "last_incident": "2023-06-15"}
            elif "status" in signal_type:
                value = random.choice(["compliant", "partial", "non_compliant"])
            else:
                value = {"status": "active", "score": random.randint(50, 100)}
            
            signal = Signal(
                signal_id=str(uuid.uuid4()),
                entity_id=entity_id,
                signal_type=signal_type,
                signal_name=signal_type.replace("_", " ").title(),
                category=category,
                value=value,
                confidence=random.uniform(0.75, 0.98),
                source=source,
                source_url=f"https://api.{source.lower().replace(' ', '')}.com/v1/{entity_id}",
                extracted_at=now,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
            signals.append(signal)
            logger.info(f"Extracted {signal_type} for {entity_id} from {source}")
        
        return signals


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


class GenericPricingEngine(PricingEngine):
    """
    Generic pricing engine for demonstration.
    
    Production implementations would be coverage-specific.
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
        "fi": {
            "name": "DSI Financial Institutions Model",
            "base_rate": 1800,
            "min_premium": 15000,
            "signal_requirements": [
                "financial_strength", "credit_rating", "regulatory_actions",
                "litigation_history", "compliance_status", "security_rating",
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
# DEMONSTRATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DSI INTEGRATED WORKFLOW DEMONSTRATION")
    print("=" * 70)
    
    # Create workflow with in-memory storage
    workflow = create_workflow("memory")
    
    # Initialize models
    initialize_models(workflow)
    
    print("\n--- Processing Quote Request ---")
    
    # Create request
    request = WorkflowRequest(
        entity_id="acme-tech-001",
        entity_name="Acme Technology Corp",
        coverage_type="cyber",
        limit=5_000_000,
        currency="USD",
        deductible=50_000,
        market="us",
        direct_inquiry={
            "pending_claims": False,
            "pending_regulatory": False,
            "coverage_declined": False,
            "material_change": False,
            "ownership_change": False,
        },
    )
    
    # Process
    response = workflow.process(request)
    
    print(f"\nQuote ID: {response.quote.quote_id}")
    print(f"Entity: {response.quote.entity_name}")
    print(f"Coverage: {response.quote.coverage_type}")
    print(f"Limit: ${response.quote.requested_limit:,.0f}")
    print(f"\nAssessment:")
    print(f"  Composite Score: {response.quote.composite_score}/1000")
    print(f"  Tier: {response.quote.tier_label}")
    print(f"  Confidence: {response.quote.confidence:.1%}")
    print(f"  Signal Coverage: {response.quote.signal_coverage:.1%}")
    print(f"\nPricing:")
    print(f"  Gross Premium: ${response.quote.gross_premium:,.2f}")
    print(f"  Rate/Million: ${response.quote.rate_per_million:,.2f}")
    print(f"  Tier Modifier: {response.quote.tier_modifier}x")
    print(f"\nDecision:")
    print(f"  Path: {response.decision_path}")
    print(f"  Status: {response.quote.status.value}")
    print(f"  Green Flags: {len(response.quote.green_flags)}")
    print(f"  Red Flags: {len(response.quote.red_flags)}")
    print(f"\nPerformance:")
    print(f"  Processing Time: {response.processing_time_ms:.0f}ms")
    print(f"  Model Version: {response.model_version}")
    print(f"  Signals Processed: {response.signal_count}")
    print(f"  Cache Hit Rate: {response.cache_stats.get('hit_rate', 0):.1%}")
    
    # Test requote with higher limit
    print("\n--- Processing Requote (Higher Limit) ---")
    
    requote_response = workflow.requote(
        response.quote.quote_id,
        limit=10_000_000,
    )
    
    print(f"Original Quote: {response.quote.quote_id[:8]}...")
    print(f"Requote ID: {requote_response.quote.quote_id[:8]}...")
    print(f"New Limit: ${requote_response.quote.requested_limit:,.0f}")
    print(f"New Premium: ${requote_response.quote.gross_premium:,.2f}")
    print(f"Cache Hit Rate: {requote_response.cache_stats.get('hit_rate', 0):.1%}")
    
    # Get entity history
    print("\n--- Entity History ---")
    history = workflow.get_entity_history(request.entity_id)
    print(f"Entity: {request.entity_id}")
    print(f"Cached Signals: {history['signal_cache']['cached_signals']}")
    print(f"Total Quotes: {history['quote_count']}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
