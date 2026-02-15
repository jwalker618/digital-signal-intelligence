"""
DSI Coverage Documentation Generator

Generates dedicated logic.md documentation files for each coverage configuration.
Documents the logic, decision-making, and structure of each coverage YAML.

Each coverage directory gets a logic.md file documenting all configurations
(e.g., cyber_general and cyber_sme get sections in coverages/cyber/logic.md).

Usage:
    # From project root:
    python coverages/doc_generator.py

    # Programmatic usage:
    from coverages.doc_generator import CoverageDocGenerator
    generator = CoverageDocGenerator()
    generator.generate_all_documentation()
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("dsi.doc_generator")


class CoverageDocGenerator:
    """
    Generates comprehensive documentation for coverage configurations.

    Each coverage gets a dedicated .md file explaining:
    - Overview and purpose
    - Signal groups and their weights
    - Scoring logic and tier bands
    - Pricing structure (ILF, deductible factors)
    - Direct queries and their actions
    - Decision-making rationale
    """

    def __init__(
        self,
        coverages_dir: str = "coverages"
    ):
        self.coverages_dir = Path(coverages_dir)

    def generate_all_documentation(self) -> Dict[str, bool]:
        """Generate logic.md documentation for all coverage configs."""

        results = {}
        for coverage_dir in sorted(self.coverages_dir.iterdir()):
            if not coverage_dir.is_dir():
                continue

            config_path = coverage_dir / "config.yaml"
            if config_path.exists():
                try:
                    success = self.generate_documentation(
                        str(config_path),
                        coverage_dir.name
                    )
                    results[coverage_dir.name] = success
                except Exception as e:
                    logger.error(f"Failed to document {coverage_dir.name}: {e}")
                    results[coverage_dir.name] = False

        # Generate index file
        self._generate_index(results)

        return results

    def generate_documentation(self, config_path: str, coverage_name: str) -> bool:
        """Generate logic.md for a single coverage config."""
        logger.info(f"Generating documentation for {coverage_name}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if not config:
            logger.warning(f"Empty config: {config_path}")
            return False

        # Get coverage root key
        coverage_key = list(config.keys())[0]
        coverage_config = config[coverage_key]

        # Generate markdown content
        md_content = self._generate_markdown(
            coverage_name,
            coverage_key,
            coverage_config
        )

        # Write documentation file to coverages/<name>/logic.md
        output_path = self.coverages_dir / coverage_name / "logic.md"
        with open(output_path, 'w') as f:
            f.write(md_content)

        logger.info(f"Documentation written to {output_path}")
        return True

    def _generate_markdown(
        self,
        coverage_name: str,
        coverage_key: str,
        coverage_config: Dict[str, Any]
    ) -> str:
        """Generate markdown documentation content."""
        sections = []

        # Header
        sections.append(self._generate_header(coverage_name, coverage_key))

        # Process each configuration within the coverage
        for config_name, inner_config in coverage_config.items():
            if not isinstance(inner_config, dict):
                continue

            sections.append(f"\n---\n")
            sections.append(self._generate_config_section(config_name, inner_config))

        # Footer
        sections.append(self._generate_footer())

        return '\n'.join(sections)

    def _generate_header(self, coverage_name: str, coverage_key: str) -> str:
        """Generate document header."""
        title = coverage_name.replace('_', ' ').title()
        return f"""# {title} Coverage Configuration

**Coverage ID:** `{coverage_key}`
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Schema Version:** v2.2

