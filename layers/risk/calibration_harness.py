"""Calibration Harness — Comprehensive Config Validation.

Generates a systematic synthetic dataset across the full parameter space for
each coverage configuration, runs it through the pricing pipeline, and
validates that outputs are sensible. Unlike the health gate (which uses
minimal fixtures), this harness exercises:

  - Every product type per config
  - Every non-DECLINE tier
  - Multiple exposure size bands (micro through mega-cap)
  - Multiple limit cohorts
  - Multiple deductible options
  - Categorical modifier scenarios (benign, neutral, adverse)

The harness produces a per-config calibration report with pass/fail status,
distribution statistics, and flagged outliers.

Usage:
    python -m layers.risk.calibration_harness          # Run all configs
    python -m layers.risk.calibration_harness energy    # Run one coverage
    python -m layers.risk.calibration_harness --json    # JSON output

Integration:
    from layers.risk.calibration_harness import CalibrationHarness

    harness = CalibrationHarness()
    report = harness.run_all()
    if not report.passed:
        print(report.format_summary())
"""

from __future__ import annotations

import json
import logging
import math
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.models.config_schema import (
    CoverageConfig,
    LimitConfigType,
    PricingMethod,
    TierAction,
)
from layers.risk.pricer import ModelPricer
from layers.risk.rol_validator import ROLValidator, DEFAULT_ROL_APPETITE, ROLAppetiteBand
from layers.risk.types import CategoricalOutput, utcnow

logger = logging.getLogger("dsi.calibration_harness")


# ---------------------------------------------------------------------------
# Fixture definition
# ---------------------------------------------------------------------------

@dataclass
class CalibrationFixture:
    """A single synthetic submission for calibration."""
    config_id: str
    coverage_id: str
    label: str
    tier: int
    composite_score: float
    product_type: str
    submission_data: Dict[str, Any]
    categorical_outputs: List[CategoricalOutput]
    modifier_scenario: str  # "benign", "neutral", "adverse"
    exposure_size_label: str
    limit: int
    deductible: int


@dataclass
class FixtureResult:
    """Result of running a single fixture through the pipeline."""
    fixture: CalibrationFixture
    premium: float = 0.0
    base_premium: float = 0.0
    total_modifier: float = 1.0
    premium_after_modifiers: float = 0.0
    ilf_factor: float = 1.0
    deductible_factor: float = 1.0
    rol: float = 0.0
    premium_was_capped: bool = False
    capped_by_limit: bool = False
    capped_by_revenue: bool = False
    modifier_was_clamped: bool = False
    guardrail_warnings: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def pl_ratio(self) -> float:
        """Premium-to-limit ratio."""
        if self.fixture.limit > 0:
            return self.premium / self.fixture.limit
        return 0.0

    @property
    def passed(self) -> bool:
        return self.error is None


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

# Target P/L ratio ranges per tier (tier 1 = best risk, tier 5 = worst)
TARGET_PL_RANGES = {
    1: (0.0005, 0.08),   # Preferred: 0.05% - 8%
    2: (0.001, 0.12),    # Standard plus: 0.1% - 12%
    3: (0.002, 0.18),    # Standard: 0.2% - 18%
    4: (0.005, 0.25),    # Substandard: 0.5% - 25%
    5: (0.01, 0.35),     # Decline-adjacent: 1% - 35%
}


@dataclass
class ValidationFailure:
    """A single validation failure."""
    fixture_label: str
    check: str
    detail: str
    severity: str = "FAIL"  # FAIL or WARNING


