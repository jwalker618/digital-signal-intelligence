"""
extractors/#coverage#.py - Coverage Inference Functions
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .base import (
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

logger = logging.getLogger(__name__)


