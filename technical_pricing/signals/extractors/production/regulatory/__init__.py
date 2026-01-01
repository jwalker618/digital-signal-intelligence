"""
DSI Production Extractors - Regulatory Databases

This module provides production extractors that query US regulatory databases.
These are FREE to use - government public data.

Extractors:
    - OFACSanctionsExtractor: OFAC SDN list search
    - EPAEchoExtractor: EPA ECHO enforcement/compliance data
    - CFPBComplaintsExtractor: Consumer Financial Protection Bureau complaints

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.regulatory import (
        OFACSanctionsExtractor,
        EPAEchoExtractor,
        CFPBComplaintsExtractor,
    )

    extractor = OFACSanctionsExtractor()
    result = extractor.extract('Company Name')
"""

from .ofac import OFACSanctionsExtractor
from .epa_echo import EPAEchoExtractor
from .cfpb import CFPBComplaintsExtractor
from ..factory import register_production

__all__ = [
    'OFACSanctionsExtractor',
    'EPAEchoExtractor',
    'CFPBComplaintsExtractor',
    'register_all',
]


def register_all():
    """Register all regulatory extractors with the factory."""
    register_production('ofac_sanctions', OFACSanctionsExtractor)
    register_production('epa_echo', EPAEchoExtractor)
    register_production('cfpb_complaints', CFPBComplaintsExtractor)
