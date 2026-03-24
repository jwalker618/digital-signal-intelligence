"""
Unit tests for ModelPricer.

Tests premium calculation (Steps 8-12 of the workflow).
"""

import pytest

from layers.risk.pricer import ModelPricer
from layers.risk.types import (
    PricingResult,
    AppliedModifier,
    BasePremiumDerivation,
    CategoricalOutput,
)
from infrastructure.models.config_schema import (
    CoverageConfig,
    ConfigMetadata,
    RiskTierBands,
    RiskTierBand,
    RiskTierInterpretation,
    RiskTierApplication,
    TierBandRange,
    TierAction,
    PricingMethod,
    Guardrails,
    Pricing,
    ProductTypePricing,
    ILFCurve,
    DeductibleFactor,
    LimitConfiguration,
    LimitConfigType,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_tier_band(
    tier_id: int,
    label: str,
    min_score: int,
    max_score: int,
    action: TierAction,
    method: PricingMethod = PricingMethod.PREMIUM_BASE,
    value: int = None,
    applied: float = None,
    basis: str = None,
) -> RiskTierBand:
    """Helper to build a RiskTierBand."""
    return RiskTierBand(
        id=tier_id,
        label=label,
        description=f"Tier {tier_id}",
        interpretation=RiskTierInterpretation(
            bands=TierBandRange(min=min_score, max=max_score),
            action=action,
            application=RiskTierApplication(
                method=method,
                value=value,
                applied=applied,
                basis=basis,
            ),
        ),
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
    """Create a sample config for pricing tests using Pydantic models."""
    return CoverageConfig(
        coverage_id="aerospace",
        config_id="aerospace_general",
        metadata=ConfigMetadata(
            name="Aerospace Test",
            version="1.0.0",
            product_types=["aerospace_hull"],
            min_premium=15000,
        ),
        risk_tier_bands=RiskTierBands(bands=[
            _make_tier_band(1, "PREFERRED", 800, 1000, TierAction.APPROVE,
                            PricingMethod.PREMIUM_BASE, value=25000),
            _make_tier_band(2, "STANDARD", 600, 799, TierAction.APPROVE,
                            PricingMethod.PREMIUM_BASE, value=35000),
            _make_tier_band(3, "SUBSTANDARD", 400, 599, TierAction.REFER,
                            PricingMethod.PREMIUM_BASE, value=50000),
            _make_tier_band(4, "BORDERLINE", 200, 399, TierAction.REFER,
                            PricingMethod.PREMIUM_BASE, value=75000),
            _make_tier_band(5, "DECLINE", 0, 199, TierAction.DECLINE,
                            PricingMethod.PREMIUM_BASE, value=100000),
        ]),
        pricing=Pricing(
            base_limit_reference=1000000,
            base_deductible_reference=25000,
            by_product_type={
                "aerospace_hull": ProductTypePricing(
                    ilf_curve=ILFCurve(
                        anchor_limit=1000000,
                        curve="power",
                        params={"alpha": 0.569},
                    ),
                    deductible_factors=[
                        DeductibleFactor(deductible=10000, factor=1.15),
                        DeductibleFactor(deductible=25000, factor=1.0),
                        DeductibleFactor(deductible=50000, factor=0.90),
                        DeductibleFactor(deductible=100000, factor=0.85),
                    ],
                ),
            },
        ),
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.DECOUPLED,
            valid_limits=[1000000, 5000000, 10000000, 25000000],
            valid_deductibles=[10000, 25000, 50000, 100000],
        ),
        guardrails=Guardrails(
            modifier_floor=0.10,
            modifier_cap=2.50,
            max_premium_to_limit_ratio=0.35,
            max_premium_to_revenue_ratio=0.01,
            max_ilf_factor=10.0,
        ),
    )


@pytest.fixture
def rate_based_config():
    """Create a config with rate-based (MULTIPLIER) pricing."""
    return CoverageConfig(
        coverage_id="aerospace",
        config_id="aerospace_rate",
        metadata=ConfigMetadata(
            name="Aerospace Rate Test",
            version="1.0.0",
            product_types=["aerospace_hull"],
            min_premium=10000,
        ),
        risk_tier_bands=RiskTierBands(bands=[
            _make_tier_band(1, "PREFERRED", 800, 1000, TierAction.APPROVE,
                            PricingMethod.MULTIPLIER, applied=0.005, basis="tiv"),
            _make_tier_band(2, "STANDARD", 600, 799, TierAction.APPROVE,
                            PricingMethod.MULTIPLIER, applied=0.0075, basis="tiv"),
            _make_tier_band(3, "SUBSTANDARD", 400, 599, TierAction.REFER,
                            PricingMethod.MULTIPLIER, applied=0.01, basis="tiv"),
        ]),
        pricing=Pricing(
            base_limit_reference=1000000,
            base_deductible_reference=25000,
            by_product_type={
                "aerospace_hull": ProductTypePricing(
                    ilf_curve=ILFCurve(
                        anchor_limit=1000000,
                        curve="power",
                        params={"alpha": 0.569},
                    ),
                    deductible_factors=[
                        DeductibleFactor(deductible=25000, factor=1.0),
                    ],
                ),
            },
        ),
        guardrails=Guardrails(),
    )


# =============================================================================
# TIER OVERRIDE TESTS (Step 8)
# =============================================================================

class TestTierOverrides:
    """Tests for Step 8: Tier override resolution."""

    def test_no_overrides_returns_score_tier(self, pricer):
        """With no overrides, should return score-based tier."""
        final, max_override = pricer.resolve_tier_overrides(score_tier=2, overrides=[])
        assert final == 2
        assert max_override is None

    def test_single_override_applies(self, pricer):
        """Single override should apply when worse than score tier."""
        final, max_override = pricer.resolve_tier_overrides(score_tier=2, overrides=[4])
        assert final == 4
        assert max_override == 4

    def test_multiple_overrides_max_wins(self, pricer):
        """Maximum override should win when multiple present."""
        final, max_override = pricer.resolve_tier_overrides(score_tier=2, overrides=[3, 5, 4])
        assert final == 5
        assert max_override == 5

    def test_override_below_score_tier_ignored(self, pricer):
        """Override better than score tier should be ignored."""
        final, max_override = pricer.resolve_tier_overrides(score_tier=4, overrides=[2])
        assert final == 4
        assert max_override == 2

    def test_mixed_overrides_max_applied(self, pricer):
        """Should apply max of overrides vs score tier."""
        final, max_override = pricer.resolve_tier_overrides(score_tier=3, overrides=[2, 4, 1])
        assert final == 4
        assert max_override == 4


# =============================================================================
# SCORE TO TIER TESTS
# =============================================================================

class TestScoreToTier:
    """Tests for score to tier mapping."""

    def test_high_score_tier_1(self, pricer, sample_config):
        """High score should map to tier 1."""
        band = pricer.get_tier_for_score(850, sample_config)
        assert band.id == 1

    def test_mid_score_tier_3(self, pricer, sample_config):
        """Mid score should map to tier 3."""
        band = pricer.get_tier_for_score(500, sample_config)
        assert band.id == 3

    def test_low_score_tier_5(self, pricer, sample_config):
        """Low score should map to tier 5."""
        band = pricer.get_tier_for_score(100, sample_config)
        assert band.id == 5

    def test_boundary_score(self, pricer, sample_config):
        """Boundary scores should map correctly."""
        assert pricer.get_tier_for_score(800, sample_config).id == 1
        assert pricer.get_tier_for_score(799, sample_config).id == 2
        assert pricer.get_tier_for_score(600, sample_config).id == 2
        assert pricer.get_tier_for_score(599, sample_config).id == 3


# =============================================================================
# BASE PREMIUM TESTS (Step 10)
# =============================================================================

class TestBasePremium:
    """Tests for Step 10: Base premium generation."""

    def test_premium_base_method(self, pricer, sample_config):
        """Should use PREMIUM_BASE value from tier band."""
        tier_band = sample_config.get_tier_band(1)
        premium, method, derivation = pricer.calculate_base_premium(
            tier=1,
            tier_band=tier_band,
            submission_data={},
            config=sample_config,
        )

        assert premium == 25000
        assert method == "premium_base"
        assert derivation.method == "PREMIUM_BASE"

    def test_multiplier_method(self, pricer, rate_based_config):
        """Should calculate premium from rate * TIV."""
        tier_band = rate_based_config.get_tier_band(1)
        submission_data = {"tiv": 10000000}

        premium, method, derivation = pricer.calculate_base_premium(
            tier=1,
            tier_band=tier_band,
            submission_data=submission_data,
            config=rate_based_config,
        )

        # 10M * 0.5% = 50,000
        assert premium == 50000
        assert method == "multiplier"
        assert derivation.basis_value == 10000000

    def test_multiplier_missing_basis_uses_fallback(self, pricer, rate_based_config):
        """Missing rate basis should use fallback."""
        tier_band = rate_based_config.get_tier_band(1)
        submission_data = {}  # No TIV provided

        premium, method, derivation = pricer.calculate_base_premium(
            tier=1,
            tier_band=tier_band,
            submission_data=submission_data,
            config=rate_based_config,
        )

        # Fallback to min_premium or default
        assert premium == 10000
        assert derivation.basis_value is None

    def test_missing_tier_band_uses_default(self, pricer, sample_config):
        """Missing tier band should use minimum premium."""
        premium, method, _ = pricer.calculate_base_premium(
            tier=99,
            tier_band=None,
            submission_data={},
            config=sample_config,
        )

        assert premium == 15000  # min_premium from metadata


# =============================================================================
# MODIFIER TESTS (Step 11)
# =============================================================================

class TestModifiers:
    """Tests for Step 11: Modifier application."""

    def test_categorical_modifier_applied(self, pricer, sample_config):
        """Should apply categorical modifier."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type",
                group_name="operator_type",
                category="major_airline",
                label="Major Airline",
                modifier=0.85,
                confidence=0.9,
            ),
        ]
        modifiers, total, premium, clamped = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=cat_outputs,
            query_modifiers=[],
            config=sample_config,
        )

        # 50,000 * 0.85 = 42,500
        assert premium == 42500
        assert len(modifiers) == 1
        assert modifiers[0].factor == 0.85
        assert not clamped

    def test_multiple_categorical_modifiers(self, pricer, sample_config):
        """Should apply multiple categorical modifiers."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type", group_name="operator_type",
                category="charter_operator", label="Charter Operator",
                modifier=1.25, confidence=0.9,
            ),
            CategoricalOutput(
                group_id="fleet_category", group_name="fleet_category",
                category="helicopter", label="Helicopter",
                modifier=1.40, confidence=0.9,
            ),
        ]
        modifiers, total, premium, clamped = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=cat_outputs,
            query_modifiers=[],
            config=sample_config,
        )

        # 50,000 * 1.25 * 1.40 = 87,500
        expected = 50000 * 1.25 * 1.40
        assert abs(premium - expected) < 0.01
        assert len(modifiers) == 2

    def test_query_modifier_applied(self, pricer, sample_config):
        """Should apply query modifiers."""
        modifiers, total, premium, clamped = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=[],
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            config=sample_config,
        )

        # 50,000 * 1.15 = 57,500
        assert abs(premium - 57500) < 0.01
        assert len(modifiers) == 1
        assert modifiers[0].source == "direct_query"

    def test_combined_modifiers(self, pricer, sample_config):
        """Should apply categorical then query modifiers."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type", group_name="operator_type",
                category="major_airline", label="Major Airline",
                modifier=0.85, confidence=0.9,
            ),
        ]
        modifiers, total, premium, clamped = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=cat_outputs,
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            config=sample_config,
        )

        # 50,000 * 0.85 * 1.15 = 48,875
        expected = 50000 * 0.85 * 1.15
        assert abs(premium - expected) < 0.01
        assert len(modifiers) == 2

    def test_modifier_1_0_skipped(self, pricer, sample_config):
        """Modifiers with factor 1.0 should be skipped."""
        modifiers, total, premium, clamped = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=[],
            query_modifiers=[{"name": "no_impact", "factor": 1.0}],
            config=sample_config,
        )

        assert premium == 50000
        assert len(modifiers) == 0

    def test_modifier_tracks_before_after(self, pricer, sample_config):
        """Modifier should track premium before and after."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type", group_name="operator_type",
                category="major_airline", label="Major Airline",
                modifier=0.85, confidence=0.9,
            ),
        ]
        modifiers, _, _, _ = pricer.apply_modifiers(
            base_premium=50000,
            categorical_outputs=cat_outputs,
            query_modifiers=[],
            config=sample_config,
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
        """Should scale premium across all limit bands with detail breakdown."""
        limit_premiums, limit_details = pricer.scale_to_limits(
            premium=50000,
            submission_data={"deductible": 25000},
            config=sample_config,
        )

        assert len(limit_premiums) == 4
        # With parametric power curve (alpha=0.569, anchor=1M) and deductible factor 1.0
        assert limit_premiums["1000000"] == 50000  # ILF 1.0 at anchor
        assert limit_premiums["5000000"] > 100000  # ILF ~2.5
        assert limit_premiums["10000000"] > limit_premiums["5000000"]  # monotonically increasing
        assert limit_premiums["25000000"] > limit_premiums["10000000"]

        # LimitPremiumDetail objects carry component factors
        assert len(limit_details) == 4
        detail_1m = next(d for d in limit_details if d.limit == 1_000_000)
        assert detail_1m.ilf_factor == 1.0  # anchor always = 1.0
        assert detail_1m.deductible_factor == 1.0
        assert detail_1m.premium_before_scaling == 50000
        assert detail_1m.premium_after_scaling == 50000

        detail_25m = next(d for d in limit_details if d.limit == 25_000_000)
        assert detail_25m.ilf_factor > 5.0  # power curve ILF for 25x anchor
        assert detail_25m.premium_after_scaling == limit_premiums["25000000"]

    def test_no_limit_config_returns_empty(self, pricer):
        """Config without limit configuration should return empty dict."""
        config = CoverageConfig(
            coverage_id="test",
            config_id="test",
            metadata=ConfigMetadata(
                name="Test", version="1.0.0", product_types=["test"],
            ),
            risk_tier_bands=RiskTierBands(bands=[
                _make_tier_band(1, "PREFERRED", 0, 1000, TierAction.APPROVE,
                                PricingMethod.PREMIUM_BASE, value=10000),
            ]),
            pricing=Pricing(
                base_limit_reference=1000000,
                base_deductible_reference=25000,
                by_product_type={},
            ),
            guardrails=Guardrails(),
        )

        limit_premiums, limit_details = pricer.scale_to_limits(50000, {}, config)
        assert len(limit_premiums) == 0
        assert len(limit_details) == 0


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
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )

        assert isinstance(result, PricingResult)

    def test_price_submission_populates_fields(self, pricer, sample_config):
        """Should populate all PricingResult fields."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type", group_name="operator_type",
                category="major_airline", label="Major Airline",
                modifier=0.85, confidence=0.9,
            ),
        ]
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=cat_outputs,
            submission_data={"deductible": 25000},
            config=sample_config,
        )

        assert result.score_based_tier == 2
        assert result.final_tier == 2
        assert result.base_premium == 35000
        assert result.base_premium_method == "premium_base"
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
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )

        assert result.score_based_tier == 2
        assert result.max_tier_override == 4
        assert result.final_tier == 4
        assert result.base_premium == 75000

    def test_price_submission_with_all_components(self, pricer, sample_config):
        """Should handle all pricing components together."""
        cat_outputs = [
            CategoricalOutput(
                group_id="operator_type", group_name="operator_type",
                category="major_airline", label="Major Airline",
                modifier=0.85, confidence=0.9,
            ),
        ]
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[3],
            query_tier_overrides=[],
            query_modifiers=[{"name": "wet_lease", "factor": 1.15}],
            categorical_outputs=cat_outputs,
            submission_data={"deductible": 25000},
            config=sample_config,
        )

        # Score tier 2, override to 3
        assert result.final_tier == 3
        assert result.base_premium == 50000

        # Modifiers: 0.85 * 1.15 = 0.9775
        # 50,000 * 0.85 * 1.15 = 48,875
        expected_premium = 50000 * 0.85 * 1.15
        assert abs(result.premium_after_modifiers - expected_premium) < 0.01


# =============================================================================
# PHASE A: NEW CAPABILITY TESTS
# =============================================================================

class TestUncappedPremium:
    """Tests for A1: uncapped premium capture."""

    def test_uncapped_premium_none_when_not_capped(self, pricer, sample_config):
        """When premium is within guardrails, uncapped_premium should be None."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000, "limit": 1000000},
            config=sample_config,
        )
        assert result.premium_was_capped is False
        assert result.uncapped_premium is None

    def test_uncapped_premium_captured_when_capped(self, pricer, sample_config):
        """When premium exceeds guardrail, uncapped premium should be preserved."""
        # Use a modifier to push premium past the limit ratio cap
        # Tier 4 (score 250) has base_premium=75000, modifier 2.5 → 187,500
        # With ILF at 1M ≈ 1.0, limit cap = 1M × 0.35 = 350,000 → not capped
        # But with revenue cap: revenue 100K × 0.01 = 1,000 → will cap
        result = pricer.price_submission(
            pure_composite_score=250,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[{"name": "loading", "factor": 2.0}],
            categorical_outputs=[],
            submission_data={"deductible": 25000, "limit": 1000000, "revenue": 100000},
            config=sample_config,
        )
        assert result.premium_was_capped is True
        assert result.uncapped_premium is not None
        assert result.uncapped_premium > result.final_premium


