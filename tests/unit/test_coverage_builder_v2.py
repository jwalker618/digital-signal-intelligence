"""
Tests for v2.0 Coverage Builder

Validates that the builder generates configs matching the canonical
v2.0 schema (as used by coverages/cyber/config.yaml).
"""

import asyncio
import pytest
import yaml

from infrastructure.builder.coverage_builder import CoverageBuilder
from infrastructure.builder.validator import ConfigValidator, validate_coverage_config
from infrastructure.builder.signal_library import SignalLibrary
from infrastructure.builder.types import CoverageSpec, ValidationSeverity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cyber_spec():
    return CoverageSpec(
        name="Cyber Japan",
        description="Cyber liability model for the Japanese market",
        industry="technology",
        target_market="Japan mid-market",
        product_types=["cyber_liability", "network_security"],
        applicable_markets=["jp"],
        tier_strategy="conservative",
        min_signals=5,
        max_signals=40,
    )


@pytest.fixture
def casualty_spec():
    return CoverageSpec(
        name="Casualty",
        description="General casualty coverage for US market",
        industry="manufacturing",
        target_market="US mid-market",
        tier_strategy="standard",
        min_signals=5,
        max_signals=30,
    )


@pytest.fixture
def builder():
    return CoverageBuilder()


@pytest.fixture
def validator():
    return ConfigValidator()


# ---------------------------------------------------------------------------
# Builder output structure tests
# ---------------------------------------------------------------------------

