"""DSI Signals - Shared signal infrastructure for all assessment layers."""
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

# V7 Phase 1 — evidence taxonomy & promotion mechanics
from .evidence import (
    EvidenceGrade,
    EvidenceSource,
    EvidenceRoleViolation,
    EVIDENCE_GRADES,
    bump_evidence,
    evidence_compare,
    evidence_at_or_above,
    evidence_rank,
    default_cap_for,
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
    # V7 Phase 1 — evidence
    "EvidenceGrade",
    "EvidenceSource",
    "EvidenceRoleViolation",
    "EVIDENCE_GRADES",
    "bump_evidence",
    "evidence_compare",
    "evidence_at_or_above",
    "evidence_rank",
    "default_cap_for",
]
