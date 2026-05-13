"""
DSI Signal Architecture - Base Classes

This module defines the abstract base classes for the signal processing pipeline:
    BaseExtractor → BaseAggregator → BaseCategorizer

All concrete implementations must inherit from these bases to ensure
consistent interfaces throughout the system.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .types import (
    ExtractorResult,
    AggregatorResult,
    CategorizerResult,
    InferenceContext,
)
from .evidence import EvidenceGrade, EvidenceSource, assert_within_role


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class BaseExtractor(ABC):
    """
    Abstract base class for all Extractors.
    
    Extractors fetch raw data from external sources (APIs, databases, FTP, etc.).
    One extractor CAN serve multiple signals/categorical features.
    
    TTL (Time-To-Live):
        Each extractor defines its DEFAULT_TTL_SECONDS based on how frequently
        the underlying data source changes:
        - Real-time data (prices, positions): 60-300 seconds
        - Regulatory status: 86400 seconds (1 day)
        - Corporate structure: 604800 seconds (1 week)
        - Historical records: 2592000 seconds (30 days)
    
    Implementation Status: STUB
        - Return randomized but structurally realistic data
        - Mimic real API response structures
        - Include metadata (timestamp, source, response time)
    
    When implementing:
        1. Set SOURCE_NAME and DEFAULT_TTL_SECONDS appropriately
        2. Define the source being simulated in docstring
        3. Return data structure matching real API responses
        4. Randomize values within realistic bounds
    
    Example:
        class AllianceMembershipExtractor(BaseExtractor):
            SOURCE_NAME = "iata_alliance_registry"
            DEFAULT_TTL_SECONDS = 86400  # Daily refresh
            
            def extract(self, entity_id: str, context: InferenceContext = None) -> ExtractorResult:
                # Check cache first
                if context:
                    cached = self._get_cached(entity_id, context)
                    if cached:
                        return cached
                
                # Fetch fresh data
                result = self._create_success_result({"alliance_code": "STAR", ...})
                
                # Cache result
                if context:
                    self._cache_result(entity_id, result, context)
                
                return result
    """
    
    # Subclasses should override these
    SOURCE_NAME: str = "unknown"
    SOURCE_VERSION: str = "1.0"
    DEFAULT_TTL_SECONDS: int = 3600  # 1 hour default

    # Common TTL presets (seconds)
    TTL_REALTIME = 60           # 1 minute - for live data
    TTL_FREQUENT = 300          # 5 minutes
    TTL_HOURLY = 3600           # 1 hour
    TTL_DAILY = 86400           # 24 hours
    TTL_WEEKLY = 604800         # 7 days
    TTL_MONTHLY = 2592000       # 30 days

    # V7 Phase 1: per-class evidence cap. Subclasses tighten as needed.
    MAX_EVIDENCE_GRADE: "EvidenceGrade" = "behaviourally_validated"

    # V7 Phase 2: every extractor has now declared an explicit cap (either
    # through inheritance from StubExtractor/ProductionExtractor or by
    # overriding MAX_EVIDENCE_GRADE on the subclass). Enforcement flipped
    # from "warn" to "raise": any extractor that asserts a grade above its
    # declared cap fails loudly.
    _EVIDENCE_ENFORCEMENT_MODE: str = "raise"

    def _check_evidence_role(self, claimed: "EvidenceGrade") -> None:
        """Call from any extractor that asserts a grade on a SignalResult."""
        assert_within_role(
            type(self).__name__,
            self.MAX_EVIDENCE_GRADE,
            claimed,
            mode=self._EVIDENCE_ENFORCEMENT_MODE,  # type: ignore[arg-type]
        )

    @abstractmethod
    def extract(
        self, 
        entity_id: str, 
        context: InferenceContext = None,
        **kwargs
    ) -> ExtractorResult:
        """
        Extract raw data for the given entity.
        
        Args:
            entity_id: Identifier for the entity being assessed
            context: InferenceContext for caching (optional)
            **kwargs: Additional parameters specific to the data source
        
        Returns:
            ExtractorResult containing raw data or error information
        """
        pass
    
    def _cache_key(self, entity_id: str, **kwargs) -> str:
        """
        Generate a cache key for this extraction.
        
        Override for extractors where kwargs affect the result.
        
        Args:
            entity_id: The entity identifier
            **kwargs: Additional parameters that affect the result
        
        Returns:
            Unique cache key string
        """
        return f"{self.SOURCE_NAME}:{entity_id}"
    
    def _get_cached(
        self, 
        entity_id: str, 
        context: InferenceContext,
        **kwargs
    ) -> Optional[ExtractorResult]:
        """
        Check cache for a valid (non-expired) result.
        
        Args:
            entity_id: The entity identifier
            context: InferenceContext containing cache
            **kwargs: Additional parameters for cache key
        
        Returns:
            Cached ExtractorResult if valid, None otherwise
        """
        if context is None:
            return None
        
        cache_key = self._cache_key(entity_id, **kwargs)
        return context.get_cached_extraction(cache_key)
    
    def _cache_result(
        self,
        entity_id: str,
        result: ExtractorResult,
        context: InferenceContext,
        **kwargs
    ) -> None:
        """
        Store result in cache.
        
        Args:
            entity_id: The entity identifier
            result: The ExtractorResult to cache
            context: InferenceContext containing cache
            **kwargs: Additional parameters for cache key
        """
        if context is None or not result.success:
            return
        
        cache_key = self._cache_key(entity_id, **kwargs)
        context.set_cached_extraction(cache_key, result)
    
    def _create_success_result(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> ExtractorResult:
        """
        Helper to create a successful extraction result.
        
        Args:
            data: The extracted data
            metadata: Additional metadata
            ttl_seconds: Override default TTL (optional)
        """
        base_metadata = {
            "source_version": self.SOURCE_VERSION,
            "extractor_class": self.__class__.__name__,
        }
        if metadata:
            base_metadata.update(metadata)
        
        return ExtractorResult(
            success=True,
            data=data,
            source=self.SOURCE_NAME,
            extracted_at=utcnow(),
            ttl_seconds=ttl_seconds or self.DEFAULT_TTL_SECONDS,
            metadata=base_metadata
        )
    
    def _create_error_result(
        self, 
        error: str,
        ttl_seconds: Optional[int] = None
    ) -> ExtractorResult:
        """
        Helper to create a failed extraction result.
        
        Note: Error results can have shorter TTL to retry sooner.
        
        Args:
            error: Error message
            ttl_seconds: TTL for error result (default: 5 minutes)
        """
        return ExtractorResult(
            success=False,
            data={},
            source=self.SOURCE_NAME,
            extracted_at=utcnow(),
            ttl_seconds=ttl_seconds or 300,  # Retry errors after 5 min
            error=error,
            metadata={"extractor_class": self.__class__.__name__}
        )


class BaseAggregator(ABC):
    """
    Abstract base class for all Aggregators.
    
    Aggregators transform raw extractor data into normalized structures
    optimized for scoring/categorization. One aggregator CAN serve
    multiple signals/categorical features.
    
    Implementation Status: PRODUCTION READY
        - Must handle real data when extractors are upgraded
        - Handle missing/malformed data gracefully
        - Include validation and error states
        - Document expected input structure in docstring
    
    When implementing:
        1. Document expected input structure from extractor(s)
        2. Document output structure for categorizer
        3. Handle None/missing values with sensible defaults
        4. Add warnings for data quality issues (don't fail)
    
    Example:
        class AllianceMembershipAggregator(BaseAggregator):
            '''
            Expected input: {"data": {"alliance_code": str, ...}}
            Output: {"has_alliance": bool, "alliance_tier": int, ...}
            '''
            def aggregate(self, results: List[ExtractorResult]) -> AggregatorResult:
                ...
    """
    
    @abstractmethod
    def aggregate(
        self,
        extractor_results: List[ExtractorResult],
        **kwargs
    ) -> AggregatorResult:
        """
        Aggregate and normalize extractor results.

        Args:
            extractor_results: List of ExtractorResult from one or more extractors
            **kwargs: Additional parameters for aggregation logic

        Returns:
            AggregatorResult containing normalized data or error information
        """
        pass

    def aggregate_evidence(
        self,
        contributing: "Sequence[SignalResult]",
    ) -> "Tuple[Optional[EvidenceGrade], List[EvidenceSource]]":
        """V7 Phase 1 stub. Returns (None, []).

        Phase 3 supplies the real implementation: promotion-merge over the
        contributing signals, with role-bound producer roles respected.
        Kept here so aggregator subclasses can call it from Phase 1 without
        knowing whether Phase 3 has landed.
        """
        return None, []

    def _create_success_result(
        self,
        data: Dict[str, Any],
        source_count: int = 1,
        warnings: Optional[List[str]] = None
    ) -> AggregatorResult:
        """Helper to create a successful aggregation result."""
        return AggregatorResult(
            success=True,
            data=data,
            aggregated_at=utcnow(),
            source_extractions=source_count,
            warnings=warnings or []
        )
    
    def _create_error_result(self, error: str) -> AggregatorResult:
        """Helper to create a failed aggregation result."""
        return AggregatorResult(
            success=False,
            data={},
            aggregated_at=utcnow(),
            error=error
        )
    
    def _safe_get(
        self,
        data: Dict[str, Any],
        *keys: str,
        default: Any = None
    ) -> Any:
        """
        Safely navigate nested dictionaries.
        
        Args:
            data: The dictionary to navigate
            *keys: Sequence of keys to traverse
            default: Value to return if path doesn't exist
        
        Returns:
            The value at the path, or default if not found
        
        Example:
            value = self._safe_get(data, "response", "items", 0, "name")
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
                if current is default:
                    return default
            elif isinstance(current, (list, tuple)) and isinstance(key, int):
                try:
                    current = current[key]
                except IndexError:
                    return default
            else:
                return default
        return current


class BaseCategorizer(ABC):
    """
    Abstract base class for all Categorizers.
    
    Categorizers apply scoring/categorization logic to produce final values.
    Categorizer TYPES are reusable across many signals (e.g., ThresholdBucketCategorizer).
    
    Implementation Status: PRODUCTION READY
        - Parameterized logic, not signal-specific
        - Deterministic given same inputs
        - Return score (0-100) OR category string
    
    When implementing:
        1. Make the categorizer generic/reusable
        2. Accept parameters via params dict, not hardcoded
        3. Document expected aggregated_data structure
        4. Document params schema
    
    Example:
        class ThresholdBucketCategorizer(BaseCategorizer):
            '''
            Params: {
                "value_field": str,
                "buckets": [{"max": float, "score": float}, ...]
            }
            '''
            def categorize(self, data: dict, params: dict) -> CategorizerResult:
                ...
    """
    
    @abstractmethod
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """
        Apply categorization logic to aggregated data.
        
        Args:
            aggregated_data: Normalized data from an aggregator
            params: Configuration parameters for the categorization logic
        
        Returns:
            CategorizerResult with score (0-100) or category string
        """
        pass
    
    def _create_score_result(
        self,
        score: float,
        confidence: float = 1.0,
        reasoning: Optional[str] = None
    ) -> CategorizerResult:
        """Helper to create a score-based result."""
        # Clamp score to valid range
        clamped_score = max(0, min(100, score))
        return CategorizerResult(
            score=clamped_score,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _create_category_result(
        self,
        category: str,
        confidence: float = 1.0,
        reasoning: Optional[str] = None
    ) -> CategorizerResult:
        """Helper to create a category-based result."""
        return CategorizerResult(
            category=category,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _create_error_result(self, error: str) -> CategorizerResult:
        """Helper to create a failed categorization result."""
        return CategorizerResult(
            score=50,  # Neutral fallback score
            confidence=0.0,
            error=error
        )
    
    def _create_skipped_result(self, reasoning: str = None) -> CategorizerResult:
        """Helper to create a skipped categorization result (not applicable)."""
        return CategorizerResult(
            skipped=True,
            confidence=0.0,
            reasoning=reasoning or "Not applicable"
        )


class BaseInferenceFunction(ABC):
    """
    Abstract base class for Inference Functions.
    
    Inference functions orchestrate the full pipeline for ONE specific signal
    or categorical feature: Extractor(s) → Aggregator(s) → Categorizer.
    
    Implementation Status: PRODUCTION READY
        - One inference function per `inference_utility_function` in YAML
        - Handle errors gracefully with fallback scores
        - Return complete SignalResult with audit trail
    
    Note: Inference functions can also be implemented as standalone functions
    rather than classes. This base class is provided for cases where
    stateful behavior or shared utilities are needed.
    
    When implementing:
        1. Document which YAML signal/categorical feature this serves
        2. Specify which extractor(s), aggregator(s), categorizer(s) are used
        3. Handle extraction/aggregation failures with neutral scores
        4. Include full audit trail in metadata
    """
    
    # Subclasses should override these
    SIGNAL_ID: str = "unknown"
    
    @abstractmethod
    def __call__(
        self,
        entity_id: str,
        context: InferenceContext
    ) -> 'SignalResult':
        """
        Execute the inference pipeline.
        
        Args:
            entity_id: Identifier for the entity being assessed
            context: InferenceContext with config and cache
        
        Returns:
            SignalResult with score/category and full audit trail
        """
        pass


# Type alias for inference functions (can be class or function)
from typing import Callable, Union
from .types import SignalResult

InferenceFunction = Union[
    BaseInferenceFunction,
    Callable[[str, InferenceContext], SignalResult]
]
