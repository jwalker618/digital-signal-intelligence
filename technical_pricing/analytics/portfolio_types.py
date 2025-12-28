"""
DSI Portfolio Analytics Types (Phase 9)

Data structures for portfolio analytics, workflow tracking,
and signal quality monitoring.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# ENUMS
# =============================================================================

class SubmissionStatus(Enum):
    """Status of a submission through the workflow."""
    RECEIVED = "received"
    PROCESSING = "processing"
    QUOTED = "quoted"
    REFERRED = "referred"
    DECLINED = "declined"
    BOUND = "bound"
    NOT_TAKEN_UP = "not_taken_up"


class ReferralReason(Enum):
    """Common referral reasons."""
    SIGNAL_THRESHOLD = "signal_threshold"
    EXPOSURE_LIMIT = "exposure_limit"
    COVERAGE_QUESTION = "coverage_question"
    PRICING_REVIEW = "pricing_review"
    UNDERWRITER_REVIEW = "underwriter_review"
    MANUAL_OVERRIDE = "manual_override"


# =============================================================================
# PORTFOLIO SUMMARY
# =============================================================================

@dataclass
class PortfolioSummary:
    """High-level portfolio metrics."""
    # Period
    as_of_date: date = field(default_factory=date.today)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    coverage: Optional[str] = None

    # Volume metrics
    total_submissions: int = 0
    total_quotes: int = 0
    total_binds: int = 0
    total_declines: int = 0

    # Premium metrics
    gross_written_premium: float = 0.0
    quoted_premium: float = 0.0
    average_premium: float = 0.0

    # Risk metrics
    average_score: float = 0.0
    average_tier: float = 0.0
    tier_distribution: Dict[int, int] = field(default_factory=dict)

    # Conversion rates
    quote_rate: float = 0.0  # Submissions → Quotes
    bind_rate: float = 0.0   # Quotes → Binds
    decline_rate: float = 0.0

    # Comparisons
    prior_period_gwp: float = 0.0
    gwp_growth: float = 0.0

    @property
    def conversion_rate(self) -> float:
        """Overall submission to bind rate."""
        if self.total_submissions == 0:
            return 0.0
        return self.total_binds / self.total_submissions


@dataclass
class TierDistribution:
    """Distribution of risks by tier."""
    coverage: str = ""
    period: str = ""

    # Current distribution
    tier_counts: Dict[int, int] = field(default_factory=dict)
    tier_premiums: Dict[int, float] = field(default_factory=dict)
    tier_percentages: Dict[int, float] = field(default_factory=dict)

    # Comparison (prior period)
    prior_tier_counts: Dict[int, int] = field(default_factory=dict)
    tier_migration: Dict[str, int] = field(default_factory=dict)
    # e.g., {"1→2": 5, "2→1": 3, "3→4": 8}


@dataclass
class SubmissionFunnel:
    """Submission to bind conversion funnel."""
    period: str = ""

    # Stages
    submissions: int = 0
    processed: int = 0
    quoted: int = 0
    referred: int = 0
    declined: int = 0
    bound: int = 0
    not_taken_up: int = 0

    # Conversion rates
    processing_rate: float = 0.0
    quote_rate: float = 0.0
    referral_rate: float = 0.0
    decline_rate: float = 0.0
    bind_rate: float = 0.0
    ntu_rate: float = 0.0

    # Average times (hours)
    avg_time_to_quote: float = 0.0
    avg_time_to_bind: float = 0.0
    avg_referral_time: float = 0.0


# =============================================================================
# SUBMISSION TRACKING
# =============================================================================

@dataclass
class SubmissionRecord:
    """Record of a submission through the workflow."""
    submission_id: str
    entity_id: str
    entity_name: str

    # Coverage
    coverage: str
    configuration: str = ""

    # Status
    status: SubmissionStatus = SubmissionStatus.RECEIVED
    received_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    quoted_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    bound_at: Optional[datetime] = None

    # DSI results
    dsi_score: float = 0.0
    dsi_tier: int = 3
    quoted_premium: float = 0.0
    bound_premium: float = 0.0

    # Workflow
    auto_approved: bool = False
    referred: bool = False
    referral_reasons: List[str] = field(default_factory=list)
    underwriter: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    # Model reference
    model_id: Optional[str] = None
    version_id: Optional[str] = None

    @property
    def time_to_quote(self) -> Optional[float]:
        """Time from receipt to quote in hours."""
        if not self.quoted_at:
            return None
        delta = self.quoted_at - self.received_at
        return delta.total_seconds() / 3600

    @property
    def time_to_decision(self) -> Optional[float]:
        """Time from receipt to decision in hours."""
        if not self.decision_at:
            return None
        delta = self.decision_at - self.received_at
        return delta.total_seconds() / 3600


@dataclass
class RiskSummary:
    """Summary of a risk for search/display."""
    entity_id: str
    entity_name: str
    coverage: str

    # Latest assessment
    score: float = 0.0
    tier: int = 3
    tier_label: str = ""
    premium: float = 0.0

    # Status
    status: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Signals summary
    signal_coverage: float = 1.0
    top_signals: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


# =============================================================================
# WORKFLOW ANALYTICS
# =============================================================================

@dataclass
class TurnaroundMetrics:
    """Workflow turnaround time metrics."""
    period: str = ""
    sample_size: int = 0

    # Average times (hours)
    avg_time_to_quote: float = 0.0
    avg_time_to_decision: float = 0.0
    avg_referral_resolution: float = 0.0

    # Percentiles
    p50_time_to_quote: float = 0.0
    p90_time_to_quote: float = 0.0
    p95_time_to_quote: float = 0.0

    # By tier
    time_by_tier: Dict[int, float] = field(default_factory=dict)

    # SLA compliance
    sla_target_hours: float = 24.0
    sla_compliance_rate: float = 0.0


@dataclass
class ReferralAnalysis:
    """Analysis of referrals."""
    period: str = ""
    total_referrals: int = 0

    # By reason
    reason_counts: Dict[str, int] = field(default_factory=dict)
    reason_percentages: Dict[str, float] = field(default_factory=dict)

    # Outcomes
    approved_count: int = 0
    declined_count: int = 0
    modified_count: int = 0
    pending_count: int = 0

    approval_rate: float = 0.0

    # Timing
    avg_resolution_time: float = 0.0

    # By underwriter
    by_underwriter: Dict[str, int] = field(default_factory=dict)


@dataclass
class UnderwriterMetrics:
    """Per-underwriter activity and performance."""
    underwriter_id: str
    underwriter_name: str = ""
    period: str = ""

    # Volume
    submissions_reviewed: int = 0
    referrals_handled: int = 0
    quotes_issued: int = 0

    # Performance
    approval_rate: float = 0.0
    avg_response_time: float = 0.0
    premium_written: float = 0.0

    # Quality
    bind_rate: float = 0.0  # Of approved quotes
    loss_ratio: float = 0.0  # Of bound business


# =============================================================================
# SIGNAL ANALYTICS
# =============================================================================

@dataclass
class SignalCoverageReport:
    """Signal extraction coverage report."""
    coverage: str = ""
    period: str = ""
    sample_size: int = 0

    # Overall coverage
    overall_coverage: float = 0.0  # % of signals extracted

    # By group
    group_coverage: Dict[str, float] = field(default_factory=dict)

    # By signal
    signal_coverage: Dict[str, float] = field(default_factory=dict)

    # Issues
    low_coverage_signals: List[str] = field(default_factory=list)
    failing_signals: List[str] = field(default_factory=list)


@dataclass
class SignalDistribution:
    """Distribution statistics for a signal."""
    signal_id: str
    signal_name: str = ""

    # Statistics
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0

    # Percentiles
    p10: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    p90: float = 0.0

    # Histogram buckets
    histogram: Dict[str, int] = field(default_factory=dict)


@dataclass
class SignalDistributions:
    """Collection of signal distributions."""
    coverage: str = ""
    group: Optional[str] = None
    distributions: Dict[str, SignalDistribution] = field(default_factory=dict)


@dataclass
class SignalIssue:
    """Issue detected with a signal."""
    signal_id: str
    signal_name: str = ""
    issue_type: str = ""  # 'low_coverage', 'high_error_rate', 'low_variance', 'drift'
    severity: str = "warning"  # 'info', 'warning', 'critical'
    description: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    recommendation: str = ""


# =============================================================================
# DASHBOARD COMPONENTS
# =============================================================================

@dataclass
class DashboardCard:
    """Summary card for dashboard."""
    title: str
    value: Any
    format: str = "number"  # 'number', 'currency', 'percentage'
    trend: Optional[float] = None  # % change from prior period
    trend_direction: str = "neutral"  # 'up', 'down', 'neutral'


@dataclass
class ChartData:
    """Generic chart data structure."""
    chart_type: str  # 'line', 'bar', 'pie', 'sankey', 'radar'
    title: str = ""
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioDashboard:
    """Complete portfolio dashboard data."""
    as_of: datetime = field(default_factory=datetime.utcnow)

    # Summary cards
    cards: List[DashboardCard] = field(default_factory=list)

    # Charts
    premium_trend: Optional[ChartData] = None
    tier_distribution: Optional[ChartData] = None
    submission_funnel: Optional[ChartData] = None
    signal_quality: Optional[ChartData] = None

    # Tables
    recent_submissions: List[SubmissionRecord] = field(default_factory=list)
    pending_referrals: List[SubmissionRecord] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)

    # Filters applied
    coverage_filter: Optional[str] = None
    date_range: Optional[Tuple[date, date]] = None