@dataclass
class ConfigCalibrationResult:
    """Calibration result for a single configuration."""
    coverage_id: str
    config_id: str
    fixture_count: int = 0
    error_count: int = 0
    guardrail_hit_count: int = 0
    limit_cap_count: int = 0
    revenue_cap_count: int = 0
    modifier_clamp_count: int = 0
    outside_appetite_count: int = 0
    failures: List[ValidationFailure] = field(default_factory=list)
    results: List[FixtureResult] = field(default_factory=list)
    checked_at: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        return f"{self.coverage_id}/{self.config_id}"

    @property
    def passed(self) -> bool:
        fail_count = sum(1 for f in self.failures if f.severity == "FAIL")
        error_pct = 100 * self.error_count / self.fixture_count if self.fixture_count else 0
        guardrail_pct = 100 * self.guardrail_hit_count / self.fixture_count if self.fixture_count else 0
        return (
            fail_count == 0
            and error_pct < 10
            and guardrail_pct < 15  # Allow some guardrail hits for extreme scenarios
        )

    @property
    def guardrail_hit_pct(self) -> float:
        return 100 * self.guardrail_hit_count / self.fixture_count if self.fixture_count else 0.0

    @property
    def premiums(self) -> List[float]:
        return [r.premium for r in self.results if r.error is None]

    @property
    def pl_ratios(self) -> List[float]:
        return [r.pl_ratio for r in self.results if r.error is None and r.fixture.limit > 0]

    def premium_stats(self) -> Dict[str, float]:
        """Compute distribution statistics for premiums."""
        vals = self.premiums
        if not vals:
            return {}
        return {
            "count": len(vals),
            "min": min(vals),
            "max": max(vals),
            "median": statistics.median(vals),
            "mean": statistics.mean(vals),
            "p10": _percentile(vals, 10),
            "p90": _percentile(vals, 90),
        }

    def pl_ratio_stats(self) -> Dict[str, float]:
        """Compute distribution statistics for P/L ratios."""
        vals = self.pl_ratios
        if not vals:
            return {}
        return {
            "count": len(vals),
            "min": min(vals),
            "max": max(vals),
            "median": statistics.median(vals),
            "mean": statistics.mean(vals),
            "p10": _percentile(vals, 10),
            "p90": _percentile(vals, 90),
        }


@dataclass
class CalibrationReport:
    """Full calibration report across all configurations."""
    config_results: Dict[str, ConfigCalibrationResult] = field(default_factory=dict)
    total_fixtures: int = 0
    total_errors: int = 0

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.config_results.values())

    @property
    def failed_configs(self) -> List[str]:
        return [k for k, v in self.config_results.items() if not v.passed]

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        lines = []
        lines.append("=" * 80)
        lines.append("CALIBRATION HARNESS REPORT")
        lines.append("=" * 80)

        total = len(self.config_results)
        failed = len(self.failed_configs)
        lines.append(f"\nConfigs: {total}  |  Passed: {total - failed}  |  Failed: {failed}")
        lines.append(f"Total fixtures: {self.total_fixtures}  |  Errors: {self.total_errors}")
        lines.append("")

        lines.append(f"{'Configuration':<40s} {'Fixtures':>8s} {'Guardrail%':>10s} "
                      f"{'OutsideROL':>10s} {'Errors':>6s} {'Status':>10s}")
        lines.append("-" * 80)

        for key in sorted(self.config_results.keys()):
            r = self.config_results[key]
            status = "PASSED" if r.passed else "FAILED"
            lines.append(
                f"{key:<40s} {r.fixture_count:>8d} "
                f"{r.guardrail_hit_pct:>9.1f}% "
                f"{r.outside_appetite_count:>10d} "
                f"{r.error_count:>6d} "
                f"{status:>10s}"
            )

        # Show failures for failed configs
        for key in sorted(self.failed_configs):
            r = self.config_results[key]
            lines.append(f"\n--- FAILURES: {key} ---")
            pl_stats = r.pl_ratio_stats()
            if pl_stats:
                lines.append(f"  P/L ratio: min={pl_stats['min']:.4f} median={pl_stats['median']:.4f} "
                              f"max={pl_stats['max']:.4f} p90={pl_stats['p90']:.4f}")
            prem_stats = r.premium_stats()
            if prem_stats:
                lines.append(f"  Premium: min=${prem_stats['min']:,.0f} median=${prem_stats['median']:,.0f} "
                              f"max=${prem_stats['max']:,.0f}")
            lines.append(f"  Guardrail hits: {r.guardrail_hit_count}/{r.fixture_count} "
                          f"({r.guardrail_hit_pct:.1f}%) — "
                          f"limit cap: {r.limit_cap_count}, revenue cap: {r.revenue_cap_count}")
            # Breakdown by exposure size
            size_total: Dict[str, int] = {}
            size_capped: Dict[str, int] = {}
            for fr in r.results:
                if fr.error is None:
                    sz = fr.fixture.exposure_size_label
                    size_total[sz] = size_total.get(sz, 0) + 1
                    if fr.premium_was_capped:
                        size_capped[sz] = size_capped.get(sz, 0) + 1
            if size_total:
                lines.append("  Guardrail hits by exposure size:")
                for sz in ["MICRO", "SMALL", "MEDIUM", "LARGE", "VERY_LARGE", "MEGA", "ULTRA", "N/A"]:
                    t = size_total.get(sz, 0)
                    c = size_capped.get(sz, 0)
                    if t > 0:
                        lines.append(f"    {sz:>12s}: {c:>4d}/{t:>4d} ({100*c/t:>5.1f}%)")

            for failure in r.failures[:10]:
                lines.append(f"  [{failure.severity}] {failure.check}: {failure.detail}")
            if len(r.failures) > 10:
                lines.append(f"  ... and {len(r.failures) - 10} more failures")

        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        """Serialize report to JSON-compatible dict."""
        result = {
            "passed": self.passed,
            "total_fixtures": self.total_fixtures,
            "total_errors": self.total_errors,
            "failed_configs": self.failed_configs,
            "configs": {},
        }
        for key, r in self.config_results.items():
            result["configs"][key] = {
                "passed": r.passed,
                "fixture_count": r.fixture_count,
                "error_count": r.error_count,
                "guardrail_hit_count": r.guardrail_hit_count,
                "guardrail_hit_pct": round(r.guardrail_hit_pct, 2),
                "limit_cap_count": r.limit_cap_count,
                "revenue_cap_count": r.revenue_cap_count,
                "modifier_clamp_count": r.modifier_clamp_count,
                "outside_appetite_count": r.outside_appetite_count,
                "failure_count": len(r.failures),
                "premium_stats": r.premium_stats(),
                "pl_ratio_stats": r.pl_ratio_stats(),
                "failures": [
                    {"label": f.fixture_label, "check": f.check,
                     "detail": f.detail, "severity": f.severity}
                    for f in r.failures[:50]  # Cap at 50 to keep JSON manageable
                ],
            }
        return result


