"""
Unit tests for ModelPricer.

Tests premium calculation (Steps 8-12 of the workflow).
"""

import pytest

from layers.risk.pricer import ModelPricer
from layers.risk.types import (
    CoverageConfig,
    TierConfig,
    LimitBand,
    PricingResult,
    ModifierApplication,
    DecisionType,
    PremiumMethod,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def pricer():
    """Create a ModelPricer instance."""
    return ModelPricer()


@pytest.fixture
def sample_config():
    """Create a sample config for pricing tests."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="test-hash",
        required_inputs=["entity_id", "tiv"],
        signal_groups=[],
        direct_queries=[],
        categorical_groups=["operator_type", "fleet_category"],
        categorical_features={
            "operator_type": {
                "major_airline": 0.85,
                "regional_airline": 1.00,
                "charter_operator": 1.25,
                "flight_school": 1.50
            },
            "fleet_category": {
                "widebody": 1.15,
                "narrowbody": 1.00,
                "turboprop": 0.95,
                "helicopter": 1.40
            }
        },
        tier_thresholds=[
            TierConfig(
                tier=1, min_score=800, max_score=1000,
                base_premium=25000, decision=DecisionType.APPROVE
            ),
            TierConfig(
                tier=2, min_score=600, max_score=799,
                base_premium=35000, decision=DecisionType.APPROVE
            ),
            TierConfig(
                tier=3, min_score=400, max_score=599,
                base_premium=50000, decision=DecisionType.REFER
            ),
            TierConfig(
                tier=4, min_score=200, max_score=399,
                base_premium=75000, decision=DecisionType.REFER
            ),
            TierConfig(
                tier=5, min_score=0, max_score=199,
                base_premium=100000, decision=DecisionType.DECLINE
            ),
        ],
        limit_bands=[
            LimitBand(limit=1000000, ilf=1.0),
            LimitBand(limit=5000000, ilf=2.5),
            LimitBand(limit=10000000, ilf=4.0),
            LimitBand(limit=25000000, ilf=7.0),
        ],
        deductible_credits={
            10000: 1.0,
            25000: 0.95,
            50000: 0.90,
            100000: 0.85,
        },
        metadata={"min_premium": 15000}
    )


@pytest.fixture
def rate_based_config():
    """Create a config with rate-based pricing."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_rate",
        version="1.0.0",
        config_hash="test-hash-rate",
        required_inputs=["entity_id", "tiv"],
        signal_groups=[],
        direct_queries=[],
        categorical_groups=[],
        categorical_features={},
        tier_thresholds=[
            TierConfig(
                tier=1, min_score=800, max_score=1000,
                rate=0.005, rate_basis="tiv",
                decision=DecisionType.APPROVE
            ),
            TierConfig(
                tier=2, min_score=600, max_score=799,
                rate=0.0075, rate_basis="tiv",
                decision=DecisionType.APPROVE
            ),
            TierConfig(
                tier=3, min_score=400, max_score=599,
                rate=0.01, rate_basis="tiv",
                decision=DecisionType.REFER
            ),
        ],
        limit_bands=[
            LimitBand(limit=1000000, ilf=1.0),
            LimitBand(limit=5000000, ilf=2.5),
        ],
        deductible_credits={},
        metadata={"min_premium": 10000}
    )


# =============================================================================
# TIER OVERRIDE TESTS (Step 8)
# =============================================================================

class TestTierOverrides:
    """Tests for Step 8: Tier override resolution."""

    def test_no_overrides_returns_score_tier(self, pricer):
        """With no overrides, should return score-based tier."""
        final = pricer.resolve_tier_overrides(score_tier=2, overrides=[])
        assert final == 2

    def test_single_override_applies(self, pricer):
        """Single override should apply when worse than score tier."""
        final = pricer.resolve_tier_overrides(score_tier=2, overrides=[4])
        assert final == 4

    def test_multiple_overrides_max_wins(self, pricer):
        """Maximum override should win when multiple present."""
        final = pricer.resolve_tier_overrides(score_tier=2, overrides=[3, 5, 4])
        assert final == 5

    def test_override_below_score_tier_ignored(self, pricer):
        """Override better than score tier should be ignored."""
        final = pricer.resolve_tier_overrides(score_tier=4, overrides=[2])
        assert final == 4

    def test_mixed_overrides_max_applied(self, pricer):
        """Should apply max of overrides vs score tier."""
        final = pricer.resolve_tier_overrides(score_tier=3, overrides=[2, 4, 1])
        assert final == 4


# =============================================================================
# SCORE TO TIER TESTS
# =============================================================================

