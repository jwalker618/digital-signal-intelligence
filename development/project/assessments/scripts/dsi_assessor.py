"""
DSI Unified Project Assessor
============================
Replaces all legacy assess scripts. Evaluates the project against the 
project_completeness_checklist.md and Phase 5 Actuarial Principles.
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime

class DSIUnifiedAssessor:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.results = {"passed": [], "failed": [], "warnings": []}

    def _assert(self, condition: bool, category: str, message: str, is_warning: bool = False):
        if condition:
            self.results["passed"].append(f"[{category}] {message}")
        else:
            if is_warning:
                self.results["warnings"].append(f"[{category}] {message}")
            else:
                self.results["failed"].append(f"[{category}] {message}")

    def assess_phase_5_compliance(self, coverage_name: str, config_name: str, config: dict):
        """Validates strictly against the Premium Methodology checklist rules."""
        
        # 1. Anchor Checks
        pricing = config.get('pricing', {})
        base_limit = pricing.get('base_limit_reference')
        base_deductible = pricing.get('base_deductible_reference')
        self._assert(base_limit is not None, "Anchors", f"{config_name} has base_limit_reference")
        self._assert(base_deductible is not None, "Anchors", f"{config_name} has base_deductible_reference")

        # 2. Limit Configuration Schema
        limits = config.get('limit_configuration', {})
        self._assert(limits.get('type') in ['BUNDLED', 'DECOUPLED'], "Schema", f"{config_name} uses BUNDLED or DECOUPLED limit_configuration")

        # 3. Scalability Trap Check
        tier_1 = next((b for b in config.get('risk_tier_bands', {}).get('bands', []) if b['id'] == 1), {})
        app = tier_1.get('interpretation', {}).get('application', {})
        method = app.get('method')
        routing = config.get('metadata', {}).get('routing_constraints', [])
        
        if method == "PREMIUM_BASE":
            has_ceiling = any(r.get('operator') in ['<', '<='] for r in routing)
            self._assert(has_ceiling, "Methodology", f"{config_name} uses PREMIUM_BASE and has a protective size ceiling constraint")
            
        elif method == "MULTIPLIER":
            self._assert('basis' in app, "Methodology", f"{config_name} uses MULTIPLIER and defines a basis (e.g. revenue, tiv)")

        # 4. Monotonicity Check (Prices must increase as Tier goes 1 -> 5)
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if len(bands) == 5:
            t1_val = bands[0]['interpretation']['application'].get('value', bands[0]['interpretation']['application'].get('applied', 0))
            t5_val = bands[4]['interpretation']['application'].get('value', bands[4]['interpretation']['application'].get('applied', 0))
            self._assert(t5_val > t1_val, "Actuarial", f"{config_name} Tier pricing is monotonic (T5 > T1)")
            if t1_val > 0:
                self._assert((t5_val / t1_val) >= 2.0, "Actuarial", f"{config_name} Penalty ratio is >= 2.0x", is_warning=True)

    def run_full_assessment(self):
        # Scan Configurations
        coverages_dir = self.root / "coverages"
        if coverages_dir.exists():
            for root, dirs, files in os.walk(coverages_dir):
                if "config.yaml" in files:
                    cov_name = Path(root).name
                    with open(Path(root) / "config.yaml", 'r') as f:
                        data = yaml.safe_load(f)
                        for config_name, config_data in data.get(cov_name, {}).items():
                            if isinstance(config_data, dict):
                                self.assess_phase_5_compliance(cov_name, config_name, config_data)
        
        # Ensure logic.md files exist (Doc Generator Check)
        for d in coverages_dir.iterdir():
            if d.is_dir():
                self._assert((d / "logic.md").exists(), "Documentation", f"{d.name} has logic.md generated")

    def save_report(self):
        self.run_full_assessment()
        
        results_dir = self.root / "development/project/assessments/results"
        results_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_path = results_dir / f"Assessment_Report_{date_str}.md"
        
        total_checks = len(self.results['passed']) + len(self.results['failed'])
        score = (len(self.results['passed']) / total_checks * 100) if total_checks > 0 else 0
        
        with open(report_path, 'w') as f:
            f.write(f"# DSI Project Completeness Assessment\n")
            f.write(f"**Date:** {date_str}\n")
            f.write(f"**Score:** {score:.1f}% ({len(self.results['passed'])}/{total_checks})\n\n")
            
            f.write("## ❌ Action Required (Failures)\n")
            if not self.results['failed']: f.write("None! Project is fully compliant.\n")
            for r in self.results['failed']: f.write(f"- {r}\n")
            
            f.write("\n## ⚠️ Warnings (Review Recommended)\n")
            if not self.results['warnings']: f.write("None.\n")
            for r in self.results['warnings']: f.write(f"- {r}\n")
            
            f.write("\n## ✅ Passed Checks\n")
            for r in self.results['passed']: f.write(f"- {r}\n")
            
        print(f"Assessment complete. Score: {score:.1f}%. Report saved to: {report_path}")

if __name__ == "__main__":
    assessor = DSIUnifiedAssessor()
    assessor.save_report()
