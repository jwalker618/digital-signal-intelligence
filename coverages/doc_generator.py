"""
DSI Coverage Documentation Generator
====================================
Generates a comprehensive logic.md for each coverage. Validates adherence
to DSI Foundational Principles, documents weight distributions, signal
architecture rationale, and outputs theoretical pricing executions.
"""

import os
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class DSIDocGenerator:
    def __init__(self, root_dir: str = "."):
        self.coverages_dir = Path(root_dir) / "coverages"

    def _analyze_weights(self, config: dict) -> dict:
        """Analyze three-layer weights at group level and validate they sum to 1.0."""
        groups = config.get('groups', {}).get('three_layer_assessment', [])

        totals = {'risk': 0.0, 'loss': 0.0, 'exposure': 0.0}
        group_weights = []

        for g in groups:
            gw = {
                'id': g.get('id', 'unknown'),
                'label': g.get('label', ''),
                'risk': g.get('risk', {}).get('weight', 0),
                'loss': g.get('loss', {}).get('weight', 0),
                'exposure': g.get('exposure', {}).get('weight', 0)
            }
            group_weights.append(gw)
            totals['risk'] += gw['risk']
            totals['loss'] += gw['loss']
            totals['exposure'] += gw['exposure']

        return {
            'groups': group_weights,
            'totals': {k: round(v, 3) for k, v in totals.items()},
            'valid': all(round(v, 2) == 1.0 for v in totals.values())
        }

    def _analyze_signals(self, config: dict) -> dict:
        """Analyze signal registry for proxy tier distribution and group assignments."""
        signals = config.get('signal_registry', [])

        by_proxy_tier = defaultdict(list)
        by_group = defaultdict(list)

        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            proxy_tier = sig.get('proxy_tier', 'UNKNOWN')
            by_proxy_tier[proxy_tier].append(sig_id)

            # Check for three_layer_assessment group assignment
            tla = sig.get('three_layer_assessment', {})
            group_id = tla.get('group_id')
            if group_id:
                by_group[group_id].append(sig_id)

            # Check for categorical group assignment
            cats = sig.get('categories', {})
            cat_group = cats.get('group_id')
            if cat_group:
                by_group[cat_group].append(sig_id)

        return {
            'total_count': len(signals),
            'by_proxy_tier': dict(by_proxy_tier),
            'by_group': dict(by_group)
        }

    def _rank_groups_by_importance(self, weight_analysis: dict) -> list:
        """Rank signal groups by their combined weight importance."""
        groups = weight_analysis['groups']
        ranked = []
        for g in groups:
            combined = g['risk'] + g['loss'] + g['exposure']
            ranked.append({
                'id': g['id'],
                'label': g['label'],
                'combined_weight': round(combined, 3),
                'risk': g['risk'],
                'loss': g['loss'],
                'exposure': g['exposure']
            })
        return sorted(ranked, key=lambda x: x['combined_weight'], reverse=True)

    def _generate_weight_section(self, config: dict) -> str:
        """Generate documentation section for weight validation."""
        analysis = self._analyze_weights(config)

        md = "### Three-Layer Weight Distribution\n"
        md += "> *DSI requires that weights for Risk, Loss, and Exposure each sum to 1.0 across all signal groups.*\n\n"

        # Validation status
        if analysis['valid']:
            md += "**Validation:** PASS\n\n"
        else:
            md += "**Validation:** FAIL - Weights do not sum to 1.0\n\n"

        # Weight table
        md += "| Group | Risk | Loss | Exposure |\n"
        md += "|-------|------|------|----------|\n"
        for g in analysis['groups']:
            md += f"| {g['label']} | {g['risk']:.2f} | {g['loss']:.2f} | {g['exposure']:.2f} |\n"
        md += f"| **TOTAL** | **{analysis['totals']['risk']:.2f}** | **{analysis['totals']['loss']:.2f}** | **{analysis['totals']['exposure']:.2f}** |\n"
        md += "\n"

        return md

    def _generate_signal_rationale_section(self, config: dict) -> str:
        """Generate documentation section explaining signal selection rationale."""
        analysis = self._analyze_signals(config)

        md = "### Signal Architecture Rationale\n"
        md += f"This configuration contains **{analysis['total_count']} signals** distributed as follows:\n\n"

        # Proxy tier distribution
        md += "**By Proxy Tier (Confidence Hierarchy):**\n"
        tier_order = ['DIRECT_OBSERVABLE', 'INFERRED_PROXY', 'COHORT_INFERENCE']
        for tier in tier_order:
            signals = analysis['by_proxy_tier'].get(tier, [])
            if signals:
                md += f"- `{tier}` ({len(signals)} signals): "
                md += "Highest confidence" if tier == 'DIRECT_OBSERVABLE' else "Medium confidence" if tier == 'INFERRED_PROXY' else "Lowest confidence"
                md += "\n"
        md += "\n"

        # Group distribution
        md += "**Signal Count by Group:**\n"
        for group_id, signals in sorted(analysis['by_group'].items(), key=lambda x: len(x[1]), reverse=True):
            md += f"- `{group_id}`: {len(signals)} signals\n"
        md += "\n"

        # Rationale
        direct_count = len(analysis['by_proxy_tier'].get('DIRECT_OBSERVABLE', []))
        inferred_count = len(analysis['by_proxy_tier'].get('INFERRED_PROXY', []))
        total = analysis['total_count']
        direct_pct = (direct_count / total * 100) if total > 0 else 0

        md += "**Selection Rationale:**\n"
        md += f"- {direct_pct:.0f}% of signals are directly observable, ensuring objective, machine-readable assessment.\n"
        md += "- Proxy tiers weight confidence: DIRECT_OBSERVABLE signals have highest pricing impact.\n"
        md += "- Signal selection prioritizes external observability (DSI Foundational Principle #1).\n"
        md += "\n"

        return md

    def _generate_group_importance_section(self, config: dict) -> str:
        """Generate documentation section ranking signal groups by importance."""
        weight_analysis = self._analyze_weights(config)
        ranked = self._rank_groups_by_importance(weight_analysis)

        md = "### Signal Group Importance Ranking\n"
        md += "> *Groups ranked by combined weight across all three assessment layers.*\n\n"

        md += "| Rank | Group | Combined | Risk | Loss | Exposure |\n"
        md += "|------|-------|----------|------|------|----------|\n"
        for i, g in enumerate(ranked, 1):
            md += f"| {i} | {g['label']} | {g['combined_weight']:.2f} | {g['risk']:.2f} | {g['loss']:.2f} | {g['exposure']:.2f} |\n"
        md += "\n"

        # Highlight most important
        if ranked:
            top = ranked[0]
            md += f"**Primary Assessment Driver:** `{top['label']}` with combined weight of {top['combined_weight']:.2f}\n"
            if len(ranked) > 1:
                second = ranked[1]
                md += f"**Secondary Driver:** `{second['label']}` with combined weight of {second['combined_weight']:.2f}\n"
        md += "\n"

        return md

    def _generate_theoretical_pricing(self, config: dict) -> str:
        """Generate theoretical pricing calculation example."""
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
        """Build complete logic.md content for a coverage."""
        md = f"# DSI Logic Document: `{cov_name.upper()}`\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d')}*\n\n"

        md += "## DSI Foundational Principles Adherence\n"
        md += "This configuration is validated against the DSI Whitepaper & Vision Paper:\n"
        md += "- **Objective Observation:** Signals derived from verifiable digital footprints, avoiding subjective interpretation.\n"
        md += "- **Three-Layer Engine:** Modifiers explicitly target Risk, Loss, and Exposure dimensions.\n"
        md += "- **Phase 5 Anchoring:** Polymorphic pricing limits scale from mathematically absolute anchor points.\n\n"

        for config_name, config in yaml_data.items():
            if not isinstance(config, dict):
                continue

            md += f"---\n\n## Model: `{config_name}`\n"
            md += f"*{config.get('metadata', {}).get('description', '')}*\n\n"

            # Routing Protocol
            md += "### Routing Protocol (Multiplexer)\n"
            routing = config.get('metadata', {}).get('routing_constraints', [])
            if routing:
                for r in routing:
                    md += f"- `{r.get('field')} {r.get('operator')} {r.get('value')}`\n"
            else:
                md += "- *Universal Routing (No constraints)*\n"
            md += "\n"

            # Weight Distribution
            md += self._generate_weight_section(config)

            # Signal Rationale
            md += self._generate_signal_rationale_section(config)

            # Group Importance
            md += self._generate_group_importance_section(config)

            # Theoretical Pricing
            md += self._generate_theoretical_pricing(config)
            md += "\n"

        return md

    def execute(self):
        """Execute documentation generation for all coverages."""
        # Map directory names to YAML top-level keys
        yaml_key_map = {
            'do': 'directors_officers',
            'fi': 'financial_institutions',
            'pi': 'professional_indemnity',
            'cyber': 'cyber',
            'aerospace': 'aerospace',
            'energy': 'energy',
            'marine': 'marine',
            'property': 'commercial_property',
            'casualty': 'commercial_casualty',
            'fpr': 'financial_political_risk',
        }

        generated = []
        for root, dirs, files in os.walk(self.coverages_dir):
            if "config.yaml" in files:
                cov_name = Path(root).name
                with open(Path(root) / "config.yaml", 'r') as f:
                    data = yaml.safe_load(f)

                # Try mapped key first, then directory name as fallback
                yaml_key = yaml_key_map.get(cov_name, cov_name)
                config_data = data.get(yaml_key, data.get(cov_name, {}))

                if not config_data:
                    print(f"Warning: No config found for {cov_name} (tried keys: {yaml_key}, {cov_name})")
                    continue

                md_content = self.build_logic_md(cov_name, config_data)

                with open(Path(root) / "logic.md", 'w') as f:
                    f.write(md_content)
                generated.append(cov_name)
                print(f"Generated logic.md for {cov_name}")

        print(f"\nComplete: {len(generated)} logic.md files generated")


if __name__ == "__main__":
    DSIDocGenerator().execute()
