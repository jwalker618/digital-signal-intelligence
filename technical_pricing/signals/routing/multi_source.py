"""
Multi-Source Aggregator

Orchestrates calling multiple extractors for a signal type and consolidates
their results into a unified output schema.

This solves the problem of:
1. Which extractors to call (via JurisdictionRouter)
2. How to call them efficiently (parallel execution)
3. How to merge results (source-attributed consolidation)
4. How to handle variance (normalization to common schema)
5. How to cache results (TTL-aware caching at routing level)
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from .router import JurisdictionRouter, RoutingStrategy
from .schemas import RiskLevel

logger = logging.getLogger(__name__)


# =============================================================================
# Routing-Level Cache
# =============================================================================

@dataclass
class CachedResult:
    """A cached extraction result with TTL."""
    data: Dict[str, Any]
    cached_at: datetime
    expires_at: datetime
    cache_key: str

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Check if this cached result has expired."""
        now = now or datetime.utcnow()
        return now >= self.expires_at


class RoutingCache:
    """
    Thread-safe cache for routing-level extraction results.

    Provides TTL-based caching to avoid redundant extractor calls
    when the same entity is queried multiple times within a short window.

    Usage:
        cache = RoutingCache(default_ttl_seconds=300)

        # Check cache
        cached = cache.get('opensanctions', 'Acme Corp')
        if cached:
            return cached.data

        # Store in cache
        cache.set('opensanctions', 'Acme Corp', result_data, ttl_seconds=600)
    """

    def __init__(
        self,
        default_ttl_seconds: int = 300,  # 5 minutes default
        max_entries: int = 10000,
    ):
        """
        Initialize the cache.

        Args:
            default_ttl_seconds: Default TTL for cached entries
            max_entries: Maximum cache entries before cleanup
        """
        self.default_ttl_seconds = default_ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, CachedResult] = {}
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'stores': 0,
            'evictions': 0,
        }

    def _make_key(self, extractor_name: str, entity_id: str) -> str:
        """Create a cache key from extractor and entity."""
        combined = f"{extractor_name}:{entity_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def get(
        self,
        extractor_name: str,
        entity_id: str,
    ) -> Optional[CachedResult]:
        """
        Get a cached result if available and not expired.

        Args:
            extractor_name: Name of the extractor
            entity_id: Entity identifier

        Returns:
            CachedResult if found and valid, None otherwise
        """
        key = self._make_key(extractor_name, entity_id)

        with self._lock:
            cached = self._cache.get(key)
            if cached is None:
                self._stats['misses'] += 1
                return None

            if cached.is_expired():
                del self._cache[key]
                self._stats['expired'] += 1
                return None

            self._stats['hits'] += 1
            return cached

    def set(
        self,
        extractor_name: str,
        entity_id: str,
        data: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Store a result in the cache.

        Args:
            extractor_name: Name of the extractor
            entity_id: Entity identifier
            data: Data to cache
            ttl_seconds: Optional custom TTL
        """
        key = self._make_key(extractor_name, entity_id)
        ttl = ttl_seconds or self.default_ttl_seconds
        now = datetime.utcnow()

        cached_result = CachedResult(
            data=data,
            cached_at=now,
            expires_at=now + timedelta(seconds=ttl),
            cache_key=key,
        )

        with self._lock:
            # Cleanup if approaching max entries
            if len(self._cache) >= self.max_entries:
                self._cleanup_expired()

            self._cache[key] = cached_result
            self._stats['stores'] += 1

    def _cleanup_expired(self) -> int:
        """Remove expired entries. Must be called with lock held."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, cached in self._cache.items()
            if cached.is_expired(now)
        ]
        for key in expired_keys:
            del self._cache[key]
            self._stats['evictions'] += 1
        return len(expired_keys)

    def invalidate(
        self,
        extractor_name: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            extractor_name: If provided with entity_id, invalidate that specific entry
            entity_id: If provided with extractor_name, invalidate that specific entry

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if extractor_name and entity_id:
                key = self._make_key(extractor_name, entity_id)
                if key in self._cache:
                    del self._cache[key]
                    return 1
                return 0
            else:
                count = len(self._cache)
                self._cache.clear()
                return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            stats = dict(self._stats)
            stats['current_entries'] = len(self._cache)
            total_requests = stats['hits'] + stats['misses'] + stats['expired']
            stats['hit_rate'] = stats['hits'] / total_requests if total_requests > 0 else 0.0
            return stats


# Global routing cache singleton
_routing_cache: Optional[RoutingCache] = None


def get_routing_cache() -> RoutingCache:
    """Get the global routing cache instance."""
    global _routing_cache
    if _routing_cache is None:
        _routing_cache = RoutingCache()
    return _routing_cache


def set_routing_cache(cache: RoutingCache) -> None:
    """Set a custom routing cache (useful for testing)."""
    global _routing_cache
    _routing_cache = cache

# Generic type for result schema
T = TypeVar('T')


@dataclass
class ExtractorCallResult:
    """Result from calling a single extractor."""
    extractor_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    from_cache: bool = False


@dataclass
class MultiSourceResult(Generic[T]):
    """
    Result from a multi-source aggregation.

    Contains both the unified result (T) and metadata about the extraction.
    """
    # The unified result in the target schema
    result: T

    # Extraction metadata
    extractors_called: List[str] = field(default_factory=list)
    extractors_succeeded: List[str] = field(default_factory=list)
    extractors_failed: List[str] = field(default_factory=list)

    # Performance
    total_time_ms: float = 0.0
    parallel_execution: bool = True

    # Per-extractor details
    extractor_results: Dict[str, ExtractorCallResult] = field(default_factory=dict)

    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MultiSourceAggregator(ABC, Generic[T]):
    """
    Base class for multi-source signal aggregation.

    Subclasses implement:
    - get_extractor_func(): Returns function to get extractor by name
    - normalize_result(): Converts extractor output to match items
    - create_unified_result(): Creates final unified result from all matches

    Usage:
        class SanctionsAggregator(MultiSourceAggregator[SanctionsResult]):
            def normalize_result(self, extractor_name, data) -> List[SanctionsMatch]:
                # Convert opensanctions format to SanctionsMatch
                # Convert uk_ofsi format to SanctionsMatch
                # etc.
                ...

        aggregator = SanctionsAggregator()
        result = aggregator.aggregate(
            entity_id='Acme Corp',
            signal_type='sanctions',
            locale='UK'
        )
    """

    def __init__(
        self,
        router: Optional[JurisdictionRouter] = None,
        max_workers: int = 10,
        timeout_seconds: float = 30.0,
        default_strategy: RoutingStrategy = RoutingStrategy.LOCALE_PLUS_GLOBAL,
        cache: Optional[RoutingCache] = None,
        use_cache: bool = True,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize the aggregator.

        Args:
            router: Jurisdiction router (creates default if None)
            max_workers: Max parallel extractor calls
            timeout_seconds: Timeout per extractor call
            default_strategy: Default routing strategy
            cache: Optional routing cache (uses global if None)
            use_cache: Whether to use caching (default True)
            cache_ttl_seconds: TTL for cached results
        """
        self.router = router or JurisdictionRouter()
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.default_strategy = default_strategy
        self.cache = cache
        self.use_cache = use_cache
        self.cache_ttl_seconds = cache_ttl_seconds

    @abstractmethod
    def get_extractor_func(self) -> Callable[[str], Any]:
        """
        Return a function that gets an extractor by name.

        Example:
            return lambda name: get_extractor(name, mode='production')
        """
        pass

    @abstractmethod
    def normalize_result(
        self,
        extractor_name: str,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[Any]:
        """
        Normalize extractor output to a list of match items.

        Args:
            extractor_name: Name of the extractor
            raw_data: Raw data from extractor
            entity_id: Entity being searched

        Returns:
            List of normalized match items (type depends on signal)
        """
        pass

    @abstractmethod
    def create_unified_result(
        self,
        entity_id: str,
        all_matches: List[Any],
        sources_checked: List[str],
        sources_with_matches: List[str],
        failed_sources: List[str],
        warnings: List[str],
        check_duration_ms: float,
    ) -> T:
        """
        Create the unified result from all normalized matches.

        Args:
            entity_id: Entity that was searched
            all_matches: All normalized matches from all sources
            sources_checked: List of extractors that were called
            sources_with_matches: Extractors that returned matches
            failed_sources: Extractors that failed
            warnings: Warning messages
            check_duration_ms: Total check duration

        Returns:
            Unified result in the target schema
        """
        pass

    def _get_cache(self) -> Optional[RoutingCache]:
        """Get the cache to use (instance cache or global)."""
        if not self.use_cache:
            return None
        return self.cache or get_routing_cache()

    def _call_extractor(
        self,
        extractor_name: str,
        entity_id: str,
        get_extractor: Callable,
    ) -> ExtractorCallResult:
        """Call a single extractor and return the result."""
        start_time = time.time()

        # Check cache first
        cache = self._get_cache()
        if cache:
            cached = cache.get(extractor_name, entity_id)
            if cached:
                logger.debug(f"Cache hit for {extractor_name}:{entity_id}")
                return ExtractorCallResult(
                    extractor_name=extractor_name,
                    success=True,
                    data=cached.data,
                    from_cache=True,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

        try:
            extractor = get_extractor(extractor_name)
            if extractor is None:
                return ExtractorCallResult(
                    extractor_name=extractor_name,
                    success=False,
                    error=f"Extractor not found: {extractor_name}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            result = extractor.extract(entity_id)

            # Get result data
            success = result.success if hasattr(result, 'success') else True
            data = result.data if hasattr(result, 'data') else result

            # Store in cache if successful
            if success and cache and data:
                cache.set(
                    extractor_name,
                    entity_id,
                    data,
                    ttl_seconds=self.cache_ttl_seconds,
                )

            return ExtractorCallResult(
                extractor_name=extractor_name,
                success=success,
                data=data,
                from_cache=result.from_cache if hasattr(result, 'from_cache') else False,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Extractor {extractor_name} failed: {e}")
            return ExtractorCallResult(
                extractor_name=extractor_name,
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def aggregate(
        self,
        entity_id: str,
        signal_type: str,
        locale: Optional[str] = None,
        domain: Optional[str] = None,
        strategy: Optional[RoutingStrategy] = None,
        parallel: bool = True,
    ) -> MultiSourceResult[T]:
        """
        Aggregate results from multiple extractors.

        Args:
            entity_id: Entity to search (name, domain, ID, etc.)
            signal_type: Type of signal (sanctions, corporate, etc.)
            locale: Explicit locale code
            domain: Domain for locale detection
            strategy: Routing strategy (uses default if None)
            parallel: Execute extractors in parallel

        Returns:
            MultiSourceResult containing unified result and metadata
        """
        start_time = time.time()
        strategy = strategy or self.default_strategy

        # Get extractors to call
        extractors = self.router.get_extractors(
            signal_type=signal_type,
            locale=locale,
            domain=domain,
            strategy=strategy,
        )

        if not extractors:
            logger.warning(f"No extractors found for {signal_type} in {locale}")
            empty_result = self.create_unified_result(
                entity_id=entity_id,
                all_matches=[],
                sources_checked=[],
                sources_with_matches=[],
                failed_sources=[],
                warnings=[f"No extractors configured for signal_type={signal_type}, locale={locale}"],
                check_duration_ms=0.0,
            )
            return MultiSourceResult(
                result=empty_result,
                warnings=["No extractors found"],
            )

        # Get extractor function
        get_extractor = self.get_extractor_func()

        # Call extractors
        extractor_results: Dict[str, ExtractorCallResult] = {}

        if parallel and len(extractors) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(extractors))) as executor:
                futures = {
                    executor.submit(
                        self._call_extractor,
                        ext_name,
                        entity_id,
                        get_extractor,
                    ): ext_name
                    for ext_name in extractors
                }

                for future in as_completed(futures, timeout=self.timeout_seconds):
                    ext_name = futures[future]
                    try:
                        result = future.result()
                        extractor_results[ext_name] = result
                    except Exception as e:
                        extractor_results[ext_name] = ExtractorCallResult(
                            extractor_name=ext_name,
                            success=False,
                            error=f"Future error: {e}",
                        )
        else:
            # Sequential execution
            for ext_name in extractors:
                extractor_results[ext_name] = self._call_extractor(
                    ext_name, entity_id, get_extractor
                )

        # Process results
        all_matches: List[Any] = []
        sources_checked: List[str] = list(extractors)
        sources_with_matches: List[str] = []
        failed_sources: List[str] = []
        warnings: List[str] = []

        for ext_name, ext_result in extractor_results.items():
            if not ext_result.success:
                failed_sources.append(ext_name)
                if ext_result.error:
                    warnings.append(f"{ext_name}: {ext_result.error}")
                continue

            # Normalize the result
            try:
                matches = self.normalize_result(
                    extractor_name=ext_name,
                    raw_data=ext_result.data,
                    entity_id=entity_id,
                )
                if matches:
                    all_matches.extend(matches)
                    sources_with_matches.append(ext_name)
            except Exception as e:
                logger.error(f"Failed to normalize {ext_name} result: {e}")
                warnings.append(f"Normalization failed for {ext_name}: {e}")

        # Create unified result
        total_time_ms = (time.time() - start_time) * 1000
        unified_result = self.create_unified_result(
            entity_id=entity_id,
            all_matches=all_matches,
            sources_checked=sources_checked,
            sources_with_matches=sources_with_matches,
            failed_sources=failed_sources,
            warnings=warnings,
            check_duration_ms=total_time_ms,
        )

        return MultiSourceResult(
            result=unified_result,
            extractors_called=sources_checked,
            extractors_succeeded=[e for e in sources_checked if e not in failed_sources],
            extractors_failed=failed_sources,
            total_time_ms=total_time_ms,
            parallel_execution=parallel and len(extractors) > 1,
            extractor_results=extractor_results,
            errors=[w for w in warnings if "failed" in w.lower() or "error" in w.lower()],
            warnings=[w for w in warnings if "failed" not in w.lower() and "error" not in w.lower()],
        )


def calculate_risk_level(
    matches: List[Any],
    sources_with_matches: List[str],
    high_confidence_threshold: float = 90.0,
    medium_confidence_threshold: float = 70.0,
) -> RiskLevel:
    """
    Calculate risk level from matches.

    Args:
        matches: List of match objects with match_score attribute
        sources_with_matches: List of sources that found matches
        high_confidence_threshold: Score threshold for HIGH risk
        medium_confidence_threshold: Score threshold for MEDIUM risk

    Returns:
        RiskLevel enum value
    """
    if not matches:
        return RiskLevel.CLEAR

    # Get highest match score
    max_score = max(
        (getattr(m, 'match_score', 0) for m in matches),
        default=0
    )

    # Multiple sources finding matches is concerning
    multi_source = len(sources_with_matches) > 1

    if max_score >= high_confidence_threshold:
        return RiskLevel.CRITICAL if multi_source else RiskLevel.HIGH
    elif max_score >= medium_confidence_threshold:
        return RiskLevel.HIGH if multi_source else RiskLevel.MEDIUM
    elif max_score >= 50:
        return RiskLevel.MEDIUM if multi_source else RiskLevel.LOW
    else:
        return RiskLevel.LOW
