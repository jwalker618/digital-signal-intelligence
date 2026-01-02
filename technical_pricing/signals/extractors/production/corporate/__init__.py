"""
DSI Production Extractors - Corporate Registries

This module provides production extractors for corporate/company registries.
These are FREE to use - government public data.

Extractors:
    - CompaniesHouseExtractor: UK Companies House registry

Requirements:
    - requests: pip install requests

API Keys (optional but recommended):
    - Companies House: Free API key from https://developer.company-information.service.gov.uk/

Usage:
    from technical_pricing.signals.extractors.production.corporate import (
        CompaniesHouseExtractor,
    )

    extractor = CompaniesHouseExtractor()
    result = extractor.extract('British Airways')
"""

from .companies_house import CompaniesHouseExtractor
from ..factory import register_production

__all__ = [
    'CompaniesHouseExtractor',
    'register_all',
]


def register_all():
    """Register all corporate extractors with the factory."""
    register_production('companies_house', CompaniesHouseExtractor)
