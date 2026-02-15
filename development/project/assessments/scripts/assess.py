#!/usr/bin/env python3
"""
DSI Comprehensive Checklist Assessment Tool
============================================

A complete assessment tool that evaluates the DSI project directly against
the project_completeness_checklist.md structure, providing:

1. Per-coverage/per-configuration visibility (matrix output)
2. Section-by-section assessment matching the checklist structure
3. Output conforming to the checklist's Assessment Summary Template
4. Clear identification of what/where/why for each gap

Phase 7.1 Implementation - Replaces fragmented assessment tools

Usage:
    python assess.py                          # Full assessment
    python assess.py --section coverages      # Specific section
    python assess.py --coverage cyber         # Specific coverage matrix
    python assess.py --detailed               # Full detail output
    python assess.py --json                   # JSON output
    python assess.py --save                   # Save to results/

Version: 2.0.0
Date: February 2026
"""

import re
import sys
import os
import yaml
import json
import subprocess
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from enum import Enum
from datetime import datetime
import argparse


# ==============================================================================
# Configuration
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]
COVERAGES_DIR = PROJECT_ROOT / 'coverages'
CHECKLIST_PATH = PROJECT_ROOT / 'development' / 'project' / 'assessments' / 'project_completeness_checklist.md'


# ==============================================================================
# Data Types
# ==============================================================================

class Status(Enum):
    """Assessment status."""
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    NA = "N/A"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    """Result of a single check."""
    status: Status
    message: str
    details: Optional[str] = None
    file_path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class CoverageConfig:
    """Represents a coverage configuration."""
    coverage_dir: str      # e.g., 'cyber'
    coverage_id: str       # e.g., 'cyber'
    config_name: str       # e.g., 'cyber_general'
    config_data: Dict[str, Any]
    config_path: Path


@dataclass
class PerCoverageResult:
    """Results for a single coverage/config across all per-coverage checks."""
    coverage_config: CoverageConfig
    results: Dict[str, CheckResult]  # check_id -> result

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results.values() if r.status == Status.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results.values() if r.status == Status.FAIL)

    @property
    def partial(self) -> int:
        return sum(1 for r in self.results.values() if r.status == Status.PARTIAL)


@dataclass
class SectionResult:
    """Results for a checklist section."""
    name: str
    display_name: str
    checks: List[Tuple[str, CheckResult]]  # (check_description, result)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for _, r in self.checks if r.status == Status.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for _, r in self.checks if r.status == Status.FAIL)

    @property
    def partial(self) -> int:
        return sum(1 for _, r in self.checks if r.status == Status.PARTIAL)


@dataclass
class AssessmentResult:
    """Complete assessment result."""
    timestamp: str
    sections: Dict[str, SectionResult]
    per_coverage_results: List[PerCoverageResult]
    codebase_stats: Dict[str, int]

    @property
    def total_items(self) -> int:
        return sum(s.total for s in self.sections.values())

    @property
    def total_passed(self) -> int:
        return sum(s.passed for s in self.sections.values())

    @property
    def total_failed(self) -> int:
        return sum(s.failed for s in self.sections.values())

    @property
    def overall_percentage(self) -> float:
        total = self.total_items
        if total == 0:
            return 0.0
        passed = sum(s.passed + s.partial * 0.5 for s in self.sections.values())
        return (passed / total) * 100


# ==============================================================================
# Coverage Configuration Loader
# ==============================================================================

def load_all_coverage_configs() -> List[CoverageConfig]:
    """Load all coverage configurations from coverages/**/config.yaml."""
    configs = []

    for coverage_dir in sorted(COVERAGES_DIR.iterdir()):
        if not coverage_dir.is_dir():
            continue
        if coverage_dir.name.startswith('.') or coverage_dir.name in ('__pycache__',):
            continue

        config_path = coverage_dir / 'config.yaml'
        if not config_path.exists():
            continue

        try:
            with open(config_path) as f:
                raw_config = yaml.safe_load(f)

            if not isinstance(raw_config, dict):
                continue

            # Structure: coverage_id -> config_name -> config_data
            for coverage_id, coverage_data in raw_config.items():
                if not isinstance(coverage_data, dict):
                    continue

                for config_name, config_data in coverage_data.items():
                    if not isinstance(config_data, dict):
                        continue

                    configs.append(CoverageConfig(
                        coverage_dir=coverage_dir.name,
                        coverage_id=coverage_id,
                        config_name=config_name,
                        config_data=config_data,
                        config_path=config_path
                    ))
        except Exception as e:
            print(f"Warning: Could not parse {config_path}: {e}", file=sys.stderr)

    return configs


# ==============================================================================
# Per-Coverage Evaluators (28 checks from checklist lines 83-112)
# ==============================================================================

