"""
DSI Portfolio Manager (Phase 9)

Central portfolio analytics and management for reviewing
all risks, submissions, and workflow across the book.
"""

import logging
import statistics
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .portfolio_types import (
    PortfolioSummary,
    TierDistribution,
    SubmissionFunnel,
    SubmissionRecord,
    RiskSummary,
    SubmissionStatus,
    DashboardCard,
    ChartData,
    PortfolioDashboard,
)


logger = logging.getLogger("dsi.analytics.portfolio")


class PortfolioManager:
    """
    Central portfolio analytics and management.

    Provides:
    - Portfolio summary metrics
    - Tier distribution analysis
    - Submission funnel tracking
    - Risk search and filtering
    - Dashboard data generation
    """

    def __init__(self):
        """Initialize PortfolioManager."""
        # In-memory storage (replace with database in production)
        self._submissions: List[SubmissionRecord] = []

    def record_submission(self, submission: SubmissionRecord) -> None:
        """Record a submission."""
        self._submissions.append(submission)
        logger.debug(f"Recorded submission {submission.submission_id}")

    def record_submissions(self, submissions: List[SubmissionRecord]) -> int:
        """Batch record submissions."""
        self._submissions.extend(submissions)
        return len(submissions)

    def get_submissions(
        self,
        coverage: Optional[str] = None,
        status: Optional[SubmissionStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tier: Optional[int] = None,
    ) -> List[SubmissionRecord]:
        """
        Retrieve submissions with optional filtering.

        Args:
            coverage: Filter by coverage type
            status: Filter by submission status
            start_date: Filter by received_at >= date
            end_date: Filter by received_at <= date
            tier: Filter by DSI tier

        Returns:
            Filtered list of submissions
        """
        results = self._submissions

        if coverage:
            results = [s for s in results if s.coverage == coverage]

        if status:
            results = [s for s in results if s.status == status]

        if start_date:
            results = [
                s for s in results
                if s.received_at.date() >= start_date
            ]

        if end_date:
            results = [
                s for s in results
                if s.received_at.date() <= end_date
            ]

        if tier is not None:
            results = [s for s in results if s.dsi_tier == tier]

        return results

    def get_portfolio_summary(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> PortfolioSummary:
        """
        Get high-level portfolio metrics.

        Args:
            coverage: Filter by coverage type
            date_range: (start_date, end_date) tuple

        Returns:
            PortfolioSummary with key metrics
        """
        start_date = date_range[0] if date_range else None
        end_date = date_range[1] if date_range else None

        submissions = self.get_submissions(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )

        if not submissions:
            return PortfolioSummary(
                coverage=coverage,
                period_start=start_date,
                period_end=end_date,
            )

        # Count by status
        total = len(submissions)
        quoted = sum(1 for s in submissions if s.status in [
            SubmissionStatus.QUOTED,
            SubmissionStatus.BOUND,
            SubmissionStatus.NOT_TAKEN_UP,
        ])
        bound = sum(1 for s in submissions if s.status == SubmissionStatus.BOUND)
        declined = sum(1 for s in submissions if s.status == SubmissionStatus.DECLINED)

        # Premium metrics
        gwp = sum(s.bound_premium for s in submissions if s.status == SubmissionStatus.BOUND)
        quoted_premium = sum(s.quoted_premium for s in submissions if s.quoted_premium > 0)
        avg_premium = gwp / bound if bound > 0 else 0.0

        # Risk metrics
        scores = [s.dsi_score for s in submissions if s.dsi_score > 0]
        tiers = [s.dsi_tier for s in submissions if s.dsi_tier > 0]

        avg_score = statistics.mean(scores) if scores else 0.0
        avg_tier = statistics.mean(tiers) if tiers else 0.0

        # Tier distribution
        tier_dist = {}
        for s in submissions:
            tier_dist[s.dsi_tier] = tier_dist.get(s.dsi_tier, 0) + 1

        # Conversion rates
        quote_rate = quoted / total if total > 0 else 0.0
        bind_rate = bound / quoted if quoted > 0 else 0.0
        decline_rate = declined / total if total > 0 else 0.0

        return PortfolioSummary(
            as_of_date=date.today(),
            period_start=start_date,
            period_end=end_date,
            coverage=coverage,
            total_submissions=total,
            total_quotes=quoted,
            total_binds=bound,
            total_declines=declined,
            gross_written_premium=gwp,
            quoted_premium=quoted_premium,
            average_premium=avg_premium,
            average_score=avg_score,
            average_tier=avg_tier,
            tier_distribution=tier_dist,
            quote_rate=quote_rate,
            bind_rate=bind_rate,
            decline_rate=decline_rate,
        )

    def get_tier_distribution(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
        compare_to: str = "prior_period",
    ) -> TierDistribution:
        """
        Get distribution of risks by tier.

        Args:
            coverage: Filter by coverage type
            date_range: Current period
            compare_to: Comparison type ('prior_period', 'prior_year')

        Returns:
            TierDistribution with current and comparison data
        """
        start_date = date_range[0] if date_range else None
        end_date = date_range[1] if date_range else None

        # Current period
        submissions = self.get_submissions(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )

        # Count and premium by tier
        tier_counts: Dict[int, int] = {}
        tier_premiums: Dict[int, float] = {}

        for s in submissions:
            tier = s.dsi_tier
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if s.status == SubmissionStatus.BOUND:
                tier_premiums[tier] = tier_premiums.get(tier, 0.0) + s.bound_premium

        # Percentages
        total = len(submissions)
        tier_percentages = {
            t: count / total if total > 0 else 0.0
            for t, count in tier_counts.items()
        }

        # Prior period comparison
        prior_counts: Dict[int, int] = {}
        if date_range and compare_to == "prior_period":
            period_length = (end_date - start_date).days
            prior_start = start_date - timedelta(days=period_length)
            prior_end = start_date - timedelta(days=1)

            prior_submissions = self.get_submissions(
                coverage=coverage,
                start_date=prior_start,
                end_date=prior_end,
            )

            for s in prior_submissions:
                prior_counts[s.dsi_tier] = prior_counts.get(s.dsi_tier, 0) + 1

        return TierDistribution(
            coverage=coverage or "",
            period=f"{start_date} to {end_date}" if date_range else "all",
            tier_counts=tier_counts,
            tier_premiums=tier_premiums,
            tier_percentages=tier_percentages,
            prior_tier_counts=prior_counts,
        )

    def get_submission_funnel(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> SubmissionFunnel:
        """
        Get submission to bind conversion funnel.

        Args:
            coverage: Filter by coverage type
            date_range: Period to analyze

        Returns:
            SubmissionFunnel with stage counts and rates
        """
        start_date = date_range[0] if date_range else None
        end_date = date_range[1] if date_range else None

        submissions = self.get_submissions(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )

        if not submissions:
            return SubmissionFunnel()

        total = len(submissions)

        # Count by status
        status_counts = {status: 0 for status in SubmissionStatus}
        for s in submissions:
            status_counts[s.status] += 1

        processed = total - status_counts[SubmissionStatus.RECEIVED]
        quoted = (
            status_counts[SubmissionStatus.QUOTED] +
            status_counts[SubmissionStatus.BOUND] +
            status_counts[SubmissionStatus.NOT_TAKEN_UP]
        )
        referred = status_counts[SubmissionStatus.REFERRED]
        declined = status_counts[SubmissionStatus.DECLINED]
        bound = status_counts[SubmissionStatus.BOUND]
        ntu = status_counts[SubmissionStatus.NOT_TAKEN_UP]

        # Times
        quote_times = [
            s.time_to_quote for s in submissions
            if s.time_to_quote is not None
        ]
        decision_times = [
            s.time_to_decision for s in submissions
            if s.time_to_decision is not None
        ]

        return SubmissionFunnel(
            period=f"{start_date} to {end_date}" if date_range else "all",
            submissions=total,
            processed=processed,
            quoted=quoted,
            referred=referred,
            declined=declined,
            bound=bound,
            not_taken_up=ntu,
            processing_rate=processed / total if total > 0 else 0.0,
            quote_rate=quoted / total if total > 0 else 0.0,
            referral_rate=referred / total if total > 0 else 0.0,
            decline_rate=declined / total if total > 0 else 0.0,
            bind_rate=bound / quoted if quoted > 0 else 0.0,
            ntu_rate=ntu / quoted if quoted > 0 else 0.0,
            avg_time_to_quote=statistics.mean(quote_times) if quote_times else 0.0,
            avg_time_to_bind=statistics.mean(decision_times) if decision_times else 0.0,
        )

    def search_risks(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[RiskSummary]:
        """
        Search portfolio with optional query and filters.

        Args:
            query: Search term (matches entity name)
            filters: Additional filters (coverage, tier, status, etc.)
            limit: Maximum results

        Returns:
            List of matching risk summaries
        """
        results = self._submissions
        filters = filters or {}

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in s.entity_name.lower() or
                   query_lower in s.entity_id.lower()
            ]

        # Apply filters
        if "coverage" in filters:
            results = [s for s in results if s.coverage == filters["coverage"]]

        if "tier" in filters:
            if isinstance(filters["tier"], list):
                results = [s for s in results if s.dsi_tier in filters["tier"]]
            else:
                results = [s for s in results if s.dsi_tier == filters["tier"]]

        if "status" in filters:
            results = [s for s in results if s.status.value == filters["status"]]

        if "min_score" in filters:
            results = [s for s in results if s.dsi_score >= filters["min_score"]]

        if "max_score" in filters:
            results = [s for s in results if s.dsi_score <= filters["max_score"]]

        # Sort by most recent
        results = sorted(results, key=lambda s: s.received_at, reverse=True)

        # Convert to summaries
        summaries = []
        for s in results[:limit]:
            summaries.append(RiskSummary(
                entity_id=s.entity_id,
                entity_name=s.entity_name,
                coverage=s.coverage,
                score=s.dsi_score,
                tier=s.dsi_tier,
                premium=s.bound_premium or s.quoted_premium,
                status=s.status.value,
                last_updated=s.decision_at or s.received_at,
            ))

        return summaries

    def get_dashboard(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> PortfolioDashboard:
        """
        Generate complete dashboard data.

        Args:
            coverage: Filter by coverage type
            date_range: Period to display

        Returns:
            PortfolioDashboard with all components
        """
        summary = self.get_portfolio_summary(coverage, date_range)
        tier_dist = self.get_tier_distribution(coverage, date_range)
        funnel = self.get_submission_funnel(coverage, date_range)

        # Build cards
        cards = [
            DashboardCard(
                title="Gross Written Premium",
                value=summary.gross_written_premium,
                format="currency",
                trend=summary.gwp_growth if summary.gwp_growth else None,
                trend_direction="up" if summary.gwp_growth > 0 else "down" if summary.gwp_growth < 0 else "neutral",
            ),
            DashboardCard(
                title="Total Submissions",
                value=summary.total_submissions,
                format="number",
            ),
            DashboardCard(
                title="Bind Rate",
                value=summary.bind_rate,
                format="percentage",
            ),
            DashboardCard(
                title="Average Score",
                value=summary.average_score,
                format="number",
            ),
        ]

        # Tier distribution chart
        tier_chart = ChartData(
            chart_type="pie",
            title="Tier Distribution",
            labels=[f"Tier {t}" for t in sorted(tier_dist.tier_counts.keys())],
            datasets=[{
                "data": [tier_dist.tier_counts.get(t, 0) for t in sorted(tier_dist.tier_counts.keys())],
            }],
        )

        # Funnel chart
        funnel_chart = ChartData(
            chart_type="bar",
            title="Submission Funnel",
            labels=["Submissions", "Quoted", "Bound"],
            datasets=[{
                "data": [funnel.submissions, funnel.quoted, funnel.bound],
            }],
        )

        # Recent submissions
        start_date = date_range[0] if date_range else None
        end_date = date_range[1] if date_range else None
        recent = self.get_submissions(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )
        recent = sorted(recent, key=lambda s: s.received_at, reverse=True)[:10]

        # Pending referrals
        pending = [
            s for s in self._submissions
            if s.status == SubmissionStatus.REFERRED
        ]
        pending = sorted(pending, key=lambda s: s.received_at)[:10]

        return PortfolioDashboard(
            as_of=datetime.utcnow(),
            cards=cards,
            tier_distribution=tier_chart,
            submission_funnel=funnel_chart,
            recent_submissions=recent,
            pending_referrals=pending,
            coverage_filter=coverage,
            date_range=date_range,
        )

    def get_premium_trend(
        self,
        coverage: Optional[str] = None,
        period_months: int = 12,
        granularity: str = "month",
    ) -> ChartData:
        """
        Get premium trend over time.

        Args:
            coverage: Filter by coverage type
            period_months: How many months to show
            granularity: 'month' or 'week'

        Returns:
            ChartData for line chart
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_months * 30)

        submissions = self.get_submissions(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )

        # Group by month
        monthly_premium: Dict[str, float] = {}
        for s in submissions:
            if s.status == SubmissionStatus.BOUND and s.bound_premium > 0:
                month_key = s.received_at.strftime("%Y-%m")
                monthly_premium[month_key] = monthly_premium.get(month_key, 0) + s.bound_premium

        # Sort by month
        sorted_months = sorted(monthly_premium.keys())

        return ChartData(
            chart_type="line",
            title="Premium Trend",
            labels=sorted_months,
            datasets=[{
                "label": "GWP",
                "data": [monthly_premium[m] for m in sorted_months],
            }],
        )
