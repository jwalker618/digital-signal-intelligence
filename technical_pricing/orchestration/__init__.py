"""
DSI Multi-Coverage Orchestration Module (Phase 10)

Coordinates pricing across multiple coverages and locales
from a single submission.

Components:
- types: Data structures for orchestration
- multi_coverage: MultiCoverageOrchestrator for execution
- locale_detection: LocaleDetector for auto-detecting locales
- aggregator: ResultsAggregator for cross-coverage analysis
"""

from .types import (
    # Enums
    LocaleDetectionMode,
    ExecutionStatus,
    # Request/Response
    MultiCoverageRequest,
    MultiCoverageResult,
    # Planning
    ExecutionPlan,
    PlannedRun,
    # Results
    CoverageResult,
    # Package
    PackageDiscount,
    PackageRecommendation,
    # Configuration
    CoverageDetectionRule,
    OrchestrationConfig,
    SharedSignalCache,
)

from .multi_coverage import MultiCoverageOrchestrator

from .locale_detection import (
    LocaleDetector,
    LocaleDetectorConfig,
    LocaleMatch,
)

from .aggregator import (
    ResultsAggregator,
    AggregatedAnalysis,
    CrossCoverageInsight,
    CoverageComparison,
    summarize_result,
)


__all__ = [
    # Types - Enums
    "LocaleDetectionMode",
    "ExecutionStatus",
    # Types - Request/Response
    "MultiCoverageRequest",
    "MultiCoverageResult",
    # Types - Planning
    "ExecutionPlan",
    "PlannedRun",
    # Types - Results
    "CoverageResult",
    # Types - Package
    "PackageDiscount",
    "PackageRecommendation",
    # Types - Configuration
    "CoverageDetectionRule",
    "OrchestrationConfig",
    "SharedSignalCache",
    # Orchestrator
    "MultiCoverageOrchestrator",
    # Locale Detection
    "LocaleDetector",
    "LocaleDetectorConfig",
    "LocaleMatch",
    # Aggregator
    "ResultsAggregator",
    "AggregatedAnalysis",
    "CrossCoverageInsight",
    "CoverageComparison",
    "summarize_result",
]
