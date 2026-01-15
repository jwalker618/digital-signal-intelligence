"""
Loss Correlation Pricing Integration (Phase 16)

Provides integration patterns for incorporating loss propensity
into the pricing engine. Supports multiplicative, additive, and
grid-based pricing methods.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .types import (
    LossPropensityResult,
    LossPropensityBand,
    SeverityPropensityBand,
)


class PricingIntegrationMethod(Enum):
    """Supported pricing integration methods."""
    MULTIPLICATIVE = "multiplicative"
    ADDITIVE = "additive"
    GRID = "grid"
    THREE_DIMENSIONAL = "three_dimensional"


@dataclass
class PricingIntegrationConfig:
    """Configuration for pricing integration."""
    method: PricingIntegrationMethod
    frequency_impact_cap: float = 1.50
    frequency_impact_floor: float = 0.70
    severity_impact_cap: float = 1.40
    severity_impact_floor: float = 0.75
    frequency_weight: float = 0.60
    severity_weight: float = 0.40
    confidence_threshold: float = 0.6  # Min confidence to apply adjustment


@dataclass
class LossPricingResult:
    """Result of loss-based pricing adjustment."""
    base_premium: float
    loss_adjusted_premium: float
    loss_modifier: float
    frequency_modifier: float
    severity_modifier: float
    adjustment_applied: bool
    adjustment_reason: str
    confidence: float
    loss_propensity_band: str
    severity_propensity_band: str


class LossPricingIntegration:
    """
    Integrates loss propensity results into pricing calculations.

    Supports three pricing patterns:
    - Multiplicative: base_premium * combined_loss_modifier
    - Additive: base_premium + loss_loading
    - Grid: lookup in (risk_tier, loss_propensity_band) matrix
    """

    def __init__(self, config: PricingIntegrationConfig):
        """
        Initialize pricing integration.

        Args:
            config: Pricing integration configuration
        """
        self.config = config
        self._pricing_grid: Optional[Dict[str, Dict[str, float]]] = None

    def apply_loss_adjustment(
        self,
        base_premium: float,
        loss_result: LossPropensityResult,
        risk_tier: Optional[str] = None,
        exposure_band: Optional[str] = None
    ) -> LossPricingResult:
        """
        Apply loss propensity adjustment to base premium.

        Args:
            base_premium: Base premium before loss adjustment
            loss_result: Loss propensity calculation result
            risk_tier: Risk tier for grid-based pricing
            exposure_band: Exposure band for 3D grid pricing

        Returns:
            LossPricingResult with adjusted premium and details
        """
        # Check confidence threshold
        if loss_result.loss_confidence < self.config.confidence_threshold:
            return LossPricingResult(
                base_premium=base_premium,
                loss_adjusted_premium=base_premium,
                loss_modifier=1.0,
                frequency_modifier=1.0,
                severity_modifier=1.0,
                adjustment_applied=False,
                adjustment_reason=f"Confidence {loss_result.loss_confidence:.2f} below threshold {self.config.confidence_threshold}",
                confidence=loss_result.loss_confidence,
                loss_propensity_band=loss_result.loss_propensity_band.value,
                severity_propensity_band=loss_result.severity_propensity_band.value
            )

        # Apply appropriate method
        if self.config.method == PricingIntegrationMethod.MULTIPLICATIVE:
            return self._apply_multiplicative(base_premium, loss_result)
        elif self.config.method == PricingIntegrationMethod.ADDITIVE:
            return self._apply_additive(base_premium, loss_result)
        elif self.config.method == PricingIntegrationMethod.GRID:
            return self._apply_grid(base_premium, loss_result, risk_tier)
        elif self.config.method == PricingIntegrationMethod.THREE_DIMENSIONAL:
            return self._apply_3d_grid(base_premium, loss_result, risk_tier, exposure_band)
        else:
            # Default to multiplicative
            return self._apply_multiplicative(base_premium, loss_result)

    def _apply_multiplicative(
        self,
        base_premium: float,
        loss_result: LossPropensityResult
    ) -> LossPricingResult:
        """
        Apply multiplicative pricing adjustment.

        Pattern: loss_adjusted_premium = base_premium * combined_loss_modifier
        """
        # Get frequency and severity modifiers
        freq_modifier = self._apply_caps_floors(
            loss_result.frequency_multiplier,
            self.config.frequency_impact_cap,
            self.config.frequency_impact_floor
        )

        sev_modifier = self._apply_caps_floors(
            loss_result.severity_multiplier,
            self.config.severity_impact_cap,
            self.config.severity_impact_floor
        )

        # Calculate combined modifier
        combined = (
            freq_modifier * self.config.frequency_weight +
            sev_modifier * self.config.severity_weight
        )

        # Apply overall caps and floors
        overall_cap = max(self.config.frequency_impact_cap, self.config.severity_impact_cap)
        overall_floor = min(self.config.frequency_impact_floor, self.config.severity_impact_floor)
        combined = self._apply_caps_floors(combined, overall_cap, overall_floor)

        adjusted_premium = base_premium * combined

        return LossPricingResult(
            base_premium=base_premium,
            loss_adjusted_premium=adjusted_premium,
            loss_modifier=combined,
            frequency_modifier=freq_modifier,
            severity_modifier=sev_modifier,
            adjustment_applied=True,
            adjustment_reason=f"Multiplicative adjustment: {combined:.3f}x ({loss_result.loss_propensity_band.value} band)",
            confidence=loss_result.loss_confidence,
            loss_propensity_band=loss_result.loss_propensity_band.value,
            severity_propensity_band=loss_result.severity_propensity_band.value
        )

    def _apply_additive(
        self,
        base_premium: float,
        loss_result: LossPropensityResult
    ) -> LossPricingResult:
        """
        Apply additive pricing adjustment.

        Pattern: loss_adjusted_premium = base_premium + loss_loading
        """
        # Convert multipliers to loading percentages
        freq_loading = (loss_result.frequency_multiplier - 1.0) * self.config.frequency_weight
        sev_loading = (loss_result.severity_multiplier - 1.0) * self.config.severity_weight

        # Calculate combined loading
        combined_loading = freq_loading + sev_loading

        # Apply caps and floors (as percentages)
        max_loading = max(self.config.frequency_impact_cap, self.config.severity_impact_cap) - 1.0
        min_loading = min(self.config.frequency_impact_floor, self.config.severity_impact_floor) - 1.0

        combined_loading = max(min_loading, min(max_loading, combined_loading))

        # Calculate adjustment
        loss_adjustment = base_premium * combined_loading
        adjusted_premium = base_premium + loss_adjustment

        combined_modifier = 1.0 + combined_loading

        return LossPricingResult(
            base_premium=base_premium,
            loss_adjusted_premium=adjusted_premium,
            loss_modifier=combined_modifier,
            frequency_modifier=1.0 + freq_loading,
            severity_modifier=1.0 + sev_loading,
            adjustment_applied=True,
            adjustment_reason=f"Additive adjustment: {combined_loading:+.1%} ({loss_result.loss_propensity_band.value} band)",
            confidence=loss_result.loss_confidence,
            loss_propensity_band=loss_result.loss_propensity_band.value,
            severity_propensity_band=loss_result.severity_propensity_band.value
        )

    def _apply_grid(
        self,
        base_premium: float,
        loss_result: LossPropensityResult,
        risk_tier: Optional[str]
    ) -> LossPricingResult:
        """
        Apply grid-based pricing adjustment.

        Pattern: rate = pricing_grid[risk_tier][loss_propensity_band]
        """
        if self._pricing_grid is None or risk_tier is None:
            # Fall back to multiplicative if grid not available
            return self._apply_multiplicative(base_premium, loss_result)

        band = loss_result.loss_propensity_band.value

        # Look up rate in grid
        if risk_tier in self._pricing_grid:
            tier_rates = self._pricing_grid[risk_tier]
            if band in tier_rates:
                rate_modifier = tier_rates[band]

                adjusted_premium = base_premium * rate_modifier

                return LossPricingResult(
                    base_premium=base_premium,
                    loss_adjusted_premium=adjusted_premium,
                    loss_modifier=rate_modifier,
                    frequency_modifier=rate_modifier,  # Grid combines both
                    severity_modifier=1.0,
                    adjustment_applied=True,
                    adjustment_reason=f"Grid lookup: tier={risk_tier}, band={band}, modifier={rate_modifier:.3f}",
                    confidence=loss_result.loss_confidence,
                    loss_propensity_band=band,
                    severity_propensity_band=loss_result.severity_propensity_band.value
                )

        # Fall back to multiplicative if lookup fails
        return self._apply_multiplicative(base_premium, loss_result)

    def _apply_3d_grid(
        self,
        base_premium: float,
        loss_result: LossPropensityResult,
        risk_tier: Optional[str],
        exposure_band: Optional[str]
    ) -> LossPricingResult:
        """
        Apply three-dimensional grid pricing.

        Pattern: rate = pricing_grid[risk_tier][exposure_band][loss_propensity_band]
        """
        # For now, fall back to multiplicative
        # Full 3D grid would require extended grid structure
        return self._apply_multiplicative(base_premium, loss_result)

    def _apply_caps_floors(
        self,
        value: float,
        cap: float,
        floor: float
    ) -> float:
        """Apply cap and floor to a value."""
        return max(floor, min(cap, value))

    def set_pricing_grid(
        self,
        grid: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Set the pricing grid for grid-based pricing.

        Args:
            grid: Nested dictionary of risk_tier -> loss_band -> rate_modifier

        Example:
            {
                'tier_1': {'very_low': 0.85, 'low': 0.95, 'moderate': 1.0, ...},
                'tier_2': {'very_low': 0.90, 'low': 1.0, ...},
                ...
            }
        """
        self._pricing_grid = grid

    def get_adjustment_summary(
        self,
        loss_result: LossPropensityResult
    ) -> Dict[str, Any]:
        """
        Get a summary of the loss pricing adjustment without applying it.

        Args:
            loss_result: Loss propensity calculation result

        Returns:
            Dictionary with adjustment details
        """
        freq_modifier = self._apply_caps_floors(
            loss_result.frequency_multiplier,
            self.config.frequency_impact_cap,
            self.config.frequency_impact_floor
        )

        sev_modifier = self._apply_caps_floors(
            loss_result.severity_multiplier,
            self.config.severity_impact_cap,
            self.config.severity_impact_floor
        )

        combined = (
            freq_modifier * self.config.frequency_weight +
            sev_modifier * self.config.severity_weight
        )

        overall_cap = max(self.config.frequency_impact_cap, self.config.severity_impact_cap)
        overall_floor = min(self.config.frequency_impact_floor, self.config.severity_impact_floor)
        combined = self._apply_caps_floors(combined, overall_cap, overall_floor)

        return {
            'method': self.config.method.value,
            'loss_propensity_band': loss_result.loss_propensity_band.value,
            'severity_propensity_band': loss_result.severity_propensity_band.value,
            'loss_propensity_score': loss_result.loss_propensity_score,
            'severity_propensity_score': loss_result.severity_propensity_score,
            'confidence': loss_result.loss_confidence,
            'would_apply': loss_result.loss_confidence >= self.config.confidence_threshold,
            'frequency_modifier': freq_modifier,
            'severity_modifier': sev_modifier,
            'combined_modifier': combined,
            'impact_percentage': (combined - 1.0) * 100,
            'caps_applied': {
                'frequency_cap': self.config.frequency_impact_cap,
                'frequency_floor': self.config.frequency_impact_floor,
                'severity_cap': self.config.severity_impact_cap,
                'severity_floor': self.config.severity_impact_floor,
            }
        }


