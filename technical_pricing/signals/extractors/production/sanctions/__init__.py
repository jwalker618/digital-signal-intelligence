"""
DSI Production Extractors - Global Sanctions

This module provides production extractors for global sanctions databases.
These are FREE to use - publicly available sanctions data.

Extractors:
    - OpenSanctionsExtractor: Consolidated global sanctions (85+ sources)
    - UKOFSIExtractor: UK Office of Financial Sanctions Implementation
    - EUSanctionsExtractor: EU Consolidated Financial Sanctions
    - WorldBankDebarredExtractor: World Bank debarred firms/individuals

Coverage:
    - UN Security Council sanctions
    - US OFAC (via our existing extractor)
    - UK OFSI sanctions
    - EU consolidated sanctions
    - World Bank/MDB cross-debarments
    - 80+ additional national sanctions lists

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.sanctions import (
        OpenSanctionsExtractor,
        UKOFSIExtractor,
    )

    extractor = OpenSanctionsExtractor()
    result = extractor.extract('Acme Corp')
"""

from .opensanctions import OpenSanctionsExtractor
from .uk_ofsi import UKOFSIExtractor
from .eu_sanctions import EUSanctionsExtractor
from .worldbank_debarred import WorldBankDebarredExtractor
from ..factory import register_production

__all__ = [
    'OpenSanctionsExtractor',
    'UKOFSIExtractor',
    'EUSanctionsExtractor',
    'WorldBankDebarredExtractor',
    'register_all',
]


def register_all():
    """Register all sanctions extractors with the factory."""
    register_production('opensanctions', OpenSanctionsExtractor)
    register_production('uk_ofsi', UKOFSIExtractor)
    register_production('eu_sanctions', EUSanctionsExtractor)
    register_production('worldbank_debarred', WorldBankDebarredExtractor)
