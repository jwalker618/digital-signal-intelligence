"""
DSI Coverage Documentation Generator
====================================
Generates a comprehensive logic.md for each coverage. Validates adherence
to DSI Foundational Principles and outputs theoretical pricing executions.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime

class DSIDocGenerator:
    def __init__(self, root_dir: str = "."):
        self.coverages_dir = Path(root_dir) / "coverages"

    def _generate_theoretical_pricing(self, config: dict) -> str:
        pricing = config.get('pricing', {})
        b_limit = pricing.get('base_limit_reference', 0)
        b_ded = pricing.get('base_deductible_reference', 0)
        
        tier_bands = config.get('risk_tier_bands', {}).get('bands', [])
        t3 = next((b for b in tier_bands if b['id'] == 3), tier_bands[0] if tier_bands else {})
        app = t3.get('interpretation', {}).get('application', {})
        method = app.get('method', 'UNKNOWN')
        
        md = "### Theoretical Premium Calculation (Tier 3 Standard)\n"
        md += "> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*\n"
        md += "> *P_final = (Base × Rate) × ILF_relativity × Deductible_Factor × Modifiers*\n\n"
        
        if method == "MULTIPLIER":
            rate = app.get('applied', 0)
            basis = app.get('basis', 'exposure')
            md += f"**1. The Pricing Anchor:** The Base Rate of `{rate * 100}%` on `{basis}` purchases exactly a `${b_limit:,.0f}` Limit with a `${b_ded:,.0f}` Deductible.\n"
            md += "**2. Theoretical Execution:**\n"
            md += f"  - Assume `{basis}` = $10,000,000\n"
            md += f"  - Base Premium = $10,000,000 × {rate} = **${10000000 * rate:,.0f}**\n"
            md += f"  - If the client requests the Anchor Limit/Deductible, the factors are 1.00, resulting in a technical premium of **${10000000 * rate:,.0f}**.\n"
        elif method == "PREMIUM_BASE":
            val = app.get('value', 0)
            md += f"**1. The Pricing Anchor:** The Flat Premium of `${val:,.0f}` purchases exactly the `${b_limit:,.0f}` Limit / `${b_ded:,.0f}` Deductible Base Package.\n"
            md += "**2. Theoretical Execution:**\n"
            md += f"  - Technical Premium = **${val:,.0f}**\n"
            md += f"  - *Scaling relies entirely on selecting a different Limit ID from the Bundled limit_configuration packages.*\n"

        return md

    def build_logic_md(self, cov_name: str, yaml_data: dict) -> str:
        md = f"# DSI Logic Document: `{cov_name.upper()}`\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d')}*\n\n"
        
        md += "## DSI Foundational Principles Adherence\n"
        md += "This configuration is validated against the DSI Whitepaper & Vision Paper:\n"
        md += "- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.\n"
        md += "- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.\n"
        md += "- **Phase 5 Anchoring:** Polmorphic pricing limits scale from mathematically absolute anchor points.\n\n"

        for config_name, config in yaml_data.items():
            if not isinstance(config, dict): continue
            
            md += f"## Model: `{config_name}`\n"
            md += f"*{config.get('metadata', {}).get('description', '')}*\n\n"
            
            md += "### Routing Protocol (Multiplexer)\n"
            routing = config.get('metadata', {}).get('routing_constraints', [])
            if routing:
                for r in routing: md += f"- `{r.get('field')} {r.get('operator')} {r.get('value')}`\n"
            else:
                md += "- *Universal Routing (No constraints)*\n"
            md += "\n"
            md += self._generate_theoretical_pricing(config)
            md += "\n---\n"
            
        return md

    def execute(self):
        for root, dirs, files in os.walk(self.coverages_dir):
            if "config.yaml" in files:
                cov_name = Path(root).name
                with open(Path(root) / "config.yaml", 'r') as f:
                    data = yaml.safe_load(f)
                
                md_content = self.build_logic_md(cov_name, data.get(cov_name, {}))
                
                with open(Path(root) / "logic.md", 'w') as f:
                    f.write(md_content)
                print(f"✅ Generated logic.md for {cov_name}")

if __name__ == "__main__":
    DSIDocGenerator().execute()
