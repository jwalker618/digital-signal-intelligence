"""
DSI Production Extractors - SEC EDGAR

This module provides production extractors for SEC EDGAR data.
These are FREE to use - SEC EDGAR is a public database.

Extractors:
    - SECFilingsExtractor: Company filings (10-K, 10-Q, 8-K, etc.)
    - SECFinancialsExtractor: Financial data from filings
    - SECOfficersExtractor: Officers and directors information

Requirements:
    - requests: pip install requests

SEC EDGAR API Requirements:
    - User-Agent header with company name and contact email
    - Rate limit: 10 requests per second

Usage:
    from technical_pricing.signals.extractors.production.sec import (
        SECFilingsExtractor,
        SECFinancialsExtractor,
    )

    extractor = SECFilingsExtractor()
    result = extractor.extract('AAPL')  # By ticker
    result = extractor.extract('0000320193')  # By CIK
"""

from .filings import SECFilingsExtractor
from .financials import SECFinancialsExtractor
from ..factory import register_production

__all__ = [
    'SECFilingsExtractor',
    'SECFinancialsExtractor',
    'register_all',
]


def register_all():
    """Register all SEC extractors with the factory."""
    register_production('sec_filings', SECFilingsExtractor)
    register_production('sec_financials', SECFinancialsExtractor)
