"""
DSI Production Extractors - Regulatory Databases

This module provides production extractors that query US/EU regulatory databases.
These are FREE to use - government public data.

Extractors:
    - OFACSanctionsExtractor: OFAC SDN list search
    - EPAEchoExtractor: EPA ECHO enforcement/compliance data
    - CFPBComplaintsExtractor: Consumer Financial Protection Bureau complaints
    - OSHAViolationsExtractor: OSHA workplace safety violations
    - FAACertificateExtractor: FAA operating certificate status
    - EUSafetyListExtractor: EU Air Safety banned airlines list
    - FDICEnforcementExtractor: FDIC/OCC/Fed bank enforcement actions

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.regulatory import (
        OFACSanctionsExtractor,
        EPAEchoExtractor,
        CFPBComplaintsExtractor,
        OSHAViolationsExtractor,
        FAACertificateExtractor,
        EUSafetyListExtractor,
        FDICEnforcementExtractor,
    )

    extractor = OFACSanctionsExtractor()
    result = extractor.extract('Company Name')
"""

from .ofac import OFACSanctionsExtractor
from .epa_echo import EPAEchoExtractor
from .cfpb import CFPBComplaintsExtractor
from .osha import OSHAViolationsExtractor
from .faa import FAACertificateExtractor
from .eu_safety_list import EUSafetyListExtractor
from .fdic_enforcement import FDICEnforcementExtractor
from .bsee import BSEEIncidentExtractor
from ..factory import register_production

__all__ = [
    'OFACSanctionsExtractor',
    'EPAEchoExtractor',
    'CFPBComplaintsExtractor',
    'OSHAViolationsExtractor',
    'FAACertificateExtractor',
    'EUSafetyListExtractor',
    'FDICEnforcementExtractor',
    'BSEEIncidentExtractor',
    'register_all',
]


def register_all():
    """Register all regulatory extractors with the factory."""
    register_production('ofac_sanctions', OFACSanctionsExtractor)
    register_production('epa_echo', EPAEchoExtractor)
    register_production('cfpb_complaints', CFPBComplaintsExtractor)
    register_production('osha_violations', OSHAViolationsExtractor)
    register_production('faa_certificate', FAACertificateExtractor)
    register_production('eu_safety_list', EUSafetyListExtractor)
    register_production('fdic_enforcement', FDICEnforcementExtractor)
    register_production('bsee_incidents', BSEEIncidentExtractor)
