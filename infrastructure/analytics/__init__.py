"""
DSI Analytics Module (Phase 8 + 9)

Performance monitoring, cohort analysis, model tuning, and portfolio analytics.

Modules:
- types: Data types for outcomes, metrics, cohorts (Phase 8)
- performance: PerformanceTracker for comparing predictions to outcomes
- cohorts: CohortAnalyzer for comparing similar risks
- tuning: ModelTuner for generating tuning recommendations
- portfolio_types: Data types for portfolio analytics (Phase 9)
- portfolio: PortfolioManager for portfolio-level analytics
- workflow_analytics: WorkflowAnalytics for workflow efficiency
- signal_analytics: SignalAnalytics for signal quality monitoring
"""

# Phase 8: Performance Monitoring
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

# Phase 9: Portfolio Analytics
from .portfolio_types import (
    PortfolioSummary,
    TierDistribution,
    SubmissionFunnel,
    SubmissionRecord,
    RiskSummary,
    SubmissionStatus,
    TurnaroundMetrics,
    ReferralAnalysis,
    UnderwriterMetrics,
    SignalCoverageReport,
    SignalDistribution,
    SignalDistributions,
    SignalIssue,
    PortfolioDashboard,
)
from .portfolio import PortfolioManager
from .workflow_analytics import WorkflowAnalytics
from .signal_analytics import SignalAnalytics

__all__ = [
    # Phase 8: Performance Types
    "OutcomeRecord",
    "PerformanceMetrics",
    "TierPerformance",
    "SignalPerformance",
    "CohortDefinition",
    "CohortComparison",
    "TuningRecommendation",
    "TuningMode",
    # Phase 8: Analyzers
    "PerformanceTracker",
    "CohortAnalyzer",
    "ModelTuner",
    # Phase 9: Portfolio Types
    "PortfolioSummary",
    "TierDistribution",
    "SubmissionFunnel",
    "SubmissionRecord",
    "RiskSummary",
    "SubmissionStatus",
    "TurnaroundMetrics",
    "ReferralAnalysis",
    "UnderwriterMetrics",
    "SignalCoverageReport",
    "SignalDistribution",
    "SignalDistributions",
    "SignalIssue",
    "PortfolioDashboard",
    # Phase 9: Analytics
    "PortfolioManager",
    "WorkflowAnalytics",
    "SignalAnalytics",
]
