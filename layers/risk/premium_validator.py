"""Premium accumulation validator.

Validates the multiplicative pricing chain (rate × basis × modifiers × ILF × deductible_factor)
against target premium-to-limit ratio ranges per limit cohort. Designed as a sense-check
that catches accumulation issues before guardrails become the primary pricing control.

Usage:
    from layers.risk.premium_validator import PremiumValidator

    validator = PremiumValidator()
    report = validator.validate_pricing(config, pricing_result, submission_data, categorical_outputs)
    if report.has_warnings:
        for w in report.warnings:
            print(w)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.models.config_schema import CoverageConfig, RiskTierBand

logger = logging.getLogger("dsi.premium_validator")


# ---------------------------------------------------------------------------
# Target premium-to-limit ratio ranges by limit cohort
#
# These represent reasonable expected P/L ratios for well-priced risks.
# If the accumulation of rate × basis × modifiers × ILF × deductible_factor
# produces a P/L ratio outside these ranges, something is likely off.
# ---------------------------------------------------------------------------

DEFAULT_LIMIT_COHORTS: List[Dict[str, Any]] = [
    # Small limits — expect relatively higher rates (fixed costs amortised)
    {"min_limit": 0,            "max_limit": 2_000_000,    "target_min": 0.001, "target_max": 0.08,  "label": "MICRO"},
    {"min_limit": 2_000_001,    "max_limit": 10_000_000,   "target_min": 0.002, "target_max": 0.12,  "label": "SMALL"},
    {"min_limit": 10_000_001,   "max_limit": 50_000_000,   "target_min": 0.005, "target_max": 0.15,  "label": "MEDIUM"},
    {"min_limit": 50_000_001,   "max_limit": 250_000_000,  "target_min": 0.005, "target_max": 0.18,  "label": "LARGE"},
    {"min_limit": 250_000_001,  "max_limit": 1_000_000_000,"target_min": 0.005, "target_max": 0.20,  "label": "JUMBO"},
    {"min_limit": 1_000_000_001,"max_limit": float("inf"), "target_min": 0.005, "target_max": 0.25,  "label": "MEGA"},
]


@dataclass
class AccumulationStep:
    """A single step in the premium accumulation chain."""
    step_name: str
    input_value: float
    output_value: float
    multiplier: float
    detail: str = ""


@dataclass
class ValidationWarning:
    """A specific validation warning with context."""
    severity: str  # INFO, WARNING, CRITICAL
    category: str  # RATIO, ACCUMULATION, BASIS, MODIFIER, ILF
    message: str
    values: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return "[{}] {}: {}".format(self.severity, self.category, self.message)


@dataclass
class ValidationReport:
    """Complete validation report for a pricing calculation."""
    entity_name: str = ""
    coverage: str = ""
    limit: float = 0.0
    limit_cohort: str = ""

    # Final metrics
    final_premium: float = 0.0
    premium_to_limit_ratio: float = 0.0
    target_min: float = 0.0
    target_max: float = 0.0

    # Accumulation chain
    steps: List[AccumulationStep] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)

    # Basis analysis
    basis_value: float = 0.0
    basis_to_limit_ratio: float = 0.0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def has_critical(self) -> bool:
        return any(w.severity == "CRITICAL" for w in self.warnings)

    @property
    def within_target(self) -> bool:
        return self.target_min <= self.premium_to_limit_ratio <= self.target_max

    def summary(self) -> str:
        """One-line summary of the validation result."""
        status = "OK" if self.within_target else "OUTSIDE TARGET"
        return "{:<30s} | P/L={:.4f} target=[{:.3f},{:.3f}] | {} | {}".format(
            self.entity_name,
            self.premium_to_limit_ratio,
            self.target_min,
            self.target_max,
            self.limit_cohort,
            status,
        )

    def detailed_report(self) -> str:
        """Multi-line report showing the full accumulation chain."""
        lines = []
        lines.append("=" * 80)
        lines.append("Premium Accumulation Report: {}".format(self.entity_name))
        lines.append("Coverage: {} | Limit: {:,} | Cohort: {}".format(
            self.coverage, int(self.limit), self.limit_cohort))
        lines.append("-" * 80)

        if self.basis_value > 0:
            lines.append("Basis value: {:,.0f} (basis/limit ratio: {:.1f}x)".format(
                self.basis_value, self.basis_to_limit_ratio))

        lines.append("")
        lines.append("Accumulation chain:")
        for step in self.steps:
            lines.append("  {:.<40s} {:>15,.0f}  (x{:.4f}) {}".format(
                step.step_name, step.output_value, step.multiplier, step.detail))

        lines.append("")
        lines.append("Final P/L ratio: {:.4f}  (target: [{:.3f}, {:.3f}])".format(
            self.premium_to_limit_ratio, self.target_min, self.target_max))

        if self.warnings:
            lines.append("")
            lines.append("Warnings ({}):" .format(len(self.warnings)))
            for w in self.warnings:
                lines.append("  {}".format(w))

        lines.append("=" * 80)
        return "\n".join(lines)


class PremiumValidator:
    """Validates premium accumulation against target P/L ratio ranges.

    The validator decomposes the pricing chain into steps:
      1. Base premium (rate × basis_value)
      2. Categorical modifiers (product of all category-based adjustments)
      3. Query/signal modifiers (product of condition-triggered adjustments)
      4. ILF scaling (increased limit factor for the requested limit)
      5. Deductible factor
      6. Guardrail application (if any)

    Each step is checked for reasonableness, and the final P/L ratio is
    compared against target ranges for the limit cohort.
    """

    def __init__(
        self,
        limit_cohorts: Optional[List[Dict[str, Any]]] = None,
        basis_to_limit_warn_threshold: float = 50.0,
        combined_modifier_warn_threshold: float = 3.0,
    ):
        self.limit_cohorts = limit_cohorts or DEFAULT_LIMIT_COHORTS
        self.basis_to_limit_warn_threshold = basis_to_limit_warn_threshold
        self.combined_modifier_warn_threshold = combined_modifier_warn_threshold

    def get_limit_cohort(self, limit: float) -> Dict[str, Any]:
        """Find the target range for a given limit."""
        for cohort in self.limit_cohorts:
            if cohort["min_limit"] <= limit <= cohort["max_limit"]:
                return cohort
        return self.limit_cohorts[-1]

    def validate_pricing(
        self,
        config: CoverageConfig,
        pricing_result: Any,
        submission_data: Dict[str, Any],
        categorical_outputs: Optional[List[Any]] = None,
        entity_name: str = "",
    ) -> ValidationReport:
        """Validate a complete pricing result against target ranges.

        Args:
            config: Coverage configuration
            pricing_result: PricingResult from the pricer
            submission_data: Submission data dict
            categorical_outputs: List of CategoricalOutput instances
            entity_name: Entity name for reporting

        Returns:
            ValidationReport with warnings and accumulation chain
        """
        limit = float(submission_data.get("limit", 0))
        cohort = self.get_limit_cohort(limit)
        report = ValidationReport(
            entity_name=entity_name,
            coverage=config.coverage_id if hasattr(config, 'coverage_id') else "",
            limit=limit,
            limit_cohort=cohort["label"],
            target_min=cohort["target_min"],
            target_max=cohort["target_max"],
            final_premium=pricing_result.final_premium,
            premium_to_limit_ratio=pricing_result.final_premium / limit if limit > 0 else 0,
        )

        # Step 1: Base premium analysis
        self._check_base_premium(report, config, pricing_result, submission_data)

        # Step 2: Modifier accumulation
        self._check_modifiers(report, pricing_result, categorical_outputs)

        # Step 3: ILF analysis
        self._check_ilf(report, pricing_result, submission_data, config)

        # Step 4: Final P/L ratio check
        self._check_final_ratio(report, pricing_result)

        return report

    def _check_base_premium(
        self,
        report: ValidationReport,
        config: CoverageConfig,
        pricing_result: Any,
        submission_data: Dict[str, Any],
    ) -> None:
        """Analyse the base premium step."""
        base_premium = pricing_result.base_premium
        tier = pricing_result.final_tier

        # Find the tier band to get rate and basis
        tier_band = config.get_tier_band(tier)
        if tier_band and tier_band.interpretation.application:
            app = tier_band.interpretation.application
            basis_field = app.basis
            rate = app.applied

            basis_value = 0.0
            if basis_field:
                basis_value = float(submission_data.get(basis_field, 0))
            report.basis_value = basis_value
            report.basis_to_limit_ratio = basis_value / report.limit if report.limit > 0 else 0

            report.steps.append(AccumulationStep(
                step_name="Base premium (rate × basis)",
                input_value=basis_value,
                output_value=base_premium,
                multiplier=rate if rate else 0,
                detail="rate={} × {}={:,.0f}".format(rate, basis_field, basis_value),
            ))

            # Warn if basis is dramatically larger than limit
            if report.basis_to_limit_ratio > self.basis_to_limit_warn_threshold:
                report.warnings.append(ValidationWarning(
                    severity="WARNING",
                    category="BASIS",
                    message="Basis ({}) is {:.0f}x the limit — base premium will inherently "
                            "exceed reasonable P/L ratios before modifiers/ILF".format(
                                basis_field, report.basis_to_limit_ratio),
                    values={"basis": basis_value, "limit": report.limit,
                            "ratio": report.basis_to_limit_ratio},
                ))

            # Check if base premium alone already exceeds target max
            base_pl = base_premium / report.limit if report.limit > 0 else 0
            if base_pl > report.target_max:
                report.warnings.append(ValidationWarning(
                    severity="CRITICAL",
                    category="BASIS",
                    message="Base premium alone ({:,.0f}) produces P/L={:.4f}, already exceeds "
                            "target max {:.3f} — modifiers and ILF will only make this worse".format(
                                base_premium, base_pl, report.target_max),
                    values={"base_premium": base_premium, "base_pl": base_pl},
                ))

    def _check_modifiers(
        self,
        report: ValidationReport,
        pricing_result: Any,
        categorical_outputs: Optional[List[Any]],
    ) -> None:
        """Analyse modifier accumulation."""
        # Categorical modifier product
        cat_mod = 1.0
        if categorical_outputs:
            for co in categorical_outputs:
                cat_mod *= co.modifier

        if cat_mod != 1.0:
            report.steps.append(AccumulationStep(
                step_name="Categorical modifiers",
                input_value=pricing_result.base_premium,
                output_value=pricing_result.base_premium * cat_mod,
                multiplier=cat_mod,
                detail="product of {} categories".format(
                    len(categorical_outputs) if categorical_outputs else 0),
            ))

        # Query/signal modifiers (from total_modifier / cat_mod)
        total_mod = pricing_result.total_modifier
        other_mod = total_mod / cat_mod if cat_mod != 0 else total_mod
        if abs(other_mod - 1.0) > 0.001:
            report.steps.append(AccumulationStep(
                step_name="Query/signal modifiers",
                input_value=pricing_result.base_premium * cat_mod,
                output_value=pricing_result.premium_after_modifiers,
                multiplier=other_mod,
            ))

        # Combined modifier check
        report.steps.append(AccumulationStep(
            step_name="Total modifier effect",
            input_value=pricing_result.base_premium,
            output_value=pricing_result.premium_after_modifiers,
            multiplier=total_mod,
        ))

        if total_mod > self.combined_modifier_warn_threshold:
            report.warnings.append(ValidationWarning(
                severity="WARNING",
                category="MODIFIER",
                message="Combined modifier ({:.3f}x) exceeds threshold ({:.1f}x) — "
                        "the accumulation of adjustments is amplifying the premium".format(
                            total_mod, self.combined_modifier_warn_threshold),
                values={"total_modifier": total_mod, "threshold": self.combined_modifier_warn_threshold},
            ))

        # Check for modifier clamping
        if pricing_result.modifier_was_clamped:
            report.warnings.append(ValidationWarning(
                severity="INFO",
                category="MODIFIER",
                message="Modifier was clamped by guardrail floor/cap",
            ))

    def _check_ilf(
        self,
        report: ValidationReport,
        pricing_result: Any,
        submission_data: Dict[str, Any],
        config: CoverageConfig,
    ) -> None:
        """Analyse ILF scaling impact."""
        premium_after_mods = pricing_result.premium_after_modifiers
        final = pricing_result.final_premium
        limit = submission_data.get("limit", 0)

        # The ILF + deductible factor effect is:
        # final_premium / premium_after_modifiers (before guardrails)
        if premium_after_mods > 0 and not pricing_result.premium_was_capped:
            ilf_effect = final / premium_after_mods
            if abs(ilf_effect - 1.0) > 0.001:
                report.steps.append(AccumulationStep(
                    step_name="ILF × deductible factor",
                    input_value=premium_after_mods,
                    output_value=final,
                    multiplier=ilf_effect,
                    detail="for limit={:,}".format(int(limit)),
                ))

                if ilf_effect > 5.0:
                    report.warnings.append(ValidationWarning(
                        severity="WARNING",
                        category="ILF",
                        message="ILF scaling factor ({:.2f}x) is very high — "
                                "limit {:,} may be far from base limit reference".format(
                                    ilf_effect, int(limit)),
                        values={"ilf_effect": ilf_effect},
                    ))

    def _check_final_ratio(
        self,
        report: ValidationReport,
        pricing_result: Any,
    ) -> None:
        """Check the final P/L ratio against targets."""
        ratio = report.premium_to_limit_ratio

        if pricing_result.premium_was_capped:
            report.warnings.append(ValidationWarning(
                severity="CRITICAL",
                category="RATIO",
                message="Premium was capped by guardrail (max_premium_to_limit_ratio). "
                        "Guardrails are acting as primary pricing control, not safety net",
                values={"guardrail_warnings": pricing_result.guardrail_warnings},
            ))

        if ratio > report.target_max:
            report.warnings.append(ValidationWarning(
                severity="CRITICAL",
                category="RATIO",
                message="Final P/L ratio ({:.4f}) exceeds target max ({:.3f}) for {} cohort".format(
                    ratio, report.target_max, report.limit_cohort),
                values={"ratio": ratio, "target_max": report.target_max},
            ))
        elif ratio < report.target_min:
            report.warnings.append(ValidationWarning(
                severity="INFO",
                category="RATIO",
                message="Final P/L ratio ({:.4f}) below target min ({:.3f}) — "
                        "premium may be too low for risk".format(
                    ratio, report.target_min),
                values={"ratio": ratio, "target_min": report.target_min},
            ))

    def validate_batch(
        self,
        results: List[Dict[str, Any]],
    ) -> Tuple[List[ValidationReport], Dict[str, Any]]:
        """Validate a batch of pricing results and produce summary statistics.

        Args:
            results: List of dicts, each with keys:
                config, pricing_result, submission_data, categorical_outputs, entity_name

        Returns:
            (list of ValidationReports, summary dict)
        """
        reports = []
        for r in results:
            report = self.validate_pricing(
                config=r["config"],
                pricing_result=r["pricing_result"],
                submission_data=r["submission_data"],
                categorical_outputs=r.get("categorical_outputs"),
                entity_name=r.get("entity_name", ""),
            )
            reports.append(report)

        # Summary statistics
        total = len(reports)
        within_target = sum(1 for r in reports if r.within_target)
        with_warnings = sum(1 for r in reports if r.has_warnings)
        with_critical = sum(1 for r in reports if r.has_critical)
        guardrail_hits = sum(1 for r in reports if any(
            w.category == "RATIO" and "capped by guardrail" in w.message.lower()
            for w in r.warnings))

        # Per-cohort breakdown
        cohort_stats: Dict[str, Dict[str, Any]] = {}
        for r in reports:
            label = r.limit_cohort
            if label not in cohort_stats:
                cohort_stats[label] = {"count": 0, "within": 0, "ratios": []}
            cohort_stats[label]["count"] += 1
            cohort_stats[label]["ratios"].append(r.premium_to_limit_ratio)
            if r.within_target:
                cohort_stats[label]["within"] += 1

        for label, stats in cohort_stats.items():
            ratios = stats["ratios"]
            stats["avg_ratio"] = sum(ratios) / len(ratios) if ratios else 0
            stats["min_ratio"] = min(ratios) if ratios else 0
            stats["max_ratio"] = max(ratios) if ratios else 0

        summary = {
            "total": total,
            "within_target": within_target,
            "within_target_pct": 100 * within_target / total if total else 0,
            "with_warnings": with_warnings,
            "with_critical": with_critical,
            "guardrail_hits": guardrail_hits,
            "guardrail_hit_pct": 100 * guardrail_hits / total if total else 0,
            "cohort_stats": cohort_stats,
        }

        return reports, summary

    def format_batch_summary(
        self,
        reports: List[ValidationReport],
        summary: Dict[str, Any],
    ) -> str:
        """Format a batch summary as a readable string."""
        lines = []
        lines.append("=" * 90)
        lines.append("PREMIUM ACCUMULATION VALIDATION SUMMARY")
        lines.append("=" * 90)
        lines.append("")
        lines.append("Total risks: {}  |  Within target: {} ({:.1f}%)  |  "
                      "Critical warnings: {}  |  Guardrail hits: {} ({:.1f}%)".format(
                          summary["total"], summary["within_target"],
                          summary["within_target_pct"],
                          summary["with_critical"], summary["guardrail_hits"],
                          summary["guardrail_hit_pct"]))
        lines.append("")

        # Cohort breakdown
        lines.append("{:<10s} {:>6s} {:>8s} {:>10s} {:>10s} {:>10s}".format(
            "Cohort", "Count", "In Tgt", "Avg P/L", "Min P/L", "Max P/L"))
        lines.append("-" * 56)
        for label, stats in summary["cohort_stats"].items():
            lines.append("{:<10s} {:>6d} {:>8d} {:>10.4f} {:>10.4f} {:>10.4f}".format(
                label, stats["count"], stats["within"],
                stats["avg_ratio"], stats["min_ratio"], stats["max_ratio"]))

        lines.append("")

        # Individual results
        lines.append("{:<30s} {:>12s} {:>10s} {:>12s} {:>8s}".format(
            "Entity", "Premium", "P/L Ratio", "Target Max", "Status"))
        lines.append("-" * 75)
        for r in sorted(reports, key=lambda x: -x.premium_to_limit_ratio):
            status = "OK" if r.within_target else "WARN" if not r.has_critical else "CRIT"
            lines.append("{:<30s} {:>12,.0f} {:>10.4f} {:>12.3f} {:>8s}".format(
                r.entity_name[:30], r.final_premium,
                r.premium_to_limit_ratio, r.target_max, status))

        # Show detailed reports for critical items
        critical_reports = [r for r in reports if r.has_critical]
        if critical_reports:
            lines.append("")
            lines.append("DETAILED REPORTS FOR CRITICAL ITEMS ({})".format(len(critical_reports)))
            for r in critical_reports:
                lines.append("")
                lines.append(r.detailed_report())

        lines.append("")
        return "\n".join(lines)
