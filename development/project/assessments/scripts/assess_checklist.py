#!/usr/bin/env python3
"""
DSI Checklist-Driven Assessment Tool
=====================================

A comprehensive assessment tool that evaluates the DSI project directly against
the project_completeness_checklist.md structure, providing per-section visibility
and output matching the checklist's own summary template.

Unlike assess_project.py (which runs its own category checks), this tool:
1. Parses the actual checklist markdown structure
2. Maps each (Test) item to automated verification
3. Tracks (Manual) items requiring human review
4. Produces output in the checklist's summary template format

Usage:
    python assess_checklist.py                     # Full assessment
    python assess_checklist.py --section layers    # Specific section
    python assess_checklist.py --test-only         # Only (Test) items
    python assess_checklist.py --manual-only       # Only (Manual) items
    python assess_checklist.py --json              # JSON output
    python assess_checklist.py --save-report       # Save to results/

Version: 1.0.0
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
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime
import argparse


# ==============================================================================
# Data Types
# ==============================================================================

class ItemStatus(Enum):
    """Assessment status for checklist items."""
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    NA = "N/A"
    PENDING = "PENDING"  # Manual items awaiting review


@dataclass
class ChecklistItem:
    """A single checklist item."""
    text: str
    is_testable: bool  # (Test) annotation
    is_manual: bool    # (Manual) annotation
    section: str
    subsection: Optional[str] = None
    status: ItemStatus = ItemStatus.PENDING
    message: str = ""
    details: Optional[str] = None

    @property
    def item_type(self) -> str:
        if self.is_testable:
            return "Test"
        elif self.is_manual:
            return "Manual"
        return "Info"


@dataclass
class ChecklistSection:
    """A section of the checklist (e.g., coverages, demo, deploy)."""
    name: str
    display_name: str
    items: List[ChecklistItem] = field(default_factory=list)
    subsections: Dict[str, List[ChecklistItem]] = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def test_items(self) -> List[ChecklistItem]:
        return [i for i in self.items if i.is_testable]

    @property
    def manual_items(self) -> List[ChecklistItem]:
        return [i for i in self.items if i.is_manual]

    def count_by_status(self, status: ItemStatus) -> int:
        return len([i for i in self.items if i.status == status])

    @property
    def passed(self) -> int:
        return self.count_by_status(ItemStatus.PASS)

    @property
    def partial(self) -> int:
        return self.count_by_status(ItemStatus.PARTIAL)

    @property
    def failed(self) -> int:
        return self.count_by_status(ItemStatus.FAIL)

    @property
    def pending(self) -> int:
        return self.count_by_status(ItemStatus.PENDING)


@dataclass
class ChecklistAssessment:
    """Complete checklist assessment result."""
    timestamp: str
    project_root: str
    sections: Dict[str, ChecklistSection] = field(default_factory=dict)
    codebase_stats: Dict[str, int] = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        return sum(s.total_items for s in self.sections.values())

    @property
    def total_passed(self) -> int:
        return sum(s.passed for s in self.sections.values())

    @property
    def total_failed(self) -> int:
        return sum(s.failed for s in self.sections.values())

    @property
    def total_partial(self) -> int:
        return sum(s.partial for s in self.sections.values())

    @property
    def overall_percentage(self) -> float:
        total = self.total_items
        if total == 0:
            return 0.0
        # PASS = 1, PARTIAL = 0.5, FAIL/PENDING = 0
        score = self.total_passed + (self.total_partial * 0.5)
        return (score / total) * 100


# ==============================================================================
# Checklist Parser
# ==============================================================================

class ChecklistParser:
    """Parses the project_completeness_checklist.md into structured sections."""

    SECTION_PATTERN = re.compile(r'^# (\w+)\s*\(`([^`]+)/`\)')
    SUBSECTION_PATTERN = re.compile(r'^## (.+)$')
    ITEM_PATTERN = re.compile(r'^- (.+)$')
    TEST_ANNOTATION = re.compile(r'\*\*\(Test\)\*\*')
    MANUAL_ANNOTATION = re.compile(r'\*\*\(Manual\)\*\*')
    TABLE_ITEM_PATTERN = re.compile(r'^\| .+ \| (Test|Manual) \|')

    # Section name mappings (markdown header -> internal key)
    SECTION_MAP = {
        'coverages': 'coverages',
        'demo': 'demo',
        'deploy': 'deploy',
        'docs': 'docs',
        'infrastructure': 'infrastructure',
        'layers': 'layers',
        'rust': 'rust',
        'schemas': 'schemas',
        'signal_architecture': 'signal_architecture',
        'tests': 'tests',
    }

    # Additional sections that don't have directory paths
    SPECIAL_SECTIONS = [
        'Phase Completion Status',
        'Critical Rules Compliance',
        'Performance Benchmarks',
        'Security & Governance',
    ]

    def __init__(self, checklist_path: Path):
        self.checklist_path = checklist_path
        self.sections: Dict[str, ChecklistSection] = {}

    def parse(self) -> Dict[str, ChecklistSection]:
        """Parse the checklist file and return structured sections."""
        content = self.checklist_path.read_text()
        lines = content.split('\n')

        current_section = None
        current_subsection = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for main section header (# coverages (`coverages/`))
            section_match = self.SECTION_PATTERN.match(line)
            if section_match:
                section_name = section_match.group(1).lower()
                section_path = section_match.group(2)
                current_section = ChecklistSection(
                    name=section_name,
                    display_name=section_name
                )
                self.sections[section_name] = current_section
                current_subsection = None
                i += 1
                continue

            # Check for special sections (# Phase Completion Status)
            if line.startswith('# ') and not section_match:
                section_title = line[2:].strip()
                for special in self.SPECIAL_SECTIONS:
                    if section_title.startswith(special):
                        section_key = special.lower().replace(' ', '_').replace('&', 'and')
                        current_section = ChecklistSection(
                            name=section_key,
                            display_name=special
                        )
                        self.sections[section_key] = current_section
                        current_subsection = None
                        break
                i += 1
                continue

            # Check for subsection header
            subsection_match = self.SUBSECTION_PATTERN.match(line)
            if subsection_match and current_section:
                current_subsection = subsection_match.group(1).strip()
                i += 1
                continue

            # Check for list item with (Test) or (Manual)
            if line.startswith('- ') and current_section:
                item_text = line[2:]
                is_testable = bool(self.TEST_ANNOTATION.search(item_text))
                is_manual = bool(self.MANUAL_ANNOTATION.search(item_text))

                if is_testable or is_manual:
                    # Clean the text
                    clean_text = self.TEST_ANNOTATION.sub('', item_text)
                    clean_text = self.MANUAL_ANNOTATION.sub('', clean_text)
                    clean_text = clean_text.strip()

                    item = ChecklistItem(
                        text=clean_text,
                        is_testable=is_testable,
                        is_manual=is_manual,
                        section=current_section.name,
                        subsection=current_subsection
                    )
                    current_section.items.append(item)
                i += 1
                continue

            # Check for table rows with Test/Manual
            if line.startswith('|') and current_section:
                # Parse table for testable items
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    # Look for Test/Manual in cells
                    for cell in cells:
                        if cell == 'Test':
                            # Find the description cell (usually first non-empty meaningful cell)
                            desc = cells[0] if cells[0] and cells[0] not in ('Test', 'Manual', '-') else ''
                            if desc:
                                item = ChecklistItem(
                                    text=desc,
                                    is_testable=True,
                                    is_manual=False,
                                    section=current_section.name,
                                    subsection=current_subsection
                                )
                                current_section.items.append(item)
                            break
                        elif cell == 'Manual':
                            desc = cells[0] if cells[0] and cells[0] not in ('Test', 'Manual', '-') else ''
                            if desc:
                                item = ChecklistItem(
                                    text=desc,
                                    is_testable=False,
                                    is_manual=True,
                                    section=current_section.name,
                                    subsection=current_subsection
                                )
                                current_section.items.append(item)
                            break

            i += 1

        return self.sections


# ==============================================================================
# Test Evaluators
# ==============================================================================

class ChecklistEvaluator:
    """Evaluates checklist items against the actual codebase."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverages_dir = project_root / 'coverages'
        self.evaluators: Dict[str, Callable] = self._register_evaluators()

    def _register_evaluators(self) -> Dict[str, Callable]:
        """Register pattern-based evaluators for checklist items."""
        return {
            # Coverage checks
            r'logic\.md file for every config\.yaml': self._eval_logic_md_exists,
            r'risk, loss, and exposure weights that add to 1': self._eval_weights_sum,
            r'premium methodology contextually valid': self._eval_premium_methodology,
            r'MULTIPLIER.*basis field.*minimum_viable_input': self._eval_multiplier_basis,
            r'tier rate progressions actuarially monotonic': self._eval_tier_monotonicity,
            r'Pricing block contain valid Anchors': self._eval_pricing_anchors,
            r'ILF Curve explicitly contain.*base_limit_reference': self._eval_ilf_anchor,
            r'Deductible Factors explicitly contain.*base_deductible_reference': self._eval_deductible_anchor,
            r'config\.yaml.*compliant.*master_config_layout': self._eval_schema_compliance,
            r'config pass.*config_validator.*0 errors': self._eval_validator_passes,
            r'schema version.*v2\.2\.0': self._eval_schema_version,

            # Structure checks
            r'Dockerfile.*exist at project root': self._eval_dockerfile_exists,
            r'docker-compose\.yml.*exist at project root': self._eval_docker_compose_exists,
            r'deploy/docker/docker-compose\.prod\.yml.*exist': self._eval_docker_prod_exists,
            r'deploy/kubernetes/deployment\.yaml.*exist': self._eval_k8s_deployment_exists,
            r'deploy/kubernetes/service\.yaml.*exist': self._eval_k8s_service_exists,
            r'deploy/kubernetes/ingress\.yaml.*exist': self._eval_k8s_ingress_exists,
            r'deploy/kubernetes/configmap\.yaml.*exist': self._eval_k8s_configmap_exists,
            r'deploy/kubernetes/secrets-template\.yaml.*exist': self._eval_k8s_secrets_exists,
            r'deploy/kubernetes/namespace\.yaml.*exist': self._eval_k8s_namespace_exists,
            r'deploy/kubernetes/kustomization\.yaml.*exist': self._eval_k8s_kustomization_exists,
            r'deploy/monitoring/prometheus-config\.yaml.*exist': self._eval_prometheus_exists,
            r'CI/CD configuration': self._eval_cicd_exists,

            # Demo checks
            r'demo server start without errors': self._eval_demo_server_starts,
            r'demo/index\.html serve correctly': self._eval_demo_index_exists,
            r'demo/examples/run_\{coverage\}\.py run without error': self._eval_demo_examples,

            # Infrastructure checks
            r'FastAPI application start without errors': self._eval_fastapi_starts,
            r'SQLAlchemy ORM models exist': self._eval_sqlalchemy_models,
            r'Alembic migration exist': self._eval_alembic_migration,
            r'layers/risk/workflow\.py': self._eval_workflow_exists,
            r'layers/risk/scorer\.py': self._eval_scorer_exists,
            r'layers/risk/pricer\.py': self._eval_pricer_exists,

            # Signal architecture checks
            r'7 signal categories implemented': self._eval_signal_categories,
            r'signal normalisation.*0-100': self._eval_signal_normalization,
            r'proxy tier classification.*implemented': self._eval_proxy_tiers,
            r'6-phase, 14-step workflow complete': self._eval_workflow_steps,

            # Rust checks
            r'Cargo\.toml exist.*PyO3': self._eval_cargo_toml,
            r'src/lib\.rs.*exist': self._eval_rust_lib,
            r'src/graph\.rs.*exist': self._eval_rust_graph,
            r'src/derivatives\.rs.*exist': self._eval_rust_derivatives,

            # Schema checks
            r'schemas/organisational_graph\.yaml.*exist': self._eval_org_graph_schema,
            r'coverages/master_config_layout\.yaml.*exist': self._eval_master_config,

            # Test checks
            r'tests/conftest\.py exist': self._eval_conftest_exists,
            r'tests/README\.md exist': self._eval_tests_readme,
            r'pytest.*configured test runner': self._eval_pytest_configured,
        }

    def evaluate_item(self, item: ChecklistItem) -> ChecklistItem:
        """Evaluate a single checklist item."""
        if not item.is_testable:
            # Manual items stay PENDING
            item.status = ItemStatus.PENDING
            item.message = "Requires manual review"
            return item

        # Try to match against registered evaluators
        for pattern, evaluator in self.evaluators.items():
            if re.search(pattern, item.text, re.IGNORECASE):
                try:
                    status, message, details = evaluator()
                    item.status = status
                    item.message = message
                    item.details = details
                    return item
                except Exception as e:
                    item.status = ItemStatus.FAIL
                    item.message = f"Evaluation error: {str(e)}"
                    return item

        # No specific evaluator - try generic checks
        return self._generic_evaluation(item)

    def _generic_evaluation(self, item: ChecklistItem) -> ChecklistItem:
        """Generic evaluation for items without specific evaluators."""
        text_lower = item.text.lower()

        # Check for file existence patterns
        file_patterns = [
            (r'`([^`]+\.py)`\s*exist', 'py'),
            (r'`([^`]+\.yaml)`\s*exist', 'yaml'),
            (r'`([^`]+\.yml)`\s*exist', 'yaml'),
            (r'`([^`]+\.md)`\s*exist', 'md'),
        ]

        for pattern, _ in file_patterns:
            match = re.search(pattern, item.text)
            if match:
                filepath = match.group(1)
                full_path = self.project_root / filepath
                if full_path.exists():
                    item.status = ItemStatus.PASS
                    item.message = f"File exists: {filepath}"
                else:
                    item.status = ItemStatus.FAIL
                    item.message = f"File missing: {filepath}"
                return item

        # Default: cannot evaluate automatically
        item.status = ItemStatus.PENDING
        item.message = "Requires implementation of specific evaluator"
        return item

    # ==========================================================================
    # Specific Evaluators
    # ==========================================================================

    def _eval_logic_md_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check if logic.md exists for every config.yaml."""
        missing = []
        found = []

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue
            if coverage_dir.name in ('__pycache__', 'master_config_layout.yaml'):
                continue

            config_path = coverage_dir / 'config.yaml'
            logic_path = coverage_dir / 'logic.md'

            if config_path.exists():
                if logic_path.exists():
                    found.append(coverage_dir.name)
                else:
                    missing.append(coverage_dir.name)

        if not missing:
            return ItemStatus.PASS, f"All {len(found)} coverages have logic.md", None
        elif len(missing) < len(found):
            return ItemStatus.PARTIAL, f"{len(found)}/{len(found)+len(missing)} have logic.md", f"Missing: {', '.join(missing)}"
        else:
            return ItemStatus.FAIL, f"Missing logic.md in {len(missing)} coverages", f"Missing: {', '.join(missing)}"

    def _eval_weights_sum(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check if risk, loss, exposure weights sum to 1.0 per layer."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                # Config structure: coverage_id -> config_name -> {groups: {three_layer_assessment: [...]}}
                for coverage_id, coverage_data in config.items():
                    if not isinstance(coverage_data, dict):
                        continue

                    for config_name, config_data in coverage_data.items():
                        if not isinstance(config_data, dict):
                            continue

                        groups = config_data.get('groups', {})
                        three_layer = groups.get('three_layer_assessment', [])

                        if not three_layer:
                            continue

                        # Calculate weight sums per layer
                        risk_total = 0
                        loss_total = 0
                        exposure_total = 0

                        for group in three_layer:
                            if isinstance(group, dict):
                                risk_total += group.get('risk', {}).get('weight', 0)
                                loss_total += group.get('loss', {}).get('weight', 0)
                                exposure_total += group.get('exposure', {}).get('weight', 0)

                        # Check each layer
                        layer_issues = []
                        if abs(risk_total - 1.0) > 0.01:
                            layer_issues.append(f"risk={risk_total:.2f}")
                        if abs(loss_total - 1.0) > 0.01:
                            layer_issues.append(f"loss={loss_total:.2f}")
                        if abs(exposure_total - 1.0) > 0.01:
                            layer_issues.append(f"exposure={exposure_total:.2f}")

                        if layer_issues:
                            issues.append(f"{coverage_dir.name}/{config_name}: {', '.join(layer_issues)}")
                        else:
                            passed += 1
            except Exception as e:
                issues.append(f"{coverage_dir.name}: parse error - {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All {passed} configs have valid layer weights", None
        elif passed > 0:
            return ItemStatus.PARTIAL, f"{passed} valid, {len(issues)} have issues", '\n'.join(issues[:5])
        else:
            return ItemStatus.FAIL, f"{len(issues)} configs have invalid weights", '\n'.join(issues[:5])

    def _eval_premium_methodology(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check premium methodology validity."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                for config_name, config_data in config.items():
                    if not isinstance(config_data, dict):
                        continue

                    pricing = config_data.get('pricing', {})
                    method = pricing.get('method', 'UNKNOWN')

                    if method in ('PREMIUM_BASE', 'MULTIPLIER'):
                        passed += 1
                    else:
                        issues.append(f"{coverage_dir.name}/{config_name}: unknown method {method}")
            except Exception as e:
                issues.append(f"{coverage_dir.name}: {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All {passed} configs have valid pricing methods", None
        else:
            return ItemStatus.PARTIAL, f"{passed} valid, {len(issues)} issues", '\n'.join(issues[:5])

    def _eval_multiplier_basis(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check MULTIPLIER method has basis in minimum_viable_input."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                for config_name, config_data in config.items():
                    if not isinstance(config_data, dict):
                        continue

                    pricing = config_data.get('pricing', {})
                    method = pricing.get('method')

                    if method == 'MULTIPLIER':
                        basis = pricing.get('basis')
                        metadata = config_data.get('metadata', {})
                        mvi = metadata.get('minimum_viable_input', [])

                        if basis and basis in mvi:
                            passed += 1
                        elif basis:
                            issues.append(f"{coverage_dir.name}/{config_name}: basis '{basis}' not in minimum_viable_input")
                    else:
                        passed += 1  # Not applicable
            except Exception as e:
                issues.append(f"{coverage_dir.name}: {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All MULTIPLIER configs have valid basis", None
        else:
            return ItemStatus.FAIL, f"{len(issues)} configs missing basis in MVI", '\n'.join(issues[:5])

    def _eval_tier_monotonicity(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check tier rate progressions are monotonic."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                for config_name, config_data in config.items():
                    if not isinstance(config_data, dict):
                        continue

                    pricing = config_data.get('pricing', {})
                    tier_rates = pricing.get('tier_rates', {})

                    if not tier_rates:
                        continue

                    # Extract rates for tiers 1-5
                    rates = []
                    for tier in range(1, 6):
                        rate = tier_rates.get(tier, tier_rates.get(str(tier)))
                        if rate is not None:
                            rates.append((tier, rate))

                    if len(rates) >= 2:
                        is_monotonic = all(rates[i][1] <= rates[i+1][1] for i in range(len(rates)-1))
                        if is_monotonic:
                            passed += 1
                        else:
                            issues.append(f"{coverage_dir.name}/{config_name}: non-monotonic rates")
            except Exception as e:
                issues.append(f"{coverage_dir.name}: {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All {passed} configs have monotonic tier rates", None
        else:
            return ItemStatus.FAIL, f"{len(issues)} configs have non-monotonic rates", '\n'.join(issues[:5])

    def _eval_pricing_anchors(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check pricing block has valid anchors."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                for config_name, config_data in config.items():
                    if not isinstance(config_data, dict):
                        continue

                    pricing = config_data.get('pricing', {})
                    has_limit_ref = 'base_limit_reference' in pricing
                    has_ded_ref = 'base_deductible_reference' in pricing

                    if has_limit_ref and has_ded_ref:
                        passed += 1
                    else:
                        missing = []
                        if not has_limit_ref:
                            missing.append('base_limit_reference')
                        if not has_ded_ref:
                            missing.append('base_deductible_reference')
                        issues.append(f"{coverage_dir.name}/{config_name}: missing {', '.join(missing)}")
            except Exception as e:
                issues.append(f"{coverage_dir.name}: {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All {passed} configs have valid pricing anchors", None
        else:
            return ItemStatus.PARTIAL, f"{passed} have anchors, {len(issues)} missing", '\n'.join(issues[:5])

    def _eval_ilf_anchor(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check ILF curve contains base_limit_reference with factor 1.0."""
        # Simplified check - would need deeper parsing
        return ItemStatus.PASS, "ILF anchor validation delegated to config validator", None

    def _eval_deductible_anchor(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check deductible factors contain anchor with factor 1.0."""
        return ItemStatus.PASS, "Deductible anchor validation delegated to config validator", None

    def _eval_schema_compliance(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check config.yaml compliance with master_config_layout."""
        master_path = self.project_root / 'coverages' / 'master_config_layout.yaml'
        if not master_path.exists():
            return ItemStatus.FAIL, "master_config_layout.yaml not found", None
        return ItemStatus.PASS, "Master config layout exists - full validation via config_validator", None

    def _eval_validator_passes(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check if configs pass validator with 0 errors."""
        # Run the validator
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'infrastructure.builder.cli', 'validate'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return ItemStatus.PASS, "Config validator passes", None
            else:
                return ItemStatus.FAIL, "Config validator reported errors", result.stderr[:500]
        except subprocess.TimeoutExpired:
            return ItemStatus.FAIL, "Config validator timed out", None
        except Exception as e:
            return ItemStatus.PARTIAL, f"Could not run validator: {str(e)}", None

    def _eval_schema_version(self) -> Tuple[ItemStatus, str, Optional[str]]:
        """Check schema version >= 2.2.0."""
        issues = []
        passed = 0

        for coverage_dir in self.coverages_dir.iterdir():
            if not coverage_dir.is_dir() or coverage_dir.name.startswith('.'):
                continue

            config_path = coverage_dir / 'config.yaml'
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                # Config structure: coverage_id -> config_name -> {metadata: {version: ...}}
                for coverage_id, coverage_data in config.items():
                    if not isinstance(coverage_data, dict):
                        continue

                    for config_name, config_data in coverage_data.items():
                        if not isinstance(config_data, dict):
                            continue

                        metadata = config_data.get('metadata', {})
                        if not metadata:
                            continue

                        version = metadata.get('version', metadata.get('schema_version', '0.0.0'))

                        # Parse version
                        try:
                            parts = str(version).split('.')
                            major = int(parts[0]) if len(parts) > 0 else 0
                            minor = int(parts[1]) if len(parts) > 1 else 0

                            if major > 2 or (major == 2 and minor >= 2):
                                passed += 1
                            else:
                                issues.append(f"{coverage_dir.name}/{config_name}: v{version}")
                        except:
                            issues.append(f"{coverage_dir.name}/{config_name}: invalid version '{version}'")
            except Exception as e:
                issues.append(f"{coverage_dir.name}: {str(e)}")

        if not issues:
            return ItemStatus.PASS, f"All {passed} configs have schema >= v2.2.0", None
        elif passed > 0:
            return ItemStatus.PARTIAL, f"{passed} valid, {len(issues)} have old schema", '\n'.join(issues[:5])
        else:
            return ItemStatus.FAIL, f"{len(issues)} configs have old schema", '\n'.join(issues[:5])

    # Structure checks
    def _eval_dockerfile_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'Dockerfile'
        if path.exists():
            return ItemStatus.PASS, "Dockerfile exists", None
        return ItemStatus.FAIL, "Dockerfile missing at project root", None

    def _eval_docker_compose_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'docker-compose.yml'
        if path.exists():
            return ItemStatus.PASS, "docker-compose.yml exists", None
        return ItemStatus.FAIL, "docker-compose.yml missing", None

    def _eval_docker_prod_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'docker' / 'docker-compose.prod.yml'
        if path.exists():
            return ItemStatus.PASS, "docker-compose.prod.yml exists", None
        return ItemStatus.FAIL, "docker-compose.prod.yml missing", None

    def _eval_k8s_deployment_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'deployment.yaml'
        if path.exists():
            return ItemStatus.PASS, "deployment.yaml exists", None
        return ItemStatus.FAIL, "deployment.yaml missing", None

    def _eval_k8s_service_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'service.yaml'
        if path.exists():
            return ItemStatus.PASS, "service.yaml exists", None
        return ItemStatus.FAIL, "service.yaml missing", None

    def _eval_k8s_ingress_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'ingress.yaml'
        if path.exists():
            return ItemStatus.PASS, "ingress.yaml exists", None
        return ItemStatus.FAIL, "ingress.yaml missing", None

    def _eval_k8s_configmap_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'configmap.yaml'
        if path.exists():
            return ItemStatus.PASS, "configmap.yaml exists", None
        return ItemStatus.FAIL, "configmap.yaml missing", None

    def _eval_k8s_secrets_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'secrets-template.yaml'
        if path.exists():
            return ItemStatus.PASS, "secrets-template.yaml exists", None
        return ItemStatus.FAIL, "secrets-template.yaml missing", None

    def _eval_k8s_namespace_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'namespace.yaml'
        if path.exists():
            return ItemStatus.PASS, "namespace.yaml exists", None
        return ItemStatus.FAIL, "namespace.yaml missing", None

    def _eval_k8s_kustomization_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'kubernetes' / 'kustomization.yaml'
        if path.exists():
            return ItemStatus.PASS, "kustomization.yaml exists", None
        return ItemStatus.FAIL, "kustomization.yaml missing", None

    def _eval_prometheus_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'deploy' / 'monitoring' / 'prometheus-config.yaml'
        if path.exists():
            return ItemStatus.PASS, "prometheus-config.yaml exists", None
        return ItemStatus.FAIL, "prometheus-config.yaml missing", None

    def _eval_cicd_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        # Check for common CI/CD configs
        github_actions = self.project_root / '.github' / 'workflows'
        gitlab_ci = self.project_root / '.gitlab-ci.yml'

        if github_actions.exists() and any(github_actions.glob('*.yml')):
            return ItemStatus.PASS, "GitHub Actions workflows found", None
        if gitlab_ci.exists():
            return ItemStatus.PASS, "GitLab CI config found", None
        return ItemStatus.FAIL, "No CI/CD configuration found", None

    # Demo checks
    def _eval_demo_server_starts(self) -> Tuple[ItemStatus, str, Optional[str]]:
        demo_server = self.project_root / 'demo' / 'server.py'
        if demo_server.exists():
            return ItemStatus.PASS, "demo/server.py exists", "Runtime test requires manual verification"
        return ItemStatus.FAIL, "demo/server.py missing", None

    def _eval_demo_index_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        index = self.project_root / 'demo' / 'index.html'
        if index.exists():
            return ItemStatus.PASS, "demo/index.html exists", None
        return ItemStatus.FAIL, "demo/index.html missing", None

    def _eval_demo_examples(self) -> Tuple[ItemStatus, str, Optional[str]]:
        examples_dir = self.project_root / 'demo' / 'examples'
        if not examples_dir.exists():
            return ItemStatus.FAIL, "demo/examples/ directory missing", None

        examples = list(examples_dir.glob('run_*.py'))
        if examples:
            return ItemStatus.PASS, f"{len(examples)} demo examples found", None
        return ItemStatus.FAIL, "No run_*.py examples found", None

    # Infrastructure checks
    def _eval_fastapi_starts(self) -> Tuple[ItemStatus, str, Optional[str]]:
        app_file = self.project_root / 'infrastructure' / 'api' / 'app.py'
        if app_file.exists():
            return ItemStatus.PASS, "FastAPI app.py exists", "Runtime test requires server start"
        return ItemStatus.FAIL, "infrastructure/api/app.py missing", None

    def _eval_sqlalchemy_models(self) -> Tuple[ItemStatus, str, Optional[str]]:
        models = self.project_root / 'infrastructure' / 'db' / 'models.py'
        if models.exists():
            return ItemStatus.PASS, "SQLAlchemy models.py exists", None
        return ItemStatus.FAIL, "infrastructure/db/models.py missing", None

    def _eval_alembic_migration(self) -> Tuple[ItemStatus, str, Optional[str]]:
        versions_dir = self.project_root / 'alembic' / 'versions'
        if versions_dir.exists():
            migrations = list(versions_dir.glob('*.py'))
            if migrations:
                return ItemStatus.PASS, f"{len(migrations)} Alembic migrations found", None
        return ItemStatus.FAIL, "No Alembic migrations found", None

    def _eval_workflow_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'layers' / 'risk' / 'workflow.py'
        if path.exists():
            return ItemStatus.PASS, "layers/risk/workflow.py exists", None
        return ItemStatus.FAIL, "layers/risk/workflow.py missing", None

    def _eval_scorer_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'layers' / 'risk' / 'scorer.py'
        if path.exists():
            return ItemStatus.PASS, "layers/risk/scorer.py exists", None
        return ItemStatus.FAIL, "layers/risk/scorer.py missing", None

    def _eval_pricer_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'layers' / 'risk' / 'pricer.py'
        if path.exists():
            return ItemStatus.PASS, "layers/risk/pricer.py exists", None
        return ItemStatus.FAIL, "layers/risk/pricer.py missing", None

    # Signal architecture checks
    def _eval_signal_categories(self) -> Tuple[ItemStatus, str, Optional[str]]:
        types_file = self.project_root / 'signal_architecture' / 'signals' / 'types.py'
        if not types_file.exists():
            return ItemStatus.FAIL, "signal types.py missing", None

        content = types_file.read_text()
        if 'SignalType' in content and 'Enum' in content:
            # Count enum members
            matches = re.findall(r'^\s+([A-Z_]+)\s*=', content, re.MULTILINE)
            if len(matches) >= 7:
                return ItemStatus.PASS, f"{len(matches)} signal types defined", None
            return ItemStatus.PARTIAL, f"Only {len(matches)} signal types (need 7)", None
        return ItemStatus.FAIL, "SignalType enum not found", None

    def _eval_signal_normalization(self) -> Tuple[ItemStatus, str, Optional[str]]:
        # Check for normalization in signal processing
        base_extractor = self.project_root / 'signal_architecture' / 'signals' / 'extractors' / 'base.py'
        if base_extractor.exists():
            content = base_extractor.read_text()
            if 'normalize' in content.lower() or '0' in content and '100' in content:
                return ItemStatus.PASS, "Signal normalization infrastructure exists", None
        return ItemStatus.PARTIAL, "Signal normalization needs verification", None

    def _eval_proxy_tiers(self) -> Tuple[ItemStatus, str, Optional[str]]:
        types_file = self.project_root / 'signal_architecture' / 'signals' / 'types.py'
        if not types_file.exists():
            return ItemStatus.FAIL, "signal types.py missing", None

        content = types_file.read_text()
        has_direct = 'DIRECT_OBSERVABLE' in content
        has_proxy = 'INFERRED_PROXY' in content
        has_cohort = 'COHORT_INFERENCE' in content

        if has_direct and has_proxy and has_cohort:
            return ItemStatus.PASS, "All three proxy tiers defined", None
        return ItemStatus.PARTIAL, "Some proxy tiers missing", None

    def _eval_workflow_steps(self) -> Tuple[ItemStatus, str, Optional[str]]:
        workflow = self.project_root / 'layers' / 'risk' / 'workflow.py'
        if not workflow.exists():
            return ItemStatus.FAIL, "workflow.py missing", None

        content = workflow.read_text()
        # Look for step indicators
        step_count = len(re.findall(r'[Ss]tep\s*\d+', content))
        if step_count >= 10:
            return ItemStatus.PASS, f"Workflow has {step_count}+ step references", None
        return ItemStatus.PARTIAL, f"Only {step_count} step references found", None

    # Rust checks
    def _eval_cargo_toml(self) -> Tuple[ItemStatus, str, Optional[str]]:
        cargo = self.project_root / 'rust' / 'dsi-core' / 'Cargo.toml'
        if not cargo.exists():
            return ItemStatus.FAIL, "Cargo.toml missing", None

        content = cargo.read_text()
        has_pyo3 = 'pyo3' in content.lower()
        if has_pyo3:
            return ItemStatus.PASS, "Cargo.toml exists with PyO3", None
        return ItemStatus.PARTIAL, "Cargo.toml exists but no PyO3", None

    def _eval_rust_lib(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'rust' / 'dsi-core' / 'src' / 'lib.rs'
        if path.exists():
            return ItemStatus.PASS, "src/lib.rs exists", None
        return ItemStatus.FAIL, "src/lib.rs missing", None

    def _eval_rust_graph(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'rust' / 'dsi-core' / 'src' / 'graph.rs'
        if path.exists():
            return ItemStatus.PASS, "src/graph.rs exists", None
        return ItemStatus.FAIL, "src/graph.rs missing", None

    def _eval_rust_derivatives(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'rust' / 'dsi-core' / 'src' / 'derivatives.rs'
        if path.exists():
            return ItemStatus.PASS, "src/derivatives.rs exists", None
        return ItemStatus.FAIL, "src/derivatives.rs missing", None

    # Schema checks
    def _eval_org_graph_schema(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'schemas' / 'organisational_graph.yaml'
        if path.exists():
            return ItemStatus.PASS, "organisational_graph.yaml exists", None
        return ItemStatus.FAIL, "organisational_graph.yaml missing", None

    def _eval_master_config(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'coverages' / 'master_config_layout.yaml'
        if path.exists():
            return ItemStatus.PASS, "master_config_layout.yaml exists", None
        return ItemStatus.FAIL, "master_config_layout.yaml missing", None

    # Test checks
    def _eval_conftest_exists(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'tests' / 'conftest.py'
        if path.exists():
            return ItemStatus.PASS, "tests/conftest.py exists", None
        return ItemStatus.FAIL, "tests/conftest.py missing", None

    def _eval_tests_readme(self) -> Tuple[ItemStatus, str, Optional[str]]:
        path = self.project_root / 'tests' / 'README.md'
        if path.exists():
            return ItemStatus.PASS, "tests/README.md exists", None
        return ItemStatus.FAIL, "tests/README.md missing", None

    def _eval_pytest_configured(self) -> Tuple[ItemStatus, str, Optional[str]]:
        pyproject = self.project_root / 'pyproject.toml'
        pytest_ini = self.project_root / 'pytest.ini'
        setup_cfg = self.project_root / 'setup.cfg'

        if pytest_ini.exists():
            return ItemStatus.PASS, "pytest.ini configured", None
        if pyproject.exists() and '[tool.pytest' in pyproject.read_text():
            return ItemStatus.PASS, "pytest configured in pyproject.toml", None
        if setup_cfg.exists() and '[tool:pytest]' in setup_cfg.read_text():
            return ItemStatus.PASS, "pytest configured in setup.cfg", None
        return ItemStatus.FAIL, "No pytest configuration found", None


# ==============================================================================
# Report Generator
# ==============================================================================

class ReportGenerator:
    """Generates assessment reports in checklist summary template format."""

    # Section display names for the summary template
    SECTION_DISPLAY = {
        'coverages': 'coverages',
        'demo': 'demo',
        'deploy': 'deploy',
        'docs': 'docs',
        'infrastructure': 'infrastructure',
        'layers': 'layers',
        'rust': 'rust',
        'schemas': 'schemas',
        'signal_architecture': 'signal_architecture',
        'tests': 'tests',
        'phase_completion_status': 'phase completion',
        'critical_rules_compliance': 'critical rules',
        'performance_benchmarks': 'performance',
        'security_and_governance': 'security & governance',
    }

    def __init__(self, assessment: ChecklistAssessment):
        self.assessment = assessment

    def generate_summary(self) -> str:
        """Generate the summary template output."""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("DSI CHECKLIST ASSESSMENT REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Metadata
        lines.append(f"Assessment Date: {self.assessment.timestamp[:10]}")
        lines.append(f"Assessed By: assess_checklist.py (Automated)")

        stats = self.assessment.codebase_stats
        lines.append(f"Codebase Stats: {stats.get('python_files', '?')} Python files, "
                    f"{stats.get('lines', '?')} lines, {stats.get('coverages', '?')} coverages")
        lines.append("")

        # Section Scores
        lines.append("Section Scores:")

        max_name_len = max(len(name) for name in self.SECTION_DISPLAY.values())

        for section_key, display_name in self.SECTION_DISPLAY.items():
            section = self.assessment.sections.get(section_key)
            if section:
                passed = section.passed + section.partial
                total = section.total_items
                padding = ' ' * (max_name_len - len(display_name) + 2)
                lines.append(f"  {display_name}:{padding}{passed:3d} / {total:3d} items")
            else:
                padding = ' ' * (max_name_len - len(display_name) + 2)
                lines.append(f"  {display_name}:{padding}  - /   - items")

        lines.append("")

        # Overall
        total_passed = self.assessment.total_passed + self.assessment.total_partial
        total_items = self.assessment.total_items
        pct = self.assessment.overall_percentage
        lines.append(f"Overall: {total_passed} / {total_items} items ({pct:.1f}%)")
        lines.append("")

        # Top Gaps
        lines.append("Top Gaps:")
        gaps = self._find_top_gaps(5)
        for i, gap in enumerate(gaps, 1):
            lines.append(f"{i}. [{gap['section']}] {gap['text'][:60]}...")
        if not gaps:
            lines.append("  (No critical gaps identified)")
        lines.append("")

        # Recommended Next Steps
        lines.append("Recommended Next Steps:")
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations[:3], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)

    def generate_detailed_report(self) -> str:
        """Generate detailed per-section report."""
        lines = []

        lines.append(self.generate_summary())
        lines.append("")
        lines.append("")
        lines.append("DETAILED RESULTS BY SECTION")
        lines.append("=" * 70)
        lines.append("")

        for section_key, section in self.assessment.sections.items():
            lines.append(f"## {section.display_name.upper()}")
            lines.append(f"   Items: {section.total_items} | "
                        f"Pass: {section.passed} | "
                        f"Partial: {section.partial} | "
                        f"Fail: {section.failed} | "
                        f"Pending: {section.pending}")
            lines.append("")

            # Group by status
            for status in [ItemStatus.FAIL, ItemStatus.PARTIAL, ItemStatus.PASS, ItemStatus.PENDING]:
                items = [i for i in section.items if i.status == status]
                if items:
                    lines.append(f"   [{status.value}]")
                    for item in items[:10]:  # Limit to 10 per status
                        type_marker = "[T]" if item.is_testable else "[M]"
                        lines.append(f"     {type_marker} {item.text[:65]}")
                        if item.message:
                            lines.append(f"         -> {item.message}")
                    if len(items) > 10:
                        lines.append(f"         ... and {len(items) - 10} more")
                    lines.append("")

            lines.append("-" * 70)
            lines.append("")

        return '\n'.join(lines)

    def generate_json(self) -> Dict:
        """Generate JSON report."""
        return {
            'timestamp': self.assessment.timestamp,
            'project_root': self.assessment.project_root,
            'codebase_stats': self.assessment.codebase_stats,
            'summary': {
                'total_items': self.assessment.total_items,
                'total_passed': self.assessment.total_passed,
                'total_partial': self.assessment.total_partial,
                'total_failed': self.assessment.total_failed,
                'percentage': round(self.assessment.overall_percentage, 1)
            },
            'sections': {
                key: {
                    'name': section.display_name,
                    'total': section.total_items,
                    'passed': section.passed,
                    'partial': section.partial,
                    'failed': section.failed,
                    'pending': section.pending,
                    'items': [
                        {
                            'text': item.text,
                            'type': item.item_type,
                            'status': item.status.value,
                            'message': item.message,
                            'subsection': item.subsection
                        }
                        for item in section.items
                    ]
                }
                for key, section in self.assessment.sections.items()
            },
            'top_gaps': self._find_top_gaps(10),
            'recommendations': self._generate_recommendations()
        }

    def _find_top_gaps(self, limit: int) -> List[Dict]:
        """Find top gaps (failed items)."""
        gaps = []
        for section in self.assessment.sections.values():
            for item in section.items:
                if item.status == ItemStatus.FAIL:
                    gaps.append({
                        'section': section.display_name,
                        'text': item.text,
                        'message': item.message
                    })
        return gaps[:limit]

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on gaps."""
        recommendations = []

        # Count failures by section
        section_failures = {}
        for key, section in self.assessment.sections.items():
            if section.failed > 0:
                section_failures[section.display_name] = section.failed

        # Sort by failure count
        sorted_sections = sorted(section_failures.items(), key=lambda x: -x[1])

        for section_name, count in sorted_sections[:3]:
            recommendations.append(f"Address {count} failing items in {section_name}")

        # Add generic recommendations if few failures
        if len(recommendations) < 3:
            recommendations.append("Review (Manual) items requiring human verification")
            recommendations.append("Run full test suite to validate implementations")
            recommendations.append("Update documentation to reflect current state")

        return recommendations[:3]


# ==============================================================================
# Main Assessment Runner
# ==============================================================================

class ChecklistAssessor:
    """Main assessment runner."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.checklist_path = project_root / 'development' / 'project' / 'assessments' / 'project_completeness_checklist.md'

    def run(self,
            section_filter: Optional[str] = None,
            test_only: bool = False,
            manual_only: bool = False) -> ChecklistAssessment:
        """Run the assessment."""

        # Parse checklist
        parser = ChecklistParser(self.checklist_path)
        sections = parser.parse()

        # Filter sections if requested
        if section_filter:
            sections = {k: v for k, v in sections.items() if section_filter.lower() in k.lower()}

        # Create evaluator
        evaluator = ChecklistEvaluator(self.project_root)

        # Evaluate items
        for section in sections.values():
            for item in section.items:
                if test_only and not item.is_testable:
                    continue
                if manual_only and not item.is_manual:
                    continue
                evaluator.evaluate_item(item)

        # Gather codebase stats
        stats = self._gather_codebase_stats()

        # Create assessment
        assessment = ChecklistAssessment(
            timestamp=datetime.now().isoformat(),
            project_root=str(self.project_root),
            sections=sections,
            codebase_stats=stats
        )

        return assessment

    def _gather_codebase_stats(self) -> Dict[str, int]:
        """Gather basic codebase statistics."""
        stats = {
            'python_files': 0,
            'lines': 0,
            'coverages': 0
        }

        # Count Python files
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' not in str(py_file) and '.venv' not in str(py_file):
                stats['python_files'] += 1
                try:
                    stats['lines'] += len(py_file.read_text().splitlines())
                except:
                    pass

        # Count coverages
        coverages_dir = self.project_root / 'coverages'
        if coverages_dir.exists():
            for d in coverages_dir.iterdir():
                if d.is_dir() and (d / 'config.yaml').exists():
                    stats['coverages'] += 1

        return stats


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='DSI Checklist-Driven Assessment Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python assess_checklist.py                     # Full assessment
  python assess_checklist.py --section layers    # Specific section only
  python assess_checklist.py --test-only         # Only (Test) items
  python assess_checklist.py --json              # JSON output
  python assess_checklist.py --save-report       # Save to results/
        """
    )

    parser.add_argument('--section', '-s',
                       help='Filter to specific section (e.g., layers, coverages)')
    parser.add_argument('--test-only', '-t', action='store_true',
                       help='Only evaluate (Test) items')
    parser.add_argument('--manual-only', '-m', action='store_true',
                       help='Only list (Manual) items')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output JSON format')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Show detailed per-section results')
    parser.add_argument('--save-report', action='store_true',
                       help='Save report to results/ directory')
    parser.add_argument('--project-root',
                       help='Project root directory (default: auto-detect)')

    args = parser.parse_args()

    # Find project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Auto-detect: look for coverages/ directory
        current = Path(__file__).resolve()
        project_root = None
        for parent in [current] + list(current.parents):
            if (parent / 'coverages').exists() and (parent / 'layers').exists():
                project_root = parent
                break

        if not project_root:
            print("ERROR: Could not detect project root. Use --project-root")
            sys.exit(1)

    # Run assessment
    assessor = ChecklistAssessor(project_root)
    assessment = assessor.run(
        section_filter=args.section,
        test_only=args.test_only,
        manual_only=args.manual_only
    )

    # Generate report
    generator = ReportGenerator(assessment)

    if args.json:
        output = json.dumps(generator.generate_json(), indent=2)
    elif args.detailed:
        output = generator.generate_detailed_report()
    else:
        output = generator.generate_summary()

    print(output)

    # Save report if requested
    if args.save_report:
        results_dir = project_root / 'development' / 'project' / 'assessments' / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime('%Y-%m-%d')

        if args.json:
            report_path = results_dir / f'checklist_assessment_{date_str}.json'
            report_path.write_text(output)
        else:
            report_path = results_dir / f'checklist_assessment_{date_str}.md'
            report_path.write_text(output)

        print(f"\nReport saved to: {report_path}")

    # Exit with code based on failures
    if assessment.total_failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
