"""
DSI Comprehensive Project Assessor
==================================
Evaluates the Python codebase, API infrastructure, and mathematical
validity of YAML configurations against project_completeness_checklist.md.

This assessor covers:
- Infrastructure file existence
- Three-layer engine components
- Coverage configuration validation
- Actuarial math validation
- Schema compliance
- Signal architecture validation
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class DSIProjectAssessor:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.scores = {
            "infrastructure": {"pass": 0, "total": 0, "gaps": []},
            "layers": {"pass": 0, "total": 0, "gaps": []},
            "coverages": {"pass": 0, "total": 0, "gaps": []},
            "schema_compliance": {"pass": 0, "total": 0, "gaps": []},
            "signal_architecture": {"pass": 0, "total": 0, "gaps": []},
            "actuarial_math": {"pass": 0, "total": 0, "gaps": []},
        }

    def _assert(self, category: str, condition: bool, gap_message: str):
        """Record a check result."""
        self.scores[category]["total"] += 1
        if condition:
            self.scores[category]["pass"] += 1
        else:
            self.scores[category]["gaps"].append(gap_message)

    # =========================================================================
    # INFRASTRUCTURE CHECKS
    # =========================================================================

    def check_infrastructure(self):
        """Check core infrastructure files exist."""
        cat = "infrastructure"

        # Multiplexer & Arbiter (in signal_architecture/)
        self._assert(cat, (self.root / "signal_architecture/multiplexer/arbiter.py").exists(),
                     "ConfigArbiter missing (signal_architecture/multiplexer/arbiter.py)")
        self._assert(cat, (self.root / "signal_architecture/multiplexer/broker.py").exists(),
                     "SignalBroker missing (signal_architecture/multiplexer/broker.py)")

        # Validation
        self._assert(cat, (self.root / "infrastructure/validation/config_validator.py").exists(),
                     "config_validator.py missing (infrastructure/validation/)")

        # API
        self._assert(cat, (self.root / "infrastructure/api/main.py").exists(),
                     "API main.py missing (infrastructure/api/)")
        self._assert(cat, (self.root / "infrastructure/api/routes").exists(),
                     "API routes directory missing (infrastructure/api/routes/)")

        # Database
        self._assert(cat, (self.root / "infrastructure/db/models.py").exists(),
                     "Database models missing (infrastructure/db/models.py)")

        # Builder
        self._assert(cat, (self.root / "infrastructure/builder").exists(),
                     "Coverage builder missing (infrastructure/builder/)")

    def check_layers(self):
        """Check three-layer engine components exist."""
        cat = "layers"

        # Risk layer
        self._assert(cat, (self.root / "layers/risk/scorer.py").exists(),
                     "Risk scorer missing (layers/risk/scorer.py)")
        self._assert(cat, (self.root / "layers/risk/workflow.py").exists(),
                     "Risk workflow missing (layers/risk/workflow.py)")
        self._assert(cat, (self.root / "layers/risk/pricer.py").exists(),
                     "Risk pricer missing (layers/risk/pricer.py)")

        # Loss layer
        self._assert(cat, (self.root / "layers/loss/scorer.py").exists(),
                     "Loss scorer missing (layers/loss/scorer.py)")

        # Exposure layer
        self._assert(cat, (self.root / "layers/exposure/scorer.py").exists(),
                     "Exposure scorer missing (layers/exposure/scorer.py)")

    # =========================================================================
    # COVERAGE CONFIGURATION CHECKS
    # =========================================================================

    def check_coverage_structure(self, cov_name: str, cov_path: Path, config: dict):
        """Check structural requirements for a coverage configuration."""
        cat = "coverages"

        # logic.md exists
        self._assert(cat, (cov_path / "logic.md").exists(),
                     f"[{cov_name}] logic.md missing (run doc_generator.py)")

        for config_name, cfg in config.items():
            if not isinstance(cfg, dict):
                continue

            prefix = f"[{cov_name}/{config_name}]"
            metadata = cfg.get('metadata', {})

            # Metadata completeness
            self._assert(cat, metadata.get('name'),
                         f"{prefix} metadata.name missing")
            self._assert(cat, metadata.get('version'),
                         f"{prefix} metadata.version missing")
            self._assert(cat, metadata.get('product_types'),
                         f"{prefix} metadata.product_types missing")
            self._assert(cat, metadata.get('minimum_viable_input'),
                         f"{prefix} metadata.minimum_viable_input missing")
            self._assert(cat, metadata.get('min_premium') is not None,
                         f"{prefix} metadata.min_premium missing")

            # routing_constraints defined (can be empty)
            self._assert(cat, 'routing_constraints' in metadata,
                         f"{prefix} metadata.routing_constraints not defined")

            # Required sections exist
            self._assert(cat, 'signal_registry' in cfg,
                         f"{prefix} signal_registry section missing")
            self._assert(cat, 'groups' in cfg,
                         f"{prefix} groups section missing")
            self._assert(cat, 'risk_tier_bands' in cfg,
                         f"{prefix} risk_tier_bands section missing")
            self._assert(cat, 'loss_tier_bands' in cfg,
                         f"{prefix} loss_tier_bands section missing")
            self._assert(cat, 'exposure' in cfg,
                         f"{prefix} exposure section missing")
            self._assert(cat, 'pricing' in cfg,
                         f"{prefix} pricing section missing")

            # Direct queries constraint
            direct_queries = cfg.get('direct_queries', [])
            self._assert(cat, len(direct_queries) <= 10,
                         f"{prefix} Too many direct_queries ({len(direct_queries)} > 10)")

    # =========================================================================
    # SCHEMA COMPLIANCE CHECKS
    # =========================================================================

    def check_schema_compliance(self, cov_name: str, config_name: str, cfg: dict):
        """Check schema version and structural compliance."""
        cat = "schema_compliance"
        prefix = f"[{cov_name}/{config_name}]"

        # Schema version
        version = cfg.get('metadata', {}).get('version', '0.0.0')
        version_parts = version.split('.')
        try:
            major, minor = int(version_parts[0]), int(version_parts[1])
            self._assert(cat, major >= 2 and minor >= 2,
                         f"{prefix} Schema version {version} below 2.2.0")
        except (ValueError, IndexError):
            self._assert(cat, False, f"{prefix} Invalid version format: {version}")

        # Risk tier bands structure
        risk_bands = cfg.get('risk_tier_bands', {}).get('bands', [])
        self._assert(cat, len(risk_bands) == 5,
                     f"{prefix} risk_tier_bands must have exactly 5 bands (has {len(risk_bands)})")

        # Check tier bands cover 0-1000 range
        if risk_bands:
            min_score = min(b.get('interpretation', {}).get('bands', {}).get('min', 1000) for b in risk_bands)
            max_score = max(b.get('interpretation', {}).get('bands', {}).get('max', 0) for b in risk_bands)
            self._assert(cat, min_score == 0,
                         f"{prefix} risk_tier_bands min is {min_score}, should be 0")
            self._assert(cat, max_score >= 999,
                         f"{prefix} risk_tier_bands max is {max_score}, should cover 1000")

        # Loss tier bands have floor/cap
        loss_bands = cfg.get('loss_tier_bands', {})
        constraints = loss_bands.get('constraints', {})
        self._assert(cat, 'floor' in constraints and 'cap' in constraints,
                     f"{prefix} loss_tier_bands missing floor/cap constraints")

        # Exposure has size and complexity
        exposure = cfg.get('exposure', {})
        self._assert(cat, 'size' in exposure,
                     f"{prefix} exposure.size missing")
        self._assert(cat, 'complexity' in exposure,
                     f"{prefix} exposure.complexity missing")

        # Legacy fields removed
        self._assert(cat, 'deductible_credits' not in cfg,
                     f"{prefix} Legacy field 'deductible_credits' present (Phase 5 deprecation)")
        self._assert(cat, 'deductible_buy_down_rates' not in cfg,
                     f"{prefix} Legacy field 'deductible_buy_down_rates' present (Phase 5 deprecation)")

    # =========================================================================
    # SIGNAL ARCHITECTURE CHECKS
    # =========================================================================

    def check_signal_architecture(self, cov_name: str, config_name: str, cfg: dict):
        """Check signal registry structure and completeness."""
        cat = "signal_architecture"
        prefix = f"[{cov_name}/{config_name}]"

        signals = cfg.get('signal_registry', [])

        # Signal count
        self._assert(cat, len(signals) >= 15,
                     f"{prefix} Insufficient signals ({len(signals)} < 15 minimum)")

        # Signal ID uniqueness
        signal_ids = [s.get('id') for s in signals]
        unique_ids = set(signal_ids)
        self._assert(cat, len(signal_ids) == len(unique_ids),
                     f"{prefix} Duplicate signal IDs detected")

        # Proxy tier assignment
        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            proxy_tier = sig.get('proxy_tier')
            valid_tiers = ['DIRECT_OBSERVABLE', 'INFERRED_PROXY', 'COHORT_INFERENCE']
            self._assert(cat, proxy_tier in valid_tiers,
                         f"{prefix} Signal '{sig_id}' has invalid proxy_tier: {proxy_tier}")

        # Group ID validation
        defined_groups = set()
        for g in cfg.get('groups', {}).get('three_layer_assessment', []):
            defined_groups.add(g.get('id'))
        for g in cfg.get('groups', {}).get('categories', []):
            defined_groups.add(g.get('id'))

        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            # Check three_layer_assessment group
            tla = sig.get('three_layer_assessment', {})
            if tla:
                group_id = tla.get('group_id')
                if group_id:
                    self._assert(cat, group_id in defined_groups,
                                 f"{prefix} Signal '{sig_id}' references undefined group '{group_id}'")
            # Check categories group
            cats = sig.get('categories', {})
            if cats:
                group_id = cats.get('group_id')
                if group_id:
                    self._assert(cat, group_id in defined_groups,
                                 f"{prefix} Signal '{sig_id}' references undefined category group '{group_id}'")

    # =========================================================================
    # ACTUARIAL MATH CHECKS
    # =========================================================================

    def check_actuarial_math(self, cov_name: str, config_name: str, cfg: dict):
        """Check actuarial constraints and pricing logic."""
        cat = "actuarial_math"
        prefix = f"[{cov_name}/{config_name}]"

        # ---------------------------------------------------------------------
        # 1. Weights sum to 1.0 across groups (per layer)
        # ---------------------------------------------------------------------
        groups = cfg.get('groups', {}).get('three_layer_assessment', [])
        totals = {'risk': 0.0, 'loss': 0.0, 'exposure': 0.0}

        for g in groups:
            totals['risk'] += g.get('risk', {}).get('weight', 0)
            totals['loss'] += g.get('loss', {}).get('weight', 0)
            totals['exposure'] += g.get('exposure', {}).get('weight', 0)

        self._assert(cat, round(totals['risk'], 2) == 1.0,
                     f"{prefix} Risk weights sum to {totals['risk']:.3f}, not 1.0")
        self._assert(cat, round(totals['loss'], 2) == 1.0,
                     f"{prefix} Loss weights sum to {totals['loss']:.3f}, not 1.0")
        self._assert(cat, round(totals['exposure'], 2) == 1.0,
                     f"{prefix} Exposure weights sum to {totals['exposure']:.3f}, not 1.0")

        # ---------------------------------------------------------------------
        # 2. Scalability Trap Check
        # ---------------------------------------------------------------------
        bands = cfg.get('risk_tier_bands', {}).get('bands', [])
        tier_1 = next((b for b in bands if b['id'] == 1), {})
        method = tier_1.get('interpretation', {}).get('application', {}).get('method')
        routing = cfg.get('metadata', {}).get('routing_constraints', [])

        if method == "PREMIUM_BASE":
            # Must have ceiling constraint
            has_ceiling = any(r.get('operator') in ['<', '<='] for r in routing)
            self._assert(cat, has_ceiling,
                         f"{prefix} Scalability Trap: PREMIUM_BASE requires maximum size routing constraint")

        # ---------------------------------------------------------------------
        # 3. Monotonicity Check (Tier 5 must cost >= 2x Tier 1)
        # ---------------------------------------------------------------------
        if len(bands) == 5:
            t1_app = bands[0].get('interpretation', {}).get('application', {})
            t5_app = bands[4].get('interpretation', {}).get('application', {})

            t1_val = t1_app.get('value', t1_app.get('applied', 0))
            t5_val = t5_app.get('value', t5_app.get('applied', 0))

            if t1_val and t1_val > 0:
                ratio = t5_val / t1_val
                self._assert(cat, ratio >= 2.0,
                             f"{prefix} Penalty ratio is {ratio:.1f}x (must be >= 2.0x)")

        # ---------------------------------------------------------------------
        # 4. Pricing Anchor Validation
        # ---------------------------------------------------------------------
        pricing = cfg.get('pricing', {})
        b_limit = pricing.get('base_limit_reference')
        b_ded = pricing.get('base_deductible_reference')

        self._assert(cat, b_limit is not None,
                     f"{prefix} Missing pricing.base_limit_reference")
        self._assert(cat, b_ded is not None,
                     f"{prefix} Missing pricing.base_deductible_reference")

        # ILF curve anchor check
        for prod, data in pricing.get('by_product_type', {}).items():
            ilf_factors = data.get('ilf_curve', {}).get('factors', [])
            anchor_factor = next((f['factor'] for f in ilf_factors if f['limit'] == b_limit), None)
            self._assert(cat, anchor_factor == 1.0,
                         f"{prefix}/{prod} ILF anchor: limit {b_limit} factor is {anchor_factor}, must be 1.0")

            # Deductible anchor check
            ded_factors = data.get('deductible_factors', [])
            ded_anchor = next((f['factor'] for f in ded_factors if f['deductible'] == b_ded), None)
            self._assert(cat, ded_anchor == 1.0,
                         f"{prefix}/{prod} Deductible anchor: {b_ded} factor is {ded_anchor}, must be 1.0")

        # ---------------------------------------------------------------------
        # 5. MULTIPLIER basis validation
        # ---------------------------------------------------------------------
        if method == "MULTIPLIER":
            basis = tier_1.get('interpretation', {}).get('application', {}).get('basis')
            mvi = cfg.get('metadata', {}).get('minimum_viable_input', {})
            required_fields = [f.get('field') for f in mvi.get('required', [])]
            self._assert(cat, basis in required_fields,
                         f"{prefix} MULTIPLIER basis '{basis}' not in minimum_viable_input.required")

    # =========================================================================
    # RUN ASSESSMENT
    # =========================================================================

    def run_assessment(self):
        """Execute all assessment checks."""
        # Infrastructure & Layers
        self.check_infrastructure()
        self.check_layers()

        # Coverage configurations
        cov_dir = self.root / "coverages"
        if not cov_dir.exists():
            self._assert("coverages", False, "coverages/ directory not found")
            return

        for root, _, files in os.walk(cov_dir):
            if "config.yaml" in files:
                cov_path = Path(root)
                cov_name = cov_path.name

                with open(cov_path / "config.yaml", 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self._assert("coverages", False, f"[{cov_name}] YAML parse error: {e}")
                        continue

                config = data.get(cov_name, {})
                self.check_coverage_structure(cov_name, cov_path, config)

                for config_name, cfg in config.items():
                    if isinstance(cfg, dict):
                        self.check_schema_compliance(cov_name, config_name, cfg)
                        self.check_signal_architecture(cov_name, config_name, cfg)
                        self.check_actuarial_math(cov_name, config_name, cfg)

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def save_report(self):
        """Run assessment and save detailed report."""
        self.run_assessment()

        out_dir = self.root / "development/project/assessments/results"
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / f"Assessment_Report_{datetime.now().strftime('%Y-%m-%d')}.md"

        t_pass = sum(s["pass"] for s in self.scores.values())
        t_checks = sum(s["total"] for s in self.scores.values())
        pct = (t_pass / t_checks * 100) if t_checks > 0 else 0

        with open(report_path, 'w') as f:
            f.write("# DSI Project Completeness Assessment\n\n")
            f.write("```text\n")
            f.write(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Overall Score: {t_pass} / {t_checks} checks ({pct:.1f}%)\n\n")
            f.write("Section Scores:\n")
            for cat, s in self.scores.items():
                status = "PASS" if s['pass'] == s['total'] else "GAPS"
                f.write(f"  {cat.ljust(22)} {s['pass']:3d} / {s['total']:3d}  [{status}]\n")
            f.write("```\n\n")

            # Summary
            total_gaps = sum(len(s['gaps']) for s in self.scores.values())
            if total_gaps == 0:
                f.write("## Status: ALL CHECKS PASSED\n\n")
            else:
                f.write(f"## Action Items ({total_gaps} gaps identified)\n\n")
                for cat, s in self.scores.items():
                    if s["gaps"]:
                        f.write(f"### {cat.upper().replace('_', ' ')}\n\n")
                        for gap in s["gaps"]:
                            f.write(f"- [ ] {gap}\n")
                        f.write("\n")

        print(f"Assessment complete: {pct:.1f}% ({t_pass}/{t_checks} checks)")
        print(f"Report saved: {report_path}")

        if total_gaps > 0:
            print(f"\n{total_gaps} gaps require attention. See report for details.")


if __name__ == "__main__":
    assessor = DSIProjectAssessor()
    assessor.save_report()