def create_default_pricing_grid() -> Dict[str, Dict[str, float]]:
    """
    Create a default pricing grid for grid-based pricing.

    Returns:
        Default pricing grid with standard tiers and bands
    """
    return {
        'tier_1': {
            'very_low': 0.85,
            'low': 0.92,
            'moderate': 1.00,
            'elevated': 1.15,
            'high': 1.35,
        },
        'tier_2': {
            'very_low': 0.88,
            'low': 0.95,
            'moderate': 1.00,
            'elevated': 1.12,
            'high': 1.30,
        },
        'tier_3': {
            'very_low': 0.90,
            'low': 0.97,
            'moderate': 1.00,
            'elevated': 1.10,
            'high': 1.25,
        },
        'tier_4': {
            'very_low': 0.92,
            'low': 0.98,
            'moderate': 1.00,
            'elevated': 1.08,
            'high': 1.20,
        },
        'tier_5': {
            'very_low': 0.95,
            'low': 0.99,
            'moderate': 1.00,
            'elevated': 1.05,
            'high': 1.15,
        },
    }


def calculate_combined_modifier(
    frequency_multiplier: float,
    severity_multiplier: float,
    frequency_weight: float = 0.60,
    severity_weight: float = 0.40,
    cap: float = 1.50,
    floor: float = 0.70
) -> float:
    """
    Calculate combined loss modifier from frequency and severity multipliers.

    Args:
        frequency_multiplier: Frequency-based multiplier
        severity_multiplier: Severity-based multiplier
        frequency_weight: Weight for frequency component
        severity_weight: Weight for severity component
        cap: Maximum allowed modifier
        floor: Minimum allowed modifier

    Returns:
        Combined loss modifier bounded by cap and floor
    """
    combined = (
        frequency_multiplier * frequency_weight +
        severity_multiplier * severity_weight
    )
    return max(floor, min(cap, combined))
