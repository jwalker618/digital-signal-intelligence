"""Tests for deductible factor interpolation in config_schema."""

import pytest
from infrastructure.models.config_schema import ProductTypePricing, DeductibleFactor, ILFCurve


@pytest.fixture
def pricing():
    """ProductTypePricing with standard deductible factors."""
    return ProductTypePricing(
        ilf_curve=ILFCurve(
            anchor_limit=1_000_000,
            curve="power",
            params={"exponent": 0.5},
        ),
        deductible_factors=[
            DeductibleFactor(deductible=10_000, factor=1.25),
            DeductibleFactor(deductible=25_000, factor=1.15),
            DeductibleFactor(deductible=50_000, factor=1.00),
            DeductibleFactor(deductible=100_000, factor=0.90),
            DeductibleFactor(deductible=250_000, factor=0.80),
            DeductibleFactor(deductible=500_000, factor=0.70),
            DeductibleFactor(deductible=1_000_000, factor=0.60),
        ],
    )


class TestDeductibleInterpolation:
    """Tests for log-linear deductible factor interpolation."""

    def test_exact_match(self, pricing):
        """Exact deductible should return exact factor."""
        assert pricing.get_deductible_factor(50_000) == 1.00
        assert pricing.get_deductible_factor(100_000) == 0.90
        assert pricing.get_deductible_factor(10_000) == 1.25

    def test_interpolation_between_points(self, pricing):
        """Deductible between reference points should interpolate."""
        # 75k is between 50k (1.00) and 100k (0.90)
        factor = pricing.get_deductible_factor(75_000)
        assert 0.90 < factor < 1.00

    def test_interpolation_monotonic(self, pricing):
        """Higher deductible should produce lower factor (more credit)."""
        f_30k = pricing.get_deductible_factor(30_000)
        f_40k = pricing.get_deductible_factor(40_000)
        f_75k = pricing.get_deductible_factor(75_000)
        assert f_30k > f_40k > f_75k

    def test_below_minimum_clamps(self, pricing):
        """Deductible below minimum reference should clamp to lowest factor."""
        factor = pricing.get_deductible_factor(5_000)
        assert factor == 1.25  # Same as 10k (lowest reference)

    def test_above_maximum_clamps(self, pricing):
        """Deductible above maximum reference should clamp to highest factor."""
        factor = pricing.get_deductible_factor(2_000_000)
        assert factor == 0.60  # Same as 1M (highest reference)

    def test_no_deductible_factors_returns_one(self):
        """Empty deductible_factors should return 1.0."""
        pricing = ProductTypePricing(
            ilf_curve=ILFCurve(anchor_limit=1_000_000, curve="power", params={"exponent": 0.5}),
            deductible_factors=[],
        )
        assert pricing.get_deductible_factor(50_000) == 1.0

    def test_single_factor_exact_match(self):
        """Single reference point should handle exact match."""
        pricing = ProductTypePricing(
            ilf_curve=ILFCurve(anchor_limit=1_000_000, curve="power", params={"exponent": 0.5}),
            deductible_factors=[DeductibleFactor(deductible=50_000, factor=1.0)],
        )
        assert pricing.get_deductible_factor(50_000) == 1.0

    def test_single_factor_clamps(self):
        """Single reference point: below and above should clamp."""
        pricing = ProductTypePricing(
            ilf_curve=ILFCurve(anchor_limit=1_000_000, curve="power", params={"exponent": 0.5}),
            deductible_factors=[DeductibleFactor(deductible=50_000, factor=1.0)],
        )
        assert pricing.get_deductible_factor(10_000) == 1.0
        assert pricing.get_deductible_factor(500_000) == 1.0

    def test_interpolation_is_log_linear(self, pricing):
        """Verify log-linear behavior: midpoint of log scale should give geometric mean."""
        import math
        # Geometric midpoint of 50k and 100k deductibles
        geo_mid = int(math.sqrt(50_000 * 100_000))  # ~70710
        factor_at_mid = pricing.get_deductible_factor(geo_mid)
        # Should be close to geometric mean of factors (1.00, 0.90)
        expected = math.sqrt(1.00 * 0.90)  # ~0.9487
        assert abs(factor_at_mid - expected) < 0.01

    def test_calibration_harness_compatible(self, pricing):
        """Deductible factor at anchor should be 1.0 (standard convention)."""
        assert pricing.get_deductible_factor(50_000) == 1.00