class TestBuilderV2Output:
    """Test that builder generates v2.0 compliant YAML."""

    def test_generates_nested_structure(self, builder, cyber_spec):
        """Config must be nested as coverage_id → config_name → sections."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        assert result.success
        config = yaml.safe_load(result.config_yaml)
        assert "cyber_japan" in config
        assert "cyber_japan_general" in config["cyber_japan"]

    def test_has_all_required_sections(self, builder, cyber_spec):
        """Inner config must have all required v2.0 sections."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        inner = config["cyber_japan"]["cyber_japan_general"]

        required = [
            "metadata", "direct_queries", "signal_registry",
            "groups", "risk_tier_bands", "loss_tier_bands",
            "exposure", "limit_bandings", "pricing",
        ]
        for section in required:
            assert section in inner, f"Missing section: {section}"

    def test_metadata_has_required_fields(self, builder, cyber_spec):
        """Metadata section must have name, version, etc."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        metadata = config["cyber_japan"]["cyber_japan_general"]["metadata"]

        assert "name" in metadata
        assert "version" in metadata
        assert metadata["version"] == "2.0.0"
        assert "minimum_viable_input" in metadata
        assert isinstance(metadata["minimum_viable_input"], list)
        assert metadata["applicable_markets"] == ["jp"]

    def test_signal_registry_uses_three_layer_assessment(self, builder, cyber_spec):
        """Signals must use three_layer_assessment (not signal_groups + signal_features)."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        inner = config["cyber_japan"]["cyber_japan_general"]

        # Must NOT have old v1.5 keys
        assert "signal_groups" not in inner
        assert "signal_features" not in inner
        assert "tier_thresholds" not in inner
        assert "exposure_tier_bands" not in inner

        # Must have signal_registry as list
        registry = inner["signal_registry"]
        assert isinstance(registry, list)
        assert len(registry) > 0

        # Each signal must have three_layer_assessment with group_id
        for sig in registry:
            assert "id" in sig
            assert "three_layer_assessment" in sig or "categories" in sig
            if "three_layer_assessment" in sig:
                tla = sig["three_layer_assessment"]
                assert "group_id" in tla
                assert "risk" in tla

    def test_groups_has_categories_and_tla(self, builder, cyber_spec):
        """Groups must have categories and three_layer_assessment sub-sections."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        groups = config["cyber_japan"]["cyber_japan_general"]["groups"]

        assert "categories" in groups
        assert "three_layer_assessment" in groups

        # Categories are list of dicts with id, label, impact
        cats = groups["categories"]
        assert isinstance(cats, list)
        for cat in cats:
            assert "id" in cat
            assert "impact" in cat

        # TLA groups have risk/loss/exposure with weight
        tla = groups["three_layer_assessment"]
        assert isinstance(tla, list)
        for grp in tla:
            assert "id" in grp
            assert "risk" in grp
            assert "weight" in grp["risk"]

    def test_risk_tier_bands_have_interpretation(self, builder, cyber_spec):
        """Risk tier bands must use interpretation blocks with action."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        rtb = config["cyber_japan"]["cyber_japan_general"]["risk_tier_bands"]

        assert "bands" in rtb
        bands = rtb["bands"]
        assert len(bands) == 5

        for band in bands:
            assert "id" in band
            assert "label" in band
            assert "interpretation" in band
            interp = band["interpretation"]
            assert "bands" in interp
            assert "action" in interp
            assert "application" in interp
            assert interp["action"] in {"APPROVE", "REFER", "DECLINE"}

        # Must have DECLINE tier
        actions = {b["interpretation"]["action"] for b in bands}
        assert "DECLINE" in actions

    def test_loss_tier_bands_have_freq_sev_modifiers(self, builder, cyber_spec):
        """Loss tier bands must have frequency_modifier and severity_modifier."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        ltb = config["cyber_japan"]["cyber_japan_general"]["loss_tier_bands"]

        assert "bands" in ltb
        assert "constraints" in ltb
        assert "floor" in ltb["constraints"]
        assert "cap" in ltb["constraints"]

        for band in ltb["bands"]:
            app = band["interpretation"]["application"]
            assert "frequency_modifier" in app
            assert "severity_modifier" in app

    def test_exposure_has_size_and_complexity(self, builder, cyber_spec):
        """Exposure must have nested size and complexity with weights summing to 1.0."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        exposure = config["cyber_japan"]["cyber_japan_general"]["exposure"]

        assert "size" in exposure
        assert "complexity" in exposure
        assert "weight" in exposure["size"]
        assert "weight" in exposure["complexity"]
        assert "bands" in exposure["size"]
        assert "bands" in exposure["complexity"]

        # Weights sum to 1.0
        total = exposure["size"]["weight"] + exposure["complexity"]["weight"]
        assert abs(total - 1.0) < 0.01

        # Size bands have implied_thresholds
        for band in exposure["size"]["bands"]:
            app = band["interpretation"]["application"]
            assert "implied_thresholds" in app

    def test_direct_queries_use_query_condition(self, builder, cyber_spec):
        """Direct queries must use query_condition (not bands)."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        queries = config["cyber_japan"]["cyber_japan_general"]["direct_queries"]

        assert isinstance(queries, list)
        assert len(queries) >= 2

        for q in queries:
            assert "id" in q
            assert "question" in q
            assert "query_condition" in q
            assert "bands" not in q  # Must NOT use old v1.5 key

    def test_pricing_section_present(self, builder, cyber_spec):
        """Config must include pricing with ILF curve."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        pricing = config["cyber_japan"]["cyber_japan_general"]["pricing"]

        assert "ilf_curve" in pricing
        assert "deductible_credits" in pricing
        assert "taxes_fees_rate" in pricing


# ---------------------------------------------------------------------------
# Score conditions constraint tests
# ---------------------------------------------------------------------------

class TestScoreConditionConstraints:
    """Verify score_conditions follow DSI rules."""

    def test_score_conditions_no_decline(self, builder, cyber_spec):
        """score_conditions must not use DECLINE (tier-level only)."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        inner = config["cyber_japan"]["cyber_japan_general"]

        # Check signal_registry
        for sig in inner["signal_registry"]:
            tla = sig.get("three_layer_assessment", {})
            risk = tla.get("risk", {})
            for cond in risk.get("score_conditions", []):
                assert cond["action"] != "DECLINE", \
                    f"DECLINE in score_conditions for signal {sig['id']}"

        # Check groups
        for grp in inner["groups"].get("three_layer_assessment", []):
            for dim in ("risk", "loss", "exposure"):
                dim_data = grp.get(dim, {})
                for cond in dim_data.get("score_conditions", []):
                    assert cond["action"] != "DECLINE", \
                        f"DECLINE in score_conditions for group {grp['id']}.{dim}"

    def test_score_conditions_valid_actions(self, builder, cyber_spec):
        """score_conditions actions must be FLAG | MODIFIER | REFER."""
        valid_actions = {"FLAG", "MODIFIER", "REFER"}
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        inner = config["cyber_japan"]["cyber_japan_general"]

        for sig in inner["signal_registry"]:
            tla = sig.get("three_layer_assessment", {})
            risk = tla.get("risk", {})
            for cond in risk.get("score_conditions", []):
                assert cond["action"] in valid_actions

    def test_decline_only_in_tier_bands(self, builder, cyber_spec):
        """DECLINE should only appear in risk_tier_bands."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        config = yaml.safe_load(result.config_yaml)
        inner = config["cyber_japan"]["cyber_japan_general"]

        # DECLINE should be in risk_tier_bands
        rtb_actions = {
            b["interpretation"]["action"]
            for b in inner["risk_tier_bands"]["bands"]
        }
        assert "DECLINE" in rtb_actions


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

