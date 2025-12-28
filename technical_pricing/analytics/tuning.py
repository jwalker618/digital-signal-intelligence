"""
DSI Model Tuning (Phase 8)

Automated model tuning based on performance data.

Modes:
- Manual: Generate recommendations for human review
- Semi-auto: Apply recommendations with approval
- Auto: Automatically adjust within bounds

Features:
- Weight optimization suggestions
- Threshold adjustments
- Signal deprecation recommendations
- Backtesting of proposed changes
"""

import logging
import statistics
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import (
    OutcomeRecord,
    PerformanceMetrics,
    TuningRecommendation,
    TuningResult,
    BacktestResult,
    TuningMode,
    RecommendationType,
)
from .performance import PerformanceTracker


logger = logging.getLogger("dsi.analytics.tuning")


class ModelTuner:
    """
    Automated model tuning based on performance data.

    Analyzes historical performance and generates tuning
    recommendations to improve model accuracy.
    """

    def __init__(
        self,
        performance_tracker: Optional[PerformanceTracker] = None,
        weight_change_limit: float = 0.20,
        min_confidence: float = 0.60,
        min_sample_size: int = 50,
    ):
        """
        Initialize ModelTuner.

        Args:
            performance_tracker: Tracker with outcome data
            weight_change_limit: Maximum weight change per tuning cycle
            min_confidence: Minimum confidence to generate recommendation
            min_sample_size: Minimum samples for reliable analysis
        """
        self.tracker = performance_tracker or PerformanceTracker()
        self.weight_change_limit = weight_change_limit
        self.min_confidence = min_confidence
        self.min_sample_size = min_sample_size

        # Pending recommendations
        self._recommendations: Dict[str, TuningRecommendation] = {}

    def analyze_performance(
        self,
        coverage: str,
        period_months: int = 12,
    ) -> PerformanceMetrics:
        """
        Analyze model performance over period.

        Args:
            coverage: Coverage type to analyze
            period_months: Months of history to analyze

        Returns:
            PerformanceMetrics with detailed breakdown
        """
        return self.tracker.calculate_metrics(coverage=coverage)

    def generate_recommendations(
        self,
        coverage: str,
        metrics: Optional[PerformanceMetrics] = None,
    ) -> List[TuningRecommendation]:
        """
        Generate tuning recommendations based on performance.

        Args:
            coverage: Coverage type
            metrics: Pre-calculated metrics (optional)

        Returns:
            List of recommendations
        """
        if metrics is None:
            metrics = self.analyze_performance(coverage)

        if metrics.total_records < self.min_sample_size:
            logger.warning(
                f"Insufficient data for tuning: {metrics.total_records} < {self.min_sample_size}"
            )
            return []

        recommendations = []

        # 1. Weight adjustments based on signal performance
        recommendations.extend(
            self._generate_weight_recommendations(metrics)
        )

        # 2. Tier boundary adjustments
        recommendations.extend(
            self._generate_tier_recommendations(metrics)
        )

        # 3. Signal deprecation suggestions
        recommendations.extend(
            self._generate_deprecation_recommendations(metrics)
        )

        # Store recommendations
        for rec in recommendations:
            self._recommendations[rec.recommendation_id] = rec

        logger.info(f"Generated {len(recommendations)} tuning recommendations for {coverage}")
        return recommendations

    def _generate_weight_recommendations(
        self,
        metrics: PerformanceMetrics,
    ) -> List[TuningRecommendation]:
        """Generate signal weight adjustment recommendations."""
        recommendations = []

        for signal_id, perf in metrics.signal_performance.items():
            # Check correlation with outcomes
            if perf.change_confidence < self.min_confidence:
                continue

            if abs(perf.recommended_weight_change) > 0.01:
                # Limit the change
                change = max(
                    -self.weight_change_limit,
                    min(self.weight_change_limit, perf.recommended_weight_change)
                )

                if perf.loss_ratio_correlation > 0.3:
                    rationale = (
                        f"Signal {signal_id} has strong correlation ({perf.loss_ratio_correlation:.2f}) "
                        f"with loss outcomes. Increasing weight may improve model accuracy."
                    )
                elif perf.loss_ratio_correlation < 0.1:
                    rationale = (
                        f"Signal {signal_id} has weak correlation ({perf.loss_ratio_correlation:.2f}) "
                        f"with loss outcomes. Consider reducing weight."
                    )
                else:
                    continue  # Skip moderate correlations

                recommendations.append(TuningRecommendation(
                    recommendation_id=f"weight_{signal_id}_{uuid.uuid4().hex[:6]}",
                    type=RecommendationType.WEIGHT_ADJUST,
                    target_id=signal_id,
                    target_name=perf.signal_name,
                    current_value=perf.weight,
                    recommended_value=perf.weight + change,
                    expected_impact=abs(change) * perf.loss_ratio_correlation,
                    confidence=perf.change_confidence,
                    rationale=rationale,
                    evidence={
                        "correlation": perf.loss_ratio_correlation,
                        "average_score": perf.average_score,
                        "sample_size": metrics.total_records,
                    },
                ))

        return recommendations

    def _generate_tier_recommendations(
        self,
        metrics: PerformanceMetrics,
    ) -> List[TuningRecommendation]:
        """Generate tier boundary adjustment recommendations."""
        recommendations = []

        # Check for tier inversions or poor separation
        tiers = sorted(metrics.tier_metrics.keys())
        if len(tiers) < 2:
            return []

        for i in range(len(tiers) - 1):
            tier_low = metrics.tier_metrics[tiers[i]]
            tier_high = metrics.tier_metrics[tiers[i + 1]]

            # Check for inversion
            if tier_high.average_loss_ratio < tier_low.average_loss_ratio - 0.05:
                recommendations.append(TuningRecommendation(
                    recommendation_id=f"tier_inversion_{tiers[i]}_{tiers[i+1]}",
                    type=RecommendationType.TIER_BOUNDARY,
                    target_id=f"tier_{tiers[i]}_{tiers[i+1]}_boundary",
                    target_name=f"Tier {tiers[i]}/{tiers[i+1]} Boundary",
                    expected_impact=tier_low.average_loss_ratio - tier_high.average_loss_ratio,
                    confidence=0.7,
                    rationale=(
                        f"Tier inversion detected: Tier {tiers[i]} has higher loss ratio "
                        f"({tier_low.average_loss_ratio:.1%}) than Tier {tiers[i+1]} "
                        f"({tier_high.average_loss_ratio:.1%}). "
                        f"Consider adjusting score thresholds."
                    ),
                    evidence={
                        "tier_low": tiers[i],
                        "tier_high": tiers[i + 1],
                        "lr_low": tier_low.average_loss_ratio,
                        "lr_high": tier_high.average_loss_ratio,
                        "count_low": tier_low.count,
                        "count_high": tier_high.count,
                    },
                ))

            # Check for poor separation (similar loss ratios)
            lr_diff = abs(tier_high.average_loss_ratio - tier_low.average_loss_ratio)
            if lr_diff < 0.05 and tier_low.count > 20 and tier_high.count > 20:
                recommendations.append(TuningRecommendation(
                    recommendation_id=f"tier_separation_{tiers[i]}_{tiers[i+1]}",
                    type=RecommendationType.TIER_BOUNDARY,
                    target_id=f"tier_{tiers[i]}_{tiers[i+1]}_boundary",
                    target_name=f"Tier {tiers[i]}/{tiers[i+1]} Boundary",
                    expected_impact=0.05,
                    confidence=0.5,
                    rationale=(
                        f"Poor tier separation: Tier {tiers[i]} and {tiers[i+1]} have "
                        f"similar loss ratios ({tier_low.average_loss_ratio:.1%} vs "
                        f"{tier_high.average_loss_ratio:.1%}). "
                        f"Consider adjusting score thresholds for better discrimination."
                    ),
                    evidence={
                        "tier_low": tiers[i],
                        "tier_high": tiers[i + 1],
                        "lr_diff": lr_diff,
                    },
                ))

        return recommendations

    def _generate_deprecation_recommendations(
        self,
        metrics: PerformanceMetrics,
    ) -> List[TuningRecommendation]:
        """Generate signal deprecation recommendations."""
        recommendations = []

        for signal_id, perf in metrics.signal_performance.items():
            # Check for consistently low correlation
            if (
                perf.loss_ratio_correlation < 0.05 and
                perf.change_confidence > self.min_confidence
            ):
                recommendations.append(TuningRecommendation(
                    recommendation_id=f"deprecate_{signal_id}",
                    type=RecommendationType.SIGNAL_DEPRECATE,
                    target_id=signal_id,
                    target_name=perf.signal_name,
                    current_value=perf.weight,
                    recommended_value=0.0,
                    expected_impact=0.02,  # Marginal improvement from removing noise
                    confidence=perf.change_confidence,
                    rationale=(
                        f"Signal {signal_id} shows near-zero correlation "
                        f"({perf.loss_ratio_correlation:.3f}) with loss outcomes. "
                        f"Consider deprecating or replacing this signal."
                    ),
                    evidence={
                        "correlation": perf.loss_ratio_correlation,
                        "claim_frequency_correlation": perf.claim_frequency_correlation,
                        "current_weight": perf.weight,
                    },
                ))

        return recommendations

    def get_recommendation(self, recommendation_id: str) -> Optional[TuningRecommendation]:
        """Get a specific recommendation by ID."""
        return self._recommendations.get(recommendation_id)

    def list_recommendations(
        self,
        status: Optional[str] = None,
    ) -> List[TuningRecommendation]:
        """
        List all recommendations.

        Args:
            status: Filter by status (pending, approved, applied, rejected)
        """
        recs = list(self._recommendations.values())
        if status:
            recs = [r for r in recs if r.status == status]
        return recs

    def approve_recommendation(
        self,
        recommendation_id: str,
        reviewer: str,
    ) -> bool:
        """
        Approve a recommendation.

        Args:
            recommendation_id: ID of recommendation
            reviewer: Who is approving

        Returns:
            True if approved successfully
        """
        rec = self._recommendations.get(recommendation_id)
        if not rec:
            return False

        rec.status = "approved"
        rec.reviewed_by = reviewer
        rec.reviewed_at = datetime.utcnow()

        logger.info(f"Recommendation {recommendation_id} approved by {reviewer}")
        return True

    def reject_recommendation(
        self,
        recommendation_id: str,
        reviewer: str,
        reason: str = "",
    ) -> bool:
        """
        Reject a recommendation.

        Args:
            recommendation_id: ID of recommendation
            reviewer: Who is rejecting
            reason: Rejection reason

        Returns:
            True if rejected successfully
        """
        rec = self._recommendations.get(recommendation_id)
        if not rec:
            return False

        rec.status = "rejected"
        rec.reviewed_by = reviewer
        rec.reviewed_at = datetime.utcnow()
        if reason:
            rec.rationale += f" [REJECTED: {reason}]"

        logger.info(f"Recommendation {recommendation_id} rejected by {reviewer}: {reason}")
        return True

    def apply_recommendations(
        self,
        recommendation_ids: List[str],
        mode: TuningMode = TuningMode.MANUAL,
    ) -> TuningResult:
        """
        Apply approved recommendations.

        Args:
            recommendation_ids: IDs of recommendations to apply
            mode: Tuning mode (manual requires approval, auto applies directly)

        Returns:
            TuningResult with applied changes
        """
        applied = []
        skipped = []
        errors = []

        for rec_id in recommendation_ids:
            rec = self._recommendations.get(rec_id)
            if not rec:
                errors.append(f"Recommendation {rec_id} not found")
                continue

            if mode == TuningMode.MANUAL and rec.status != "approved":
                skipped.append(rec_id)
                continue

            # In production, this would actually update the configuration
            # For now, just mark as applied
            rec.status = "applied"
            applied.append(rec_id)

            logger.info(f"Applied recommendation {rec_id}: {rec.change_description}")

        return TuningResult(
            applied_recommendations=applied,
            skipped_recommendations=skipped,
            errors=errors,
            new_config_version=f"tuned_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            estimated_improvement=sum(
                self._recommendations[r].expected_impact
                for r in applied
                if r in self._recommendations
            ),
        )

    def backtest_recommendations(
        self,
        recommendation_ids: List[str],
        outcomes: Optional[List[OutcomeRecord]] = None,
    ) -> BacktestResult:
        """
        Backtest recommendations against historical data.

        Simulates what performance would have been with the proposed changes.

        Args:
            recommendation_ids: IDs of recommendations to test
            outcomes: Historical outcomes (uses tracker data if None)

        Returns:
            BacktestResult comparing current vs simulated performance
        """
        if outcomes is None:
            outcomes = self.tracker.get_outcomes()

        if len(outcomes) < self.min_sample_size:
            return BacktestResult(
                recommendations_tested=recommendation_ids,
                current_metrics=PerformanceMetrics(),
                simulated_metrics=PerformanceMetrics(),
                sample_size=len(outcomes),
            )

        # Get current performance
        current_metrics = self.tracker.calculate_metrics()

        # Simulate with changes
        # Note: Full implementation would re-score all outcomes with new weights
        # This is a simplified estimation
        simulated_metrics = PerformanceMetrics(
            total_records=current_metrics.total_records,
            total_premium=current_metrics.total_premium,
            total_losses=current_metrics.total_losses,
            overall_loss_ratio=current_metrics.overall_loss_ratio,
        )

        # Estimate improvements based on recommendation expected impacts
        improvements = {}
        total_improvement = 0.0

        for rec_id in recommendation_ids:
            rec = self._recommendations.get(rec_id)
            if rec:
                total_improvement += rec.expected_impact

        # Apply estimated improvements to metrics
        simulated_metrics.tier_accuracy = min(
            1.0,
            current_metrics.tier_accuracy + total_improvement * 0.5
        )
        simulated_metrics.score_correlation = min(
            1.0,
            current_metrics.score_correlation + total_improvement * 0.3
        )

        improvements = {
            "tier_accuracy": simulated_metrics.tier_accuracy - current_metrics.tier_accuracy,
            "score_correlation": simulated_metrics.score_correlation - current_metrics.score_correlation,
        }

        return BacktestResult(
            recommendations_tested=recommendation_ids,
            current_metrics=current_metrics,
            simulated_metrics=simulated_metrics,
            improvement=improvements,
            sample_size=len(outcomes),
        )

    def auto_tune(
        self,
        coverage: str,
        max_changes: int = 5,
    ) -> TuningResult:
        """
        Perform automatic tuning within safe bounds.

        Only applies high-confidence recommendations within limits.

        Args:
            coverage: Coverage type to tune
            max_changes: Maximum number of changes to apply

        Returns:
            TuningResult with applied changes
        """
        # Generate fresh recommendations
        recommendations = self.generate_recommendations(coverage)

        # Filter to high-confidence only
        high_confidence = [
            r for r in recommendations
            if r.confidence >= 0.75 and
            abs(r.expected_impact) > 0.01
        ]

        # Sort by expected impact
        high_confidence.sort(key=lambda r: r.expected_impact, reverse=True)

        # Take top N
        to_apply = high_confidence[:max_changes]

        if not to_apply:
            return TuningResult(
                applied_recommendations=[],
                skipped_recommendations=[r.recommendation_id for r in recommendations],
                errors=[],
            )

        # Auto-approve and apply
        for rec in to_apply:
            rec.status = "approved"
            rec.reviewed_by = "auto_tune"
            rec.reviewed_at = datetime.utcnow()

        return self.apply_recommendations(
            recommendation_ids=[r.recommendation_id for r in to_apply],
            mode=TuningMode.AUTO,
        )
