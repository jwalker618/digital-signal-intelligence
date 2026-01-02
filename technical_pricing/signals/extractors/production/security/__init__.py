"""
DSI Production Extractors - Security & Vulnerability

This module provides production extractors for security and vulnerability data.
These are FREE to use - based on public vulnerability databases.

Extractors:
    - NVDCVEExtractor: NIST National Vulnerability Database
    - (Future: HIBP, breach databases, etc.)

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.security import (
        NVDCVEExtractor,
    )

    extractor = NVDCVEExtractor()
    result = extractor.extract('apache http server 2.4')
"""

from .nvd_cve import NVDCVEExtractor
from ..factory import register_production

__all__ = [
    'NVDCVEExtractor',
    'register_all',
]


def register_all():
    """Register all security extractors with the factory."""
    register_production('nvd_cve', NVDCVEExtractor)
