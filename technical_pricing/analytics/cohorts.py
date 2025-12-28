"""
DSI Cohort Analysis (Phase 8)

Compare performance of similar risks to identify patterns
and opportunities for model improvement.

Use cases:
- Large banks vs other large banks
- Tech companies by tier
- Geographic performance differences
- New vs renewal business
"""

import logging
import statistics
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .types import (
    OutcomeRecord,
    CohortDefinition,
    CohortComparison,
    OutlierRisk,
    TuningRecommendation,
    RecommendationType,
)


logger = logging.getLogger("dsi.analytics.cohorts")


class CohortAnalyzer:
    """
    Analyze and compare cohorts of similar risks.

    Cohorts are defined by filtering criteria and compared
    on various performance metrics.
    """

    def __init__(self):
        """Initialize CohortAnalyzer."""
        self._cohorts: Dict[str, CohortDefinition] = {}
        self._outcomes: List[OutcomeRecord] = []

    def set_outcomes(self, outcomes: List[OutcomeRecord]) -> None:
        """
        Set the outcome data to analyze.

        Args:
            outcomes: List of outcome records
        """
        self._outcomes = outcomes
        logger.info(f"Loaded {len(outcomes)} outcomes for cohort analysis")

    def define_cohort(
        self,
        name: str,
        criteria: Dict[str, Any],
        description: str = "",
        created_by: str = "system",
    ) -> CohortDefinition:
        """
        Create a cohort definition.

        Criteria examples:
        - {"coverage": "fi"} - All FI coverage
        - {"tier": [1, 2]} - Tier 1 or 2
        - {"revenue_min": 100000000} - Revenue >= 100M
        - {"dsi_score_min": 700} - Score >= 700
        - {"coverage": "cyber", "tier": 1} - Cyber tier 1

        Args:
            name: Cohort name
            criteria: Filter criteria
            description: Optional description
            created_by: User creating the cohort

        Returns:
            CohortDefinition
        """
        cohort_id = str(uuid.uuid4())[:8]

        # Count members
        members = self._filter_outcomes(criteria)

        cohort = CohortDefinition(
            cohort_id=cohort_id,
            name=name,
            description=description,
            criteria=criteria,
            created_by=created_by,
            member_count=len(members),
        )

        self._cohorts[cohort_id] = cohort
        logger.info(f"Created cohort '{name}' with {len(members)} members")

        return cohort

    def get_cohort(self, cohort_id: str) -> Optional[CohortDefinition]:
        """Get cohort by ID."""
        return self._cohorts.get(cohort_id)

    def list_cohorts(self) -> List[CohortDefinition]:
        """List all defined cohorts."""
        return list(self._cohorts.values())

    def get_cohort_members(self, cohort_id: str) -> List[OutcomeRecord]:
        """Get all outcomes in a cohort."""
        cohort = self._cohorts.get(cohort_id)
        if not cohort:
            return []
        return self._filter_outcomes(cohort.criteria)

    def _filter_outcomes(self, criteria: Dict[str, Any]) -> List[OutcomeRecord]:
        """Filter outcomes by criteria."""
        results = self._outcomes

        for key, value in criteria.items():
            if key == "coverage":
                results = [o for o in results if o.coverage == value]

            elif key == "tier" or key == "dsi_tier":
                if isinstance(value, list):
                    results = [o for o in results if o.dsi_tier in value]
                else:
                    results = [o for o in results if o.dsi_tier == value]

            elif key == "revenue_min":
                # Requires signal_values to have revenue
                results = [
                    o for o in results
                    if o.signal_values.get("revenue", 0) >= value
                ]

            elif key == "revenue_max":
                results = [
                    o for o in results
                    if o.signal_values.get("revenue", float("inf")) <= value
                ]

            elif key == "dsi_score_min":
                results = [o for o in results if o.dsi_score >= value]

            elif key == "dsi_score_max":
                results = [o for o in results if o.dsi_score <= value]

            elif key == "has_claims":
                results = [o for o in results if o.has_claims == value]

            elif key == "configuration":
                results = [o for o in results if o.configuration == value]

        return results

    def compare_cohorts(
        self,
        cohort_a_id: str,
        cohort_b_id: str,
        metrics: Optional[List[str]] = None,
    ) -> CohortComparison:
        """
        Compare two cohorts on specified metrics.

        Args:
            cohort_a_id: First cohort ID
            cohort_b_id: Second cohort ID
            metrics: Metrics to compare (default: all)

        Returns:
            CohortComparison with metric values and insights
        """
        cohort_a = self._cohorts.get(cohort_a_id)
        cohort_b = self._cohorts.get(cohort_b_id)

        if not cohort_a or not cohort_b:
            raise ValueError("Cohort not found")

        members_a = self._filter_outcomes(cohort_a.criteria)
        members_b = self._filter_outcomes(cohort_b.criteria)

        if not members_a or not members_b:
            return CohortComparison(
                cohort_a=cohort_a,
                cohort_b=cohort_b,
                metric_comparisons={},
                insights=["Insufficient data for comparison"],
            )

        # Default metrics
        if metrics is None:
            metrics = [
                "count", "loss_ratio", "claim_frequency",
                "average_score", "average_premium", "average_losses"
            ]

        comparisons: Dict[str, Dict[str, float]] = {}
        significant_diffs: List[str] = []
        insights: List[str] = []

        for metric in metrics:
            val_a = self._calculate_cohort_metric(members_a, metric)
            val_b = self._calculate_cohort_metric(members_b, metric)
            diff = val_b - val_a

            comparisons[metric] = {
                "cohort_a": val_a,
                "cohort_b": val_b,
                "diff": diff,
            }

            # Check significance (simple threshold-based)
            if metric == "loss_ratio" and abs(diff) > 0.10:
                significant_diffs.append(metric)
                higher = cohort_b.name if diff > 0 else cohort_a.name
                insights.append(
                    f"Significant loss ratio difference: {higher} is {abs(diff):.1%} higher"
                )

            if metric == "claim_frequency" and abs(diff) > 0.10:
                significant_diffs.append(metric)

            if metric == "average_score" and abs(diff) > 50:
                significant_diffs.append(metric)
                insights.append(
                    f"Score difference of {abs(diff):.0f} points between cohorts"
                )

        return CohortComparison(
            cohort_a=cohort_a,
            cohort_b=cohort_b,
            metric_comparisons=comparisons,
            significant_differences=significant_diffs,
            insights=insights,
        )

    def _calculate_cohort_metric(
        self,
        outcomes: List[OutcomeRecord],
        metric: str,
    ) -> float:
        """Calculate a specific metric for a cohort."""
        if not outcomes:
            return 0.0

        if metric == "count":
            return float(len(outcomes))

        if metric == "loss_ratio":
            total_premium = sum(o.bound_premium for o in outcomes)
            total_losses = sum(o.incurred_losses for o in outcomes)
            return total_losses / total_premium if total_premium > 0 else 0.0

        if metric == "claim_frequency":
            claims = sum(1 for o in outcomes if o.has_claims)
            return claims / len(outcomes)

        if metric == "average_score":
            return statistics.mean([o.dsi_score for o in outcomes])

        if metric == "average_premium":
            return statistics.mean([o.bound_premium for o in outcomes])

        if metric == "average_losses":
            return statistics.mean([o.incurred_losses for o in outcomes])

        if metric == "average_tier":
            return statistics.mean([o.dsi_tier for o in outcomes])

        return 0.0

    def identify_outliers(
        self,
        cohort_id: str,
        metric: str = "loss_ratio",
        threshold: float = 2.0,
    ) -> List[OutlierRisk]:
        """
        Find risks that deviate significantly from cohort norm.

        Args:
            cohort_id: Cohort to analyze
            metric: Metric to check for outliers
            threshold: Standard deviations for outlier threshold

        Returns:
            List of outlier risks
        """
        cohort = self._cohorts.get(cohort_id)
        if not cohort:
            return []

        members = self._filter_outcomes(cohort.criteria)
        if len(members) < 5:
            return []

        # Get metric values
        values = []
        for o in members:
            if metric == "loss_ratio":
                values.append((o, o.loss_ratio))
            elif metric == "dsi_score":
                values.append((o, o.dsi_score))
            elif metric == "incurred_losses":
                values.append((o, o.incurred_losses))
            else:
                continue

        if not values:
            return []

        # Calculate mean and std
        metric_values = [v[1] for v in values]
        mean = statistics.mean(metric_values)
        std = statistics.stdev(metric_values) if len(metric_values) > 1 else 0.0

        if std == 0:
            return []

        # Find outliers
        outliers = []
        for outcome, value in values:
            z_score = abs(value - mean) / std
            if z_score >= threshold:
                direction = "above" if value > mean else "below"
                outliers.append(OutlierRisk(
                    entity_id=outcome.entity_id,
                    model_id=outcome.model_id,
                    cohort_id=cohort_id,
                    metric=metric,
                    value=value,
                    cohort_mean=mean,
                    cohort_std=std,
                    z_score=z_score,
                    notes=[
                        f"{z_score:.1f} standard deviations {direction} cohort mean",
                        f"Cohort: {cohort.name}",
                    ],
                ))

        return sorted(outliers, key=lambda x: x.z_score, reverse=True)

    def suggest_cohort_adjustments(
        self,
        cohort_id: str,
    ) -> List[TuningRecommendation]:
        """
        Suggest model adjustments based on cohort performance.

        Analyzes whether the cohort is systematically over/under-priced
        and suggests weight or threshold adjustments.

        Args:
            cohort_id: Cohort to analyze

        Returns:
            List of tuning recommendations
        """
        cohort = self._cohorts.get(cohort_id)
        if not cohort:
            return []

        members = self._filter_outcomes(cohort.criteria)
        if len(members) < 10:
            return []

        recommendations = []

        # Calculate cohort performance
        total_premium = sum(o.bound_premium for o in members)
        total_losses = sum(o.incurred_losses for o in members)
        actual_lr = total_losses / total_premium if total_premium > 0 else 0.0

        # Expected LR based on tier distribution
        expected_lr = 0.0
        for o in members:
            tier_expected = {1: 0.35, 2: 0.45, 3: 0.55, 4: 0.70, 5: 0.90}
            expected_lr += o.bound_premium * tier_expected.get(o.dsi_tier, 0.55)
        expected_lr = expected_lr / total_premium if total_premium > 0 else 0.55

        # Check for systematic mis-pricing
        diff = actual_lr - expected_lr
        if abs(diff) > 0.10:
            # Cohort is mis-priced by more than 10%
            direction = "under-priced" if diff > 0 else "over-priced"

            # Find which signals are most different in this cohort
            # compared to overall population (if signal data available)
            signal_analysis = self._analyze_cohort_signals(members)

            for signal_id, signal_diff in signal_analysis.items():
                if abs(signal_diff) > 0.5:  # Significant deviation
                    weight_change = -0.05 if diff > 0 else 0.05
                    recommendations.append(TuningRecommendation(
                        recommendation_id=f"cohort_{cohort_id}_{signal_id}",
                        type=RecommendationType.WEIGHT_ADJUST,
                        target_id=signal_id,
                        target_name=signal_id,
                        current_value=1.0,  # Placeholder
                        recommended_value=1.0 + weight_change,
                        expected_impact=abs(diff) * 0.3,  # Estimated
                        confidence=0.6,
                        rationale=(
                            f"Cohort '{cohort.name}' is {direction} by {abs(diff):.1%}. "
                            f"Signal {signal_id} shows significant deviation in this cohort."
                        ),
                        evidence={
                            "cohort_actual_lr": actual_lr,
                            "cohort_expected_lr": expected_lr,
                            "signal_deviation": signal_diff,
                            "cohort_size": len(members),
                        },
                    ))

            # If no specific signal identified, suggest tier boundary adjustment
            if not recommendations:
                avg_tier = statistics.mean([o.dsi_tier for o in members])
                recommendations.append(TuningRecommendation(
                    recommendation_id=f"cohort_{cohort_id}_tier",
                    type=RecommendationType.TIER_BOUNDARY,
                    target_id=f"tier_{int(avg_tier)}",
                    target_name=f"Tier {int(avg_tier)} boundaries",
                    expected_impact=abs(diff) * 0.5,
                    confidence=0.5,
                    rationale=(
                        f"Cohort '{cohort.name}' centered around tier {avg_tier:.1f} "
                        f"is {direction}. Consider adjusting tier score boundaries."
                    ),
                    evidence={
                        "cohort_actual_lr": actual_lr,
                        "cohort_expected_lr": expected_lr,
                        "average_tier": avg_tier,
                        "cohort_size": len(members),
                    },
                ))

        return recommendations

    def _analyze_cohort_signals(
        self,
        cohort_members: List[OutcomeRecord],
    ) -> Dict[str, float]:
        """
        Analyze how signal values in cohort differ from population.

        Returns dict of signal_id -> deviation (cohort_avg - pop_avg) / pop_std
        """
        # Get all outcomes for population comparison
        all_outcomes = [o for o in self._outcomes if o.signal_values]
        cohort_with_signals = [o for o in cohort_members if o.signal_values]

        if not all_outcomes or not cohort_with_signals:
            return {}

        # Get all signal IDs
        all_signals = set()
        for o in all_outcomes:
            all_signals.update(o.signal_values.keys())

        deviations = {}
        for signal_id in all_signals:
            pop_values = [
                o.signal_values[signal_id]
                for o in all_outcomes
                if signal_id in o.signal_values
            ]
            cohort_values = [
                o.signal_values[signal_id]
                for o in cohort_with_signals
                if signal_id in o.signal_values
            ]

            if len(pop_values) < 10 or len(cohort_values) < 5:
                continue

            pop_mean = statistics.mean(pop_values)
            pop_std = statistics.stdev(pop_values) if len(pop_values) > 1 else 1.0
            cohort_mean = statistics.mean(cohort_values)

            if pop_std > 0:
                deviations[signal_id] = (cohort_mean - pop_mean) / pop_std

        return deviations

    def auto_discover_cohorts(
        self,
        coverage: str,
        min_size: int = 20,
    ) -> List[CohortDefinition]:
        """
        Automatically discover meaningful cohorts.

        Creates cohorts based on common segmentation patterns.

        Args:
            coverage: Coverage to analyze
            min_size: Minimum cohort size

        Returns:
            List of discovered cohorts
        """
        discovered = []

        # Coverage filter
        coverage_outcomes = [o for o in self._outcomes if o.coverage == coverage]
        if len(coverage_outcomes) < min_size:
            return []

        # Tier-based cohorts
        for tier in [1, 2, 3, 4, 5]:
            cohort = self.define_cohort(
                name=f"{coverage.upper()} Tier {tier}",
                criteria={"coverage": coverage, "tier": tier},
                description=f"All {coverage} risks in tier {tier}",
            )
            if cohort.member_count >= min_size:
                discovered.append(cohort)

        # Score-based cohorts (quintiles)
        scores = sorted([o.dsi_score for o in coverage_outcomes])
        if len(scores) >= min_size * 2:
            quintiles = [
                scores[len(scores) // 5],
                scores[2 * len(scores) // 5],
                scores[3 * len(scores) // 5],
                scores[4 * len(scores) // 5],
            ]

            cohort = self.define_cohort(
                name=f"{coverage.upper()} High Score (Top 20%)",
                criteria={
                    "coverage": coverage,
                    "dsi_score_min": quintiles[3],
                },
                description="Top 20% by DSI score",
            )
            if cohort.member_count >= min_size:
                discovered.append(cohort)

            cohort = self.define_cohort(
                name=f"{coverage.upper()} Low Score (Bottom 20%)",
                criteria={
                    "coverage": coverage,
                    "dsi_score_max": quintiles[0],
                },
                description="Bottom 20% by DSI score",
            )
            if cohort.member_count >= min_size:
                discovered.append(cohort)

        # Claims vs no-claims
        cohort = self.define_cohort(
            name=f"{coverage.upper()} With Claims",
            criteria={"coverage": coverage, "has_claims": True},
            description="Risks that had claims",
        )
        if cohort.member_count >= min_size:
            discovered.append(cohort)

        cohort = self.define_cohort(
            name=f"{coverage.upper()} Clean (No Claims)",
            criteria={"coverage": coverage, "has_claims": False},
            description="Risks with no claims",
        )
        if cohort.member_count >= min_size:
            discovered.append(cohort)

        logger.info(f"Auto-discovered {len(discovered)} cohorts for {coverage}")
        return discovered
