"""
DSI Extractors

Extractors fetch raw data from external sources (APIs, databases, FTP, etc.).

Implementation Status: STUB
    All extractors return randomized but structurally realistic data
    that mimics real API responses.

Classes:
    StubExtractor: Base class with randomization utilities for stub implementations

Usage:
    from signals.extractors import StubExtractor
    
    class MyExtractor(StubExtractor):
        SOURCE_NAME = "my_api"
        
        def extract(self, entity_id: str) -> ExtractorResult:
            data = {"value": self._random_int(1, 100)}
            return self._create_success_result(data)
"""

from .base import (
    StubExtractor,
    generate_company_profile,
    generate_financial_summary,
    generate_address,
)

__all__ = [
    "StubExtractor",
    "generate_company_profile",
    "generate_financial_summary",
    "generate_address",
]
