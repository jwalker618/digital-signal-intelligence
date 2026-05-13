"""
DSI Signal Architecture - Core Data Types

This module defines the data structures used throughout the signal processing pipeline:
    Extractor → Aggregator → Categorizer → Inference

All components use these standardized types to ensure consistent data flow.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from .evidence import EvidenceGrade, EvidenceSource


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class SignalType(Enum):
    """Classification of signal types per DSI principles."""
    NETWORK_AUTHORITY = "network_authority"
    TECHNICAL_INFRASTRUCTURE = "technical_infrastructure"
    ASSET_TELEMETRY = "asset_telemetry"
    STRUCTURED_DATA_FEED = "structured_data_feed"
    CORPORATE_DIGITAL_FOOTPRINT = "corporate_digital_footprint"
    PUBLIC_RECORD = "public_record"
    DIRECT_INQUIRY = "direct_inquiry"


class OverrideAction(Enum):
    """Actions triggered by score_condition bands."""
    NONE = "NONE"
    REFER = "REFER"
    DECLINE = "DECLINE"
    MODIFIER = "MODIFIER"


@dataclass
class ExtractorResult:
    """
    Output from an Extractor.
    
    Extractors fetch raw data from external sources (APIs, databases, FTP).
    The data field contains the raw response structure mimicking real sources.
    
    Attributes:
        success: Whether the extraction completed without errors
        data: Raw data from the source (structure varies by extractor)
        source: Identifier for the data source (e.g., "iata_alliance_registry")
        extracted_at: Timestamp of extraction
        ttl_seconds: Time-to-live in seconds (how long this result remains valid)
        expires_at: Computed expiration timestamp (extracted_at + ttl_seconds)
        error: Error message if success is False
        metadata: Additional context (response time, API version, etc.)
        from_cache: Whether this result was retrieved from cache
    """
    success: bool
    data: Dict[str, Any]
    source: str
    extracted_at: datetime
    ttl_seconds: int = 3600  # Default 1 hour
    expires_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    from_cache: bool = False
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Compute expires_at if not provided
        if self.expires_at is None and self.extracted_at:
            from datetime import timedelta
            self.expires_at = self.extracted_at + timedelta(seconds=self.ttl_seconds)
    
    def is_expired(self, reference_time: Optional[datetime] = None) -> bool:
        """
        Check if this result has expired.
        
        Args:
            reference_time: Time to check against (default: now)
        
        Returns:
            True if the result has expired and should be refreshed
        """
        if self.expires_at is None:
            return False
        
        if reference_time is None:
            reference_time = utcnow()
        
        return reference_time >= self.expires_at
    
    def time_until_expiry(self, reference_time: Optional[datetime] = None) -> Optional[timedelta]:
        """
        Get time remaining until this result expires.
        
        Returns:
            timedelta until expiry, or None if already expired or no expiry set
        """
        if self.expires_at is None:
            return None
        
        if reference_time is None:
            reference_time = utcnow()
        
        remaining = self.expires_at - reference_time
        if remaining.total_seconds() < 0:
            return None
        
        return remaining


@dataclass
class AggregatorResult:
    """
    Output from an Aggregator.
    
    Aggregators transform raw extractor data into normalized structures
    optimized for scoring/categorization.
    
    Attributes:
        success: Whether aggregation completed without errors
        data: Normalized, structured data ready for categorizer
        aggregated_at: Timestamp of aggregation
        error: Error message if success is False
        source_extractions: Count of extractor results processed
        sources: List of source names that contributed data
        warnings: Non-fatal issues encountered during aggregation
    """
    success: bool
    data: Dict[str, Any]
    aggregated_at: datetime
    error: Optional[str] = None
    source_extractions: int = 1
    sources: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.sources is None:
            self.sources = []


@dataclass
class CategorizerResult:
    """
    Output from a Categorizer.
    
    Categorizers apply scoring/categorization logic to produce final values.
    Returns EITHER a score (0-100) for signal features OR a category string
    for categorical features.
    
    Attributes:
        score: Numeric score 0-100 (for signal features)
        category: Category string (for categorical features, e.g., "MAJOR_AIRLINE")
        confidence: Confidence level 0-1 based on data completeness
        error: Error message if categorization failed
        reasoning: Optional explanation of scoring logic applied
        skipped: Whether categorization was skipped (not applicable)
    """
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    reasoning: Optional[str] = None
    skipped: bool = False
    
    def __post_init__(self):
        # Validate that we have either score, category, error, or skipped
        if not self.skipped and self.error is None and self.score is None and self.category is None:
            raise ValueError("CategorizerResult must have score, category, error, or be skipped")
        
        # Validate score range
        if self.score is not None and not (0 <= self.score <= 100):
            raise ValueError(f"Score must be between 0 and 100, got {self.score}")
        
        # Validate confidence range
        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    @property
    def is_valid(self) -> bool:
        """Check if result has a valid score or category."""
        return (self.score is not None or self.category is not None) and self.error is None


@dataclass
class SignalResult:
    """
    Output from an Inference function.
    
    Inference functions orchestrate the full pipeline for ONE specific signal
    or categorical feature: Extractor(s) → Aggregator(s) → Categorizer.
    
    Attributes:
        signal_id: Identifier matching the YAML config (e.g., "alliance_membership")
        score: Final score 0-100 (for signal features)
        category: Final category (for categorical features)
        confidence: Overall confidence 0-1
        raw_data: Original extractor output (for audit trail)
        aggregated_data: Aggregator output (for audit trail)
        metadata: Pipeline metadata (which components were used)
        error: Error message if pipeline failed
        execution_time_ms: Time taken to execute pipeline (milliseconds)
        skipped: Whether this signal was skipped (not applicable)
    """
    signal_id: str
    score: Optional[float] = None
    category: Optional[str] = None
    confidence: float = 1.0
    raw_data: Optional[Dict[str, Any]] = None
    aggregated_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    skipped: bool = False

    # --- V7 Phase 1: evidence fields. Optional during migration. ---
    # Phase 2 populates them in every extractor.
    # Phase 6 tightens `evidence_grade` and `evidence_basis` to required.
    evidence_grade: Optional[EvidenceGrade] = None
    evidence_basis: Optional[str] = None
    evidence_sources: List[EvidenceSource] = field(default_factory=list)

    # Adversarial validation (populated by Phase 6).
    evidence_pro: Optional[str] = None
    evidence_counter: Optional[str] = None
    evidence_tie_breaker: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # Validate score range if present
        if self.score is not None and not (0 <= self.score <= 100):
            raise ValueError(f"Score must be between 0 and 100, got {self.score}")

        # V7 Phase 1: validate evidence_basis length only if present.
        if self.evidence_basis is not None and len(self.evidence_basis) > 500:
            raise ValueError(
                f"evidence_basis must be <=500 chars, got {len(self.evidence_basis)}"
            )
        if self.evidence_basis is not None and len(self.evidence_basis) == 0:
            raise ValueError("evidence_basis must be non-empty if present")
    
    @property
    def is_valid(self) -> bool:
        """Check if result has a valid score or category."""
        return (self.score is not None or self.category is not None) and self.error is None
    
    @property
    def is_error(self) -> bool:
        """Check if result represents an error state."""
        return self.error is not None


@dataclass
class Override:
    """
    Represents a triggered score_condition band override.
    
    When a signal or group score falls within a band defined in the YAML config,
    an override action may be triggered (REFER, DECLINE, tier override, etc.).
    """
    source_type: str  # "signal_feature", "signal_group", "direct_query"
    source_id: str  # e.g., "accident_history", "safety_record"
    score: float
    band_max: float
    tier_override: Optional[int] = None
    action: OverrideAction = OverrideAction.NONE
    modifier: Optional[float] = None
    note: Optional[str] = None


@dataclass
class CategoricalResult:
    """
    Result of categorical feature inference.
    
    Categorical features (e.g., operator_type, fleet_size) produce a category
    that maps to a modifier in the YAML config.
    """
    group_id: str  # e.g., "operator_type"
    category: str  # e.g., "MAJOR_AIRLINE"
    modifier: float  # e.g., 0.85
    confidence: float = 1.0
    error: Optional[str] = None


@dataclass
class ModelResult:
    """
    Complete output from a DSI model run.
    
    This is the final result of processing an entity through a complete
    coverage configuration (e.g., aerospace_general).
    
    Attributes:
        entity_id: The entity being assessed
        configuration: The config used (e.g., "aerospace_general")
        composite_score: Weighted composite 0-1000
        tier: Risk tier 1-5
        tier_label: Tier name (e.g., "PREFERRED", "STANDARD")
        signal_results: Individual signal scores by group and feature
        categorical_results: Category assignments and modifiers
        modifiers: All applied modifiers (categorical + direct query)
        base_premium: Premium from tier before modifiers
        final_premium: Premium after all modifiers applied
        confidence: Overall confidence based on signal availability
        overrides: Any triggered score_condition bands
        direct_query_responses: Responses to optional direct queries
        timestamp: When the model was run
        auto_approve: Whether this tier allows auto-approval
        auto_decline: Whether this tier triggers auto-decline
        referral_reasons: List of reasons requiring referral
    """
    entity_id: str
    configuration: str
    composite_score: float
    tier: int
    tier_label: str
    signal_results: Dict[str, Dict[str, SignalResult]]  # group_id -> signal_id -> result
    categorical_results: Dict[str, CategoricalResult]
    modifiers: Dict[str, float]
    base_premium: float
    final_premium: float
    confidence: float
    overrides: List[Override]
    timestamp: datetime
    direct_query_responses: Optional[Dict[str, bool]] = None
    auto_approve: bool = False
    auto_decline: bool = False
    referral_reasons: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.referral_reasons is None:
            self.referral_reasons = []
        if self.direct_query_responses is None:
            self.direct_query_responses = {}
        
        # Validate composite score range
        if not (0 <= self.composite_score <= 1000):
            raise ValueError(f"Composite score must be between 0 and 1000, got {self.composite_score}")
        
        # Validate tier range
        if not (1 <= self.tier <= 5):
            raise ValueError(f"Tier must be between 1 and 5, got {self.tier}")


@dataclass
class InferenceContext:
    """
    Context passed to inference functions.

    Provides access to configuration and shared resources needed
    during signal processing, including TTL-aware caching and discovery data.

    Attributes:
        configuration: The full parsed YAML configuration
        coverage: Coverage domain (e.g., "aerospace")
        config_name: Configuration name (e.g., "aerospace_general")
        cache: Cache for extractor results (avoids duplicate API calls within TTL)
        cache_stats: Statistics on cache hits/misses

        Discovery context (populated by Step 0):
        discovered_website: The discovered corporate website URL
        discovered_domain: The domain extracted from the website
        corporate_identity: Corporate identity info from discovery
        discovery_confidence: Confidence level from discovery (0.0-1.0)
        discovery_method: How the website was discovered
        discovery_warnings: Any warnings from the discovery process

        Locale context (for jurisdiction-aware routing):
        entity_locale: ISO country code for entity jurisdiction (e.g., 'UK', 'US', 'DE')
        entity_country: Full country name (e.g., 'United Kingdom')
        locale_source: How locale was determined ('submission', 'discovery', 'default')
    """
    configuration: Dict[str, Any]
    coverage: str
    config_name: str
    cache: Optional[Dict[str, ExtractorResult]] = None
    cache_stats: Optional[Dict[str, int]] = None

    # Discovery context (populated by Step 0)
    discovered_website: Optional[str] = None
    discovered_domain: Optional[str] = None
    corporate_identity: Optional[Dict[str, Any]] = None
    discovery_confidence: float = 1.0
    discovery_method: Optional[str] = None
    discovery_warnings: Optional[List[str]] = None

    # Locale context (for jurisdiction-aware routing)
    entity_locale: Optional[str] = None
    entity_country: Optional[str] = None
    locale_source: Optional[str] = None
    
    def __post_init__(self):
        if self.cache is None:
            self.cache = {}
        if self.cache_stats is None:
            self.cache_stats = {"hits": 0, "misses": 0, "expired": 0, "stores": 0}
        if self.discovery_warnings is None:
            self.discovery_warnings = []
    
    def get_cached_extraction(
        self, 
        cache_key: str,
        respect_ttl: bool = True
    ) -> Optional[ExtractorResult]:
        """
        Retrieve a cached extractor result if available and not expired.
        
        Args:
            cache_key: Unique key for this extraction (typically source:entity_id)
            respect_ttl: If True, return None for expired results
        
        Returns:
            Cached ExtractorResult if valid, None otherwise
        """
        cached = self.cache.get(cache_key)
        
        if cached is None:
            self.cache_stats["misses"] += 1
            return None
        
        if respect_ttl and cached.is_expired():
            self.cache_stats["expired"] += 1
            # Optionally remove expired entry
            del self.cache[cache_key]
            return None
        
        self.cache_stats["hits"] += 1
        # Mark as from cache for audit trail
        cached.from_cache = True
        return cached
    
    def set_cached_extraction(
        self, 
        cache_key: str, 
        result: ExtractorResult
    ) -> None:
        """
        Cache an extractor result for reuse within its TTL.
        
        Args:
            cache_key: Unique key for this extraction
            result: The ExtractorResult to cache
        """
        self.cache[cache_key] = result
        self.cache_stats["stores"] += 1
    
    def invalidate_cache(self, cache_key: str = None) -> int:
        """
        Invalidate cached entries.
        
        Args:
            cache_key: Specific key to invalidate, or None for all
        
        Returns:
            Number of entries invalidated
        """
        if cache_key:
            if cache_key in self.cache:
                del self.cache[cache_key]
                return 1
            return 0
        else:
            count = len(self.cache)
            self.cache.clear()
            return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, result in self.cache.items() 
            if result.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, expired, stores, and hit_rate
        """
        stats = dict(self.cache_stats)
        total_requests = stats["hits"] + stats["misses"] + stats["expired"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0.0
        stats["current_entries"] = len(self.cache)
        return stats