class PerCoverageEvaluator:
    """Evaluates all 28 per-coverage checks for a single configuration."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.inference_registry = self._load_inference_registry()

    def _load_inference_registry(self) -> Set[str]:
        """Load all registered inference function names."""
        functions = set()
        try:
            registry_path = self.project_root / 'signal_architecture' / 'signals' / 'inference' / 'registry.py'
            if registry_path.exists():
                content = registry_path.read_text()
                # Extract function names from @register_inference_function decorators
                matches = re.findall(r"@register_inference_function\(['\"]([^'\"]+)", content)
                functions.update(matches)

            # Also scan coverage-specific inference files
            inference_dir = self.project_root / 'signal_architecture' / 'signals' / 'inference' / 'functions'
            if inference_dir.exists():
                for coverage_dir in inference_dir.iterdir():
                    if coverage_dir.is_dir():
                        signals_file = coverage_dir / 'signals.py'
                        if signals_file.exists():
                            content = signals_file.read_text()
                            matches = re.findall(r'def ([a-z_]+_basefunction)', content)
                            functions.update(matches)
        except Exception:
            pass
        return functions

    def evaluate(self, cfg: CoverageConfig) -> PerCoverageResult:
        """Run all 28 per-coverage checks."""
        results = {}

        # 1. Config parses
        results['config_parses'] = self._check_config_parses(cfg)

        # 2. Validator passes (simplified - checks structure)
        results['validator_passes'] = self._check_validator_passes(cfg)

        # 3. Metadata complete
        results['metadata_complete'] = self._check_metadata_complete(cfg)

        # 4. model_specificity set
        results['model_specificity'] = self._check_model_specificity(cfg)

        # 5. routing_constraints defined
        results['routing_constraints'] = self._check_routing_constraints(cfg)

        # 6. Signal count >= 15
        results['signal_count'] = self._check_signal_count(cfg)

        # 7. Signal IDs unique
        results['signal_ids_unique'] = self._check_signal_ids_unique(cfg)

        # 8. Inference functions exist
        results['inference_functions'] = self._check_inference_functions(cfg)

        # 9. Proxy tiers assigned
        results['proxy_tiers'] = self._check_proxy_tiers(cfg)

        # 10. Three-layer dimensions
        results['three_layer'] = self._check_three_layer_dimensions(cfg)

        # 11. Group IDs match
        results['group_ids_match'] = self._check_group_ids_match(cfg)

        # 12. Risk weights sum to 1.0
        results['risk_weights'] = self._check_risk_weights(cfg)

        # 13. Loss weights sum to 1.0
        results['loss_weights'] = self._check_loss_weights(cfg)

        # 14. Exposure weights sum to 1.0
        results['exposure_weights'] = self._check_exposure_weights(cfg)

        # 15. Risk tier bands correct
        results['risk_tier_bands'] = self._check_risk_tier_bands(cfg)

        # 16. Loss tier bands correct
        results['loss_tier_bands'] = self._check_loss_tier_bands(cfg)

        # 17. Exposure bands correct
        results['exposure_bands'] = self._check_exposure_bands(cfg)

        # 18. Direct queries <= 10
        results['direct_queries'] = self._check_direct_queries(cfg)

        # 19. Query actions valid
        results['query_actions'] = self._check_query_actions(cfg)

        # 20. ILF curve defined
        results['ilf_curve'] = self._check_ilf_curve(cfg)

        # 21. Deductible factors defined
        results['deductible_factors'] = self._check_deductible_factors(cfg)

        # 22. Taxes/fees rate defined
        results['taxes_fees'] = self._check_taxes_fees(cfg)

        # 23. Coverage docs exist
        results['coverage_docs'] = self._check_coverage_docs(cfg)

        # 24. Legacy fields removed
        results['legacy_fields'] = self._check_legacy_fields(cfg)

        # 25. Routing exclusivity (checked at coverage level)
        results['routing_exclusivity'] = self._check_routing_exclusivity(cfg)

        # 26. Dynamic input validation
        results['dynamic_input'] = self._check_dynamic_input(cfg)

        # 27. base_limit_reference in pricing
        results['base_limit_anchor'] = self._check_base_limit_anchor(cfg)

        # 28. base_deductible_reference in pricing
        results['base_deductible_anchor'] = self._check_base_deductible_anchor(cfg)

        return PerCoverageResult(coverage_config=cfg, results=results)

    def _check_config_parses(self, cfg: CoverageConfig) -> CheckResult:
        """Check if config parses without errors."""
        # Already parsed to get here
        return CheckResult(Status.PASS, "Config parses successfully")

    def _check_validator_passes(self, cfg: CoverageConfig) -> CheckResult:
        """Check if config has required structure."""
        required_sections = ['metadata', 'signal_registry', 'groups', 'pricing']
        missing = [s for s in required_sections if s not in cfg.config_data]

        if not missing:
            return CheckResult(Status.PASS, "All required sections present")
        return CheckResult(Status.FAIL, f"Missing sections: {', '.join(missing)}")

    def _check_metadata_complete(self, cfg: CoverageConfig) -> CheckResult:
        """Check metadata completeness."""
        metadata = cfg.config_data.get('metadata', {})
        required = ['name', 'version', 'product_types', 'applicable_markets',
                   'minimum_viable_input', 'min_premium', 'default_currency']
        missing = [f for f in required if f not in metadata]

        if not missing:
            return CheckResult(Status.PASS, "Metadata complete")
        elif len(missing) <= 2:
            return CheckResult(Status.PARTIAL, f"Missing: {', '.join(missing)}")
        return CheckResult(Status.FAIL, f"Missing {len(missing)} fields: {', '.join(missing)}")

    def _check_model_specificity(self, cfg: CoverageConfig) -> CheckResult:
        """Check model_specificity is set (1-5)."""
        metadata = cfg.config_data.get('metadata', {})
        specificity = metadata.get('model_specificity')

        if specificity is None:
            return CheckResult(Status.FAIL, "model_specificity not set")
        if isinstance(specificity, int) and 1 <= specificity <= 5:
            return CheckResult(Status.PASS, f"model_specificity = {specificity}")
        return CheckResult(Status.FAIL, f"Invalid model_specificity: {specificity}")

    def _check_routing_constraints(self, cfg: CoverageConfig) -> CheckResult:
        """Check routing_constraints is defined."""
        metadata = cfg.config_data.get('metadata', {})
        constraints = metadata.get('routing_constraints')

        if constraints is None:
            return CheckResult(Status.FAIL, "routing_constraints not defined")
        if isinstance(constraints, list):
            return CheckResult(Status.PASS, f"{len(constraints)} routing constraint(s)")
        return CheckResult(Status.PARTIAL, "routing_constraints present but invalid format")

    def _check_signal_count(self, cfg: CoverageConfig) -> CheckResult:
        """Check signal count >= 15."""
        signals = cfg.config_data.get('signal_registry', [])
        count = len(signals) if isinstance(signals, list) else 0

        if count >= 15:
            return CheckResult(Status.PASS, f"{count} signals")
        elif count >= 10:
            return CheckResult(Status.PARTIAL, f"Only {count} signals (recommend >= 15)")
        return CheckResult(Status.FAIL, f"Only {count} signals (need >= 15)")

    def _check_signal_ids_unique(self, cfg: CoverageConfig) -> CheckResult:
        """Check signal IDs are unique."""
        signals = cfg.config_data.get('signal_registry', [])
        if not isinstance(signals, list):
            return CheckResult(Status.FAIL, "signal_registry not a list")

        ids = [s.get('id') for s in signals if isinstance(s, dict)]
        duplicates = [id for id in ids if ids.count(id) > 1]

        if not duplicates:
            return CheckResult(Status.PASS, f"{len(ids)} unique signal IDs")
        return CheckResult(Status.FAIL, f"Duplicate IDs: {set(duplicates)}")

    def _check_inference_functions(self, cfg: CoverageConfig) -> CheckResult:
        """Check inference functions exist in registry."""
        signals = cfg.config_data.get('signal_registry', [])
        if not isinstance(signals, list):
            return CheckResult(Status.FAIL, "signal_registry not a list")

        missing = []
        for signal in signals:
            if isinstance(signal, dict):
                func = signal.get('inference_utility_function')
                if func and func not in self.inference_registry:
                    missing.append(func)

        if not missing:
            return CheckResult(Status.PASS, "All inference functions registered")
        elif len(missing) <= 3:
            return CheckResult(Status.PARTIAL, f"Missing {len(missing)}: {', '.join(missing[:3])}")
        return CheckResult(Status.FAIL, f"Missing {len(missing)} functions")

    def _check_proxy_tiers(self, cfg: CoverageConfig) -> CheckResult:
        """Check proxy_tier assigned to signals."""
        signals = cfg.config_data.get('signal_registry', [])
        if not isinstance(signals, list):
            return CheckResult(Status.FAIL, "signal_registry not a list")

        valid_tiers = {'DIRECT_OBSERVABLE', 'INFERRED_PROXY', 'COHORT_INFERENCE'}
        missing = []
        invalid = []

        for signal in signals:
            if isinstance(signal, dict):
                tier = signal.get('proxy_tier')
                if not tier:
                    missing.append(signal.get('id', 'unknown'))
                elif tier not in valid_tiers:
                    invalid.append(f"{signal.get('id')}: {tier}")

        if not missing and not invalid:
            return CheckResult(Status.PASS, "All signals have valid proxy_tier")
        if invalid:
            return CheckResult(Status.FAIL, f"Invalid tiers: {', '.join(invalid[:3])}")
        return CheckResult(Status.PARTIAL, f"{len(missing)} signals missing proxy_tier")

    def _check_three_layer_dimensions(self, cfg: CoverageConfig) -> CheckResult:
        """Check three-layer assessment dimensions exist."""
        groups = cfg.config_data.get('groups', {})
        three_layer = groups.get('three_layer_assessment', [])

        if not three_layer:
            return CheckResult(Status.FAIL, "No three_layer_assessment groups")

        for group in three_layer:
            if isinstance(group, dict):
                if 'risk' not in group or 'loss' not in group or 'exposure' not in group:
                    return CheckResult(Status.PARTIAL, "Some groups missing risk/loss/exposure")

        return CheckResult(Status.PASS, f"{len(three_layer)} three-layer groups")

    def _check_group_ids_match(self, cfg: CoverageConfig) -> CheckResult:
        """Check group_id references match groups section."""
        groups = cfg.config_data.get('groups', {})
        signals = cfg.config_data.get('signal_registry', [])

        # Get all defined group IDs
        defined_groups = set()
        for group_type in ['categorical', 'three_layer_assessment']:
            for group in groups.get(group_type, []):
                if isinstance(group, dict):
                    gid = group.get('group_id') or group.get('id')
                    if gid:
                        defined_groups.add(gid)

        # Check signal group_id references
        missing = []
        for signal in signals:
            if isinstance(signal, dict):
                # Check categories.group_id or scored.group_id
                for section in ['categories', 'scored']:
                    data = signal.get(section, {})
                    if isinstance(data, dict):
                        gid = data.get('group_id')
                        if gid and gid not in defined_groups:
                            missing.append(f"{signal.get('id')}: {gid}")

        if not missing:
            return CheckResult(Status.PASS, "All group_id references valid")
        return CheckResult(Status.FAIL, f"Invalid group refs: {', '.join(missing[:3])}")

    def _check_layer_weights(self, cfg: CoverageConfig, layer: str) -> CheckResult:
        """Generic check for layer weights summing to 1.0."""
        groups = cfg.config_data.get('groups', {})
        three_layer = groups.get('three_layer_assessment', [])

        if not three_layer:
            return CheckResult(Status.FAIL, "No three_layer_assessment groups")

        total = 0.0
        for group in three_layer:
            if isinstance(group, dict):
                layer_data = group.get(layer, {})
                if isinstance(layer_data, dict):
                    total += layer_data.get('weight', 0)

        if abs(total - 1.0) < 0.01:
            return CheckResult(Status.PASS, f"{layer} weights sum to {total:.2f}")
        return CheckResult(Status.FAIL, f"{layer} weights sum to {total:.2f} (expected 1.0)")

    def _check_risk_weights(self, cfg: CoverageConfig) -> CheckResult:
        return self._check_layer_weights(cfg, 'risk')

    def _check_loss_weights(self, cfg: CoverageConfig) -> CheckResult:
        return self._check_layer_weights(cfg, 'loss')

    def _check_exposure_weights(self, cfg: CoverageConfig) -> CheckResult:
        return self._check_layer_weights(cfg, 'exposure')

    def _check_risk_tier_bands(self, cfg: CoverageConfig) -> CheckResult:
        """Check risk tier bands (5 bands, 0-1000)."""
        bands = cfg.config_data.get('risk_tier_bands', [])

        if not bands:
            return CheckResult(Status.FAIL, "No risk_tier_bands defined")
        if len(bands) < 5:
            return CheckResult(Status.PARTIAL, f"Only {len(bands)} bands (expected 5)")
        if len(bands) == 5:
            return CheckResult(Status.PASS, "5 risk tier bands defined")
        return CheckResult(Status.PARTIAL, f"{len(bands)} bands (expected 5)")

    def _check_loss_tier_bands(self, cfg: CoverageConfig) -> CheckResult:
        """Check loss tier bands exist."""
        bands = cfg.config_data.get('loss_tier_bands', [])

        if not bands:
            return CheckResult(Status.FAIL, "No loss_tier_bands defined")
        return CheckResult(Status.PASS, f"{len(bands)} loss tier bands")

    def _check_exposure_bands(self, cfg: CoverageConfig) -> CheckResult:
        """Check exposure bands exist."""
        exposure = cfg.config_data.get('exposure', {})

        size_bands = exposure.get('size_bands', [])
        complexity = exposure.get('complexity', {})

        if not size_bands:
            return CheckResult(Status.FAIL, "No exposure size_bands")
        if not complexity:
            return CheckResult(Status.PARTIAL, "size_bands present, complexity missing")
        return CheckResult(Status.PASS, f"{len(size_bands)} size bands with complexity")

    def _check_direct_queries(self, cfg: CoverageConfig) -> CheckResult:
        """Check direct_queries <= 10."""
        queries = cfg.config_data.get('direct_queries', [])
        count = len(queries) if isinstance(queries, list) else 0

        if count == 0:
            return CheckResult(Status.PASS, "No direct queries (acceptable)")
        elif count <= 10:
            return CheckResult(Status.PASS, f"{count} direct queries")
        return CheckResult(Status.FAIL, f"{count} direct queries (max 10)")

    def _check_query_actions(self, cfg: CoverageConfig) -> CheckResult:
        """Check query actions are valid (FLAG|MODIFIER|REFER)."""
        queries = cfg.config_data.get('direct_queries', [])
        valid_actions = {'FLAG', 'MODIFIER', 'REFER'}
        invalid = []

        for query in queries:
            if isinstance(query, dict):
                conditions = query.get('query_condition', [])
                for cond in conditions:
                    if isinstance(cond, dict):
                        action = cond.get('action')
                        if action and action not in valid_actions:
                            invalid.append(f"{query.get('id')}: {action}")

        if not invalid:
            return CheckResult(Status.PASS, "All query actions valid")
        return CheckResult(Status.FAIL, f"Invalid actions: {', '.join(invalid)}")

    def _check_ilf_curve(self, cfg: CoverageConfig) -> CheckResult:
        """Check ILF curve defined per product type."""
        pricing = cfg.config_data.get('pricing', {})
        by_product = pricing.get('by_product_type', {})
        metadata = cfg.config_data.get('metadata', {})
        product_types = metadata.get('product_types', [])

        if not by_product and not product_types:
            return CheckResult(Status.PARTIAL, "No product types defined")

        missing_ilf = []
        for pt in product_types:
            pt_pricing = by_product.get(pt, {})
            if 'ilf_curve' not in pt_pricing:
                missing_ilf.append(pt)

        if not missing_ilf:
            return CheckResult(Status.PASS, f"ILF curves for {len(product_types)} product types")
        return CheckResult(Status.FAIL, f"Missing ILF: {', '.join(missing_ilf)}")

    def _check_deductible_factors(self, cfg: CoverageConfig) -> CheckResult:
        """Check deductible factors defined per product type."""
        pricing = cfg.config_data.get('pricing', {})
        by_product = pricing.get('by_product_type', {})
        metadata = cfg.config_data.get('metadata', {})
        product_types = metadata.get('product_types', [])

        if not by_product:
            return CheckResult(Status.PARTIAL, "No by_product_type pricing")

        missing = []
        for pt in product_types:
            pt_pricing = by_product.get(pt, {})
            if 'deductible_factors' not in pt_pricing:
                missing.append(pt)

        if not missing:
            return CheckResult(Status.PASS, f"Deductible factors for all product types")
        return CheckResult(Status.FAIL, f"Missing deductible factors: {', '.join(missing)}")

    def _check_taxes_fees(self, cfg: CoverageConfig) -> CheckResult:
        """Check taxes_fees_rate is defined."""
        pricing = cfg.config_data.get('pricing', {})
        rate = pricing.get('taxes_fees_rate')

        if rate is not None:
            return CheckResult(Status.PASS, f"taxes_fees_rate = {rate}")
        return CheckResult(Status.FAIL, "taxes_fees_rate not defined")

    def _check_coverage_docs(self, cfg: CoverageConfig) -> CheckResult:
        """Check logic.md exists for coverage."""
        logic_path = COVERAGES_DIR / cfg.coverage_dir / 'logic.md'

        if logic_path.exists():
            return CheckResult(Status.PASS, f"logic.md exists")
        return CheckResult(Status.FAIL, f"Missing: coverages/{cfg.coverage_dir}/logic.md")

    def _check_legacy_fields(self, cfg: CoverageConfig) -> CheckResult:
        """Check legacy fields are removed."""
        legacy = ['deductible_credits', 'deductible_buy_down_rates']
        found = []

        def check_dict(d, path=""):
            for key, value in d.items():
                if key in legacy:
                    found.append(f"{path}{key}")
                if isinstance(value, dict):
                    check_dict(value, f"{path}{key}.")

        check_dict(cfg.config_data)

        if not found:
            return CheckResult(Status.PASS, "No legacy fields")
        return CheckResult(Status.FAIL, f"Legacy fields: {', '.join(found)}")

    def _check_routing_exclusivity(self, cfg: CoverageConfig) -> CheckResult:
        """Check routing constraints are exclusive (SME vs Corporate)."""
        # This requires comparing with other configs in same coverage
        # For now, check if constraints are defined
        metadata = cfg.config_data.get('metadata', {})
        constraints = metadata.get('routing_constraints', [])

        if not constraints:
            if '_sme' in cfg.config_name:
                return CheckResult(Status.PARTIAL, "SME config should have routing constraints")
            return CheckResult(Status.PASS, "No routing constraints (acceptable for general)")

        return CheckResult(Status.PASS, f"{len(constraints)} routing constraints defined")

    def _check_dynamic_input(self, cfg: CoverageConfig) -> CheckResult:
        """Check routing constraint fields are in minimum_viable_input."""
        metadata = cfg.config_data.get('metadata', {})
        constraints = metadata.get('routing_constraints', [])
        mvi = metadata.get('minimum_viable_input', {})

        if not constraints:
            return CheckResult(Status.PASS, "No routing constraints to validate")

        required_fields = set()
        for c in constraints:
            if isinstance(c, dict) and c.get('required_in_input'):
                required_fields.add(c.get('field'))

        # Check if required fields are in MVI
        mvi_required = mvi.get('required', [])
        mvi_fields = {f.get('field') for f in mvi_required if isinstance(f, dict)}

        missing = required_fields - mvi_fields
        if not missing:
            return CheckResult(Status.PASS, "Routing fields in MVI")
        return CheckResult(Status.PARTIAL, f"Fields not in MVI: {missing}")

    def _check_base_limit_anchor(self, cfg: CoverageConfig) -> CheckResult:
        """Check base_limit_reference exists in pricing."""
        pricing = cfg.config_data.get('pricing', {})
        ref = pricing.get('base_limit_reference')

        if ref is not None:
            return CheckResult(Status.PASS, f"base_limit_reference = {ref}")
        return CheckResult(Status.FAIL, "Missing base_limit_reference in pricing")

    def _check_base_deductible_anchor(self, cfg: CoverageConfig) -> CheckResult:
        """Check base_deductible_reference exists in pricing."""
        pricing = cfg.config_data.get('pricing', {})
        ref = pricing.get('base_deductible_reference')

        if ref is not None:
            return CheckResult(Status.PASS, f"base_deductible_reference = {ref}")
        return CheckResult(Status.FAIL, "Missing base_deductible_reference in pricing")


# ==============================================================================
# Section Evaluators
# ==============================================================================

class SectionEvaluator:
    """Evaluates non-coverage sections of the checklist."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def evaluate_demo(self) -> SectionResult:
        """Evaluate demo/ section."""
        checks = []

        # Demo server exists
        server_path = self.project_root / 'demo' / 'server.py'
        if server_path.exists():
            checks.append(("Demo server exists", CheckResult(Status.PASS, "demo/server.py exists")))
        else:
            checks.append(("Demo server exists", CheckResult(Status.FAIL, "demo/server.py missing")))

        # Index.html exists
        index_path = self.project_root / 'demo' / 'index.html'
        if index_path.exists():
            checks.append(("Index.html exists", CheckResult(Status.PASS, "demo/index.html exists")))
        else:
            checks.append(("Index.html exists", CheckResult(Status.FAIL, "demo/index.html missing")))

        # Examples exist
        examples_dir = self.project_root / 'demo' / 'examples'
        if examples_dir.exists():
            examples = list(examples_dir.glob('run_*.py'))
            if examples:
                checks.append(("Coverage examples exist", CheckResult(Status.PASS, f"{len(examples)} run_*.py examples")))
            else:
                checks.append(("Coverage examples exist", CheckResult(Status.FAIL, "No run_*.py examples")))
        else:
            checks.append(("Coverage examples exist", CheckResult(Status.FAIL, "demo/examples/ missing")))

        return SectionResult("demo", "demo", checks)

    def evaluate_deploy(self) -> SectionResult:
        """Evaluate deploy/ section."""
        checks = []

        # Dockerfile
        dockerfile = self.project_root / 'Dockerfile'
        checks.append(("Dockerfile exists",
            CheckResult(Status.PASS if dockerfile.exists() else Status.FAIL,
                       "Dockerfile exists" if dockerfile.exists() else "Dockerfile missing")))

        # docker-compose.yml
        compose = self.project_root / 'docker-compose.yml'
        checks.append(("docker-compose.yml exists",
            CheckResult(Status.PASS if compose.exists() else Status.FAIL,
                       "docker-compose.yml exists" if compose.exists() else "docker-compose.yml missing")))

        # Kubernetes manifests
        k8s_files = [
            'deployment.yaml', 'service.yaml', 'ingress.yaml', 'configmap.yaml',
            'secrets-template.yaml', 'namespace.yaml', 'kustomization.yaml'
        ]
        k8s_dir = self.project_root / 'deploy' / 'kubernetes'
        for f in k8s_files:
            path = k8s_dir / f
            checks.append((f"K8s {f} exists",
                CheckResult(Status.PASS if path.exists() else Status.FAIL,
                           f"{f} exists" if path.exists() else f"{f} missing")))

        # Prometheus
        prometheus = self.project_root / 'deploy' / 'monitoring' / 'prometheus-config.yaml'
        checks.append(("Prometheus config exists",
            CheckResult(Status.PASS if prometheus.exists() else Status.FAIL,
                       "prometheus-config.yaml exists" if prometheus.exists() else "prometheus-config.yaml missing")))

        # CI/CD
        github_actions = self.project_root / '.github' / 'workflows'
        gitlab_ci = self.project_root / '.gitlab-ci.yml'
        if github_actions.exists() and list(github_actions.glob('*.yml')):
            checks.append(("CI/CD config exists", CheckResult(Status.PASS, "GitHub Actions found")))
        elif gitlab_ci.exists():
            checks.append(("CI/CD config exists", CheckResult(Status.PASS, "GitLab CI found")))
        else:
            checks.append(("CI/CD config exists", CheckResult(Status.FAIL, "No CI/CD config")))

        return SectionResult("deploy", "deploy", checks)

    def evaluate_docs(self) -> SectionResult:
        """Evaluate docs/ section."""
        checks = []

        # Core documentation files
        doc_files = [
            ('Foundational Principles', 'docs/overview/Foundational Principles.md'),
            ('Configuration Architecture', 'docs/overview/Configuration_Architecture.md'),
            ('Premium Calculation Methodology', 'docs/overview/Premium_Calculation_Methodology.md'),
            ('Agent Interaction Spec', 'docs/agent_interaction/dsi_specification.md'),
            ('Whitepaper PDF', 'docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf'),
            ('Vision Paper PDF', 'docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf'),
            ('SKILL.md', 'SKILL.md'),
            ('README.md', 'README.md'),
            ('CHANGELOG.md', 'CHANGELOG.md'),
        ]

        for name, path in doc_files:
            full_path = self.project_root / path
            if full_path.exists():
                checks.append((f"{name} exists", CheckResult(Status.PASS, f"{path} exists")))
            else:
                checks.append((f"{name} exists", CheckResult(Status.FAIL, f"{path} missing")))

        return SectionResult("docs", "docs", checks)

    def evaluate_infrastructure(self) -> SectionResult:
        """Evaluate infrastructure/ section."""
        checks = []

        # API
        api_app = self.project_root / 'infrastructure' / 'api' / 'app.py'
        checks.append(("FastAPI app exists",
            CheckResult(Status.PASS if api_app.exists() else Status.FAIL,
                       "app.py exists" if api_app.exists() else "app.py missing")))

        # DB models
        models = self.project_root / 'infrastructure' / 'db' / 'models.py'
        checks.append(("SQLAlchemy models exist",
            CheckResult(Status.PASS if models.exists() else Status.FAIL,
                       "models.py exists" if models.exists() else "models.py missing")))

        # Alembic
        alembic_dir = self.project_root / 'alembic' / 'versions'
        if alembic_dir.exists():
            migrations = list(alembic_dir.glob('*.py'))
            checks.append(("Alembic migrations exist",
                CheckResult(Status.PASS if migrations else Status.FAIL,
                           f"{len(migrations)} migrations" if migrations else "No migrations")))
        else:
            checks.append(("Alembic migrations exist", CheckResult(Status.FAIL, "alembic/versions/ missing")))

        # Builder CLI
        builder_cli = self.project_root / 'infrastructure' / 'builder' / 'cli.py'
        checks.append(("Builder CLI exists",
            CheckResult(Status.PASS if builder_cli.exists() else Status.FAIL,
                       "cli.py exists" if builder_cli.exists() else "cli.py missing")))

        # Config validator
        validator = self.project_root / 'infrastructure' / 'validation' / 'config_validator.py'
        checks.append(("Config validator exists",
            CheckResult(Status.PASS if validator.exists() else Status.FAIL,
                       "config_validator.py exists" if validator.exists() else "config_validator.py missing")))

        return SectionResult("infrastructure", "infrastructure", checks)

    def evaluate_layers(self) -> SectionResult:
        """Evaluate layers/ section."""
        checks = []

        # Risk layer files
        risk_files = ['workflow.py', 'scorer.py', 'pricer.py', 'config_manager.py',
                     'query_evaluator.py', 'model_data.py', 'types.py']
        for f in risk_files:
            path = self.project_root / 'layers' / 'risk' / f
            checks.append((f"Risk {f} exists",
                CheckResult(Status.PASS if path.exists() else Status.FAIL,
                           f"{f} exists" if path.exists() else f"{f} missing")))

        # Loss layer
        loss_files = ['scorer.py', 'matrix.py', 'config_adapter.py']
        for f in loss_files:
            path = self.project_root / 'layers' / 'loss' / f
            checks.append((f"Loss {f} exists",
                CheckResult(Status.PASS if path.exists() else Status.FAIL,
                           f"{f} exists" if path.exists() else f"{f} missing")))

        # Exposure layer
        exposure_scorer = self.project_root / 'layers' / 'exposure' / 'scorer.py'
        checks.append(("Exposure scorer exists",
            CheckResult(Status.PASS if exposure_scorer.exists() else Status.FAIL,
                       "scorer.py exists" if exposure_scorer.exists() else "scorer.py missing")))

        return SectionResult("layers", "layers", checks)

    def evaluate_rust(self) -> SectionResult:
        """Evaluate rust/ section."""
        checks = []

        rust_dir = self.project_root / 'rust' / 'dsi-core'

        # Cargo.toml
        cargo = rust_dir / 'Cargo.toml'
        if cargo.exists():
            content = cargo.read_text()
            has_pyo3 = 'pyo3' in content.lower()
            checks.append(("Cargo.toml with PyO3",
                CheckResult(Status.PASS if has_pyo3 else Status.PARTIAL,
                           "Cargo.toml with PyO3" if has_pyo3 else "Cargo.toml without PyO3")))
        else:
            checks.append(("Cargo.toml exists", CheckResult(Status.FAIL, "Cargo.toml missing")))

        # Source files
        src_files = ['lib.rs', 'graph.rs', 'derivatives.rs', 'validation.rs']
        src_dir = rust_dir / 'src'
        for f in src_files:
            path = src_dir / f
            checks.append((f"src/{f} exists",
                CheckResult(Status.PASS if path.exists() else Status.FAIL,
                           f"{f} exists" if path.exists() else f"{f} missing")))

        # Benchmarks
        benches_dir = rust_dir / 'benches'
        if benches_dir.exists():
            benches = list(benches_dir.glob('*.rs'))
            checks.append(("Benchmarks exist",
                CheckResult(Status.PASS if benches else Status.FAIL,
                           f"{len(benches)} benchmarks" if benches else "No benchmarks")))
        else:
            checks.append(("Benchmarks exist", CheckResult(Status.FAIL, "benches/ missing")))

        return SectionResult("rust", "rust", checks)

    def evaluate_schemas(self) -> SectionResult:
        """Evaluate schemas/ section."""
        checks = []

        # Organisational graph
        org_graph = self.project_root / 'schemas' / 'organisational_graph.yaml'
        if org_graph.exists():
            checks.append(("organisational_graph.yaml exists", CheckResult(Status.PASS, "File exists")))

            # Check for 6 node and edge types
            try:
                with open(org_graph) as f:
                    schema = yaml.safe_load(f)
                nodes = schema.get('nodes', {})
                edges = schema.get('edges', {})
                checks.append(("6 node types defined",
                    CheckResult(Status.PASS if len(nodes) >= 6 else Status.PARTIAL,
                               f"{len(nodes)} node types")))
                checks.append(("6 edge types defined",
                    CheckResult(Status.PASS if len(edges) >= 6 else Status.PARTIAL,
                               f"{len(edges)} edge types")))
            except Exception as e:
                checks.append(("Schema parseable", CheckResult(Status.FAIL, str(e))))
        else:
            checks.append(("organisational_graph.yaml exists", CheckResult(Status.FAIL, "File missing")))

        # Master config layout
        master = COVERAGES_DIR / 'master_config_layout.yaml'
        checks.append(("master_config_layout.yaml exists",
            CheckResult(Status.PASS if master.exists() else Status.FAIL,
                       "File exists" if master.exists() else "File missing")))

        return SectionResult("schemas", "schemas", checks)

    def evaluate_signal_architecture(self) -> SectionResult:
        """Evaluate signal_architecture/ section."""
        checks = []
        sa_dir = self.project_root / 'signal_architecture'

        # Core types
        types_file = sa_dir / 'signals' / 'types.py'
        if types_file.exists():
            content = types_file.read_text()
            has_signal_type = 'SignalType' in content
            has_extractor_result = 'ExtractorResult' in content
            checks.append(("SignalType defined",
                CheckResult(Status.PASS if has_signal_type else Status.FAIL,
                           "SignalType enum exists" if has_signal_type else "SignalType missing")))
            checks.append(("ExtractorResult defined",
                CheckResult(Status.PASS if has_extractor_result else Status.FAIL,
                           "ExtractorResult exists" if has_extractor_result else "ExtractorResult missing")))
        else:
            checks.append(("types.py exists", CheckResult(Status.FAIL, "types.py missing")))

        # Inference registry
        registry = sa_dir / 'signals' / 'inference' / 'registry.py'
        checks.append(("Inference registry exists",
            CheckResult(Status.PASS if registry.exists() else Status.FAIL,
                       "registry.py exists" if registry.exists() else "registry.py missing")))

        # Discovery engine
        discovery = sa_dir / 'discovery' / 'website_discovery.py'
        checks.append(("Discovery engine exists",
            CheckResult(Status.PASS if discovery.exists() else Status.FAIL,
                       "website_discovery.py exists" if discovery.exists() else "website_discovery.py missing")))

        # Orchestration
        orchestrator = sa_dir / 'orchestration' / 'multi_coverage.py'
        checks.append(("MultiCoverageOrchestrator exists",
            CheckResult(Status.PASS if orchestrator.exists() else Status.FAIL,
                       "multi_coverage.py exists" if orchestrator.exists() else "multi_coverage.py missing")))

        # Multiplexer
        broker = sa_dir / 'multiplexer' / 'broker.py'
        arbiter = sa_dir / 'multiplexer' / 'arbiter.py'
        checks.append(("DSIMultiplexer exists",
            CheckResult(Status.PASS if broker.exists() else Status.FAIL,
                       "broker.py exists" if broker.exists() else "broker.py missing")))
        checks.append(("ConfigArbiter exists",
            CheckResult(Status.PASS if arbiter.exists() else Status.FAIL,
                       "arbiter.py exists" if arbiter.exists() else "arbiter.py missing")))

        # Graph components
        graph_files = ['types.py', 'node_factory.py', 'edge_inferencer.py', 'graph_builder.py']
        graph_dir = sa_dir / 'graph'
        for f in graph_files:
            path = graph_dir / f
            checks.append((f"Graph {f} exists",
                CheckResult(Status.PASS if path.exists() else Status.FAIL,
                           f"{f} exists" if path.exists() else f"{f} missing")))

        return SectionResult("signal_architecture", "signal_architecture", checks)

    def evaluate_tests(self) -> SectionResult:
        """Evaluate tests/ section."""
        checks = []
        tests_dir = self.project_root / 'tests'

        # conftest.py
        conftest = tests_dir / 'conftest.py'
        checks.append(("conftest.py exists",
            CheckResult(Status.PASS if conftest.exists() else Status.FAIL,
                       "conftest.py exists" if conftest.exists() else "conftest.py missing")))

        # README.md
        readme = tests_dir / 'README.md'
        checks.append(("tests/README.md exists",
            CheckResult(Status.PASS if readme.exists() else Status.FAIL,
                       "README.md exists" if readme.exists() else "README.md missing")))

        # pytest configured
        pyproject = self.project_root / 'pyproject.toml'
        pytest_ini = self.project_root / 'pytest.ini'
        if pytest_ini.exists():
            checks.append(("pytest configured", CheckResult(Status.PASS, "pytest.ini exists")))
        elif pyproject.exists() and '[tool.pytest' in pyproject.read_text():
            checks.append(("pytest configured", CheckResult(Status.PASS, "configured in pyproject.toml")))
        else:
            checks.append(("pytest configured", CheckResult(Status.FAIL, "No pytest config")))

        # Test organization
        test_dirs = ['unit', 'integration', 'api', 'performance']
        found_dirs = [d for d in test_dirs if (tests_dir / d).exists()]
        checks.append(("Tests organized by type",
            CheckResult(Status.PASS if len(found_dirs) >= 3 else Status.PARTIAL,
                       f"Found: {', '.join(found_dirs)}")))

        return SectionResult("tests", "tests", checks)


