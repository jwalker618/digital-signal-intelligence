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

    def _signals_by_group(self, config: dict) -> dict:
        """Bucket full signal objects by their assigned group id."""
        signals = config.get('signal_registry', [])
        by_group = defaultdict(list)
        for sig in signals:
            tla = sig.get('three_layer_assessment', {})
            cats = sig.get('categories', {})
            gid = tla.get('group_id') or cats.get('group_id') or 'ungrouped'
            by_group[gid].append(sig)
        return dict(by_group)

    def _signal_layer_summary(self, sig: dict) -> dict:
        """Extract per-layer weights and correlation direction for a scored signal."""
        tla = sig.get('three_layer_assessment', {})
        risk = tla.get('risk', {})
        loss = tla.get('loss', {})
        exposure = tla.get('exposure', {})

        loss_freq = loss.get('frequency', {}).get('weight', 0)
        loss_sev = loss.get('severity', {}).get('weight', 0)

        exp_weight = 0.0
        exp_dims = []
        for dim, cfg in exposure.items():
            if isinstance(cfg, dict) and 'weight' in cfg:
                exp_weight += cfg['weight']
                exp_dims.append(dim)

        direction = (
            risk.get('correlation_direction')
            or loss.get('frequency', {}).get('correlation_direction')
            or loss.get('severity', {}).get('correlation_direction')
        )
        for cfg in exposure.values():
            if not direction and isinstance(cfg, dict):
                direction = cfg.get('correlation_direction')

        return {
            'risk': risk.get('weight', 0),
            'loss_freq': loss_freq,
            'loss_sev': loss_sev,
            'exposure': round(exp_weight, 3),
            'exposure_dims': exp_dims,
            'direction': direction,
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

        # Group definitions — surface the human-readable description of each group
        groups = config.get('groups', {}).get('three_layer_assessment', [])
        described = [g for g in groups if g.get('description')]
        if described:
            md += "**Group Definitions:**\n"
            for g in described:
                md += f"- **{g.get('label', g.get('id'))}:** {g['description']}\n"
            md += "\n"
        md += (
            "*Reading the table: a group's three weights are independent. The same group "
            "can be a dominant driver of one pillar and a minor input to another — e.g. a "
            "group may carry most of the Exposure weight while contributing little to Risk.*\n\n"
        )

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

    def _generate_signal_detail_section(self, config: dict) -> str:
        """Generate a per-group breakdown of individual signals and their layer weights."""
        groups = config.get('groups', {}).get('three_layer_assessment', [])
        by_group = self._signals_by_group(config)

        md = "### Signal Detail by Group\n"
        md += (
            "> *Each signal is an objectively observable data point. The weights show how "
            "strongly that signal informs each assessment pillar; correlation direction "
            "indicates whether a higher observed value increases (+) or decreases (-) the "
            "assessed exposure.*\n\n"
        )

        # Iterate groups in their configured order, then any unassigned bucket.
        ordered_ids = [g['id'] for g in groups]
        for gid in [g['id'] for g in groups] + [k for k in by_group if k not in ordered_ids]:
            sigs = by_group.get(gid, [])
            if not sigs:
                continue
            group_meta = next((g for g in groups if g['id'] == gid), {})
            label = group_meta.get('label', gid)
            md += f"#### {label}\n"
            if group_meta.get('description'):
                md += f"*{group_meta['description']}*\n\n"

            scored = [s for s in sigs if 'three_layer_assessment' in s]
            categorical = [s for s in sigs if 'categories' in s]

            if scored:
                md += "| Signal | Proxy Tier | Risk | Loss (Freq/Sev) | Exposure | Dir |\n"
                md += "|--------|-----------|------|-----------------|----------|-----|\n"
                for s in scored:
                    ls = self._signal_layer_summary(s)
                    direction = ls['direction'] or ''
                    dir_sym = {'positive': '+', 'negative': '-'}.get(direction, direction)
                    loss_cell = f"{ls['loss_freq']:.2f} / {ls['loss_sev']:.2f}"
                    md += (
                        f"| `{s.get('id', 'unknown')}` | {s.get('proxy_tier', 'UNKNOWN')} "
                        f"| {ls['risk']:.2f} | {loss_cell} | {ls['exposure']:.2f} | {dir_sym} |\n"
                    )
                md += "\n"

            for s in categorical:
                cats = s.get('categories', {})
                features = cats.get('features', [])
                md += (
                    f"**Categorical signal `{s.get('id', 'unknown')}`** — "
                    f"proxy tier: `{s.get('proxy_tier', 'UNKNOWN')}`, "
                    f"source: `{cats.get('source', 'n/a')}`\n\n"
                )
                if features:
                    md += "| Category | Label | Applied Factor |\n"
                    md += "|----------|-------|----------------|\n"
                    for f in features:
                        md += (
                            f"| `{f.get('cat', '')}` | {f.get('label', '')} "
                            f"| {f.get('applied', '')} |\n"
                        )
                    md += "\n"

        return md

    def _generate_pricing_translation_section(self, config: dict) -> str:
        """Show how each pillar's tier score converts into a pricing action or modifier."""
        md = "### Three-Layer Pricing Translation\n"
        md += (
            "> *How each pillar's tier score becomes a concrete underwriting action or "
            "pricing modifier. This is the bridge between signal observation and premium.*\n\n"
        )

        risk_bands = config.get('risk_tier_bands', {}).get('bands', [])
        if risk_bands:
            md += "**Risk -> Underwriting Action & Base Rate**\n\n"
            md += "| Tier | Score Band | Action | Rate / Method |\n"
            md += "|------|-----------|--------|---------------|\n"
            for b in sorted(risk_bands, key=lambda x: x.get('id', 0)):
                interp = b.get('interpretation', {})
                bands = interp.get('bands', {})
                app = interp.get('application', {})
                rate = app.get('applied')
                method = app.get('method', '')
                rate_cell = f"{rate * 100:g}% ({method})" if rate is not None else method
                md += (
                    f"| {b.get('label', b.get('id'))} "
                    f"| {bands.get('min', '?')}-{bands.get('max', '?')} "
                    f"| {interp.get('action', '')} | {rate_cell} |\n"
                )
            md += "\n"

        loss_bands = config.get('loss_tier_bands', {}).get('bands', [])
        if loss_bands:
            md += "**Loss -> Frequency & Severity Modifiers**\n\n"
            md += "| Tier | Score Band | Frequency Modifier | Severity Modifier |\n"
            md += "|------|-----------|--------------------|-------------------|\n"
            for b in sorted(loss_bands, key=lambda x: x.get('id', 0)):
                interp = b.get('interpretation', {})
                bands = interp.get('bands', {})
                app = interp.get('application', {})
                md += (
                    f"| {b.get('label', b.get('id'))} "
                    f"| {bands.get('min', '?')}-{bands.get('max', '?')} "
                    f"| {app.get('frequency_modifier', '')} "
                    f"| {app.get('severity_modifier', '')} |\n"
                )
            constraints = config.get('loss_tier_bands', {}).get('constraints', {})
            md += "\n"
            if constraints:
                md += (
                    f"*Loss modifier is bounded: floor {constraints.get('floor', 'n/a')}, "
                    f"cap {constraints.get('cap', 'n/a')}.*\n\n"
                )

        exposure = config.get('exposure', {})
        for dim, dim_cfg in exposure.items():
            if not isinstance(dim_cfg, dict):
                continue
            bands = dim_cfg.get('bands', [])
            if not bands:
                continue
            md += f"**Exposure ({dim}) -> Scale Modifier**\n\n"
            md += "| Band | Score Band | Modifier | Implied Value Range |\n"
            md += "|------|-----------|----------|---------------------|\n"
            for b in sorted(bands, key=lambda x: x.get('id', 0)):
                interp = b.get('interpretation', {})
                score = interp.get('bands', {})
                app = interp.get('application', {})
                thresh = app.get('implied_thresholds', {})
                t_min = thresh.get('min') if thresh else None
                t_max = thresh.get('max') if thresh else None
                if t_min is not None or t_max is not None:
                    lo = f"${t_min:,.0f}" if t_min is not None else "-"
                    hi = f"${t_max:,.0f}" if t_max is not None else "+"
                    val_range = f"{lo} - {hi}"
                else:
                    val_range = "n/a"
                md += (
                    f"| {b.get('label', b.get('id'))} "
                    f"| {score.get('min', '?')}-{score.get('max', '?')} "
                    f"| {app.get('applied', '')} | {val_range} |\n"
                )
            md += "\n"

        return md

    def _example_basis_value(self, config: dict, basis: str) -> float:
        """Derive a routing-valid example value for the pricing basis (e.g. tiv)."""
        routing = config.get('metadata', {}).get('routing_constraints', [])
        lower = None
        upper = None
        for r in routing:
            if r.get('field') != basis:
                continue
            val = r.get('value')
            if not isinstance(val, (int, float)):
                continue
            if r.get('operator') in ('>=', '>'):
                lower = val if lower is None else max(lower, val)
            elif r.get('operator') in ('<=', '<'):
                upper = val if upper is None else min(upper, val)

        if lower is not None and upper is not None:
            candidate = lower * 3
            return candidate if candidate < upper else (lower + upper) / 2
        if lower is not None:
            return lower * 3
        if upper is not None:
            return upper / 2
        return 10_000_000

    def _exposure_modifier_for_value(self, config: dict, value: float) -> tuple:
        """Find the exposure size band a basis value falls into; return (label, modifier)."""
        size_bands = config.get('exposure', {}).get('size', {}).get('bands', [])
        for band in size_bands:
            app = band.get('interpretation', {}).get('application', {})
            thresh = app.get('implied_thresholds') or {}
            lo, hi = thresh.get('min'), thresh.get('max')
            if lo is None and hi is None:
                continue
            if (lo is None or value >= lo) and (hi is None or value < hi):
                return band.get('label', band.get('id')), app.get('applied')
        return None, None

    def _deductible_factor(self, pt_cfg: dict, deductible: float) -> float:
        """Look up the deductible factor for a given deductible amount."""
        for df in pt_cfg.get('deductible_factors', []):
            if df.get('deductible') == deductible:
                return df.get('factor')
        return None

    def _generate_theoretical_pricing(self, config: dict) -> str:
        """Generate a worked premium calculation showing the full factor chain."""
        pricing = config.get('pricing', {})
        b_limit = pricing.get('base_limit_reference', 0)
        b_ded = pricing.get('base_deductible_reference', 0)

        tier_bands = config.get('risk_tier_bands', {}).get('bands', [])
        t3 = next((b for b in tier_bands if b['id'] == 3), tier_bands[0] if tier_bands else {})
        app = t3.get('interpretation', {}).get('application', {})
        method = app.get('method', 'UNKNOWN')

        md = "### Theoretical Premium Calculation (Worked Example)\n"

        if method == "MULTIPLIER":
            rate = app.get('applied', 0)
            rate_pct = round(rate * 100, 4)
            basis = app.get('basis', 'exposure')
            basis_value = self._example_basis_value(config, basis)
            base_premium = basis_value * rate

            # ILF / deductible factors are keyed by product type; use the primary one.
            by_pt = pricing.get('by_product_type', {})
            pt_cfg = by_pt.get('commercial_property') or (
                next(iter(by_pt.values())) if by_pt else {}
            )
            anchor_limit = pt_cfg.get('ilf_curve', {}).get('anchor_limit', b_limit)
            ded_factor = self._deductible_factor(pt_cfg, b_ded)
            if ded_factor is None:
                ded_factor = 1.0
            ilf = 1.0  # client assumed to request the anchor limit

            # Loss pillar — bounds applied to the combined frequency × severity modifier.
            loss_cfg = config.get('loss_tier_bands', {})
            loss_bands = loss_cfg.get('bands', [])
            loss_constraints = loss_cfg.get('constraints', {})
            floor = loss_constraints.get('floor')
            cap = loss_constraints.get('cap')

            def loss_modifier(band):
                la = band.get('interpretation', {}).get('application', {})
                combined = la.get('frequency_modifier', 1.0) * la.get('severity_modifier', 1.0)
                if floor is not None:
                    combined = max(combined, floor)
                if cap is not None:
                    combined = min(combined, cap)
                return combined

            # The worked example holds Risk at Tier 3 (STANDARD) but uses an ELEVATED
            # Loss tier so the loss loading is visible rather than collapsing to 1.00.
            example_loss = next(
                (b for b in loss_bands if b.get('id') == 4),
                next((b for b in loss_bands if b.get('id') == 3), {}),
            )
            loss_app = example_loss.get('interpretation', {}).get('application', {})
            freq_mod = loss_app.get('frequency_modifier', 1.0)
            sev_mod = loss_app.get('severity_modifier', 1.0)
            loss_mod = loss_modifier(example_loss)

            # Exposure pillar — size modifier for the example basis value.
            exp_label, exp_mod = self._exposure_modifier_for_value(config, basis_value)
            if exp_mod is None:
                exp_mod, exp_label = 1.0, 'n/a'

            final = base_premium * ilf * ded_factor * loss_mod * exp_mod

            md += "> *Per the DSI Premium Calculation Methodology v2.0, the full factor chain is:*\n"
            md += ("> *P_final = (Basis × Base Rate) × ILF_relativity × Deductible_Factor "
                   "× Loss_Modifier × Exposure_Modifier*\n\n")
            md += ("**Worked example — Risk Tier 3 (STANDARD), Loss Tier "
                   f"{example_loss.get('id', '?')} ({example_loss.get('label', '')}), "
                   "requesting the anchor limit/deductible:**\n\n")
            md += "| Factor | Source | Value |\n"
            md += "|--------|--------|-------|\n"
            md += f"| `{basis}` (rating basis) | Routing-valid assumption | ${basis_value:,.0f} |\n"
            md += f"| Base Rate | Risk Tier 3 (STANDARD) | {rate_pct:g}% |\n"
            md += f"| **Base Premium** | `{basis}` × Base Rate | **${base_premium:,.0f}** |\n"
            md += f"| ILF relativity | Limit = anchor (${anchor_limit:,.0f}) | {ilf:.2f} |\n"
            md += f"| Deductible factor | Deductible = anchor (${b_ded:,.0f}) | {ded_factor:.2f} |\n"
            md += (f"| Loss frequency modifier | Loss Tier "
                   f"{example_loss.get('id', '?')} ({example_loss.get('label', '')}) "
                   f"| {freq_mod:.2f} |\n")
            md += (f"| Loss severity modifier | Loss Tier "
                   f"{example_loss.get('id', '?')} ({example_loss.get('label', '')}) "
                   f"| {sev_mod:.2f} |\n")
            bound_note = ""
            if floor is not None and cap is not None:
                bound_note = f", bounded [{floor:g}, {cap:g}]"
            md += (f"| **Loss modifier** | Frequency × Severity{bound_note} "
                   f"| **{loss_mod:.2f}** |\n")
            md += f"| Exposure modifier | Size band {exp_label} | {exp_mod:.2f} |\n"
            md += f"| **Technical Premium** | Product of all factors | **${final:,.0f}** |\n\n"
            md += (
                f"*Basis vs. limit: `{basis}` is the total insured value the rate is applied "
                f"to — a Base Rate of {rate_pct:g}% on `{basis}` is the rated cost of risk, "
                f"not the policy limit. The policy Limit (anchored at ${anchor_limit:,.0f}) is "
                f"the maximum payout and scales premium independently via the ILF curve; "
                f"requesting a limit above the anchor lifts the ILF relativity above 1.00.*\n\n"
            )

            # Loss tier sensitivity — hold Risk and Exposure constant, vary the Loss tier.
            if loss_bands:
                md += ("**Loss Tier Sensitivity** — holding Risk Tier 3 and the Exposure "
                       "modifier constant, the technical premium moves with the Loss tier:\n\n")
                md += "| Loss Tier | Freq Mod | Sev Mod | Loss Modifier | Technical Premium |\n"
                md += "|-----------|----------|---------|---------------|-------------------|\n"
                for b in sorted(loss_bands, key=lambda x: x.get('id', 0)):
                    la = b.get('interpretation', {}).get('application', {})
                    lm = loss_modifier(b)
                    prem = base_premium * ilf * ded_factor * lm * exp_mod
                    marker = "  *(example)*" if b.get('id') == example_loss.get('id') else ""
                    md += (f"| {b.get('id', '?')} {b.get('label', '')}{marker} "
                           f"| {la.get('frequency_modifier', 1.0):.2f} "
                           f"| {la.get('severity_modifier', 1.0):.2f} "
                           f"| {lm:.2f} | ${prem:,.0f} |\n")
                md += "\n"
        elif method == "PREMIUM_BASE":
            val = app.get('value', 0)
            md += "> *Per the DSI Premium Calculation Methodology v2.0, the core formula is:*\n"
            md += "> *P_final = Base Package Premium × Modifiers*\n\n"
            md += (f"**1. The Pricing Anchor:** The Flat Premium of `${val:,.0f}` purchases "
                   f"exactly the `${b_limit:,.0f}` Limit / `${b_ded:,.0f}` Deductible Base "
                   f"Package.\n")
            md += "**2. Theoretical Execution:**\n"
            md += f"  - Technical Premium = **${val:,.0f}**\n"
            md += ("  - *Scaling relies entirely on selecting a different Limit ID from the "
                   "Bundled limit_configuration packages.*\n")

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

        md += "## The Three-Layer Assessment Engine\n"
        md += (
            "Every DSI model scores a risk across three independent pillars before any "
            "premium is calculated. Each pillar answers a distinct underwriting question "
            "and enters the pricing formula at a different point:\n\n"
        )
        md += (
            "- **Risk** — *How likely is this account to behave badly?* Signal evidence is "
            "aggregated into a quality score that maps to an underwriting action "
            "(approve / refer / decline) and selects the base rate applied to the exposure basis.\n"
        )
        md += (
            "- **Loss** — *If a loss occurs, how often and how severe?* Scored separately into "
            "frequency and severity modifiers, letting the model distinguish attritional-loss "
            "accounts from low-frequency / high-severity ones.\n"
        )
        md += (
            "- **Exposure** — *How much value is at stake?* Scales premium to the size of the "
            "insured object, independent of risk quality.\n\n"
        )
        md += (
            "Within each pillar, signals are organised into groups (e.g. Construction Quality, "
            "Occupancy Risk). The weight tables show how much each group contributes to each "
            "pillar; the signal detail tables show how each individual signal informs them. "
            "Critically, a single signal can carry very different weight across the three "
            "pillars — highly predictive of loss severity, say, yet barely moving the exposure "
            "score.\n\n"
        )

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

            # Signal Detail by Group
            md += self._generate_signal_detail_section(config)

            # Group Importance
            md += self._generate_group_importance_section(config)

            # Three-Layer Pricing Translation
            md += self._generate_pricing_translation_section(config)

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
