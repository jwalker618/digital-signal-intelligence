"""
Tests for DSI Coverage Builder (Phase 13)

Tests for LLM-assisted coverage building.
"""

import asyncio

import pytest
import yaml

from infrastructure.builder import (
    # Types
    CoverageSpec,
    CoverageBuildResult,
    IndustryAnalysis,
    SignalRecommendation,
    SignalSelection,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    BuildStage,
    # Components
    CoverageBuilder,
    SignalLibrary,
    ConfigValidator,
    validate_coverage_config,
)


# =============================================================================
# COVERAGE SPEC TESTS
# =============================================================================

class TestCoverageSpec:
    """Tests for CoverageSpec."""

    def test_create_basic_spec(self):
        """Should create basic coverage spec."""
        spec = CoverageSpec(
            name="Renewable Energy",
            description="Coverage for renewable energy companies",
            industry="energy",
            target_market="US mid-market",
        )

        assert spec.name == "Renewable Energy"
        assert spec.industry == "energy"
        assert spec.locale == "US"
        assert spec.tier_strategy == "standard"

    def test_create_full_spec(self):
        """Should create spec with all options."""
        spec = CoverageSpec(
            name="FinTech",
            description="Financial technology coverage",
            industry="financial_services",
            target_market="Global enterprise",
            risk_factors=["cyber_risk", "regulatory_risk"],
            example_companies=["Stripe", "Square"],
            base_coverage="fi",
            tier_strategy="conservative",
            min_signals=20,
            max_signals=50,
        )

        assert len(spec.risk_factors) == 2
        assert len(spec.example_companies) == 2
        assert spec.base_coverage == "fi"


# =============================================================================
# SIGNAL LIBRARY TESTS
# =============================================================================

class TestSignalLibrary:
    """Tests for SignalLibrary."""

    @pytest.fixture
    def library(self):
        return SignalLibrary()

    def test_get_signal_groups(self, library):
        """Should return all signal groups."""
        groups = library.get_signal_groups()

        assert len(groups) > 0
        assert any(g.group_id == "technical_infrastructure" for g in groups)
        assert any(g.group_id == "financial_health" for g in groups)

    def test_get_signals_for_financial_industry(self, library):
        """Should return relevant signals for financial industry."""
        recommendations = library.get_signals_for_industry("financial_services")

        assert len(recommendations) > 0
        # Should prioritize regulatory and financial signals
        group_ids = [r.group_id for r in recommendations[:10]]
        assert "regulatory_compliance" in group_ids or "financial_health" in group_ids

    def test_get_signals_for_technology_industry(self, library):
        """Should return relevant signals for technology."""
        recommendations = library.get_signals_for_industry("technology")

        assert len(recommendations) > 0
        # Should prioritize technical and cyber signals
        group_ids = [r.group_id for r in recommendations[:10]]
        assert "technical_infrastructure" in group_ids or "cyber_security" in group_ids

    def test_get_industry_profile(self, library):
        """Should return industry profile."""
        profile = library.get_industry_profile("financial_services")

        assert profile is not None
        assert profile.industry == "financial_services"
        assert len(profile.primary_groups) > 0
        assert len(profile.risk_focus) > 0

    def test_has_signal(self, library):
        """Should check signal existence."""
        assert library.has_signal("security_headers") is True
        assert library.has_signal("nonexistent_signal") is False

    def test_get_signal_template(self, library):
        """Should return signal template."""
        template = library.get_signal_template("security_headers")

        assert template.signal_id == "security_headers"
        assert "extract_security_headers" in template.extractor_template

    def test_add_custom_signal(self, library):
        """Should add custom signal."""
        library.add_custom_signal(
            signal_id="custom_signal",
            name="Custom Signal",
            group_id="custom_group",
        )

        assert library.has_signal("custom_signal") is True


# =============================================================================
# CONFIG VALIDATOR TESTS
# =============================================================================

