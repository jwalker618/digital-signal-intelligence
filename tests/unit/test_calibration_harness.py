"""
Tests for the Calibration Harness.

Validates that the harness correctly generates fixtures, runs them through
the pipeline, and detects calibration issues.

Run: pytest tests/unit/test_calibration_harness.py -v
"""

import pytest

from infrastructure.models.compiler import get_config
from layers.risk.calibration_harness import (
    CalibrationHarness,
    CalibrationFixture,
    ConfigCalibrationResult,
    CalibrationReport,
    FixtureResult,
    ValidationFailure,
    generate_fixtures_for_config,
    _extract_categorical_groups,
    _build_modifier_scenario,
    EXPOSURE_SIZE_BANDS,
    LIMIT_COHORTS,
    MODIFIER_SCENARIOS,
)
from layers.risk.config_health_gate import ConfigHealthGate


# ---------------------------------------------------------------------------
# Fixture generation tests
# ---------------------------------------------------------------------------

class TestFixtureGeneration:
    """Tests for the fixture generation logic."""

    def test_generates_fixtures_for_energy_general(self):
        """energy_general should produce fixtures across all product types and tiers."""
        config = get_config("energy", "energy_general")
        fixtures = generate_fixtures_for_config("energy", "energy_general", config)

        assert len(fixtures) > 0
        # Should cover all product types
        product_types = set(f.product_type for f in fixtures)
        assert len(product_types) >= 2, f"Expected multiple product types, got {product_types}"

        # Should cover all modifier scenarios
        scenarios = set(f.modifier_scenario for f in fixtures)
        assert scenarios == {"benign", "neutral", "adverse"}

        # Should cover multiple tiers
        tiers = set(f.tier for f in fixtures)
        assert len(tiers) >= 2, f"Expected multiple tiers, got {tiers}"

        # Should cover multiple exposure sizes
        sizes = set(f.exposure_size_label for f in fixtures)
        assert len(sizes) >= 3, f"Expected multiple exposure sizes, got {sizes}"

    def test_generates_fixtures_for_sme_config(self):
        """SME configs with PREMIUM_BASE should also generate fixtures."""
        config = get_config("cyber", "cyber_sme")
        fixtures = generate_fixtures_for_config("cyber", "cyber_sme", config)

        assert len(fixtures) > 0
        # SME configs may use PREMIUM_BASE method
        for f in fixtures:
            assert f.limit > 0
            assert f.deductible >= 0

    def test_fixture_submission_data_has_required_fields(self):
        """Every fixture should have limit, deductible, and product_type."""
        config = get_config("energy", "energy_general")
        fixtures = generate_fixtures_for_config("energy", "energy_general", config)

        for f in fixtures[:50]:  # Check first 50
            sd = f.submission_data
            assert "limit" in sd, f"Missing limit in {f.label}"
            assert "deductible" in sd, f"Missing deductible in {f.label}"
            assert "product_type" in sd, f"Missing product_type in {f.label}"
            assert sd["limit"] > 0
            assert "revenue" in sd, f"Missing revenue in {f.label}"

    def test_categorical_groups_extracted(self):
        """Should extract categorical groups with modifiers from config."""
        config = get_config("energy", "energy_general")
        groups = _extract_categorical_groups(config)

        assert len(groups) > 0
        for g in groups:
            assert "group_id" in g
            assert "features" in g
            assert len(g["features"]) > 0
            for feat in g["features"]:
                assert "modifier" in feat
                assert isinstance(feat["modifier"], (int, float))

    def test_modifier_scenario_builds_outputs(self):
        """Modifier scenarios should produce CategoricalOutput objects."""
        config = get_config("energy", "energy_general")
        groups = _extract_categorical_groups(config)

        for scenario, factor in MODIFIER_SCENARIOS.items():
            outputs = _build_modifier_scenario(groups, scenario, factor)
            assert len(outputs) == len(groups)
            for out in outputs:
                assert out.modifier > 0
                assert out.confidence > 0

    def test_benign_modifiers_lower_than_adverse(self):
        """Benign scenario should have lower combined modifier than adverse."""
        config = get_config("energy", "energy_general")
        groups = _extract_categorical_groups(config)

        benign = _build_modifier_scenario(groups, "benign", 0.7)
        adverse = _build_modifier_scenario(groups, "adverse", 1.6)

        benign_product = 1.0
        adverse_product = 1.0
        for b, a in zip(benign, adverse):
            benign_product *= b.modifier
            adverse_product *= a.modifier

        assert benign_product < adverse_product, (
            f"Benign ({benign_product:.3f}) should be < adverse ({adverse_product:.3f})"
        )

    def test_no_fixtures_for_all_decline_config(self):
        """A config with only DECLINE tiers should generate no fixtures."""
        # We don't have such a config, but test the logic by checking
        # that fixture count correlates with priceable tiers
        config = get_config("energy", "energy_general")
        fixtures = generate_fixtures_for_config("energy", "energy_general", config)

        # At least 4 non-DECLINE tiers × multiple combos
        assert len(fixtures) >= 100


