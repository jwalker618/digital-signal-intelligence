"""
Digital Signal Intelligence - Corporate Website Discovery
==========================================================

Main module for discovering corporate websites from company names or domains.

Author: John Walker
Date: November 2025
Version: 1.0
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .strategies import (
    DomainGenerationStrategy,
    SearchStrategy,
    WikipediaStrategy,
)
from .validators import ValidationResult, WebsiteValidator


class DiscoveryMethod(Enum):
    """Methods used for discovery"""

    DOMAIN_GENERATION = "domain_generation"
    SEARCH_ENGINE = "search_engine"
    LINKEDIN = "linkedin"
    WIKIPEDIA = "wikipedia"
    MANUAL = "manual"


@dataclass
class WebsiteCandidate:
    """A potential corporate website candidate"""

    url: str
    confidence_score: float
    discovery_method: DiscoveryMethod
    validation_result: Optional[ValidationResult] = None
    rank: int = 0
    title: str = ""
    description: str = ""
    corporate_indicators: List[str] = field(default_factory=list)


@dataclass
class DiscoveryResult:
    """Result of corporate website discovery"""

    company_name: str
    best_match: Optional[WebsiteCandidate]
    all_candidates: List[WebsiteCandidate]
    discovery_time: float
    strategies_used: List[str]
    total_candidates: int
    success: bool


class CorporateWebsiteDiscovery:
    """
    Main class for discovering corporate websites.

    Orchestrates multiple discovery strategies and ranks results.
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        bing_api_key: Optional[str] = None,
        timeout: int = 10,
        max_candidates: int = 20,
        use_cache: bool = True,
    ):
        """
        Initialize corporate website discovery.

        Args:
            google_api_key: Google Custom Search API key
            google_cx: Google Custom Search Engine ID
            bing_api_key: Bing Search API key
            timeout: Request timeout in seconds
            max_candidates: Maximum number of candidates to evaluate
            use_cache: Whether to cache results
        """
        self.timeout = timeout
        self.max_candidates = max_candidates
        self.use_cache = use_cache

        # Initialize strategies
        self.domain_strategy = DomainGenerationStrategy(max_attempts=20)
        self.search_strategy = SearchStrategy(
            google_api_key=google_api_key,
            google_cx=google_cx,
            bing_api_key=bing_api_key,
        )
        self.wikipedia_strategy = WikipediaStrategy()

        # Initialize validator
        self.validator = WebsiteValidator(timeout=timeout)

        # Cache for results
        self._cache: Dict[str, DiscoveryResult] = {}

    def discover(
        self,
        company_name: str,
        domain_hint: Optional[str] = None,
        use_search: bool = True,
    ) -> DiscoveryResult:
        """
        Discover corporate website for a company.

        Args:
            company_name: Company name to search for
            domain_hint: Optional domain hint to prioritize
            use_search: Whether to use search engines (requires API keys)

        Returns:
            DiscoveryResult with best match and all candidates
        """
        start_time = time.time()

        # Check cache
        cache_key = f"{company_name}:{domain_hint}:{use_search}"
        if self.use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        candidates = []
        strategies_used = []

        # Strategy 1: Domain Generation
        print(f"🔍 Discovering website for: {company_name}")
        print("  Strategy 1: Domain generation...")
        domain_candidates = self._discover_via_domains(company_name)
        candidates.extend(domain_candidates)
        if domain_candidates:
            strategies_used.append("domain_generation")
        print(f"  Found {len(domain_candidates)} candidates via domain generation")

        # Strategy 2: Domain hint (if provided)
        if domain_hint:
            print("  Strategy 2: Using domain hint...")
            hint_candidate = self._discover_via_hint(domain_hint, company_name)
            if hint_candidate:
                candidates.append(hint_candidate)
                strategies_used.append("domain_hint")
            print(f"  Domain hint validated: {hint_candidate is not None}")

        # Strategy 3: Search engines (if enabled and API keys available)
        if use_search:
            print("  Strategy 3: Search engine discovery...")
            search_candidates = self._discover_via_search(company_name)
            candidates.extend(search_candidates)
            if search_candidates:
                strategies_used.append("search_engine")
            print(f"  Found {len(search_candidates)} candidates via search")

        # Rank and deduplicate candidates
        candidates = self._rank_candidates(candidates)

        # Limit to max candidates
        candidates = candidates[: self.max_candidates]

        # Find best match
        best_match = candidates[0] if candidates else None

        discovery_time = time.time() - start_time

        result = DiscoveryResult(
            company_name=company_name,
            best_match=best_match,
            all_candidates=candidates,
            discovery_time=discovery_time,
            strategies_used=strategies_used,
            total_candidates=len(candidates),
            success=best_match is not None,
        )

        # Cache result
        if self.use_cache:
            self._cache[cache_key] = result

        return result

    def _discover_via_domains(self, company_name: str) -> List[WebsiteCandidate]:
        """Discover via domain generation strategy"""
        candidates = []
        valid_domains = self.domain_strategy.discover(company_name)

        for url in valid_domains:
            try:
                validation = self.validator.validate_website(url, company_name)
                if validation.is_valid:
                    candidate = WebsiteCandidate(
                        url=url,
                        confidence_score=validation.confidence_score,
                        discovery_method=DiscoveryMethod.DOMAIN_GENERATION,
                        validation_result=validation,
                        title=validation.title,
                        description=validation.description,
                        corporate_indicators=validation.corporate_indicators,
                    )
                    candidates.append(candidate)
                    print(f"    ✓ {url} (score: {validation.confidence_score:.1f})")
            except Exception:
                pass  # Skip failed validations

        return candidates

    def _discover_via_hint(
        self, domain_hint: str, company_name: str
    ) -> Optional[WebsiteCandidate]:
        """Discover via provided domain hint"""
        try:
            # Ensure URL format
            if not domain_hint.startswith(("http://", "https://")):
                domain_hint = f"https://{domain_hint}"

            validation = self.validator.validate_website(domain_hint, company_name)
            if validation.is_valid:
                return WebsiteCandidate(
                    url=domain_hint,
                    confidence_score=validation.confidence_score
                    + 10.0,  # Bonus for hint
                    discovery_method=DiscoveryMethod.MANUAL,
                    validation_result=validation,
                    title=validation.title,
                    description=validation.description,
                    corporate_indicators=validation.corporate_indicators,
                )
        except Exception:
            pass

        return None

    def _discover_via_search(self, company_name: str) -> List[WebsiteCandidate]:
        """Discover via search engine strategy"""
        candidates = []
        search_results = self.search_strategy.discover(company_name, max_results=10)

        for result in search_results:
            try:
                validation = self.validator.validate_website(result.url, company_name)
                if validation.is_valid:
                    candidate = WebsiteCandidate(
                        url=result.url,
                        confidence_score=validation.confidence_score,
                        discovery_method=DiscoveryMethod.SEARCH_ENGINE,
                        validation_result=validation,
                        rank=result.rank,
                        title=validation.title or result.title,
                        description=validation.description or result.snippet,
                        corporate_indicators=validation.corporate_indicators,
                    )
                    candidates.append(candidate)
            except Exception:
                pass  # Skip failed validations

        return candidates

    def _rank_candidates(
        self, candidates: List[WebsiteCandidate]
    ) -> List[WebsiteCandidate]:
        """
        Rank candidates by confidence score and deduplicate.

        Args:
            candidates: List of candidates

        Returns:
            Sorted and deduplicated list
        """
        # Deduplicate by URL
        seen_urls = set()
        unique_candidates = []

        for candidate in candidates:
            # Normalize URL for comparison
            normalized_url = candidate.url.lower().rstrip("/")

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_candidates.append(candidate)

        # Sort by confidence score (highest first)
        sorted_candidates = sorted(
            unique_candidates,
            key=lambda c: (c.confidence_score, -len(c.corporate_indicators)),
            reverse=True,
        )

        # Update ranks
        for idx, candidate in enumerate(sorted_candidates):
            candidate.rank = idx + 1

        return sorted_candidates

    def discover_batch(
        self,
        company_names: List[str],
        use_search: bool = True,
        delay: float = 1.0,
    ) -> Dict[str, DiscoveryResult]:
        """
        Discover websites for multiple companies.

        Args:
            company_names: List of company names
            use_search: Whether to use search engines
            delay: Delay between requests in seconds

        Returns:
            Dictionary mapping company names to results
        """
        results = {}

        for company_name in company_names:
            result = self.discover(company_name, use_search=use_search)
            results[company_name] = result

            # Rate limiting
            if delay > 0:
                time.sleep(delay)

        return results

    def clear_cache(self):
        """Clear the results cache"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {"cached_results": len(self._cache)}
