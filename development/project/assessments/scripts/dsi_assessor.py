"""
DSI Comprehensive Project Assessor
==================================
Evaluates the Python codebase, API infrastructure, and mathematical 
validity of YAML configurations against project_completeness_checklist.md.
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
            "actuarial_math": {"pass": 0, "total": 0, "gaps": []}
        }

    def _assert(self, category: str, condition: bool, gap_message: str):
        self.scores[category]["total"] += 1
        if condition:
            self.scores[category]["pass"] += 1
        else:
            self.scores[category]["gaps"].append(gap_message)

    def check_infrastructure_and_layers(self):
        cat_infra = "infrastructure"
        cat_layers = "layers"
        
        # Multiplexer & API Checks
        self._assert(cat_infra, (self.root / "infrastructure/multiplexer/arbiter.py").exists(), "ConfigArbiter missing.")
        self._assert(cat_infra, (self.root / "infrastructure/multiplexer/broker.py").exists(), "SignalBroker missing.")
        self._assert(cat_infra, (self.root / "infrastructure/validation/config_validator.py").exists(), "config_validator.py missing.")
        
        # Three-Layer Checks
        self._assert(cat_layers, (self.root / "layers/risk/scorer.py").exists(), "Risk scorer missing.")
        self._assert(cat_layers, (self.root / "layers/loss/scorer.py").exists(), "Loss scorer missing.")
        self._assert(cat_layers, (self.root / "layers/exposure/scorer.py").exists(), "Exposure scorer missing.")

    def check_actuarial_math(self, config_name: str, config: dict):
        cat = "actuarial_math"
        
        # 1. Weights sum to 1.0 Check
        groups = config.get('groups', {}).get('three_layer_assessment', [])
        for g in groups:
            w_risk = g.get('risk', {}).get('weight', 0)
            w_loss = g.get('loss', {}).get('weight', 0)
            w_exp = g.get('exposure', {}).get('weight', 0)
            total = round(w_risk + w_loss + w_exp, 3)
            self._assert(cat, total == 1.0, f"[{config_name}] Weights for {g['id']} sum to {total}, not 1.0")

        # 2. Phase 5 Schema Version
        version = config.get('metadata', {}).get('version', '0.0')
        self._assert(cat, version >= "2.2.0", f"[{config_name}] Schema version {version} is below 2.2.0")

        # 3. Scalability Trap Check
        tier_1 = next((b for b in config.get('risk_tier_bands', {}).get('bands', []) if b['id'] == 1), {})
        method = tier_1.get('interpretation', {}).get('application', {}).get('method')
        routing = config.get('metadata', {}).get('routing_constraints', [])
        if method == "PREMIUM_BASE":
            has_ceiling = any(r.get('operator') in ['<', '<='] for r in routing)
            self._assert(cat, has_ceiling, f"[{config_name}] Scalability Trap: PREMIUM_BASE lacks maximum size routing constraint.")

        # 4. Monotonicity Check (T5 must cost >= 2x T1)
        bands = config.get('risk_tier_bands', {}).get('bands', [])
        if len(bands) == 5:
            t1 = bands[0]['interpretation']['application'].get('value', bands[0]['interpretation']['application'].get('applied', 0))
            t5 = bands[4]['interpretation']['application'].get('value', bands[4]['interpretation']['application'].get('applied', 0))
            if t1 > 0:
                ratio = t5 / t1
                self._assert(cat, ratio >= 2.0, f"[{config_name}] Penalty Ratio is {ratio:.1f}x (must be >= 2.0x). Tier 5 is too cheap.")

        # 5. Anchor Logic Check
        pricing = config.get('pricing', {})
        b_limit = pricing.get('base_limit_reference')
        b_ded = pricing.get('base_deductible_reference')
        self._assert(cat, b_limit is not None and b_ded is not None, f"[{config_name}] Missing Pricing Anchors.")
        
        for prod, data in pricing.get('by_product_type', {}).items():
            ilf_factors = data.get('ilf_curve', {}).get('factors', [])
            anchor_factor = next((f['factor'] for f in ilf_factors if f['limit'] == b_limit), None)
            self._assert(cat, anchor_factor == 1.0, f"[{config_name} -> {prod}] Base limit {b_limit} does not have an ILF factor of exactly 1.0")

    def run_assessment(self):
        self.check_infrastructure_and_layers()
        
        cov_dir = self.root / "coverages"
        if not cov_dir.exists(): return

        for root, _, files in os.walk(cov_dir):
            if "config.yaml" in files:
                with open(Path(root) / "config.yaml", 'r') as f:
                    data = yaml.safe_load(f)
                    cov_name = Path(root).name
                    self._assert("coverages", (Path(root) / "logic.md").exists(), f"logic.md missing for {cov_name} (Run doc_generator.py)")
                    
                    for config_name, config in data.get(cov_name, {}).items():
                        if isinstance(config, dict):
                            self.check_actuarial_math(config_name, config)

    def save_report(self):
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
            f.write(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"Overall Score: {t_pass} / {t_checks} items ({pct:.1f}%)\n\n")
            f.write("Section Scores:\n")
            for cat, s in self.scores.items():
                f.write(f"  {cat.ljust(18)} {s['pass']} / {s['total']} items\n")
            f.write("```\n\n## Action Items (Gaps)\n")
            for cat, s in self.scores.items():
                if s["gaps"]:
                    f.write(f"\n### {cat.upper()}\n")
                    for gap in s["gaps"]: f.write(f"- [ ] {gap}\n")
        
        print(f"✅ Assessment complete! Score: {pct:.1f}%. Saved to {report_path}")

if __name__ == "__main__":
    assessor = DSIProjectAssessor()
    assessor.save_report()