class TestScoreToTier:
    """Tests for score to tier mapping."""

    def test_high_score_tier_1(self, pricer, sample_config):
        """High score should map to tier 1."""
        tier = pricer._score_to_tier(850, sample_config)
        assert tier == 1

    def test_mid_score_tier_3(self, pricer, sample_config):
        """Mid score should map to tier 3."""
        tier = pricer._score_to_tier(500, sample_config)
        assert tier == 3

    def test_low_score_tier_5(self, pricer, sample_config):
        """Low score should map to tier 5."""
        tier = pricer._score_to_tier(100, sample_config)
        assert tier == 5

    def test_boundary_score(self, pricer, sample_config):
        """Boundary scores should map correctly."""
        assert pricer._score_to_tier(800, sample_config) == 1
        assert pricer._score_to_tier(799, sample_config) == 2
        assert pricer._score_to_tier(600, sample_config) == 2
        assert pricer._score_to_tier(599, sample_config) == 3


# =============================================================================
# BASE PREMIUM TESTS (Step 10)
# =============================================================================

class TestBasePremium:
    """Tests for Step 10: Base premium generation."""

    def test_pure_premium_method(self, pricer, sample_config):
        """Should use pure premium from tier config."""
        premium, method, rate_value = pricer.calculate_base_premium(
            tier=1,
            submission_data={},
            config=sample_config
        )

        assert premium == 25000
        assert method == PremiumMethod.PURE
        assert rate_value is None

    def test_rate_based_method(self, pricer, rate_based_config):
        """Should calculate premium from rate * TIV."""
        submission_data = {"tiv": 10000000}

        premium, method, rate_value = pricer.calculate_base_premium(
            tier=1,
            submission_data=submission_data,
            config=rate_based_config
        )

        # 10M * 0.5% = 50,000
        assert premium == 50000
        assert method == PremiumMethod.RATE_BASED
        assert rate_value == 10000000

    def test_rate_based_respects_minimum(self, pricer, rate_based_config):
        """Rate-based should respect minimum premium."""
        submission_data = {"tiv": 100000}  # Small TIV

        premium, method, _ = pricer.calculate_base_premium(
            tier=1,
            submission_data=submission_data,
            config=rate_based_config
        )

        # 100,000 * 0.5% = 500, but min is 10,000
        assert premium == 10000

    def test_missing_rate_basis_uses_minimum(self, pricer, rate_based_config):
        """Missing rate basis should use minimum premium."""
        submission_data = {}  # No TIV provided

        premium, method, rate_value = pricer.calculate_base_premium(
            tier=1,
            submission_data=submission_data,
            config=rate_based_config
        )

        assert premium == 10000
        assert rate_value is None

    def test_invalid_tier_uses_minimum(self, pricer, sample_config):
        """Invalid tier should use minimum premium."""
        premium, method, _ = pricer.calculate_base_premium(
            tier=99,
            submission_data={},
            config=sample_config
        )

        assert premium == 15000  # min_premium from metadata


# =============================================================================
# MODIFIER TESTS (Step 11)
# =============================================================================

