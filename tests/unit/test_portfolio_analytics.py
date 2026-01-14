"""
Tests for DSI Portfolio Analytics (Phase 9)

Tests portfolio management, workflow analytics, and signal quality monitoring.
"""

import pytest
from datetime import date, datetime, timedelta

from analytics import (
    PortfolioManager,
    WorkflowAnalytics,
    SubmissionRecord,
    SubmissionStatus,
    PortfolioSummary,
    TierDistribution,
    SubmissionFunnel,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_submissions():
    """Generate sample submission records for testing."""
    submissions = []
    base_date = datetime.utcnow() - timedelta(days=30)

    # Generate 50 submissions across tiers
    for i in range(50):
        tier = (i % 5) + 1
        status_options = [
            SubmissionStatus.BOUND,
            SubmissionStatus.QUOTED,
            SubmissionStatus.DECLINED,
            SubmissionStatus.REFERRED,
            SubmissionStatus.NOT_TAKEN_UP,
        ]
        status = status_options[i % len(status_options)]

        received = base_date + timedelta(hours=i * 12)
        processed = received + timedelta(hours=2)
        quoted = processed + timedelta(hours=4) if status != SubmissionStatus.DECLINED else None
        decision = quoted + timedelta(hours=8) if quoted else processed + timedelta(hours=4)

        submissions.append(SubmissionRecord(
            submission_id=f"SUB_{i:04d}",
            entity_id=f"ENT_{i:04d}",
            entity_name=f"Company {i}",
            coverage="fi",
            configuration="fi_general",
            status=status,
            received_at=received,
            processed_at=processed,
            quoted_at=quoted,
            decision_at=decision,
            bound_at=decision if status == SubmissionStatus.BOUND else None,
            dsi_score=850 - (tier - 1) * 150 + (i % 50),
            dsi_tier=tier,
            quoted_premium=50000 + tier * 10000,
            bound_premium=48000 + tier * 9500 if status == SubmissionStatus.BOUND else 0,
            auto_approved=tier <= 2,
            referred=status == SubmissionStatus.REFERRED or tier == 3,
            referral_reasons=["pricing_review"] if tier == 3 else [],
            underwriter=f"UW_{i % 3}" if tier >= 3 else None,
        ))

    return submissions


@pytest.fixture
def portfolio_manager(sample_submissions):
    """Portfolio manager with sample data."""
    manager = PortfolioManager()
    manager.record_submissions(sample_submissions)
    return manager


@pytest.fixture
def workflow_analytics(sample_submissions):
    """Workflow analytics with sample data."""
    analytics = WorkflowAnalytics()
    analytics.set_submissions(sample_submissions)
    return analytics


# =============================================================================
# PORTFOLIO MANAGER TESTS
# =============================================================================

class TestPortfolioManager:
    """Tests for PortfolioManager."""

    def test_record_submission(self):
        """Should record a submission."""
        manager = PortfolioManager()
        submission = SubmissionRecord(
            submission_id="TEST_001",
            entity_id="ENT_001",
            entity_name="Test Company",
            coverage="fi",
        )
        manager.record_submission(submission)

        results = manager.get_submissions()
        assert len(results) == 1
        assert results[0].submission_id == "TEST_001"

    def test_filter_by_coverage(self, portfolio_manager):
        """Should filter submissions by coverage."""
        results = portfolio_manager.get_submissions(coverage="fi")
        assert len(results) == 50

        results = portfolio_manager.get_submissions(coverage="cyber")
        assert len(results) == 0

    def test_filter_by_status(self, portfolio_manager):
        """Should filter submissions by status."""
        bound = portfolio_manager.get_submissions(status=SubmissionStatus.BOUND)
        assert len(bound) == 10  # 1 in 5

    def test_filter_by_tier(self, portfolio_manager):
        """Should filter submissions by tier."""
        tier1 = portfolio_manager.get_submissions(tier=1)
        assert len(tier1) == 10  # 1 in 5

    def test_get_portfolio_summary(self, portfolio_manager):
        """Should calculate portfolio summary."""
        summary = portfolio_manager.get_portfolio_summary(coverage="fi")

        assert summary.total_submissions == 50
        assert summary.total_binds == 10
        assert summary.gross_written_premium > 0
        assert summary.average_tier > 0

    def test_get_tier_distribution(self, portfolio_manager):
        """Should calculate tier distribution."""
        dist = portfolio_manager.get_tier_distribution(coverage="fi")

        # Should have all 5 tiers
        assert len(dist.tier_counts) == 5
        for tier in range(1, 6):
            assert tier in dist.tier_counts
            assert dist.tier_counts[tier] == 10  # Even distribution

    def test_get_submission_funnel(self, portfolio_manager):
        """Should calculate submission funnel."""
        funnel = portfolio_manager.get_submission_funnel(coverage="fi")

        assert funnel.submissions == 50
        assert funnel.bound > 0
        assert funnel.declined > 0
        assert funnel.quote_rate > 0
        assert funnel.bind_rate > 0

    def test_search_risks(self, portfolio_manager):
        """Should search risks by query."""
        results = portfolio_manager.search_risks(query="Company 1")

        # Should match Company 1, 10, 11, 12, etc.
        assert len(results) > 0
        assert all("Company 1" in r.entity_name for r in results)

    def test_search_with_filters(self, portfolio_manager):
        """Should search with filters."""
        results = portfolio_manager.search_risks(
            filters={"tier": 1, "status": "bound"}
        )

        assert all(r.tier == 1 for r in results)
        assert all(r.status == "bound" for r in results)

    def test_get_dashboard(self, portfolio_manager):
        """Should generate dashboard data."""
        dashboard = portfolio_manager.get_dashboard(coverage="fi")

        assert len(dashboard.cards) > 0
        assert dashboard.tier_distribution is not None
        assert dashboard.submission_funnel is not None
        assert len(dashboard.recent_submissions) > 0


# =============================================================================
# WORKFLOW ANALYTICS TESTS
# =============================================================================

class TestWorkflowAnalytics:
    """Tests for WorkflowAnalytics."""

    def test_get_turnaround_times(self, workflow_analytics):
        """Should calculate turnaround metrics."""
        metrics = workflow_analytics.get_turnaround_times()

        assert metrics.sample_size == 50
        assert metrics.avg_time_to_quote > 0
        assert metrics.avg_time_to_decision > 0
        assert metrics.p50_time_to_quote > 0
        assert metrics.sla_compliance_rate > 0

    def test_turnaround_by_tier(self, workflow_analytics):
        """Should break down turnaround by tier."""
        metrics = workflow_analytics.get_turnaround_times()

        assert len(metrics.time_by_tier) > 0

    def test_get_referral_analysis(self, workflow_analytics):
        """Should analyze referrals."""
        analysis = workflow_analytics.get_referral_analysis()

        assert analysis.total_referrals > 0
        # Check that we have some breakdown

    def test_get_underwriter_metrics(self, workflow_analytics):
        """Should get underwriter metrics."""
        metrics = workflow_analytics.get_underwriter_metrics(underwriter="UW_0")

        assert metrics.underwriter_id == "UW_0"
        assert metrics.submissions_reviewed > 0

    def test_get_all_underwriter_metrics(self, workflow_analytics):
        """Should get metrics for all underwriters."""
        all_metrics = workflow_analytics.get_all_underwriter_metrics()

        assert len(all_metrics) > 0
        assert all(m.underwriter_id is not None for m in all_metrics)

    def test_get_bottlenecks(self, workflow_analytics):
        """Should identify bottlenecks."""
        bottlenecks = workflow_analytics.get_bottlenecks(threshold_hours=1.0)

        # May or may not have bottlenecks depending on test data
        assert isinstance(bottlenecks, list)


# =============================================================================
# SUBMISSION RECORD TESTS
# =============================================================================

class TestSubmissionRecord:
    """Tests for SubmissionRecord dataclass."""

    def test_time_to_quote(self):
        """Should calculate time to quote."""
        now = datetime.utcnow()
        record = SubmissionRecord(
            submission_id="TEST",
            entity_id="ENT",
            entity_name="Test",
            coverage="fi",
            received_at=now - timedelta(hours=6),
            quoted_at=now,
        )

        assert record.time_to_quote == pytest.approx(6.0, abs=0.1)

    def test_time_to_quote_none(self):
        """Should return None if not quoted."""
        record = SubmissionRecord(
            submission_id="TEST",
            entity_id="ENT",
            entity_name="Test",
            coverage="fi",
        )

        assert record.time_to_quote is None

    def test_time_to_decision(self):
        """Should calculate time to decision."""
        now = datetime.utcnow()
        record = SubmissionRecord(
            submission_id="TEST",
            entity_id="ENT",
            entity_name="Test",
            coverage="fi",
            received_at=now - timedelta(hours=10),
            decision_at=now,
        )

        assert record.time_to_decision == pytest.approx(10.0, abs=0.1)


# =============================================================================
# PORTFOLIO SUMMARY TESTS
# =============================================================================

class TestPortfolioSummary:
    """Tests for PortfolioSummary dataclass."""

    def test_conversion_rate(self):
        """Should calculate conversion rate."""
        summary = PortfolioSummary(
            total_submissions=100,
            total_binds=25,
        )

        assert summary.conversion_rate == 0.25

    def test_conversion_rate_zero_submissions(self):
        """Should handle zero submissions."""
        summary = PortfolioSummary(total_submissions=0)

        assert summary.conversion_rate == 0.0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPortfolioIntegration:
    """Integration tests for portfolio analytics workflow."""

    def test_full_workflow(self, sample_submissions):
        """Test complete portfolio analytics workflow."""
        # 1. Set up managers
        portfolio = PortfolioManager()
        portfolio.record_submissions(sample_submissions)

        workflow = WorkflowAnalytics()
        workflow.set_submissions(sample_submissions)

        # 2. Get portfolio overview
        summary = portfolio.get_portfolio_summary(coverage="fi")
        assert summary.total_submissions == 50

        # 3. Get tier distribution
        tier_dist = portfolio.get_tier_distribution(coverage="fi")
        assert len(tier_dist.tier_counts) == 5

        # 4. Get funnel
        funnel = portfolio.get_submission_funnel(coverage="fi")
        assert funnel.submissions == 50

        # 5. Get turnaround
        turnaround = workflow.get_turnaround_times()
        assert turnaround.avg_time_to_quote > 0

        # 6. Analyze referrals
        referrals = workflow.get_referral_analysis()
        assert referrals.total_referrals >= 0

        # 7. Generate dashboard
        dashboard = portfolio.get_dashboard(coverage="fi")
        assert len(dashboard.cards) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
