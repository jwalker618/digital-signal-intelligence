"""
DSI Traditional Pricing Modifiers - Loss History Modifier

Experience rating based on historical loss data. When no loss history
is available, returns factor=1.0 (no impact on premium).

Methods supported:
- Pure loss ratio method
- Frequency/severity method
- Credibility-weighted method (default)
"""

import logging
from typing import Any, Dict, List, Optional

from .base import (
    TraditionalModifier,
    TraditionalModifierResult,
    LossHistoryInput,
    PolicyYear,
)
from ..types import CoverageConfig
from ...signals.types import InferenceContext


logger = logging.getLogger("dsi.modifiers.loss_history")


# Expected loss ratios by coverage (defaults)
DEFAULT_EXPECTED_LOSS_RATIOS: Dict[str, float] = {
    "aerospace": 0.55,
    "marine": 0.60,
    "cyber": 0.45,
    "financial_institutions": 0.50,
    "professional_indemnity": 0.55,
    "directors_officers": 0.40,
    "default": 0.55,
}


class LossHistoryModifier(TraditionalModifier):
    """
    Experience rating modifier based on loss history.

    Calculates an Experience Modification Factor (EMF) using
    credibility-weighted loss ratio method.

    When no loss history is provided, returns factor=1.0 (no impact).

    Configuration:
        full_credibility_premium: Premium threshold for full credibility (default: 500,000)
        years_required: Minimum years of history required (default: 3)
        large_loss_threshold: Threshold for large loss treatment (default: 100,000)
        cap_factor: Maximum loading factor (default: 1.50)
        floor_factor: Maximum credit factor (default: 0.75)
        expected_loss_ratio: Override expected loss ratio for coverage
    """

    def __init__(
        self,
        full_credibility_premium: float = 500_000.0,
        years_required: int = 3,
        large_loss_threshold: float = 100_000.0,
        cap_factor: float = 1.50,
        floor_factor: float = 0.75,
        expected_loss_ratios: Optional[Dict[str, float]] = None,
        enabled: bool = True,
    ):
        """
        Initialize LossHistoryModifier.

        Args:
            full_credibility_premium: Premium needed for 100% credibility
            years_required: Minimum years of history (fewer = lower credibility)
            large_loss_threshold: Amount above which claims are capped
            cap_factor: Maximum loading (e.g., 1.50 = +50%)
            floor_factor: Maximum credit (e.g., 0.75 = -25%)
            expected_loss_ratios: Coverage-specific expected loss ratios
            enabled: Whether this modifier is active
        """
        self.full_credibility_premium = full_credibility_premium
        self.years_required = years_required
        self.large_loss_threshold = large_loss_threshold
        self.cap_factor = cap_factor
        self.floor_factor = floor_factor
        self.expected_loss_ratios = expected_loss_ratios or DEFAULT_EXPECTED_LOSS_RATIOS
        self._enabled = enabled

    @property
    def modifier_type(self) -> str:
        return "loss_history"

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def calculate(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext,
        config: Optional[CoverageConfig] = None,
    ) -> TraditionalModifierResult:
        """
        Calculate experience modification factor.

        Returns neutral result (factor=1.0) if:
        - Modifier is disabled
        - No loss history data available
        - Insufficient years of history
        """
        if not self._enabled:
            return TraditionalModifierResult.neutral(self.modifier_type, "Modifier disabled")

        # Extract loss history from submission
        loss_input = LossHistoryInput.from_submission(submission_data)

        if not loss_input.has_data:
            logger.debug(f"No loss history for {entity_id} - returning neutral")
            return TraditionalModifierResult.neutral(self.modifier_type, "No loss history data")

        # Check for sufficient history
        years_count = len(loss_input.policy_years)
        if years_count < self.years_required:
            logger.debug(f"Insufficient history ({years_count}/{self.years_required} years) for {entity_id}")
            # Apply with reduced credibility rather than skipping
            credibility_reduction = years_count / self.years_required
        else:
            credibility_reduction = 1.0

        # Calculate base credibility from premium volume
        premium_credibility = min(1.0, loss_input.total_premium / self.full_credibility_premium)

        # Combined credibility
        credibility = premium_credibility * credibility_reduction

        # Calculate loss ratio (capping large losses)
        adjusted_loss_ratio = self._calculate_adjusted_loss_ratio(loss_input)

        # Get expected loss ratio for coverage
        expected_lr = self.expected_loss_ratios.get(
            coverage, self.expected_loss_ratios.get("default", 0.55)
        )

        # Calculate Experience Modification Factor (EMF)
        # EMF = (Z * Actual LR + (1-Z) * Expected LR) / Expected LR
        # where Z = credibility factor
        if expected_lr <= 0:
            expected_lr = 0.55  # Safety fallback

        weighted_lr = (credibility * adjusted_loss_ratio) + ((1 - credibility) * expected_lr)
        raw_emf = weighted_lr / expected_lr

        # Apply cap and floor
        emf = max(self.floor_factor, min(self.cap_factor, raw_emf))

        # Determine notes
        notes = []
        if years_count < self.years_required:
            notes.append(f"Limited history: {years_count}/{self.years_required} years")
        if len(loss_input.claims) > 0:
            large_losses = sum(1 for c in loss_input.claims if c.is_large_loss)
            if large_losses > 0:
                notes.append(f"{large_losses} large loss(es) capped at {self.large_loss_threshold:,.0f}")
        if raw_emf != emf:
            notes.append(f"EMF capped from {raw_emf:.3f} to {emf:.3f}")

        notes.append(f"Experience mod based on {years_count} year(s) of history")

        logger.info(
            f"Loss history modifier for {entity_id}: EMF={emf:.3f}, "
            f"LR={adjusted_loss_ratio:.2%}, credibility={credibility:.2%}"
        )

        return TraditionalModifierResult(
            modifier_type=self.modifier_type,
            factor=emf,
            confidence=credibility,
            components={
                "actual_loss_ratio": loss_input.overall_loss_ratio,
                "adjusted_loss_ratio": adjusted_loss_ratio,
                "expected_loss_ratio": expected_lr,
                "credibility": credibility,
                "premium_credibility": premium_credibility,
                "years_count": float(years_count),
                "raw_emf": raw_emf,
                "total_premium": loss_input.total_premium,
                "total_losses": loss_input.total_incurred_losses,
            },
            notes=notes,
            data_sources=["submission", "loss_history"],
        )

    def _calculate_adjusted_loss_ratio(self, loss_input: LossHistoryInput) -> float:
        """
        Calculate loss ratio with large loss capping.

        Large losses are capped at threshold to prevent single events
        from distorting the experience rating.
        """
        if not loss_input.policy_years:
            return 0.0

        total_premium = loss_input.total_premium
        if total_premium <= 0:
            return 0.0

        # Start with incurred losses
        total_losses = loss_input.total_incurred_losses

        # If we have claim detail, apply large loss capping
        if loss_input.claims:
            # Remove actual large losses and add capped amounts
            for claim in loss_input.claims:
                if claim.is_large_loss or claim.incurred_amount > self.large_loss_threshold:
                    # Subtract excess over threshold
                    excess = claim.incurred_amount - self.large_loss_threshold
                    total_losses -= max(0, excess)

        return total_losses / total_premium

    def validate_input(self, submission_data: Dict[str, Any]) -> bool:
        """Check if loss history data is available."""
        loss_input = LossHistoryInput.from_submission(submission_data)
        return loss_input.has_data
