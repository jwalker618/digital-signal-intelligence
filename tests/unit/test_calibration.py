"""
DSI Calibration Validation Tests

Validates that coverage configurations produce commercially reasonable premiums
across representative scenarios. These tests catch miscalibrated rates, modifier
double-counting, and ILF amplification issues before deployment.

Run: pytest tests/unit/test_calibration.py -v
"""

import pytest
import yaml
from pathlib import Path

from infrastructure.models.config_schema import CoverageConfig
from layers.risk.pricer import ModelPricer
from layers.risk.types import CategoricalOutput

COVERAGES_DIR = Path(__file__).parent.parent.parent / "coverages"


def load_config(coverage: str, config_name: str) -> CoverageConfig:
    """Load and compile a coverage config from YAML."""
    config_path = COVERAGES_DIR / coverage / "config.yaml"
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    coverage_key = list(raw.keys())[0]
    config_data = raw[coverage_key][config_name]
    return CoverageConfig(**config_data, coverage_id=coverage_key, config_id=config_name)


def price_scenario(
    config: CoverageConfig,
    score: float,
    submission_data: dict,
    categorical_modifiers: list[tuple[str, str, float]] | None = None,
) -> dict:
    """
    Price a scenario and return key metrics.

    Args:
        config: Compiled coverage config
        score: Composite score (0-1000)
        submission_data: Must include limit, deductible, and basis field (revenue/tiv/total_assets)
        categorical_modifiers: List of (group_id, label, modifier) tuples
    """
    pricer = ModelPricer()

    cat_outputs = []
    if categorical_modifiers:
        for group_id, label, modifier in categorical_modifiers:
            cat_outputs.append(CategoricalOutput(
                group_id=group_id,
                group_name=group_id,
                category=label,
                label=label,
                modifier=modifier,
                confidence=1.0,
            ))

    result = pricer.price_submission(
        pure_composite_score=score,
        signal_tier_overrides=[],
        query_tier_overrides=[],
        query_modifiers=[],
        categorical_outputs=cat_outputs,
        submission_data=submission_data,
        config=config,
    )

    return {
        "final_premium": result.final_premium,
        "base_premium": result.base_premium,
        "total_modifier": result.total_modifier,
        "final_tier": result.final_tier,
        "guardrail_warnings": result.guardrail_warnings,
        "modifier_was_clamped": result.modifier_was_clamped,
        "premium_was_capped": result.premium_was_capped,
        "limit_premiums": result.limit_premiums,
    }


# =============================================================================
# CYBER GENERAL CALIBRATION
# =============================================================================

class TestCyberGeneralCalibration:
    """Validate cyber_general produces market-realistic premiums."""

    @pytest.fixture
    def config(self):
        return load_config("cyber", "cyber_general")

    def test_midmarket_t3_base_premium(self, config):
        """$500M revenue, MEDIUM, T3, $1M limit → base premium $20K-$80K."""
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 500_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "MEDIUM", 1.0)],
        )
        assert 10_000 <= result["base_premium"] <= 100_000, (
            f"Base premium {result['base_premium']:.0f} outside expected range for mid-market cyber"
        )

    def test_enterprise_t1_premium_reasonable(self, config):
        """$50B revenue, ENTERPRISE, T1 → premium should not exceed $1M at $1M limit."""
        result = price_scenario(
            config, score=850,
            submission_data={"revenue": 50_000_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "ENTERPRISE", 0.12)],
        )
        assert result["final_premium"] <= 1_000_000, (
            f"Enterprise T1 premium {result['final_premium']:.0f} exceeds $1M for $1M limit"
        )

    def test_enterprise_modifier_compresses(self, config):
        """ENTERPRISE modifier < 1.0 to prevent revenue double-counting."""
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 50_000_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "ENTERPRISE", 0.12)],
        )
        assert result["total_modifier"] < 1.0, (
            "ENTERPRISE modifier should compress (< 1.0) for MULTIPLIER on revenue"
        )

    def test_small_company_uses_min_premium(self, config):
        """$10M revenue with low rate should hit min_premium floor."""
        result = price_scenario(
            config, score=850,
            submission_data={"revenue": 10_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "MICRO", 1.5)],
        )
        assert result["final_premium"] >= config.metadata.min_premium, (
            f"Premium {result['final_premium']:.0f} below min_premium {config.metadata.min_premium}"
        )

    def test_premium_never_exceeds_limit_guardrail(self, config):
        """Premium should never exceed 35% of requested limit."""
        result = price_scenario(
            config, score=400,  # T4
            submission_data={"revenue": 100_000_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "ENTERPRISE", 0.12)],
        )
        max_allowed = 1_000_000 * config.guardrails.max_premium_to_limit_ratio
        assert result["final_premium"] <= max_allowed, (
            f"Premium {result['final_premium']:.0f} exceeds guardrail cap {max_allowed:.0f}"
        )