class TestConfigValidator:
    """Tests for ConfigValidator."""

    @pytest.fixture
    def validator(self):
        return ConfigValidator()

    def test_validate_valid_config(self, validator):
        """Should validate correct configuration."""
        config = """
test_coverage:
  test_coverage_general:
    metadata:
      name: Test Coverage
      version: "1.0"
    signal_registry:
      - id: security_headers
        three_layer_assessment:
          group_id: technical
      - id: tls_config
        three_layer_assessment:
          group_id: technical
      - id: revenue_growth
        three_layer_assessment:
          group_id: financial
    groups:
      three_layer_assessment:
        - id: technical
          risk:
            weight: 0.5
        - id: financial
          risk:
            weight: 0.5
    risk_tier_bands:
      bands:
        - tier: 1
          interpretation:
            bands: {min: 780, max: 850}
            action: APPROVE
            application: {applied: true}
        - tier: 2
          interpretation:
            bands: {min: 680, max: 779}
            action: APPROVE
            application: {applied: true}
        - tier: 3
          interpretation:
            bands: {min: 580, max: 679}
            action: REFER
            application: {applied: true}
        - tier: 4
          interpretation:
            bands: {min: 480, max: 579}
            action: REFER
            application: {applied: true}
        - tier: 5
          interpretation:
            bands: {min: 0, max: 479}
            action: DECLINE
            application: {applied: true}
    loss_tier_bands:
      bands:
        - tier: 1
          label: low
          interpretation:
            application:
              frequency_modifier: 0.8
              severity_modifier: 0.9
        - tier: 2
          label: high
          interpretation:
            application:
              frequency_modifier: 1.2
              severity_modifier: 1.1
      constraints:
        floor: 0.5
        cap: 2.0
    exposure:
      size:
        weight: 0.5
        bands: []
      complexity:
        weight: 0.5
        bands: []
"""

        result = validator.validate_yaml(config)

        assert result.valid is True
        assert result.error_count == 0

    def test_validate_missing_required_keys(self, validator):
        """Should detect missing required keys."""
        config = """
test:
  test_general:
    metadata:
      name: Test
      version: "1.0"
"""

        result = validator.validate_yaml(config)

        assert result.valid is False
        assert result.error_count > 0
        assert any("signal_registry" in i.message for i in result.issues)

    def test_validate_invalid_yaml(self, validator):
        """Should detect invalid YAML."""
        config = "invalid: yaml: syntax: :"

        result = validator.validate_yaml(config)

        assert result.valid is False
        assert any("syntax" in i.category for i in result.issues)

    def test_validate_weight_sum(self, validator):
        """Should check weight sums."""
        config = """
test:
  test_general:
    metadata:
      name: Test
      version: "1.0"
    signal_registry:
      - signal_id: a
        three_layer_assessment:
          group_id: group1
      - signal_id: b
        three_layer_assessment:
          group_id: group2
    groups:
      three_layer_assessment:
        - id: group1
          risk:
            weight: 0.3
        - id: group2
          risk:
            weight: 0.3
    risk_tier_bands:
      bands:
        - tier: 1
          min_score: 700
          action: APPROVE
    loss_tier_bands:
      bands:
        - tier: 1
          min_score: 0
    exposure:
      size:
        weight: 0.5
      complexity:
        weight: 0.5
"""

        result = validator.validate_yaml(config)

        # Should warn about weights not summing to 1.0
        weight_issues = [i for i in result.issues if "weight" in i.message.lower()]
        assert len(weight_issues) > 0

    def test_validate_tier_ordering(self, validator):
        """Should detect tier band issues."""
        config = """
test:
  test_general:
    metadata:
      name: Test
      version: "1.0"
    signal_registry:
      - signal_id: a
        three_layer_assessment:
          group_id: group1
    groups:
      three_layer_assessment:
        - id: group1
          risk:
            weight: 1.0
    risk_tier_bands:
      bands:
        - tier: 1
          interpretation:
            bands:
              min: 700
              max: 850
            action: APPROVE
            application:
              applied: true
        - tier: 2
          interpretation:
            bands:
              min: 500
              max: 900
            action: APPROVE
            application:
              applied: true
    loss_tier_bands:
      bands:
        - tier: 1
          min_score: 0
    exposure:
      size:
        weight: 0.5
      complexity:
        weight: 0.5
"""

        result = validator.validate_yaml(config)

        # Should warn about tier band overlap
        tier_issues = [i for i in result.issues if "tier" in i.category.lower()]
        assert any("overlap" in str(i.message).lower() or "band" in str(i.message).lower() for i in tier_issues)


# =============================================================================
# COVERAGE BUILDER TESTS
# =============================================================================