class TestV2Validator:
    """Test the validator against v2.0 schema."""

    def test_validates_builder_output(self, builder, validator, cyber_spec):
        """Builder output must pass its own validator."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(cyber_spec)
        )
        validation = validator.validate_yaml(result.config_yaml)
        errors = [i for i in validation.issues if i.severity == ValidationSeverity.ERROR]
        assert validation.valid, f"Validation errors: {[e.message for e in errors]}"

    def test_validates_existing_cyber_config(self, validator):
        """Existing cyber config must pass validation."""
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "coverages" / "cyber" / "config.yaml"
        if not config_path.exists():
            pytest.skip("Cyber config not found")
        result = validator.validate_file(str(config_path))
        errors = [i for i in result.issues if i.severity == ValidationSeverity.ERROR]
        assert result.valid, f"Validation errors: {[e.message for e in errors]}"

    def test_rejects_v1_flat_structure(self, validator):
        """Validator should reject v1.0 flat structure."""
        v1_yaml = """
coverage:
  id: test
  name: Test Coverage
signal_groups:
  group_a:
    weight: 1.0
    signals:
      - signal_1
"""
        result = validator.validate_yaml(v1_yaml)
        assert not result.valid

    def test_rejects_decline_in_score_conditions(self, validator):
        """Validator should reject DECLINE in score_conditions."""
        config = """
test_coverage:
  test_coverage_general:
    metadata:
      name: Test
      version: "2.0.0"
    signal_registry:
      - id: test_signal
        three_layer_assessment:
          group_id: test_group
          risk:
            correlation_direction: positive
            weight: 0.5
            score_conditions:
              - threshold: 30
                comparison: "<="
                action: "DECLINE"
                note: "This should fail"
    groups:
      categories: []
      three_layer_assessment:
        - id: test_group
          risk:
            weight: 1.0
          loss:
            weight: 1.0
          exposure:
            weight: 1.0
    risk_tier_bands:
      bands:
        - id: 1
          label: PREFERRED
          interpretation:
            bands: {min: 500, max: 1000}
            action: APPROVE
            application: {method: PREMIUM_BASE, applied: 5000}
        - id: 2
          label: DECLINE
          interpretation:
            bands: {min: 0, max: 499}
            action: DECLINE
            application: {method: PREMIUM_BASE, applied: 50000}
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 50, max: 100}
            application: {frequency_modifier: 1.0, severity_modifier: 1.0}
      constraints: {floor: 0.5, cap: 1.5}
    exposure:
      size:
        weight: 0.6
        bands:
          - id: 1
            label: SMALL
            interpretation:
              bands: {min: 0, max: 50}
              application: {method: MODIFIER, applied: 1.0}
      complexity:
        weight: 0.4
        bands:
          - id: 1
            label: SIMPLE
            interpretation:
              bands: {min: 0, max: 50}
              application: {method: MODIFIER, applied: 1.0}
"""
        result = validator.validate_yaml(config)
        # Should have error for DECLINE in score_conditions
        decline_errors = [
            i for i in result.issues
            if "DECLINE" in i.message and i.severity == ValidationSeverity.ERROR
        ]
        assert len(decline_errors) > 0, "Should reject DECLINE in score_conditions"

    def test_validates_direct_queries_use_query_condition(self, validator):
        """Should error when direct_queries use 'bands' instead of 'query_condition'."""
        config = """
