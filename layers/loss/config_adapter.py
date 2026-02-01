"""
Loss Layer - v2.0 Config Adapter

Bridges the existing loss correlation scorer with the v2.0
loss_tier_bands configuration from coverage YAML files.

The loss_tier_bands define frequency and severity modifiers
per score band, with floor/cap constraints.
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("dsi.loss.config_adapter")


class LossTierBandAdapter:
    """
    Adapts v2.0 loss_tier_bands config to produce frequency and
    severity modifiers for pricing integration.

    loss_tier_bands structure:
        bands:
          - id: 1
            label: "VERY_LOW"
            interpretation:
              bands: {min: 80, max: 100}
              application:
                frequency_modifier: 0.70
                severity_modifier: 0.80
        constraints:
          floor: 0.55
          cap: 1.60
    """

    def __init__(self, loss_tier_config: Any):
        """
        Initialize with a LossTierConfig from the parsed coverage config.

        Args:
            loss_tier_config: LossTierConfig instance (from types.py)
        """
        self.config = loss_tier_config

    def get_modifiers_for_score(
        self,
        loss_score: float,
    ) -> Tuple[float, float, float, str]:
        """
        Map a loss propensity score to frequency and severity modifiers.

        Args:
            loss_score: Loss propensity score (0-100)

        Returns:
            Tuple of (frequency_modifier, severity_modifier,
                       combined_modifier, band_label)
        """
        if self.config is None:
            return 1.0, 1.0, 1.0, "NO_CONFIG"

        band = self.config.get_band_for_score(loss_score)

        if band is None:
            logger.warning(f"No loss band found for score {loss_score}")
            return 1.0, 1.0, 1.0, "NO_BAND"

        freq_mod = band.frequency_modifier
        sev_mod = band.severity_modifier

        # Apply constraints
        freq_mod = self._apply_constraints(freq_mod)
        sev_mod = self._apply_constraints(sev_mod)

        # Combined modifier: geometric mean of frequency and severity
        combined = (freq_mod * sev_mod) ** 0.5

        logger.debug(
            f"Loss score {loss_score:.1f} → band={band.label}, "
            f"freq={freq_mod:.3f}, sev={sev_mod:.3f}, combined={combined:.3f}"
        )

        return freq_mod, sev_mod, combined, band.label

    def _apply_constraints(self, modifier: float) -> float:
        """Apply floor/cap constraints to a modifier value."""
        if self.config is None:
            return modifier

        floor = self.config.floor
        cap = self.config.cap

        return max(floor, min(cap, modifier))

    def get_all_bands(self) -> list:
        """Get all loss tier bands for reporting."""
        if self.config is None:
            return []
        return [
            {
                "id": b.id,
                "label": b.label,
                "min_score": b.min_score,
                "max_score": b.max_score,
                "frequency_modifier": b.frequency_modifier,
                "severity_modifier": b.severity_modifier,
            }
            for b in self.config.bands
        ]
