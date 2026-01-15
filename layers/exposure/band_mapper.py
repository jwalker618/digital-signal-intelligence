"""
Exposure Band Mapper (Phase 17)

Maps exposure scores to bands with implied TIV ranges.
Supports fixed threshold and quantile-based mapping methods.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ExposureConfig,
    ExposureBand,
    ExposureBandConfig,
)


class BandMapper:
    """
    Map exposure scores to bands with implied TIV ranges.

    Supports two mapping methods:
    - fixed_threshold: Fixed score cutoffs (initial deployment)
    - quantile: Dynamically calibrated from historical data

    Usage:
        mapper = BandMapper(config)
        band = mapper.map_score(score)
        tiv_range = mapper.get_implied_tiv(band)
    """

    def __init__(self, config: ExposureConfig):
        """
        Initialize band mapper.

        Args:
            config: Exposure configuration from YAML
        """
        self.config = config
        self._bands = sorted(config.exposure_bands, key=lambda b: b.min_score)
        self._method = config.band_mapping_method

    def map_score(self, score: float) -> ExposureBand:
        """
        Map exposure score to band.

        Args:
            score: Exposure score (0-100)

        Returns:
            ExposureBand enum value
        """
        if self._method == "quantile":
            return self._map_quantile(score)
        else:
            return self._map_fixed_threshold(score)

    def _map_fixed_threshold(self, score: float) -> ExposureBand:
        """Map using fixed thresholds from config."""
        for band_config in self._bands:
            if band_config.min_score <= score < band_config.max_score:
                return ExposureBand(band_config.name)

        # Return last band if score exceeds all thresholds
        if self._bands and score >= self._bands[-1].max_score:
            return ExposureBand(self._bands[-1].name)

        # Return first band if score below all thresholds
        if self._bands:
            return ExposureBand(self._bands[0].name)

        return ExposureBand.MEDIUM

    def _map_quantile(self, score: float) -> ExposureBand:
        """
        Map using quantile-based thresholds.

        Requires calibration data to be set via set_quantile_thresholds().
        Falls back to fixed threshold if quantiles not available.
        """
        # For now, fall back to fixed threshold
        # Full implementation would use calibrated quantiles
        return self._map_fixed_threshold(score)

    def get_implied_tiv(
        self,
        band: ExposureBand
    ) -> Tuple[float, float]:
        """
        Get implied TIV range for a band.

        Args:
            band: Exposure band

        Returns:
            Tuple of (tiv_low, tiv_high)
        """
        for band_config in self._bands:
            if band_config.name == band.value:
                return (band_config.implied_tiv_low, band_config.implied_tiv_high)

        # Default TIV ranges
        default_ranges = {
            ExposureBand.MICRO: (0, 1_000_000),
            ExposureBand.SMALL: (1_000_000, 10_000_000),
            ExposureBand.MEDIUM: (10_000_000, 50_000_000),
            ExposureBand.LARGE: (50_000_000, 250_000_000),
            ExposureBand.VERY_LARGE: (250_000_000, 1_000_000_000),
        }
        return default_ranges.get(band, (0, 50_000_000))

    def get_implied_tiv_string(self, band: ExposureBand) -> str:
        """
        Get human-readable TIV range string.

        Args:
            band: Exposure band

        Returns:
            Formatted string like "$10M - $50M"
        """
        low, high = self.get_implied_tiv(band)

        def format_amount(amount: float) -> str:
            if amount >= 1_000_000_000:
                return f"${amount / 1_000_000_000:.1f}B"
            elif amount >= 1_000_000:
                return f"${amount / 1_000_000:.0f}M"
            elif amount >= 1_000:
                return f"${amount / 1_000:.0f}K"
            else:
                return f"${amount:.0f}"

        return f"{format_amount(low)} - {format_amount(high)}"

    def get_band_config(self, band: ExposureBand) -> Optional[ExposureBandConfig]:
        """
        Get full configuration for a band.

        Args:
            band: Exposure band

        Returns:
            ExposureBandConfig or None
        """
        for band_config in self._bands:
            if band_config.name == band.value:
                return band_config
        return None

    def get_exposure_modifier(self, band: ExposureBand) -> float:
        """
        Get pricing modifier for exposure band.

        Args:
            band: Exposure band

        Returns:
            Pricing modifier (1.0 = no change)
        """
        config = self.get_band_config(band)
        if config:
            return config.exposure_modifier

        # Default modifiers
        default_modifiers = {
            ExposureBand.MICRO: 0.50,
            ExposureBand.SMALL: 0.75,
            ExposureBand.MEDIUM: 1.00,
            ExposureBand.LARGE: 1.50,
            ExposureBand.VERY_LARGE: 2.50,
        }
        return default_modifiers.get(band, 1.0)

    def get_all_bands(self) -> List[ExposureBandConfig]:
        """Get all configured bands in order."""
        return self._bands.copy()

    def set_quantile_thresholds(
        self,
        quantiles: Dict[str, float]
    ) -> None:
        """
        Set quantile thresholds for quantile-based mapping.

        Args:
            quantiles: Dict mapping band name to score threshold
                       e.g., {"micro": 15, "small": 35, "medium": 60, ...}
        """
        # Update band configs with new thresholds
        for band_config in self._bands:
            if band_config.name in quantiles:
                # Update max_score to the quantile threshold
                # Next band's min_score becomes this band's max_score
                pass

        # Full implementation would recalculate all band boundaries
        # based on the quantile calibration data
