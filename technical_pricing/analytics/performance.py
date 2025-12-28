"""
DSI Performance Tracking (Phase 8)

Compares DSI predictions to actual outcomes to measure model accuracy
and identify areas for improvement.
"""

import logging
import statistics
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    OutcomeRecord,
    PerformanceMetrics,
    TierPerformance,
    SignalPerformance,
    PerformanceAlert,
    AlertSeverity,
)


logger = logging.getLogger("dsi.analytics.performance")


# Expected loss ratios by tier (defaults)
DEFAULT_EXPECTED_LOSS_RATIOS: Dict[int, float] = {
    1: 0.35,  # Best tier - lowest expected losses
    2: 0.45,
    3: 0.55,  # Standard
    4: 0.70,
    5: 0.90,  # Worst tier - highest expected losses
}


class PerformanceTracker:
    """
    Track and analyze DSI model performance against actual outcomes.

    Capabilities:
    - Record outcome data (claims, losses) for priced risks
    - Calculate accuracy metrics (tier accuracy, correlation)
    - Identify systematic biases
    - Generate performance alerts
    - Track signal-level performance
    """

    def __init__(
        self,
        expected_loss_ratios: Optional[Dict[int, float]] = None,
        correlation_threshold: float = 0.30,
        bias_threshold: float = 0.10,
    ):
        """
        Initialize PerformanceTracker.

        Args:
            expected_loss_ratios: Expected loss ratio by tier
            correlation_threshold: Minimum correlation to consider model effective
            bias_threshold: Maximum acceptable systematic bias
        """
        self.expected_loss_ratios = expected_loss_ratios or DEFAULT_EXPECTED_LOSS_RATIOS
        self.correlation_threshold = correlation_threshold
        self.bias_threshold = bias_threshold

        # In-memory storage (replace with database in production)
        self._outcomes: List[OutcomeRecord] = []

    def record_outcome(self, outcome: OutcomeRecord) -> None:
        """
        Record an actual outcome for a priced risk.

        Args:
            outcome: The outcome record with claims/losses data
        """
        self._outcomes.append(outcome)
        logger.info(
            f"Recorded outcome for {outcome.entity_id}: "
            f"tier={outcome.dsi_tier}, loss_ratio={outcome.loss_ratio:.2%}"
        )

    def record_outcomes(self, outcomes: List[OutcomeRecord]) -> int:
        """
        Batch record multiple outcomes.

        Returns:
            Number of outcomes recorded
        """
        for outcome in outcomes:
            self._outcomes.append(outcome)
        logger.info(f"Recorded {len(outcomes)} outcomes")
        return len(outcomes)

    def get_outcomes(
        self,
        coverage: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tier: Optional[int] = None,
    ) -> List[OutcomeRecord]:
        """
        Retrieve outcomes with optional filtering.

        Args:
            coverage: Filter by coverage type
            start_date: Filter by policy inception >= date
            end_date: Filter by policy inception <= date
            tier: Filter by DSI tier

        Returns:
            Filtered list of outcomes
        """
        results = self._outcomes

        if coverage:
            results = [o for o in results if o.coverage == coverage]

        if start_date:
            results = [
                o for o in results
                if o.policy_inception and o.policy_inception >= start_date
            ]

        if end_date:
            results = [
                o for o in results
                if o.policy_inception and o.policy_inception <= end_date
            ]

        if tier is not None:
            results = [o for o in results if o.dsi_tier == tier]

        return results

    def calculate_metrics(
        self,
        coverage: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            coverage: Filter by coverage type
            start_date: Period start date
            end_date: Period end date

        Returns:
            PerformanceMetrics with accuracy, bias, and tier breakdown
        """
        outcomes = self.get_outcomes(
            coverage=coverage,
            start_date=start_date,
            end_date=end_date,
        )

        if not outcomes:
            return PerformanceMetrics(
                coverage=coverage or "",
                start_date=start_date,
                end_date=end_date,
                total_records=0,
            )

        # Basic aggregates
        total_premium = sum(o.bound_premium for o in outcomes)
        total_losses = sum(o.incurred_losses for o in outcomes)
        overall_lr = total_losses / total_premium if total_premium > 0 else 0.0

        # Score-to-loss correlation
        scores = [o.dsi_score for o in outcomes]
        loss_ratios = [o.loss_ratio for o in outcomes]
        correlation = self._calculate_correlation(scores, loss_ratios)

        # Tier accuracy - do higher tiers have higher loss ratios?
        tier_accuracy = self._calculate_tier_accuracy(outcomes)

        # Systematic bias - are we consistently over/under pricing?
        bias = self._calculate_systematic_bias(outcomes)

        # Tier breakdown
        tier_metrics = self._calculate_tier_metrics(outcomes)

        # Signal performance (if signal values available)
        signal_performance = self._calculate_signal_performance(outcomes)

        # Generate alerts
        alerts = self._generate_alerts(
            correlation=correlation,
            bias=bias,
            tier_metrics=tier_metrics,
        )

        # Calculate Gini coefficient
        gini = self._calculate_gini(outcomes)

        return PerformanceMetrics(
            period="custom",
            start_date=start_date,
            end_date=end_date,
            coverage=coverage or "",
            total_records=len(outcomes),
            total_premium=total_premium,
            total_losses=total_losses,
            tier_accuracy=tier_accuracy,
            score_correlation=correlation,
            gini_coefficient=gini,
            average_prediction_error=self._calculate_prediction_error(outcomes),
            systematic_bias=bias,
            overall_loss_ratio=overall_lr,
            tier_metrics=tier_metrics,
            signal_performance=signal_performance,
            alerts=alerts,
        )

    def _calculate_correlation(
        self,
        x: List[float],
        y: List[float],
    ) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) < 3 or len(y) < 3:
            return 0.0

        n = len(x)
        if n != len(y):
            return 0.0

        try:
            mean_x = statistics.mean(x)
            mean_y = statistics.mean(y)

            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
            denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

            if denom_x == 0 or denom_y == 0:
                return 0.0

            return numerator / (denom_x * denom_y)
        except Exception:
            return 0.0

    def _calculate_tier_accuracy(self, outcomes: List[OutcomeRecord]) -> float:
        """
        Calculate tier accuracy.

        Measures whether higher tiers have appropriately higher loss ratios.
        A score of 1.0 means perfect ordering (tier 1 < tier 2 < ... < tier 5).
        """
        if len(outcomes) < 5:
            return 0.0

        # Group by tier
        tier_lr: Dict[int, List[float]] = {}
        for o in outcomes:
            if o.dsi_tier not in tier_lr:
                tier_lr[o.dsi_tier] = []
            tier_lr[o.dsi_tier].append(o.loss_ratio)

        if len(tier_lr) < 2:
            return 0.0

        # Calculate average LR per tier
        tier_avg = {
            tier: statistics.mean(lrs) if lrs else 0.0
            for tier, lrs in tier_lr.items()
        }

        # Check ordering - higher tiers should have higher LR
        tiers_sorted = sorted(tier_avg.keys())
        correct_orderings = 0
        total_comparisons = 0

        for i in range(len(tiers_sorted) - 1):
            t1, t2 = tiers_sorted[i], tiers_sorted[i + 1]
            total_comparisons += 1
            # Higher tier should have higher or equal loss ratio
            if tier_avg[t2] >= tier_avg[t1]:
                correct_orderings += 1

        return correct_orderings / total_comparisons if total_comparisons > 0 else 0.0

    def _calculate_systematic_bias(self, outcomes: List[OutcomeRecord]) -> float:
        """
        Calculate systematic bias.

        Positive = over-pricing (actual < expected)
        Negative = under-pricing (actual > expected)
        """
        if not outcomes:
            return 0.0

        errors = []
        for o in outcomes:
            expected_lr = self.expected_loss_ratios.get(o.dsi_tier, 0.55)
            actual_lr = o.loss_ratio
            error = expected_lr - actual_lr  # Positive if we overestimated risk
            errors.append(error)

        return statistics.mean(errors) if errors else 0.0

    def _calculate_prediction_error(self, outcomes: List[OutcomeRecord]) -> float:
        """Calculate average absolute prediction error."""
        if not outcomes:
            return 0.0

        errors = []
        for o in outcomes:
            expected_lr = self.expected_loss_ratios.get(o.dsi_tier, 0.55)
            actual_lr = o.loss_ratio
            errors.append(abs(expected_lr - actual_lr))

        return statistics.mean(errors) if errors else 0.0

    def _calculate_tier_metrics(
        self,
        outcomes: List[OutcomeRecord],
    ) -> Dict[int, TierPerformance]:
        """Calculate performance metrics by tier."""
        tier_groups: Dict[int, List[OutcomeRecord]] = {}
        for o in outcomes:
            if o.dsi_tier not in tier_groups:
                tier_groups[o.dsi_tier] = []
            tier_groups[o.dsi_tier].append(o)

        result = {}
        for tier, tier_outcomes in tier_groups.items():
            premium = sum(o.bound_premium for o in tier_outcomes)
            losses = sum(o.incurred_losses for o in tier_outcomes)
            avg_lr = losses / premium if premium > 0 else 0.0
            claim_count = sum(1 for o in tier_outcomes if o.has_claims)

            result[tier] = TierPerformance(
                tier=tier,
                count=len(tier_outcomes),
                premium_volume=premium,
                average_score=statistics.mean([o.dsi_score for o in tier_outcomes]),
                average_loss_ratio=avg_lr,
                expected_loss_ratio=self.expected_loss_ratios.get(tier, 0.55),
                claim_frequency=claim_count / len(tier_outcomes) if tier_outcomes else 0.0,
                severity_average=(
                    statistics.mean([o.incurred_losses for o in tier_outcomes if o.has_claims])
                    if claim_count > 0 else 0.0
                ),
            )

        return result

    def _calculate_signal_performance(
        self,
        outcomes: List[OutcomeRecord],
    ) -> Dict[str, SignalPerformance]:
        """Calculate signal-level performance metrics."""
        # Only works if outcomes have signal_values populated
        outcomes_with_signals = [o for o in outcomes if o.signal_values]
        if not outcomes_with_signals:
            return {}

        # Get all signal IDs
        all_signals = set()
        for o in outcomes_with_signals:
            all_signals.update(o.signal_values.keys())

        result = {}
        for signal_id in all_signals:
            signal_values = []
            loss_ratios = []

            for o in outcomes_with_signals:
                if signal_id in o.signal_values:
                    signal_values.append(o.signal_values[signal_id])
                    loss_ratios.append(o.loss_ratio)

            if len(signal_values) >= 3:
                correlation = self._calculate_correlation(signal_values, loss_ratios)

                # Recommend weight changes based on correlation
                # Higher correlation = more predictive = potentially increase weight
                if correlation > 0.3:
                    weight_change = 0.1  # Suggest increase
                elif correlation < 0.1:
                    weight_change = -0.1  # Suggest decrease
                else:
                    weight_change = 0.0

                result[signal_id] = SignalPerformance(
                    signal_id=signal_id,
                    signal_name=signal_id,
                    group_id="",
                    average_score=statistics.mean(signal_values),
                    loss_ratio_correlation=correlation,
                    recommended_weight_change=weight_change,
                    change_confidence=min(len(signal_values) / 100, 0.9),
                )

        return result

    def _calculate_gini(self, outcomes: List[OutcomeRecord]) -> float:
        """
        Calculate Gini coefficient for model discrimination.

        Higher Gini = better model discrimination.
        Range: 0 (random) to 1 (perfect).
        """
        if len(outcomes) < 10:
            return 0.0

        # Sort by predicted score (lower score = better risk)
        sorted_outcomes = sorted(outcomes, key=lambda o: o.dsi_score)

        n = len(sorted_outcomes)
        total_losses = sum(o.incurred_losses for o in sorted_outcomes)
        if total_losses == 0:
            return 0.0

        # Cumulative losses
        cumulative = 0.0
        area = 0.0

        for i, o in enumerate(sorted_outcomes):
            cumulative += o.incurred_losses / total_losses
            # Area under curve
            area += (i + 1) / n - cumulative

        # Gini = 2 * area under curve
        gini = 2 * area / n

        return max(0.0, min(1.0, gini))

    def _generate_alerts(
        self,
        correlation: float,
        bias: float,
        tier_metrics: Dict[int, TierPerformance],
    ) -> List[str]:
        """Generate performance alerts based on metrics."""
        alerts = []

        # Low correlation alert
        if correlation < self.correlation_threshold:
            alerts.append(
                f"Low score-to-loss correlation ({correlation:.2f} < {self.correlation_threshold:.2f})"
            )

        # Systematic bias alert
        if abs(bias) > self.bias_threshold:
            direction = "over-pricing" if bias > 0 else "under-pricing"
            alerts.append(f"Systematic {direction} detected (bias={bias:.2%})")

        # Tier inversion alerts
        tier_avgs = [(t, m.average_loss_ratio) for t, m in tier_metrics.items()]
        tier_avgs.sort(key=lambda x: x[0])
        for i in range(len(tier_avgs) - 1):
            t1, lr1 = tier_avgs[i]
            t2, lr2 = tier_avgs[i + 1]
            if lr2 < lr1 - 0.05:  # Significant inversion
                alerts.append(
                    f"Tier inversion: Tier {t1} ({lr1:.2%}) > Tier {t2} ({lr2:.2%})"
                )

        return alerts

    def compare_periods(
        self,
        period_a: Tuple[date, date],
        period_b: Tuple[date, date],
        coverage: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare performance metrics between two periods.

        Returns:
            Dict with metric comparisons
        """
        metrics_a = self.calculate_metrics(
            coverage=coverage,
            start_date=period_a[0],
            end_date=period_a[1],
        )
        metrics_b = self.calculate_metrics(
            coverage=coverage,
            start_date=period_b[0],
            end_date=period_b[1],
        )

        return {
            "tier_accuracy": {
                "period_a": metrics_a.tier_accuracy,
                "period_b": metrics_b.tier_accuracy,
                "change": metrics_b.tier_accuracy - metrics_a.tier_accuracy,
            },
            "score_correlation": {
                "period_a": metrics_a.score_correlation,
                "period_b": metrics_b.score_correlation,
                "change": metrics_b.score_correlation - metrics_a.score_correlation,
            },
            "overall_loss_ratio": {
                "period_a": metrics_a.overall_loss_ratio,
                "period_b": metrics_b.overall_loss_ratio,
                "change": metrics_b.overall_loss_ratio - metrics_a.overall_loss_ratio,
            },
            "systematic_bias": {
                "period_a": metrics_a.systematic_bias,
                "period_b": metrics_b.systematic_bias,
                "change": metrics_b.systematic_bias - metrics_a.systematic_bias,
            },
        }
