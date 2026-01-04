"""
DSI Production Extractors - Securities Regulators

This module provides production extractors for securities regulatory data.
These are FREE to use - public government databases.

Extractors:
    US SEC EDGAR:
        - SECFilingsExtractor: Company filings (10-K, 10-Q, 8-K, etc.)
        - SECFinancialsExtractor: Financial data from XBRL filings
        - SECLitigationExtractor: 8-K litigation/legal disclosures
        - SECGovernanceExtractor: DEF 14A governance analysis

    Canada SEDAR+:
        - SEDARCanadaExtractor: Canadian securities filings

Coverage:
    - United States (SEC EDGAR)
    - Canada (SEDAR+)

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.sec import (
        SECFilingsExtractor,
        SECFinancialsExtractor,
        SEDARCanadaExtractor,
    )

    # US company
    extractor = SECFilingsExtractor()
    result = extractor.extract('AAPL')

    # Canadian company
    extractor = SEDARCanadaExtractor()
    result = extractor.extract('Royal Bank of Canada')
"""

from .filings import SECFilingsExtractor
from .financials import SECFinancialsExtractor
from .litigation import SECLitigationExtractor
from .governance import SECGovernanceExtractor
from .sedar_canada import SEDARCanadaExtractor
from ..factory import register_production

__all__ = [
    'SECFilingsExtractor',
    'SECFinancialsExtractor',
    'SECLitigationExtractor',
    'SECGovernanceExtractor',
    'SEDARCanadaExtractor',
    'register_all',
]


def register_all():
    """Register all securities extractors with the factory."""
    register_production('sec_filings', SECFilingsExtractor)
    register_production('sec_financials', SECFinancialsExtractor)
    register_production('sec_litigation', SECLitigationExtractor)
    register_production('sec_governance', SECGovernanceExtractor)
    register_production('sedar_canada', SEDARCanadaExtractor)
