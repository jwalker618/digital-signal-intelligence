"""
extractors/__init__.py - DSI Extractor Function Framework

DSI uses a logical architectural with a clear seperation of tasks. These are:
1/. Extractor
    Fetches raw data from a source (API, FTP, database, etc.). One extractor can provide data for multiple signals.
2/. Aggregator
    Structures/transforms raw extractor data, optimising it for scoring/categorisation. One aggregator can serve multiple signals.
3/. Categorizer
    Applies scoring/categorisation logic to produce the final signal value. One categorizer type (e.g., threshold_bucket for "size" signals) can be reused across many signals.
4/. Inference
    Orchestrates extractor(s) → aggregator(s) → categorizer(s) for ONE specific signal. 

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