test_cov:
  test_cov_general:
    metadata:
      name: Test
      version: "2.0.0"
    direct_queries:
      - id: test_q
        question: "Test?"
        bands:
          - {return: true, action: "FLAG"}
    signal_registry:
      - id: test_sig
        three_layer_assessment:
          group_id: tg
          risk:
            correlation_direction: positive
            weight: 1.0
    groups:
      three_layer_assessment:
        - id: tg
          risk: {weight: 1.0}
          loss: {weight: 1.0}
          exposure: {weight: 1.0}
    risk_tier_bands:
      bands:
        - id: 1
          label: DECLINE
          interpretation:
            bands: {min: 0, max: 1000}
            action: DECLINE
            application: {method: PREMIUM_BASE, applied: 50000}
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application: {frequency_modifier: 1.0, severity_modifier: 1.0}
      constraints: {floor: 0.5, cap: 1.5}
    exposure:
      size:
        weight: 0.6
        bands:
          - id: 1
            label: S
            interpretation:
              bands: {min: 0, max: 100}
              application: {method: MODIFIER, applied: 1.0}
      complexity:
        weight: 0.4
        bands:
          - id: 1
            label: S
            interpretation:
              bands: {min: 0, max: 100}
              application: {method: MODIFIER, applied: 1.0}
"""
        result = validator.validate_yaml(config)
        bands_errors = [
            i for i in result.issues
            if "query_condition" in i.message and "bands" in i.message
        ]
        assert len(bands_errors) > 0


# ---------------------------------------------------------------------------
# Different industry tests
# ---------------------------------------------------------------------------

class TestMultipleIndustries:
    """Test builder works for different industries."""

    def test_casualty_coverage(self, builder, casualty_spec, validator):
        """Casualty coverage should build and validate."""
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(casualty_spec)
        )
        assert result.success
        validation = validator.validate_yaml(result.config_yaml)
        errors = [i for i in validation.issues if i.severity == ValidationSeverity.ERROR]
        assert validation.valid, f"Errors: {[e.message for e in errors]}"

    def test_healthcare_coverage(self, builder, validator):
        """Healthcare coverage should include PHI query."""
        spec = CoverageSpec(
            name="Healthcare Professional",
            description="Healthcare professional liability",
            industry="healthcare",
            target_market="US enterprise",
            min_signals=5,
        )
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(spec)
        )
        assert result.success
        config = yaml.safe_load(result.config_yaml)
        inner = list(list(config.values())[0].values())[0]
        query_ids = [q["id"] for q in inner["direct_queries"]]
        assert "phi_handler" in query_ids

    def test_financial_coverage(self, builder, validator):
        """Financial coverage should include regulatory query."""
        spec = CoverageSpec(
            name="Financial Institutions",
            description="FI coverage",
            industry="financial_services",
            target_market="Global enterprise",
            min_signals=5,
        )
        result = asyncio.get_event_loop().run_until_complete(
            builder.create_coverage(spec)
        )
        assert result.success
        config = yaml.safe_load(result.config_yaml)
        inner = list(list(config.values())[0].values())[0]
        query_ids = [q["id"] for q in inner["direct_queries"]]
        assert "regulatory_actions" in query_ids


# ---------------------------------------------------------------------------
# Signal library tests
# ---------------------------------------------------------------------------

class TestSignalLibrary:
    """Test signal library integration."""

    def test_recommendations_have_proxy_tier(self):
        lib = SignalLibrary()
        recs = lib.get_signals_for_industry("technology")
        assert len(recs) > 0
        for rec in recs:
            assert rec.proxy_tier in ("DIRECT_OBSERVABLE", "INFERRED_PROXY", "COHORT_INFERENCE")

    def test_industry_profiles_available(self):
        lib = SignalLibrary()
        for industry in ["technology", "financial_services", "healthcare", "manufacturing", "retail"]:
            profile = lib.get_industry_profile(industry)
            assert profile is not None, f"Missing profile for {industry}"

    def test_has_signal_check(self):
        lib = SignalLibrary()
        assert lib.has_signal("security_headers")
        assert lib.has_signal("tls_configuration")
        assert not lib.has_signal("nonexistent_signal_xyz")
