"""
DSI Production Extractors - Maritime Registries

This module provides production extractors that query maritime databases.
These are FREE to use - public maritime safety data.

Extractors:
    - IMOGISISExtractor: IMO GISIS ship and company data
    - IOSARegistryExtractor: IATA IOSA airline audit registry

Requirements:
    - requests: pip install requests

Usage:
    from technical_pricing.signals.extractors.production.maritime import (
        IMOGISISExtractor,
        IOSARegistryExtractor,
    )

    extractor = IMOGISISExtractor()
    result = extractor.extract('9074729')  # IMO number
"""

from .imo_gisis import IMOGISISExtractor
from .iosa_registry import IOSARegistryExtractor
from ..factory import register_production

__all__ = [
    'IMOGISISExtractor',
    'IOSARegistryExtractor',
    'register_all',
]


def register_all():
    """Register all maritime extractors with the factory."""
    register_production('imo_gisis', IMOGISISExtractor)
    register_production('iosa_registry', IOSARegistryExtractor)
