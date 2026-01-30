"""
Exposure Layer - Scorer (v2.0)

Evaluates exposure tier bands from coverage configuration.
Maps exposure values (e.g., TIV, revenue, asset size) to bands
that produce pricing modifiers.

The exposure assessment works in parallel with risk and loss scoring.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ExposureAssessmentResult,
    ExposureBandResult,
    ExposureSignalOutput,
)

logger = logging.getLogger("dsi.exposure.scorer")


class ExposureScorer:
    """
    Evaluates exposure using v2.0 exposure_tier_bands configuration.

    Exposure assessment determines the magnitude and complexity
    of the risk being underwritten, producing a modifier that
    adjusts the base premium.
    """

    def __init__(self, default_modifier: float = 1.0):
        self.default_modifier = default_modifier

    def assess_exposure(
        self,
        exposure_value: float,
        exposure_tier_config: Any,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> ExposureAssessmentResult:
        """
        Assess exposure and determine the appropriate band and modifier.

        Args:
            exposure_value: Primary exposure metric (TIV, revenue, assets)
            exposure_tier_config: ExposureTierConfig from parsed config
            submission_data: Optional additional submission data

        Returns:
            ExposureAssessmentResult with band and modifier
        """
        if exposure_tier_config is None:
            logger.debug("No exposure_tier_config provided, using default modifier")
            return ExposureAssessmentResult(
                exposure_value=exposure_value,
                exposure_modifier=self.default_modifier,
                assessment_method="no_config",
            )

        # Find matching band
        band = exposure_tier_config.get_band_for_value(exposure_value)

        if band is None:
            logger.warning(
                f"No exposure band found for value {exposure_value}, "
                f"using default modifier"
            )
            return ExposureAssessmentResult(
                exposure_value=exposure_value,
                exposure_modifier=self.default_modifier,
                assessment_method="no_band_match",
                flags=[f"Exposure value {exposure_value} outside all bands"],
            )

        # Build band result
        band_result = ExposureBandResult(
            band_id=band.id,
            label=band.label,
            method=band.method,
            applied=band.applied,
            raw_value=exposure_value,
        )

        # Calculate modifier based on method
        if band.method == "MODIFIER":
            modifier = band.applied
        elif band.method == "MULTIPLIER":
            # MULTIPLIER: the applied value is a rate to multiply
            modifier = band.applied
        else:
            modifier = self.default_modifier

        # Calculate composite scores for reporting
        magnitude_score = self._calculate_magnitude_score(
            exposure_value, exposure_tier_config
        )

        result = ExposureAssessmentResult(
            exposure_value=exposure_value,
            exposure_band=band_result,
            magnitude_score=magnitude_score,
            composite_exposure_score=magnitude_score,
            exposure_modifier=modifier,
            confidence=1.0,
            signal_coverage=1.0,
            assessment_method="config_band_lookup",
        )

        logger.info(
            f"Exposure assessed: value={exposure_value}, "
            f"band={band.label}, modifier={modifier:.4f}"
        )

        return result

    def _calculate_magnitude_score(
        self,
        exposure_value: float,
        exposure_tier_config: Any,
    ) -> float:
        """
        Calculate a normalized magnitude score (0-100) based on
        where the exposure value falls within the band spectrum.
        """
        if not exposure_tier_config or not exposure_tier_config.bands:
            return 50.0

        bands = sorted(exposure_tier_config.bands, key=lambda b: b.min_value)
        if not bands:
            return 50.0

        # Find position within band spectrum
        min_val = bands[0].min_value
        max_val = bands[-1].max_value or bands[-1].min_value * 10

        if max_val <= min_val:
            return 50.0

        # Normalize to 0-100
        if exposure_value <= min_val:
            return 0.0
        elif exposure_value >= max_val:
            return 100.0
        else:
            return ((exposure_value - min_val) / (max_val - min_val)) * 100.0

    def assess_with_signals(
        self,
        signal_outputs: List[ExposureSignalOutput],
        exposure_tier_config: Any,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> ExposureAssessmentResult:
        """
        Assess exposure using signal outputs when explicit value
        is not available.

        Uses signal-inferred exposure estimation (future: Phase 17
        shadow layer integration).

        Args:
            signal_outputs: Extracted exposure signals
            exposure_tier_config: ExposureTierConfig from parsed config
            submission_data: Optional additional submission data

        Returns:
            ExposureAssessmentResult
        """
        if not signal_outputs:
            # No signals - use submission data if available
            if submission_data:
                # Try standard exposure fields
                for field_name in ["tiv", "revenue", "total_assets", "limit"]:
                    value = submission_data.get(field_name, 0)
                    if value > 0:
                        return self.assess_exposure(
                            value, exposure_tier_config, submission_data
                        )

            return ExposureAssessmentResult(
                exposure_value=0,
                exposure_modifier=self.default_modifier,
                signal_outputs=[],
                confidence=0.0,
                signal_coverage=0.0,
                assessment_method="no_signals",
                flags=["No exposure signals available"],
            )

        # Calculate composite from signals
        total_weight = len(signal_outputs)
        weighted_score = sum(s.normalized_score for s in signal_outputs)
        composite = weighted_score / total_weight if total_weight > 0 else 50.0

        confidence = sum(s.confidence for s in signal_outputs) / total_weight
        coverage = sum(1 for s in signal_outputs if s.error is None) / total_weight

        # Map composite score to exposure value estimate
        # This is a simplified mapping - Phase 17 will have full shadow layer
        estimated_value = self._score_to_exposure_estimate(composite)

        result = self.assess_exposure(
            estimated_value, exposure_tier_config, submission_data
        )
        result.signal_outputs = signal_outputs
        result.composite_exposure_score = composite
        result.confidence = confidence
        result.signal_coverage = coverage
        result.assessment_method = "signal_composite"

        return result

    def _score_to_exposure_estimate(self, composite_score: float) -> float:
        """
        Convert a composite exposure score to an estimated exposure value.

        Simple logarithmic mapping - Phase 17 shadow layer will provide
        more sophisticated estimation.
        """
        # Map 0-100 score to approximate exposure range
        # 0 = ~$1M, 50 = ~$50M, 100 = ~$1B
        import math
        base = 1_000_000  # $1M floor
        multiplier = math.exp(composite_score / 100.0 * math.log(1000))
        return base * multiplier
