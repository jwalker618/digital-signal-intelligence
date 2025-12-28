"""
DSI Model Pricer

Calculates premium from score and conditions (Steps 8-12).

Step 8: Maximum tier override application
Step 9: Final tier capture
Step 10: Base premium generation
Step 11: Modifier application
Step 12: Limit band scaling
"""

from .types import (
    CoverageConfig,
    TierConfig,
    LimitBand,
    PricingResult,
    ModifierApplication,
    PremiumMethod,
)


class ModelPricer:
    """
    Calculates premium from score and conditions.
    
    All pricing parameters come from YAML configuration.
    Nothing is hardcoded.
    """
    
    def price_submission(
        self,
        pure_composite_score: float,
        signal_tier_overrides: list[int],
        query_tier_overrides: list[int],
        query_modifiers: list[dict],
        categorical_selections: dict[str, str],
        submission_data: dict,
        config: CoverageConfig
    ) -> PricingResult:
        """
        Execute Steps 8-12 of the pricing workflow.
        
        Args:
            pure_composite_score: Score from Step 5 (0-1000)
            signal_tier_overrides: Tier overrides from Step 6
            query_tier_overrides: Tier overrides from Step 7
            query_modifiers: Modifiers from Step 7
            categorical_selections: Selected categories for categorical features
            submission_data: Submission data (for rate basis values)
            config: Coverage configuration
        
        Returns:
            PricingResult with full breakdown
        """
        result = PricingResult(score_based_tier=0)
        
        # Step 8: Resolve tier overrides
        score_based_tier = self._score_to_tier(pure_composite_score, config)
        result.score_based_tier = score_based_tier
        
        all_overrides = signal_tier_overrides + query_tier_overrides
        result.tier_overrides_considered = all_overrides
        
        final_tier = self.resolve_tier_overrides(
            score_tier=score_based_tier,
            overrides=all_overrides
        )
        result.max_tier_override = max(all_overrides) if all_overrides else None
        
        # Step 9: Final tier
        result.final_tier = final_tier
        
        # Step 10: Base premium
        base_premium, method, rate_basis_value = self.calculate_base_premium(
            tier=final_tier,
            submission_data=submission_data,
            config=config
        )
        result.base_premium = base_premium
        result.base_premium_method = method
        result.rate_basis_value = rate_basis_value
        
        # Step 11: Apply modifiers
        premium_after_mods, modifiers_applied = self.apply_modifiers(
            base_premium=base_premium,
            categorical_selections=categorical_selections,
            query_modifiers=query_modifiers,
            config=config
        )
        result.modifiers_applied = modifiers_applied
        result.premium_after_modifiers = premium_after_mods
        
        # Step 12: Scale to limit bands
        limit_premiums = self.scale_to_limits(
            premium=premium_after_mods,
            config=config
        )
        result.limit_premiums = limit_premiums
        
        return result
    
    # =========================================================================
    # STEP 8: TIER OVERRIDE RESOLUTION
    # =========================================================================
    
    def resolve_tier_overrides(
        self,
        score_tier: int,
        overrides: list[int]
    ) -> int:
        """
        Apply maximum tier override.
        
        If multiple tier overrides triggered, apply the MAXIMUM (worst) tier.
        Higher tier number = worse risk = higher premium.
        
        Example: Score says Tier 2, conditions say Tier 3 and Tier 4 â apply Tier 4
        """
        if not overrides:
            return score_tier
        
        # Maximum override wins
        max_override = max(overrides)
        
        # Override only applies if it's worse than score-based tier
        return max(score_tier, max_override)
    
    def _score_to_tier(self, score: float, config: CoverageConfig) -> int:
        """Map composite score to tier using config thresholds"""
        tier_config = config.get_tier_for_score(score)
        if tier_config:
            return tier_config.tier
        
        # Fallback: find closest tier
        if not config.tier_thresholds:
            return 1  # Default to tier 1 if no config
        
        # If score is above all tiers, return worst tier
        # If score is below all tiers, return best tier
        sorted_tiers = sorted(config.tier_thresholds, key=lambda t: t.min_score)
        
        if score < sorted_tiers[0].min_score:
            return sorted_tiers[-1].tier  # Worst tier for very low scores
        if score > sorted_tiers[-1].max_score:
            return sorted_tiers[0].tier  # Best tier for very high scores
        
        return sorted_tiers[len(sorted_tiers) // 2].tier  # Middle tier as fallback
    
    # =========================================================================
    # STEP 10: BASE PREMIUM GENERATION
    # =========================================================================
    
    def calculate_base_premium(
        self,
        tier: int,
        submission_data: dict,
        config: CoverageConfig
    ) -> tuple[float, PremiumMethod, float | None]:
        """
        Calculate base premium for the final tier.
        
        Two options defined in YAML:
        - Option A (pure): Fixed premium per tier
        - Option B (rate_based): Metric * rate (e.g., TIV * 0.5%)
        
        Returns:
            Tuple of (premium, method, rate_basis_value)
        """
        # Find tier configuration
        tier_config = self._get_tier_config(tier, config)
        
        if tier_config is None:
            # No config for this tier - return minimum premium from metadata
            min_premium = config.metadata.get('min_premium', 1000)
            return (float(min_premium), PremiumMethod.PURE, None)
        
        # Option A: Pure premium
        if tier_config.base_premium is not None:
            return (tier_config.base_premium, PremiumMethod.PURE, None)
        
        # Option B: Rate-based
        if tier_config.rate is not None and tier_config.rate_basis is not None:
            rate_basis_value = submission_data.get(tier_config.rate_basis)
            
            if rate_basis_value is None:
                # Rate basis not provided - use minimum premium
                min_premium = config.metadata.get('min_premium', 1000)
                return (float(min_premium), PremiumMethod.RATE_BASED, None)
            
            premium = float(rate_basis_value) * tier_config.rate
            
            # Apply minimum premium floor
            min_premium = config.metadata.get('min_premium', 0)
            premium = max(premium, float(min_premium))
            
            return (premium, PremiumMethod.RATE_BASED, float(rate_basis_value))
        
        # Fallback
        min_premium = config.metadata.get('min_premium', 1000)
        return (float(min_premium), PremiumMethod.PURE, None)
    
    def _get_tier_config(self, tier: int, config: CoverageConfig) -> TierConfig | None:
        """Get tier configuration by tier number"""
        for t in config.tier_thresholds:
            if t.tier == tier:
                return t
        return None
    
    # =========================================================================
    # STEP 11: MODIFIER APPLICATION
    # =========================================================================
    
    def apply_modifiers(
        self,
        base_premium: float,
        categorical_selections: dict[str, str],
        query_modifiers: list[dict],
        config: CoverageConfig
    ) -> tuple[float, list[ModifierApplication]]:
        """
        Apply all modifiers in sequence.
        
        Order of application:
        1. Categorical feature modifiers
        2. Direct query modifiers (from Step 7)
        
        Modifiers are multiplicative.
        
        Returns:
            Tuple of (final_premium, modifiers_breakdown)
        """
        current_premium = base_premium
        modifiers_applied = []
        
        # 1. Apply categorical modifiers
        for group_name, selected_category in categorical_selections.items():
            if group_name not in config.categorical_features:
                continue
            
            category_modifiers = config.categorical_features[group_name]
            if selected_category not in category_modifiers:
                continue
            
            factor = category_modifiers[selected_category]
            premium_before = current_premium
            current_premium = current_premium * factor
            
            modifiers_applied.append(ModifierApplication(
                name=f"{group_name}:{selected_category}",
                factor=factor,
                premium_before=premium_before,
                premium_after=current_premium,
                source='categorical'
            ))
        
        # 2. Apply direct query modifiers
        for mod in query_modifiers:
            factor = mod.get('factor', 1.0)
            if factor == 1.0:
                continue
            
            premium_before = current_premium
            current_premium = current_premium * factor
            
            modifiers_applied.append(ModifierApplication(
                name=mod.get('name', 'query_modifier'),
                factor=factor,
                premium_before=premium_before,
                premium_after=current_premium,
                source='direct_query'
            ))
        
        return (current_premium, modifiers_applied)
    
    # =========================================================================
    # STEP 12: LIMIT BAND SCALING
    # =========================================================================
    
    def scale_to_limits(
        self,
        premium: float,
        config: CoverageConfig
    ) -> dict[float, float]:
        """
        Scale premium across all relevant limit bands.
        
        Uses ILF (Increased Limit Factor) table from configuration.
        
        Returns:
            Dict mapping limit -> premium
        """
        if not config.limit_bands:
            # No limit bands defined - return single premium
            return {0: premium}
        
        limit_premiums = {}
        
        # Sort bands by limit for consistent ordering
        sorted_bands = sorted(config.limit_bands, key=lambda b: b.limit)
        
        for band in sorted_bands:
            # Apply ILF factor
            limit_premium = premium * band.ilf
            limit_premiums[band.limit] = round(limit_premium, 2)
        
        return limit_premiums
    
    def apply_deductible_credit(
        self,
        premium: float,
        deductible: float,
        config: CoverageConfig
    ) -> tuple[float, float]:
        """
        Apply deductible credit to premium.
        
        Returns:
            Tuple of (adjusted_premium, credit_factor)
        """
        if not config.deductible_credits:
            return (premium, 1.0)
        
        # Find exact match or closest lower deductible
        credit = 1.0
        
        if deductible in config.deductible_credits:
            credit = config.deductible_credits[deductible]
        else:
            # Find closest lower deductible
            lower_deductibles = [
                d for d in config.deductible_credits.keys()
                if d <= deductible
            ]
            if lower_deductibles:
                closest = max(lower_deductibles)
                credit = config.deductible_credits[closest]
        
        adjusted_premium = premium * credit
        return (adjusted_premium, credit)
    
    def get_limit_options(
        self,
        premium: float,
        deductible: float,
        config: CoverageConfig
    ) -> list[dict]:
        """
        Get all limit/premium options with deductible applied.
        
        Returns list of options for presentation.
        """
        # Get base limit premiums
        limit_premiums = self.scale_to_limits(premium, config)
        
        options = []
        for limit, base_premium in limit_premiums.items():
            # Apply deductible credit
            adjusted_premium, credit = self.apply_deductible_credit(
                premium=base_premium,
                deductible=deductible,
                config=config
            )
            
            options.append({
                'limit': limit,
                'deductible': deductible,
                'base_premium': base_premium,
                'deductible_credit': credit,
                'final_premium': round(adjusted_premium, 2)
            })
        
        return sorted(options, key=lambda x: x['limit'])
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_pricing_breakdown(
        self,
        result: PricingResult,
        config: CoverageConfig
    ) -> dict:
        """
        Get detailed breakdown of pricing for audit/debug.
        """
        tier_config = self._get_tier_config(result.final_tier, config)
        
        return {
            'tier_resolution': {
                'score_based_tier': result.score_based_tier,
                'overrides_considered': result.tier_overrides_considered,
                'max_override': result.max_tier_override,
                'final_tier': result.final_tier
            },
            'base_premium': {
                'amount': result.base_premium,
                'method': result.base_premium_method.value,
                'rate_basis_value': result.rate_basis_value,
                'tier_decision': tier_config.decision.value if tier_config else 'unknown'
            },
            'modifiers': [
                {
                    'name': m.name,
                    'factor': m.factor,
                    'source': m.source,
                    'impact': m.premium_after - m.premium_before
                }
                for m in result.modifiers_applied
            ],
            'total_modifier_factor': self._calculate_total_modifier(result.modifiers_applied),
            'premium_after_modifiers': result.premium_after_modifiers,
            'limit_options': result.limit_premiums
        }
    
    def _calculate_total_modifier(self, modifiers: list[ModifierApplication]) -> float:
        """Calculate combined modifier factor"""
        if not modifiers:
            return 1.0
        
        total = 1.0
        for mod in modifiers:
            total *= mod.factor
        return round(total, 4)
    
    def validate_pricing_inputs(
        self,
        tier: int,
        categorical_selections: dict[str, str],
        config: CoverageConfig
    ) -> tuple[bool, list[str]]:
        """
        Validate pricing inputs against configuration.
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Validate tier exists
        if not self._get_tier_config(tier, config):
            errors.append(f"Invalid tier: {tier}")
        
        # Validate categorical selections
        for group_name, category in categorical_selections.items():
            if group_name not in config.categorical_features:
                errors.append(f"Unknown categorical group: {group_name}")
            elif category not in config.categorical_features.get(group_name, {}):
                errors.append(f"Invalid category '{category}' for group '{group_name}'")
        
        return (len(errors) == 0, errors)
