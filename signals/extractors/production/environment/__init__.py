"""
DSI Production Extractors - Environmental Data

This module provides production extractors for environmental/pollution databases.
These are FREE to use - government public environmental data.

Extractors:
    - EEAEnvironmentExtractor: European Environment Agency data
    - CanadaNPRIExtractor: Canadian National Pollutant Release Inventory

Coverage:
    - European Union (38 EEA member countries)
    - Canada (national pollutant releases)
    Note: US EPA covered in regulatory/epa_echo.py

Requirements:
    - requests: pip install requests

Usage:
    from signals.extractors.production.environment import (
        EEAEnvironmentExtractor,
        CanadaNPRIExtractor,
    )

    extractor = CanadaNPRIExtractor()
    result = extractor.extract('Suncor Energy')
"""

from .eea import EEAEnvironmentExtractor
from .canada_npri import CanadaNPRIExtractor
from ..factory import register_production

__all__ = [
    'EEAEnvironmentExtractor',
    'CanadaNPRIExtractor',
    'register_all',
]


def register_all():
    """Register all environment extractors with the factory."""
    register_production('eea_environment', EEAEnvironmentExtractor)
    register_production('canada_npri', CanadaNPRIExtractor)
