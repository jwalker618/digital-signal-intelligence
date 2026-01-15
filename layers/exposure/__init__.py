"""
Exposure Shadow Layer (Phase 17)

Exposure magnitude and complexity scoring from observable signals.
Enables TIV estimation without client-provided data.

This layer extends DSI to estimate exposure size and complexity
using the same signal infrastructure as risk scoring.
"""

# Types and enums
from .types import (
    # Enums
    ProxyTier,
    ExposureBand,
    ComplexityCategory,
    ExposureSignalType,
    # Configuration types
    ExposureBandConfig,
    ComplexityCategoryConfig,
    ExposureFeatureConfig,
    ExposureGroupConfig,
    CohortPriorConfig,
    ExposureConfig,
    # Signal output types
    ExposureSignalOutput,
    ExposureGroupScore,
    # Result types
    ExposureResult,
    ComplexityResult,
    CombinedExposureResult,
    # Cohort types
    CohortPrior,
    CohortMatch,
    # Rule types
    ExposureRuleResult,
    ExposureDecision,
)

# Scorers
from .scorer import ExposureScorer
from .complexity import ComplexityScorer

# Band mapping
from .band_mapper import BandMapper

# Cohort management
from .cohort_manager import CohortManager

# Rules engine
from .rules_engine import ExposureRulesEngine


__all__ = [
    # Enums
    'ProxyTier',
    'ExposureBand',
    'ComplexityCategory',
    'ExposureSignalType',
    # Configuration types
    'ExposureBandConfig',
    'ComplexityCategoryConfig',
    'ExposureFeatureConfig',
    'ExposureGroupConfig',
    'CohortPriorConfig',
    'ExposureConfig',
    # Signal output types
    'ExposureSignalOutput',
    'ExposureGroupScore',
    # Result types
    'ExposureResult',
    'ComplexityResult',
    'CombinedExposureResult',
    # Cohort types
    'CohortPrior',
    'CohortMatch',
    # Rule types
    'ExposureRuleResult',
    'ExposureDecision',
    # Classes
    'ExposureScorer',
    'ComplexityScorer',
    'BandMapper',
    'CohortManager',
    'ExposureRulesEngine',
]