class TestCoverageBuilder:
    """Tests for CoverageBuilder."""

    @pytest.fixture
    def builder(self):
        return CoverageBuilder()

    def test_analyze_industry(self, builder):
        """Should analyze industry."""
        analysis = asyncio.run(builder.analyze_industry(
            "financial_services",
            examples=["JPMorgan", "Goldman Sachs"],
        ))

        assert analysis.industry == "financial_services"
        assert len(analysis.key_risk_factors) > 0
        assert len(analysis.relevant_categories) > 0

    def test_select_signals(self, builder):
        """Should select signals based on analysis."""
        analysis = IndustryAnalysis(
            industry="technology",
            key_risk_factors=["cyber_risk"],
            relevant_categories=["technical_infrastructure", "cyber_security"],
            specific_considerations=[],
            confidence=0.9,
        )

        spec = CoverageSpec(
            name="Tech",
            description="Tech coverage",
            industry="technology",
            target_market="US",
        )

        selections = asyncio.run(builder.select_signals(analysis, spec))

        assert len(selections) > 0
        # Weights should sum to ~1.0 within each group
        from collections import defaultdict
        groups = defaultdict(float)
        for s in selections:
            groups[s.group_id] += s.weight
        for group_id, total in groups.items():
            assert 0.99 <= total <= 1.01, f"Group {group_id} weights sum to {total}"

    def test_generate_config(self, builder):
        """Should generate valid config."""
        spec = CoverageSpec(
            name="Test Coverage",
            description="A test coverage",
            industry="technology",
            target_market="US",
        )

        selections = [
            SignalSelection(
                signal_id="security_headers",
                signal_name="Security Headers",
                group_id="technical",
                weight=0.5,
            ),
            SignalSelection(
                signal_id="revenue_growth",
                signal_name="Revenue Growth",
                group_id="financial",
                weight=0.5,
            ),
        ]

        config_yaml = asyncio.run(builder.generate_config(spec, selections))

        # Should be valid YAML
        config = yaml.safe_load(config_yaml)
        # v2.2 config uses coverage_id as top-level key
        assert "test_coverage" in config
        # Inner config has signal_registry
        inner = config["test_coverage"]["test_coverage_general"]
        assert "signal_registry" in inner

    def test_validate_config(self, builder):
        """Should validate configuration."""
        valid_config = """
test:
  test_general:
    metadata:
      name: Test
      version: "1.0"
    signal_registry:
      - id: a
        three_layer_assessment:
          group_id: group1
      - id: b
        three_layer_assessment:
          group_id: group1
      - id: c
        three_layer_assessment:
          group_id: group1
    groups:
      three_layer_assessment:
        - id: group1
          risk:
            weight: 1.0
    risk_tier_bands:
      bands:
        - tier: 1
          interpretation:
            bands: {min: 700, max: 850}
            action: APPROVE
            application: {applied: true}
        - tier: 2
          interpretation:
            bands: {min: 600, max: 699}
            action: APPROVE
            application: {applied: true}
        - tier: 3
          interpretation:
            bands: {min: 500, max: 599}
            action: REFER
            application: {applied: true}
        - tier: 4
          interpretation:
            bands: {min: 400, max: 499}
            action: REFER
            application: {applied: true}
        - tier: 5
          interpretation:
            bands: {min: 0, max: 399}
            action: DECLINE
            application: {applied: true}
    loss_tier_bands:
      bands:
        - tier: 1
          label: low
          interpretation:
            application:
              frequency_modifier: 0.8
              severity_modifier: 0.9
      constraints:
        floor: 0.5
        cap: 2.0
    exposure:
      size:
        weight: 0.5
        bands: []
      complexity:
        weight: 0.5
        bands: []
"""

        result = asyncio.run(builder.validate_config(valid_config))

        assert result.valid is True

    def test_create_coverage_full(self, builder):
        """Should create complete coverage."""
        spec = CoverageSpec(
            name="Test Energy",
            description="Coverage for energy sector",
            industry="energy",
            target_market="US mid-market",
            tier_strategy="standard",
        )

        result = asyncio.run(builder.create_coverage(spec))

        assert result.coverage_name == "Test Energy"
        assert len(result.config_yaml) > 0
        # Should generate some files
        assert isinstance(result.generated_files, dict)

    def test_progress_callbacks(self, builder):
        """Should trigger progress callbacks."""
        progress_updates = []

        def on_progress(progress):
            progress_updates.append(progress.stage)

        builder.on_progress(on_progress)

        # Manually trigger updates
        builder._update_progress(BuildStage.ANALYSIS, 0.5, "Analyzing")
        builder._update_progress(BuildStage.COMPLETE, 1.0, "Done")

        assert BuildStage.ANALYSIS in progress_updates
        assert BuildStage.COMPLETE in progress_updates


# =============================================================================
# BUILD RESULT TESTS
# =============================================================================

class TestCoverageBuildResult:
    """Tests for CoverageBuildResult."""

    def test_needs_review(self):
        """Should determine if review needed."""
        result_no_review = CoverageBuildResult(
            success=True,
            coverage_name="Test",
            config_yaml="config",
            config_path="path",
            human_review_required=[],
        )

        result_with_review = CoverageBuildResult(
            success=True,
            coverage_name="Test",
            config_yaml="config",
            config_path="path",
            human_review_required=["Check signals"],
        )

        assert result_no_review.needs_review is False
        assert result_with_review.needs_review is True


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================

class TestValidationResult:
    """Tests for ValidationResult."""

    def test_error_count(self):
        """Should count errors."""
        result = ValidationResult(
            valid=False,
            issues=[
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="test",
                    message="Error 1",
                ),
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="test",
                    message="Warning 1",
                ),
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="test",
                    message="Error 2",
                ),
            ],
        )

        assert result.error_count == 2
        assert result.warning_count == 1


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_validate_coverage_config(self):
        """Should validate using convenience function."""
        config = """
coverage:
  id: test
  name: Test
  description: Test

signal_groups:
  group:
    weight: 1.0
    signals: [a]

scoring:
  composite_method: weighted

tiers:
  1:
    min_score: 700
"""

        result = validate_coverage_config(config)

        assert isinstance(result, ValidationResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
