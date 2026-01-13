"""
DSI Signal Architecture - Extractor Base

This module provides the base class and utilities for Extractors.
Extractors fetch raw data from external sources (APIs, databases, FTP, etc.).

Implementation Status: STUB
    All extractors are currently stubs that return randomized but
    structurally realistic data. When real data sources are integrated,
    only the extract() method needs to change - aggregators and
    categorizers remain unchanged.

Utilities provided:
    - StubExtractor: Extended base with randomization helpers
    - Common data generation functions for realistic stub data
"""

import random
import string
from abc import abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base import BaseExtractor
from ..types import ExtractorResult, InferenceContext


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class StubExtractor(BaseExtractor):
    """
    Extended base class for stub extractors with randomization utilities.
    
    Provides helper methods for generating realistic random data
    that mimics real API responses, plus TTL-aware caching.
    
    TTL Configuration:
        Override DEFAULT_TTL_SECONDS based on the data source characteristics:
        - TTL_REALTIME (60s): Live prices, positions
        - TTL_FREQUENT (300s): Frequently updated feeds
        - TTL_HOURLY (3600s): General API data
        - TTL_DAILY (86400s): Regulatory status, certifications
        - TTL_WEEKLY (604800s): Corporate structure
        - TTL_MONTHLY (2592000s): Historical records
    
    Example:
        class AllianceExtractor(StubExtractor):
            SOURCE_NAME = "iata_alliance_registry"
            DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY  # Alliance membership rarely changes
            
            def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
                data = {
                    "alliance": self._random_choice(["STAR", "OW", "ST", None]),
                    "join_date": self._random_date_iso(years_back=10),
                }
                return self._create_success_result(data)
    """
    
    def extract(
        self, 
        entity_id: str, 
        context: 'InferenceContext' = None,
        force_refresh: bool = False,
        **kwargs
    ) -> ExtractorResult:
        """
        Extract data with TTL-aware caching.
        
        This method handles the caching logic. Subclasses should implement
        _do_extract() for the actual data fetching.
        
        Args:
            entity_id: Identifier for the entity
            context: InferenceContext for caching
            force_refresh: If True, bypass cache and fetch fresh
            **kwargs: Additional parameters
        
        Returns:
            ExtractorResult (from cache if valid, fresh otherwise)
        """
        # Check cache first (unless force_refresh)
        if context and not force_refresh:
            cached = self._get_cached(entity_id, context, **kwargs)
            if cached:
                return cached
        
        # Simulate occasional failures
        if self._simulate_failure():
            result = self._create_error_result(self._random_error())
        else:
            # Fetch fresh data via subclass implementation
            result = self._do_extract(entity_id, **kwargs)
        
        # Cache successful results
        if context and result.success:
            self._cache_result(entity_id, result, context, **kwargs)
        
        return result
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """
        Perform the actual extraction. Override in subclasses.
        
        This is where stub data generation happens. The caching logic
        is handled by extract().
        
        Args:
            entity_id: Identifier for the entity
            **kwargs: Additional parameters
        
        Returns:
            ExtractorResult with generated stub data
        """
        # Default implementation - override in subclasses
        return self._create_success_result({
            "entity_id": entity_id,
            "stub": True,
            "message": "Override _do_extract() in subclass"
        })
    
    def _random_choice(
        self,
        options: List[Any],
        weights: Optional[List[float]] = None
    ) -> Any:
        """
        Select randomly from options with optional weighting.
        
        Args:
            options: List of possible values
            weights: Optional probability weights (must sum to 1.0)
        
        Returns:
            Randomly selected option
        """
        if weights:
            return random.choices(options, weights=weights, k=1)[0]
        return random.choice(options)
    
    def _random_bool(self, true_probability: float = 0.5) -> bool:
        """Return True with the given probability."""
        return random.random() < true_probability
    
    def _random_int(self, min_val: int, max_val: int) -> int:
        """Return a random integer in the inclusive range."""
        return random.randint(min_val, max_val)
    
    def _random_float(
        self,
        min_val: float,
        max_val: float,
        decimals: int = 2
    ) -> float:
        """Return a random float in the range, rounded to decimals."""
        value = random.uniform(min_val, max_val)
        return round(value, decimals)
    
    def _random_date(
        self,
        years_back: int = 5,
        years_forward: int = 0
    ) -> datetime:
        """
        Generate a random date within the specified range.
        
        Args:
            years_back: Maximum years in the past
            years_forward: Maximum years in the future
        
        Returns:
            Random datetime
        """
        now = utcnow()
        start = now - timedelta(days=years_back * 365)
        end = now + timedelta(days=years_forward * 365)
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)
    
    def _random_date_iso(
        self,
        years_back: int = 5,
        years_forward: int = 0,
        include_time: bool = False
    ) -> str:
        """Generate a random date as ISO format string."""
        dt = self._random_date(years_back, years_forward)
        if include_time:
            return dt.isoformat()
        return dt.date().isoformat()
    
    def _random_date_or_none(
        self,
        none_probability: float = 0.2,
        **kwargs
    ) -> Optional[str]:
        """Generate a random date or None."""
        if random.random() < none_probability:
            return None
        return self._random_date_iso(**kwargs)
    
    def _random_string(
        self,
        length: int = 10,
        include_digits: bool = False
    ) -> str:
        """Generate a random alphanumeric string."""
        chars = string.ascii_uppercase
        if include_digits:
            chars += string.digits
        return ''.join(random.choices(chars, k=length))
    
    def _random_id(self, prefix: str = "") -> str:
        """Generate a random ID with optional prefix."""
        suffix = self._random_string(8, include_digits=True)
        return f"{prefix}{suffix}" if prefix else suffix
    
    def _random_percentage(self, decimals: int = 1) -> float:
        """Generate a random percentage 0-100."""
        return self._random_float(0, 100, decimals)
    
    def _random_count(
        self,
        min_val: int = 0,
        max_val: int = 100,
        zero_probability: float = 0.1
    ) -> int:
        """Generate a random count with probability of zero."""
        if random.random() < zero_probability:
            return 0
        return self._random_int(min_val, max_val)
    
    def _random_rating(
        self,
        ratings: List[str] = None,
        include_none: bool = True
    ) -> Optional[str]:
        """
        Generate a random rating from a standard set.
        
        Default ratings follow S&P-style: AAA, AA, A, BBB, BB, B, CCC, CC, C
        """
        if ratings is None:
            ratings = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
                      "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
                      "B+", "B", "B-", "CCC", "CC", "C"]
        
        if include_none:
            ratings = ratings + [None]
        
        return self._random_choice(ratings)
    
    def _random_country_code(self) -> str:
        """Generate a random ISO country code."""
        codes = ["US", "GB", "DE", "FR", "JP", "CN", "AU", "CA", 
                 "BR", "IN", "SG", "AE", "CH", "NL", "KR"]
        return self._random_choice(codes)
    
    def _random_currency(self) -> str:
        """Generate a random currency code."""
        currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD"]
        return self._random_choice(currencies)
    
    def _random_amount(
        self,
        min_val: float = 1000,
        max_val: float = 1000000,
        currency: bool = False
    ) -> Dict[str, Any] | float:
        """Generate a random monetary amount."""
        amount = self._random_float(min_val, max_val, 2)
        if currency:
            return {
                "amount": amount,
                "currency": self._random_currency()
            }
        return amount
    
    def _simulate_response_time(self) -> int:
        """Simulate API response time in milliseconds."""
        return self._random_int(50, 500)
    
    def _create_stub_metadata(self) -> Dict[str, Any]:
        """Create standard metadata for stub responses."""
        return {
            "api_version": self.SOURCE_VERSION,
            "response_time_ms": self._simulate_response_time(),
            "is_stub": True,
            "stub_generated_at": utcnow().isoformat(),
            "ttl_seconds": self.DEFAULT_TTL_SECONDS,
        }
    
    def _create_success_result(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None
    ) -> ExtractorResult:
        """
        Create a successful extraction result with TTL.
        
        Args:
            data: The extracted data
            metadata: Additional metadata to merge
            ttl_seconds: Override default TTL
        """
        stub_metadata = self._create_stub_metadata()
        if metadata:
            stub_metadata.update(metadata)
        return super()._create_success_result(
            data, 
            stub_metadata, 
            ttl_seconds=ttl_seconds or self.DEFAULT_TTL_SECONDS
        )
    
    def _simulate_failure(self, failure_rate: float = 0.05) -> bool:
        """
        Determine if this extraction should simulate a failure.
        
        Args:
            failure_rate: Probability of failure (default 5%)
        
        Returns:
            True if extraction should fail
        """
        return random.random() < failure_rate
    
    def _random_error(self) -> str:
        """Generate a random realistic error message."""
        errors = [
            "Connection timeout",
            "Rate limit exceeded",
            "Service temporarily unavailable",
            "Invalid API key",
            "Resource not found",
            "Internal server error",
        ]
        return self._random_choice(errors)


