"""
Premium Assembly — Constructs Gross Premium from Technical Premium

The assembly layer sits between the technical pricer and the market.
It applies entity-specific commercial terms (brokerage, commission,
taxes, distribution structure) to produce the gross premium that
the insured actually pays.

Architecture:
    pricer.price_submission()
        → technical_premium (USD, single limit/deductible)
    premium_assembly.assemble()
        → PremiumBreakdown (gross, taxes, commission, in local CCY)

The assembly also handles:
    - FX conversion (submission CCY → USD → entity CCY)
    - Distribution structure (tower layers, subscription lines, packages)
    - ILF-based limit scaling across the distribution structure
    - Offered premium discretion

Usage:
    from layers.risk.premium_assembly import PremiumAssembler

    assembler = PremiumAssembler()
    breakdown = assembler.assemble(
        technical_premium_usd=125000.0,
        submission_data=submission_data,
        config=config,
        entity=entity,
        fx_context=fx_context,
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from infrastructure.models.commercial_schema import (
    CommercialEntity,
    DistributionType,
)
from infrastructure.models.config_schema import CoverageConfig
from layers.risk.fx import FXContext, FXConverter, get_fx_converter

logger = logging.getLogger("dsi.premium_assembly")


# =============================================================================
# OUTPUT STRUCTURES
# =============================================================================

@dataclass
class LayerBreakdown:
    """Premium breakdown for a single tower/subscription layer."""
    layer_id: int = 0
    layer_label: str = ""
    attachment: int = 0
    limit: int = 0
    order_premium: float = 0.0       # 100% basis premium for this layer
    signed_line: float = 1.0
    line_premium: float = 0.0        # Entity's share
    lead_loading: float = 1.0
    ilf_top: float = 0.0
    ilf_bottom: float = 0.0
    layer_ilf: float = 0.0


@dataclass
class CommissionBreakdown:
    """Breakdown of commission components."""
    brokerage: float = 0.0
    overrider: float = 0.0
    fronting_fee: float = 0.0
    total_commission: float = 0.0


@dataclass
class TaxBreakdown:
    """Breakdown of tax and levy components."""
    insurance_premium_tax: float = 0.0
    stamp_duty: float = 0.0
    regulatory_levy: float = 0.0
    fire_service_levy: float = 0.0
    total_taxes: float = 0.0


@dataclass
class PremiumBreakdown:
    """Complete premium breakdown from technical to gross.

    All amounts are in the entity's base_currency unless otherwise noted.
    """
    # Technical premium
    technical_premium_usd: float = 0.0
    technical_premium_local: float = 0.0

    # Distribution
    distribution_type: str = ""
    layers: List[LayerBreakdown] = field(default_factory=list)

    # Net premium (technical, potentially adjusted)
    net_premium: float = 0.0

    # Commission
    commission: CommissionBreakdown = field(default_factory=CommissionBreakdown)

    # Taxes
    taxes: TaxBreakdown = field(default_factory=TaxBreakdown)

    # Gross premium
    gross_premium: float = 0.0

    # Currency
    currency: str = "USD"

    # FX audit
    fx_rate: float = 1.0
    fx_source: str = ""
    fx_date: str = ""

    # Offered premium (may differ from gross)
    offered_premium: Optional[float] = None
    discretion_applied: float = 0.0


# =============================================================================
# ASSEMBLER
# =============================================================================

class PremiumAssembler:
    """Assembles gross premium from technical premium and commercial terms."""

    def __init__(self, fx_converter: Optional[FXConverter] = None):
        self._fx = fx_converter or get_fx_converter()

    def assemble(
        self,
        technical_premium_usd: float,
        submission_data: Dict[str, Any],
        config: CoverageConfig,
        entity: CommercialEntity,
        fx_context: Optional[FXContext] = None,
        requested_limit: Optional[int] = None,
        requested_deductible: Optional[int] = None,
    ) -> PremiumBreakdown:
        """Assemble gross premium from technical premium and commercial terms.

        Args:
            technical_premium_usd: Technical premium from pricer (USD).
            submission_data: Original submission data.
            config: Coverage configuration used for pricing.
            entity: Commercial entity terms.
            fx_context: FX context from input conversion (for rate consistency).
            requested_limit: Specific limit (if not in submission_data).
            requested_deductible: Specific deductible (if not in submission_data).

        Returns:
            PremiumBreakdown with full gross premium decomposition.
        """
        breakdown = PremiumBreakdown(
            technical_premium_usd=technical_premium_usd,
            distribution_type=entity.distribution.type.value,
            currency=entity.base_currency,
        )

        # Step 1: Convert technical premium to entity currency
        target_ccy = entity.base_currency.upper()
        if target_ccy == "USD":
            breakdown.technical_premium_local = technical_premium_usd
            breakdown.fx_rate = 1.0
        else:
            breakdown.technical_premium_local = self._fx.from_usd(
                technical_premium_usd, target_ccy, fx_context,
            )
            if fx_context:
                breakdown.fx_rate = fx_context.inverse_rate
                breakdown.fx_source = fx_context.rate_source
                breakdown.fx_date = fx_context.rate_date

        # Step 2: Apply distribution structure
        net = breakdown.technical_premium_local
        self._apply_distribution(breakdown, net, submission_data, config, entity,
                                 requested_limit, requested_deductible)

        # Step 3: Apply minimum gross premium
        if entity.pricing_adjustments.minimum_gross_premium > 0:
            net = max(net, entity.pricing_adjustments.minimum_gross_premium)

        breakdown.net_premium = net

        # Step 4: Calculate commission
        self._calculate_commission(breakdown, entity)

        # Step 5: Calculate taxes and levies
        self._calculate_taxes(breakdown, entity)

        # Step 6: Assemble gross premium
        # Gross = net + commission + taxes + fronting
        breakdown.gross_premium = round(
            breakdown.net_premium
            + breakdown.commission.total_commission
            + breakdown.taxes.total_taxes
            + breakdown.commission.fronting_fee,
            2,
        )

        return breakdown

    def _apply_distribution(
        self,
        breakdown: PremiumBreakdown,
        net_premium: float,
        submission_data: Dict[str, Any],
        config: CoverageConfig,
        entity: CommercialEntity,
        requested_limit: Optional[int],
        requested_deductible: Optional[int],
    ) -> None:
        """Apply distribution structure (tower/subscription/bundled/decoupled)."""
        dist = entity.distribution

        if dist.type == DistributionType.SUBSCRIPTION and dist.subscription:
            sub = dist.subscription
            signed_line = sub.default_signed_line
            lead_loading = sub.lead_loading_factor if sub.role.value == "LEAD" else 1.0
            line_premium = net_premium * signed_line * lead_loading

            breakdown.layers.append(LayerBreakdown(
                layer_id=1,
                layer_label="Primary",
                limit=int(submission_data.get("limit", 0)),
                order_premium=round(net_premium, 2),
                signed_line=signed_line,
                line_premium=round(line_premium, 2),
                lead_loading=lead_loading,
            ))

        elif dist.type == DistributionType.TOWER and dist.tower:
            tower = dist.tower
            total_limit = int(submission_data.get("limit", 0))
            product_type = submission_data.get(
                "product_type",
                config.metadata.product_types[0] if config.metadata.product_types else "standard",
            )

            if tower.layer_templates:
                for tmpl in tower.layer_templates:
                    attachment = int(tmpl.attachment_pct * total_limit)
                    layer_limit = int(tmpl.limit_pct * total_limit)

                    ilf_top = config.get_cumulative_ilf(product_type, attachment + layer_limit)
                    ilf_bottom = config.get_cumulative_ilf(product_type, attachment)
                    layer_ilf = ilf_top - ilf_bottom

                    # Layer premium relative to base (which already includes ILF for full limit)
                    full_ilf = config.get_ilf(product_type, total_limit)
                    if full_ilf > 0:
                        layer_premium = net_premium * (layer_ilf / full_ilf)
                    else:
                        layer_premium = net_premium

                    signed_line = 1.0
                    lead_loading = 1.0
                    if tower.subscription:
                        signed_line = tower.subscription.default_signed_line
                        if tower.subscription.role.value == "LEAD":
                            lead_loading = tower.subscription.lead_loading_factor

                    breakdown.layers.append(LayerBreakdown(
                        layer_id=tmpl.id,
                        layer_label=tmpl.label,
                        attachment=attachment,
                        limit=layer_limit,
                        order_premium=round(layer_premium, 2),
                        signed_line=signed_line,
                        line_premium=round(layer_premium * signed_line * lead_loading, 2),
                        lead_loading=lead_loading,
                        ilf_top=ilf_top,
                        ilf_bottom=ilf_bottom,
                        layer_ilf=layer_ilf,
                    ))

        # BUNDLED and DECOUPLED don't add layers — they use the flat premium

    def _calculate_commission(
        self,
        breakdown: PremiumBreakdown,
        entity: CommercialEntity,
    ) -> None:
        """Calculate commission components."""
        comm = entity.commission
        net = breakdown.net_premium

        brokerage = round(net * comm.brokerage_rate, 2)
        overrider = round(net * comm.overrider_rate, 2)

        fronting_fee = 0.0
        if entity.fronting.enabled:
            fronting_fee = round(net * entity.fronting.fronting_fee_rate, 2)

        breakdown.commission = CommissionBreakdown(
            brokerage=brokerage,
            overrider=overrider,
            fronting_fee=fronting_fee,
            total_commission=round(brokerage + overrider, 2),
        )

    def _calculate_taxes(
        self,
        breakdown: PremiumBreakdown,
        entity: CommercialEntity,
    ) -> None:
        """Calculate tax and levy components."""
        tax = entity.taxes_and_levies
        # Taxes typically applied to gross (net + commission)
        taxable_base = breakdown.net_premium + breakdown.commission.total_commission

        ipt = round(taxable_base * tax.insurance_premium_tax_rate, 2)
        stamp = round(taxable_base * tax.stamp_duty_rate, 2)
        reg_levy = round(taxable_base * tax.regulatory_levy_rate, 2)
        fire = round(taxable_base * tax.fire_service_levy_rate, 2)

        breakdown.taxes = TaxBreakdown(
            insurance_premium_tax=ipt,
            stamp_duty=stamp,
            regulatory_levy=reg_levy,
            fire_service_levy=fire,
            total_taxes=round(ipt + stamp + reg_levy + fire, 2),
        )
