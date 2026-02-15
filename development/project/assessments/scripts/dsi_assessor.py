"""
DSI Comprehensive Project Assessor
==================================
A unified tool replacing all legacy assess scripts. Evaluates the Python 
codebase, API infrastructure, Multiplexer, and YAML configurations against 
the project_completeness_checklist.md.
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime

class DSIProjectAssessor:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.scores = {
            "coverages": {"pass": 0, "total": 0, "gaps": []},
            "infrastructure": {"pass": 0, "total": 0, "gaps": []},
            "layers": {"pass": 0, "total": 0, "gaps": []},
            "tests": {"pass": 0, "total": 0, "gaps": []},
            "critical_rules": {"pass": 0, "total": 0, "gaps": []}
        }

    def _assert(self, category: str, condition: bool, gap_message: str):
        self.scores[category]["total"] += 1
        if condition:
            self.scores[category]["pass"] += 1
        else:
            self.scores[category]["gaps"].append(gap_message)

    def check_infrastructure(self):
        """Checks API, Builder, and Multiplexer (Phase 4)."""
        cat = "infrastructure"
        api_dir = self.root / "infrastructure" / "api"
        multi_dir = self.root / "infrastructure" / "multiplexer"
        
        # Multiplexer Checks
        self._assert(cat, multi_dir.exists(), "Multiplexer directory missing.")
        self._assert(cat, (multi_dir / "arbiter.py").exists(), "ConfigArbiter not implemented.")
        self._assert(cat, (multi_dir / "broker.py").exists(), "SignalBroker not implemented.")
        
        # API Checks
        self._assert(cat, api_dir.exists(), "API directory missing.")
        
        # Validation Checks
        val_dir = self.root / "infrastructure" / "validation"
        self._assert(cat, (val_dir / "config_validator.py").exists(), "Schema Validator missing.")

    def check_layers(self):
        """Checks the Three-Layer Assessment Architecture."""
        cat = "layers"
        layers_dir = self.root / "layers"
        
        self._assert(cat, layers_dir.exists(), "Layers directory missing.")
        self._assert(cat, (layers_dir / "risk").exists(), "Risk layer missing.")
        self._assert(cat, (layers_dir / "loss").exists(), "Loss layer missing.")
        self._assert(cat, (layers_dir / "exposure").exists(), "Exposure layer missing.")
        self._assert(cat, (layers_dir / "risk" / "scorer.py").exists(), "Risk Scorer missing.")

    def check_tests(self):
        """Checks testing infrastructure."""
        cat = "tests"
        self._assert(cat, (self.root / "tests").exists(), "Tests directory missing.")
        self._assert(cat, (self.root / "pytest.ini").exists() or (self.root / "pyproject.toml").exists(), "Pytest config missing.")

    def check_coverages(self):
        """Strict Phase 5 Config Validation (Actuarial & Structural)."""
        cat = "coverages"
        crit = "critical_rules"
        cov_dir = self.root / "coverages"
        self._assert(cat, cov_dir.exists(), "Coverages directory missing.")
        if not cov_dir.exists(): return

        for root, _, files in os.walk(cov_dir):
            if "config.yaml" not in files: continue
            
            with open(Path(root) / "config.yaml", 'r') as f:
                data = yaml.safe_load(f)
                coverage_name = Path(root).name
                
                # Check for logic.md (Doc Generator)
                self._assert(cat, (Path(root) / "logic.md").exists(), f"logic.md missing for {coverage_name}")

                for config_name, config in data.get(coverage_name, {}).items():
                    if not isinstance(config, dict): continue

                    # 1. Routing Exclusivity
                    routing = config.get('metadata', {}).get('routing_constraints', [])
                    self._assert(cat, len(routing) > 0 or "general" in config_name, f"{config_name} has no routing constraints.")

                    # 2. Phase 5 Anchors
                    pricing = config.get('pricing', {})
                    self._assert(crit, 'base_limit_reference' in pricing, f"{config_name} missing base_limit_reference.")
                    self._assert(crit, 'base_deductible_reference' in pricing, f"{config_name} missing base_deductible_reference.")

                    # 3. Polymorphic Limits
                    limits = config.get('limit_configuration', {})
                    self._assert(crit, limits.get('type') in ['BUNDLED', 'DECOUPLED'], f"{config_name} limit_configuration type invalid.")

                    # 4. Scalability Trap & Pricing Method
                    tier_1 = next((b for b in config.get('risk_tier_bands', {}).get('bands', []) if b['id'] == 1), {})
                    method = tier_1.get('interpretation', {}).get('application', {}).get('method')
                    
                    if method == "PREMIUM_BASE":
                        has_ceiling = any(r.get('operator') in ['<', '<='] for r in routing)
                        self._assert(crit, has_ceiling, f"{config_name} uses PREMIUM_BASE but lacks size routing ceiling.")
                    elif method == "MULTIPLIER":
                        self._assert(crit, 'basis' in tier_1.get('interpretation', {}).get('application', {}), f"{config_name} missing basis for MULTIPLIER.")

    def run_assessment(self):
        self.check_infrastructure()
        self.check_layers()
        self.check_tests()
        self.check_coverages()

    def save_report(self):
        self.run_assessment()
        results_dir = self.root / "development/project/assessments/results"
        results_dir.mkdir(parents=True, exist_ok=True)
        report_path = results_dir / f"Assessment_Report_{datetime.now().strftime('%Y-%m-%d')}.md"

        total_pass = sum(s["pass"] for s in self.scores.values())
        total_checks = sum(s["total"] for s in self.scores.values())
        score_pct = (total_pass / total_checks * 100) if total_checks > 0 else 0

        # Collect top 3 gaps
        all_gaps = []
        for s in self.scores.values(): all_gaps.extend(s["gaps"])

        with open(report_path, 'w') as f:
            f.write("# DSI Project Completeness Assessment\n\n")
            f.write("```text\n")
            f.write(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"Assessed By: DSI Unified Assessor\n\n")
            f.write("Section Scores:\n")
            for cat, scores in self.scores.items():
                f.write(f"  {cat.ljust(22)} {scores['pass']} / {scores['total']} items\n")
            
            f.write(f"\nOverall: {total_pass} / {total_checks} items ({score_pct:.1f}%)\n\n")
            f.write("Top Gaps:\n")
            for i, gap in enumerate(all_gaps[:3], 1):
                f.write(f"{i}. {gap}\n")
            if not all_gaps:
                f.write("1. None! Project is fully compliant.\n")
            f.write("```\n\n")

            f.write("## Detailed Action Items\n")
            for cat, scores in self.scores.items():
                if scores["gaps"]:
                    f.write(f"### {cat.upper()}\n")
                    for gap in scores["gaps"]:
                        f.write(f"- [ ] {gap}\n")
        
        print(f"✅ Assessment complete! Score: {score_pct:.1f}%. Saved to {report_path}")

if __name__ == "__main__":
    assessor = DSIProjectAssessor()
    assessor.save_report()
