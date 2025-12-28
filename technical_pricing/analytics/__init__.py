"""
DSI Analytics Module (Phase 8)

Performance monitoring, cohort analysis, and model tuning.

Modules:
- types: Data types for outcomes, metrics, cohorts
- performance: PerformanceTracker for comparing predictions to outcomes
- cohorts: CohortAnalyzer for comparing similar risks
- tuning: ModelTuner for generating tuning recommendations
"""

from .types import (
    OutcomeRecord,
    PerformanceMetrics,
    TierPerformance,
    SignalPerformance,
    CohortDefinition,
    CohortComparison,
    TuningRecommendation,
    TuningMode,
)
from .performance import PerformanceTracker
from .cohorts import CohortAnalyzer
from .tuning import ModelTuner

__all__ = [
    # Types
    "OutcomeRecord",
    "PerformanceMetrics",
    "TierPerformance",
    "SignalPerformance",
    "CohortDefinition",
    "CohortComparison",
    "TuningRecommendation",
    "TuningMode",
    # Analyzers
    "PerformanceTracker",
    "CohortAnalyzer",
    "ModelTuner",
]
