"""
DSI Production Extractors - Security & Vulnerability

This module provides production extractors for security and vulnerability data.
These are FREE to use - based on public vulnerability databases.

Extractors:
    - NVDCVEExtractor: NIST National Vulnerability Database
    - HHSBreachExtractor: HHS HIPAA breach portal

Requirements:
    - requests: pip install requests

Usage:
    from signals.extractors.production.security import (
        NVDCVEExtractor,
        HHSBreachExtractor,
    )

    extractor = NVDCVEExtractor()
    result = extractor.extract('apache http server 2.4')

    breach_extractor = HHSBreachExtractor()
    result = breach_extractor.extract('Hospital Name')
"""

from .nvd_cve import NVDCVEExtractor
from .hhs_breach import HHSBreachExtractor
from ..factory import register_production

__all__ = [
    'NVDCVEExtractor',
    'HHSBreachExtractor',
    'register_all',
]


def register_all():
    """Register all security extractors with the factory."""
    register_production('nvd_cve', NVDCVEExtractor)
    register_production('hhs_breach', HHSBreachExtractor)
