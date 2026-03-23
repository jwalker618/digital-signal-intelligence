"""
Unit Tests for ROL Validator (Phase C — C1)

Tests the ROL appetite band matching, single validation, and batch validation.
"""

import pytest
from layers.risk.rol_validator import (
    ROLValidator,
    ROLAppetiteBand,
    ROLValidationResult,
    ROLBatchResult,
    DEFAULT_ROL_APPETITE,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def validator():
    return ROLValidator()


@pytest.fixture
def custom_validator():
    """Validator with tight single-band appetite for testing."""
    return ROLValidator(appetite_bands=[
        ROLAppetiteBand(
            label="TEST",
            limit_min=0, limit_max=0,
            rol_floor=0.01, rol_ceiling=0.05,
            warning_floor=0.005, warning_ceiling=0.08,
        ),
    ])


# =============================================================================
# BAND MATCHING
# =============================================================================

class TestBandMatching:

    def test_micro_band(self, validator):
        band = validator.get_band(1_000_000)
        assert band is not None
        assert band.label == "MICRO"

    def test_small_band(self, validator):
        band = validator.get_band(5_000_000)
        assert band is not None
        assert band.label == "SMALL"

    def test_medium_band(self, validator):
        band = validator.get_band(25_000_000)
        assert band is not None
        assert band.label == "MEDIUM"

    def test_large_band(self, validator):
        band = validator.get_band(100_000_000)
        assert band is not None
        assert band.label == "LARGE"

    def test_jumbo_band(self, validator):
        band = validator.get_band(500_000_000)
        assert band is not None
        assert band.label == "JUMBO"

    def test_mega_band(self, validator):
        band = validator.get_band(2_000_000_000)
        assert band is not None
        assert band.label == "MEGA"

    def test_ground_up_default_attachment(self, validator):
        """Default attachment=0 matches all ground-up bands."""
        for limit in [1_000_000, 5_000_000, 100_000_000]:
            band = validator.get_band(limit, attachment=0)
            assert band is not None


# =============================================================================
# SINGLE VALIDATION
# =============================================================================

class TestSingleValidation:

    def test_within_appetite(self, validator):
        """ROL within appetite → OK."""
        result = validator.validate_rol(premium=50_000, limit=1_000_000)
        assert result.within_appetite
        assert result.severity == "OK"
        assert result.rol == 0.05

    def test_above_appetite_within_warning(self, custom_validator):
        """ROL above ceiling but within warning → WARNING."""
        # ROL = 0.06, ceiling = 0.05, warning_ceiling = 0.08
        result = custom_validator.validate_rol(premium=60_000, limit=1_000_000)
        assert not result.within_appetite
        assert result.within_warning
        assert result.severity == "WARNING"

    def test_above_warning_ceiling(self, custom_validator):
        """ROL above warning ceiling → FAIL."""
        # ROL = 0.10
        result = custom_validator.validate_rol(premium=100_000, limit=1_000_000)
        assert not result.within_appetite
        assert not result.within_warning
        assert result.severity == "FAIL"

    def test_below_appetite_within_warning(self, custom_validator):
        """ROL below floor but within warning floor → WARNING."""
        # ROL = 0.008, floor = 0.01, warning_floor = 0.005
        result = custom_validator.validate_rol(premium=8_000, limit=1_000_000)
        assert not result.within_appetite
        assert result.within_warning
        assert result.severity == "WARNING"

    def test_below_warning_floor(self, custom_validator):
        """ROL below warning floor → FAIL."""
        # ROL = 0.001
        result = custom_validator.validate_rol(premium=1_000, limit=1_000_000)
        assert not result.within_appetite
        assert not result.within_warning
        assert result.severity == "FAIL"

    def test_zero_limit_fails(self, validator):
        result = validator.validate_rol(premium=1_000, limit=0)
        assert result.severity == "FAIL"
        assert "positive" in result.reason.lower()

    def test_rol_calculation(self, validator):
        result = validator.validate_rol(premium=250_000, limit=5_000_000)
        assert result.rol == pytest.approx(0.05)

    def test_attachment_parameter_accepted(self, validator):
        """Attachment parameter works (ground-up default=0)."""
        result = validator.validate_rol(premium=50_000, limit=5_000_000, attachment=0)
        assert result.severity in ("OK", "WARNING")


# =============================================================================
# BATCH VALIDATION
# =============================================================================

class TestBatchValidation:

    def test_batch_all_pass(self, validator):
        limit_premiums = {
            "1000000": 30_000,    # ROL 0.03
            "5000000": 150_000,   # ROL 0.03
            "10000000": 400_000,  # ROL 0.04
        }
        batch = validator.validate_limit_menu(limit_premiums)
        assert batch.all_passed or batch.fail_count == 0
        assert len(batch.results) == 3

    def test_batch_counts(self, custom_validator):
        limit_premiums = {
            "1000000": 30_000,    # ROL 0.03 → OK (within 0.01-0.05)
            "2000000": 200_000,   # ROL 0.10 → FAIL (above 0.08 warning)
        }
        batch = custom_validator.validate_limit_menu(limit_premiums)
        assert batch.ok_count == 1
        assert batch.fail_count == 1
        assert not batch.all_passed

    def test_batch_pass_rate(self, validator):
        limit_premiums = {
            "1000000": 30_000,
            "5000000": 150_000,
        }
        batch = validator.validate_limit_menu(limit_premiums)
        assert batch.pass_rate >= 0.0
        assert batch.pass_rate <= 1.0

    def test_empty_menu(self, validator):
        batch = validator.validate_limit_menu({})
        assert batch.all_passed
        assert len(batch.results) == 0


# =============================================================================
# DEFAULT APPETITE BANDS
# =============================================================================

class TestDefaultAppetite:

    def test_bands_cover_all_sizes(self):
        """Default bands cover micro through mega without gaps."""
        limits = [500_000, 5_000_000, 25_000_000, 100_000_000, 500_000_000, 2_000_000_000]
        validator = ROLValidator()
        for limit in limits:
            band = validator.get_band(limit)
            assert band is not None, f"No band for limit={limit:,}"

    def test_bands_are_monotonic(self):
        """Ceiling increases or stays constant as limit cohort grows."""
        prev_ceiling = 0.0
        for band in DEFAULT_ROL_APPETITE:
            assert band.rol_ceiling >= prev_ceiling, (
                f"{band.label} ceiling {band.rol_ceiling} < previous {prev_ceiling}"
            )
            prev_ceiling = band.rol_ceiling