def _percentile(data: List[float], pct: int) -> float:
    """Simple percentile calculation."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


# ---------------------------------------------------------------------------
# Exposure size bands for systematic testing
# ---------------------------------------------------------------------------

EXPOSURE_SIZE_BANDS = [
    # (label, basis_value) — these are TIV / hull_value / total_assets values
    ("MICRO",       500_000),
    ("SMALL",       5_000_000),
    ("MEDIUM",      50_000_000),
    ("LARGE",       500_000_000),
    ("VERY_LARGE",  5_000_000_000),
    ("MEGA",        50_000_000_000),
    ("ULTRA",       200_000_000_000),
]

# Basis-specific scale factors. Different basis fields have very different
# typical numeric magnitudes: revenue/tiv/assets are in the range 10^6-10^11,
# but underlying_premium is typically 1-2% of the limit (10^4-10^8), payroll
# is typically 20-40% of revenue, and fleet_value is 5-15% of revenue.
# Without this scaling the calibration harness feeds revenue-scale values
# into tiny-basis configs and produces premiums that always hit guardrails.
BASIS_SCALE = {
    # Umbrella primary-premium is typically 0.1-0.3% of annual revenue
    # for large commercial accounts. 0.002 places the EXPOSURE_SIZE_BANDS
    # from $1k (MICRO) up to $400M (ULTRA) — the high end being a
    # national-carrier primary book. Realistic for umbrella calibration.
    "underlying_premium": 0.002,
    "payroll":            0.30,   # payroll ≈ 30% of revenue for typical employer
    "fleet_value":        0.10,   # fleet value ≈ 10% of revenue for transport
    "bonded_obligation":  0.20,   # contract-surety bonded amount
    "subject_premium":    0.03,   # reinsurance subject premium on ceded book
    "gross_written_premium": 0.05,
}


def _scale_basis_value(raw_value: int, basis_field: str) -> int:
    """Apply BASIS_SCALE to a raw EXPOSURE_SIZE_BANDS value."""
    factor = BASIS_SCALE.get(basis_field, 1.0)
    return max(1_000, int(raw_value * factor))

# Limit cohorts to test (for DECOUPLED configs)
LIMIT_COHORTS = [
    1_000_000,
    5_000_000,
    10_000_000,
    25_000_000,
    50_000_000,
    100_000_000,
    250_000_000,
    500_000_000,
]

# Modifier scenarios: simulate different combinations of categorical modifiers
MODIFIER_SCENARIOS = {
    "benign": 0.7,    # Favourable modifiers (e.g., supermajor, low complexity)
    "neutral": 1.0,   # No modifier impact
    "adverse": 1.6,   # Unfavourable modifiers (e.g., unknown operator, high complexity)
}


# ---------------------------------------------------------------------------
# Fixture generator
# ---------------------------------------------------------------------------

def generate_fixtures_for_config(
    coverage_id: str,
    config_id: str,
    config: CoverageConfig,
) -> List[CalibrationFixture]:
    """Generate comprehensive calibration fixtures for a single config.

    Produces fixtures across the full parameter space, filtered by routing
    constraints so only submissions that would actually reach this config
    in production are tested:
    - Every product type
    - Every non-DECLINE tier
    - Multiple exposure sizes (within routing bounds)
    - Multiple limit cohorts (within routing bounds)
    - Multiple modifier scenarios
    """
    fixtures = []

    # Get product types
    product_types = config.metadata.product_types or ["standard"]

    # Get non-DECLINE tier bands
    priceable_bands = []
    for band in config.risk_tier_bands.bands:
        action = band.interpretation.action.value
        if action == "DECLINE":
            continue
        app = band.interpretation.application
        if app is None:
            continue
        if (app.applied or 0) <= 0 and (app.value or 0) <= 0:
            continue
        priceable_bands.append(band)

    if not priceable_bands:
        return fixtures

    # Determine basis field and pricing method from first priceable band
    first_app = priceable_bands[0].interpretation.application
    basis_field = first_app.basis or "tiv"
    is_multiplier = first_app.method == PricingMethod.MULTIPLIER

    # Handle categorical basis: the pricer falls back to PREMIUM_BASE
    # because submission_data won't have a numeric "categorical" field.
    # Treat these like PREMIUM_BASE configs with a synthetic base.
    is_categorical = basis_field in ("categorical", "category")
    if is_categorical:
        is_multiplier = False

    # Extract routing constraints to filter fixture parameters
    basis_floor, basis_ceiling = _get_routing_bounds(config, basis_field)
    limit_floor, limit_ceiling = _get_routing_bounds(config, "limit")

    # Build deductible options from product type configs
    deductible_options_map = {}
    for pt in product_types:
        pt_pricing = config.pricing.by_product_type.get(pt)
        if pt_pricing and pt_pricing.deductible_factors:
            deds = sorted(df.deductible for df in pt_pricing.deductible_factors)
            deductible_options_map[pt] = deds
        else:
            deductible_options_map[pt] = [config.pricing.base_deductible_reference]

    # Choose limit options based on config type, filtered by routing constraints
    limit_config = config.limit_configuration
    if limit_config and limit_config.type == LimitConfigType.BUNDLED and limit_config.packages:
        limit_options = sorted(set(pkg.limit for pkg in limit_config.packages))
    elif limit_config and limit_config.type == LimitConfigType.TOWER:
        # For tower configs, use the total tower limit
        total = sum(l.limit for l in (limit_config.layers or []))
        limit_options = [total] if total > 0 else [10_000_000]
    else:
        # DECOUPLED: use our standard cohorts, filtered by routing constraints
        limit_options = [
            lim for lim in LIMIT_COHORTS
            if lim >= limit_floor and (limit_ceiling == 0 or lim <= limit_ceiling)
        ]
        if not limit_options:
            # If all standard cohorts are outside routing bounds, generate
            # sensible options within the constraint range
            limit_options = _generate_range_options(limit_floor, limit_ceiling or 500_000_000)

    # Choose exposure sizes based on method, filtered by routing constraints
    if is_multiplier:
        # Scale the standard band values to the basis field's typical
        # magnitude (e.g. underlying_premium is ~2% of revenue, payroll
        # ~30% of revenue). Without this, umbrella / WC / auto / surety
        # configs see revenue-scale synthetic values and always hit
        # guardrails. See BASIS_SCALE dict for per-field factors.
        exposure_sizes = [
            (label, _scale_basis_value(val, basis_field))
            for label, val in EXPOSURE_SIZE_BANDS
            if _scale_basis_value(val, basis_field) >= basis_floor
            and (
                basis_ceiling == 0
                or _scale_basis_value(val, basis_field) <= basis_ceiling
            )
        ]
        if not exposure_sizes:
            # Generate exposure sizes within routing bounds
            exposure_sizes = [
                (f"ROUTED_{i+1}", val)
                for i, val in enumerate(
                    _generate_range_options(basis_floor, basis_ceiling or 100_000_000_000)
                )
            ]
    else:
        # PREMIUM_BASE or categorical: no basis field needed
        exposure_sizes = [("N/A", 0)]

    # Build categorical modifier scenarios
    cat_groups = _extract_categorical_groups(config)

    for band in priceable_bands:
        tier = band.id
        score_mid = (band.interpretation.bands.min + band.interpretation.bands.max) / 2

        for pt in product_types:
            # Use subset of deductibles (min, mid, max) to keep fixture count manageable
            all_deds = deductible_options_map.get(pt, [config.pricing.base_deductible_reference])
            if len(all_deds) >= 3:
                test_deds = [all_deds[0], all_deds[len(all_deds) // 2], all_deds[-1]]
            else:
                test_deds = all_deds

            # Tier rate is used below to skip economically-impossible
            # (basis, limit) combos — where raw premium would exceed 3x
            # the limit we don't bother pricing the fixture (guaranteed
            # to clamp, drags the guardrail-hit-rate diagnostic without
            # telling us anything about pricing calibration).
            tier_app = band.interpretation.application
            tier_rate = (tier_app.applied or 0) if tier_app else 0

            for size_label, basis_value in exposure_sizes:
                for limit in limit_options:
                    # Skip unrealistic (basis, limit) pairings where raw
                    # premium is guaranteed to clamp to the limit cap —
                    # e.g. MEGA underlying-premium against a $5M umbrella
                    # limit isn't sold in the real market. Caps the
                    # harness's fixture set to economically-sensible
                    # scenarios.
                    if is_multiplier and tier_rate > 0 and basis_value > 0 and limit > 0:
                        raw_est = tier_rate * basis_value
                        if raw_est > 1.5 * limit:
                            continue
                    for ded in test_deds:
                        for mod_scenario, mod_factor in MODIFIER_SCENARIOS.items():
                            submission = {
                                "limit": limit,
                                "deductible": ded,
                                "product_type": pt,
                            }

                            if is_multiplier and basis_value > 0:
                                # When the config prices "basis=limit" the
                                # basis field IS limit — skip the overwrite
                                # so submission's limit matches the fixture
                                # label (otherwise the diagnostic checks use
                                # a different limit than the pricer and the
                                # premium_exceeds_limit_ratio check reads
                                # nonsensical P/Ls).
                                if basis_field != "limit":
                                    submission[basis_field] = basis_value
                                # Provide revenue for guardrail check
                                # Revenue is typically 2-10x the insured value
                                submission["revenue"] = max(basis_value * 3, limit * 10)
                            else:
                                # PREMIUM_BASE or categorical: provide revenue for
                                # guardrail checks, proportional to the limit
                                submission["revenue"] = limit * 20

                            # Build categorical outputs for this modifier scenario
                            cat_outputs = _build_modifier_scenario(
                                cat_groups, mod_scenario, mod_factor
                            )

                            label = (
                                f"t{tier}_{pt}_{size_label}_{limit // 1_000_000}M"
                                f"_d{ded // 1_000}K_{mod_scenario}"
                            )

                            fixtures.append(CalibrationFixture(
                                config_id=config_id,
                                coverage_id=coverage_id,
                                label=label,
                                tier=tier,
                                composite_score=score_mid,
                                product_type=pt,
                                submission_data=submission,
                                categorical_outputs=cat_outputs,
                                modifier_scenario=mod_scenario,
                                exposure_size_label=size_label,
                                limit=limit,
                                deductible=ded,
                            ))

    return fixtures


def _extract_categorical_groups(config: CoverageConfig) -> List[Dict[str, Any]]:
    """Extract categorical group definitions from config signal registry.

    Returns list of {group_id, group_name, features: [{cat, label, modifier}]}
    """
    groups = []
    seen_group_ids = set()

    for signal in config.signal_registry:
        if signal.categories and signal.categories.group_id not in seen_group_ids:
            group_id = signal.categories.group_id
            seen_group_ids.add(group_id)
            features = []
            for feat in signal.categories.features:
                features.append({
                    "cat": feat.cat,
                    "label": feat.label or feat.cat,
                    "modifier": feat.applied if feat.applied is not None else 1.0,
                })
            groups.append({
                "group_id": group_id,
                "group_name": signal.id,
                "features": features,
            })

    return groups


def _build_modifier_scenario(
    cat_groups: List[Dict[str, Any]],
    scenario: str,
    target_factor: float,
) -> List[CategoricalOutput]:
    """Build CategoricalOutput list for a modifier scenario.

    For each categorical group, pick the feature whose modifier is closest
    to the target scenario factor.
    """
    outputs = []

    for group in cat_groups:
        features = group["features"]
        if not features:
            continue

        # Find the feature closest to the target factor
        best = min(features, key=lambda f: abs(f["modifier"] - target_factor))

        outputs.append(CategoricalOutput(
            group_id=group["group_id"],
            group_name=group["group_name"],
            category=best["cat"],
            label=best["label"],
            modifier=best["modifier"],
            confidence=0.95,
            extracted_at=utcnow(),
        ))

    return outputs


def _get_routing_bounds(
    config: CoverageConfig,
    field_name: str,
) -> Tuple[int, int]:
    """Extract floor/ceiling bounds for a field from routing constraints.

    Returns (floor, ceiling) where 0 = unbounded.
    """
    floor = 0
    ceiling = 0

    for rc in config.metadata.routing_constraints:
        if rc.field != field_name:
            continue
        try:
            val = int(rc.value) if isinstance(rc.value, (int, float)) else 0
        except (ValueError, TypeError):
            continue

        op = rc.operator.value if hasattr(rc.operator, "value") else str(rc.operator)
        if op in (">", ">="):
            floor = max(floor, val)
        elif op in ("<", "<="):
            ceiling = val if ceiling == 0 else min(ceiling, val)

    return floor, ceiling


def _generate_range_options(floor: int, ceiling: int) -> List[int]:
    """Generate sensible test values within a routing constraint range.

    Produces 3-5 logarithmically spaced values between floor and ceiling.
    """
    if floor <= 0:
        floor = 1_000_000
    if ceiling <= floor:
        ceiling = floor * 100

    options = []
    current = floor
    while current <= ceiling and len(options) < 5:
        options.append(current)
        current *= 5  # Rough log spacing: 5x steps

    # Always include the ceiling if not already there
    if options and options[-1] != ceiling:
        options.append(ceiling)

    return options


# ---------------------------------------------------------------------------
# Core harness
# ---------------------------------------------------------------------------

class CalibrationHarness:
    """Runs comprehensive calibration across all configurations.

    Generates systematic synthetic fixtures, runs them through the full
    pricing pipeline, and validates outputs against expected ranges.
    """

    def __init__(
        self,
        max_guardrail_hit_pct: float = 15.0,
        max_error_pct: float = 10.0,
    ):
        self.max_guardrail_hit_pct = max_guardrail_hit_pct
        self.max_error_pct = max_error_pct
        self._pricer = ModelPricer()
        self._rol_validator = ROLValidator()

    def run_all(
        self,
        coverage_filter: Optional[str] = None,
    ) -> CalibrationReport:
        """Run calibration across all (or filtered) configurations.

        Args:
            coverage_filter: If set, only run configs for this coverage_id.

        Returns:
            CalibrationReport with per-config results.
        """
        from infrastructure.models.compiler import get_compiled_configs

        configs = get_compiled_configs()
        report = CalibrationReport()

        for coverage_id, coverage in sorted(configs.items()):
            if coverage_filter and coverage_id != coverage_filter:
                continue

            for config_id, config in sorted(coverage.configurations.items()):
                result = self.calibrate_config(coverage_id, config_id, config)
                report.config_results[result.key] = result
                report.total_fixtures += result.fixture_count
                report.total_errors += result.error_count

        return report

    def calibrate_config(
        self,
        coverage_id: str,
        config_id: str,
        config: CoverageConfig,
    ) -> ConfigCalibrationResult:
        """Run calibration for a single configuration."""
        result = ConfigCalibrationResult(
            coverage_id=coverage_id,
            config_id=config_id,
        )

        fixtures = generate_fixtures_for_config(coverage_id, config_id, config)
        result.fixture_count = len(fixtures)

        if not fixtures:
            result.failures.append(ValidationFailure(
                fixture_label="N/A",
                check="fixture_generation",
                detail="No fixtures could be generated — config may have no priceable tiers",
            ))
            return result

        logger.info("Calibrating %s/%s: %d fixtures", coverage_id, config_id, len(fixtures))

        for fixture in fixtures:
            fx_result = self._run_fixture(fixture, config)
            result.results.append(fx_result)

            if fx_result.error:
                result.error_count += 1
                continue

            if fx_result.premium_was_capped:
                result.guardrail_hit_count += 1
            if fx_result.capped_by_limit:
                result.limit_cap_count += 1
            if fx_result.capped_by_revenue:
                result.revenue_cap_count += 1

            if fx_result.modifier_was_clamped:
                result.modifier_clamp_count += 1

            # ROL check
            rol_result = self._rol_validator.validate_rol(
                fx_result.premium, fixture.limit
            )
            fx_result.rol = rol_result.rol

            if not rol_result.within_appetite:
                result.outside_appetite_count += 1

        # Run validation checks
        self._validate_results(result, config)

        return result

    def _run_fixture(
        self,
        fixture: CalibrationFixture,
        config: CoverageConfig,
    ) -> FixtureResult:
        """Run a single fixture through the pricing pipeline."""
        fx_result = FixtureResult(fixture=fixture)

        try:
            pricing = self._pricer.price_submission(
                pure_composite_score=fixture.composite_score,
                signal_tier_overrides=[],
                query_tier_overrides=[],
                query_modifiers=[],
                categorical_outputs=fixture.categorical_outputs,
                submission_data=fixture.submission_data,
                config=config,
            )

            fx_result.premium = pricing.final_premium
            fx_result.base_premium = pricing.base_premium
            fx_result.total_modifier = pricing.total_modifier
            fx_result.premium_after_modifiers = pricing.premium_after_modifiers
            fx_result.premium_was_capped = pricing.premium_was_capped
            fx_result.modifier_was_clamped = pricing.modifier_was_clamped
            fx_result.guardrail_warnings = pricing.guardrail_warnings

            # Classify which guardrail capped the premium
            for w in pricing.guardrail_warnings:
                source = w.get("source", "")
                if source == "premium_cap_by_limit":
                    fx_result.capped_by_limit = True
                elif source == "premium_cap_by_revenue":
                    fx_result.capped_by_revenue = True

            # Extract ILF and deductible factor from limit details
            if pricing.limit_premium_details:
                for detail in pricing.limit_premium_details:
                    if detail.limit == fixture.limit:
                        fx_result.ilf_factor = detail.ilf_factor
                        fx_result.deductible_factor = detail.deductible_factor
                        break

        except Exception as e:
            fx_result.error = str(e)
            logger.warning(
                "Fixture %s failed: %s", fixture.label, e
            )

        return fx_result

    def _validate_results(
        self,
        result: ConfigCalibrationResult,
        config: CoverageConfig,
    ) -> None:
        """Run validation checks on collected results."""
        successful = [r for r in result.results if r.error is None]
        if not successful:
            result.failures.append(ValidationFailure(
                fixture_label="ALL",
                check="pipeline_execution",
                detail="All fixtures failed with errors",
            ))
            return

        # Check 1: Guardrail hit rate
        if result.fixture_count > 0:
            guardrail_pct = result.guardrail_hit_pct
            if guardrail_pct > self.max_guardrail_hit_pct:
                result.failures.append(ValidationFailure(
                    fixture_label="AGGREGATE",
                    check="guardrail_hit_rate",
                    detail=(
                        f"Guardrail hit rate {guardrail_pct:.1f}% exceeds "
                        f"threshold {self.max_guardrail_hit_pct:.1f}% — "
                        f"guardrails are acting as primary pricing control"
                    ),
                ))

        # Check 2: P/L ratio sanity per tier
        tier_results: Dict[int, List[FixtureResult]] = {}
        for r in successful:
            tier = r.fixture.tier
            tier_results.setdefault(tier, []).append(r)

        for tier, tier_fxs in tier_results.items():
            pl_ratios = [r.pl_ratio for r in tier_fxs if r.fixture.limit > 0]
            if not pl_ratios:
                continue

            target_min, target_max = TARGET_PL_RANGES.get(tier, (0.001, 0.25))
            median_pl = statistics.median(pl_ratios)
            max_pl = max(pl_ratios)
            min_pl = min(pl_ratios)

            # Median P/L should be within target range
            if median_pl > target_max * 1.5:
                result.failures.append(ValidationFailure(
                    fixture_label=f"TIER_{tier}",
                    check="pl_ratio_high",
                    detail=(
                        f"Tier {tier} median P/L ratio {median_pl:.4f} "
                        f"exceeds 1.5x target ceiling {target_max:.4f}"
                    ),
                ))
            if median_pl < target_min * 0.5 and median_pl > 0:
                result.failures.append(ValidationFailure(
                    fixture_label=f"TIER_{tier}",
                    check="pl_ratio_low",
                    detail=(
                        f"Tier {tier} median P/L ratio {median_pl:.4f} "
                        f"below 0.5x target floor {target_min:.4f}"
                    ),
                    severity="WARNING",
                ))

        # Check 3: Premium monotonicity — worse tier should produce higher premiums
        # (controlling for same product type, exposure, limit, deductible, modifier)
        self._check_monotonicity(result, successful)

        # Check 4: No absurd premiums (exceeding the configured limit ratio)
        pl_cap = config.guardrails.max_premium_to_limit_ratio
        for r in successful:
            if r.fixture.limit > 0 and r.premium > r.fixture.limit * pl_cap:
                result.failures.append(ValidationFailure(
                    fixture_label=r.fixture.label,
                    check="premium_exceeds_limit_ratio",
                    detail=(
                        f"[{r.fixture.label}] Premium ${r.premium:,.0f} exceeds {pl_cap:.0%} of "
                        f"limit ${r.fixture.limit:,.0f} "
                        f"(P/L={r.pl_ratio:.2%})"
                    ),
                ))

        # Check 5: Premium should not exceed revenue
        for r in successful:
            revenue = r.fixture.submission_data.get("revenue", 0)
            if revenue > 0 and r.premium > revenue:
                result.failures.append(ValidationFailure(
                    fixture_label=r.fixture.label,
                    check="premium_exceeds_revenue",
                    detail=(
                        f"Premium ${r.premium:,.0f} exceeds "
                        f"revenue ${revenue:,.0f}"
                    ),
                ))

    def _check_monotonicity(
        self,
        result: ConfigCalibrationResult,
        successful: List[FixtureResult],
    ) -> None:
        """Check that worse tiers produce higher base rates.

        Groups fixtures by (product_type, exposure_size, limit, deductible,
        modifier_scenario) and checks that tier N+1 >= tier N for base premium.
        """
        grouped: Dict[str, Dict[int, List[FixtureResult]]] = {}

        for r in successful:
            f = r.fixture
            key = (
                f"{f.product_type}|{f.exposure_size_label}|"
                f"{f.limit}|{f.deductible}|{f.modifier_scenario}"
            )
            grouped.setdefault(key, {}).setdefault(f.tier, []).append(r)

        violations = 0
        for key, tier_map in grouped.items():
            tiers = sorted(tier_map.keys())
            for i in range(len(tiers) - 1):
                t_better = tiers[i]
                t_worse = tiers[i + 1]
                # Compare median premiums
                premiums_better = [r.premium for r in tier_map[t_better]]
                premiums_worse = [r.premium for r in tier_map[t_worse]]
                if not premiums_better or not premiums_worse:
                    continue
                median_better = statistics.median(premiums_better)
                median_worse = statistics.median(premiums_worse)
                # Worse tier should have >= premium (with 5% tolerance)
                if median_worse < median_better * 0.95 and median_better > 0:
                    violations += 1

        if violations > 0:
            result.failures.append(ValidationFailure(
                fixture_label="AGGREGATE",
                check="tier_monotonicity",
                detail=(
                    f"{violations} tier monotonicity violations detected — "
                    f"worse tiers producing lower premiums than better tiers"
                ),
                severity="WARNING",
            ))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Run calibration harness from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    coverage_filter = None
    json_output = False

    for arg in sys.argv[1:]:
        if arg == "--json":
            json_output = True
        elif arg == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            coverage_filter = arg

    harness = CalibrationHarness()
    report = harness.run_all(coverage_filter=coverage_filter)

    if json_output:
        print(json.dumps(report.to_json(), indent=2, default=str))
    else:
        print(report.format_summary())

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
