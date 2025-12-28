"""
Tests for DSI Analytics Module (Phase 8)

Tests performance tracking, cohort analysis, and model tuning.
"""

import pytest
from datetime import date, datetime

from technical_pricing.analytics import (
    OutcomeRecord,
    PerformanceMetrics,
    TierPerformance,
    CohortDefinition,
    TuningRecommendation,
    TuningMode,
    PerformanceTracker,
    CohortAnalyzer,
    ModelTuner,
)
from technical_pricing.analytics.types import RecommendationType


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_outcomes():
    """Generate sample outcome records for testing."""
    outcomes = []

    # Tier 1 - best risks, low losses
    for i in range(20):
        outcomes.append(OutcomeRecord(
            entity_id=f"tier1_{i}",
            model_id=f"model_t1_{i}",
            dsi_score=850 - i * 5,
            dsi_tier=1,
            quoted_premium=50_000,
            bound_premium=48_000,
            claim_count=1 if i < 3 else 0,
            incurred_losses=10_000 if i < 3 else 0,
            coverage="fi",
            signal_values={"cyber_posture": 85, "financial_health": 90},
        ))

    # Tier 2
    for i in range(25):
        outcomes.append(OutcomeRecord(
            entity_id=f"tier2_{i}",
            model_id=f"model_t2_{i}",
            dsi_score=700 - i * 4,
            dsi_tier=2,
            quoted_premium=60_000,
            bound_premium=58_000,
            claim_count=1 if i < 8 else 0,
            incurred_losses=25_000 if i < 8 else 0,
            coverage="fi",
            signal_values={"cyber_posture": 70, "financial_health": 75},
        ))

    # Tier 3 - average risks
    for i in range(30):
        outcomes.append(OutcomeRecord(
            entity_id=f"tier3_{i}",
            model_id=f"model_t3_{i}",
            dsi_score=550 - i * 3,
            dsi_tier=3,
            quoted_premium=75_000,
            bound_premium=72_000,
            claim_count=1 if i < 15 else 0,
            incurred_losses=40_000 if i < 15 else 0,
            coverage="fi",
            signal_values={"cyber_posture": 55, "financial_health": 60},
        ))

    # Tier 4
    for i in range(15):
        outcomes.append(OutcomeRecord(
            entity_id=f"tier4_{i}",
            model_id=f"model_t4_{i}",
            dsi_score=350 - i * 5,
            dsi_tier=4,
            quoted_premium=100_000,
            bound_premium=95_000,
            claim_count=1 if i < 10 else 0,
            incurred_losses=70_000 if i < 10 else 0,
            coverage="fi",
            signal_values={"cyber_posture": 40, "financial_health": 45},
        ))

    # Tier 5 - worst risks, high losses
    for i in range(10):
        outcomes.append(OutcomeRecord(
            entity_id=f"tier5_{i}",
            model_id=f"model_t5_{i}",
            dsi_score=200 - i * 10,
            dsi_tier=5,
            quoted_premium=150_000,
            bound_premium=140_000,
            claim_count=1 if i < 8 else 0,
            incurred_losses=120_000 if i < 8 else 0,
            coverage="fi",
            signal_values={"cyber_posture": 25, "financial_health": 30},
        ))

    return outcomes


@pytest.fixture
def performance_tracker(sample_outcomes):
    """Performance tracker with sample data."""
    tracker = PerformanceTracker()
    tracker.record_outcomes(sample_outcomes)
    return tracker


@pytest.fixture
def cohort_analyzer(sample_outcomes):
    """Cohort analyzer with sample data."""
    analyzer = CohortAnalyzer()
    analyzer.set_outcomes(sample_outcomes)
    return analyzer


# =============================================================================
# OUTCOME RECORD TESTS
# =============================================================================

class TestOutcomeRecord:
    """Tests for OutcomeRecord dataclass."""

    def test_loss_ratio_calculation(self):
        """Loss ratio should be incurred/bound premium."""
        outcome = OutcomeRecord(
            entity_id="test",
            model_id="model_1",
            bound_premium=100_000,
            incurred_losses=45_000,
        )
        assert outcome.loss_ratio == 0.45

    def test_loss_ratio_zero_premium(self):
        """Loss ratio should be 0 when premium is 0."""
        outcome = OutcomeRecord(
            entity_id="test",
            model_id="model_1",
            bound_premium=0,
            incurred_losses=10_000,
        )
        assert outcome.loss_ratio == 0.0

    def test_has_claims(self):
        """has_claims should be True when there are claims."""
        outcome = OutcomeRecord(
            entity_id="test",
            model_id="model_1",
            claim_count=1,
            incurred_losses=10_000,
        )
        assert outcome.has_claims is True

    def test_no_claims(self):
        """has_claims should be False when no claims."""
        outcome = OutcomeRecord(
            entity_id="test",
            model_id="model_1",
            claim_count=0,
            incurred_losses=0,
        )
        assert outcome.has_claims is False