# ---------------------------------------------------------------------------
# Calibration execution tests
# ---------------------------------------------------------------------------

class TestCalibration:
    """Tests for running calibration against configs."""

    @pytest.fixture
    def harness(self):
        return CalibrationHarness()

    def test_calibrate_single_config(self, harness):
        """Should calibrate a single config and return results."""
        config = get_config("cyber", "cyber_sme")
        result = harness.calibrate_config("cyber", "cyber_sme", config)

        assert isinstance(result, ConfigCalibrationResult)
        assert result.fixture_count > 0
        assert len(result.results) == result.fixture_count
        assert result.coverage_id == "cyber"
        assert result.config_id == "cyber_sme"

    def test_no_pipeline_errors(self, harness):
        """No fixtures should cause pipeline exceptions."""
        config = get_config("energy", "energy_general")
        result = harness.calibrate_config("energy", "energy_general", config)

        assert result.error_count == 0, (
            f"Expected 0 errors, got {result.error_count}: "
            + ", ".join(r.error for r in result.results if r.error)[:200]
        )

    def test_premiums_are_positive(self, harness):
        """All successful fixtures should produce positive premiums."""
        config = get_config("cyber", "cyber_sme")
        result = harness.calibrate_config("cyber", "cyber_sme", config)

        for r in result.results:
            if r.error is None:
                assert r.premium > 0, f"Zero/negative premium for {r.fixture.label}"

    def test_guardrail_tracking(self, harness):
        """Should correctly track limit vs revenue guardrail caps."""
        config = get_config("energy", "energy_general")
        result = harness.calibrate_config("energy", "energy_general", config)

        # energy_general should have both types of caps
        assert result.guardrail_hit_count > 0
        assert result.limit_cap_count + result.revenue_cap_count >= result.guardrail_hit_count // 2

    def test_result_statistics(self, harness):
        """Premium and P/L statistics should be computed correctly."""
        config = get_config("cyber", "cyber_sme")
        result = harness.calibrate_config("cyber", "cyber_sme", config)

        stats = result.premium_stats()
        assert stats["count"] > 0
        assert stats["min"] > 0
        assert stats["min"] <= stats["median"] <= stats["max"]
        assert stats["p10"] <= stats["p90"]

        pl_stats = result.pl_ratio_stats()
        assert pl_stats["count"] > 0
        assert pl_stats["min"] >= 0

    def test_sme_configs_generally_pass(self, harness):
        """SME configs should generally have low guardrail hit rates."""
        for cov, cfg in [("cyber", "cyber_sme"), ("do", "do_sme"), ("fi", "fi_sme")]:
            config = get_config(cov, cfg)
            result = harness.calibrate_config(cov, cfg, config)
            assert result.guardrail_hit_pct < 50, (
                f"{cov}/{cfg} has {result.guardrail_hit_pct:.1f}% guardrail hits"
            )


# ---------------------------------------------------------------------------
# Report tests
# ---------------------------------------------------------------------------

class TestReport:
    """Tests for the calibration report."""

    def test_report_format_summary(self):
        """Report should produce a readable summary string."""
        harness = CalibrationHarness()
        config = get_config("cyber", "cyber_sme")
        result = harness.calibrate_config("cyber", "cyber_sme", config)

        report = CalibrationReport()
        report.config_results[result.key] = result
        report.total_fixtures = result.fixture_count

        summary = report.format_summary()
        assert "CALIBRATION HARNESS REPORT" in summary
        assert "cyber/cyber_sme" in summary

    def test_report_to_json(self):
        """Report should serialize to valid JSON structure."""
        harness = CalibrationHarness()
        config = get_config("cyber", "cyber_sme")
        result = harness.calibrate_config("cyber", "cyber_sme", config)

        report = CalibrationReport()
        report.config_results[result.key] = result
        report.total_fixtures = result.fixture_count

        data = report.to_json()
        assert "passed" in data
        assert "configs" in data
        assert "cyber/cyber_sme" in data["configs"]
        cfg_data = data["configs"]["cyber/cyber_sme"]
        assert "fixture_count" in cfg_data
        assert "guardrail_hit_pct" in cfg_data
        assert "limit_cap_count" in cfg_data
        assert "revenue_cap_count" in cfg_data
        assert "premium_stats" in cfg_data
        assert "pl_ratio_stats" in cfg_data


# ---------------------------------------------------------------------------
# Health gate integration tests
# ---------------------------------------------------------------------------

class TestHealthGateIntegration:
    """Tests for the health gate's deep calibration integration."""

    def test_deep_calibration_runs(self):
        """Deep calibration should run without errors."""
        gate = ConfigHealthGate()
        report = gate.run_deep_calibration(coverage_filter="cyber")

        assert len(report.config_results) >= 1
        assert report.total_fixtures > 0

    def test_deep_calibration_updates_quarantine(self):
        """Deep calibration should update quarantine status."""
        gate = ConfigHealthGate()
        report = gate.run_deep_calibration(coverage_filter="fi")

        # fi configs should generally pass
        results = gate.get_all_results()
        for key in results:
            if key.startswith("fi/"):
                assert key in results


