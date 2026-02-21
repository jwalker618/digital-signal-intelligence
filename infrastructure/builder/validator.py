"""
DSI Configuration Validator (Phase 13 → v2.0 Overhaul)

Validates coverage configurations against the v2.0 schema:
  coverage_id:
    coverage_id_general:
      metadata, direct_queries, signal_registry, groups,
      risk_tier_bands, loss_tier_bands, exposure, limit_bandings, pricing

Constraints enforced:
- score_conditions actions: FLAG | MODIFIER | REFER (DECLINE is tier-level only)
- score_conditions must be banded (plural, list)
- score_conditions do NOT apply to tier bands
- Signals defined once in signal_registry with group_id reference
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

# Valid actions for score_conditions (DECLINE is tier-level only)
SCORE_CONDITION_ACTIONS = {"FLAG", "MODIFIER", "REFER"}
# Valid actions for tier bands (includes DECLINE)
TIER_ACTIONS = {"APPROVE", "REFER", "DECLINE"}


class ConfigValidator:
    """
    Validates v2.0 coverage configurations.

    Checks:
    - v2.0 nested structure (coverage_id → config_name → sections)
    - signal_registry with three_layer_assessment or categories
    - groups with categories and three_layer_assessment
    - risk_tier_bands with interpretation blocks
    - loss_tier_bands with frequency/severity modifiers
    - exposure with nested size/complexity
    - score_conditions action constraints
    - Weight sums and band coverage
    """

    V2_REQUIRED_SECTIONS = [
        "metadata", "signal_registry", "groups",
        "risk_tier_bands", "loss_tier_bands", "exposure",
    ]

    def __init__(self, signal_library=None):
        self.signal_library = signal_library

    def validate_yaml(self, yaml_content: str) -> ValidationResult:
        """Validate YAML configuration string against v2.0 schema."""
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

        # Detect and extract v2.0 inner config
        inner = self._extract_inner_config(config)
        if inner is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="Expected v2.0 structure: coverage_id → config_name → {sections}",
                suggestion="Config should be nested as: cyber: cyber_general: {metadata, signal_registry, ...}",
            ))
            return ValidationResult(valid=False, issues=issues)

        # Validate required sections
        issues.extend(self._validate_required_sections(inner))

        # Validate each section
        if "metadata" in inner:
            issues.extend(self._validate_metadata(inner["metadata"]))

        if "direct_queries" in inner:
            issues.extend(self._validate_direct_queries(inner["direct_queries"]))

        if "signal_registry" in inner:
            issues.extend(self._validate_signal_registry(inner["signal_registry"]))

        if "groups" in inner:
            issues.extend(self._validate_groups(inner["groups"]))

        if "risk_tier_bands" in inner:
            issues.extend(self._validate_risk_tier_bands(inner["risk_tier_bands"]))

        if "loss_tier_bands" in inner:
            issues.extend(self._validate_loss_tier_bands(inner["loss_tier_bands"]))

        if "exposure" in inner:
            issues.extend(self._validate_exposure(inner["exposure"]))

        if "pricing" in inner:
            issues.extend(self._validate_pricing(inner["pricing"]))

        # Cross-section validation
        issues.extend(self._validate_cross_references(inner))

        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        return ValidationResult(
            valid=not has_errors,
            issues=issues,
            warnings=[i.message for i in issues if i.severity == ValidationSeverity.WARNING],
        )

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a YAML configuration file."""
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

    def _extract_inner_config(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract the inner config from v2.0 nested structure.

        Expects: coverage_id → config_name → {metadata, signal_registry, ...}
        """
        for coverage_id, coverage_value in config.items():
            if not isinstance(coverage_value, dict):
                continue
            for config_name, inner in coverage_value.items():
                if isinstance(inner, dict) and ("metadata" in inner or "signal_registry" in inner):
                    return inner
        return None

    def _validate_required_sections(self, inner: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        for section in self.V2_REQUIRED_SECTIONS:
            if section not in inner:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"Missing required section: {section}",
                    path=section,
                ))
        return issues

    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(metadata, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="metadata",
                message="metadata must be a dictionary",
            )]

        required_fields = ["name", "version"]
        for f in required_fields:
            if f not in metadata:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="metadata",
                    message=f"Missing metadata field: {f}",
                    path=f"metadata.{f}",
                ))

        if "minimum_viable_input" in metadata:
            mvi = metadata["minimum_viable_input"]
            if not isinstance(mvi, list) or len(mvi) == 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="metadata",
                    message="minimum_viable_input should be a non-empty list",
                    path="metadata.minimum_viable_input",
                ))

        return issues

    def _validate_direct_queries(self, queries: list) -> List[ValidationIssue]:
        issues = []
        if not isinstance(queries, list):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="direct_queries",
                message="direct_queries must be a list",
            )]

        if len(queries) > 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="direct_queries",
                message=f"direct_queries has {len(queries)} items (max recommended: 10)",
            ))

        for i, q in enumerate(queries):
            path = f"direct_queries[{i}]"
            if not isinstance(q, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="direct_queries",
                    message=f"Query must be a dict at {path}",
                    path=path,
                ))
                continue

            if "id" not in q:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="direct_queries",
                    message=f"Missing 'id' at {path}",
                    path=path,
                ))

            if "question" not in q:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="direct_queries",
                    message=f"Missing 'question' at {path}",
                    path=path,
                ))

            # Must use query_condition (not bands)
            if "query_condition" not in q:
                if "bands" in q:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="direct_queries",
                        message=f"Use 'query_condition' not 'bands' at {path}",
                        path=path,
                        suggestion="Rename 'bands' to 'query_condition'",
                    ))
                else:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="direct_queries",
                        message=f"Missing 'query_condition' at {path}",
                        path=path,
                    ))
            else:
                issues.extend(self._validate_query_conditions(q["query_condition"], path))

        return issues

    def _validate_query_conditions(self, conditions: list, parent_path: str) -> List[ValidationIssue]:
        issues = []
        if not isinstance(conditions, list):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="direct_queries",
                message=f"query_condition must be a list at {parent_path}",
                path=f"{parent_path}.query_condition",
            )]

        for i, cond in enumerate(conditions):
            path = f"{parent_path}.query_condition[{i}]"
            if not isinstance(cond, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="direct_queries",
                    message=f"Condition must be a dict at {path}",
                    path=path,
                ))
                continue

            if "action" in cond and cond["action"] not in SCORE_CONDITION_ACTIONS:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="direct_queries",
                    message=f"Invalid action '{cond['action']}' at {path}. "
                            f"Valid: {SCORE_CONDITION_ACTIONS}. DECLINE is tier-level only.",
                    path=path,
                ))

            if cond.get("action") == "MODIFIER" and cond.get("applied") is None:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="direct_queries",
                    message=f"MODIFIER action missing 'applied' value at {path}",
                    path=path,
                ))

        return issues

    def _validate_signal_registry(self, registry: list) -> List[ValidationIssue]:
        issues = []
        if not isinstance(registry, list):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message="signal_registry must be a list",
            )]

        if len(registry) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message="signal_registry must contain at least one signal",
            ))

        signal_ids = set()
        for i, signal in enumerate(registry):
            path = f"signal_registry[{i}]"
            if not isinstance(signal, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_registry",
                    message=f"Signal must be a dict at {path}",
                    path=path,
                ))
                continue

            # Required: id
            sig_id = signal.get("id")
            if not sig_id:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_registry",
                    message=f"Missing 'id' at {path}",
                    path=path,
                ))
            elif sig_id in signal_ids:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_registry",
                    message=f"Duplicate signal id '{sig_id}' at {path}",
                    path=path,
                ))
            else:
                signal_ids.add(sig_id)

            # Must have either categories or three_layer_assessment
            has_categories = "categories" in signal
            has_tla = "three_layer_assessment" in signal
            if not has_categories and not has_tla:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="signal_registry",
                    message=f"Signal '{sig_id}' must have 'categories' or 'three_layer_assessment'",
                    path=path,
                ))

            # Validate three_layer_assessment
            if has_tla:
                issues.extend(self._validate_tla_signal(signal["three_layer_assessment"], path, sig_id))

            # Validate categories
            if has_categories:
                issues.extend(self._validate_categorical_signal(signal["categories"], path, sig_id))

        return issues

    def _validate_tla_signal(
        self, tla: Dict[str, Any], parent_path: str, signal_id: str
    ) -> List[ValidationIssue]:
        issues = []
        path = f"{parent_path}.three_layer_assessment"

        if not isinstance(tla, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message=f"three_layer_assessment must be a dict for '{signal_id}'",
                path=path,
            )]

        if "group_id" not in tla:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message=f"Missing 'group_id' in three_layer_assessment for '{signal_id}'",
                path=path,
            ))

        # Validate risk dimension
        if "risk" in tla:
            risk = tla["risk"]
            if isinstance(risk, dict):
                if "score_conditions" in risk:
                    issues.extend(self._validate_score_conditions(
                        risk["score_conditions"], f"{path}.risk"
                    ))

        # Validate loss dimension
        if "loss" in tla:
            loss = tla["loss"]
            if isinstance(loss, dict):
                # Loss can have frequency and/or severity sub-blocks
                for sub in ("frequency", "severity"):
                    if sub in loss and isinstance(loss[sub], dict):
                        if "correlation_direction" not in loss[sub] and "source" not in loss[sub]:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="signal_registry",
                                message=f"Loss.{sub} for '{signal_id}' missing correlation_direction or source",
                                path=f"{path}.loss.{sub}",
                            ))

        return issues

    def _validate_categorical_signal(
        self, cats: Dict[str, Any], parent_path: str, signal_id: str
    ) -> List[ValidationIssue]:
        issues = []
        path = f"{parent_path}.categories"

        if not isinstance(cats, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message=f"categories must be a dict for '{signal_id}'",
                path=path,
            )]

        if "group_id" not in cats:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message=f"Missing 'group_id' in categories for '{signal_id}'",
                path=path,
            ))

        if "features" not in cats:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="signal_registry",
                message=f"Missing 'features' in categories for '{signal_id}'",
                path=path,
            ))
        elif isinstance(cats["features"], list):
            for j, feat in enumerate(cats["features"]):
                if isinstance(feat, dict) and "applied" not in feat:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="signal_registry",
                        message=f"Category feature missing 'applied' modifier for '{signal_id}'",
                        path=f"{path}.features[{j}]",
                    ))

        return issues

    def _validate_score_conditions(self, conditions: list, path: str) -> List[ValidationIssue]:
        """Validate score_conditions: actions must be FLAG | MODIFIER | REFER."""
        issues = []

        if not isinstance(conditions, list):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="score_conditions",
                message=f"score_conditions must be a list at {path}",
                path=path,
            ))
            return issues

        for i, cond in enumerate(conditions):
            cond_path = f"{path}.score_conditions[{i}]"

            if not isinstance(cond, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="score_conditions",
                    message=f"Condition must be a dict at {cond_path}",
                    path=cond_path,
                ))
                continue

            if "threshold" not in cond:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="score_conditions",
                    message=f"Missing 'threshold' at {cond_path}",
                    path=cond_path,
                ))

            if "action" not in cond:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="score_conditions",
                    message=f"Missing 'action' at {cond_path}",
                    path=cond_path,
                ))
            elif cond["action"] not in SCORE_CONDITION_ACTIONS:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="score_conditions",
                    message=f"Invalid action '{cond['action']}' at {cond_path}. "
                            f"Valid: {SCORE_CONDITION_ACTIONS}. DECLINE is tier-level only.",
                    path=cond_path,
                ))

            if cond.get("action") == "MODIFIER" and "applied" not in cond:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="score_conditions",
                    message=f"MODIFIER action missing 'applied' value at {cond_path}",
                    path=cond_path,
                ))

        return issues

    def _validate_groups(self, groups: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(groups, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="groups",
                message="groups must be a dictionary with 'categories' and/or 'three_layer_assessment'",
            )]

        # Validate categories
        if "categories" in groups:
            cats = groups["categories"]
            if not isinstance(cats, list):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="groups",
                    message="groups.categories must be a list",
                    path="groups.categories",
                ))
            else:
                for i, cat in enumerate(cats):
                    if isinstance(cat, dict):
                        if "id" not in cat:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                category="groups",
                                message=f"Category missing 'id' at groups.categories[{i}]",
                                path=f"groups.categories[{i}]",
                            ))

        # Validate three_layer_assessment groups
        if "three_layer_assessment" in groups:
            tla_groups = groups["three_layer_assessment"]
            if not isinstance(tla_groups, list):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="groups",
                    message="groups.three_layer_assessment must be a list",
                    path="groups.three_layer_assessment",
                ))
            else:
                total_risk_weight = 0.0
                for i, grp in enumerate(tla_groups):
                    path = f"groups.three_layer_assessment[{i}]"
                    if not isinstance(grp, dict):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="groups",
                            message=f"Group must be a dict at {path}",
                            path=path,
                        ))
                        continue

                    if "id" not in grp:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="groups",
                            message=f"Group missing 'id' at {path}",
                            path=path,
                        ))

                    # Validate risk/loss/exposure dimension blocks
                    for dim in ("risk", "loss", "exposure"):
                        if dim in grp and isinstance(grp[dim], dict):
                            dim_data = grp[dim]
                            if dim == "risk":
                                total_risk_weight += dim_data.get("weight", 0)
                            if "score_conditions" in dim_data:
                                issues.extend(self._validate_score_conditions(
                                    dim_data["score_conditions"], f"{path}.{dim}"
                                ))

                # Check risk weights sum
                if total_risk_weight > 0 and not (0.95 <= total_risk_weight <= 1.05):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="groups",
                        message=f"Group risk weights sum to {total_risk_weight:.2f}, expected ~1.0",
                        suggestion="Adjust three_layer_assessment group risk weights to sum to 1.0",
                    ))

        return issues

    def _validate_risk_tier_bands(self, rtb: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(rtb, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="risk_tier_bands",
                message="risk_tier_bands must be a dictionary",
            )]

        if "bands" not in rtb:
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="risk_tier_bands",
                message="risk_tier_bands missing 'bands' array",
            )]

        bands = rtb["bands"]
        if not isinstance(bands, list) or len(bands) == 0:
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="risk_tier_bands",
                message="risk_tier_bands.bands must be a non-empty list",
            )]

        has_decline = False
        prev_max = None
        for i, band in enumerate(bands):
            path = f"risk_tier_bands.bands[{i}]"
            if not isinstance(band, dict):
                continue

            interp = band.get("interpretation", {})
            if not isinstance(interp, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="risk_tier_bands",
                    message=f"Missing 'interpretation' block at {path}",
                    path=path,
                ))
                continue

            # Check action
            action = interp.get("action")
            if action and action not in TIER_ACTIONS:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="risk_tier_bands",
                    message=f"Invalid tier action '{action}' at {path}. Valid: {TIER_ACTIONS}",
                    path=path,
                ))
            if action == "DECLINE":
                has_decline = True

            # Check bands range
            band_range = interp.get("bands", {})
            if isinstance(band_range, dict):
                bmin = band_range.get("min", 0)
                bmax = band_range.get("max", 0)
                if prev_max is not None and bmax >= prev_max:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="risk_tier_bands",
                        message=f"Band ranges may overlap at {path}",
                        path=path,
                    ))
                prev_max = bmin

            # Check application
            app = interp.get("application", {})
            if isinstance(app, dict) and "applied" not in app:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="risk_tier_bands",
                    message=f"Missing 'applied' in application at {path}",
                    path=path,
                ))

        if not has_decline:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="risk_tier_bands",
                message="No DECLINE tier found - all submissions could be approved",
            ))

        return issues

    def _validate_loss_tier_bands(self, ltb: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(ltb, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="loss_tier_bands",
                message="loss_tier_bands must be a dictionary",
            )]

        if "bands" not in ltb:
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="loss_tier_bands",
                message="loss_tier_bands missing 'bands' array",
            )]

        for i, band in enumerate(ltb["bands"]):
            if not isinstance(band, dict):
                continue
            interp = band.get("interpretation", {})
            app = interp.get("application", {}) if isinstance(interp, dict) else {}
            if "frequency_modifier" not in app or "severity_modifier" not in app:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="loss_tier_bands",
                    message=f"Loss band '{band.get('label', '?')}' missing frequency/severity modifiers",
                    path=f"loss_tier_bands.bands[{i}]",
                ))

        if "constraints" not in ltb:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="loss_tier_bands",
                message="loss_tier_bands missing 'constraints' (floor/cap)",
            ))
        elif isinstance(ltb["constraints"], dict):
            constraints = ltb["constraints"]
            if "floor" not in constraints or "cap" not in constraints:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="loss_tier_bands",
                    message="loss_tier_bands.constraints should have 'floor' and 'cap'",
                ))

        return issues

    def _validate_exposure(self, exposure: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(exposure, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="exposure",
                message="exposure must be a dictionary with 'size' and 'complexity'",
            )]

        # Must have size and complexity sub-sections
        for dim in ("size", "complexity"):
            if dim not in exposure:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="exposure",
                    message=f"exposure missing '{dim}' section",
                    path=f"exposure.{dim}",
                ))
                continue

            dim_data = exposure[dim]
            if not isinstance(dim_data, dict):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="exposure",
                    message=f"exposure.{dim} must be a dictionary",
                    path=f"exposure.{dim}",
                ))
                continue

            if "weight" not in dim_data:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="exposure",
                    message=f"exposure.{dim} missing 'weight'",
                    path=f"exposure.{dim}.weight",
                ))

            if "bands" not in dim_data:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="exposure",
                    message=f"exposure.{dim} missing 'bands' array",
                    path=f"exposure.{dim}.bands",
                ))
            elif isinstance(dim_data["bands"], list):
                for j, band in enumerate(dim_data["bands"]):
                    if isinstance(band, dict):
                        interp = band.get("interpretation", {})
                        if not isinstance(interp, dict) or "bands" not in interp:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="exposure",
                                message=f"Exposure band missing interpretation at exposure.{dim}.bands[{j}]",
                                path=f"exposure.{dim}.bands[{j}]",
                            ))

        # Check weights sum to ~1.0
        size_w = exposure.get("size", {}).get("weight", 0) if isinstance(exposure.get("size"), dict) else 0
        comp_w = exposure.get("complexity", {}).get("weight", 0) if isinstance(exposure.get("complexity"), dict) else 0
        total = size_w + comp_w
        if total > 0 and not (0.95 <= total <= 1.05):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="exposure",
                message=f"Exposure weights sum to {total:.2f}, expected ~1.0",
            ))

        return issues

    def _validate_pricing(self, pricing: Dict[str, Any]) -> List[ValidationIssue]:
        issues = []
        if not isinstance(pricing, dict):
            return [ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="pricing",
                message="pricing must be a dictionary",
            )]

        # Phase 5 Strict Anchor Enforcement
        if "base_limit_reference" not in pricing or "base_deductible_reference" not in pricing:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="pricing",
                message="pricing is missing required Phase 5 anchors (base_limit_reference, base_deductible_reference)",
            ))

        if "by_product_type" not in pricing:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="pricing",
                message="pricing missing 'by_product_type' mapping",
            ))
        else:
            for prod, data in pricing.get("by_product_type", {}).items():
                if "ilf_curve" not in data or "deductible_factors" not in data:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="pricing",
                        message=f"Product '{prod}' missing 'ilf_curve' or 'deductible_factors'",
                        path=f"pricing.by_product_type.{prod}"
                    ))
        return issues

    def _validate_cross_references(self, inner: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate cross-references between sections."""
        issues = []

        # Collect group_ids from signal_registry
        signal_group_ids = set()
        registry = inner.get("signal_registry", [])
        if isinstance(registry, list):
            for sig in registry:
                if isinstance(sig, dict):
                    tla = sig.get("three_layer_assessment", {})
                    cats = sig.get("categories", {})
                    if isinstance(tla, dict) and "group_id" in tla:
                        signal_group_ids.add(tla["group_id"])
                    if isinstance(cats, dict) and "group_id" in cats:
                        signal_group_ids.add(cats["group_id"])

        # Check that groups section defines all referenced group_ids
        groups = inner.get("groups", {})
        defined_group_ids = set()
        if isinstance(groups, dict):
            for cat in groups.get("categories", []):
                if isinstance(cat, dict) and "id" in cat:
                    defined_group_ids.add(cat["id"])
            for tla in groups.get("three_layer_assessment", []):
                if isinstance(tla, dict) and "id" in tla:
                    defined_group_ids.add(tla["id"])

        missing = signal_group_ids - defined_group_ids
        if missing:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="cross_reference",
                message=f"Signal registry references undefined groups: {missing}",
                suggestion="Add these groups to the 'groups' section",
            ))

        return issues


