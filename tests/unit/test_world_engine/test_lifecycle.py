"""WE-3d: Lifecycle manager -- state machine criteria."""

import pytest

from world_engine.lifecycle import PROMOTION_CRITERIA


class TestPromotionCriteria:
    def test_all_three_transitions_defined(self):
        assert set(PROMOTION_CRITERIA.keys()) == {
            "candidate_to_provisional",
            "provisional_to_active",
            "active_to_deprecated",
        }

    def test_candidate_to_provisional_criteria(self):
        c = PROMOTION_CRITERIA["candidate_to_provisional"]
        assert c["holdout_rho_min"] == 0.2
        assert c["holdout_p_max"] == 0.05
        assert c["stability_windows_min"] == 3

    def test_provisional_to_active_has_effect_size_gate(self):
        c = PROMOTION_CRITERIA["provisional_to_active"]
        assert c["predictive_hit_rate_min"] == 0.6
        assert c["effect_size_min"] == 0.3
        assert c["min_age_months"] == 6

    def test_active_to_deprecated_thresholds(self):
        c = PROMOTION_CRITERIA["active_to_deprecated"]
        assert c["predictive_hit_rate_below"] == 0.4
        assert c["consecutive_windows_below"] == 3

    def test_deprecate_threshold_strictly_lower_than_promotion(self):
        """Hysteresis: you need to be significantly worse than the promotion
        bar to get demoted, so relationships don't oscillate."""
        promo = PROMOTION_CRITERIA["provisional_to_active"]["predictive_hit_rate_min"]
        deprec = PROMOTION_CRITERIA["active_to_deprecated"]["predictive_hit_rate_below"]
        assert deprec < promo
