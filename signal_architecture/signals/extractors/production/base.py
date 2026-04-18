"""
DSI Signal Architecture - Production Extractor Base

This module provides the base class for production extractors that connect
to real external data sources.

Key differences from StubExtractor:
    - No random data generation
    - Real API/database connections
    - Proper error handling and retry logic
    - Rate limiting support
    - Detailed logging
    - Kill-switch env var per extractor (V6/D1)
    - OpenTelemetry span per extraction (V6/C3)
"""

import logging
import os
import time
from abc import abstractmethod
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from ..base import BaseExtractor
from ...types import ExtractorResult, InferenceContext

logger = logging.getLogger(__name__)


COST_TIER_RANK = {"free": 0, "low": 1, "medium": 2, "high": 3}


class _NullCM:
    """No-op context manager used when OTel is unavailable."""

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False

T = TypeVar('T')


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
) -> Callable:
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exception types to retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.1f}s: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


class ProductionExtractor(BaseExtractor):
    """
    Base class for production extractors.

    Extends BaseExtractor with production-specific features:
        - Real data source connections
        - Rate limiting
        - Retry logic with exponential backoff
        - Detailed error handling
        - Metrics collection

    Subclasses must implement:
        - _do_extract(): The actual data fetching logic
        - get_required_config(): List of required config keys

    Example:
        class EmailAuthExtractor(ProductionExtractor):
            SOURCE_NAME = "dns_txt_records"
            DEFAULT_TTL_SECONDS = 3600
            RATE_LIMIT = 10.0  # 10 requests per second

            def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
                domain = self._normalize_domain(entity_id)
                spf = self._query_spf(domain)
                dmarc = self._query_dmarc(domain)
                dkim = self._query_dkim(domain)
                return self._create_success_result({
                    'spf': spf,
                    'dmarc': dmarc,
                    'dkim': dkim,
                })

            def get_required_config(self) -> List[str]:
                return []  # No API key needed for DNS
    """

    # Subclasses should override these
    SOURCE_NAME: str = "unknown"
    SOURCE_VERSION: str = "1.0"
    DEFAULT_TTL_SECONDS: int = 3600
    RATE_LIMIT: float = 1.0  # Requests per second
    MAX_RETRIES: int = 3

    # Cost tier for documentation/budgeting
    COST_TIER: str = "free"  # 'free', 'low', 'medium', 'high'

    # V6 (D1): kill-switch env var. When set to a truthy value the extractor
    # short-circuits to a neutral "absence-as-signal" result so ops can shed
    # a broken / noisy / expensive source without a deploy. Subclasses that
    # want a kill-switch override this.
    KILL_SWITCH_ENV: Optional[str] = None

    # V6 (D1): environment variable carrying the API key, when applicable.
    # If set but the env var is unset, extract() returns a neutral-absence
    # result instead of raising, matching the "framework runs without
    # paid sources" principle.
    API_KEY_ENV: Optional[str] = None

    @classmethod
    def cost_tier_rank(cls) -> int:
        return COST_TIER_RANK.get(cls.COST_TIER, 99)

    @classmethod
    def is_disabled(cls) -> bool:
        if not cls.KILL_SWITCH_ENV:
            return False
        return os.environ.get(cls.KILL_SWITCH_ENV, "").strip().lower() in (
            "1", "true", "yes", "on",
        )

    @classmethod
    def has_api_key(cls) -> bool:
        if not cls.API_KEY_ENV:
            return True
        return bool(os.environ.get(cls.API_KEY_ENV, "").strip())

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the production extractor.

        Args:
            config: Configuration dictionary with API keys, etc.
        """
        self.config = config or {}
        self._rate_limiter = RateLimiter(self.RATE_LIMIT)
        self._request_count = 0
        self._error_count = 0
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        required = self.get_required_config()
        missing = [key for key in required if key not in self.config]
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} missing required config: {missing}"
            )

    @abstractmethod
    def get_required_config(self) -> List[str]:
        """
        Return list of required configuration keys.

        Returns:
            List of config key names (e.g., ['api_key', 'base_url'])
        """
        return []

    @abstractmethod
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """
        Perform the actual data extraction.

        This method should:
            1. Connect to the real data source
            2. Fetch and parse the data
            3. Return an ExtractorResult

        Args:
            entity_id: Identifier for the entity (domain, company name, etc.)
            **kwargs: Additional parameters

        Returns:
            ExtractorResult with the fetched data
        """
        pass

    def extract(
        self,
        entity_id: str,
        context: Optional[InferenceContext] = None,
        force_refresh: bool = False,
        **kwargs
    ) -> ExtractorResult:
        """
        Extract data with caching, rate limiting, and error handling.

        Args:
            entity_id: Identifier for the entity
            context: InferenceContext for caching
            force_refresh: If True, bypass cache
            **kwargs: Additional parameters

        Returns:
            ExtractorResult with the data
        """
        # V6 D1: kill-switch — short-circuit to neutral absence.
        if self.is_disabled():
            return self._create_neutral_absence(reason="kill_switch_active")

        # V6 D1: paid extractor without an API key — neutral absence.
        if not self.has_api_key():
            return self._create_neutral_absence(reason="api_key_missing")

        # Check cache first (unless force_refresh)
        if context and not force_refresh:
            cached = self._get_cached(entity_id, context, **kwargs)
            if cached:
                logger.debug(f"{self.SOURCE_NAME}: Cache hit for {entity_id}")
                return cached

        # Apply rate limiting
        self._rate_limiter.wait()

        # Track metrics
        self._request_count += 1
        start_time = time.time()

        # V6 C3: open a per-extractor OTel span (no-op when OTel disabled).
        try:
            from infrastructure.api.observability.otel import extractor_span
        except ImportError:
            extractor_span = None

        span_cm = (
            extractor_span(
                self.SOURCE_NAME,
                entity_id=entity_id,
                cost_tier=self.COST_TIER,
                cache_hit=False,
            )
            if extractor_span is not None
            else _NullCM()
        )

        try:
            with span_cm:
                # Fetch fresh data
                result = self._do_extract(entity_id, **kwargs)

            # Add timing metadata
            elapsed_ms = (time.time() - start_time) * 1000
            if result.metadata is None:
                result.metadata = {}
            result.metadata['response_time_ms'] = elapsed_ms
            result.metadata['source_version'] = self.SOURCE_VERSION

            # V6/E2 (follow-up 1.1) — build + attach a Provenance record
            # to every successful extraction. Persisting into the
            # signal_provenance table is a job of the extractor
            # orchestrator (seen the context object it gets called from);
            # we attach the dataclass to metadata so the orchestrator
            # can hand it to the persistence layer without re-running
            # the hash.
            try:
                from signal_architecture.signals.provenance import (
                    build_provenance,
                )
                provenance = build_provenance(
                    source_name=self.SOURCE_NAME,
                    source_url=f"dsi://extractor/{self.SOURCE_NAME}",
                    response_body=result.data or {},
                    response_status_code=(
                        200 if result.success else 599
                    ),
                    extractor_version=self.SOURCE_VERSION,
                    cache_hit=False,
                )
                result.metadata["provenance"] = provenance.to_dict()
            except Exception as prov_exc:  # pragma: no cover
                logger.debug(
                    "%s: provenance build failed (non-blocking): %s",
                    self.SOURCE_NAME, prov_exc,
                )

            # Cache successful results
            if context and result.success:
                self._cache_result(entity_id, result, context, **kwargs)

            logger.debug(
                f"{self.SOURCE_NAME}: Extracted data for {entity_id} in {elapsed_ms:.0f}ms"
            )
            return result

        except Exception as e:
            self._error_count += 1
            logger.error(f"{self.SOURCE_NAME}: Error extracting {entity_id}: {e}")
            return self._create_error_result(str(e))

    def get_metrics(self) -> Dict[str, Any]:
        """Get extractor metrics for monitoring."""
        return {
            'source_name': self.SOURCE_NAME,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(self._request_count, 1),
            'cost_tier': self.COST_TIER,
        }

    # Helper methods for subclasses

    def _normalize_domain(self, entity_id: str) -> str:
        """Normalize a domain name (remove protocol, trailing slash, etc.)."""
        domain = entity_id.lower().strip()
        # Remove protocol
        for prefix in ['https://', 'http://', 'www.']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        # Remove path/trailing slash
        domain = domain.split('/')[0]
        return domain

    def _create_success_result(
        self,
        data: Dict[str, Any],
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractorResult:
        """Create a successful ExtractorResult."""
        meta = dict(metadata or {})
        meta.setdefault("confidence", confidence)
        return ExtractorResult(
            success=True,
            data=data,
            source=self.SOURCE_NAME,
            extracted_at=utcnow(),
            ttl_seconds=self.DEFAULT_TTL_SECONDS,
            error=None,
            metadata=meta,
        )

    def _create_error_result(
        self,
        error: str,
        partial_data: Optional[Dict[str, Any]] = None
    ) -> ExtractorResult:
        """Create a failed ExtractorResult."""
        return ExtractorResult(
            success=False,
            data=partial_data or {},
            source=self.SOURCE_NAME,
            extracted_at=utcnow(),
            ttl_seconds=60,  # Short TTL for errors
            error=error,
            metadata={
                'error_type': type(error).__name__,
                'confidence': 0.0,
            },
        )

    def _create_neutral_absence(self, *, reason: str) -> ExtractorResult:
        """V6 (D1) — signal a known absence without raising.

        Used when a kill-switch is active or a required API key is
        missing. Downstream inference treats confidence=0 as "no signal",
        matching the absence-as-signal principle.
        """
        return ExtractorResult(
            success=False,
            data={},
            source=f"{self.SOURCE_NAME}:absent",
            extracted_at=utcnow(),
            ttl_seconds=300,
            error=None,
            metadata={
                "absence_reason": reason,
                "cost_tier": self.COST_TIER,
                "confidence": 0.0,
            },
        )

    def _get_cached(
        self,
        entity_id: str,
        context: InferenceContext,
        **kwargs
    ) -> Optional[ExtractorResult]:
        """Check cache for valid result."""
        if not hasattr(context, 'cache') or context.cache is None:
            return None

        cache_key = self._cache_key(entity_id, **kwargs)
        cached = context.cache.get(cache_key)

        if cached and isinstance(cached, ExtractorResult):
            # Check if still valid
            age_seconds = (utcnow() - cached.timestamp).total_seconds()
            if age_seconds < cached.ttl_seconds:
                return cached

        return None

    def _cache_result(
        self,
        entity_id: str,
        result: ExtractorResult,
        context: InferenceContext,
        **kwargs
    ) -> None:
        """Cache a result."""
        if not hasattr(context, 'cache') or context.cache is None:
            return

        cache_key = self._cache_key(entity_id, **kwargs)
        context.cache[cache_key] = result

    def _cache_key(self, entity_id: str, **kwargs) -> str:
        """Generate a cache key."""
        key_parts = [self.SOURCE_NAME, entity_id]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return ":".join(key_parts)
