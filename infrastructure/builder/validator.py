"""
DSI Configuration Validator (Phase 13)

Validates coverage configurations for correctness.
"""

import logging
import yaml
from typing import Any, Dict, List, Optional

from .types import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


logger = logging.getLogger("dsi.builder.validator")


class ConfigValidator:
    """
    Validates coverage configurations.

    Checks:
    - Schema compliance
    - Weight verification
    - Tier coverage
    - Signal availability
    - Logical consistency
    """

    # Required top-level keys
    REQUIRED_KEYS = ["coverage", "signal_groups", "scoring", "tiers"]

    # Required coverage fields
    REQUIRED_COVERAGE_FIELDS = ["id", "name", "description"]

    def __init__(self, signal_library=None):
        """Initialize ConfigValidator."""
        self.signal_library = signal_library

    def validate_yaml(self, yaml_content: str) -> ValidationResult:
        """
        Validate YAML configuration string.

        Args:
            yaml_content: YAML configuration

        Returns:
            ValidationResult with issues
        """
        issues: List[ValidationIssue] = []
        warnings: List[str] = []

        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="syntax",
                    message=f"Invalid YAML syntax: {e}",
                )],
            )

        if not isinstance(config, dict):
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message="Configuration must be a dictionary",
                )],
            )

        # Validate structure
        issues.extend(self._validate_structure(config))

        # Validate coverage section
        if "coverage" in config:
            issues.extend(self._validate_coverage_section(config["coverage"]))

        # Validate signal groups
        if "signal_groups" in config:
            issues.extend(self._validate_signal_groups(config["signal_groups"]))

        # Validate tiers
        if "tiers" in config:
            issues.extend(self._validate_tiers(config["tiers"]))

        # Validate scoring
        if "scoring" in config:
            issues.extend(self._validate_scoring(config["scoring"]))

        # Check weight sums
        weight_result = self._validate_weight_sums(config)
        issues.extend(weight_result)

        # Determine overall validity
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)

        return ValidationResult(
            valid=not has_errors,
            issues=issues,
            warnings=warnings,
        )

    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a YAML configuration file.

        Args:
            file_path: Path to configuration file

        Returns:
            ValidationResult with issues
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return self.validate_yaml(content)
        except FileNotFoundError:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="file",
                    message=f"File not found: {file_path}",
                )],
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="file",
                    message=f"Error reading file: {e}",
                )],
            )

    def _validate_structure(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate top-level structure."""
        issues = []

        for key in self.REQUIRED_KEYS:
            if key not in config:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"Missing required key: {key}",
                    path=key,
                ))

        return issues

    def _validate_coverage_section(self, coverage: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate coverage section."""
        issues = []

        if not isinstance(coverage, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="coverage",
                message="Coverage section must be a dictionary",
            )]

        for field in self.REQUIRED_COVERAGE_FIELDS:
            if field not in coverage:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="coverage",
                    message=f"Missing required coverage field: {field}",
                    path=f"coverage.{field}",
                ))

        # Validate ID format
        if "id" in coverage:
            cov_id = coverage["id"]
            if not isinstance(cov_id, str) or not cov_id.islower():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="coverage",
                    message="Coverage ID should be lowercase",
                    path="coverage.id",
                    suggestion="Use lowercase with underscores",
                ))

        return issues

    def _validate_signal_groups(self, groups: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate signal groups section."""
        issues = []

        if not isinstance(groups, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_groups",
                message="signal_groups must be a dictionary",
            )]

        if len(groups) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_groups",
                message="At least one signal group is required",
            ))

        for group_id, group_config in groups.items():
            if not isinstance(group_config, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_groups",
                    message=f"Signal group {group_id} must be a dictionary",
                    path=f"signal_groups.{group_id}",
                ))
                continue

            # Check for weight
            if "weight" not in group_config:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="signal_groups",
                    message=f"Signal group {group_id} missing weight",
                    path=f"signal_groups.{group_id}.weight",
                ))

            # Check for signals
            if "signals" not in group_config:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_groups",
                    message=f"Signal group {group_id} missing signals array",
                    path=f"signal_groups.{group_id}.signals",
                ))
            elif not isinstance(group_config["signals"], list):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_groups",
                    message=f"Signals in {group_id} must be an array",
                    path=f"signal_groups.{group_id}.signals",
                ))

        return issues

    def _validate_tiers(self, tiers: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate tiers section."""
        issues = []

        if not isinstance(tiers, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="tiers",
                message="tiers must be a dictionary",
            )]

        # Check for required tiers (1-5)
        for tier_num in ["1", "2", "3", "4", "5"]:
            if tier_num not in tiers:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="tiers",
                    message=f"Missing tier {tier_num}",
                    path=f"tiers.{tier_num}",
                ))

        # Validate tier thresholds are monotonic
        prev_score = 1000
        for tier_num in sorted(tiers.keys()):
            tier_config = tiers[tier_num]
            if isinstance(tier_config, dict) and "min_score" in tier_config:
                score = tier_config["min_score"]
                if score > prev_score:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="tiers",
                        message=f"Tier {tier_num} min_score ({score}) should be <= tier {int(tier_num)-1}",
                        path=f"tiers.{tier_num}.min_score",
                    ))
                prev_score = score

        return issues

    def _validate_scoring(self, scoring: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate scoring section."""
        issues = []

        if not isinstance(scoring, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="scoring",
                message="scoring must be a dictionary",
            )]

        # Check for scale
        if "scale" in scoring:
            scale = scoring["scale"]
            if isinstance(scale, dict):
                if "min" not in scale or "max" not in scale:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="scoring",
                        message="Scale should have min and max values",
                        path="scoring.scale",
                    ))
                elif scale.get("min", 0) >= scale.get("max", 100):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="scoring",
                        message="Scale min must be less than max",
                        path="scoring.scale",
                    ))

        return issues

    def _validate_weight_sums(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate that weights sum to 1.0."""
        issues = []

        groups = config.get("signal_groups", {})
        if not groups:
            return issues

        # Sum group weights
        total_weight = 0.0
        for group_id, group_config in groups.items():
            if isinstance(group_config, dict):
                weight = group_config.get("weight", 0)
                total_weight += float(weight)

        # Allow some tolerance
        if not (0.95 <= total_weight <= 1.05):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR if abs(total_weight - 1.0) > 0.1 else ValidationSeverity.WARNING,
                category="weights",
                message=f"Group weights sum to {total_weight:.3f}, expected ~1.0",
                suggestion="Adjust group weights to sum to 1.0",
            ))

        return issues


def validate_coverage_config(yaml_content: str) -> ValidationResult:
    """
    Convenience function to validate coverage config.

    Args:
        yaml_content: YAML configuration string

    Returns:
        ValidationResult
    """
    validator = ConfigValidator()
    return validator.validate_yaml(yaml_content)
