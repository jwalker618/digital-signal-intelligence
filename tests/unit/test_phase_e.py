"""
Unit tests for Phase E: Tower & Subscription Market Structure.

Tests cover:
  - E2: Tower layer schema and bespoke validation
  - E3: Multi-layer pricing via ILF differentials
  - E4: Subscription order/line model with lead/follow
  - E5: LayerPremiumDetail output type
  - Ground-up regression (no impact on existing behaviour)
"""

import pytest

from layers.risk.pricer import ModelPricer
from layers.risk.types import LimitPremiumDetail, LayerPremiumDetail
from layers.risk.rol_validator import ROLValidator
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
    TowerLayer,
    SubscriptionOrder,
    SubscriptionLine,
    LineRole,
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


def _base_pricing():
    """Shared pricing config with power ILF curve (alpha=0.569)."""
    return Pricing(
        base_limit_reference=1000000,
        base_deductible_reference=25000,
        by_product_type={
            "liability": ProductTypePricing(
                ilf_curve=ILFCurve(
                    anchor_limit=1000000,
                    curve="power",
                    params={"alpha": 0.569},
                ),
                deductible_factors=[
                    DeductibleFactor(deductible=25000, factor=1.0),
                    DeductibleFactor(deductible=50000, factor=0.90),
                ],
            ),
        },
    )


def _base_pricing_with_lead_loading(factor: float = 1.10):
    """Pricing config with lead loading factor."""
    return Pricing(
        base_limit_reference=1000000,
        base_deductible_reference=25000,
        by_product_type={
            "liability": ProductTypePricing(
                ilf_curve=ILFCurve(
                    anchor_limit=1000000,
                    curve="power",
                    params={"alpha": 0.569},
                ),
                deductible_factors=[
                    DeductibleFactor(deductible=25000, factor=1.0),
                    DeductibleFactor(deductible=50000, factor=0.90),
                ],
                lead_loading_factor=factor,
            ),
        },
    )


def _base_tiers():
    return RiskTierBands(bands=[
        _make_tier_band(1, "PREFERRED", 800, 1000, TierAction.APPROVE,
                        PricingMethod.PREMIUM_BASE, value=50000),
        _make_tier_band(2, "STANDARD", 600, 799, TierAction.APPROVE,
                        PricingMethod.PREMIUM_BASE, value=75000),
        _make_tier_band(3, "DECLINE", 0, 599, TierAction.DECLINE,
                        PricingMethod.PREMIUM_BASE, value=100000),
    ])


def _base_metadata():
    return ConfigMetadata(
        name="Phase E Test",
        version="1.0.0",
        product_types=["liability"],
        min_premium=1000,
    )


# =============================================================================
# E2: TOWER LAYER SCHEMA TESTS
# =============================================================================

class TestTowerLayerSchema:
    """Tests for tower layer configuration schema and validation."""

    def test_valid_tower_config(self):
        """Standard tower with contiguous layers validates successfully."""
        config = LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=10_000_000),
                TowerLayer(id=2, label="First Excess", attachment=10_000_000, limit=15_000_000),
                TowerLayer(id=3, label="Second Excess", attachment=25_000_000, limit=25_000_000),
            ],
        )
        assert len(config.layers) == 3
        assert config.type == LimitConfigType.TOWER

    def test_bespoke_tower_with_gap(self):
        """Bespoke tower with a gap between layers is valid."""
        config = LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=5_000_000),
                # Gap: 5M to 10M uninsured
                TowerLayer(id=2, label="Excess", attachment=10_000_000, limit=10_000_000),
            ],
        )
        assert len(config.layers) == 2

    def test_bespoke_tower_non_standard_widths(self):
        """Thin primary with wide excess is valid."""
        config = LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                TowerLayer(id=2, label="Wide Excess", attachment=1_000_000, limit=99_000_000),
            ],
        )
        assert config.layers[1].limit == 99_000_000

    def test_tower_overlapping_layers_rejected(self):
        """Overlapping layers within the same config are rejected."""
        with pytest.raises(ValueError, match="overlap"):
            LimitConfiguration(
                type=LimitConfigType.TOWER,
                layers=[
                    TowerLayer(id=1, label="Primary", attachment=0, limit=10_000_000),
                    TowerLayer(id=2, label="Overlap", attachment=5_000_000, limit=10_000_000),
                ],
            )

    def test_tower_requires_layers(self):
        """TOWER mode without layers raises validation error."""
        with pytest.raises(ValueError, match="requires 'layers'"):
            LimitConfiguration(type=LimitConfigType.TOWER)

    def test_tower_layer_zero_limit_rejected(self):
        """Layer with limit=0 is rejected."""
        with pytest.raises(ValueError):
            TowerLayer(id=1, label="Bad", attachment=0, limit=0)

    def test_tower_layer_negative_attachment_rejected(self):
        """Layer with negative attachment is rejected."""
        with pytest.raises(ValueError):
            TowerLayer(id=1, label="Bad", attachment=-1, limit=1_000_000)