class TestLimitPremiumDetails:
    """Tests for A2: ILF transparency via LimitPremiumDetail."""

    def test_limit_details_populated(self, pricer, sample_config):
        """Each limit option should have a LimitPremiumDetail."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        assert len(result.limit_premium_details) == len(result.limit_premiums)

    def test_limit_details_have_component_factors(self, pricer, sample_config):
        """LimitPremiumDetail should store ilf_factor and deductible_factor."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        for detail in result.limit_premium_details:
            assert detail.ilf_factor >= 1.0
            assert detail.deductible_factor > 0
            assert detail.premium_before_scaling > 0
            assert detail.premium_after_scaling > 0
            # Verify the math: premium = base × ilf × ded_factor
            expected = round(detail.premium_before_scaling * detail.ilf_factor * detail.deductible_factor, 2)
            assert abs(detail.premium_after_scaling - expected) < 0.01

    def test_anchor_limit_ilf_is_one(self, pricer, sample_config):
        """ILF at anchor limit should be 1.0."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        anchor_detail = next(
            (d for d in result.limit_premium_details if d.limit == 1000000), None
        )
        assert anchor_detail is not None
        assert anchor_detail.ilf_factor == 1.0


class TestTierMargin:
    """Tests for A4: tier margin context."""

    def test_tier_margin_populated(self, pricer, sample_config):
        """PricingResult should include tier margin context."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        margin = result.tier_margin
        assert margin is not None
        assert margin.score == 750
        assert margin.tier_id == 2  # score 750 → tier 2 (600-799)
        assert 0.0 <= margin.percentile_in_tier <= 1.0

    def test_tier_margin_distance_to_boundaries(self, pricer, sample_config):
        """Should calculate distance to adjacent tier boundaries."""
        result = pricer.price_submission(
            pure_composite_score=750,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        margin = result.tier_margin
        # Tier 2 is 600-799, score 750
        assert margin.distance_to_better_tier == 150.0  # 750 - 600 = 150
        assert margin.distance_to_worse_tier == 49.0    # 799 - 750 = 49
        assert margin.adjacent_better_tier == 1
        assert margin.adjacent_worse_tier == 3

    def test_tier_margin_best_tier_no_better(self, pricer, sample_config):
        """Best tier should have no adjacent_better_tier but still show distance."""
        result = pricer.price_submission(
            pure_composite_score=950,
            signal_tier_overrides=[],
            query_tier_overrides=[],
            query_modifiers=[],
            categorical_outputs=[],
            submission_data={"deductible": 25000},
            config=sample_config,
        )
        margin = result.tier_margin
        assert margin.tier_id == 1  # best tier
        assert margin.adjacent_better_tier is None
        # Distance always populated — shows headroom within the tier
        assert margin.distance_to_better_tier >= 0
        assert margin.distance_to_worse_tier >= 0


class TestParametricOnlyILF:
    """Tests for A5: table-based ILF removal."""

    def test_table_ilf_rejected(self):
        """ILFCurve should reject table-based configuration."""
        with pytest.raises(Exception):
            ILFCurve(base_limit=1000000, factors=[])

    def test_parametric_ilf_required(self):
        """ILFCurve must have anchor_limit and curve."""
        curve = ILFCurve(
            anchor_limit=5000000,
            curve="power",
            params={"alpha": 0.5},
        )
        assert curve.is_parametric is True
        assert curve.get_factor_for_limit(5000000) == 1.0
        assert curve.get_factor_for_limit(20000000) > 1.0