class TestModifiers:
    """Tests for Step 11: Modifier application."""

    def test_categorical_modifier_applied(self, pricer, sample_config):
        """Should apply categorical modifier."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={"operator_type": "major_airline"},
            query_modifiers=[],
            config=sample_config
        )

        # 50,000 * 0.85 = 42,500
        assert premium == 42500
        assert len(modifiers) == 1
        assert modifiers[0].name == "operator_type:major_airline"
        assert modifiers[0].factor == 0.85

    def test_multiple_categorical_modifiers(self, pricer, sample_config):
        """Should apply multiple categorical modifiers."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={
                "operator_type": "charter_operator",
                "fleet_category": "helicopter"
            },
            query_modifiers=[],
            config=sample_config
        )

        # 50,000 * 1.25 * 1.40 = 87,500
        expected = 50000 * 1.25 * 1.40
        assert abs(premium - expected) < 0.01
        assert len(modifiers) == 2

    def test_query_modifier_applied(self, pricer, sample_config):
        """Should apply query modifiers."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={},
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            config=sample_config
        )

        # 50,000 * 1.15 = 57,500
        assert premium == 57500
        assert len(modifiers) == 1
        assert modifiers[0].source == "direct_query"

    def test_combined_modifiers(self, pricer, sample_config):
        """Should apply categorical then query modifiers."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={"operator_type": "major_airline"},
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            config=sample_config
        )

        # 50,000 * 0.85 * 1.15 = 48,875
        expected = 50000 * 0.85 * 1.15
        assert abs(premium - expected) < 0.01
        assert len(modifiers) == 2

    def test_modifier_1_0_skipped(self, pricer, sample_config):
        """Modifiers with factor 1.0 should be skipped."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={},
            query_modifiers=[{"name": "no_impact", "factor": 1.0}],
            config=sample_config
        )

        assert premium == 50000
        assert len(modifiers) == 0

    def test_unknown_categorical_group_ignored(self, pricer, sample_config):
        """Unknown categorical group should be ignored."""
        premium, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={"unknown_group": "some_category"},
            query_modifiers=[],
            config=sample_config
        )

        assert premium == 50000
        assert len(modifiers) == 0

    def test_modifier_tracks_before_after(self, pricer, sample_config):
        """Modifier should track premium before and after."""
        _, modifiers = pricer.apply_modifiers(
            base_premium=50000,
            categorical_selections={"operator_type": "major_airline"},
            query_modifiers=[],
            config=sample_config
        )

        mod = modifiers[0]
        assert mod.premium_before == 50000
        assert mod.premium_after == 42500


# =============================================================================
# LIMIT BAND TESTS (Step 12)
# =============================================================================

class TestLimitBands:
    """Tests for Step 12: Limit band scaling."""

    def test_scale_to_limits(self, pricer, sample_config):
        """Should scale premium across all limit bands."""
        limit_premiums = pricer.scale_to_limits(
            premium=50000,
            config=sample_config
        )

        assert len(limit_premiums) == 4
        assert limit_premiums[1000000] == 50000  # ILF 1.0
        assert limit_premiums[5000000] == 125000  # ILF 2.5
        assert limit_premiums[10000000] == 200000  # ILF 4.0
        assert limit_premiums[25000000] == 350000  # ILF 7.0

    def test_scale_rounds_to_cents(self, pricer, sample_config):
        """Should round premiums to 2 decimal places."""
        limit_premiums = pricer.scale_to_limits(
            premium=33333.333,
            config=sample_config
        )

        for premium in limit_premiums.values():
            # Should be rounded to 2 decimals
            assert premium == round(premium, 2)

    def test_no_limit_bands_returns_single(self, pricer):
        """Config without limit bands should return single premium."""
        config = CoverageConfig(
            coverage="test",
            configuration="test",
            version="1.0.0",
            config_hash="hash",
            required_inputs=[],
            signal_groups=[],
            direct_queries=[],
            categorical_groups=[],
            categorical_features={},
            tier_thresholds=[
                TierConfig(tier=1, min_score=0, max_score=1000, base_premium=10000, decision=DecisionType.APPROVE)
            ],
            limit_bands=[],  # No limit bands
            deductible_credits={},
            metadata={}
        )

        limit_premiums = pricer.scale_to_limits(50000, config)

        assert len(limit_premiums) == 1
        assert limit_premiums[0] == 50000


# =============================================================================
# DEDUCTIBLE CREDIT TESTS
# =============================================================================

class TestDeductibleCredits:
    """Tests for deductible credit application."""

    def test_exact_deductible_match(self, pricer, sample_config):
        """Should apply exact deductible credit."""
        premium, credit = pricer.apply_deductible_credit(
            premium=50000,
            deductible=25000,
            config=sample_config
        )

        assert premium == 47500  # 50,000 * 0.95
        assert credit == 0.95

    def test_deductible_between_tiers(self, pricer, sample_config):
        """Should use closest lower deductible credit."""
        premium, credit = pricer.apply_deductible_credit(
            premium=50000,
            deductible=35000,  # Between 25k and 50k
            config=sample_config
        )

        # Should use 25k credit (0.95)
        assert premium == 47500
        assert credit == 0.95

    def test_deductible_above_all_tiers(self, pricer, sample_config):
        """Should use highest deductible credit when above all tiers."""
        premium, credit = pricer.apply_deductible_credit(
            premium=50000,
            deductible=200000,  # Above 100k
            config=sample_config
        )

        # Should use 100k credit (0.85)
        assert premium == 42500
        assert credit == 0.85

    def test_no_deductible_credits_returns_same(self, pricer):
        """Should return same premium when no deductible credits configured."""
        config = CoverageConfig(
            coverage="test",
            configuration="test",
            version="1.0.0",
            config_hash="hash",
            required_inputs=[],
            signal_groups=[],
            direct_queries=[],
            categorical_groups=[],
            categorical_features={},
            tier_thresholds=[
                TierConfig(tier=1, min_score=0, max_score=1000, base_premium=10000, decision=DecisionType.APPROVE)
            ],
            limit_bands=[],
            deductible_credits={},  # No credits
            metadata={}
        )

        premium, credit = pricer.apply_deductible_credit(50000, 25000, config)

        assert premium == 50000
        assert credit == 1.0


# =============================================================================
# FULL PRICING PIPELINE TESTS
# =============================================================================

class TestFullPricingPipeline:
    """Tests for complete price_submission method."""

    def test_price_submission_returns_result(self, pricer, sample_config):
        """Should return complete PricingResult."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_selections={},
            submission_data={},
            config=sample_config
        )

        assert isinstance(result, PricingResult)

    def test_price_submission_populates_fields(self, pricer, sample_config):
        """Should populate all PricingResult fields."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_selections={"operator_type": "major_airline"},
            submission_data={},
            config=sample_config
        )

        assert result.score_based_tier == 2
        assert result.final_tier == 2
        assert result.base_premium == 35000
        assert result.base_premium_method == PremiumMethod.PURE
        assert len(result.modifiers_applied) == 1
        assert result.premium_after_modifiers == 29750  # 35000 * 0.85
        assert len(result.limit_premiums) == 4

    def test_price_submission_with_overrides(self, pricer, sample_config):
        """Should apply tier overrides correctly."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[3],
            query_tier_overrides=[4],
            query_modifiers=[],
            categorical_selections={},
            submission_data={},
            config=sample_config
        )

        assert result.score_based_tier == 2
        assert result.max_tier_override == 4
        assert result.final_tier == 4
        assert result.base_premium == 75000

    def test_price_submission_with_all_components(self, pricer, sample_config):
        """Should handle all pricing components together."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[3],
            query_tier_overrides=[],
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            categorical_selections={
                "operator_type": "major_airline",
                "fleet_category": "widebody"
            },
            submission_data={},
            config=sample_config
        )

        # Score tier 2, override to 3
        assert result.final_tier == 3
        assert result.base_premium == 50000

        # Modifiers: 0.85 * 1.15 * 1.15 = 1.124
        # 50,000 * 0.85 * 1.15 * 1.15 = 56,243.75
        expected_premium = 50000 * 0.85 * 1.15 * 1.15
        assert abs(result.premium_after_modifiers - expected_premium) < 0.01


# =============================================================================
# LIMIT OPTIONS TESTS
# =============================================================================

class TestLimitOptions:
    """Tests for getting limit options with deductible."""

    def test_get_limit_options(self, pricer, sample_config):
        """Should return all limit options with deductible applied."""
        options = pricer.get_limit_options(
            premium=50000,
            deductible=25000,
            config=sample_config
        )

        assert len(options) == 4
        assert all("limit" in opt for opt in options)
        assert all("deductible" in opt for opt in options)
        assert all("final_premium" in opt for opt in options)

    def test_limit_options_sorted_by_limit(self, pricer, sample_config):
        """Options should be sorted by limit."""
        options = pricer.get_limit_options(
            premium=50000,
            deductible=25000,
            config=sample_config
        )

        limits = [opt["limit"] for opt in options]
        assert limits == sorted(limits)


# =============================================================================
# PRICING BREAKDOWN TESTS
# =============================================================================

class TestPricingBreakdown:
    """Tests for pricing breakdown utility."""

    def test_get_pricing_breakdown(self, pricer, sample_config):
        """Should return detailed breakdown dict."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            categorical_selections={"operator_type": "major_airline"},
            submission_data={},
            config=sample_config
        )

        breakdown = pricer.get_pricing_breakdown(result, sample_config)

        assert "tier_resolution" in breakdown
        assert "base_premium" in breakdown
        assert "modifiers" in breakdown
        assert "total_modifier_factor" in breakdown
        assert "limit_options" in breakdown

    def test_breakdown_modifier_impact(self, pricer, sample_config):
        """Breakdown should show modifier impact."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_selections={"operator_type": "major_airline"},
            submission_data={},
            config=sample_config
        )

        breakdown = pricer.get_pricing_breakdown(result, sample_config)

        mod = breakdown["modifiers"][0]
        assert "name" in mod
        assert "factor" in mod
        assert "impact" in mod
        # Impact should be negative for discount
        assert mod["impact"] < 0


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestPricingValidation:
    """Tests for pricing input validation."""

    def test_validate_valid_inputs(self, pricer, sample_config):
        """Should pass validation for valid inputs."""
        is_valid, errors = pricer.validate_pricing_inputs(
            tier=2,
            categorical_selections={"operator_type": "major_airline"},
            config=sample_config
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_tier(self, pricer, sample_config):
        """Should fail for invalid tier."""
        is_valid, errors = pricer.validate_pricing_inputs(
            tier=99,
            categorical_selections={},
            config=sample_config
        )

        assert is_valid is False
        assert any("Invalid tier" in e for e in errors)

    def test_validate_unknown_categorical_group(self, pricer, sample_config):
        """Should fail for unknown categorical group."""
        is_valid, errors = pricer.validate_pricing_inputs(
            tier=2,
            categorical_selections={"unknown_group": "some_value"},
            config=sample_config
        )

        assert is_valid is False
        assert any("Unknown categorical group" in e for e in errors)

    def test_validate_invalid_category(self, pricer, sample_config):
        """Should fail for invalid category value."""
        is_valid, errors = pricer.validate_pricing_inputs(
            tier=2,
            categorical_selections={"operator_type": "invalid_type"},
            config=sample_config
        )

        assert is_valid is False
        assert any("Invalid category" in e for e in errors)