This document describes the configuration, decision logic, and pricing structure
for the {title} coverage vertical in the DSI platform.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Signal Groups](#signal-groups)
3. [Scoring Logic](#scoring-logic)
4. [Pricing Structure](#pricing-structure)
5. [Direct Queries](#direct-queries)
6. [Decision Flow](#decision-flow)
"""

    def _generate_config_section(
        self,
        config_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate documentation section for a single configuration."""
        sections = []

        # Configuration header
        title = config_name.replace('_', ' ').title()
        sections.append(f"\n## Configuration: {title}\n")

        # Metadata
        if 'metadata' in config:
            sections.append(self._document_metadata(config['metadata']))

        # Signal Registry
        if 'signal_registry' in config:
            sections.append(self._document_signal_registry(config['signal_registry']))

        # Groups
        if 'groups' in config:
            sections.append(self._document_groups(config['groups']))

        # Risk Tier Bands
        if 'risk_tier_bands' in config:
            sections.append(self._document_risk_tiers(config['risk_tier_bands']))

        # Loss Tier Bands
        if 'loss_tier_bands' in config:
            sections.append(self._document_loss_tiers(config['loss_tier_bands']))

        # Direct Queries
        if 'direct_queries' in config:
            sections.append(self._document_direct_queries(config['direct_queries']))

        # Limit Configuration (BUNDLED or DECOUPLED)
        if 'limit_configuration' in config:
            sections.append(self._document_limit_configuration(config['limit_configuration']))
        # Legacy Limit Bandings (deprecated)
        elif 'limit_bandings' in config:
            sections.append(self._document_limit_bandings(config['limit_bandings']))

        # Pricing
        if 'pricing' in config:
            sections.append(self._document_pricing(config['pricing']))

        return '\n'.join(sections)

    def _document_metadata(self, metadata: Dict[str, Any]) -> str:
        """Document metadata section."""
        lines = ["### Metadata\n"]

        lines.append(f"- **Name:** {metadata.get('name', 'N/A')}")
        lines.append(f"- **Version:** {metadata.get('version', 'N/A')}")
        lines.append(f"- **Description:** {metadata.get('description', 'N/A')}")

        if 'product_types' in metadata:
            products = ', '.join(f"`{p}`" for p in metadata['product_types'])
            lines.append(f"- **Product Types:** {products}")

        if 'applicable_markets' in metadata:
            markets = ', '.join(metadata['applicable_markets'])
            lines.append(f"- **Markets:** {markets.upper()}")

        lines.append(f"- **Minimum Premium:** ${metadata.get('min_premium', 0):,}")
        lines.append(f"- **Currency:** {metadata.get('default_currency', 'USD')}")

        # V4 Multiplexer fields
        if 'model_specificity' in metadata:
            specificity = metadata['model_specificity']
            spec_labels = {1: "General", 2: "Segment", 3: "Niche", 4: "Bespoke", 5: "Custom"}
            lines.append(f"\n#### Multiplexer Configuration (V4)\n")
            lines.append(f"- **Model Specificity:** {specificity} ({spec_labels.get(specificity, 'Unknown')})")

            constraints = metadata.get('routing_constraints', [])
            if constraints:
                lines.append(f"- **Routing Constraints:**")
                for c in constraints:
                    field = c.get('field', 'unknown')
                    op = c.get('operator', '?')
                    value = c.get('value', '?')
                    required = "required" if c.get('required_in_input', False) else "optional"
                    lines.append(f"  - `{field} {op} {value}` ({required})")
            else:
                lines.append(f"- **Routing Constraints:** None (accepts all)")

        return '\n'.join(lines) + '\n'

    def _document_signal_registry(self, signals: List[Dict[str, Any]]) -> str:
        """Document signal registry."""
        lines = ["### Signal Registry\n"]
        lines.append(f"**Total Signals:** {len(signals)}\n")

        # Group signals by group_id
        by_group: Dict[str, List[Dict]] = {}
        for sig in signals:
            tla = sig.get('three_layer_assessment', {})
            cat = sig.get('categories', {})
            group_id = tla.get('group_id') or cat.get('group_id') or 'ungrouped'
            by_group.setdefault(group_id, []).append(sig)

        for group_id, group_signals in sorted(by_group.items()):
            lines.append(f"\n#### Group: `{group_id}`\n")
            lines.append("| Signal ID | Type | Weight | Direction | Proxy Tier |")
            lines.append("|-----------|------|--------|-----------|------------|")

            for sig in group_signals:
                sig_id = sig.get('id', 'unknown')
                proxy_tier = sig.get('proxy_tier', 'INFERRED_PROXY')

                tla = sig.get('three_layer_assessment', {})
                cat = sig.get('categories', {})

                if cat:
                    sig_type = "Categorical"
                    weight = "N/A"
                    direction = "modifier"
                else:
                    sig_type = "Scoring"
                    risk = tla.get('risk', {})
                    weight = f"{risk.get('weight', 0):.2%}"
                    direction = risk.get('correlation_direction', 'positive')

                lines.append(f"| `{sig_id}` | {sig_type} | {weight} | {direction} | {proxy_tier} |")

        return '\n'.join(lines) + '\n'

    def _document_groups(self, groups: Dict[str, Any]) -> str:
        """Document groups configuration."""
        lines = ["### Signal Groups\n"]

        # Categories
        categories = groups.get('categories', [])
        if categories:
            lines.append("#### Categorical Groups\n")
            lines.append("These groups apply modifiers based on classification:\n")
            lines.append("| Group ID | Label | Impact | Default |")
            lines.append("|----------|-------|--------|---------|")
            for cat in categories:
                lines.append(f"| `{cat.get('id')}` | {cat.get('label')} | {cat.get('impact')} | {cat.get('default_cat')} |")
            lines.append("")

        # Three Layer Assessment
        tla_groups = groups.get('three_layer_assessment', [])
        if tla_groups:
            lines.append("#### Three-Layer Assessment Groups\n")
            lines.append("These groups contribute to Risk, Loss, and Exposure scoring:\n")
            lines.append("| Group ID | Risk Weight | Loss Weight | Exposure Weight |")
            lines.append("|----------|-------------|-------------|-----------------|")
            for grp in tla_groups:
                risk_w = grp.get('risk', {}).get('weight', 0)
                loss_w = grp.get('loss', {}).get('weight', 0)
                exp_w = grp.get('exposure', {}).get('weight', 0)
                lines.append(f"| `{grp.get('id')}` | {risk_w:.0%} | {loss_w:.0%} | {exp_w:.0%} |")

        return '\n'.join(lines) + '\n'

    def _document_risk_tiers(self, risk_tiers: Dict[str, Any]) -> str:
        """Document risk tier bands and decision logic."""
        lines = ["### Risk Tier Bands\n"]
        lines.append("Risk tiers determine the base pricing and underwriting action:\n")

        bands = risk_tiers.get('bands', [])
        lines.append("| Tier | Label | Score Range | Action | Base Premium |")
        lines.append("|------|-------|-------------|--------|--------------|")

        for band in bands:
            tier_id = band.get('id')
            label = band.get('label')
            interp = band.get('interpretation', {})
            score_bands = interp.get('bands', {})
            action = interp.get('action', 'N/A')
            app = interp.get('application', {})

            score_range = f"{score_bands.get('min', 0)}-{score_bands.get('max', 100)}"

            if app.get('method') == 'PREMIUM_BASE':
                base_prem = f"${app.get('applied', 0):,}"
            elif app.get('applied'):
                base_prem = f"{app.get('applied')}x"
            else:
                base_prem = "N/A"

            lines.append(f"| {tier_id} | {label} | {score_range} | {action} | {base_prem} |")

        lines.append("\n**Decision Logic:**")
        lines.append("- Scores 0-1000 (composite from weighted signals)")
        lines.append("- Higher scores = better risk = lower tier number")
        lines.append("- APPROVE: Automatic binding eligible")
        lines.append("- REFER: Requires underwriter review")
        lines.append("- DECLINE: Outside risk appetite")

        return '\n'.join(lines) + '\n'

    def _document_loss_tiers(self, loss_tiers: Dict[str, Any]) -> str:
        """Document loss tier bands."""
        lines = ["### Loss Tier Bands\n"]
        lines.append("Loss tiers adjust premium based on expected loss frequency and severity:\n")

        bands = loss_tiers.get('bands', [])
        lines.append("| Tier | Label | Score Range | Freq Modifier | Sev Modifier |")
        lines.append("|------|-------|-------------|---------------|--------------|")

        for band in bands:
            tier_id = band.get('id')
            label = band.get('label')
            interp = band.get('interpretation', {})
            score_bands = interp.get('bands', {})
            app = interp.get('application', {})

            score_range = f"{score_bands.get('min', 0)}-{score_bands.get('max', 100)}"
            freq_mod = app.get('frequency_modifier', 1.0)
            sev_mod = app.get('severity_modifier', 1.0)

            lines.append(f"| {tier_id} | {label} | {score_range} | {freq_mod:.2f}x | {sev_mod:.2f}x |")

        constraints = loss_tiers.get('constraints', {})
        if constraints:
            lines.append(f"\n**Constraints:** Floor = {constraints.get('floor', 0):.2f}, Cap = {constraints.get('cap', 2):.2f}")

        return '\n'.join(lines) + '\n'

    def _document_direct_queries(self, queries: List[Dict[str, Any]]) -> str:
        """Document direct queries and their decision impact."""
        lines = ["### Direct Queries\n"]
        lines.append("Binary questions that cannot be inferred from external signals:\n")

        lines.append("| Query ID | Question | Trigger | Action | Impact |")
        lines.append("|----------|----------|---------|--------|--------|")

        for query in queries:
            query_id = query.get('id')
            question = query.get('question', '')[:50] + '...' if len(query.get('question', '')) > 50 else query.get('question', '')

            conditions = query.get('query_condition', [])
            for cond in conditions:
                trigger = f"Answer = {cond.get('return')}"
                action = cond.get('action', 'N/A')

                if cond.get('override'):
                    impact = f"Override to Tier {cond.get('override')}"
                elif cond.get('applied'):
                    impact = f"Modifier: {cond.get('applied')}x"
                else:
                    impact = cond.get('note', 'Flag only')

                lines.append(f"| `{query_id}` | {question} | {trigger} | {action} | {impact} |")

        lines.append("\n**Action Types:**")
        lines.append("- **FLAG:** Adds note to underwriter; no pricing impact")
        lines.append("- **MODIFIER:** Applies premium multiplier")
        lines.append("- **REFER:** Forces underwriter review regardless of score")

        return '\n'.join(lines) + '\n'

    def _document_pricing(self, pricing: Dict[str, Any]) -> str:
        """Document pricing structure."""
        lines = ["### Pricing Structure\n"]

        # Check for by_product_type structure
        if 'by_product_type' in pricing:
            lines.append("Pricing varies by product type:\n")
            for product_type, product_pricing in pricing['by_product_type'].items():
                lines.append(f"\n#### {product_type.replace('_', ' ').title()}\n")
                lines.append(self._format_single_pricing(product_pricing))
        else:
            lines.append(self._format_single_pricing(pricing))

        return '\n'.join(lines) + '\n'

    def _format_single_pricing(self, pricing: Dict[str, Any]) -> str:
        """Format a single pricing block."""
        lines = []

        # Pricing anchors (V5)
        if 'base_limit_reference' in pricing:
            lines.append("**Pricing Anchors (V5):**")
            lines.append(f"- Base Limit Reference: ${pricing.get('base_limit_reference', 0):,}")
            lines.append(f"- Base Deductible Reference: ${pricing.get('base_deductible_reference', 0):,}")
            lines.append("")

        # ILF Curve
        ilf_curve = pricing.get('ilf_curve', {})
        if ilf_curve:
            lines.append("**Increased Limit Factors (ILF):**\n")
            lines.append("| Limit | Factor | Premium Multiplier |")
            lines.append("|-------|--------|-------------------|")
            base_limit = ilf_curve.get('base_limit', 1000000)
            for factor_entry in ilf_curve.get('factors', []):
                limit = factor_entry.get('limit', 0)
                factor = factor_entry.get('factor', 1.0)
                is_base = " (base)" if limit == base_limit else ""
                lines.append(f"| ${limit:,}{is_base} | {factor:.2f} | {factor:.2f}x base |")
            lines.append("")

        # Deductible Factors (V5)
        ded_factors = pricing.get('deductible_factors', [])
        if ded_factors:
            lines.append("**Deductible Factors (V5):**\n")
            lines.append("| Deductible | Factor | Effect |")
            lines.append("|------------|--------|--------|")
            base_ded = pricing.get('base_deductible_reference', 50000)
            for df in ded_factors:
                ded = df.get('deductible', 0)
                factor = df.get('factor', 1.0)
                is_anchor = " (anchor)" if ded == base_ded else ""
                if factor > 1.0:
                    effect = f"+{(factor-1)*100:.0f}% loading"
                elif factor < 1.0:
                    effect = f"-{(1-factor)*100:.0f}% credit"
                else:
                    effect = "Base price"
                lines.append(f"| ${ded:,}{is_anchor} | {factor:.2f} | {effect} |")
            lines.append("")

        # Legacy deductible credits
        ded_credits = pricing.get('deductible_credits', [])
        if ded_credits:
            lines.append("**Deductible Credits (Legacy):**\n")
            lines.append("| Ded % of Limit | Credit |")
            lines.append("|----------------|--------|")
            for dc in ded_credits:
                min_pct = dc.get('min_pct', 0) * 100
                max_pct = dc.get('max_pct')
                max_str = f"{max_pct*100:.1f}%" if max_pct else "+"
                credit = dc.get('credit', 0)
                lines.append(f"| {min_pct:.1f}% - {max_str} | {credit:.0%} |")
            lines.append("")

        # Taxes & Fees
        if 'taxes_fees_rate' in pricing:
            lines.append(f"**Taxes & Fees Rate:** {pricing['taxes_fees_rate']:.0%}")

        return '\n'.join(lines)

    def _document_limit_configuration(self, limit_config: Dict[str, Any]) -> str:
        """Document limit_configuration section for BUNDLED or DECOUPLED types."""
        config_type = limit_config.get('type', 'UNKNOWN')
        lines = ["### Limit & Deductible Configuration\n"]
        lines.append(f"**Type:** `{config_type}`\n")

        if config_type == 'BUNDLED':
            lines.append("**Mode:** Menu Pricing (Fixed Packages)\n")
            lines.append("Pre-configured limit/deductible packages for simplified selection:\n")
            lines.append("| ID | Package | Limit | Deductible |")
            lines.append("|---:|---------|------:|----------:|")

            packages = limit_config.get('packages', [])
            for pkg in packages:
                pkg_id = pkg.get('id', 0)
                label = pkg.get('label', 'N/A')
                limit = pkg.get('limit', 0)
                ded = pkg.get('deductible', 0)
                lines.append(f"| {pkg_id} | {label} | ${limit:,} | ${ded:,} |")

            lines.append("")
            lines.append("*Clients select a package; the associated limit and deductible are applied automatically.*")

        elif config_type == 'DECOUPLED':
            lines.append("**Mode:** Tower Pricing (Independent Selection)\n")
            lines.append("Clients independently select from valid limits and deductibles. ")
            lines.append("Pricing scales via ILF curves and deductible factors.\n")

            valid_limits = limit_config.get('valid_limits', [])
            if valid_limits:
                lines.append("**Available Limits:**\n")
                for limit in valid_limits:
                    lines.append(f"- ${limit:,}")
                lines.append("")

            valid_deductibles = limit_config.get('valid_deductibles', [])
            if valid_deductibles:
                lines.append("**Available Deductibles:**\n")
                for ded in valid_deductibles:
                    lines.append(f"- ${ded:,}")
                lines.append("")

        else:
            lines.append(f"*Unknown limit_configuration type: {config_type}*\n")

        return '\n'.join(lines)

    def _document_limit_bandings(self, bandings: List[Dict[str, Any]]) -> str:
        """Document legacy limit bandings (deprecated)."""
        lines = ["### Limit Bandings (Legacy)\n"]
        lines.append("Pre-configured limit/deductible packages:\n")
        lines.append("| Package | Limit | Deductible |")
        lines.append("|---------|-------|------------|")

        for band in bandings:
            pkg_id = band.get('id', 0)
            limit = band.get('limit', 0)
            ded = band.get('deductible', 0)
            lines.append(f"| {pkg_id} | ${limit:,} | ${ded:,} |")

        return '\n'.join(lines) + '\n'

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return f"""
---

## Decision Flow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    DSI Decision Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SIGNAL EXTRACTION                                       │
│     └─► External APIs → Normalized Scores (0-100)          │
│                                                             │
│  2. GROUP AGGREGATION                                       │
│     └─► Weighted combination within groups                  │
│                                                             │
│  3. THREE-LAYER ASSESSMENT                                  │
│     ├─► Risk Score (0-1000)                                │
│     ├─► Loss Score (frequency × severity)                  │
│     └─► Exposure Score (size × complexity)                 │
│                                                             │
│  4. TIER ASSIGNMENT                                         │
│     └─► Risk Score → Tier Band → Base Premium              │
│                                                             │
│  5. DIRECT QUERIES                                          │
│     └─► Binary answers → FLAGS / MODIFIERS / REFERS        │
│                                                             │
│  6. PRICING CALCULATION                                     │
│     └─► Base × ILF × Ded Factor × Modifiers × Tax          │
│                                                             │
│  7. DECISION OUTPUT                                         │
│     └─► APPROVE / REFER / DECLINE + Audit Trail            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*Generated by DSI Coverage Documentation Generator*
"""

    def _generate_index(self, results: Dict[str, bool]) -> None:
        """Log index of generated documentation (no separate index file needed)."""
        # Each coverage now has its own logic.md in coverages/<name>/logic.md
        # No central index needed as documentation lives alongside configs
        successful = [c for c, s in results.items() if s]
        failed = [c for c, s in results.items() if not s]

        logger.info(f"Generated {len(successful)} logic.md files")
        if failed:
            logger.warning(f"Failed to generate: {', '.join(failed)}")


def generate_coverage_documentation() -> None:
    """CLI entry point for generating coverage documentation."""
    generator = CoverageDocGenerator()
    results = generator.generate_all_documentation()

    print("\n" + "=" * 60)
    print("DOCUMENTATION GENERATION REPORT")
    print("=" * 60)

    for coverage, success in sorted(results.items()):
        status = "Generated" if success else "Failed"
        output = f"coverages/{coverage}/logic.md" if success else ""
        print(f"  {coverage}: {status} {output}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotal: {passed}/{total} logic.md files generated")
    print(f"Output: coverages/<coverage>/logic.md")


if __name__ == "__main__":
    generate_coverage_documentation()
