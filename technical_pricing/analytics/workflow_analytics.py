"""
DSI Workflow Analytics (Phase 9)

Workflow efficiency and quality metrics for tracking
submission processing, referrals, and underwriter performance.
"""

import logging
import statistics
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .portfolio_types import (
    SubmissionRecord,
    SubmissionStatus,
    TurnaroundMetrics,
    ReferralAnalysis,
    UnderwriterMetrics,
)


logger = logging.getLogger("dsi.analytics.workflow")


class WorkflowAnalytics:
    """
    Workflow efficiency and quality metrics.

    Tracks:
    - Turnaround times (submission to quote, to decision)
    - Referral analysis (reasons, outcomes, resolution time)
    - Underwriter performance metrics
    """

    def __init__(self):
        """Initialize WorkflowAnalytics."""
        self._submissions: List[SubmissionRecord] = []

    def set_submissions(self, submissions: List[SubmissionRecord]) -> None:
        """Set submission data to analyze."""
        self._submissions = submissions
        logger.debug(f"Loaded {len(submissions)} submissions for workflow analysis")

    def get_turnaround_times(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
        sla_target_hours: float = 24.0,
    ) -> TurnaroundMetrics:
        """
        Calculate submission to decision timing metrics.

        Args:
            coverage: Filter by coverage type
            date_range: Period to analyze
            sla_target_hours: SLA target in hours

        Returns:
            TurnaroundMetrics with timing statistics
        """
        submissions = self._filter_submissions(coverage, date_range)

        if not submissions:
            return TurnaroundMetrics(sla_target_hours=sla_target_hours)

        # Collect quote times
        quote_times = []
        decision_times = []
        referral_times = []

        for s in submissions:
            if s.time_to_quote is not None:
                quote_times.append(s.time_to_quote)

            if s.time_to_decision is not None:
                decision_times.append(s.time_to_decision)

            # Referral resolution time
            if s.referred and s.decision_at and s.quoted_at:
                referral_time = (s.decision_at - s.quoted_at).total_seconds() / 3600
                referral_times.append(referral_time)

        # Calculate statistics
        avg_quote = statistics.mean(quote_times) if quote_times else 0.0
        avg_decision = statistics.mean(decision_times) if decision_times else 0.0
        avg_referral = statistics.mean(referral_times) if referral_times else 0.0

        # Percentiles for quote time
        p50 = p90 = p95 = 0.0
        if quote_times:
            sorted_times = sorted(quote_times)
            n = len(sorted_times)
            p50 = sorted_times[int(n * 0.50)]
            p90 = sorted_times[int(n * 0.90)] if n > 10 else sorted_times[-1]
            p95 = sorted_times[int(n * 0.95)] if n > 20 else sorted_times[-1]

        # By tier
        time_by_tier: Dict[int, float] = {}
        tier_times: Dict[int, List[float]] = {}
        for s in submissions:
            if s.time_to_quote is not None:
                if s.dsi_tier not in tier_times:
                    tier_times[s.dsi_tier] = []
                tier_times[s.dsi_tier].append(s.time_to_quote)

        for tier, times in tier_times.items():
            time_by_tier[tier] = statistics.mean(times)

        # SLA compliance
        within_sla = sum(1 for t in quote_times if t <= sla_target_hours)
        sla_compliance = within_sla / len(quote_times) if quote_times else 0.0

        return TurnaroundMetrics(
            period=self._format_period(date_range),
            sample_size=len(submissions),
            avg_time_to_quote=avg_quote,
            avg_time_to_decision=avg_decision,
            avg_referral_resolution=avg_referral,
            p50_time_to_quote=p50,
            p90_time_to_quote=p90,
            p95_time_to_quote=p95,
            time_by_tier=time_by_tier,
            sla_target_hours=sla_target_hours,
            sla_compliance_rate=sla_compliance,
        )

    def get_referral_analysis(
        self,
        coverage: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> ReferralAnalysis:
        """
        Analyze referral reasons and outcomes.

        Args:
            coverage: Filter by coverage type
            date_range: Period to analyze

        Returns:
            ReferralAnalysis with breakdown by reason and outcome
        """
        submissions = self._filter_submissions(coverage, date_range)
        referred = [s for s in submissions if s.referred]

        if not referred:
            return ReferralAnalysis(period=self._format_period(date_range))

        # Count by reason
        reason_counts: Dict[str, int] = {}
        for s in referred:
            for reason in s.referral_reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

        total_referrals = len(referred)
        reason_percentages = {
            reason: count / total_referrals
            for reason, count in reason_counts.items()
        }

        # Outcomes
        approved = sum(1 for s in referred if s.status == SubmissionStatus.BOUND)
        declined = sum(1 for s in referred if s.status == SubmissionStatus.DECLINED)
        pending = sum(1 for s in referred if s.status == SubmissionStatus.REFERRED)
        modified = sum(1 for s in referred if s.status in [
            SubmissionStatus.QUOTED, SubmissionStatus.NOT_TAKEN_UP
        ])

        approval_rate = approved / total_referrals if total_referrals > 0 else 0.0

        # Resolution times
        resolution_times = []
        for s in referred:
            if s.decision_at and s.quoted_at:
                delta = (s.decision_at - s.quoted_at).total_seconds() / 3600
                resolution_times.append(delta)

        avg_resolution = statistics.mean(resolution_times) if resolution_times else 0.0

        # By underwriter
        by_underwriter: Dict[str, int] = {}
        for s in referred:
            if s.underwriter:
                by_underwriter[s.underwriter] = by_underwriter.get(s.underwriter, 0) + 1

        return ReferralAnalysis(
            period=self._format_period(date_range),
            total_referrals=total_referrals,
            reason_counts=reason_counts,
            reason_percentages=reason_percentages,
            approved_count=approved,
            declined_count=declined,
            modified_count=modified,
            pending_count=pending,
            approval_rate=approval_rate,
            avg_resolution_time=avg_resolution,
            by_underwriter=by_underwriter,
        )

    def get_underwriter_metrics(
        self,
        underwriter: Optional[str] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> UnderwriterMetrics:
        """
        Get per-underwriter activity and performance metrics.

        Args:
            underwriter: Specific underwriter (or None for aggregate)
            date_range: Period to analyze

        Returns:
            UnderwriterMetrics for the underwriter
        """
        submissions = self._filter_submissions(None, date_range)

        if underwriter:
            submissions = [s for s in submissions if s.underwriter == underwriter]
            name = underwriter
        else:
            name = "All Underwriters"

        if not submissions:
            return UnderwriterMetrics(
                underwriter_id=underwriter or "all",
                underwriter_name=name,
                period=self._format_period(date_range),
            )

        # Volume
        reviewed = len(submissions)
        referrals = sum(1 for s in submissions if s.referred)
        quotes = sum(1 for s in submissions if s.status in [
            SubmissionStatus.QUOTED,
            SubmissionStatus.BOUND,
            SubmissionStatus.NOT_TAKEN_UP,
        ])

        # Performance
        bound = [s for s in submissions if s.status == SubmissionStatus.BOUND]
        approved = len(bound)
        approval_rate = approved / reviewed if reviewed > 0 else 0.0

        # Response time
        response_times = [
            s.time_to_decision for s in submissions
            if s.time_to_decision is not None
        ]
        avg_response = statistics.mean(response_times) if response_times else 0.0

        # Premium
        premium = sum(s.bound_premium for s in bound)

        # Bind rate (of quotes)
        bind_rate = approved / quotes if quotes > 0 else 0.0

        return UnderwriterMetrics(
            underwriter_id=underwriter or "all",
            underwriter_name=name,
            period=self._format_period(date_range),
            submissions_reviewed=reviewed,
            referrals_handled=referrals,
            quotes_issued=quotes,
            approval_rate=approval_rate,
            avg_response_time=avg_response,
            premium_written=premium,
            bind_rate=bind_rate,
        )

    def get_all_underwriter_metrics(
        self,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> List[UnderwriterMetrics]:
        """
        Get metrics for all underwriters.

        Args:
            date_range: Period to analyze

        Returns:
            List of UnderwriterMetrics, one per underwriter
        """
        # Get unique underwriters
        underwriters = set()
        for s in self._submissions:
            if s.underwriter:
                underwriters.add(s.underwriter)

        return [
            self.get_underwriter_metrics(uw, date_range)
            for uw in sorted(underwriters)
        ]

    def get_bottlenecks(
        self,
        threshold_hours: float = 24.0,
    ) -> List[Dict[str, Any]]:
        """
        Identify workflow bottlenecks.

        Args:
            threshold_hours: Time threshold to flag as bottleneck

        Returns:
            List of bottleneck issues
        """
        bottlenecks = []

        # Check pending referrals
        pending_referrals = [
            s for s in self._submissions
            if s.status == SubmissionStatus.REFERRED
        ]

        for s in pending_referrals:
            hours_pending = (datetime.utcnow() - s.received_at).total_seconds() / 3600
            if hours_pending > threshold_hours:
                bottlenecks.append({
                    "type": "pending_referral",
                    "submission_id": s.submission_id,
                    "entity_name": s.entity_name,
                    "hours_pending": hours_pending,
                    "underwriter": s.underwriter,
                    "reasons": s.referral_reasons,
                })

        # Check slow quotes
        slow_quotes = [
            s for s in self._submissions
            if s.time_to_quote and s.time_to_quote > threshold_hours
        ]

        if len(slow_quotes) > len(self._submissions) * 0.2:
            bottlenecks.append({
                "type": "slow_quoting",
                "count": len(slow_quotes),
                "percentage": len(slow_quotes) / len(self._submissions) if self._submissions else 0,
                "avg_time": statistics.mean([s.time_to_quote for s in slow_quotes]),
            })

        return bottlenecks

    def _filter_submissions(
        self,
        coverage: Optional[str],
        date_range: Optional[Tuple[date, date]],
    ) -> List[SubmissionRecord]:
        """Filter submissions by coverage and date range."""
        results = self._submissions

        if coverage:
            results = [s for s in results if s.coverage == coverage]

        if date_range:
            start_date, end_date = date_range
            results = [
                s for s in results
                if start_date <= s.received_at.date() <= end_date
            ]

        return results

    def _format_period(self, date_range: Optional[Tuple[date, date]]) -> str:
        """Format date range as string."""
        if date_range:
            return f"{date_range[0]} to {date_range[1]}"
        return "all"
