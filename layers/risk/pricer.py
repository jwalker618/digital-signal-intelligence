"""
DSI Model Layer - Model Pricer (Phase 4)

Executes Steps 8-12 of the workflow:
- Step 8: Maximum Tier Override Application
- Step 9: Final Tier Capture
- Step 10: Base Premium Generation
- Step 11: Modifier Application
- Step 12: Limit Band Scaling

Calculates premium from score, tier, and modifiers.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

from infrastructure.models.config_schema import (
    CoverageConfig,
    Guardrails,
    RiskTierBand,
    TierAction,
    PricingMethod,
    LimitConfigType,
)

from .types import (
    PricingResult,
    AppliedModifier,
    BasePremiumDerivation,
    CategoricalOutput,
)


logger = logging.getLogger("dsi.pricer")


class PricingError(Exception):
    """Raised when pricing calculation fails."""
    pass


class ModelPricer:
    """
    Calculates premium from score and conditions (Steps 8-12).

    The pricing flow:
    1. Resolve tier from score and overrides
    2. Generate base premium from tier
    3. Apply categorical and query modifiers
    4. Scale across limit bands
    """

    def price_submission(
        self,
        pure_composite_score: float,
        signal_tier_overrides: List[int],
        query_tier_overrides: List[int],
        query_modifiers: List[Dict[str, Any]],
        categorical_outputs: List[CategoricalOutput],
        submission_data: Dict[str, Any],
        config: CoverageConfig
    ) -> PricingResult:
        """
        Execute Steps 8-12 to calculate premium.

        Args:
            pure_composite_score: Score from Step 5 (0-1000)
            signal_tier_overrides: Tier overrides from Step 6
            query_tier_overrides: Tier overrides from Step 7
            query_modifiers: Modifiers from Step 7
            categorical_outputs: Inferred categorical values
            submission_data: Submission data (for rate basis values)
            config: Coverage configuration (Pydantic compiled)

        Returns:
            PricingResult with complete pricing breakdown
        """
        # Step 8: Combine and resolve tier overrides
        all_overrides = signal_tier_overrides + query_tier_overrides
        score_based_band = self.get_tier_for_score(pure_composite_score, config)
        final_tier, max_override = self.resolve_tier_overrides(
            score_based_band.id,
            all_overrides
        )

        # Step 9: Get final tier band
        final_tier_band = config.get_tier_band(final_tier)

        # Step 10: Calculate base premium
        tier_label = final_tier_band.label if final_tier_band else f"TIER_{final_tier}"
        base_premium, method, base_premium_derivation = self.calculate_base_premium(
            tier=final_tier,
            tier_band=final_tier_band,
            submission_data=submission_data,
            config=config,
            tier_label=tier_label,
        )

        # Step 11: Apply modifiers
        modifiers_applied, total_modifier, premium_after_modifiers, modifier_was_clamped = (
            self.apply_modifiers(
                base_premium=base_premium,
                categorical_outputs=categorical_outputs,
                query_modifiers=query_modifiers,
                config=config,
            )
        )

        # Ensure minimum premium
        if config.metadata.min_premium > 0:
            premium_after_modifiers = max(premium_after_modifiers, config.metadata.min_premium)

        # Step 12: Scale to limit bands
        limit_premiums = self.scale_to_limits(
            premium=premium_after_modifiers,
            submission_data=submission_data,
            config=config,
        )

        # Determine final premium (use first limit band if available)
        final_premium = premium_after_modifiers
        if limit_premiums:
            requested_limit = submission_data.get("limit")
            if requested_limit and str(int(requested_limit)) in limit_premiums:
                final_premium = limit_premiums[str(int(requested_limit))]
            else:
                first_limit = min(limit_premiums.keys(), key=lambda x: float(x))
                final_premium = limit_premiums[first_limit]

        # Guardrail checks on final premium
        guardrail_warnings: List[str] = []
        premium_was_capped = False
        guardrails = config.guardrails

        if modifier_was_clamped:
            guardrail_warnings.append(
                f"MODIFIER_CLAMPED: total_modifier clamped to "
                f"[{guardrails.modifier_floor}, {guardrails.modifier_cap}]"
            )

        # Cap premium vs limit
        requested_limit = submission_data.get("limit", 0)
        if requested_limit and requested_limit > 0:
            max_premium_by_limit = requested_limit * guardrails.max_premium_to_limit_ratio
            if final_premium > max_premium_by_limit:
                guardrail_warnings.append(
                    f"PREMIUM_CAPPED_BY_LIMIT: {final_premium:.0f} exceeds "
                    f"{guardrails.max_premium_to_limit_ratio:.0%} of limit {requested_limit:.0f}, "
                    f"capped to {max_premium_by_limit:.0f}"
                )
                final_premium = max_premium_by_limit
                premium_was_capped = True
                # Also cap limit_premiums
                for lim_key in limit_premiums:
                    lim_val = float(lim_key)
                    cap = lim_val * guardrails.max_premium_to_limit_ratio
                    if limit_premiums[lim_key] > cap:
                        limit_premiums[lim_key] = round(cap, 2)

        # Cap premium vs revenue
        revenue = submission_data.get("revenue", 0)
        if revenue and revenue > 0:
            max_premium_by_revenue = revenue * guardrails.max_premium_to_revenue_ratio
            if final_premium > max_premium_by_revenue:
                guardrail_warnings.append(
                    f"PREMIUM_CAPPED_BY_REVENUE: {final_premium:.0f} exceeds "
                    f"{guardrails.max_premium_to_revenue_ratio:.2%} of revenue {revenue:.0f}, "
                    f"capped to {max_premium_by_revenue:.0f}"
                )
                final_premium = max_premium_by_revenue
                premium_was_capped = True
                for lim_key in limit_premiums:
                    if limit_premiums[lim_key] > max_premium_by_revenue:
                        limit_premiums[lim_key] = round(max_premium_by_revenue, 2)

        if guardrail_warnings:
            logger.warning(
                "Guardrails triggered for %s/%s: %s",
                config.coverage_id, config.config_id,
                "; ".join(guardrail_warnings),
            )

        return PricingResult(
            tier_overrides_considered=all_overrides,
            max_tier_override=max_override,
            score_based_tier=score_based_band.id,
            final_tier=final_tier,
            tier_label=tier_label,
            tier_config=None,  # Deprecated: use config.get_tier_band() directly
            base_premium=base_premium,
            base_premium_method=method,
            base_premium_derivation=base_premium_derivation,
            modifiers_applied=modifiers_applied,
            total_modifier=total_modifier,
            premium_after_modifiers=premium_after_modifiers,
            limit_premiums=limit_premiums,
            final_premium=final_premium,
            guardrail_warnings=guardrail_warnings,
            modifier_was_clamped=modifier_was_clamped,
            premium_was_capped=premium_was_capped,
        )

    def get_tier_for_score(
        self,
        score: float,
        config: CoverageConfig
    ) -> RiskTierBand:
        """
        Get tier band for a composite score.

        Args:
            score: Composite score (0-1000)
            config: Coverage configuration (Pydantic compiled)

        Returns:
            Matching RiskTierBand
        """
        for band in config.risk_tier_bands.bands:
            if band.interpretation.bands.min <= score <= band.interpretation.bands.max:
                return band
        # Default to last tier
        return config.risk_tier_bands.bands[-1]

    def get_tier_band(
        self,
        tier: int,
        config: CoverageConfig
    ) -> Optional[RiskTierBand]:
        """
        Get tier band by tier number.

        Args:
            tier: Tier number (1-5)
            config: Coverage configuration (Pydantic compiled)

        Returns:
            RiskTierBand or None
        """
        return config.get_tier_band(tier)

    def resolve_tier_overrides(
        self,
        score_tier: int,
        overrides: List[int]
    ) -> Tuple[int, Optional[int]]:
        """
        Step 8: Apply maximum tier override.

        When multiple tier overrides are triggered, the maximum (worst)
        tier is applied. Tier overrides can only make the tier worse,
        never better.

        Args:
            score_tier: Tier from composite score
            overrides: List of tier overrides from conditions

        Returns:
            Tuple of (final_tier, max_override)
        """
        if not overrides:
            return score_tier, None

        # Maximum override is the worst (highest number) tier
        max_override = max(overrides)

        # Final tier is the worse of score-based and override
        final_tier = max(score_tier, max_override)

        logger.debug(
            f"Tier resolution: score={score_tier}, "
            f"overrides={overrides}, "
            f"max_override={max_override}, "
            f"final={final_tier}"
        )

        return final_tier, max_override

    def calculate_base_premium(
        self,
        tier: int,
        tier_band: Optional[RiskTierBand],
        submission_data: Dict[str, Any],
        config: CoverageConfig,
        tier_label: str = "STANDARD",
    ) -> Tuple[float, str, BasePremiumDerivation]:
        """
        Step 10: Generate base premium from tier.

        Uses the Pydantic RiskTierBand.interpretation.application block:
        - PREMIUM_BASE: Direct premium amount from tier (application.value)
        - MULTIPLIER: Rate (application.applied) × basis value

        Args:
            tier: Final tier number
            tier_band: Risk tier band from compiled config
            submission_data: Submission data with metrics
            config: Coverage configuration (Pydantic compiled)
            tier_label: Human-readable tier label

        Returns:
            Tuple of (base_premium, method, derivation)
        """
        if tier_band is None:
            logger.warning(f"No config for tier {tier}, using default")
            result = config.metadata.min_premium or 25000
            derivation = BasePremiumDerivation(
                method="DEFAULT", tier=tier, tier_label=tier_label, result=result,
            )
            return result, "default", derivation

        app = tier_band.interpretation.application

        # MULTIPLIER: rate × basis value
        if app.method == PricingMethod.MULTIPLIER:
            rate_basis = app.basis or "tiv"
            basis_value = submission_data.get(rate_basis, 0)

            if basis_value <= 0:
                logger.debug(f"No {rate_basis} value for MULTIPLIER, using PREMIUM_BASE fallback")
                result = app.value or config.metadata.min_premium or 25000
                derivation = BasePremiumDerivation(
                    method="DEFAULT", basis_field=rate_basis,
                    tier=tier, tier_label=tier_label, result=result,
                )
                return result, "default", derivation

            rate = app.applied or 0
            base_premium = basis_value * rate
            derivation = BasePremiumDerivation(
                method="MULTIPLIER", basis_field=rate_basis,
                basis_value=basis_value, rate=rate,
                tier=tier, tier_label=tier_label, result=base_premium,
            )
            return base_premium, "multiplier", derivation

        # PREMIUM_BASE: direct premium from tier
        if app.method == PricingMethod.PREMIUM_BASE:
            if app.value is not None:
                result = float(app.value)
                derivation = BasePremiumDerivation(
                    method="PREMIUM_BASE",
                    tier=tier, tier_label=tier_label, result=result,
                )
                return result, "premium_base", derivation
            result = config.metadata.min_premium or 25000
            derivation = BasePremiumDerivation(
                method="DEFAULT", tier=tier, tier_label=tier_label, result=result,
            )
            return result, "default", derivation

        # MODIFIER or unknown: use value if available
        if app.value is not None:
            result = float(app.value)
            derivation = BasePremiumDerivation(
                method="DEFAULT", tier=tier, tier_label=tier_label, result=result,
            )
            return result, "pure", derivation
        result = config.metadata.min_premium or 25000
        derivation = BasePremiumDerivation(
            method="DEFAULT", tier=tier, tier_label=tier_label, result=result,
        )
        return result, "default", derivation

    def apply_modifiers(
        self,
        base_premium: float,
        categorical_outputs: List[CategoricalOutput],
        query_modifiers: List[Dict[str, Any]],
        config: CoverageConfig
    ) -> Tuple[List[AppliedModifier], float, float, bool]:
        """
        Step 11: Apply all modifiers in sequence.

        Modifiers are applied multiplicatively:
        - Categorical feature modifiers (from inferred categories)
        - Direct query modifiers (from Step 7)
        - Experience modifiers (if provided)

        Args:
            base_premium: Premium from Step 10
            categorical_outputs: Inferred categorical values
            query_modifiers: Modifiers from query evaluation
            config: Coverage configuration

        Returns:
            Tuple of (modifiers_applied, total_modifier, final_premium)
        """
        modifiers_applied: List[AppliedModifier] = []
        current_premium = base_premium
        total_modifier = 1.0

        # Apply categorical modifiers
        for cat_output in categorical_outputs:
            if cat_output.modifier != 1.0:
                premium_before = current_premium
                current_premium *= cat_output.modifier
                total_modifier *= cat_output.modifier

                modifiers_applied.append(AppliedModifier(
                    source="categorical",
                    source_id=cat_output.group_id,
                    name=f"{cat_output.group_name}: {cat_output.label}",
                    factor=cat_output.modifier,
                    premium_before=premium_before,
                    premium_after=current_premium,
                ))

        # Apply signal, query, and traditional modifiers
        for mod in query_modifiers:
            factor = mod.get("factor", 1.0)
            if factor != 1.0:
                premium_before = current_premium
                current_premium *= factor
                total_modifier *= factor

                modifiers_applied.append(AppliedModifier(
                    source=mod.get("source", "direct_query"),
                    source_id=mod.get("source_id", "unknown"),
                    name=mod.get("name", "Modifier"),
                    factor=factor,
                    premium_before=premium_before,
                    premium_after=current_premium,
                ))

        # Clamp total modifier within guardrail bounds
        guardrails = config.guardrails
        modifier_was_clamped = False
        if total_modifier < guardrails.modifier_floor:
            logger.info(
                f"Modifier {total_modifier:.3f} clamped to floor {guardrails.modifier_floor}"
            )
            total_modifier = guardrails.modifier_floor
            current_premium = base_premium * total_modifier
            modifier_was_clamped = True
        elif total_modifier > guardrails.modifier_cap:
            logger.info(
                f"Modifier {total_modifier:.3f} clamped to cap {guardrails.modifier_cap}"
            )
            total_modifier = guardrails.modifier_cap
            current_premium = base_premium * total_modifier
            modifier_was_clamped = True

        logger.debug(
            f"Applied {len(modifiers_applied)} modifiers: "
            f"total_modifier={total_modifier:.3f}, "
            f"base={base_premium:.0f}, "
            f"final={current_premium:.0f}"
        )

        return modifiers_applied, total_modifier, current_premium, modifier_was_clamped

    def scale_to_limits(
        self,
        premium: float,
        submission_data: Dict[str, Any],
        config: CoverageConfig
    ) -> Dict[str, float]:
        """
        Step 12: Scale premium across limit bands.

        Uses ILF (Increased Limit Factor) curves from Pydantic pricing config
        to calculate premium for each available limit option.

        Args:
            premium: Premium after modifiers
            submission_data: Submission data
            config: Coverage configuration (Pydantic compiled)

        Returns:
            Dictionary of limit -> premium
        """
        limit_config = config.limit_configuration
        if limit_config is None:
            return {}

        product_type = self._resolve_product_type(submission_data, config)
        limit_premiums: Dict[str, float] = {}

        if limit_config.type == LimitConfigType.BUNDLED and limit_config.packages:
            # BUNDLED: fixed limit/deductible packages
            for pkg in limit_config.packages:
                ilf = config.get_ilf(product_type, pkg.limit)
                ded_factor = config.get_deductible_factor(product_type, pkg.deductible)
                limit_premium = premium * ilf * ded_factor
                limit_premiums[str(pkg.limit)] = round(limit_premium, 2)

        elif limit_config.type == LimitConfigType.DECOUPLED and limit_config.valid_limits:
            # DECOUPLED: independent limit/deductible selection
            base_deductible = int(
                submission_data.get("deductible", config.pricing.base_deductible_reference)
            )
            ded_factor = config.get_deductible_factor(product_type, base_deductible)

            for limit in limit_config.valid_limits:
                ilf = config.get_ilf(product_type, limit)
                limit_premium = premium * ilf * ded_factor
                limit_premiums[str(limit)] = round(limit_premium, 2)

            # If the requested limit isn't in the standard menu, price it
            # via ILF interpolation so any limit can be quoted
            requested_limit = submission_data.get("limit")
            if requested_limit:
                req_key = str(int(requested_limit))
                if req_key not in limit_premiums:
                    ilf = config.get_ilf(product_type, int(requested_limit))
                    limit_premium = premium * ilf * ded_factor
                    limit_premiums[req_key] = round(limit_premium, 2)

        return limit_premiums

    def _resolve_product_type(
        self,
        submission_data: Dict[str, Any],
        config: CoverageConfig,
    ) -> str:
        """Resolve product type from submission data or config defaults."""
        product_type = submission_data.get("product_type")
        if product_type and product_type in config.pricing.by_product_type:
            return product_type
        # Default to first available product type
        if config.pricing.by_product_type:
            return next(iter(config.pricing.by_product_type))
        return "standard"

    def calculate_hull_premium(
        self,
        hull_value: float,
        tier: int,
        tier_band: Optional[RiskTierBand],
        config: CoverageConfig
    ) -> float:
        """
        Calculate hull premium component (for combined coverage).

        Args:
            hull_value: Insured hull value
            tier: Final tier
            tier_band: Risk tier band
            config: Coverage configuration (Pydantic compiled)

        Returns:
            Hull premium
        """
        if hull_value <= 0:
            return 0.0

        # Get base rate per million from tier
        base_rate = 2000
        if tier_band and tier_band.interpretation.application.value:
            base_rate = tier_band.interpretation.application.value
        hull_factor = hull_value / 1_000_000

        return base_rate * hull_factor


# Singleton instance for convenience
_default_pricer: Optional[ModelPricer] = None


def get_pricer() -> ModelPricer:
    """Get the default ModelPricer instance."""
    global _default_pricer
    if _default_pricer is None:
        _default_pricer = ModelPricer()
    return _default_pricer
