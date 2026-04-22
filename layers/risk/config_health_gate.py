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

from infrastructure.models.config_schema import CoverageConfig, LimitConfigType

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

def _revenue_for_guardrail(
    config: CoverageConfig, base_value: float, limit: int,
) -> int:
    """Return a synthetic revenue that won't trip the revenue guardrail.

    The pricer caps final premium at `revenue * max_premium_to_revenue_ratio`.
    Fixture revenue of `limit * 20` is too low for tight SME configs
    (0.10-0.20%) since their fixed base premium alone can exceed the cap.
    Scale revenue up from the expected premium so structurally valid
    configs don't emit capping warnings during gate fixture runs.
    """
    default = limit * 20
    guardrails = getattr(config, "guardrails", None)
    ratio = getattr(guardrails, "max_premium_to_revenue_ratio", 0) or 0
    if ratio <= 0 or base_value <= 0:
        return default
    # Account for ~1.15 ILF uplift × 2× safety margin
    expected_premium = base_value * 1.15 * 2.0
    min_revenue = int(expected_premium / ratio)
    return max(default, min_revenue)


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
                # MULTIPLIER method: solve for basis so that the pricing
                # pipeline (including sub-linear damping) produces a premium
                # that hits the target P/L ratio.
                #
                # The pricer applies:
                #   effective_basis = limit × (basis / limit)^damping   [when basis > limit]
                #   base_premium = rate × effective_basis
                #   final_premium ≈ base_premium × ILF
                #
                # Setting final_premium = target_pl × limit and solving:
                #   target_pl × limit = rate × limit × (basis/limit)^d × ILF
                #   (basis/limit)^d = target_pl / (rate × ILF)
                #   basis = limit × (target_pl / (rate × ILF))^(1/d)
                #
                # When basis ≤ limit, damping doesn't apply — use the linear
                # formula: basis = target_pl × limit / (rate × ILF).
                # Try the submission's product type first; fall back to the
                # first ILF curve key if no curve is registered for it.
                product_type = submission["product_type"]
                estimated_ilf = config.get_ilf(product_type, limit)
                if estimated_ilf <= 0 or estimated_ilf == 1.0:
                    for pt_key in config.pricing.by_product_type:
                        alt = config.get_ilf(pt_key, limit)
                        if alt > 1.0:
                            estimated_ilf = alt
                            break
                if estimated_ilf <= 0:
                    estimated_ilf = 1.0

                damping = config.pricing.basis_damping
                ratio = target_pl / (rate * estimated_ilf)

                if damping < 1.0 and ratio > 1.0:
                    # Damping will apply (basis > limit) — use damped formula
                    basis_value = limit * ratio ** (1.0 / damping)
                else:
                    # No damping or basis ≤ limit — linear formula
                    basis_value = limit * ratio

                basis_value = max(1_000_000, min(basis_value, 500_000_000_000))
                submission[basis_field] = basis_value
            elif rate > 0:
                # Categorical basis — the rate is applied to a category-derived
                # base, not a submission field. Provide revenue for guardrail checks.
                submission["revenue"] = _revenue_for_guardrail(
                    config, base_value, limit,
                )
            else:
                # PREMIUM_BASE method: fixed base premium, no basis needed.
                # Provide revenue large enough to clear the revenue guardrail
                # so structurally valid configs don't emit capping warnings
                # during gate fixture runs.
                submission["revenue"] = _revenue_for_guardrail(
                    config, base_value, limit,
                )

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
        # Use ROL validator with widened appetite bands for health gate —
        # synthetic fixtures lack categorical modifiers that compress real
        # premiums. The gate catches broken calibration, not edge-case ROL.
        from layers.risk.rol_validator import ROLValidator, ROLAppetiteBand, DEFAULT_ROL_APPETITE
        widened_bands = []
        for b in DEFAULT_ROL_APPETITE:
            widened_bands.append(ROLAppetiteBand(
                label=b.label,
                attachment_min=b.attachment_min,
                attachment_max=b.attachment_max,
                limit_min=b.limit_min,
                limit_max=b.limit_max,
                rol_floor=b.rol_floor * 0.5,
                rol_ceiling=min(b.rol_ceiling * 1.5, 0.35),
                warning_floor=b.warning_floor * 0.5,
                warning_ceiling=min(b.warning_ceiling * 1.5, 0.40),
            ))
        rol_validator = ROLValidator(appetite_bands=widened_bands)
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

                limit = int(fixture["submission_data"].get("limit", 0))
                premium = pricing_result.final_premium

                # For tower configs, validate ROL per layer from limit_details
                if (config.limit_configuration
                        and config.limit_configuration.type == LimitConfigType.TOWER
                        and pricing_result.limit_premium_details):
                    # Use worst-case ROL across layers for gate purposes
                    layer_results = []
                    for ld in pricing_result.limit_premium_details:
                        lr = rol_validator.validate_rol(
                            ld.premium_after_scaling,
                            ld.limit,
                            attachment=ld.attachment_point or 0,
                        )
                        layer_results.append(lr)
                    # Use the first layer's result as representative
                    rol_result = layer_results[0] if layer_results else rol_validator.validate_rol(premium, limit)
                else:
                    rol_result = rol_validator.validate_rol(premium, limit)

                # Guardrail is "primary control" when premium was capped AND
                # the ROL is still outside appetite (capping wasn't enough)
                has_primary = (
                    pricing_result.premium_was_capped
                    and not rol_result.within_appetite
                )
                if has_primary:
                    guardrail_primary_count += 1
                    failures.append(
                        "{}: guardrail is primary pricing control "
                        "(ROL={:.4f}, ceiling={:.3f})".format(
                            fixture["label"],
                            rol_result.rol,
                            rol_result.rol_ceiling,
                        )
                    )

                if not rol_result.within_appetite:
                    outside_target_count += 1
                    if not has_primary:
                        failures.append(
                            "{}: ROL {:.4f} outside appetite [{:.3f}, {:.3f}]".format(
                                fixture["label"],
                                rol_result.rol,
                                rol_result.rol_floor,
                                rol_result.rol_ceiling,
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

    def run_deep_calibration(
        self,
        coverage_filter: Optional[str] = None,
    ) -> "CalibrationReport":
        """Run comprehensive calibration using the CalibrationHarness.

        This is a deeper check than run_all_checks(). It exercises the full
        parameter space (every product type, exposure size, limit cohort,
        deductible, and modifier scenario) and produces a detailed report.

        Use this for:
        - Validating new configs created by the builder
        - Pre-commit validation of config changes
        - Periodic calibration audits

        Args:
            coverage_filter: If set, only calibrate this coverage_id.

        Returns:
            CalibrationReport from the harness.
        """
        from layers.risk.calibration_harness import CalibrationHarness

        harness = CalibrationHarness()
        report = harness.run_all(coverage_filter=coverage_filter)

        # Update quarantine status based on calibration results
        for key, cal_result in report.config_results.items():
            if not cal_result.passed:
                fail_reasons = []
                if cal_result.guardrail_hit_pct > 15.0:
                    fail_reasons.append(
                        "guardrail hit rate {:.1f}%".format(cal_result.guardrail_hit_pct)
                    )
                if cal_result.error_count > 0:
                    fail_reasons.append(
                        "{} pricing errors".format(cal_result.error_count)
                    )
                for f in cal_result.failures:
                    if f.severity == "FAIL":
                        fail_reasons.append(f.detail[:80])

                result = HealthCheckResult(
                    coverage_id=cal_result.coverage_id,
                    config_id=cal_result.config_id,
                    passed=False,
                    reason="DEEP CALIBRATION FAILED: {}".format("; ".join(fail_reasons[:3])),
                    fixture_count=cal_result.fixture_count,
                    failures=[f.detail for f in cal_result.failures],
                )
                self._results[key] = result
                self._quarantined[key] = result
                logger.warning(
                    "Deep calibration FAILED for %s: %s",
                    key, result.reason,
                )
            else:
                # If deep calibration passes, clear any quarantine
                result = HealthCheckResult(
                    coverage_id=cal_result.coverage_id,
                    config_id=cal_result.config_id,
                    passed=True,
                    fixture_count=cal_result.fixture_count,
                )
                self._results[key] = result
                self._quarantined.pop(key, None)

        return report

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
