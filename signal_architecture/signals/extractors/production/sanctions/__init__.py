"""
DSI Production Extractors - Global Sanctions

This module provides production extractors for global sanctions databases.
These are FREE to use - publicly available sanctions data.

Extractors:
    Consolidated:
        - OpenSanctionsExtractor: Consolidated global sanctions (85+ sources)

    National/Regional:
        - UKOFSIExtractor: UK Office of Financial Sanctions Implementation
        - EUSanctionsExtractor: EU Consolidated Financial Sanctions

    Multilateral Development Banks:
        - WorldBankDebarredExtractor: World Bank debarred firms/individuals
        - ADBSanctionsExtractor: Asian Development Bank
        - IDBSanctionsExtractor: Inter-American Development Bank
        - EBRDIneligibleExtractor: European Bank for Reconstruction and Development
        - AfDBSanctionsExtractor: African Development Bank

    Law Enforcement:
        - InterpolRedNoticesExtractor: Interpol Red Notices (wanted persons)
        - FBIMostWantedExtractor: FBI Most Wanted list

Coverage:
    - UN Security Council sanctions
    - US OFAC (via our existing extractor)
    - UK OFSI sanctions
    - EU consolidated sanctions
    - World Bank/MDB cross-debarments (5 MDBs)
    - Interpol Red Notices
    - 80+ additional national sanctions lists

Requirements:
    - requests: pip install requests

Usage:
    from signals.extractors.production.sanctions import (
        OpenSanctionsExtractor,
        InterpolRedNoticesExtractor,
        ADBSanctionsExtractor,
    )

    extractor = OpenSanctionsExtractor()
    result = extractor.extract('Acme Corp')
"""

from .opensanctions import OpenSanctionsExtractor
from .uk_ofsi import UKOFSIExtractor
from .eu_sanctions import EUSanctionsExtractor
from .worldbank_debarred import WorldBankDebarredExtractor
from .interpol import InterpolRedNoticesExtractor
from .fbi_wanted import FBIMostWantedExtractor
from .mdb_exclusions import (
    ADBSanctionsExtractor,
    IDBSanctionsExtractor,
    EBRDIneligibleExtractor,
    AfDBSanctionsExtractor,
)
from ..factory import register_production

__all__ = [
    'OpenSanctionsExtractor',
    'UKOFSIExtractor',
    'EUSanctionsExtractor',
    'WorldBankDebarredExtractor',
    'InterpolRedNoticesExtractor',
    'FBIMostWantedExtractor',
    'ADBSanctionsExtractor',
    'IDBSanctionsExtractor',
    'EBRDIneligibleExtractor',
    'AfDBSanctionsExtractor',
    'register_all',
]


def register_all():
    """Register all sanctions extractors with the factory."""
    register_production('opensanctions', OpenSanctionsExtractor)
    register_production('uk_ofsi', UKOFSIExtractor)
    register_production('eu_sanctions', EUSanctionsExtractor)
    register_production('worldbank_debarred', WorldBankDebarredExtractor)
    register_production('interpol_red_notices', InterpolRedNoticesExtractor)
    register_production('fbi_most_wanted', FBIMostWantedExtractor)
    register_production('adb_sanctions', ADBSanctionsExtractor)
    register_production('idb_sanctions', IDBSanctionsExtractor)
    register_production('ebrd_ineligible', EBRDIneligibleExtractor)
    register_production('afdb_sanctions', AfDBSanctionsExtractor)
