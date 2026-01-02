"""
DSI Production Extractors - Industry Registries

This module provides production extractors for industry-specific registries.
These are FREE to use - public professional registries.

Extractors:
    - PCAOBExtractor: PCAOB registered auditor firm status
    - (Future: IOSA, IMO GISIS, Classification Societies)

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.industry import (
        PCAOBExtractor,
    )

    extractor = PCAOBExtractor()
    result = extractor.extract('Deloitte & Touche LLP')
"""

from .pcaob import PCAOBExtractor
from ..factory import register_production

__all__ = [
    'PCAOBExtractor',
    'register_all',
]


def register_all():
    """Register all industry extractors with the factory."""
    register_production('pcaob', PCAOBExtractor)
