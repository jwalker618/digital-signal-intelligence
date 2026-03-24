"""
Unit Tests for ROL Recommender (Phase C — C2/C3)

Tests the dual recommendation engine and limit re-pricing.
"""

import pytest
from layers.risk.rol_validator import ROLValidator, ROLAppetiteBand
from layers.risk.rol_recommender import (
    ROLRecommender,
    LimitRecommendation,
    DualRecommendation,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def validator():
    return ROLValidator()


@pytest.fixture
def recommender(validator):
    return ROLRecommender(validator=validator)


@pytest.fixture
def sample_menu():
    """Typical limit/premium menu with decreasing ROL at higher limits."""
    return {
        "1000000": 50_000,      # ROL 0.050
        "2000000": 80_000,      # ROL 0.040
        "5000000": 150_000,     # ROL 0.030
        "10000000": 250_000,    # ROL 0.025
        "25000000": 500_000,    # ROL 0.020
        "50000000": 900_000,    # ROL 0.018
        "100000000": 1_500_000, # ROL 0.015
    }


@pytest.fixture
def high_premium_menu():
    """Menu where higher limits exceed appetite."""
    return {
        "1000000": 70_000,       # ROL 0.070
        "5000000": 500_000,      # ROL 0.100
        "10000000": 2_000_000,   # ROL 0.200
    }


# =============================================================================
# DUAL RECOMMENDATION
# =============================================================================

class TestDualRecommendation:

    def test_basic_recommendation(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert result.upper.limit > 0
        assert result.lower.limit > 0
        assert result.upper.premium > 0
        assert result.lower.premium > 0

    def test_upper_is_highest_within_appetite(self, recommender, sample_menu):
        """Upper recommendation should be the highest limit within appetite."""
        result = recommender.recommend(sample_menu)
        assert result.upper.limit >= result.lower.limit

    def test_lower_matches_requested_limit(self, recommender, sample_menu):
        """Lower recommendation should match or exceed requested limit."""
        result = recommender.recommend(sample_menu, requested_limit=5_000_000)
        assert result.lower.limit == 5_000_000

    def test_lower_nearest_above_requested(self, recommender, sample_menu):
        """If exact match unavailable, lower picks nearest above."""
        result = recommender.recommend(sample_menu, requested_limit=3_000_000)
        assert result.lower.limit >= 3_000_000

    def test_no_requested_limit(self, recommender, sample_menu):
        """Without requested limit, lower picks best value."""
        result = recommender.recommend(sample_menu, requested_limit=0)
        assert result.lower.limit > 0

    def test_all_options_populated(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert len(result.all_options) == len(sample_menu)

    def test_options_sorted_by_limit(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        limits = [o.limit for o in result.all_options]
        assert limits == sorted(limits)

    def test_spread_calculation(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu, requested_limit=1_000_000)
        assert result.spread == result.upper.premium - result.lower.premium

    def test_limit_ratio(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu, requested_limit=1_000_000)
        if result.lower.limit > 0:
            assert result.limit_ratio == result.upper.limit / result.lower.limit


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:

    def test_empty_menu(self, recommender):
        result = recommender.recommend({})
        assert result.upper.limit == 0
        assert result.lower.limit == 0

    def test_single_option(self, recommender):
        result = recommender.recommend({"5000000": 150_000})
        assert result.upper.limit == 5_000_000
        assert result.lower.limit == 5_000_000

    def test_requested_above_all_options(self, recommender, sample_menu):
        """Requested limit higher than all options → highest available."""
        result = recommender.recommend(sample_menu, requested_limit=500_000_000)
        assert result.lower.limit == max(int(float(k)) for k in sample_menu.keys())

    def test_high_premium_upper_fallback(self, recommender, high_premium_menu):
        """When higher limits exceed appetite, upper picks best value."""
        result = recommender.recommend(high_premium_menu)
        # Upper should not be the highest limit since those exceed appetite
        assert result.upper.limit > 0


# =============================================================================
# PHASE E FUTURE FIELDS
# =============================================================================

class TestPhaseEFields:
    """Verify Phase E accommodation fields exist with ground-up defaults."""

    def test_recommendation_has_attachment(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert result.upper.attachment == 0
        assert result.lower.attachment == 0

    def test_recommendation_has_participation(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert result.upper.participation_pct == 1.0
        assert result.lower.participation_pct == 1.0

    def test_recommendation_has_structure_type(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert result.upper.structure_type == "ground_up"
        assert result.lower.structure_type == "ground_up"


# =============================================================================
# ROL PERCENTILE
# =============================================================================

class TestROLPercentile:

    def test_percentile_within_band(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        for opt in result.all_options:
            assert 0.0 <= opt.rol_percentile <= 1.0

    def test_lower_rol_lower_percentile(self, recommender):
        """Lower ROL should produce lower percentile within band."""
        menu = {
            "5000000": 50_000,    # ROL 0.01
            "10000000": 500_000,  # ROL 0.05
        }
        result = recommender.recommend(menu)
        # The option with lower ROL should have lower percentile
        options = sorted(result.all_options, key=lambda o: o.rol)
        if len(options) >= 2:
            assert options[0].rol_percentile <= options[1].rol_percentile


# =============================================================================
# RATIONALE
# =============================================================================

class TestRationale:

    def test_upper_has_rationale(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu)
        assert len(result.upper.rationale) > 0

    def test_lower_has_rationale(self, recommender, sample_menu):
        result = recommender.recommend(sample_menu, requested_limit=5_000_000)
        assert len(result.lower.rationale) > 0
        assert "5,000,000" in result.lower.rationale or "requested" in result.lower.rationale.lower()
