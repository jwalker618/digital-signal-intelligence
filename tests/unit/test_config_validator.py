"""
Tests for infrastructure/validation/config_validator.py

Validates the ModelConfigValidator against v2.0 config structures.
"""

import pytest
import tempfile
import importlib.util
from pathlib import Path

import sys

# Direct import to avoid FastAPI dependency in infrastructure/__init__.py
_validator_path = Path(__file__).parent.parent.parent / "infrastructure" / "validation" / "config_validator.py"
_spec = importlib.util.spec_from_file_location("config_validator", _validator_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ModelConfigValidator = _mod.ModelConfigValidator
ValidationReport = _mod.ValidationReport
ValidationIssue = _mod.ValidationIssue
Severity = _mod.Severity
VALID_SCORE_CONDITION_ACTIONS = _mod.VALID_SCORE_CONDITION_ACTIONS


@pytest.fixture
def validator():
    return ModelConfigValidator()


@pytest.fixture
def valid_config_yaml():
    """A minimal valid v2.0 config."""
    return """
aerospace:
  aerospace_general:
    metadata:
      name: "Aerospace General"
      version: "2.0"

    signal_groups:
      - id: fleet_quality
        weight: 0.40
        score_conditions:
          - threshold: 20
            comparison: "<="
            action: MODIFIER
            applied: 0.90
      - id: regulatory_compliance
        weight: 0.35
        score_conditions:
          - threshold: 80
            comparison: ">="
            action: FLAG
            note: "High regulatory score"
      - id: financial_stability
        weight: 0.25
        score_conditions:
          - threshold: 95
            comparison: ">="
            action: REFER
            override: 4

    signal_features:
      fleet_quality:
        - id: fleet_age
          weight: 0.50
          inference_utility_function: infer_fleet_age
        - id: maintenance_record
          weight: 0.50
          inference_utility_function: infer_maintenance

      regulatory_compliance:
        - id: faa_compliance
          weight: 1.0
          inference_utility_function: infer_faa_compliance

      financial_stability:
        - id: credit_rating
          weight: 1.0
          inference_utility_function: infer_credit

    tier_thresholds:
      tiers:
        - id: 1
          application:
            method: PREMIUM_BASE
            applied: 25000
        - id: 2
          application:
            method: PREMIUM_BASE
            applied: 35000

    loss_tier_bands:
      bands:
        - id: 1
          label: VERY_LOW
          interpretation:
            bands: {min: 80, max: 100}
            application:
              frequency_modifier: 0.70
              severity_modifier: 0.80
      constraints:
        floor: 0.55
        cap: 1.60

    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 50000000}
            application:
              method: MODIFIER
              applied: 0.85
"""


@pytest.fixture
def config_file(valid_config_yaml, tmp_path):
    """Write valid config to temp file."""
    f = tmp_path / "config.yaml"
    f.write_text(valid_config_yaml)
    return f


class TestValidationReport:
    def test_report_creation(self):
        report = ValidationReport(coverage="test", valid=True)
        assert report.valid is True
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_add_error(self):
        report = ValidationReport(coverage="test", valid=True)
        report.add(ValidationIssue(Severity.ERROR, "test", "error msg"))
        assert report.valid is False
        assert report.error_count == 1

    def test_add_warning(self):
        report = ValidationReport(coverage="test", valid=True)
        report.add(ValidationIssue(Severity.WARNING, "test", "warning msg"))
        assert report.valid is True
        assert report.warning_count == 1

    def test_add_info(self):
        report = ValidationReport(coverage="test", valid=True)
        report.add(ValidationIssue(Severity.INFO, "test", "info msg"))
        assert report.valid is True
        assert report.info_count == 1

    def test_summary(self):
        report = ValidationReport(coverage="test", valid=True)
        report.add(ValidationIssue(Severity.ERROR, "test", "err"))
        summary = report.summary()
        assert "FAIL" in summary
        assert "1 errors" in summary


class TestModelConfigValidator:
    def test_valid_config(self, validator, config_file):
        report = validator.validate_file(config_file)
        assert report.valid is True
        assert report.error_count == 0

    def test_invalid_yaml(self, validator, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("{{invalid yaml")
        report = validator.validate_file(f)
        assert report.valid is False
        assert report.error_count > 0

    def test_non_dict_root(self, validator, tmp_path):
        f = tmp_path / "list.yaml"
        f.write_text("- item1\n- item2\n")
        report = validator.validate_file(f)
        assert report.valid is False

    def test_missing_metadata_warning(self, validator, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("""
coverage:
  config:
    signal_groups:
      - id: g1
        weight: 1.0
        score_conditions:
          - threshold: 50
            comparison: ">="
            action: FLAG
            note: test
    tier_thresholds:
      tiers:
        - id: 1
          application:
            method: PREMIUM_BASE
            applied: 10000
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application:
              frequency_modifier: 1.0
              severity_modifier: 1.0
      constraints:
        floor: 0.5
        cap: 1.5
    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 100}
            application:
              method: MODIFIER
              applied: 1.0
""")
        report = validator.validate_file(f)
        assert report.warning_count >= 1  # Missing metadata

    def test_boolean_score_conditions_error(self, validator, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("""
coverage:
  config:
    signal_groups:
      - id: g1
        weight: 1.0
        score_conditions: true
    tier_thresholds:
      tiers:
        - id: 1
          application:
            method: PREMIUM_BASE
            applied: 10000
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application:
              frequency_modifier: 1.0
              severity_modifier: 1.0
      constraints:
        floor: 0.5
        cap: 1.5
    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 100}
            application:
              method: MODIFIER
              applied: 1.0
""")
        report = validator.validate_file(f)
        assert report.error_count >= 1

    def test_decline_in_score_conditions_error(self, validator, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("""
coverage:
  config:
    signal_groups:
      - id: g1
        weight: 1.0
        score_conditions:
          - threshold: 50
            comparison: ">="
            action: DECLINE
    tier_thresholds:
      tiers:
        - id: 1
          application:
            method: PREMIUM_BASE
            applied: 10000
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application:
              frequency_modifier: 1.0
              severity_modifier: 1.0
      constraints:
        floor: 0.5
        cap: 1.5
    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 100}
            application:
              method: MODIFIER
              applied: 1.0
""")
        report = validator.validate_file(f)
        # Should flag DECLINE as invalid action AND in no-decline check
        errors = [i for i in report.issues if i.severity == Severity.ERROR]
        assert len(errors) >= 1

    def test_weight_sum_error(self, validator, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("""
coverage:
  config:
    metadata:
      name: test
      version: "2.0"
    signal_groups:
      - id: g1
        weight: 0.30
        score_conditions:
          - threshold: 50
            comparison: ">="
            action: FLAG
            note: test
      - id: g2
        weight: 0.30
        score_conditions:
          - threshold: 50
            comparison: ">="
            action: FLAG
            note: test
    tier_thresholds:
      tiers:
        - id: 1
          application:
            method: PREMIUM_BASE
            applied: 10000
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application:
              frequency_modifier: 1.0
              severity_modifier: 1.0
      constraints:
        floor: 0.5
        cap: 1.5
    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 100}
            application:
              method: MODIFIER
              applied: 1.0
""")
        report = validator.validate_file(f)
        weight_errors = [
            i for i in report.issues
            if i.category == "weights" and i.severity == Severity.ERROR
        ]
        assert len(weight_errors) >= 1

    def test_v1_tier_format_error(self, validator, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("""
coverage:
  config:
    signal_groups:
      - id: g1
        weight: 1.0
        score_conditions:
          - threshold: 50
            comparison: ">="
            action: FLAG
            note: test
    tier_thresholds:
      tiers:
        - id: 1
          premium_generation_method: rate_based
          premium: 25000
    loss_tier_bands:
      bands:
        - id: 1
          label: LOW
          interpretation:
            bands: {min: 0, max: 100}
            application:
              frequency_modifier: 1.0
              severity_modifier: 1.0
      constraints:
        floor: 0.5
        cap: 1.5
    exposure_tier_bands:
      bands:
        - id: 1
          label: SMALL
          interpretation:
            bands: {min: 0, max: 100}
            application:
              method: MODIFIER
              applied: 1.0
""")
        report = validator.validate_file(f)
        tier_errors = [
            i for i in report.issues
            if i.category == "tiers" and i.severity == Severity.ERROR
        ]
        assert len(tier_errors) >= 1

    def test_valid_actions_constant(self):
        assert "FLAG" in VALID_SCORE_CONDITION_ACTIONS
        assert "MODIFIER" in VALID_SCORE_CONDITION_ACTIONS
        assert "REFER" in VALID_SCORE_CONDITION_ACTIONS
        assert "DECLINE" not in VALID_SCORE_CONDITION_ACTIONS


class TestValidateAllConfigs:
    """Test validation against actual coverage configs."""

    def test_all_coverages_valid(self, validator):
        coverages_dir = Path(__file__).parent.parent.parent / "coverages"
        if not coverages_dir.exists():
            pytest.skip("coverages directory not found")

        reports = validator.validate_all(coverages_dir)
        assert len(reports) > 0

        for report in reports:
            assert report.valid is True, (
                f"{report.coverage} failed: "
                + "; ".join(
                    i.message for i in report.issues
                    if i.severity == Severity.ERROR
                )
            )
