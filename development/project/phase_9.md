# Phase 9: Portfolio Analytics

## Purpose
Provide portfolio‑level analytics to evaluate performance, distribution, and behaviour across all submissions processed by the DSI engine.

## Key Deliverables
- Portfolio analytics module
- Workflow analytics
- Signal analytics (cross‑entity)
- Aggregated performance metrics

## Implementation Summary
This phase extends the analytics engine (Phase 8) to operate across entire books of business. It enables underwriters, actuaries, and product teams to analyse trends, identify anomalies, and evaluate the impact of signals and tiers at scale.

## Detailed Plan

Rebuilt portfolio analytics allowing review of all risks, submissions, and workflow across the book.

### 9.1 Portfolio Analytics Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   PORTFOLIO ANALYTICS SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     DATA LAYER                           │   │
│  │                                                          │   │
│  │  Submissions  │  Quotes  │  Binds  │  Claims  │  Signals │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   ANALYTICS ENGINE                       │   │
│  │                                                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │ PORTFOLIO   │  │ WORKFLOW    │  │ SIGNAL      │       │   │
│  │  │ METRICS     │  │ ANALYTICS   │  │ ANALYTICS   │       │   │
│  │  │             │  │             │  │             │       │   │
│  │  │ • Tier dist │  │ • Turnaround│  │ • Coverage  │       │   │
│  │  │ • Premium   │  │ • Referrals │  │ • Quality   │       │   │
│  │  │ • Growth    │  │ • Decline % │  │ • Trends    │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   VISUALIZATION LAYER                    │   │
│  │                                                          │   │
│  │  • Interactive dashboards                                │   │
│  │  • Drill-down capability                                 │   │
│  │  • Export to PDF/Excel                                   │   │
│  │  • Scheduled reports                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Core Analytics Classes

```python
class PortfolioManager:
    """
    Central portfolio analytics and management.
    """

    def get_portfolio_summary(
        self,
        coverage: str = None,
        date_range: Tuple[date, date] = None
    ) -> PortfolioSummary:
        """High-level portfolio metrics"""
        pass

    def get_tier_distribution(
        self,
        coverage: str = None,
        compare_to: str = "prior_year"
    ) -> TierDistribution:
        """Distribution of risks by tier"""
        pass

    def get_submission_funnel(
        self,
        period: str = "mtd"
    ) -> SubmissionFunnel:
        """Submission → Quote → Bind conversion"""
        pass

    def search_risks(
        self,
        query: str,  # Natural language query
        filters: Dict[str, Any] = None
    ) -> List[RiskSummary]:
        """Search portfolio with natural language"""
        pass

class WorkflowAnalytics:
    """
    Workflow efficiency and quality metrics.
    """

    def get_turnaround_times(
        self,
        period: str = "30_days"
    ) -> TurnaroundMetrics:
        """Submission to decision timing"""
        pass

    def get_referral_analysis(
        self,
        period: str = "30_days"
    ) -> ReferralAnalysis:
        """Referral reasons and outcomes"""
        pass

    def get_underwriter_metrics(
        self,
        underwriter: str = None
    ) -> UnderwriterMetrics:
        """Per-underwriter activity and performance"""
        pass

class SignalAnalytics:
    """
    Signal quality and coverage analysis.
    """

    def get_signal_coverage(
        self,
        coverage: str
    ) -> SignalCoverageReport:
        """% of signals successfully extracted"""
        pass

    def get_signal_distributions(
        self,
        coverage: str,
        signal_group: str = None
    ) -> SignalDistributions:
        """Score distributions by signal"""
        pass

    def identify_signal_issues(
        self,
        threshold: float = 0.7
    ) -> List[SignalIssue]:
        """Find signals with low coverage or quality"""
        pass
```

### 9.3 Dashboard Components

```python
@dataclass
class PortfolioDashboard:
    """Interactive portfolio dashboard"""

    # Summary cards
    total_gwp: float
    risk_count: int
    average_score: float
    tier_distribution: Dict[int, int]

    # Charts
    premium_trend: TimeSeriesChart
    tier_migration: SankeyChart
    geographic_heat_map: MapChart
    signal_quality_radar: RadarChart

    # Tables
    recent_submissions: List[SubmissionRow]
    pending_referrals: List[ReferralRow]
    alerts: List[AlertRow]

    # Filters
    coverage_filter: List[str]
    date_range: Tuple[date, date]
    tier_filter: List[int]
```

### 9.4 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create PortfolioManager | `analytics/portfolio.py` | ✅ Complete |
| Create WorkflowAnalytics | `analytics/workflow_analytics.py` | ✅ Complete |
| Create SignalAnalytics | `analytics/signal_analytics.py` | ✅ Complete |
| Implement natural language search | `analytics/search.py` | 🔲 Optional |
| Create dashboard data models | `analytics/portfolio_types.py` | ✅ Complete |
| Build dashboard API endpoints | `api/routes/analytics.py` | ✅ Complete |
| Create visualization components | `analytics/visualizations.py` | 🔲 Optional |
| Add unit tests | `tests/unit/test_portfolio_analytics.py` | ✅ Complete |

