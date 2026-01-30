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

from .types import (
    CoverageConfig,
    TierConfig,
    PricingResult,
    AppliedModifier,
    CategoricalOutput,
    PremiumMethod,
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
            config: Coverage configuration

        Returns:
            PricingResult with complete pricing breakdown
        """
        # Step 8: Combine and resolve tier overrides
        all_overrides = signal_tier_overrides + query_tier_overrides
        score_based_tier = self.get_tier_for_score(pure_composite_score, config)
        final_tier, max_override = self.resolve_tier_overrides(
            score_based_tier.tier,
            all_overrides
        )

        # Step 9: Get final tier configuration
        final_tier_config = self.get_tier_config(final_tier, config)

        # Step 10: Calculate base premium
        base_premium, method = self.calculate_base_premium(
            tier=final_tier,
            tier_config=final_tier_config,
            submission_data=submission_data,
            config=config,
        )

        # Step 11: Apply modifiers
        modifiers_applied, total_modifier, premium_after_modifiers = self.apply_modifiers(
            base_premium=base_premium,
            categorical_outputs=categorical_outputs,
            query_modifiers=query_modifiers,
            config=config,
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
            # Use the premium for the selected limit or first available
            requested_limit = submission_data.get("limit")
            if requested_limit and str(int(requested_limit)) in limit_premiums:
                final_premium = limit_premiums[str(int(requested_limit))]
            else:
                # Use first limit band
                first_limit = min(limit_premiums.keys(), key=lambda x: float(x))
                final_premium = limit_premiums[first_limit]

        return PricingResult(
            tier_overrides_considered=all_overrides,
            max_tier_override=max_override,
            score_based_tier=score_based_tier.tier,
            final_tier=final_tier,
            tier_label=final_tier_config.label if final_tier_config else f"TIER_{final_tier}",
            tier_config=final_tier_config,
            base_premium=base_premium,
            base_premium_method=method,
            modifiers_applied=modifiers_applied,
            total_modifier=total_modifier,
            premium_after_modifiers=premium_after_modifiers,
            limit_premiums=limit_premiums,
            final_premium=final_premium,
        )

    def get_tier_for_score(
        self,
        score: float,
        config: CoverageConfig
    ) -> TierConfig:
        """
        Get tier configuration for a composite score.

        Args:
            score: Composite score (0-1000)
            config: Coverage configuration

        Returns:
            Matching TierConfig
        """
        return config.get_tier_for_score(score)

    def get_tier_config(
        self,
        tier: int,
        config: CoverageConfig
    ) -> Optional[TierConfig]:
        """
        Get tier configuration by tier number.

        Args:
            tier: Tier number (1-5)
            config: Coverage configuration

        Returns:
            TierConfig or None
        """
        for t in config.tiers:
            if t.tier == tier:
                return t
        return None

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
        tier_config: Optional[TierConfig],
        submission_data: Dict[str, Any],
        config: CoverageConfig
    ) -> Tuple[float, str]:
        """
        Step 10: Generate base premium from tier.

        Two methods:
        - PURE: Direct premium amount from tier config
        - RATE_BASED: Rate applied to metric (TIV, revenue, etc.)

        Args:
            tier: Final tier number
            tier_config: Tier configuration
            submission_data: Submission data with metrics
            config: Coverage configuration

        Returns:
            Tuple of (base_premium, method)
        """
        if tier_config is None:
            logger.warning(f"No config for tier {tier}, using default")
            return config.metadata.min_premium or 25000, "default"

        # v2.0: MULTIPLIER method - rate × basis value
        if tier_config.premium_method == PremiumMethod.MULTIPLIER:
            rate_basis = tier_config.rate_basis or "tiv"
            basis_value = submission_data.get(rate_basis, 0)

            if basis_value <= 0:
                logger.debug(f"No {rate_basis} value for MULTIPLIER, using PREMIUM_BASE fallback")
                return tier_config.base_premium or config.metadata.min_premium or 25000, "default"

            rate = tier_config.rate or tier_config.base_premium or 0
            base_premium = basis_value * rate
            return base_premium, "multiplier"

        # v2.0: PREMIUM_BASE - direct premium from tier
        if tier_config.premium_method == PremiumMethod.PREMIUM_BASE:
            if tier_config.base_premium is not None:
                return tier_config.base_premium, "premium_base"
            return config.metadata.min_premium or 25000, "default"

        # v1.0: RATE_BASED - rate applied to metric
        if tier_config.premium_method == PremiumMethod.RATE_BASED:
            if tier_config.rate is None:
                logger.warning("Rate-based tier missing rate, falling back to pure")
                return tier_config.base_premium or config.metadata.min_premium, "pure"

            rate_basis = tier_config.rate_basis or "tiv"
            basis_value = submission_data.get(rate_basis, 0)

            if basis_value <= 0:
                logger.debug(f"No {rate_basis} value, using pure premium")
                return tier_config.base_premium or config.metadata.min_premium, "pure"

            base_premium = basis_value * tier_config.rate
            return base_premium, "rate"

        # v1.0: PURE / default
        if tier_config.base_premium is not None:
            return tier_config.base_premium, "pure"
        return config.metadata.min_premium or 25000, "default"

    def apply_modifiers(
        self,
        base_premium: float,
        categorical_outputs: List[CategoricalOutput],
        query_modifiers: List[Dict[str, Any]],
        config: CoverageConfig
    ) -> Tuple[List[AppliedModifier], float, float]:
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

        # Apply query modifiers
        for mod in query_modifiers:
            factor = mod.get("factor", 1.0)
            if factor != 1.0:
                premium_before = current_premium
                current_premium *= factor
                total_modifier *= factor

                modifiers_applied.append(AppliedModifier(
                    source="direct_query",
                    source_id=mod.get("source_id", "unknown"),
                    name=mod.get("name", "Query modifier"),
                    factor=factor,
                    premium_before=premium_before,
                    premium_after=current_premium,
                ))

        logger.debug(
            f"Applied {len(modifiers_applied)} modifiers: "
            f"total_modifier={total_modifier:.3f}, "
            f"base={base_premium:.0f}, "
            f"final={current_premium:.0f}"
        )

        return modifiers_applied, total_modifier, current_premium

    def scale_to_limits(
        self,
        premium: float,
        submission_data: Dict[str, Any],
        config: CoverageConfig
    ) -> Dict[str, float]:
        """
        Step 12: Scale premium across limit bands.

        Uses ILF (Increased Limit Factor) tables to calculate
        premium for each available limit option.

        Args:
            premium: Premium after modifiers
            submission_data: Submission data
            config: Coverage configuration

        Returns:
            Dictionary of limit -> premium
        """
        if not config.limit_bands:
            # No limit bands defined, return single option
            return {}

        limit_premiums: Dict[str, float] = {}
        base_ilf = 1.0

        # Calculate for each limit band
        for band in config.limit_bands:
            limit = band.limit

            # Get ILF for this limit
            ilf = self._get_ilf_for_limit(limit, config.pricing)

            # Calculate premium
            limit_premium = premium * (ilf / base_ilf)

            # Apply deductible credit if applicable
            deductible = band.deductible
            if deductible > 0:
                credit = self._get_deductible_credit(
                    deductible,
                    submission_data,
                    config.pricing
                )
                limit_premium *= (1 - credit)

            limit_premiums[str(int(limit))] = round(limit_premium, 2)

        return limit_premiums

    def _get_ilf_for_limit(
        self,
        limit: float,
        pricing_config
    ) -> float:
        """
        Get Increased Limit Factor for a liability limit.

        Args:
            limit: The limit value
            pricing_config: Pricing configuration

        Returns:
            ILF factor
        """
        factors = pricing_config.liability_ilf_factors
        if not factors:
            return 1.0

        # Find appropriate factor or interpolate
        prev_factor = {"limit": 0, "factor": 1.0}

        for factor_def in factors:
            factor_limit = factor_def.get("limit", 0)
            factor_value = factor_def.get("factor", 1.0)

            if limit <= factor_limit:
                if limit == factor_limit:
                    return factor_value

                # Interpolate
                if prev_factor["limit"] < limit < factor_limit:
                    ratio = (limit - prev_factor["limit"]) / (factor_limit - prev_factor["limit"])
                    return prev_factor["factor"] + ratio * (factor_value - prev_factor["factor"])

                return factor_value

            prev_factor = {"limit": factor_limit, "factor": factor_value}

        # Above highest bracket
        return factors[-1].get("factor", 1.0) if factors else 1.0

    def _get_deductible_credit(
        self,
        deductible: float,
        submission_data: Dict[str, Any],
        pricing_config
    ) -> float:
        """
        Get deductible credit factor.

        Args:
            deductible: Deductible amount
            submission_data: Submission data (for basis value)
            pricing_config: Pricing configuration

        Returns:
            Credit factor (0-1)
        """
        credits = pricing_config.deductible_credits
        if not credits:
            return 0.0

        # Calculate deductible as percentage of basis (e.g., TIV)
        tiv = submission_data.get("tiv", 0)
        if tiv <= 0:
            return 0.0

        deductible_pct = deductible / tiv

        # Find matching credit band
        for credit_def in credits:
            min_pct = credit_def.get("min_pct", 0)
            max_pct = credit_def.get("max_pct")

            if max_pct is None:
                max_pct = float('inf')

            if min_pct <= deductible_pct < max_pct:
                return credit_def.get("credit", 0)

        return 0.0

    def calculate_hull_premium(
        self,
        hull_value: float,
        tier: int,
        tier_config: Optional[TierConfig],
        config: CoverageConfig
    ) -> float:
        """
        Calculate hull premium component (for combined coverage).

        Args:
            hull_value: Insured hull value
            tier: Final tier
            tier_config: Tier configuration
            config: Coverage configuration

        Returns:
            Hull premium
        """
        if hull_value <= 0:
            return 0.0

        # Get base rate per million from tier
        base_rate = tier_config.base_premium if tier_config else 2000
        hull_factor = hull_value / 1_000_000

        # Apply hull ILF
        hull_ilf = self._get_hull_ilf(hull_value, config.pricing)

        return base_rate * hull_factor * hull_ilf

    def _get_hull_ilf(
        self,
        hull_value: float,
        pricing_config
    ) -> float:
        """Get hull value ILF."""
        factors = pricing_config.hull_ilf_factors
        if not factors:
            return 1.0

        base_value = pricing_config.hull_ilf_base

        # Find appropriate factor
        prev_factor = {"value": 0, "factor": 1.0}

        for factor_def in factors:
            factor_value = factor_def.get("value", 0)
            factor = factor_def.get("factor", 1.0)

            if hull_value <= factor_value:
                if prev_factor["value"] < hull_value < factor_value:
                    # Interpolate
                    ratio = (hull_value - prev_factor["value"]) / (factor_value - prev_factor["value"])
                    return prev_factor["factor"] + ratio * (factor - prev_factor["factor"])
                return factor

            prev_factor = {"value": factor_value, "factor": factor}

        # Above highest bracket
        return factors[-1].get("factor", 1.0) if factors else 1.0


# Singleton instance for convenience
_default_pricer: Optional[ModelPricer] = None


def get_pricer() -> ModelPricer:
    """Get the default ModelPricer instance."""
    global _default_pricer
    if _default_pricer is None:
        _default_pricer = ModelPricer()
    return _default_pricer
