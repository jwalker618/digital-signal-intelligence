"""
DSI Results Aggregator (Phase 10)

Aggregates and analyzes multi-coverage pricing results
to generate package recommendations and cross-coverage insights.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    MultiCoverageResult,
    CoverageResult,
    PackageRecommendation,
    PackageDiscount,
    OrchestrationConfig,
)


logger = logging.getLogger("dsi.orchestration.aggregator")


@dataclass
class CrossCoverageInsight:
    """Insight from analyzing multiple coverages together."""
    insight_type: str  # correlation, anomaly, recommendation
    coverages: List[str]
    description: str
    severity: str = "info"  # info, warning, critical
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoverageComparison:
    """Comparison between locale options for same coverage."""
    coverage: str
    locales_compared: List[str]
    best_locale: str
    best_premium: float
    premium_by_locale: Dict[str, float]
    score_by_locale: Dict[str, float]
    recommendation: str


@dataclass
class AggregatedAnalysis:
    """Complete analysis of multi-coverage results."""
    # Summary
    total_coverages: int
    successful_coverages: int
    total_premium: float
    discounted_premium: float
    total_savings: float

    # Package info
    best_package: List[str]
    best_package_discount: float
    all_recommendations: List[PackageRecommendation]

    # Cross-coverage analysis
    insights: List[CrossCoverageInsight]
    locale_comparisons: List[CoverageComparison]

    # Risk analysis
    average_tier: float
    tier_consistency: float  # How consistent are tiers across coverages
    risk_flags: List[str]


class ResultsAggregator:
    """
    Aggregates multi-coverage results for comprehensive analysis.

    Provides:
    - Best package recommendations
    - Cross-coverage discount calculations
    - Locale comparison and selection
    - Risk consistency analysis
    - Premium optimization suggestions
    """

    def __init__(self, config: Optional[OrchestrationConfig] = None):
        """Initialize ResultsAggregator."""
        self.config = config or OrchestrationConfig.default()

    def aggregate(
        self,
        result: MultiCoverageResult,
    ) -> AggregatedAnalysis:
        """
        Perform full aggregation and analysis.

        Args:
            result: Multi-coverage result to analyze

        Returns:
            AggregatedAnalysis with full breakdown
        """
        # Basic counts
        successful_results = [
            r for r in result.coverage_results.values()
            if r.success
        ]

        # Calculate totals
        total_premium = sum(result.individual_premiums.values())
        discounted_premium = result.combined_premium
        savings = result.total_savings

        # Get all package recommendations
        recommendations = self._generate_all_recommendations(
            list(result.individual_premiums.keys()),
            result.individual_premiums,
        )

        # Best package
        best_package = result.recommended_package
        best_discount = result.package_discount

        # Cross-coverage insights
        insights = self._analyze_cross_coverage(result)

        # Locale comparisons
        comparisons = self._compare_locales(result)

        # Risk analysis
        tiers = self._extract_tiers(result)
        avg_tier = sum(tiers) / len(tiers) if tiers else 0.0
        tier_consistency = self._calculate_tier_consistency(tiers)
        risk_flags = self._identify_risk_flags(result, tiers)

        return AggregatedAnalysis(
            total_coverages=len(result.coverage_results),
            successful_coverages=len(successful_results),
            total_premium=total_premium,
            discounted_premium=discounted_premium,
            total_savings=savings,
            best_package=best_package,
            best_package_discount=best_discount,
            all_recommendations=recommendations,
            insights=insights,
            locale_comparisons=comparisons,
            average_tier=avg_tier,
            tier_consistency=tier_consistency,
            risk_flags=risk_flags,
        )

    def find_best_package(
        self,
        available_coverages: List[str],
        premiums: Dict[str, float],
    ) -> Tuple[List[str], float, float]:
        """
        Find the best package for given coverages.

        Args:
            available_coverages: Coverages that priced successfully
            premiums: Premium by coverage

        Returns:
            Tuple of (package coverages, discount rate, savings)
        """
        best_package: List[str] = []
        best_discount = 0.0
        best_savings = 0.0

        for discount in self.config.package_discounts:
            if discount.applies_to(available_coverages):
                package_premium = sum(
                    premiums.get(c, 0) for c in discount.coverages
                )
                savings = package_premium * discount.discount_rate

                if savings > best_savings:
                    best_package = discount.coverages
                    best_discount = discount.discount_rate
                    best_savings = savings

        return best_package, best_discount, best_savings

    def compare_locale_options(
        self,
        result: MultiCoverageResult,
        coverage: str,
    ) -> Optional[CoverageComparison]:
        """
        Compare locale options for a specific coverage.

        Args:
            result: Multi-coverage result
            coverage: Coverage to analyze

        Returns:
            CoverageComparison or None if single locale
        """
        # Find all results for this coverage
        locale_results: Dict[str, CoverageResult] = {}

        for key, cov_result in result.coverage_results.items():
            if cov_result.coverage == coverage:
                locale_results[cov_result.locale] = cov_result

        if len(locale_results) <= 1:
            return None

        # Extract metrics
        premium_by_locale: Dict[str, float] = {}
        score_by_locale: Dict[str, float] = {}

        for locale, cov_result in locale_results.items():
            if cov_result.workflow_result:
                premium = getattr(cov_result.workflow_result, 'final_premium', 0)
                score = getattr(cov_result.workflow_result, 'dsi_score', 0)
                premium_by_locale[locale] = premium
                score_by_locale[locale] = score

        if not premium_by_locale:
            return None

        # Find best (lowest premium or highest score?)
        best_locale = min(premium_by_locale, key=premium_by_locale.get)
        best_premium = premium_by_locale[best_locale]

        # Generate recommendation
        savings_range = max(premium_by_locale.values()) - min(premium_by_locale.values())
        if savings_range > best_premium * 0.1:
            recommendation = f"Significant locale difference: {savings_range:.0f} premium variance"
        else:
            recommendation = "Locale choice has minimal impact on premium"

        return CoverageComparison(
            coverage=coverage,
            locales_compared=list(locale_results.keys()),
            best_locale=best_locale,
            best_premium=best_premium,
            premium_by_locale=premium_by_locale,
            score_by_locale=score_by_locale,
            recommendation=recommendation,
        )

    def _generate_all_recommendations(
        self,
        coverages: List[str],
        premiums: Dict[str, float],
    ) -> List[PackageRecommendation]:
        """Generate all possible package recommendations."""
        recommendations: List[PackageRecommendation] = []

        for discount in self.config.package_discounts:
            if discount.applies_to(coverages):
                package_premium = sum(
                    premiums.get(c, 0) for c in discount.coverages
                )
                savings = package_premium * discount.discount_rate
                combined = package_premium - savings

                recommendations.append(PackageRecommendation(
                    coverages=discount.coverages,
                    combined_premium=combined,
                    discount_applied=savings,
                    discount_rate=discount.discount_rate,
                    savings=savings,
                    reason=discount.description or f"Bundle discount for {', '.join(discount.coverages)}",
                ))

        # Sort by savings
        recommendations.sort(key=lambda r: r.savings, reverse=True)
        return recommendations

    def _analyze_cross_coverage(
        self,
        result: MultiCoverageResult,
    ) -> List[CrossCoverageInsight]:
        """Analyze patterns across coverages."""
        insights: List[CrossCoverageInsight] = []

        successful = [
            r for r in result.coverage_results.values()
            if r.success and r.workflow_result
        ]

        if len(successful) < 2:
            return insights

        # Check tier consistency
        tiers = []
        for r in successful:
            tier = getattr(r.workflow_result, 'tier', None)
            if tier:
                tiers.append((r.coverage, tier))

        if tiers:
            unique_tiers = set(t[1] for t in tiers)
            if len(unique_tiers) > 2:
                insights.append(CrossCoverageInsight(
                    insight_type="anomaly",
                    coverages=[t[0] for t in tiers],
                    description=f"Wide tier spread across coverages: {unique_tiers}",
                    severity="warning",
                    data={"tiers": dict(tiers)},
                ))

        # Check for all high tiers
        if all(t[1] <= 2 for t in tiers):
            insights.append(CrossCoverageInsight(
                insight_type="recommendation",
                coverages=[t[0] for t in tiers],
                description="All coverages qualify for preferred pricing - consider full package",
                severity="info",
            ))

        # Check for mixed tiers
        if any(t[1] <= 2 for t in tiers) and any(t[1] >= 4 for t in tiers):
            high_risk = [t[0] for t in tiers if t[1] >= 4]
            insights.append(CrossCoverageInsight(
                insight_type="anomaly",
                coverages=high_risk,
                description=f"Coverage(s) {high_risk} have higher risk tiers - review signal drivers",
                severity="warning",
            ))

        return insights

    def _compare_locales(
        self,
        result: MultiCoverageResult,
    ) -> List[CoverageComparison]:
        """Compare locale options for each coverage."""
        comparisons: List[CoverageComparison] = []

        # Find unique coverages
        coverages = set(r.coverage for r in result.coverage_results.values())

        for coverage in coverages:
            comparison = self.compare_locale_options(result, coverage)
            if comparison:
                comparisons.append(comparison)

        return comparisons

    def _extract_tiers(self, result: MultiCoverageResult) -> List[int]:
        """Extract tiers from all successful results."""
        tiers: List[int] = []

        for cov_result in result.coverage_results.values():
            if cov_result.success and cov_result.workflow_result:
                tier = getattr(cov_result.workflow_result, 'tier', None)
                if tier:
                    tiers.append(tier)

        return tiers

    def _calculate_tier_consistency(self, tiers: List[int]) -> float:
        """Calculate how consistent tiers are (0-1, 1 = all same)."""
        if not tiers or len(tiers) == 1:
            return 1.0

        # Calculate standard deviation relative to range
        avg = sum(tiers) / len(tiers)
        variance = sum((t - avg) ** 2 for t in tiers) / len(tiers)
        std_dev = variance ** 0.5

        # Normalize: 0 std_dev = 1.0 consistency, 2 std_dev = 0 consistency
        consistency = max(0, 1 - (std_dev / 2))
        return consistency

    def _identify_risk_flags(
        self,
        result: MultiCoverageResult,
        tiers: List[int],
    ) -> List[str]:
        """Identify risk flags from results."""
        flags: List[str] = []

        # High tier warnings
        if any(t >= 4 for t in tiers):
            flags.append("One or more coverages in elevated risk tier")

        # Inconsistent tiers
        if len(set(tiers)) > 2:
            flags.append("Risk profile varies significantly across coverages")

        # Check for failures
        if result.failed_runs > 0:
            flags.append(f"{result.failed_runs} coverage(s) failed to price")

        # Check for referrals
        for cov_result in result.coverage_results.values():
            if cov_result.workflow_result:
                referred = getattr(cov_result.workflow_result, 'referred', False)
                if referred:
                    flags.append(f"{cov_result.coverage} requires underwriter review")

        return flags


def summarize_result(result: MultiCoverageResult) -> Dict[str, Any]:
    """
    Create a summary of multi-coverage result for display.

    Args:
        result: Multi-coverage result

    Returns:
        Dictionary with summary data
    """
    return {
        "entity": result.entity_name,
        "domain": result.discovered_domain,
        "locale": result.detected_locale,
        "coverages_priced": result.successful_runs,
        "coverages_failed": result.failed_runs,
        "individual_premiums": result.individual_premiums,
        "combined_premium": result.combined_premium,
        "package_discount": f"{result.package_discount:.1%}" if result.package_discount else "None",
        "total_savings": result.total_savings,
        "recommended_package": result.recommended_package,
        "cache_efficiency": f"{result.cache_hit_rate:.1%}",
        "duration": f"{result.total_duration_seconds:.1f}s",
    }
