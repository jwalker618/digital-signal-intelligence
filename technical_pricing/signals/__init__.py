"""
DSI Signal Architecture

This package implements the signal processing pipeline for Digital Signal Intelligence:
    Extractor → Aggregator → Categorizer → Inference

Core components:
    - types: Data structures (ExtractorResult, AggregatorResult, CategorizerResult, etc.)
    - base: Abstract base classes (BaseExtractor, BaseAggregator, BaseCategorizer)
    - extractors: Data extraction from external sources (STUB implementations)
    - aggregators: Data normalization and transformation (PRODUCTION READY)
    - categorizers: Scoring and categorization logic (PRODUCTION READY)
    - inference: Pipeline orchestration functions (PRODUCTION READY)

Usage:
    from signals import ExtractorResult, BaseExtractor, SignalResult
    from signals.extractors import StubExtractor
    from signals.aggregators import ProductionAggregator
    from signals.categorizers import ProductionCategorizer
"""

# Core data types
from .types import (
    SignalType,
    OverrideAction,
    ExtractorResult,
    AggregatorResult,
    CategorizerResult,
    SignalResult,
    Override,
    CategoricalResult,
    ModelResult,
    InferenceContext,
)

# Base classes
from .base import (
    BaseExtractor,
    BaseAggregator,
    BaseCategorizer,
    BaseInferenceFunction,
    InferenceFunction,
)

__all__ = [
    # Types
    "SignalType",
    "OverrideAction",
    "ExtractorResult",
    "AggregatorResult",
    "CategorizerResult",
    "SignalResult",
    "Override",
    "CategoricalResult",
    "ModelResult",
    "InferenceContext",
    # Base classes
    "BaseExtractor",
    "BaseAggregator",
    "BaseCategorizer",
    "BaseInferenceFunction",
    "InferenceFunction",
]