# =============================================================================
# PERFORMANCE TRACKER TESTS
# =============================================================================

class TestPerformanceTracker:
    """Tests for PerformanceTracker."""

    def test_record_outcome(self):
        """Should record an outcome."""
        tracker = PerformanceTracker()
        outcome = OutcomeRecord(
            entity_id="test",
            model_id="model_1",
            dsi_tier=2,
            bound_premium=50_000,
            incurred_losses=20_000,
        )
        tracker.record_outcome(outcome)

        outcomes = tracker.get_outcomes()
        assert len(outcomes) == 1
        assert outcomes[0].entity_id == "test"

    def test_filter_by_coverage(self, performance_tracker):
        """Should filter outcomes by coverage."""
        outcomes = performance_tracker.get_outcomes(coverage="fi")
        assert len(outcomes) == 100

        outcomes = performance_tracker.get_outcomes(coverage="cyber")
        assert len(outcomes) == 0

    def test_filter_by_tier(self, performance_tracker):
        """Should filter outcomes by tier."""
        tier1_outcomes = performance_tracker.get_outcomes(tier=1)
        assert len(tier1_outcomes) == 20

        tier5_outcomes = performance_tracker.get_outcomes(tier=5)
        assert len(tier5_outcomes) == 10

    def test_calculate_metrics(self, performance_tracker):
        """Should calculate comprehensive metrics."""
        metrics = performance_tracker.calculate_metrics(coverage="fi")

        assert metrics.total_records == 100
        assert metrics.total_premium > 0
        assert metrics.total_losses > 0
        assert 0 <= metrics.overall_loss_ratio <= 1

    def test_tier_metrics(self, performance_tracker):
        """Should calculate metrics by tier."""
        metrics = performance_tracker.calculate_metrics(coverage="fi")

        assert 1 in metrics.tier_metrics
        assert 5 in metrics.tier_metrics

        # Higher tiers should generally have higher loss ratios
        tier1_lr = metrics.tier_metrics[1].average_loss_ratio
        tier5_lr = metrics.tier_metrics[5].average_loss_ratio
        assert tier5_lr > tier1_lr

    def test_tier_accuracy(self, performance_tracker):
        """Should calculate tier ordering accuracy."""
        metrics = performance_tracker.calculate_metrics(coverage="fi")

        # With good tier separation, accuracy should be high
        assert metrics.tier_accuracy > 0.5

    def test_signal_performance(self, performance_tracker):
        """Should calculate signal-level performance."""
        metrics = performance_tracker.calculate_metrics(coverage="fi")

        # Should have signal performance data
        assert len(metrics.signal_performance) > 0
        assert "cyber_posture" in metrics.signal_performance

    def test_empty_data(self):
        """Should handle empty data gracefully."""
        tracker = PerformanceTracker()
        metrics = tracker.calculate_metrics(coverage="fi")

        assert metrics.total_records == 0
        assert metrics.tier_accuracy == 0.0


# =============================================================================
# COHORT ANALYZER TESTS
# =============================================================================

class TestCohortAnalyzer:
    """Tests for CohortAnalyzer."""

    def test_define_cohort(self, cohort_analyzer):
        """Should define a cohort."""
        cohort = cohort_analyzer.define_cohort(
            name="Tier 1 FI",
            criteria={"coverage": "fi", "tier": 1},
        )

        assert cohort.name == "Tier 1 FI"
        assert cohort.member_count == 20

    def test_get_cohort_members(self, cohort_analyzer):
        """Should retrieve cohort members."""
        cohort = cohort_analyzer.define_cohort(
            name="Tier 1 FI",
            criteria={"coverage": "fi", "tier": 1},
        )

        members = cohort_analyzer.get_cohort_members(cohort.cohort_id)
        assert len(members) == 20
        assert all(m.dsi_tier == 1 for m in members)

    def test_compare_cohorts(self, cohort_analyzer):
        """Should compare two cohorts."""
        cohort_a = cohort_analyzer.define_cohort(
            name="Tier 1",
            criteria={"tier": 1},
        )
        cohort_b = cohort_analyzer.define_cohort(
            name="Tier 5",
            criteria={"tier": 5},
        )

        comparison = cohort_analyzer.compare_cohorts(
            cohort_a.cohort_id,
            cohort_b.cohort_id,
        )

        assert comparison.cohort_a.name == "Tier 1"
        assert comparison.cohort_b.name == "Tier 5"
        assert "loss_ratio" in comparison.metric_comparisons

        # Tier 5 should have higher loss ratio
        lr_diff = comparison.metric_comparisons["loss_ratio"]["diff"]
        assert lr_diff > 0

    def test_identify_outliers(self, cohort_analyzer):
        """Should identify outlier risks."""
        cohort = cohort_analyzer.define_cohort(
            name="All FI",
            criteria={"coverage": "fi"},
        )

        outliers = cohort_analyzer.identify_outliers(
            cohort.cohort_id,
            metric="loss_ratio",
            threshold=1.5,
        )

        # Should find some outliers
        assert isinstance(outliers, list)
        for outlier in outliers:
            assert outlier.z_score >= 1.5

    def test_suggest_cohort_adjustments(self, cohort_analyzer):
        """Should suggest adjustments for cohort."""
        cohort = cohort_analyzer.define_cohort(
            name="Tier 3",
            criteria={"tier": 3},
        )

        recommendations = cohort_analyzer.suggest_cohort_adjustments(cohort.cohort_id)

        # May or may not have recommendations depending on data
        assert isinstance(recommendations, list)

    def test_auto_discover_cohorts(self, cohort_analyzer):
        """Should auto-discover meaningful cohorts."""
        cohorts = cohort_analyzer.auto_discover_cohorts(
            coverage="fi",
            min_size=5,
        )

        assert len(cohorts) > 0
        assert any("Tier" in c.name for c in cohorts)