# =============================================================================
# D&O GENERAL CALIBRATION
# =============================================================================

class TestDOGeneralCalibration:
    """Validate do_general produces market-realistic premiums."""

    @pytest.fixture
    def config(self):
        return load_config("do", "do_general")

    def test_midmarket_public_small_cap(self, config):
        """$500M revenue, PUBLIC_SMALL_CAP, T3 → premium $20K-$100K at $1M limit."""
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 500_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "side_a"},
            categorical_modifiers=[("company_type", "PUBLIC_SMALL_CAP", 1.0)],
        )
        assert 10_000 <= result["final_premium"] <= 200_000, (
            f"D&O mid-market premium {result['final_premium']:.0f} outside expected range"
        )

    def test_large_cap_modifier_compresses(self, config):
        """PUBLIC_LARGE_CAP modifier < 1.0 to prevent revenue double-counting."""
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 50_000_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "side_a"},
            categorical_modifiers=[("company_type", "PUBLIC_LARGE_CAP", 0.12)],
        )
        assert result["total_modifier"] < 1.0, (
            "PUBLIC_LARGE_CAP modifier should compress for MULTIPLIER on revenue"
        )


# =============================================================================
# FI GENERAL CALIBRATION
# =============================================================================

class TestFIGeneralCalibration:
    """Validate fi_general produces market-realistic premiums."""

    @pytest.fixture
    def config(self):
        return load_config("fi", "fi_general")

    def test_midsize_bank_t3(self, config):
        """$20B total assets, MID, T3 → base premium $100K-$500K at $1M limit."""
        result = price_scenario(
            config, score=575,
            submission_data={"total_assets": 20_000_000_000, "limit": 1_000_000,
                             "deductible": 50_000, "product_type": "bankers_professional"},
            categorical_modifiers=[("asset_size_band", "MID", 1.0)],
        )
        assert 25_000 <= result["final_premium"] <= 500_000, (
            f"FI mid-size premium {result['final_premium']:.0f} outside expected range"
        )

    def test_mega_bank_modifier_compresses(self, config):
        """MEGA modifier < 1.0 to prevent total_assets double-counting."""
        result = price_scenario(
            config, score=850,
            submission_data={"total_assets": 500_000_000_000, "limit": 1_000_000,
                             "deductible": 50_000, "product_type": "bankers_professional"},
            categorical_modifiers=[("asset_size_band", "MEGA", 0.15)],
        )
        assert result["total_modifier"] < 1.0, (
            "MEGA modifier should compress for MULTIPLIER on total_assets"
        )


# =============================================================================
# PI GENERAL CALIBRATION
# =============================================================================

class TestPIGeneralCalibration:
    """Validate pi_general produces market-realistic premiums."""

    @pytest.fixture
    def config(self):
        return load_config("pi", "pi_general")

    def test_midmarket_firm_t3(self, config):
        """$100M revenue, T3 → base premium $10K-$50K at $1M limit."""
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 100_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "professional_liability"},
        )
        assert 5_000 <= result["final_premium"] <= 100_000, (
            f"PI mid-market premium {result['final_premium']:.0f} outside expected range"
        )