# =============================================================================
# Phase 8 Audit Trail Validation (Cycle 3 Requirement)
# =============================================================================

AUDIT_TRAIL_REQUIRED_FIELDS = ["user_id", "timestamp", "rationale"]
AUDIT_TRAIL_OPTIONAL_FIELDS = ["evidence_reference", "previous_value", "new_value"]


def validate_audit_trail_entry(entry: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate a single audit trail entry.

    When is_overridden == True, the audit_trail must contain entries with:
    - user_id: Non-null identifier of the underwriter
    - timestamp: Non-null ISO 8601 timestamp
    - rationale: Non-null explanation for the override
    - evidence_reference: Optional reference to supporting documentation

    Args:
        entry: Single audit trail entry dict

    Returns:
        List of validation issues found
    """
    issues = []

    if not isinstance(entry, dict):
        return [ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="audit_trail",
            message="Audit trail entry must be a dictionary",
        )]

    # Check required fields
    for field in AUDIT_TRAIL_REQUIRED_FIELDS:
        if field not in entry or entry[field] is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="audit_trail",
                message=f"Missing required audit trail field: '{field}'",
                suggestion=f"Ensure '{field}' is provided and non-null",
            ))

    # Validate timestamp format
    if "timestamp" in entry and entry["timestamp"]:
        timestamp = entry["timestamp"]
        if isinstance(timestamp, str):
            # Basic ISO 8601 validation
            import re
            iso_pattern = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
            if not re.match(iso_pattern, timestamp):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="audit_trail",
                    message=f"Timestamp '{timestamp}' may not be valid ISO 8601 format",
                    suggestion="Use format: YYYY-MM-DDTHH:MM:SSZ",
                ))

    # Validate rationale is not empty
    if "rationale" in entry and entry["rationale"] is not None:
        rationale = entry["rationale"]
        if isinstance(rationale, str) and len(rationale.strip()) < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="audit_trail",
                message="Rationale is too short (minimum 10 characters recommended)",
                suggestion="Provide a meaningful explanation for the override",
            ))

    return issues


def validate_audit_trail(
    audit_trail: List[Dict[str, Any]],
    is_overridden: bool = False,
) -> List[ValidationIssue]:
    """
    Validate the complete audit_trail JSONB field.

    Enforces Cycle 3 requirement: strict schema validation when is_overridden == True.

    Args:
        audit_trail: List of audit trail entries
        is_overridden: Whether the signal value has been overridden

    Returns:
        List of validation issues found
    """
    issues = []

    if not isinstance(audit_trail, list):
        return [ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="audit_trail",
            message="audit_trail must be a list (array)",
        )]

    # If overridden, must have at least one audit entry
    if is_overridden and len(audit_trail) == 0:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category="audit_trail",
            message="is_overridden is True but audit_trail is empty",
            suggestion="Add an audit entry explaining the override",
        ))

    # Validate each entry
    for i, entry in enumerate(audit_trail):
        entry_issues = validate_audit_trail_entry(entry)
        for issue in entry_issues:
            issue.path = f"audit_trail[{i}].{issue.path or ''}"
            issues.append(issue)

    return issues


def validate_signal_override_payload(payload: Dict[str, Any]) -> ValidationResult:
    """
    Validate a signal override API request payload.

    Used by Phase 8 API endpoints to ensure override requests are complete.

    Args:
        payload: Signal override request body

    Returns:
        ValidationResult with any issues found
    """
    issues = []

    required_fields = ["signal_id", "audited_value", "rationale"]
    for field in required_fields:
        if field not in payload or payload[field] is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="api_validation",
                message=f"Missing required field: '{field}'",
                path=field,
            ))

    # Validate audited_value is numeric
    if "audited_value" in payload:
        val = payload["audited_value"]
        if not isinstance(val, (int, float)):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="api_validation",
                message="audited_value must be numeric",
                path="audited_value",
            ))
        elif not (0 <= val <= 100):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="api_validation",
                message=f"audited_value {val} is outside normal range (0-100)",
                path="audited_value",
            ))

    # Validate rationale length
    if "rationale" in payload and payload["rationale"]:
        if len(payload["rationale"].strip()) < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="api_validation",
                message="Rationale should be at least 10 characters",
                path="rationale",
            ))

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(
        valid=not has_errors,
        issues=issues,
        warnings=[i.message for i in issues if i.severity == ValidationSeverity.WARNING],
    )


def validate_coverage_config(yaml_content: str) -> ValidationResult:
    """Convenience function to validate coverage config."""
    validator = ConfigValidator()
    return validator.validate_yaml(yaml_content)
