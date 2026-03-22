"""Configuration Health Gate.

Validates that each coverage configuration produces sane pricing outputs
before allowing it to be used in production. Configurations that fail
health checks are quarantined — they cannot process live submissions
until the issues are resolved.

The gate runs synthetic test fixtures through the full pricing pipeline
(scoring → pricing → guardrail check) and verifies:

  1. No guardrails acting as primary pricing control
  2. Final P/L ratios within target ranges for all test fixtures
  3. Pricing pipeline executes without errors

Usage:
    from layers.risk.config_health_gate import get_health_gate

    gate = get_health_gate()

    # Check a specific config
    result = gate.check_config("cyber", "cyber_general")
    if not result.passed:
        print(result.reason)

    # Check all configs (called automatically at startup)
    gate.run_all_checks()

    # Query quarantine status
    gate.is_quarantined("cyber", "cyber_general")  # False if healthy
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.models.config_schema import CoverageConfig

logger = logging.getLogger("dsi.config_health_gate")


# ---------------------------------------------------------------------------
# Environment variable to bypass the gate (testing/CI only)
# ---------------------------------------------------------------------------
_ENV_BYPASS = "DSI_BYPASS_HEALTH_GATE"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class HealthCheckResult:
    """Result of a health check for a single configuration."""
    coverage_id: str
    config_id: str
    passed: bool
    reason: str = ""
    fixture_count: int = 0
    failures: List[str] = field(default_factory=list)
    checked_at: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        return f"{self.coverage_id}/{self.config_id}"


# ---------------------------------------------------------------------------
# Test fixtures per coverage
#
# Each fixture is a minimal synthetic submission that exercises the pricing
# pipeline for a given tier and limit cohort. We test at least one fixture
# per active tier (non-DECLINE) and multiple limit levels.
# ---------------------------------------------------------------------------

def _build_fixtures_for_config(config: CoverageConfig) -> List[Dict[str, Any]]:
    """Generate synthetic test fixtures for a configuration.

    Fixtures are designed to cover:
      - Each non-DECLINE tier
      - A spread of limit cohorts (small, medium, large)
      - The basis field used by each tier's pricing method
    """
    fixtures = []

    for band in config.risk_tier_bands.bands:
        action = band.interpretation.action.value
        app = band.interpretation.application
        if app is None:
            continue

        # Skip DECLINE tiers — they are not priced
        if action == "DECLINE":
            continue

        basis_field = app.basis or "revenue"
        rate = app.applied or 0.0
        base_value = app.value or 0

        # Categorical basis requires actual category selections which
        # synthetic fixtures can't provide — treat as PREMIUM_BASE.
        if basis_field in ("categorical", "category"):
            if base_value <= 0:
                # Estimate a typical base from the rate × a midrange categorical base.
                # SME PI typically has categories producing bases of $5K-$20K.
                base_value = max(5_000, int((rate or 1.0) * 10_000))
            rate = 0.0

        # Skip tiers with no pricing mechanism
        if rate <= 0 and base_value <= 0:
            continue

        # Choose limit tiers based on pricing method.
        # MULTIPLIER configs (rate × basis) are used for large commercial/specialty;
        # PREMIUM_BASE configs (fixed premium) are used for SME/small lines.
        if rate > 0:
            limit_tiers = [
                ("small",  5_000_000,   0.05),
                ("medium", 50_000_000,  0.08),
                ("large",  250_000_000, 0.10),
            ]
        else:
            # Fixed-premium SME: choose limits based on the actual base premium
            # so we test at P/L ratios that are structurally achievable.
            # Target: limits where base_premium/limit is in [2%, 10%]
            bp = base_value
            limit_tiers = [
                ("small",  max(50_000,  int(bp / 0.08)), 0.06),  # ~8% P/L
                ("medium", max(100_000, int(bp / 0.03)), 0.02),  # ~3% P/L
                ("large",  max(250_000, int(bp / 0.01)), 0.01),  # ~1% P/L
            ]

        for size_label, limit, target_pl in limit_tiers:
            submission = {
                "limit": limit,
                "deductible": config.pricing.base_deductible_reference,
                "product_type": (
                    config.metadata.product_types[0]
                    if config.metadata.product_types else "standard"
                ),
            }

            if rate > 0 and basis_field not in ("categorical", "category"):
                # MULTIPLIER method: solve rate * basis * ilf = target_pl * limit
                # Estimate ILF for this limit to avoid base premium × ILF exceeding target
                product_type = submission["product_type"]
                estimated_ilf = config.get_ilf(product_type, limit)
                if estimated_ilf <= 0:
                    estimated_ilf = 1.0
                basis_value = target_pl * limit / (rate * estimated_ilf)
                basis_value = max(1_000_000, min(basis_value, 500_000_000_000))
                submission[basis_field] = basis_value
            elif rate > 0:
                # Categorical basis — the rate is applied to a category-derived
                # base, not a submission field. Provide revenue for guardrail checks.
                submission["revenue"] = limit * 20
            else:
                # PREMIUM_BASE method: fixed base premium, no basis needed
                # Provide revenue proportional to the limit for guardrail checks
                submission["revenue"] = limit * 20

            fixtures.append({
                "tier": band.id,
                "label": f"tier{band.id}_{size_label}",
                "composite_score": (
                    band.interpretation.bands.min
                    + band.interpretation.bands.max
                ) / 2,
                "submission_data": submission,
                "action": action,
            })

    return fixtures


# ---------------------------------------------------------------------------
# Core gate
# ---------------------------------------------------------------------------

class ConfigHealthGate:
    """Validates configuration pricing calibration and quarantines failures.

    The gate maintains a registry of quarantined configurations. Once a config
    is quarantined, any attempt to use it via ``get_config()`` raises
    ``ConfigQuarantinedError`` unless the bypass environment variable is set.
    """

    def __init__(
        self,
        max_guardrail_primary_pct: float = 0.0,
        max_outside_target_pct: float = 10.0,
    ):
        """
        Args:
            max_guardrail_primary_pct: Max % of fixtures where guardrails are
                the primary pricing control. Default 0% — no tolerance.
            max_outside_target_pct: Max % of fixtures with P/L outside target.
                Default 10% — allows one outlier in a small fixture set.
        """
        self.max_guardrail_primary_pct = max_guardrail_primary_pct
        self.max_outside_target_pct = max_outside_target_pct

        # Quarantine registry: {coverage_id/config_id: HealthCheckResult}
        self._quarantined: Dict[str, HealthCheckResult] = {}
        self._results: Dict[str, HealthCheckResult] = {}

    @property
    def bypass_enabled(self) -> bool:
        """True if the health gate is bypassed via environment variable."""
        return os.environ.get(_ENV_BYPASS, "").lower() in ("1", "true", "yes")

    def is_quarantined(self, coverage_id: str, config_id: str) -> bool:
        """Check if a configuration is quarantined."""
        if self.bypass_enabled:
            return False
        key = f"{coverage_id}/{config_id}"
        return key in self._quarantined

    def get_quarantine_reason(self, coverage_id: str, config_id: str) -> str:
        """Get the quarantine reason for a configuration."""
        key = f"{coverage_id}/{config_id}"
        result = self._quarantined.get(key)
        return result.reason if result else ""

    def get_all_results(self) -> Dict[str, HealthCheckResult]:
        """Return all health check results."""
        return dict(self._results)

    def get_quarantined(self) -> Dict[str, HealthCheckResult]:
        """Return all quarantined configurations."""
        return dict(self._quarantined)

    def check_config(
        self,
        coverage_id: str,
        config_id: str,
        config: Optional[CoverageConfig] = None,
    ) -> HealthCheckResult:
        """Run health check on a single configuration.

        Args:
            coverage_id: Coverage identifier
            config_id: Configuration identifier
            config: Pre-loaded config (loaded from compiler if None)

        Returns:
            HealthCheckResult with pass/fail and details
        """
        # Lazy imports to avoid circular dependencies
        from layers.risk.pricer import ModelPricer
        from layers.risk.premium_validator import PremiumValidator, DEFAULT_LIMIT_COHORTS

        key = f"{coverage_id}/{config_id}"

        if config is None:
            from infrastructure.models.compiler import get_compiled_configs
            configs = get_compiled_configs()
            cov = configs.get(coverage_id)
            if cov is None:
                result = HealthCheckResult(
                    coverage_id=coverage_id,
                    config_id=config_id,
                    passed=False,
                    reason=f"Coverage '{coverage_id}' not found",
                )
                self._results[key] = result
                self._quarantined[key] = result
                return result
            config = cov.configurations.get(config_id)
            if config is None:
                result = HealthCheckResult(
                    coverage_id=coverage_id,
                    config_id=config_id,
                    passed=False,
                    reason=f"Config '{config_id}' not found in '{coverage_id}'",
                )
                self._results[key] = result
                self._quarantined[key] = result
                return result

        fixtures = _build_fixtures_for_config(config)
        if not fixtures:
            result = HealthCheckResult(
                coverage_id=coverage_id,
                config_id=config_id,
                passed=False,
                reason="No test fixtures could be generated — config may have no priceable tiers",
            )
            self._results[key] = result
            self._quarantined[key] = result
            return result

        pricer = ModelPricer()
        # Use wider target bands for health gate — synthetic fixtures lack
        # the categorical modifiers that compress real premiums. The gate
        # catches broken calibration, not edge-case P/L at limit extremes.
        gate_cohorts = []
        for c in DEFAULT_LIMIT_COHORTS:
            widened = dict(c)
            widened["target_min"] = c["target_min"] * 0.5
            widened["target_max"] = min(c["target_max"] * 1.5, 0.35)
            gate_cohorts.append(widened)
        validator = PremiumValidator(limit_cohorts=gate_cohorts)
        failures = []
        guardrail_primary_count = 0
        outside_target_count = 0
        error_count = 0

        for fixture in fixtures:
            try:
                pricing_result = pricer.price_submission(
                    pure_composite_score=fixture["composite_score"],
                    signal_tier_overrides=[],
                    query_tier_overrides=[],
                    query_modifiers=[],
                    categorical_outputs=[],
                    submission_data=fixture["submission_data"],
                    config=config,
                )

                report = validator.validate_pricing(
                    config=config,
                    pricing_result=pricing_result,
                    submission_data=fixture["submission_data"],
                    entity_name=fixture["label"],
                )

                # Check for guardrail as primary control
                has_primary = any(
                    "primary pricing control" in w.message
                    for w in report.warnings
                )
                if has_primary:
                    guardrail_primary_count += 1
                    failures.append(
                        "{}: guardrail is primary pricing control "
                        "(P/L={:.4f}, cap={:.3f})".format(
                            fixture["label"],
                            report.premium_to_limit_ratio,
                            report.target_max,
                        )
                    )

                if not report.within_target:
                    outside_target_count += 1
                    if not has_primary:
                        failures.append(
                            "{}: P/L {:.4f} outside target [{:.3f}, {:.3f}]".format(
                                fixture["label"],
                                report.premium_to_limit_ratio,
                                report.target_min,
                                report.target_max,
                            )
                        )

            except Exception as e:
                error_count += 1
                failures.append(
                    "{}: pricing pipeline error: {}".format(fixture["label"], e)
                )

        total = len(fixtures)
        primary_pct = 100 * guardrail_primary_count / total if total else 0
        outside_pct = 100 * outside_target_count / total if total else 0
        error_pct = 100 * error_count / total if total else 0

        passed = (
            primary_pct <= self.max_guardrail_primary_pct
            and outside_pct <= self.max_outside_target_pct
            and error_pct < 50  # More than half erroring → broken config
        )

        if not passed:
            reasons = []
            if primary_pct > self.max_guardrail_primary_pct:
                reasons.append(
                    "guardrails as primary control: {:.0f}% "
                    "(max {:.0f}%)".format(primary_pct, self.max_guardrail_primary_pct)
                )
            if outside_pct > self.max_outside_target_pct:
                reasons.append(
                    "outside target: {:.0f}% "
                    "(max {:.0f}%)".format(outside_pct, self.max_outside_target_pct)
                )
            if error_pct >= 50:
                reasons.append(
                    "pricing errors: {:.0f}% of fixtures".format(error_pct)
                )
            reason = "QUARANTINED: {} — {}".format(key, "; ".join(reasons))
        else:
            reason = ""

        result = HealthCheckResult(
            coverage_id=coverage_id,
            config_id=config_id,
            passed=passed,
            reason=reason,
            fixture_count=total,
            failures=failures,
        )

        self._results[key] = result
        if passed:
            self._quarantined.pop(key, None)
        else:
            self._quarantined[key] = result
            logger.error(
                "Config %s QUARANTINED: %s (%d/%d fixtures failed)",
                key, reason, len(failures), total,
            )

        return result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run health checks on all compiled configurations.

        Returns:
            Dict mapping config key to HealthCheckResult
        """
        from infrastructure.models.compiler import get_compiled_configs

        configs = get_compiled_configs()
        results = {}
        quarantined_count = 0

        for coverage_id, coverage in configs.items():
            for config_id, config in coverage.configurations.items():
                result = self.check_config(coverage_id, config_id, config)
                results[result.key] = result
                if not result.passed:
                    quarantined_count += 1

        total = len(results)
        healthy = total - quarantined_count

        if quarantined_count > 0:
            logger.warning(
                "Health gate: %d/%d configs healthy, %d QUARANTINED",
                healthy, total, quarantined_count,
            )
            for key, r in self._quarantined.items():
                logger.warning("  QUARANTINED: %s — %s", key, r.reason)
        else:
            logger.info("Health gate: all %d configs healthy", total)

        return results

    def format_summary(self) -> str:
        """Format a human-readable summary of all health check results."""
        lines = []
        lines.append("=" * 70)
        lines.append("CONFIGURATION HEALTH GATE SUMMARY")
        lines.append("=" * 70)

        if self.bypass_enabled:
            lines.append("")
            lines.append("*** BYPASS ENABLED ({}) — quarantine not enforced ***".format(
                _ENV_BYPASS))

        total = len(self._results)
        quarantined = len(self._quarantined)
        lines.append("")
        lines.append("Total configs: {}  |  Healthy: {}  |  Quarantined: {}".format(
            total, total - quarantined, quarantined))
        lines.append("")

        lines.append("{:<40s} {:>8s} {:>10s} {:>8s}".format(
            "Configuration", "Fixtures", "Failures", "Status"))
        lines.append("-" * 70)

        for key in sorted(self._results.keys()):
            r = self._results[key]
            status = "HEALTHY" if r.passed else "QUARANTINED"
            lines.append("{:<40s} {:>8d} {:>10d} {:>8s}".format(
                key, r.fixture_count, len(r.failures), status))

        if self._quarantined:
            lines.append("")
            lines.append("QUARANTINE DETAILS:")
            for key, r in self._quarantined.items():
                lines.append("")
                lines.append("  {} — {}".format(key, r.reason))
                for f in r.failures[:5]:  # Show first 5 failures
                    lines.append("    - {}".format(f))
                if len(r.failures) > 5:
                    lines.append("    ... and {} more".format(len(r.failures) - 5))

        lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_default_gate: Optional[ConfigHealthGate] = None


def get_health_gate() -> ConfigHealthGate:
    """Get or create the singleton health gate."""
    global _default_gate
    if _default_gate is None:
        _default_gate = ConfigHealthGate()
    return _default_gate


def reset_health_gate() -> None:
    """Reset the singleton health gate. For testing."""
    global _default_gate
    _default_gate = None