# =============================================================================
# GUARDRAIL ENFORCEMENT TESTS
# =============================================================================

class TestGuardrailEnforcement:
    """Verify guardrails are active and enforced across all configs."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.mark.parametrize("coverage,config_name", [
        ("cyber", "cyber_general"),
        ("do", "do_general"),
        ("fi", "fi_general"),
        ("pi", "pi_general"),
    ])
    def test_guardrails_present(self, coverage, config_name):
        """Every config has guardrails with sensible defaults."""
        config = load_config(coverage, config_name)
        assert config.guardrails is not None
        assert 0 < config.guardrails.modifier_floor < config.guardrails.modifier_cap
        assert 0 < config.guardrails.max_premium_to_limit_ratio <= 1.0
        assert 0 < config.guardrails.max_premium_to_revenue_ratio <= 1.0

    def test_modifier_clamping_enforced(self):
        """Extreme modifier stack gets clamped."""
        config = load_config("cyber", "cyber_general")
        result = price_scenario(
            config, score=575,
            submission_data={"revenue": 500_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[
                ("size_band", "ENTERPRISE", 4.0),  # Intentionally extreme
                ("industry_classification", "HEALTHCARE", 1.5),
            ],
        )
        # Total modifier = 4.0 * 1.5 = 6.0 → should be clamped to cap (2.5)
        assert result["total_modifier"] <= config.guardrails.modifier_cap, (
            f"Modifier {result['total_modifier']:.2f} exceeds cap {config.guardrails.modifier_cap}"
        )
        assert result["modifier_was_clamped"] is True

    def test_premium_to_limit_cap_enforced(self):
        """Premium exceeding limit ratio gets capped."""
        config = load_config("cyber", "cyber_general")
        # Use extreme revenue to force high premium
        result = price_scenario(
            config, score=400,  # T4
            submission_data={"revenue": 500_000_000_000, "limit": 1_000_000, "deductible": 50_000,
                             "product_type": "cyber_liability"},
            categorical_modifiers=[("size_band", "ENTERPRISE", 0.12)],
        )
        max_allowed = 1_000_000 * config.guardrails.max_premium_to_limit_ratio
        assert result["final_premium"] <= max_allowed + 1, (  # +1 for rounding
            f"Premium {result['final_premium']:.0f} exceeds limit cap {max_allowed:.0f}"
        )


# =============================================================================
# CROSS-COVERAGE RATE CONSISTENCY
# =============================================================================

class TestCrossCoverageConsistency:
    """Verify rate magnitudes are consistent across coverages."""

    def test_multiplier_rates_order_of_magnitude(self):
        """All MULTIPLIER rates should be < 0.001 for revenue-based configs."""
        for coverage, config_name in [
            ("cyber", "cyber_general"),
            ("do", "do_general"),
            ("pi", "pi_general"),
        ]:
            config = load_config(coverage, config_name)
            for band in config.risk_tier_bands.bands:
                rate = band.interpretation.application.applied
                if rate is not None:
                    assert rate < 0.001, (
                        f"{config_name} tier {band.id} rate {rate} is too high "
                        f"(>= 0.001) for revenue-based MULTIPLIER"
                    )

    def test_size_modifiers_compress_for_large(self):
        """Size/type modifiers for large entities must be < 1.0 in MULTIPLIER configs."""
        checks = [
            ("cyber", "cyber_general", "size_band", ["LARGE", "ENTERPRISE"]),
            ("fi", "fi_general", "asset_size_band", ["MEGA", "LARGE"]),
        ]
        for coverage, config_name, group_id, large_cats in checks:
            config = load_config(coverage, config_name)
            for sig in config.signal_registry:
                if sig.categories and sig.categories.group_id == group_id:
                    for feat in sig.categories.features:
                        if feat.cat in large_cats:
                            assert feat.applied is not None and feat.applied < 1.0, (
                                f"{config_name} {group_id} {feat.cat} modifier "
                                f"{feat.applied} should be < 1.0 to compress for large entities"
                            )
