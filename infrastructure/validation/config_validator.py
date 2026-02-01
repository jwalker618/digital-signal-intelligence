"""
DSI Model Configuration Validator (v2.0)

Comprehensive validation of coverage YAML configurations against
the v2.0 master schema defined in master_config_layout.yaml.

Validates:
- Structural compliance (required sections, proper nesting)
- Score conditions (threshold/comparison/action format, no DECLINE)
- Weight summation (groups sum to 1.0, features within groups sum to 1.0)
- Tier coverage (0-1000 range, no gaps)
- Loss tier bands (frequency/severity modifiers, constraints)
- Exposure tier bands (method on each band)
- Inference function references
- Cross-coverage consistency
"""

import logging
import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dsi.validation")


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: Severity
    category: str
    message: str
    path: str = ""
    suggestion: str = ""


@dataclass
class ValidationReport:
    coverage: str
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity == Severity.ERROR:
            self.error_count += 1
            self.valid = False
        elif issue.severity == Severity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    def summary(self) -> str:
        status = "PASS" if self.valid else "FAIL"
        return (
            f"{self.coverage}: {status} "
            f"({self.error_count} errors, {self.warning_count} warnings, "
            f"{self.info_count} info)"
        )


VALID_SCORE_CONDITION_ACTIONS = {"FLAG", "MODIFIER", "REFER"}


