"""
DSI Traditional Pricing Modifiers - Exposure Modifier

Exposure-based adjustments with two modes:

1. STREAMLINED (STP - Straight-Through Processing):
   - Only needs revenue OR tiv
   - Uses simplified size curve lookup
   - Returns quick factor for automatic processing
   - Lower confidence (0.7) due to limited data

2. FULL (when rich data available):
   - Analyzes multiple exposure metrics
   - Considers growth trends
   - Evaluates concentration factors
   - Higher confidence based on data completeness

When no exposure data is available, returns factor=1.0 (no impact).
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    TraditionalModifier,
    TraditionalModifierResult,
    ExposureInput,
)
from ..types import CoverageConfig
from signals.types import InferenceContext


logger = logging.getLogger("dsi.modifiers.exposure")


# =============================================================================
# SIZE CURVES - Exposure relativity by size band
# =============================================================================

# Size curve: maps exposure amount to relativity factor
# Format: (max_exposure, relativity)
# Smaller risks get higher relativity (more per-unit premium)
# Larger risks get lower relativity (volume discount)

SIZE_CURVE_ISO_2: List[Tuple[float, float]] = [
    # (Max TIV/Revenue, Relativity Factor)
    (1_000_000, 1.35),        # < 1M
    (5_000_000, 1.20),        # 1M - 5M
    (10_000_000, 1.10),       # 5M - 10M
    (25_000_000, 1.00),       # 10M - 25M (base)
    (50_000_000, 0.95),       # 25M - 50M
    (100_000_000, 0.90),      # 50M - 100M
    (250_000_000, 0.85),      # 100M - 250M
    (500_000_000, 0.80),      # 250M - 500M
    (1_000_000_000, 0.75),    # 500M - 1B
    (float("inf"), 0.70),     # > 1B
]

SIZE_CURVE_FLAT: List[Tuple[float, float]] = [
    (float("inf"), 1.00),  # No size adjustment
]

SIZE_CURVES: Dict[str, List[Tuple[float, float]]] = {
    "iso_curve_2": SIZE_CURVE_ISO_2,
    "flat": SIZE_CURVE_FLAT,
}


class ExposureModifier(TraditionalModifier):
    """
    Exposure-based adjustment modifier with streamlined STP mode.

    Calculates size-based relativity factors and growth adjustments.

    Configuration:
        size_curve: Name of size curve to use (default: "iso_curve_2")
        growth_threshold: Revenue growth triggering review (default: 0.20)
        growth_loading: Loading per 10% excess growth (default: 0.02)
        concentration_threshold: Location concentration trigger (default: 0.5)
        enabled: Whether this modifier is active
    """

    def __init__(
        self,
        size_curve: str = "iso_curve_2",
        growth_threshold: float = 0.20,
        growth_loading: float = 0.02,
        concentration_threshold: float = 0.50,
        enabled: bool = True,
    ):
        """
        Initialize ExposureModifier.

        Args:
            size_curve: Name of size relativity curve to use
            growth_threshold: Growth rate triggering additional loading
            growth_loading: Additional loading per 10% excess growth
            concentration_threshold: TIV concentration triggering review
            enabled: Whether this modifier is active
        """
        self.size_curve_name = size_curve
        self.size_curve = SIZE_CURVES.get(size_curve, SIZE_CURVE_ISO_2)
        self.growth_threshold = growth_threshold
        self.growth_loading = growth_loading
        self.concentration_threshold = concentration_threshold
        self._enabled = enabled

    @property
    def modifier_type(self) -> str:
        return "exposure"

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
        Calculate exposure-based modifier.

        Returns neutral result (factor=1.0) if:
        - Modifier is disabled
        - No exposure data available

        Uses streamlined mode if only TIV or revenue available.
        Uses full mode if multiple exposure metrics available.
        """
        if not self._enabled:
            return TraditionalModifierResult.neutral(self.modifier_type, "Modifier disabled")

        # Extract exposure from submission
        exposure = ExposureInput.from_submission(submission_data)

        if not exposure.has_minimal_data:
            logger.debug(f"No exposure data for {entity_id} - returning neutral")
            return TraditionalModifierResult.neutral(self.modifier_type, "No exposure data")

        # Determine mode
        mode = exposure.mode

        if mode == "streamlined":
            return self._calculate_streamlined(entity_id, exposure)
        else:
            return self._calculate_full(entity_id, exposure, coverage)

    def _calculate_streamlined(
        self,
        entity_id: str,
        exposure: ExposureInput,
    ) -> TraditionalModifierResult:
        """
        Streamlined (STP) exposure calculation.

        Uses only primary exposure (TIV or revenue) for quick size factor.
        Lower confidence due to limited data.
        """
        primary = exposure.primary_exposure

        # Get size factor from curve
        size_factor = self._get_size_factor(primary)

        logger.info(
            f"Streamlined exposure for {entity_id}: "
            f"exposure={primary:,.0f}, size_factor={size_factor:.3f}"
        )

        return TraditionalModifierResult(
            modifier_type=self.modifier_type,
            factor=size_factor,
            confidence=0.70,  # Lower confidence for streamlined
            components={
                "primary_exposure": primary,
                "size_factor": size_factor,
                "mode": 0.0,  # 0 = streamlined
            },
            notes=["Streamlined exposure analysis (STP mode)"],
            data_sources=["submission"],
        )

    def _calculate_full(
        self,
        entity_id: str,
        exposure: ExposureInput,
        coverage: str,
    ) -> TraditionalModifierResult:
        """
        Full exposure calculation with multiple metrics.

        Considers:
        - Size relativity
        - Growth trends
        - Concentration factors (if location data available)
        """
        primary = exposure.primary_exposure
        components: Dict[str, float] = {
            "mode": 1.0,  # 1 = full
        }
        notes: List[str] = []

        # 1. Base size factor
        size_factor = self._get_size_factor(primary)
        components["primary_exposure"] = primary
        components["size_factor"] = size_factor

        # 2. Growth adjustment
        growth_factor = 1.0
        growth = exposure.revenue_growth
        if growth is not None:
            components["revenue_growth"] = growth
            if growth > self.growth_threshold:
                # Loading for excess growth
                excess = growth - self.growth_threshold
                excess_tiers = excess / 0.10  # per 10% excess
                growth_factor = 1.0 + (excess_tiers * self.growth_loading)
                growth_factor = min(1.25, growth_factor)  # Cap at 25%
                notes.append(f"Growth loading: {growth:.1%} growth exceeds {self.growth_threshold:.0%} threshold")
            elif growth < -0.10:
                # Credit for shrinkage (might indicate run-off)
                notes.append(f"Declining exposure: {growth:.1%} year-over-year")
        components["growth_factor"] = growth_factor

        # 3. Concentration factor (for property exposures)
        concentration_factor = 1.0
        if exposure.locations_count is not None and exposure.tiv is not None:
            if exposure.locations_count == 1:
                # Single location - higher concentration risk
                concentration_factor = 1.10
                notes.append("Single location concentration")
            elif exposure.locations_count <= 3:
                concentration_factor = 1.05
        components["concentration_factor"] = concentration_factor

        # 4. Employee intensity (if available)
        employee_factor = 1.0
        if exposure.employee_count is not None and exposure.revenue is not None:
            revenue_per_employee = exposure.revenue / max(1, exposure.employee_count)
            # Very high revenue per employee might indicate automation/tech
            # Very low might indicate labor-intensive (different risk profile)
            components["revenue_per_employee"] = revenue_per_employee
        components["employee_factor"] = employee_factor

        # Combined factor
        combined = size_factor * growth_factor * concentration_factor * employee_factor

        # Confidence based on data completeness
        data_points = sum([
            exposure.tiv is not None,
            exposure.revenue is not None,
            exposure.employee_count is not None,
            exposure.locations_count is not None,
            exposure.prior_year_revenue is not None,
        ])
        confidence = min(0.95, 0.60 + (data_points * 0.07))  # 0.67 to 0.95

        notes.append(f"Full exposure analysis ({data_points} metrics)")

        logger.info(
            f"Full exposure for {entity_id}: combined={combined:.3f}, "
            f"size={size_factor:.2f}, growth={growth_factor:.2f}, "
            f"concentration={concentration_factor:.2f}"
        )

        return TraditionalModifierResult(
            modifier_type=self.modifier_type,
            factor=combined,
            confidence=confidence,
            components=components,
            notes=notes,
            data_sources=["submission"],
        )

    def _get_size_factor(self, exposure_amount: float) -> float:
        """
        Look up size relativity factor from curve.

        Args:
            exposure_amount: TIV or revenue

        Returns:
            Relativity factor (1.0 = base, <1.0 = credit, >1.0 = loading)
        """
        for max_exposure, relativity in self.size_curve:
            if exposure_amount <= max_exposure:
                return relativity
        # Fallback (should not reach here with inf in curve)
        return 1.0

    def validate_input(self, submission_data: Dict[str, Any]) -> bool:
        """Check if exposure data is available."""
        exposure = ExposureInput.from_submission(submission_data)
        return exposure.has_minimal_data