# =============================================================================
# E3: MULTI-LAYER PRICING ENGINE TESTS
# =============================================================================

class TestTowerPricing:
    """Tests for tower layer pricing via ILF differentials."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.fixture
    def tower_config(self):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_tower",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.TOWER,
                layers=[
                    TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                    TowerLayer(id=2, label="First Excess", attachment=1_000_000, limit=4_000_000),
                    TowerLayer(id=3, label="Second Excess", attachment=5_000_000, limit=5_000_000),
                ],
            ),
        )

    def test_tower_produces_single_limit_premium(self, pricer, tower_config):
        """Tower config produces a single technical premium at the total limit.

        Per-layer decomposition is now handled by PremiumAssembler,
        not the pricer. The pricer prices at the requested limit.
        """
        total_limit = 10_000_000  # 1M + 4M + 5M
        premium = 50000.0
        limit_premiums, limit_details = pricer.scale_to_limits(
            premium, {"deductible": 25000, "limit": total_limit}, tower_config
        )
        assert len(limit_details) == 1
        assert limit_details[0].limit == total_limit

    def test_tower_ilf_at_total_limit(self, pricer, tower_config):
        """Technical premium uses ILF at the total program limit."""
        total_limit = 10_000_000
        premium = 50000.0
        _, details = pricer.scale_to_limits(
            premium, {"deductible": 25000, "limit": total_limit}, tower_config
        )
        detail = details[0]
        expected_ilf = tower_config.get_ilf("liability", total_limit)
        assert abs(detail.ilf_factor - expected_ilf) < 0.001

    def test_tower_with_deductible_factor(self, pricer, tower_config):
        """Deductible factor applies to tower technical premium."""
        total_limit = 10_000_000
        _, details_25k = pricer.scale_to_limits(
            50000, {"deductible": 25000, "limit": total_limit}, tower_config
        )
        _, details_50k = pricer.scale_to_limits(
            50000, {"deductible": 50000, "limit": total_limit}, tower_config
        )
        # 50k deductible should produce lower premium than 25k
        assert details_50k[0].premium_after_scaling < details_25k[0].premium_after_scaling

    def test_tower_no_limit_returns_empty(self, pricer, tower_config):
        """Without a requested limit, tower returns empty (assembly handles distribution)."""
        premium = 50000.0
        limit_premiums, limit_details = pricer.scale_to_limits(
            premium, {"deductible": 25000}, tower_config
        )
        assert len(limit_details) == 0


# =============================================================================
# E3+: PRICE_TOWER_LAYERS (DETAILED OUTPUT)
# =============================================================================

class TestPriceTowerLayers:
    """Tests for price_tower_layers producing LayerPremiumDetail."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.fixture
    def tower_config(self):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_tower",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.TOWER,
                layers=[
                    TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                    TowerLayer(id=2, label="Excess", attachment=1_000_000, limit=4_000_000),
                ],
            ),
        )

    def test_returns_layer_premium_details(self, pricer, tower_config):
        """price_tower_layers returns LayerPremiumDetail objects."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, tower_config)
        assert len(layers) == 2
        assert isinstance(layers[0], LayerPremiumDetail)

    def test_layer_detail_fields(self, pricer, tower_config):
        """LayerPremiumDetail has correct ILF components."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, tower_config)
        primary = layers[0]
        assert primary.layer_id == 1
        assert primary.layer_label == "Primary"
        assert primary.attachment == 0
        assert primary.limit == 1_000_000
        assert primary.ilf_bottom == 0.0 or primary.ilf_bottom >= 0
        assert primary.ilf_top > 0
        assert primary.layer_ilf == primary.ilf_top - primary.ilf_bottom
        assert primary.order_premium > 0
        assert primary.rol > 0

    def test_default_follow_role(self, pricer, tower_config):
        """Without subscription line, role defaults to FOLLOW."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, tower_config)
        for layer in layers:
            assert layer.role == "FOLLOW"
            assert layer.signed_line == 1.0
            assert layer.lead_loading == 1.0
            assert layer.line_premium == layer.order_premium

    def test_returns_empty_for_ground_up(self, pricer):
        """price_tower_layers returns [] for non-tower config."""
        config = CoverageConfig(
            coverage_id="test", config_id="test_gu",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.DECOUPLED,
                valid_limits=[1_000_000, 5_000_000],
                valid_deductibles=[25000],
            ),
        )
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, config)
        assert layers == []


# =============================================================================
# E4: SUBSCRIPTION ORDER/LINE TESTS
# =============================================================================

class TestSubscriptionSchema:
    """Tests for subscription order/line schema."""

    def test_valid_subscription_config(self):
        """Valid subscription config with order and line."""
        config = LimitConfiguration(
            type=LimitConfigType.SUBSCRIPTION,
            subscription_order=SubscriptionOrder(total_limit=50_000_000),
            subscription_line=SubscriptionLine(
                minimum_line=0.05,
                maximum_line=0.25,
                signed_line=0.15,
                role=LineRole.FOLLOW,
            ),
        )
        assert config.subscription_order.total_limit == 50_000_000
        assert config.subscription_line.signed_line == 0.15

    def test_subscription_requires_order(self):
        """SUBSCRIPTION mode without order raises error."""
        with pytest.raises(ValueError, match="requires 'subscription_order'"):
            LimitConfiguration(type=LimitConfigType.SUBSCRIPTION)

    def test_line_bounds_validation(self):
        """signed_line must be between min and max."""
        with pytest.raises(ValueError, match="signed_line"):
            SubscriptionLine(
                minimum_line=0.10,
                maximum_line=0.20,
                signed_line=0.30,
            )

    def test_line_max_below_min_rejected(self):
        """maximum_line < minimum_line is rejected."""
        with pytest.raises(ValueError, match="maximum_line"):
            SubscriptionLine(
                minimum_line=0.25,
                maximum_line=0.10,
            )

    def test_any_line_between_min_max_valid(self):
        """Any value between min and max is valid — no discrete options."""
        line = SubscriptionLine(
            minimum_line=0.05,
            maximum_line=0.25,
            signed_line=0.1337,  # arbitrary value
        )
        assert line.signed_line == 0.1337

    def test_line_without_signed(self):
        """Line with no signed_line is valid (pre-binding)."""
        line = SubscriptionLine(
            minimum_line=0.05,
            maximum_line=0.25,
        )
        assert line.signed_line is None

    def test_lead_role(self):
        """Line can specify LEAD role."""
        line = SubscriptionLine(
            minimum_line=0.10,
            maximum_line=0.30,
            signed_line=0.20,
            role=LineRole.LEAD,
        )
        assert line.role == LineRole.LEAD


class TestSubscriptionPricing:
    """Tests for subscription order-level pricing and line allocation."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.fixture
    def subscription_config(self):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_sub",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.SUBSCRIPTION,
                subscription_order=SubscriptionOrder(total_limit=10_000_000),
                subscription_line=SubscriptionLine(
                    minimum_line=0.05,
                    maximum_line=0.25,
                    signed_line=0.10,
                    role=LineRole.FOLLOW,
                ),
            ),
        )

    def test_order_level_pricing(self, pricer, subscription_config):
        """scale_to_limits prices at the requested limit (single-limit pricing)."""
        premium = 50000.0
        limit_premiums, details = pricer.scale_to_limits(
            premium, {"deductible": 25000, "limit": 10_000_000}, subscription_config
        )
        assert len(details) == 1
        assert details[0].limit == 10_000_000
        ilf = subscription_config.get_ilf("liability", 10_000_000)
        expected = round(premium * ilf * 1.0, 2)
        assert details[0].premium_after_scaling == expected

    def test_line_premium_allocation(self, pricer, subscription_config):
        """price_tower_layers allocates line premium = signed_line * order_premium."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, subscription_config)
        assert len(layers) == 1
        layer = layers[0]
        assert layer.signed_line == 0.10
        expected_line = round(layer.order_premium * 0.10 * 1.0, 2)
        assert layer.line_premium == expected_line

    def test_rol_at_order_level(self, pricer, subscription_config):
        """ROL is calculated at order level, not line level."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, subscription_config)
        layer = layers[0]
        expected_rol = layer.order_premium / layer.limit
        assert abs(layer.rol - expected_rol) < 0.0001


