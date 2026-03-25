"""Tests for layers.risk.fx — FX conversion layer."""

import pytest
from layers.risk.fx import (
    Currency,
    FXContext,
    FXConverter,
    StaticRateProvider,
    MONETARY_FIELDS,
    get_fx_converter,
    set_fx_provider,
)


class TestStaticRateProvider:
    """Tests for the static (dev/test) rate provider."""

    def test_usd_to_usd_is_one(self):
        provider = StaticRateProvider()
        assert provider.get_rate(Currency.USD, Currency.USD) == 1.0

    def test_gbp_to_usd(self):
        provider = StaticRateProvider()
        rate = provider.get_rate(Currency.GBP, Currency.USD)
        assert rate > 1.0  # GBP is stronger than USD

    def test_usd_to_gbp(self):
        provider = StaticRateProvider()
        rate = provider.get_rate(Currency.USD, Currency.GBP)
        assert rate < 1.0  # Takes less GBP to make 1 USD

    def test_cross_rate_consistency(self):
        """GBP→USD and USD→GBP should be inverses."""
        provider = StaticRateProvider()
        gbp_to_usd = provider.get_rate(Currency.GBP, Currency.USD)
        usd_to_gbp = provider.get_rate(Currency.USD, Currency.GBP)
        assert abs(gbp_to_usd * usd_to_gbp - 1.0) < 0.0001

    def test_all_currencies_have_rates(self):
        """Every currency should have a rate to USD."""
        provider = StaticRateProvider()
        for currency in Currency:
            rate = provider.get_rate(currency, Currency.USD)
            assert rate > 0, f"{currency} has no rate to USD"


class TestFXConverter:
    """Tests for FX conversion logic."""

    @pytest.fixture
    def converter(self):
        return FXConverter(StaticRateProvider())

    def test_usd_to_usd_no_change(self, converter):
        """USD submission should pass through unchanged."""
        data = {"limit": 1_000_000, "deductible": 50_000, "revenue": 10_000_000}
        converted, ctx = converter.to_usd(data, Currency.USD)
        assert converted["limit"] == 1_000_000
        assert converted["deductible"] == 50_000
        assert ctx.rate == 1.0

    def test_gbp_to_usd_converts_monetary_fields(self, converter):
        """GBP monetary fields should be scaled by the GBP→USD rate."""
        data = {"limit": 1_000_000, "deductible": 50_000, "country": "GB"}
        converted, ctx = converter.to_usd(data, Currency.GBP)

        rate = ctx.rate
        assert rate > 1.0  # GBP→USD rate
        assert converted["limit"] == round(1_000_000 * rate, 2)
        assert converted["deductible"] == round(50_000 * rate, 2)
        # Non-monetary fields should be unchanged
        assert converted["country"] == "GB"

    def test_from_usd_reverses_conversion(self, converter):
        """from_usd should reverse a previous to_usd conversion."""
        data = {"limit": 1_000_000, "deductible": 50_000}
        _, ctx = converter.to_usd(data, Currency.GBP)

        # Convert a USD premium back to GBP
        usd_premium = 50_000.0
        gbp_premium = converter.from_usd(usd_premium, "GBP", fx_context=ctx)
        # Should be less than USD amount (GBP is stronger)
        assert gbp_premium < usd_premium

    def test_fx_context_audit_trail(self, converter):
        """FXContext should capture full audit trail."""
        data = {"limit": 1_000_000, "revenue": 5_000_000}
        _, ctx = converter.to_usd(data, Currency.EUR)

        assert ctx.source_currency == Currency.EUR
        assert ctx.target_currency == Currency.USD
        assert ctx.rate > 0
        assert "static" in ctx.rate_source
        assert "limit" in ctx.monetary_fields_converted
        assert "revenue" in ctx.monetary_fields_converted

    def test_monetary_fields_comprehensive(self):
        """All monetary fields should be in the MONETARY_FIELDS set."""
        expected = {
            "limit", "deductible", "revenue", "tiv", "hull_value",
            "total_assets", "aggregate_limit", "min_premium_override",
        }
        assert expected.issubset(MONETARY_FIELDS)

    def test_missing_monetary_fields_ignored(self, converter):
        """Fields not present in submission should not cause errors."""
        data = {"limit": 1_000_000}  # No deductible, revenue, etc.
        converted, ctx = converter.to_usd(data, Currency.JPY)
        assert "limit" in converted
        assert "deductible" not in converted


class TestModuleSingleton:
    """Tests for module-level singleton access."""

    def test_get_converter_returns_instance(self):
        converter = get_fx_converter()
        assert isinstance(converter, FXConverter)

    def test_set_provider_changes_behavior(self):
        """Setting a custom provider should affect conversion results."""
        original = get_fx_converter()
        # Set a new provider and verify it's used
        set_fx_provider(StaticRateProvider())
        new = get_fx_converter()
        assert isinstance(new, FXConverter)