# Convenience functions for common data patterns

def generate_company_profile() -> Dict[str, Any]:
    """Generate a random company profile structure."""
    return {
        "name": f"Company_{random.randint(1000, 9999)}",
        "incorporated_country": random.choice(["US", "GB", "DE", "FR", "JP"]),
        "incorporated_date": (utcnow() - timedelta(days=random.randint(365, 20000))).date().isoformat(),
        "public": random.random() > 0.6,
        "employee_count": random.randint(10, 50000),
        "industry_codes": {
            "sic": str(random.randint(1000, 9999)),
            "naics": str(random.randint(100000, 999999)),
        }
    }


def generate_financial_summary() -> Dict[str, Any]:
    """Generate a random financial summary structure."""
    revenue = random.uniform(1e6, 1e10)
    return {
        "revenue": round(revenue, 2),
        "revenue_currency": "USD",
        "fiscal_year": utcnow().year - 1,
        "net_income": round(revenue * random.uniform(-0.1, 0.3), 2),
        "total_assets": round(revenue * random.uniform(0.5, 3.0), 2),
        "total_liabilities": round(revenue * random.uniform(0.2, 1.5), 2),
    }


def generate_address() -> Dict[str, Any]:
    """Generate a random address structure."""
    return {
        "street": f"{random.randint(1, 999)} Main Street",
        "city": random.choice(["New York", "London", "Tokyo", "Singapore", "Frankfurt"]),
        "country": random.choice(["US", "GB", "JP", "SG", "DE"]),
        "postal_code": str(random.randint(10000, 99999)),
    }
