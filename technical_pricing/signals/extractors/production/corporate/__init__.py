"""
DSI Production Extractors - Corporate Registries

This module provides production extractors for corporate/company registries.
These are FREE to use - government public data.

Extractors:
    - CompaniesHouseExtractor: UK Companies House registry
    - OpenCorporatesExtractor: Global corporate data (145 jurisdictions)
    - AustraliaABNExtractor: Australian Business Register

Coverage:
    - United Kingdom (Companies House)
    - Australia (ABN Lookup)
    - 145+ jurisdictions (OpenCorporates)

Requirements:
    - requests: pip install requests

API Keys (optional but recommended):
    - Companies House: Free API key from https://developer.company-information.service.gov.uk/
    - OpenCorporates: Free API key from https://opencorporates.com/api_accounts/new

Usage:
    from technical_pricing.signals.extractors.production.corporate import (
        CompaniesHouseExtractor,
        OpenCorporatesExtractor,
        AustraliaABNExtractor,
    )

    extractor = OpenCorporatesExtractor()
    result = extractor.extract('Acme Corporation')
"""

from .companies_house import CompaniesHouseExtractor
from .opencorporates import OpenCorporatesExtractor
from .australia_abn import AustraliaABNExtractor
from ..factory import register_production

__all__ = [
    'CompaniesHouseExtractor',
    'OpenCorporatesExtractor',
    'AustraliaABNExtractor',
    'register_all',
]


def register_all():
    """Register all corporate extractors with the factory."""
    register_production('companies_house', CompaniesHouseExtractor)
    register_production('opencorporates', OpenCorporatesExtractor)
    register_production('australia_abn', AustraliaABNExtractor)
