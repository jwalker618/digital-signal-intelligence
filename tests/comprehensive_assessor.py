#!/usr/bin/env python3
"""
DSI Comprehensive Project Assessor
===================================

A unified assessment framework that validates the DSI project against:
1. Configuration compliance (Phase 5 schema, pricing anchors, weights)
2. Project structure (required files, directories, documentation)
3. Cross-coverage consistency (structural patterns, signal reuse)
4. Inference function registry (all referenced functions exist)
5. Test infrastructure status (import checks, test collection)
6. Documentation completeness

Usage:
    python tests/comprehensive_assessor.py                    # Full assessment
    python tests/comprehensive_assessor.py --config-only      # Config assessment only
    python tests/comprehensive_assessor.py --structure-only   # Structure assessment only
    python tests/comprehensive_assessor.py --json             # JSON output
    python tests/comprehensive_assessor.py --coverage cyber   # Specific coverage

Version: 1.0.0
Date: February 2026
"""

import yaml
import json
import sys
import os
import importlib
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class Severity(Enum):
    """Assessment result severity levels."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class AssessmentResult:
    """Single assessment result."""
    category: str
    test_name: str
    severity: Severity
    message: str
    details: Optional[str] = None
    config_name: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "test": self.test_name,
            "status": self.severity.value,
            "message": self.message,
            "details": self.details,
            "config": self.config_name
        }


@dataclass
class CategorySummary:
    """Summary for an assessment category."""
    name: str
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def total(self) -> int:
        return self.passed + self.warnings + self.failed + self.skipped

    @property
    def score(self) -> float:
        if self.total == 0:
            return 0.0
        # Warnings count as half-pass
        return ((self.passed + self.warnings * 0.5) / self.total) * 100


@dataclass
class AssessmentReport:
    """Complete assessment report."""
    timestamp: str
    project_root: str
    results: List[AssessmentResult] = field(default_factory=list)
    summaries: Dict[str, CategorySummary] = field(default_factory=dict)

    def add_result(self, result: AssessmentResult):
        self.results.append(result)

        # Update summary
        if result.category not in self.summaries:
            self.summaries[result.category] = CategorySummary(name=result.category)

        summary = self.summaries[result.category]
        if result.severity == Severity.PASS:
            summary.passed += 1
        elif result.severity == Severity.WARNING:
            summary.warnings += 1
        elif result.severity == Severity.FAIL:
            summary.failed += 1
        else:
            summary.skipped += 1

    @property
    def overall_score(self) -> float:
        total_passed = sum(s.passed for s in self.summaries.values())
        total_warnings = sum(s.warnings for s in self.summaries.values())
        total_tests = sum(s.total for s in self.summaries.values())
        if total_tests == 0:
            return 0.0
        return ((total_passed + total_warnings * 0.5) / total_tests) * 100

    @property
    def total_failures(self) -> int:
        return sum(s.failed for s in self.summaries.values())

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "project_root": self.project_root,
            "overall_score": round(self.overall_score, 1),
            "total_failures": self.total_failures,
            "summaries": {k: asdict(v) for k, v in self.summaries.items()},
            "results": [r.to_dict() for r in self.results]
        }


class DSIComprehensiveAssessor:
    """
    Comprehensive DSI project assessor.

    Categories:
    - CONFIG: Configuration compliance (Phase 5 schema, pricing, weights)
    - STRUCTURE: Project structure (files, directories, organization)
    - CONSISTENCY: Cross-coverage consistency (patterns, signals)
    - REGISTRY: Inference function registry validation
    - TESTS: Test infrastructure status
    - DOCS: Documentation completeness
    """

    CATEGORIES = {
        "CONFIG": "Configuration Compliance",
        "STRUCTURE": "Project Structure",
        "CONSISTENCY": "Cross-Coverage Consistency",
        "REGISTRY": "Inference Registry",
        "TESTS": "Test Infrastructure",
        "DOCS": "Documentation"
    }

    # Required top-level directories
    REQUIRED_DIRECTORIES = [
        "coverages",
        "layers",
        "signal_architecture",
        "infrastructure",
        "tests",
        "docs",
        "schemas"
    ]

    # Required coverage directories
    COVERAGE_DIRS = ["aerospace", "cyber", "do", "energy", "fi", "marine", "pi"]

    # Required files per coverage
    COVERAGE_REQUIRED_FILES = ["config.yaml"]

    # Required documentation files
    REQUIRED_DOCS = [
        "docs/overview/Premium_Calculation_Methodology.md",
        "docs/overview/Configuration_Architecture.md",
        "docs/overview/Foundational Principles.md",
        "development/project/version/project_completeness_checklist.md",
        "coverages/master_config_layout.yaml"
    ]

    def __init__(self, project_root: str = None):
        """Initialize assessor with project root path."""
        self.project_root = Path(project_root or self._find_project_root())
        self.report = AssessmentReport(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root)
        )
        self._coverage_configs: Dict[str, Dict] = {}

    def _find_project_root(self) -> Path:
        """Find project root by looking for characteristic files."""
        current = Path.cwd()
        while current != current.parent:
            if (current / "coverages").exists() and (current / "layers").exists():
                return current
            current = current.parent
        return Path.cwd()

    def _add_result(self, category: str, test_name: str, passed: bool,
                   message: str, details: str = None, config_name: str = None,
                   warning: bool = False):
        """Helper to add assessment result."""
        if passed:
            severity = Severity.PASS
        elif warning:
            severity = Severity.WARNING
        else:
            severity = Severity.FAIL

        self.report.add_result(AssessmentResult(
            category=category,
            test_name=test_name,
            severity=severity,
            message=message,
            details=details,
            config_name=config_name
        ))

    def _load_coverage_configs(self):
        """Load all coverage configuration files."""
        coverages_dir = self.project_root / "coverages"
        for coverage_name in self.COVERAGE_DIRS:
            config_path = coverages_dir / coverage_name / "config.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        self._coverage_configs[coverage_name] = yaml.safe_load(f)
                except Exception as e:
                    self._coverage_configs[coverage_name] = {"_error": str(e)}

    # =========================================================================
    # STRUCTURE ASSESSMENTS
    # =========================================================================

    def assess_project_structure(self):
        """Assess project directory structure."""
        # Check required directories
        for dir_name in self.REQUIRED_DIRECTORIES:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            self._add_result(
                "STRUCTURE", f"Directory: {dir_name}",
                exists,
                f"Required directory '{dir_name}' exists" if exists else f"Missing required directory: {dir_name}"
            )

        # Check coverage directories
        coverages_dir = self.project_root / "coverages"
        for coverage in self.COVERAGE_DIRS:
            coverage_dir = coverages_dir / coverage
            exists = coverage_dir.exists() and coverage_dir.is_dir()
            self._add_result(
                "STRUCTURE", f"Coverage: {coverage}",
                exists,
                f"Coverage '{coverage}' directory exists" if exists else f"Missing coverage directory: {coverage}"
            )

            if exists:
                # Check required files within coverage
                for req_file in self.COVERAGE_REQUIRED_FILES:
                    file_path = coverage_dir / req_file
                    file_exists = file_path.exists()
                    self._add_result(
                        "STRUCTURE", f"Coverage File: {coverage}/{req_file}",
                        file_exists,
                        f"Required file exists" if file_exists else f"Missing: {coverage}/{req_file}",
                        config_name=coverage
                    )

        # Check required documentation
        for doc_path in self.REQUIRED_DOCS:
            full_path = self.project_root / doc_path
            exists = full_path.exists()
            self._add_result(
                "STRUCTURE", f"Doc: {doc_path}",
                exists,
                f"Documentation exists" if exists else f"Missing documentation: {doc_path}"
            )

        # Check master config layout
        master_layout = self.project_root / "coverages" / "master_config_layout.yaml"
        if master_layout.exists():
            with open(master_layout) as f:
                content = f.read()
            has_limit_config = "limit_configuration:" in content
            has_limit_bandings = "limit_bandings:" in content and "# OPTION A: BUNDLED" in content

            self._add_result(
                "STRUCTURE", "Master Layout: limit_configuration",
                has_limit_config and not has_limit_bandings,
                "Master layout uses limit_configuration only" if has_limit_config and not has_limit_bandings
                else "Master layout should use limit_configuration only (remove BUNDLED option)"
            )

    # =========================================================================
    # CONFIGURATION ASSESSMENTS
    # =========================================================================

    def assess_configuration_compliance(self):
        """Assess all coverage configurations for Phase 5 compliance."""
        if not self._coverage_configs:
            self._load_coverage_configs()

        for coverage_name, yaml_data in self._coverage_configs.items():
            if "_error" in yaml_data:
                self._add_result(
                    "CONFIG", "YAML Parse",
                    False,
                    f"Failed to parse config",
                    details=yaml_data["_error"],
                    config_name=coverage_name
                )
                continue

            # Navigate nested structure: yaml_data = {coverage_key: {config1: {...}, config2: {...}}}
            # Find the coverage-level key (e.g., "cyber", "energy")
            coverage_keys = [k for k in yaml_data.keys() if isinstance(yaml_data.get(k), dict)]
            if not coverage_keys:
                self._add_result(
                    "CONFIG", "Structure",
                    False,
                    f"No coverage structure found",
                    config_name=coverage_name
                )
                continue

            # Use the first coverage key (should be only one)
            coverage_key = coverage_keys[0]
            coverage_data = yaml_data[coverage_key]

            # Get all configuration names within coverage (e.g., "cyber_general", "cyber_sme")
            configs = [k for k in coverage_data.keys() if isinstance(coverage_data.get(k), dict)]

            # Cross-configuration test: routing exclusivity
            self._test_routing_exclusivity(coverage_name, coverage_data, configs)

            # Per-configuration tests
            for config_name in configs:
                config = coverage_data[config_name]
                self._test_schema_version(config_name, config)
                self._test_weights_sum(config_name, config)
                self._test_pricing_anchors(config_name, config)
                self._test_deprecation_rules(config_name, config)
                self._test_premium_methodology(config_name, config)
                self._test_monotonicity(config_name, config)
                self._test_limit_configuration(config_name, config)
                self._test_signal_count(config_name, config)
                self._test_metadata_completeness(config_name, config)

    def _test_routing_exclusivity(self, coverage_name: str, coverage_data: Dict, configs: List[str]):
        """Test that configs within a coverage have mutually exclusive routing."""
        routing_maps = {}
        for c in configs:
            config = coverage_data.get(c, {})
            constraints = config.get('metadata', {}).get('routing_constraints', [])
            for req in constraints:
                field = req.get('field')
                if field:
                    routing_maps.setdefault(field, []).append((c, req.get('operator'), req.get('value')))

        for field, rules in routing_maps.items():
            if len(rules) > 1:
                operators = [r[1] for r in rules]
                has_ceiling = any(op in ['<', '<='] for op in operators)
                has_floor = any(op in ['>', '>='] for op in operators)

                self._add_result(
                    "CONFIG", f"Routing Exclusivity: {field}",
                    has_ceiling and has_floor,
                    f"Mutually exclusive routing on '{field}'" if has_ceiling and has_floor
                    else f"Potential Arbiter collision on '{field}'",
                    details=str(rules) if not (has_ceiling and has_floor) else None,
                    config_name=coverage_name
                )

    def _test_schema_version(self, config_name: str, config: Dict):
        """Test schema version is >= 2.2.0."""
        version = config.get('metadata', {}).get('version', '0.0.0')
        try:
            parts = version.split('.')
            major, minor = int(parts[0]), int(parts[1])
            is_compliant = major >= 2 and minor >= 2
        except (ValueError, IndexError):
            is_compliant = False

        self._add_result(
            "CONFIG", "Schema Version",
            is_compliant,
            f"Version {version} is Phase 5 compliant" if is_compliant
            else f"Version {version} below requirement (>= 2.2.0)",
            config_name=config_name
        )

    def _test_weights_sum(self, config_name: str, config: Dict):
        """Test that weights sum to 1.0 for each dimension."""
        groups = config.get('groups', {}).get('three_layer_assessment', [])

        totals = {'risk': 0.0, 'loss': 0.0, 'exposure': 0.0}
        for g in groups:
            totals['risk'] += g.get('risk', {}).get('weight', 0.0)
            totals['loss'] += g.get('loss', {}).get('weight', 0.0)
            totals['exposure'] += g.get('exposure', {}).get('weight', 0.0)

        for dim, total in totals.items():
            is_one = abs(total - 1.0) < 0.01
            self._add_result(
                "CONFIG", f"Weights Sum ({dim})",
                is_one,
                f"{dim} weights sum to {total:.2f}" if is_one
                else f"{dim} weights sum to {total:.2f}, expected 1.0",
                config_name=config_name
            )

    def _test_pricing_anchors(self, config_name: str, config: Dict):
        """Test pricing anchors are defined and normalized."""
        pricing = config.get('pricing', {})
        products = pricing.get('by_product_type', {})

        for prod_name, p_data in products.items():
            base_limit = p_data.get('base_limit_reference')
            base_deductible = p_data.get('base_deductible_reference')

            # Anchors exist
            self._add_result(
                "CONFIG", f"Anchors: {prod_name}",
                bool(base_limit and base_deductible),
                f"Anchors defined for {prod_name}" if base_limit and base_deductible
                else f"Missing anchors in {prod_name}",
                config_name=config_name
            )

            # ILF anchor = 1.0
            ilf_factors = p_data.get('ilf_curve', {}).get('factors', [])
            ilf_anchor = next((f['factor'] for f in ilf_factors if f.get('limit') == base_limit), None)
            self._add_result(
                "CONFIG", f"ILF Anchor: {prod_name}",
                ilf_anchor == 1.0,
                f"ILF at {base_limit} = 1.0" if ilf_anchor == 1.0
                else f"ILF at {base_limit} = {ilf_anchor}, expected 1.0",
                config_name=config_name
            )

            # Deductible anchor = 1.0
            ded_factors = p_data.get('deductible_factors', [])
            ded_anchor = next((f['factor'] for f in ded_factors if f.get('deductible') == base_deductible), None)
            self._add_result(
                "CONFIG", f"Deductible Anchor: {prod_name}",
                ded_anchor == 1.0,
                f"Deductible factor at {base_deductible} = 1.0" if ded_anchor == 1.0
                else f"Deductible factor at {base_deductible} = {ded_anchor}, expected 1.0",
                config_name=config_name
            )

    def _test_deprecation_rules(self, config_name: str, config: Dict):
        """Test legacy fields are removed."""
        products = config.get('pricing', {}).get('by_product_type', {})
        for prod_name, p_data in products.items():
            has_legacy = 'deductible_credits' in p_data or 'deductible_buy_down_rates' in p_data
            self._add_result(
                "CONFIG", f"Deprecation: {prod_name}",
                not has_legacy,
                f"No legacy fields in {prod_name}" if not has_legacy
                else f"Found deprecated fields in {prod_name}",
                config_name=config_name
            )

    def _test_premium_methodology(self, config_name: str, config: Dict):
        """Test premium methodology is appropriate."""
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if not bands:
            return

        method = bands[0].get('interpretation', {}).get('application', {}).get('method')
        constraints = config.get('metadata', {}).get('routing_constraints', [])
        has_ceiling = any(c.get('operator') in ['<', '<='] for c in constraints)

        if method == "PREMIUM_BASE":
            self._add_result(
                "CONFIG", "Scalability Trap",
                has_ceiling,
                "PREMIUM_BASE safely constrained" if has_ceiling
                else "PREMIUM_BASE without routing ceiling - Scalability Trap risk",
                config_name=config_name
            )
        elif method == "MULTIPLIER":
            basis = bands[0].get('interpretation', {}).get('application', {}).get('basis')
            mvi = config.get('metadata', {}).get('minimum_viable_input', {}).get('required', [])
            mvi_fields = [f.get('field') for f in mvi]

            self._add_result(
                "CONFIG", "Multiplier Basis",
                basis in mvi_fields,
                f"Basis '{basis}' in MVI" if basis in mvi_fields
                else f"Basis '{basis}' missing from minimum_viable_input",
                config_name=config_name
            )

    def _test_monotonicity(self, config_name: str, config: Dict):
        """Test tier pricing is monotonic."""
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if not bands or len(bands) < 5:
            return

        method = bands[0].get('interpretation', {}).get('application', {}).get('method')
        key = 'value' if method == 'PREMIUM_BASE' else 'applied'

        try:
            sorted_bands = sorted(bands, key=lambda x: x['id'])
            prices = [b['interpretation']['application'][key] for b in sorted_bands]

            is_monotonic = all(prices[i] < prices[i+1] for i in range(len(prices)-1))
            self._add_result(
                "CONFIG", "Actuarial Monotonicity",
                is_monotonic,
                "Pricing strictly increases with tier" if is_monotonic
                else f"Non-monotonic pricing: {prices}",
                config_name=config_name
            )

            ratio = prices[-1] / prices[0] if prices[0] > 0 else 0
            self._add_result(
                "CONFIG", "Penalty Ratio",
                ratio >= 2.0,
                f"Tier 5/Tier 1 ratio = {ratio:.2f}x" if ratio >= 2.0
                else f"Penalty ratio {ratio:.2f}x < 2.0x required",
                config_name=config_name
            )
        except (KeyError, TypeError):
            self._add_result(
                "CONFIG", "Actuarial Monotonicity",
                False,
                "Malformed tier band data",
                config_name=config_name
            )

    def _test_limit_configuration(self, config_name: str, config: Dict):
        """Test limit_configuration structure."""
        limit_config = config.get('limit_configuration')
        limit_bandings = config.get('limit_bandings')

        if limit_bandings:
            self._add_result(
                "CONFIG", "Limit Configuration",
                False,
                "Uses legacy limit_bandings - should use limit_configuration",
                config_name=config_name
            )
        elif limit_config:
            has_type = limit_config.get('type') == 'DECOUPLED'
            has_limits = bool(limit_config.get('valid_limits'))
            has_deductibles = bool(limit_config.get('valid_deductibles'))

            self._add_result(
                "CONFIG", "Limit Configuration",
                has_type and has_limits and has_deductibles,
                "Valid limit_configuration structure" if has_type and has_limits and has_deductibles
                else "Incomplete limit_configuration",
                config_name=config_name
            )
        else:
            self._add_result(
                "CONFIG", "Limit Configuration",
                False,
                "Missing limit_configuration",
                config_name=config_name,
                warning=True
            )

    def _test_signal_count(self, config_name: str, config: Dict):
        """Test signal registry has adequate signals."""
        signals = config.get('signal_registry', [])
        count = len(signals)

        self._add_result(
            "CONFIG", "Signal Count",
            count >= 10,
            f"{count} signals defined" if count >= 10
            else f"Only {count} signals (recommend >= 10)",
            config_name=config_name,
            warning=count < 10 and count > 0
        )

    def _test_metadata_completeness(self, config_name: str, config: Dict):
        """Test metadata section completeness."""
        metadata = config.get('metadata', {})
        required_fields = ['name', 'version', 'product_types', 'minimum_viable_input', 'min_premium', 'default_currency']

        missing = [f for f in required_fields if not metadata.get(f)]

        self._add_result(
            "CONFIG", "Metadata Completeness",
            len(missing) == 0,
            "All required metadata fields present" if not missing
            else f"Missing metadata: {', '.join(missing)}",
            config_name=config_name
        )

    # =========================================================================
    # CONSISTENCY ASSESSMENTS
    # =========================================================================

    def assess_cross_coverage_consistency(self):
        """Assess consistency across all coverages."""
        if not self._coverage_configs:
            self._load_coverage_configs()

        # Collect structural info from each config
        structures = {}
        for coverage_name, yaml_data in self._coverage_configs.items():
            if "_error" in yaml_data:
                continue

            # Navigate nested structure
            coverage_keys = [k for k in yaml_data.keys() if isinstance(yaml_data.get(k), dict)]
            if not coverage_keys:
                continue
            coverage_data = yaml_data[coverage_keys[0]]

            configs = [k for k in coverage_data.keys() if isinstance(coverage_data.get(k), dict)]
            for config_name in configs:
                config = coverage_data[config_name]
                structures[f"{coverage_name}/{config_name}"] = {
                    "has_direct_queries": bool(config.get('direct_queries')),
                    "has_signal_registry": bool(config.get('signal_registry')),
                    "has_groups": bool(config.get('groups')),
                    "has_risk_bands": bool(config.get('risk_tier_bands')),
                    "has_loss_bands": bool(config.get('loss_tier_bands')),
                    "has_exposure": bool(config.get('exposure')),
                    "has_pricing": bool(config.get('pricing')),
                    "has_limit_config": bool(config.get('limit_configuration')),
                }

        # Check all configs have same structure
        if structures:
            reference = list(structures.values())[0]
            all_match = all(s == reference for s in structures.values())

            self._add_result(
                "CONSISTENCY", "Structural Pattern",
                all_match,
                "All configurations follow identical structure" if all_match
                else "Structural inconsistency across configurations",
                details=None if all_match else str({k: v for k, v in structures.items() if v != reference})
            )

        # Check version consistency
        versions = set()
        for coverage_name, yaml_data in self._coverage_configs.items():
            if "_error" in yaml_data:
                continue
            # Navigate nested structure
            coverage_keys = [k for k in yaml_data.keys() if isinstance(yaml_data.get(k), dict)]
            if not coverage_keys:
                continue
            coverage_data = yaml_data[coverage_keys[0]]

            configs = [k for k in coverage_data.keys() if isinstance(coverage_data.get(k), dict)]
            for config_name in configs:
                version = coverage_data[config_name].get('metadata', {}).get('version', 'unknown')
                versions.add(version)

        self._add_result(
            "CONSISTENCY", "Version Alignment",
            len(versions) <= 1,
            f"All configs use version {list(versions)[0]}" if len(versions) == 1
            else f"Multiple versions in use: {versions}",
            warning=len(versions) > 1
        )

    # =========================================================================
    # REGISTRY ASSESSMENTS
    # =========================================================================

    def assess_inference_registry(self):
        """Assess inference function registry completeness."""
        # Try to import and check registry
        try:
            sys.path.insert(0, str(self.project_root))
            from signal_architecture.signals.inference.registry import get_inference_function, list_inference_functions

            registered_functions = list_inference_functions()

            self._add_result(
                "REGISTRY", "Registry Import",
                True,
                f"Registry loaded with {len(registered_functions)} functions"
            )

            # Check that all referenced functions exist
            if not self._coverage_configs:
                self._load_coverage_configs()

            all_referenced = set()
            for coverage_name, yaml_data in self._coverage_configs.items():
                if "_error" in yaml_data:
                    continue
                # Navigate nested structure
                coverage_keys = [k for k in yaml_data.keys() if isinstance(yaml_data.get(k), dict)]
                if not coverage_keys:
                    continue
                coverage_data = yaml_data[coverage_keys[0]]

                configs = [k for k in coverage_data.keys() if isinstance(coverage_data.get(k), dict)]
                for config_name in configs:
                    signals = coverage_data[config_name].get('signal_registry', [])
                    for signal in signals:
                        func_name = signal.get('inference_utility_function')
                        if func_name:
                            all_referenced.add(func_name)

            missing_funcs = [f for f in all_referenced if f not in registered_functions]

            self._add_result(
                "REGISTRY", "Function Coverage",
                len(missing_funcs) == 0,
                f"All {len(all_referenced)} referenced functions exist" if not missing_funcs
                else f"Missing {len(missing_funcs)} functions: {missing_funcs[:5]}{'...' if len(missing_funcs) > 5 else ''}"
            )

        except ImportError as e:
            self._add_result(
                "REGISTRY", "Registry Import",
                False,
                f"Cannot import registry: {e}",
                warning=True
            )
        except Exception as e:
            self._add_result(
                "REGISTRY", "Registry Check",
                False,
                f"Error checking registry: {e}",
                warning=True
            )

    # =========================================================================
    # TEST INFRASTRUCTURE ASSESSMENTS
    # =========================================================================

    def assess_test_infrastructure(self):
        """Assess test infrastructure status."""
        tests_dir = self.project_root / "tests"

        # Check test directories exist
        test_subdirs = ["unit", "integration", "api", "performance"]
        for subdir in test_subdirs:
            path = tests_dir / subdir
            exists = path.exists()
            self._add_result(
                "TESTS", f"Directory: tests/{subdir}",
                exists,
                f"Test directory exists" if exists else f"Missing tests/{subdir}",
                warning=not exists
            )

        # Check conftest.py
        conftest = tests_dir / "conftest.py"
        self._add_result(
            "TESTS", "conftest.py",
            conftest.exists(),
            "Shared fixtures available" if conftest.exists() else "Missing conftest.py"
        )

        # Try to collect tests
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q", str(tests_dir)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60
            )

            # Parse output
            lines = result.stdout.strip().split('\n')
            test_count = 0
            error_count = 0

            for line in lines:
                if 'test' in line.lower() and '::' in line:
                    test_count += 1
                if 'error' in line.lower():
                    error_count += 1

            # Look for summary line
            for line in lines[-5:]:
                if 'selected' in line or 'collected' in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p.isdigit():
                            test_count = int(p)
                            break
                if 'error' in line:
                    for p in line.split():
                        if p.isdigit():
                            error_count = int(p)
                            break

            self._add_result(
                "TESTS", "Test Collection",
                test_count > 0,
                f"{test_count} tests collected" if test_count > 0 else "No tests found"
            )

            if error_count > 0:
                self._add_result(
                    "TESTS", "Collection Errors",
                    False,
                    f"{error_count} collection errors",
                    details=result.stderr[:500] if result.stderr else None,
                    warning=True
                )

        except subprocess.TimeoutExpired:
            self._add_result(
                "TESTS", "Test Collection",
                False,
                "Test collection timed out",
                warning=True
            )
        except Exception as e:
            self._add_result(
                "TESTS", "Test Collection",
                False,
                f"Cannot collect tests: {e}",
                warning=True
            )

    # =========================================================================
    # DOCUMENTATION ASSESSMENTS
    # =========================================================================

    def assess_documentation(self):
        """Assess documentation completeness."""
        docs_dir = self.project_root / "docs"

        # Check for logic.md in each coverage
        coverages_dir = self.project_root / "coverages"
        for coverage in self.COVERAGE_DIRS:
            logic_md = coverages_dir / coverage / "logic.md"
            self._add_result(
                "DOCS", f"Coverage Logic: {coverage}",
                logic_md.exists(),
                "logic.md exists" if logic_md.exists() else "Missing logic.md",
                config_name=coverage,
                warning=not logic_md.exists()
            )

        # Check key documentation files
        key_docs = {
            "README.md": self.project_root / "README.md",
            "SKILL.md": self.project_root / "SKILL.md",
            "CHANGELOG.md": self.project_root / "CHANGELOG.md",
        }

        for doc_name, doc_path in key_docs.items():
            self._add_result(
                "DOCS", f"Root: {doc_name}",
                doc_path.exists(),
                f"{doc_name} exists" if doc_path.exists() else f"Missing {doc_name}",
                warning=not doc_path.exists()
            )

    # =========================================================================
    # MAIN ASSESSMENT RUNNER
    # =========================================================================

    def run_full_assessment(self):
        """Run all assessment categories."""
        self.assess_project_structure()
        self.assess_configuration_compliance()
        self.assess_cross_coverage_consistency()
        self.assess_inference_registry()
        self.assess_test_infrastructure()
        self.assess_documentation()
        return self.report

    def run_config_assessment_only(self):
        """Run configuration assessments only."""
        self.assess_configuration_compliance()
        self.assess_cross_coverage_consistency()
        return self.report

    def run_structure_assessment_only(self):
        """Run structure assessments only."""
        self.assess_project_structure()
        self.assess_documentation()
        return self.report

    def print_report(self, show_passes: bool = False):
        """Print formatted assessment report."""
        print("\n" + "=" * 70)
        print(" DSI COMPREHENSIVE PROJECT ASSESSMENT")
        print("=" * 70)
        print(f" Timestamp: {self.report.timestamp}")
        print(f" Project: {self.report.project_root}")
        print("-" * 70)

        # Print by category
        for category, summary in sorted(self.report.summaries.items()):
            print(f"\n## {self.CATEGORIES.get(category, category)}")
            print(f"   Score: {summary.score:.1f}% ({summary.passed} pass, {summary.warnings} warn, {summary.failed} fail)")

            # Print failures and warnings
            for result in self.report.results:
                if result.category == category:
                    if result.severity == Severity.FAIL:
                        prefix = "FAIL"
                        config = f" [{result.config_name}]" if result.config_name else ""
                        print(f"   [{prefix}]{config} {result.test_name}: {result.message}")
                    elif result.severity == Severity.WARNING:
                        prefix = "WARN"
                        config = f" [{result.config_name}]" if result.config_name else ""
                        print(f"   [{prefix}]{config} {result.test_name}: {result.message}")
                    elif show_passes and result.severity == Severity.PASS:
                        config = f" [{result.config_name}]" if result.config_name else ""
                        print(f"   [PASS]{config} {result.test_name}: {result.message}")

        # Print summary
        print("\n" + "=" * 70)
        print(f" OVERALL SCORE: {self.report.overall_score:.1f}%")
        if self.report.total_failures > 0:
            print(f" STATUS: ACTION REQUIRED ({self.report.total_failures} failures)")
        else:
            print(" STATUS: ALL CHECKS PASSED")
        print("=" * 70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="DSI Comprehensive Project Assessor")
    parser.add_argument("--config-only", action="store_true", help="Run config assessment only")
    parser.add_argument("--structure-only", action="store_true", help="Run structure assessment only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--show-passes", action="store_true", help="Show passing tests")
    parser.add_argument("--coverage", type=str, help="Assess specific coverage only")
    parser.add_argument("--project-root", type=str, help="Project root path")

    args = parser.parse_args()

    assessor = DSIComprehensiveAssessor(project_root=args.project_root)

    if args.config_only:
        report = assessor.run_config_assessment_only()
    elif args.structure_only:
        report = assessor.run_structure_assessment_only()
    else:
        report = assessor.run_full_assessment()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        assessor.print_report(show_passes=args.show_passes)

    # Exit with error code if failures
    sys.exit(1 if report.total_failures > 0 else 0)


if __name__ == "__main__":
    main()
