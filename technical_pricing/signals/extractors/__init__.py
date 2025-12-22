"""
extractors/__init__.py - DSI Extractor Function Framework

This module provides the extractor function framework for all coverage lines.
Extractor functions provide raw data to .

Design Principles:
1. Data is raw from source and un-adjusted in any way.
2. ...

Organisation:
- /framework.py - Core classes, registry, and utilities
- /#base (cross-coverage), specific or group of coverages.py
"""

from .framework import (
    TTLCategory,
    TTLConfig,
    DataSource,
    SignalResult,
    ExtractionResult,
    MissingSignalStrategy,
    SignalWeightConfig,
    DataExtractor,

    EXTRACTOR_REGISTRY,

    register_extractor
)

__all__ = [
    "TTLCategory",
    "TTLConfig",
    "DataSource",
    "SignalResult",
    "ExtractionResult",
    "MissingSignalStrategy",
    "SignalWeightConfig",
    "DataExtractor",

    "EXTRACTOR_REGISTRY",

    "register_extractor"
]