# =============================================================================
# E4: LEAD VS FOLLOW PRICING
# =============================================================================

class TestLeadFollowPricing:
    """Tests for lead/follow role pricing impact."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    def _make_config(self, role: LineRole, loading: float = 1.10):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_lf",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing_with_lead_loading(loading),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.SUBSCRIPTION,
                subscription_order=SubscriptionOrder(total_limit=10_000_000),
                subscription_line=SubscriptionLine(
                    minimum_line=0.10,
                    maximum_line=0.25,
                    signed_line=0.15,
                    role=role,
                ),
            ),
        )

    def test_lead_gets_loading(self, pricer):
        """Lead insurer gets lead_loading_factor applied."""
        config = self._make_config(LineRole.LEAD, 1.10)
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, config)
        layer = layers[0]
        assert layer.role == "LEAD"
        assert layer.lead_loading == 1.10
        expected = round(layer.order_premium * 0.15 * 1.10, 2)
        assert layer.line_premium == expected

    def test_follow_at_par(self, pricer):
        """Follow insurer gets no loading (factor = 1.0)."""
        config = self._make_config(LineRole.FOLLOW, 1.10)
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, config)
        layer = layers[0]
        assert layer.role == "FOLLOW"
        assert layer.lead_loading == 1.0
        expected = round(layer.order_premium * 0.15 * 1.0, 2)
        assert layer.line_premium == expected

    def test_lead_follow_same_order_premium(self, pricer):
        """Lead and follow see the same order premium."""
        lead_config = self._make_config(LineRole.LEAD)
        follow_config = self._make_config(LineRole.FOLLOW)
        lead_layers = pricer.price_tower_layers(50000, {"deductible": 25000}, lead_config)
        follow_layers = pricer.price_tower_layers(50000, {"deductible": 25000}, follow_config)
        assert lead_layers[0].order_premium == follow_layers[0].order_premium

    def test_lead_premium_higher_than_follow(self, pricer):
        """Lead's line premium is higher than follow's at the same signed_line."""
        lead_config = self._make_config(LineRole.LEAD, 1.15)
        follow_config = self._make_config(LineRole.FOLLOW, 1.15)
        lead_layers = pricer.price_tower_layers(50000, {"deductible": 25000}, lead_config)
        follow_layers = pricer.price_tower_layers(50000, {"deductible": 25000}, follow_config)
        assert lead_layers[0].line_premium > follow_layers[0].line_premium


# =============================================================================
# COMBINED TOWER + SUBSCRIPTION
# =============================================================================

class TestTowerSubscription:
    """Tests for tower layers with subscription line allocation."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.fixture
    def tower_sub_config(self):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_tower_sub",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing_with_lead_loading(1.10),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.TOWER,
                layers=[
                    TowerLayer(id=1, label="Primary", attachment=0, limit=5_000_000),
                    TowerLayer(id=2, label="Excess", attachment=5_000_000, limit=5_000_000),
                ],
                subscription_line=SubscriptionLine(
                    minimum_line=0.05,
                    maximum_line=0.25,
                    signed_line=0.20,
                    role=LineRole.LEAD,
                ),
            ),
        )

    def test_tower_with_line_allocation(self, pricer, tower_sub_config):
        """Tower layers with subscription line applied per-layer."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, tower_sub_config)
        assert len(layers) == 2
        for layer in layers:
            assert layer.signed_line == 0.20
            assert layer.role == "LEAD"
            assert layer.lead_loading == 1.10
            expected = round(layer.order_premium * 0.20 * 1.10, 2)
            assert layer.line_premium == expected

    def test_tower_sub_rol_at_order_level(self, pricer, tower_sub_config):
        """ROL is at the 100% order level even with subscription."""
        layers = pricer.price_tower_layers(50000, {"deductible": 25000}, tower_sub_config)
        for layer in layers:
            expected_rol = layer.order_premium / layer.limit
            assert abs(layer.rol - expected_rol) < 0.0001


# =============================================================================
# GROUND-UP REGRESSION
# =============================================================================

class TestGroundUpRegression:
    """Verify existing ground-up pricing is unaffected by Phase E changes."""

    @pytest.fixture
    def pricer(self):
        return ModelPricer()

    @pytest.fixture
    def decoupled_config(self):
        return CoverageConfig(
            coverage_id="test",
            config_id="test_gu",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.DECOUPLED,
                valid_limits=[1_000_000, 5_000_000, 10_000_000],
                valid_deductibles=[25000, 50000],
            ),
        )

    def test_decoupled_unchanged(self, pricer, decoupled_config):
        """DECOUPLED pricing produces same results as before Phase E."""
        premium = 50000.0
        limit_premiums, details = pricer.scale_to_limits(
            premium, {"deductible": 25000}, decoupled_config
        )
        assert len(details) == 3
        for d in details:
            assert d.attachment_point is None
            ilf = decoupled_config.get_ilf("liability", d.limit)
            expected = round(premium * ilf * 1.0, 2)
            assert d.premium_after_scaling == expected

    def test_decoupled_no_tower_fields(self, pricer, decoupled_config):
        """Ground-up LimitPremiumDetail has no attachment."""
        _, details = pricer.scale_to_limits(50000, {"deductible": 25000}, decoupled_config)
        for d in details:
            assert d.attachment_point is None


# =============================================================================
# HEALTH GATE COMPATIBILITY
# =============================================================================

class TestHealthGatePhaseE:
    """Verify health gate handles tower/subscription configs."""

    def test_tower_config_validates(self):
        """Tower config passes Pydantic validation for CoverageConfig."""
        config = CoverageConfig(
            coverage_id="test",
            config_id="test_tower",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.TOWER,
                layers=[
                    TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                    TowerLayer(id=2, label="Excess", attachment=1_000_000, limit=4_000_000),
                ],
            ),
        )
        assert config.limit_configuration.type == LimitConfigType.TOWER

    def test_subscription_config_validates(self):
        """Subscription config passes Pydantic validation for CoverageConfig."""
        config = CoverageConfig(
            coverage_id="test",
            config_id="test_sub",
            metadata=_base_metadata(),
            risk_tier_bands=_base_tiers(),
            pricing=_base_pricing(),
            limit_configuration=LimitConfiguration(
                type=LimitConfigType.SUBSCRIPTION,
                subscription_order=SubscriptionOrder(total_limit=50_000_000),
                subscription_line=SubscriptionLine(
                    minimum_line=0.05,
                    maximum_line=0.25,
                    role=LineRole.LEAD,
                ),
            ),
        )
        assert config.limit_configuration.type == LimitConfigType.SUBSCRIPTION
