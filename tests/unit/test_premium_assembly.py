"""Tests for layers.risk.premium_assembly — premium assembly layer."""

import pytest
from layers.risk.premium_assembly import (
    PremiumAssembler,
    PremiumBreakdown,
    CommissionBreakdown,
    TaxBreakdown,
    LayerBreakdown,
)
from layers.risk.fx import FXConverter, StaticRateProvider, Currency
from infrastructure.models.commercial_schema import (
    CommercialEntity,
    CoverageBinding,
    DistributionConfig,
    DistributionType,
    SubscriptionTerms,
    CommissionStructure,
    TaxesAndLevies,
    PricingAdjustments,
    FrontingTerms,
    EntityRole,
)
# Reuse helpers from test_phase_e
from tests.unit.test_phase_e import _base_metadata, _base_tiers, _base_pricing
from infrastructure.models.config_schema import (
    CoverageConfig,
    LimitConfiguration,
    LimitConfigType,
)


def _minimal_config():
    """Create a minimal CoverageConfig for assembly tests."""
    return CoverageConfig(
        coverage_id="test",
        config_id="test_config",
        metadata=_base_metadata(),
        risk_tier_bands=_base_tiers(),
        pricing=_base_pricing(),
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.DECOUPLED,
            min_limit=250_000,
            max_limit=100_000_000,
            min_deductible=10_000,
            max_deductible=1_000_000,
        ),
    )


@pytest.fixture
def fx_converter():
    return FXConverter(StaticRateProvider())


@pytest.fixture
def minimal_config():
    return _minimal_config()


@pytest.fixture
def subscription_entity():
    """Lloyd's syndicate — GBP, subscription, follow."""
    return CommercialEntity(
        id="test_syndicate",
        name="Test Syndicate",
        market="lloyds",
        base_currency="GBP",
        coverages=[
            CoverageBinding(coverage="energy", max_single_limit=500_000_000),
        ],
        distribution=DistributionConfig(
            type=DistributionType.SUBSCRIPTION,
            subscription=SubscriptionTerms(
                minimum_line=0.05,
                maximum_line=0.25,
                default_signed_line=0.10,
                role=EntityRole.FOLLOW,
                lead_loading_factor=1.0,
            ),
        ),
        commission=CommissionStructure(
            brokerage_rate=0.20,
            overrider_rate=0.025,
        ),
        taxes_and_levies=TaxesAndLevies(
            insurance_premium_tax_rate=0.12,
            regulatory_levy_rate=0.01,
        ),
        pricing_adjustments=PricingAdjustments(
            offered_premium_discretion=0.10,
            minimum_gross_premium=7500,
        ),
    )


@pytest.fixture
def direct_entity():
    """US direct writer — USD, no subscription."""
    return CommercialEntity(
        id="test_direct",
        name="Test Direct",
        market="us",
        base_currency="USD",
        coverages=[
            CoverageBinding(coverage="cyber", max_single_limit=50_000_000),
        ],
        distribution=DistributionConfig(type=DistributionType.DIRECT),
        commission=CommissionStructure(brokerage_rate=0.15),
        taxes_and_levies=TaxesAndLevies(insurance_premium_tax_rate=0.03),
        pricing_adjustments=PricingAdjustments(minimum_gross_premium=2500),
    )


class TestPremiumAssembler:
    """Tests for the premium assembly pipeline."""

    def test_usd_direct_assembly(self, fx_converter, direct_entity, minimal_config):
        """USD direct writer: technical → gross without FX or line allocation."""
        assembler = PremiumAssembler(fx_converter)
        breakdown = assembler.assemble(
            technical_premium_usd=100_000.0,
            submission_data={"limit": 10_000_000, "deductible": 50_000},
            config=minimal_config,
            entity=direct_entity,
        )

        assert isinstance(breakdown, PremiumBreakdown)
        assert breakdown.technical_premium_usd == 100_000.0
        # USD entity — no FX conversion
        assert breakdown.technical_premium_local == 100_000.0
        assert breakdown.currency == "USD"
        # Commission = 15% of net
        assert breakdown.commission.brokerage > 0
        # Taxes = 3% of (net + commission)
        assert breakdown.taxes.total_taxes > 0
        # Gross > technical (commission + taxes added)
        assert breakdown.gross_premium > breakdown.technical_premium_usd

    def test_gbp_subscription_assembly(self, fx_converter, subscription_entity, minimal_config):
        """GBP subscription: FX conversion, signed line, commission, taxes."""
        assembler = PremiumAssembler(fx_converter)
        breakdown = assembler.assemble(
            technical_premium_usd=100_000.0,
            submission_data={"limit": 50_000_000, "deductible": 100_000},
            config=minimal_config,
            entity=subscription_entity,
        )

        # Technical premium should be converted to GBP
        assert breakdown.currency == "GBP"
        assert breakdown.technical_premium_local != breakdown.technical_premium_usd

        # Subscription line allocation happens in layers
        assert len(breakdown.layers) >= 1
        assert breakdown.layers[0].signed_line == 0.10
        # Commission applied
        assert breakdown.commission.brokerage > 0
        assert breakdown.commission.total_commission > 0
        # Taxes applied
        assert breakdown.taxes.total_taxes > 0
        # Gross calculated
        assert breakdown.gross_premium > 0

    def test_minimum_premium_enforcement(self, fx_converter, direct_entity, minimal_config):
        """Very small premium should be raised to minimum_gross_premium."""
        assembler = PremiumAssembler(fx_converter)
        breakdown = assembler.assemble(
            technical_premium_usd=100.0,  # Very small
            submission_data={"limit": 250_000, "deductible": 10_000},
            config=minimal_config,
            entity=direct_entity,
        )

        # Gross should be at least the minimum (2500)
        assert breakdown.gross_premium >= 2500

    def test_premium_breakdown_chain(self, fx_converter, direct_entity, minimal_config):
        """Verify the premium chain: technical → net → commission → taxes → gross."""
        assembler = PremiumAssembler(fx_converter)
        breakdown = assembler.assemble(
            technical_premium_usd=50_000.0,
            submission_data={"limit": 5_000_000, "deductible": 25_000},
            config=minimal_config,
            entity=direct_entity,
        )

        # Net premium = technical (for direct writer with 100% line)
        assert breakdown.net_premium == breakdown.technical_premium_local
        # Gross >= net + commission + taxes
        expected_gross = (
            breakdown.net_premium
            + breakdown.commission.total_commission
            + breakdown.taxes.total_taxes
        )
        assert abs(breakdown.gross_premium - expected_gross) < 1.0


class TestPremiumBreakdown:
    """Tests for PremiumBreakdown dataclass."""

    def test_breakdown_fields_present(self):
        breakdown = PremiumBreakdown(
            technical_premium_usd=100_000.0,
            technical_premium_local=80_000.0,
            net_premium=80_000.0,
            commission=CommissionBreakdown(
                brokerage=16_000.0,
                overrider=0.0,
                fronting_fee=0.0,
                total_commission=16_000.0,
            ),
            taxes=TaxBreakdown(
                insurance_premium_tax=11_520.0,
                stamp_duty=0.0,
                regulatory_levy=960.0,
                fire_service_levy=0.0,
                total_taxes=12_480.0,
            ),
            gross_premium=108_480.0,
            currency="GBP",
        )
        assert breakdown.gross_premium == 108_480.0
        assert breakdown.commission.brokerage == 16_000.0
        assert breakdown.taxes.insurance_premium_tax == 11_520.0
