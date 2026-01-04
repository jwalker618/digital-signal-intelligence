"""
DSI Production Extractors - Industry Registries

This module provides production extractors for industry-specific registries.
These are FREE to use - public professional registries.

Extractors:
    - PCAOBExtractor: PCAOB registered auditor firm status
    - AviationSafetyExtractor: Aviation Safety Network accident database

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.industry import (
        PCAOBExtractor,
        AviationSafetyExtractor,
    )

    extractor = PCAOBExtractor()
    result = extractor.extract('Deloitte & Touche LLP')

    asn = AviationSafetyExtractor()
    result = asn.extract('Delta Air Lines')
"""

from .pcaob import PCAOBExtractor
from .aviation_safety import AviationSafetyExtractor
from ..factory import register_production

__all__ = [
    'PCAOBExtractor',
    'AviationSafetyExtractor',
    'register_all',
]


def register_all():
    """Register all industry extractors with the factory."""
    register_production('pcaob', PCAOBExtractor)
    register_production('aviation_safety', AviationSafetyExtractor)