# ==============================================================================
# Report Generator
# ==============================================================================

class ReportGenerator:
    """Generates reports in checklist template format."""

    SECTION_ORDER = [
        ('coverages', 'coverages'),
        ('demo', 'demo'),
        ('deploy', 'deploy'),
        ('docs', 'docs'),
        ('infrastructure', 'infrastructure'),
        ('layers', 'layers'),
        ('rust', 'rust'),
        ('schemas', 'schemas'),
        ('signal_architecture', 'signal_architecture'),
        ('tests', 'tests'),
    ]

    def __init__(self, result: AssessmentResult):
        self.result = result

    def generate_summary(self) -> str:
        """Generate summary matching checklist template."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("DSI CHECKLIST ASSESSMENT REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Metadata
        lines.append(f"Assessment Date: {self.result.timestamp[:10]}")
        lines.append(f"Assessed By: assess.py (Automated - Phase 7.1)")

        stats = self.result.codebase_stats
        lines.append(f"Codebase Stats: {stats.get('python_files', '?')} Python files, "
                    f"{stats.get('lines', '?')} lines, {stats.get('coverages', '?')} coverages, "
                    f"{stats.get('configurations', '?')} configurations")
        lines.append("")

        # Section Scores
        lines.append("Section Scores:")
        max_name_len = max(len(name) for _, name in self.SECTION_ORDER) + 2

        for section_key, display_name in self.SECTION_ORDER:
            section = self.result.sections.get(section_key)
            if section:
                passed = section.passed
                total = section.total
                padding = ' ' * (max_name_len - len(display_name))
                lines.append(f"  {display_name}:{padding}{passed:3d} / {total:3d} items")
            else:
                padding = ' ' * (max_name_len - len(display_name))
                lines.append(f"  {display_name}:{padding}  - /   - items")

        lines.append("")

        # Overall
        total_passed = self.result.total_passed
        total_items = self.result.total_items
        pct = self.result.overall_percentage
        lines.append(f"Overall: {total_passed} / {total_items} items ({pct:.1f}%)")
        lines.append("")

        # Per-Coverage Matrix Summary
        lines.append("Per-Coverage Configuration Status:")
        lines.append("-" * 50)
        for pcr in self.result.per_coverage_results:
            cfg = pcr.coverage_config
            total_checks = len(pcr.results)
            status_icon = "PASS" if pcr.failed == 0 else f"{pcr.failed} FAIL"
            lines.append(f"  {cfg.config_name:25s} {pcr.passed:2d}/{total_checks} checks  [{status_icon}]")
        lines.append("")

        # Top Gaps
        lines.append("Top Gaps:")
        gaps = self._find_top_gaps(5)
        for i, gap in enumerate(gaps, 1):
            lines.append(f"{i}. [{gap['section']}] {gap['check'][:50]}")
            lines.append(f"   -> {gap['message']}")
        if not gaps:
            lines.append("  (No critical gaps identified)")
        lines.append("")

        # Recommended Next Steps
        lines.append("Recommended Next Steps:")
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)

    def generate_detailed(self) -> str:
        """Generate detailed report with per-coverage matrix."""
        lines = []
        lines.append(self.generate_summary())
        lines.append("")
        lines.append("")

        # Per-Coverage Matrix
        lines.append("=" * 70)
        lines.append("PER-COVERAGE VERIFICATION MATRIX")
        lines.append("=" * 70)
        lines.append("")

        # Get all check IDs
        if self.result.per_coverage_results:
            check_ids = list(self.result.per_coverage_results[0].results.keys())

            # Header row
            header = "Check".ljust(25)
            for pcr in self.result.per_coverage_results:
                header += pcr.coverage_config.config_name[:10].center(12)
            lines.append(header)
            lines.append("-" * len(header))

            # Check rows
            for check_id in check_ids:
                row = check_id[:24].ljust(25)
                for pcr in self.result.per_coverage_results:
                    result = pcr.results.get(check_id)
                    if result:
                        status_char = {
                            Status.PASS: "PASS",
                            Status.FAIL: "FAIL",
                            Status.PARTIAL: "PART",
                            Status.NA: "N/A",
                            Status.SKIP: "SKIP"
                        }.get(result.status, "?")
                        row += status_char.center(12)
                    else:
                        row += "?".center(12)
                lines.append(row)

        lines.append("")
        lines.append("")

        # Section Details
        lines.append("=" * 70)
        lines.append("SECTION DETAILS")
        lines.append("=" * 70)

        for section_key, section in self.result.sections.items():
            lines.append("")
            lines.append(f"## {section.display_name.upper()}")
            lines.append(f"   Score: {section.passed}/{section.total} | "
                        f"Pass: {section.passed} | Partial: {section.partial} | Fail: {section.failed}")
            lines.append("")

            # Group by status
            for status in [Status.FAIL, Status.PARTIAL, Status.PASS]:
                items = [(desc, r) for desc, r in section.checks if r.status == status]
                if items:
                    lines.append(f"   [{status.value}]")
                    for desc, result in items[:15]:  # Limit display
                        lines.append(f"     - {desc[:50]}")
                        lines.append(f"       {result.message}")
                    if len(items) > 15:
                        lines.append(f"       ... and {len(items) - 15} more")
                    lines.append("")

            lines.append("-" * 70)

        return '\n'.join(lines)

    def generate_json(self) -> Dict:
        """Generate JSON output."""
        return {
            'timestamp': self.result.timestamp,
            'codebase_stats': self.result.codebase_stats,
            'summary': {
                'total_items': self.result.total_items,
                'total_passed': self.result.total_passed,
                'total_failed': self.result.total_failed,
                'percentage': round(self.result.overall_percentage, 1)
            },
            'sections': {
                key: {
                    'display_name': section.display_name,
                    'total': section.total,
                    'passed': section.passed,
                    'partial': section.partial,
                    'failed': section.failed,
                    'checks': [
                        {
                            'description': desc,
                            'status': r.status.value,
                            'message': r.message,
                            'details': r.details
                        }
                        for desc, r in section.checks
                    ]
                }
                for key, section in self.result.sections.items()
            },
            'per_coverage': [
                {
                    'coverage_dir': pcr.coverage_config.coverage_dir,
                    'config_name': pcr.coverage_config.config_name,
                    'passed': pcr.passed,
                    'failed': pcr.failed,
                    'results': {
                        check_id: {
                            'status': r.status.value,
                            'message': r.message
                        }
                        for check_id, r in pcr.results.items()
                    }
                }
                for pcr in self.result.per_coverage_results
            ],
            'top_gaps': self._find_top_gaps(10),
            'recommendations': self._generate_recommendations()
        }

    def _find_top_gaps(self, limit: int) -> List[Dict]:
        """Find top gaps (failures)."""
        gaps = []

        # From sections
        for section in self.result.sections.values():
            for desc, result in section.checks:
                if result.status == Status.FAIL:
                    gaps.append({
                        'section': section.display_name,
                        'check': desc,
                        'message': result.message,
                        'details': result.details
                    })

        # From per-coverage
        for pcr in self.result.per_coverage_results:
            for check_id, result in pcr.results.items():
                if result.status == Status.FAIL:
                    gaps.append({
                        'section': 'coverages',
                        'check': f"{pcr.coverage_config.config_name}: {check_id}",
                        'message': result.message
                    })

        return gaps[:limit]

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        # Count failures by category
        failures = {}
        for section in self.result.sections.values():
            fail_count = section.failed
            if fail_count > 0:
                failures[section.display_name] = fail_count

        # Per-coverage failures
        coverage_failures = sum(pcr.failed for pcr in self.result.per_coverage_results)
        if coverage_failures > 0:
            failures['coverage configs'] = coverage_failures

        # Sort by failure count
        sorted_failures = sorted(failures.items(), key=lambda x: -x[1])

        for section_name, count in sorted_failures[:3]:
            recommendations.append(f"Address {count} failing checks in {section_name}")

        # Add generic if few
        if len(recommendations) < 3:
            recommendations.append("Run full test suite to validate implementations")
            recommendations.append("Review (Manual) checklist items requiring human verification")

        return recommendations[:5]


# ==============================================================================
# Main Assessor
# ==============================================================================

class ChecklistAssessor:
    """Main assessment orchestrator."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.per_coverage_evaluator = PerCoverageEvaluator(project_root)
        self.section_evaluator = SectionEvaluator(project_root)

    def run(self, section_filter: Optional[str] = None,
            coverage_filter: Optional[str] = None) -> AssessmentResult:
        """Run full assessment."""

        # Load all coverage configs
        configs = load_all_coverage_configs()

        # Filter if requested
        if coverage_filter:
            configs = [c for c in configs if coverage_filter.lower() in c.config_name.lower()]

        # Run per-coverage evaluations
        per_coverage_results = []
        for cfg in configs:
            result = self.per_coverage_evaluator.evaluate(cfg)
            per_coverage_results.append(result)

        # Run section evaluations
        sections = {}

        # Coverages section - aggregate per-coverage results
        coverage_checks = []
        for pcr in per_coverage_results:
            for check_id, result in pcr.results.items():
                coverage_checks.append(
                    (f"{pcr.coverage_config.config_name}: {check_id}", result)
                )
        sections['coverages'] = SectionResult('coverages', 'coverages', coverage_checks)

        # Other sections
        if not section_filter or 'demo' in section_filter:
            sections['demo'] = self.section_evaluator.evaluate_demo()
        if not section_filter or 'deploy' in section_filter:
            sections['deploy'] = self.section_evaluator.evaluate_deploy()
        if not section_filter or 'docs' in section_filter:
            sections['docs'] = self.section_evaluator.evaluate_docs()
        if not section_filter or 'infrastructure' in section_filter:
            sections['infrastructure'] = self.section_evaluator.evaluate_infrastructure()
        if not section_filter or 'layers' in section_filter:
            sections['layers'] = self.section_evaluator.evaluate_layers()
        if not section_filter or 'rust' in section_filter:
            sections['rust'] = self.section_evaluator.evaluate_rust()
        if not section_filter or 'schemas' in section_filter:
            sections['schemas'] = self.section_evaluator.evaluate_schemas()
        if not section_filter or 'signal' in section_filter:
            sections['signal_architecture'] = self.section_evaluator.evaluate_signal_architecture()
        if not section_filter or 'tests' in section_filter:
            sections['tests'] = self.section_evaluator.evaluate_tests()

        # Gather codebase stats
        stats = self._gather_codebase_stats(configs)

        return AssessmentResult(
            timestamp=datetime.now().isoformat(),
            sections=sections,
            per_coverage_results=per_coverage_results,
            codebase_stats=stats
        )

    def _gather_codebase_stats(self, configs: List[CoverageConfig]) -> Dict[str, int]:
        """Gather codebase statistics."""
        stats = {
            'python_files': 0,
            'lines': 0,
            'coverages': len(set(c.coverage_dir for c in configs)),
            'configurations': len(configs)
        }

        # Count Python files
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' not in str(py_file) and '.venv' not in str(py_file):
                stats['python_files'] += 1
                try:
                    stats['lines'] += len(py_file.read_text().splitlines())
                except:
                    pass

        return stats


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='DSI Comprehensive Checklist Assessment Tool (Phase 7.1)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python assess.py                          # Full assessment
  python assess.py --section coverages      # Specific section
  python assess.py --coverage cyber         # Filter to cyber configs
  python assess.py --detailed               # Full detail output
  python assess.py --json                   # JSON output
  python assess.py --save                   # Save to results/
        """
    )

    parser.add_argument('--section', '-s',
                       help='Filter to specific section')
    parser.add_argument('--coverage', '-c',
                       help='Filter to specific coverage')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Show detailed output with matrix')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output JSON format')
    parser.add_argument('--save', action='store_true',
                       help='Save report to results/')
    parser.add_argument('--project-root',
                       help='Project root (auto-detected)')

    args = parser.parse_args()

    # Determine project root
    project_root = Path(args.project_root) if args.project_root else PROJECT_ROOT

    # Run assessment
    assessor = ChecklistAssessor(project_root)
    result = assessor.run(
        section_filter=args.section,
        coverage_filter=args.coverage
    )

    # Generate output
    generator = ReportGenerator(result)

    if args.json:
        output = json.dumps(generator.generate_json(), indent=2)
    elif args.detailed:
        output = generator.generate_detailed()
    else:
        output = generator.generate_summary()

    print(output)

    # Save if requested
    if args.save:
        results_dir = project_root / 'development' / 'project' / 'assessments' / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')

        if args.json:
            report_path = results_dir / f'assessment_{date_str}.json'
        else:
            report_path = results_dir / f'assessment_{date_str}.md'

        report_path.write_text(output)
        print(f"\nReport saved to: {report_path}")

    # Exit code based on failures
    if result.total_failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
