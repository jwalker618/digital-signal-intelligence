"""
DSI Production Extractors - Corporate Registries

This module provides production extractors for corporate/company registries.
These are FREE to use - government public data.

Extractors:
    - CompaniesHouseExtractor: UK Companies House registry
    - OpenCorporatesExtractor: Global corporate data (145 jurisdictions)
    - AustraliaABNExtractor: Australian Business Register
    - IndiaMCAExtractor: India Ministry of Corporate Affairs
    - GLEIFLEIExtractor: GLEIF Legal Entity Identifier (2.5M+ entities)

Coverage:
    - United Kingdom (Companies House)
    - Australia (ABN Lookup)
    - India (MCA registry - 1.5M+ companies)
    - 145+ jurisdictions (OpenCorporates)

Requirements:
    - requests: pip install requests

API Keys (optional but recommended):
    - Companies House: Free API key from https://developer.company-information.service.gov.uk/
    - OpenCorporates: Free API key from https://opencorporates.com/api_accounts/new
    - India data.gov.in: Free API key from https://data.gov.in/

Usage:
    from signals.extractors.production.corporate import (
        CompaniesHouseExtractor,
        OpenCorporatesExtractor,
        AustraliaABNExtractor,
        IndiaMCAExtractor,
    )

    extractor = IndiaMCAExtractor()
    result = extractor.extract('Tata Consultancy Services')
"""

from .companies_house import CompaniesHouseExtractor
from .opencorporates import OpenCorporatesExtractor
from .australia_abn import AustraliaABNExtractor
from .india_mca import IndiaMCAExtractor
from .gleif_lei import GLEIFLEIExtractor
from ..factory import register_production

__all__ = [
    'CompaniesHouseExtractor',
    'OpenCorporatesExtractor',
    'AustraliaABNExtractor',
    'IndiaMCAExtractor',
    'GLEIFLEIExtractor',
    'register_all',
]


def register_all():
    """Register all corporate extractors with the factory."""
    register_production('companies_house', CompaniesHouseExtractor)
    register_production('opencorporates', OpenCorporatesExtractor)
    register_production('australia_abn', AustraliaABNExtractor)
    register_production('india_mca', IndiaMCAExtractor)
    register_production('gleif_lei', GLEIFLEIExtractor)