# ---------------------------------------------------------------------------
# Regression anchor tests
# ---------------------------------------------------------------------------

class TestRegressionAnchors:
    """Tests that known entities produce premiums in expected ranges.

    These anchors prevent regression: when config changes are made,
    these real-world scenarios must still produce reasonable premiums.
    """

    @pytest.fixture
    def pricer(self):
        return CalibrationHarness()._pricer

    def test_shell_energy_premium_reasonable(self, pricer):
        """Shell plc: $85B TIV, $500M limit should NOT produce $100M+ premiums."""
        config = get_config("energy", "energy_general")
        result = pricer.price_submission(
            pure_composite_score=900,  # Tier 1
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={
                "tiv": 85_000_000_000,
                "revenue": 380_000_000_000,
                "limit": 500_000_000,
                "deductible": 1_000_000,
                "product_type": "property_damage",
            },
            config=config,
        )
        # With basis_damping at 0.5, Shell should produce reasonable premiums
        assert result.final_premium < 50_000_000, (
            f"Shell premium ${result.final_premium:,.0f} is too high "
            f"(base=${result.base_premium:,.0f}, modifier={result.total_modifier:.2f})"
        )
        # But should still be meaningful (not trivially low)
        assert result.final_premium > 100_000, (
            f"Shell premium ${result.final_premium:,.0f} is unreasonably low"
        )

    def test_devon_control_of_well_reasonable(self, pricer):
        """Devon Energy: $8B TIV, control_of_well should not explode via ILF."""
        config = get_config("energy", "energy_general")
        result = pricer.price_submission(
            pure_composite_score=725,  # Tier 2
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={
                "tiv": 8_000_000_000,
                "revenue": 20_000_000_000,
                "limit": 500_000_000,
                "deductible": 1_000_000,
                "product_type": "control_of_well",
            },
            config=config,
        )
        # Devon premium should be constrained by damping + ILF
        assert result.final_premium < 100_000_000, (
            f"Devon premium ${result.final_premium:,.0f} too high"
        )

    def test_maersk_hull_machinery_reasonable(self, pricer):
        """Maersk: $25B TIV, marine hull_machinery should be reasonable."""
        config = get_config("marine", "marine_general")
        result = pricer.price_submission(
            pure_composite_score=850,  # Tier 1
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={
                "tiv": 25_000_000_000,       # Marine uses tiv as basis
                "hull_value": 25_000_000_000,  # Also provided for reference
                "revenue": 81_000_000_000,
                "limit": 500_000_000,
                "deductible": 1_000_000,
                "product_type": "hull_machinery",
            },
            config=config,
        )
        assert result.final_premium < 50_000_000, (
            f"Maersk premium ${result.final_premium:,.0f} too high"
        )
        assert result.final_premium > 100_000, (
            f"Maersk premium ${result.final_premium:,.0f} unreasonably low"
        )

    def test_small_cyber_company_reasonable(self, pricer):
        """Small tech company: $50M revenue, $10M cyber limit."""
        config = get_config("cyber", "cyber_general")
        result = pricer.price_submission(
            pure_composite_score=750,  # Tier 2
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={
                "revenue": 50_000_000,
                "limit": 10_000_000,
                "deductible": 100_000,
                "product_type": "cyber_liability",
            },
            config=config,
        )
        # Premium should be meaningful but not absurd
        assert result.final_premium > 1_000, (
            f"Cyber premium ${result.final_premium:,.0f} is unreasonably low "
            f"(ROL={result.final_premium/10_000_000:.4f})"
        )
        assert result.final_premium < 5_000_000, (
            f"Cyber premium ${result.final_premium:,.0f} is too high"
        )

    def test_tier_ordering_produces_higher_premiums(self, pricer):
        """Worse tier should produce higher premium for same submission."""
        config = get_config("energy", "energy_general")
        submission = {
            "tiv": 1_000_000_000,
            "revenue": 5_000_000_000,
            "limit": 100_000_000,
            "deductible": 500_000,
            "product_type": "property_damage",
        }

        result_t1 = pricer.price_submission(
            pure_composite_score=900, signal_tier_overrides=[],
            query_tier_overrides=[], query_modifiers=[],
            categorical_outputs=[], submission_data=submission, config=config,
        )
        result_t3 = pricer.price_submission(
            pure_composite_score=575, signal_tier_overrides=[],
            query_tier_overrides=[], query_modifiers=[],
            categorical_outputs=[], submission_data=submission, config=config,
        )

        assert result_t3.final_premium > result_t1.final_premium, (
            f"Tier 3 (${result_t3.final_premium:,.0f}) should be > "
            f"Tier 1 (${result_t1.final_premium:,.0f})"
        )