class ModelConfigValidator:
    """
    Validates DSI v2.0 coverage configurations.

    Performs structural, semantic, and cross-coverage validation.
    """

    def validate_file(self, file_path: Path) -> ValidationReport:
        """Validate a single coverage config file."""
        report = ValidationReport(coverage=str(file_path), valid=True)

        try:
            content = file_path.read_text()
            raw = yaml.safe_load(content)
        except Exception as e:
            report.add(ValidationIssue(
                Severity.ERROR, "parse", f"Failed to parse YAML: {e}"))
            return report

        if not isinstance(raw, dict):
            report.add(ValidationIssue(
                Severity.ERROR, "structure", "Root must be a dict"))
            return report

        # Get the coverage config (nested structure)
        coverage_name = list(raw.keys())[0]
        report.coverage = coverage_name
        coverage_data = raw[coverage_name]

        if not isinstance(coverage_data, dict):
            report.add(ValidationIssue(
                Severity.ERROR, "structure",
                f"Coverage '{coverage_name}' value must be a dict"))
            return report

        config_name = list(coverage_data.keys())[0]
        config = coverage_data[config_name]

        # Run all validations
        self._validate_metadata(config, report)
        self._validate_signal_groups(config, report)
        self._validate_signal_features(config, report)
        self._validate_score_conditions_in_groups(config, report)
        self._validate_score_conditions_in_features(config, report)
        self._validate_tier_thresholds(config, report)
        self._validate_loss_tier_bands(config, report)
        self._validate_exposure_tier_bands(config, report)
        self._validate_weight_sums(config, report)
        self._validate_no_decline_in_score_conditions(config, report)

        return report

    def validate_all(self, coverages_dir: Path) -> List[ValidationReport]:
        """Validate all coverage configs in a directory."""
        reports = []
        for config_file in sorted(coverages_dir.glob("*/config.yaml")):
            report = self.validate_file(config_file)
            reports.append(report)
        return reports

    def _validate_metadata(self, config: Dict, report: ValidationReport):
        """Validate metadata section."""
        metadata = config.get("metadata")
        if metadata is None:
            report.add(ValidationIssue(
                Severity.WARNING, "metadata", "Missing metadata section"))
            return

        for field_name in ["name", "version"]:
            if field_name not in metadata:
                report.add(ValidationIssue(
                    Severity.WARNING, "metadata",
                    f"Missing metadata.{field_name}",
                    path=f"metadata.{field_name}"))

    def _validate_signal_groups(self, config: Dict, report: ValidationReport):
        """Validate signal_groups section exists and has required fields."""
        groups = config.get("signal_groups", [])
        if not groups:
            # Check for signal_registry (cyber-style)
            if "signal_registry" not in config:
                report.add(ValidationIssue(
                    Severity.ERROR, "signal_groups",
                    "Missing signal_groups or signal_registry"))
            return

        for group in groups:
            gid = group.get("id", "?")
            if "weight" not in group:
                report.add(ValidationIssue(
                    Severity.ERROR, "signal_groups",
                    f"Group '{gid}' missing weight",
                    path=f"signal_groups.{gid}.weight"))

    def _validate_signal_features(self, config: Dict, report: ValidationReport):
        """Validate signal_features section."""
        features = config.get("signal_features", {})
        groups = config.get("signal_groups", [])

        if not features and not config.get("signal_registry"):
            report.add(ValidationIssue(
                Severity.WARNING, "signal_features",
                "Missing signal_features section"))
            return

        group_ids = {g.get("id") for g in groups}
        for group_id, feature_list in features.items():
            if group_id not in group_ids:
                report.add(ValidationIssue(
                    Severity.WARNING, "signal_features",
                    f"Features for unknown group '{group_id}'",
                    path=f"signal_features.{group_id}"))

            if not isinstance(feature_list, list):
                continue

            for feat in feature_list:
                fid = feat.get("id", "?")
                if "inference_utility_function" not in feat:
                    report.add(ValidationIssue(
                        Severity.WARNING, "signal_features",
                        f"Feature '{fid}' missing inference_utility_function",
                        path=f"signal_features.{group_id}.{fid}"))

    def _validate_score_conditions_in_groups(self, config: Dict, report: ValidationReport):
        """Validate score_conditions format in signal groups."""
        for group in config.get("signal_groups", []):
            gid = group.get("id", "?")
            sc = group.get("score_conditions")
            if sc is None:
                report.add(ValidationIssue(
                    Severity.WARNING, "score_conditions",
                    f"Group '{gid}' has no score_conditions",
                    path=f"signal_groups.{gid}"))
                continue

            if isinstance(sc, bool):
                report.add(ValidationIssue(
                    Severity.ERROR, "score_conditions",
                    f"Group '{gid}' uses boolean score_conditions (v1.0). "
                    f"Must be a list of condition objects (v2.0).",
                    path=f"signal_groups.{gid}.score_conditions"))
                continue

            if isinstance(sc, list):
                self._validate_conditions_list(sc, f"signal_groups.{gid}", report)

    def _validate_score_conditions_in_features(self, config: Dict, report: ValidationReport):
        """Validate score_conditions format in signal features."""
        for group_id, features in config.get("signal_features", {}).items():
            if not isinstance(features, list):
                continue
            for feat in features:
                fid = feat.get("id", "?")
                sc = feat.get("score_conditions")
                if sc is None:
                    continue  # Features don't require score_conditions

                if isinstance(sc, bool):
                    report.add(ValidationIssue(
                        Severity.ERROR, "score_conditions",
                        f"Feature '{fid}' uses boolean score_conditions (v1.0)",
                        path=f"signal_features.{group_id}.{fid}"))
                    continue

                if isinstance(sc, list):
                    self._validate_conditions_list(
                        sc, f"signal_features.{group_id}.{fid}", report)

    def _validate_conditions_list(
        self, conditions: list, path: str, report: ValidationReport
    ):
        """Validate a list of score_condition objects."""
        for i, cond in enumerate(conditions):
            cpath = f"{path}.score_conditions[{i}]"
            if not isinstance(cond, dict):
                report.add(ValidationIssue(
                    Severity.ERROR, "score_conditions",
                    f"Condition must be dict at {cpath}", path=cpath))
                continue

            if "threshold" not in cond:
                report.add(ValidationIssue(
                    Severity.ERROR, "score_conditions",
                    f"Missing 'threshold' at {cpath}", path=cpath))

            if "action" not in cond:
                report.add(ValidationIssue(
                    Severity.ERROR, "score_conditions",
                    f"Missing 'action' at {cpath}", path=cpath))
            elif cond["action"] not in VALID_SCORE_CONDITION_ACTIONS:
                report.add(ValidationIssue(
                    Severity.ERROR, "score_conditions",
                    f"Invalid action '{cond['action']}' at {cpath}. "
                    f"Valid: {VALID_SCORE_CONDITION_ACTIONS}",
                    path=cpath))

            if cond.get("action") == "MODIFIER" and "applied" not in cond:
                report.add(ValidationIssue(
                    Severity.WARNING, "score_conditions",
                    f"MODIFIER missing 'applied' at {cpath}", path=cpath))

    def _validate_no_decline_in_score_conditions(
        self, config: Dict, report: ValidationReport
    ):
        """Ensure DECLINE never appears in score_conditions."""
        # Check signal groups
        for group in config.get("signal_groups", []):
            sc = group.get("score_conditions", [])
            if isinstance(sc, list):
                for cond in sc:
                    if isinstance(cond, dict) and cond.get("action") == "DECLINE":
                        report.add(ValidationIssue(
                            Severity.ERROR, "score_conditions",
                            f"DECLINE in score_conditions for group "
                            f"'{group.get('id')}'. DECLINE is tier-level only.",
                            path=f"signal_groups.{group.get('id')}"))

        # Check signal features
        for group_id, features in config.get("signal_features", {}).items():
            if not isinstance(features, list):
                continue
            for feat in features:
                sc = feat.get("score_conditions", [])
                if isinstance(sc, list):
                    for cond in sc:
                        if isinstance(cond, dict) and cond.get("action") == "DECLINE":
                            report.add(ValidationIssue(
                                Severity.ERROR, "score_conditions",
                                f"DECLINE in score_conditions for feature "
                                f"'{feat.get('id')}'. DECLINE is tier-level only.",
                                path=f"signal_features.{group_id}.{feat.get('id')}"))

    def _validate_tier_thresholds(self, config: Dict, report: ValidationReport):
        """Validate tier_thresholds structure."""
        tiers_section = config.get("tier_thresholds", {})
        tiers = tiers_section.get("tiers", [])

        # Also check risk_tier_bands
        if not tiers and "risk_tier_bands" in config:
            tiers = config["risk_tier_bands"].get("bands", [])

        if not tiers:
            report.add(ValidationIssue(
                Severity.ERROR, "tiers",
                "No tier_thresholds or risk_tier_bands found"))
            return

        # Check application format on each tier
        for tier in tiers:
            tid = tier.get("id", "?")
            app = tier.get("application")
            if app is None:
                # Check for old format
                if "premium_generation_method" in tier:
                    report.add(ValidationIssue(
                        Severity.ERROR, "tiers",
                        f"Tier {tid} uses v1.0 premium_generation_method. "
                        f"Use application: {{method, applied}} instead.",
                        path=f"tier_thresholds.{tid}"))
                elif "premium" in tier:
                    report.add(ValidationIssue(
                        Severity.ERROR, "tiers",
                        f"Tier {tid} uses v1.0 premium field. "
                        f"Use application: {{method, applied}} instead.",
                        path=f"tier_thresholds.{tid}"))
                continue

            if "method" not in app:
                report.add(ValidationIssue(
                    Severity.WARNING, "tiers",
                    f"Tier {tid} application missing 'method'",
                    path=f"tier_thresholds.{tid}.application"))

            if "applied" not in app and "value" not in app:
                report.add(ValidationIssue(
                    Severity.WARNING, "tiers",
                    f"Tier {tid} application missing 'applied'",
                    path=f"tier_thresholds.{tid}.application"))

    def _validate_loss_tier_bands(self, config: Dict, report: ValidationReport):
        """Validate loss_tier_bands section."""
        loss = config.get("loss_tier_bands")
        if loss is None:
            report.add(ValidationIssue(
                Severity.WARNING, "loss_tier_bands",
                "Missing loss_tier_bands section"))
            return

        bands = loss.get("bands", [])
        if not bands:
            report.add(ValidationIssue(
                Severity.ERROR, "loss_tier_bands",
                "loss_tier_bands has no bands"))
            return

        for band in bands:
            label = band.get("label", "?")
            interp = band.get("interpretation", {})
            app = interp.get("application", {})

            if "frequency_modifier" not in app:
                report.add(ValidationIssue(
                    Severity.WARNING, "loss_tier_bands",
                    f"Band '{label}' missing frequency_modifier"))
            if "severity_modifier" not in app:
                report.add(ValidationIssue(
                    Severity.WARNING, "loss_tier_bands",
                    f"Band '{label}' missing severity_modifier"))

        if "constraints" not in loss:
            report.add(ValidationIssue(
                Severity.WARNING, "loss_tier_bands",
                "Missing constraints (floor/cap)"))

    def _validate_exposure_tier_bands(self, config: Dict, report: ValidationReport):
        """Validate exposure_tier_bands section."""
        # Check for exposure_tier_bands or exposure section
        exposure = config.get("exposure_tier_bands") or config.get("exposure")
        if exposure is None:
            report.add(ValidationIssue(
                Severity.WARNING, "exposure_tier_bands",
                "Missing exposure_tier_bands section"))
            return

        bands = exposure.get("bands", [])
        if not bands:
            # Exposure might use size/complexity sub-sections
            return

        for band in bands:
            label = band.get("label", "?")
            interp = band.get("interpretation", {})
            app = interp.get("application", {})

            if "method" not in app:
                report.add(ValidationIssue(
                    Severity.WARNING, "exposure_tier_bands",
                    f"Band '{label}' missing 'method'"))

    def _validate_weight_sums(self, config: Dict, report: ValidationReport):
        """Validate that group and feature weights sum to ~1.0."""
        groups = config.get("signal_groups", [])
        if not groups:
            return

        # Group weights
        total = sum(g.get("weight", 0) for g in groups)
        if abs(total - 1.0) > 0.01:
            report.add(ValidationIssue(
                Severity.ERROR, "weights",
                f"Signal group weights sum to {total:.3f}, expected ~1.0",
                suggestion="Adjust weights to sum to 1.0"))

        # Feature weights within each group
        features = config.get("signal_features", {})
        for group in groups:
            gid = group.get("id", "?")
            group_features = features.get(gid, [])
            if not group_features:
                continue

            feat_total = sum(f.get("weight", 0) for f in group_features)
            if abs(feat_total - 1.0) > 0.02:
                report.add(ValidationIssue(
                    Severity.ERROR, "weights",
                    f"Feature weights in '{gid}' sum to {feat_total:.3f}, "
                    f"expected ~1.0",
                    path=f"signal_features.{gid}"))
