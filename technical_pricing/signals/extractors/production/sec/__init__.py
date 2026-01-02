"""
DSI Production Extractors - SEC EDGAR

This module provides production extractors for SEC EDGAR data.
These are FREE to use - SEC EDGAR is a public database.

Extractors:
    - SECFilingsExtractor: Company filings (10-K, 10-Q, 8-K, etc.)
    - SECFinancialsExtractor: Financial data from XBRL filings
    - SECLitigationExtractor: 8-K litigation/legal disclosures
    - SECGovernanceExtractor: DEF 14A governance analysis

Requirements:
    - requests: pip install requests

SEC EDGAR API Requirements:
    - User-Agent header with company name and contact email
    - Rate limit: 10 requests per second

Usage:
    from technical_pricing.signals.extractors.production.sec import (
        SECFilingsExtractor,
        SECFinancialsExtractor,
        SECLitigationExtractor,
        SECGovernanceExtractor,
    )

    extractor = SECFilingsExtractor()
    result = extractor.extract('AAPL')  # By ticker
    result = extractor.extract('0000320193')  # By CIK
"""

from .filings import SECFilingsExtractor
from .financials import SECFinancialsExtractor
from .litigation import SECLitigationExtractor
from .governance import SECGovernanceExtractor
from ..factory import register_production

__all__ = [
    'SECFilingsExtractor',
    'SECFinancialsExtractor',
    'SECLitigationExtractor',
    'SECGovernanceExtractor',
    'register_all',
]


def register_all():
    """Register all SEC extractors with the factory."""
    register_production('sec_filings', SECFilingsExtractor)
    register_production('sec_financials', SECFinancialsExtractor)
    register_production('sec_litigation', SECLitigationExtractor)
    register_production('sec_governance', SECGovernanceExtractor)
