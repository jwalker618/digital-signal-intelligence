"""
Multi-Source Aggregator

Orchestrates calling multiple extractors for a signal type and consolidates
their results into a unified output schema.

This solves the problem of:
1. Which extractors to call (via JurisdictionRouter)
2. How to call them efficiently (parallel execution)
3. How to merge results (source-attributed consolidation)
4. How to handle variance (normalization to common schema)
"""

import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from .router import JurisdictionRouter, RoutingStrategy
from .schemas import RiskLevel

logger = logging.getLogger(__name__)

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
    ):
        """
        Initialize the aggregator.

        Args:
            router: Jurisdiction router (creates default if None)
            max_workers: Max parallel extractor calls
            timeout_seconds: Timeout per extractor call
            default_strategy: Default routing strategy
        """
        self.router = router or JurisdictionRouter()
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.default_strategy = default_strategy

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

    def _call_extractor(
        self,
        extractor_name: str,
        entity_id: str,
        get_extractor: Callable,
    ) -> ExtractorCallResult:
        """Call a single extractor and return the result."""
        start_time = time.time()

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

            return ExtractorCallResult(
                extractor_name=extractor_name,
                success=result.success if hasattr(result, 'success') else True,
                data=result.data if hasattr(result, 'data') else result,
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