# =============================================================================
# MODEL TUNER TESTS
# =============================================================================

class TestModelTuner:
    """Tests for ModelTuner."""

    def test_generate_recommendations(self, performance_tracker):
        """Should generate tuning recommendations."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        assert isinstance(recommendations, list)
        # Should have at least some recommendations with this data

    def test_approve_recommendation(self, performance_tracker):
        """Should approve a recommendation."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        if recommendations:
            rec_id = recommendations[0].recommendation_id
            result = tuner.approve_recommendation(rec_id, reviewer="test_user")

            rec = tuner.get_recommendation(rec_id)
            assert rec.status == "approved"
            assert rec.reviewed_by == "test_user"

    def test_reject_recommendation(self, performance_tracker):
        """Should reject a recommendation."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        if recommendations:
            rec_id = recommendations[0].recommendation_id
            result = tuner.reject_recommendation(
                rec_id,
                reviewer="test_user",
                reason="Not applicable",
            )

            rec = tuner.get_recommendation(rec_id)
            assert rec.status == "rejected"

    def test_apply_recommendations(self, performance_tracker):
        """Should apply approved recommendations."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        if recommendations:
            # Approve first
            rec_id = recommendations[0].recommendation_id
            tuner.approve_recommendation(rec_id, reviewer="test")

            # Apply
            result = tuner.apply_recommendations([rec_id])

            assert rec_id in result.applied_recommendations

    def test_backtest_recommendations(self, performance_tracker):
        """Should backtest recommendations."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        if recommendations:
            rec_ids = [r.recommendation_id for r in recommendations[:2]]
            result = tuner.backtest_recommendations(rec_ids)

            assert result.sample_size > 0
            assert result.current_metrics is not None
            assert result.simulated_metrics is not None

    def test_auto_tune(self, performance_tracker):
        """Should perform auto-tuning."""
        tuner = ModelTuner(performance_tracker=performance_tracker)
        result = tuner.auto_tune(coverage="fi", max_changes=3)

        # Should have some applied or skipped
        assert isinstance(result.applied_recommendations, list)
        assert isinstance(result.skipped_recommendations, list)

    def test_insufficient_data(self):
        """Should handle insufficient data gracefully."""
        tracker = PerformanceTracker()
        # Add only a few records
        for i in range(5):
            tracker.record_outcome(OutcomeRecord(
                entity_id=f"test_{i}",
                model_id=f"model_{i}",
                coverage="fi",
            ))

        tuner = ModelTuner(performance_tracker=tracker, min_sample_size=50)
        recommendations = tuner.generate_recommendations(coverage="fi")

        # Should return empty list due to insufficient data
        assert recommendations == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAnalyticsIntegration:
    """Integration tests for analytics workflow."""

    def test_full_workflow(self, sample_outcomes):
        """Test complete analytics workflow."""
        # 1. Track performance
        tracker = PerformanceTracker()
        tracker.record_outcomes(sample_outcomes)

        # 2. Calculate metrics
        metrics = tracker.calculate_metrics(coverage="fi")
        assert metrics.total_records == 100

        # 3. Analyze cohorts
        analyzer = CohortAnalyzer()
        analyzer.set_outcomes(sample_outcomes)

        cohort_good = analyzer.define_cohort("Good Risks", {"tier": [1, 2]})
        cohort_bad = analyzer.define_cohort("Poor Risks", {"tier": [4, 5]})

        comparison = analyzer.compare_cohorts(
            cohort_good.cohort_id,
            cohort_bad.cohort_id,
        )

        # Poor risks should have higher loss ratio
        assert comparison.metric_comparisons["loss_ratio"]["cohort_b"] > \
               comparison.metric_comparisons["loss_ratio"]["cohort_a"]

        # 4. Generate tuning recommendations
        tuner = ModelTuner(performance_tracker=tracker)
        recommendations = tuner.generate_recommendations(coverage="fi")

        # 5. Backtest
        if recommendations:
            backtest = tuner.backtest_recommendations(
                [r.recommendation_id for r in recommendations[:2]]
            )
            assert backtest.sample_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
