"""
Tests for Traditional Pricing Modifiers (Phase 7)

Tests the optional traditional pricing modifiers:
- LossHistoryModifier
- ExposureModifier
- ExternalRatingModifier

Key test scenarios:
- Missing data returns neutral (factor=1.0)
- Streamlined mode for STP
- Full mode with rich data
- Cap and floor constraints
"""

import pytest
from datetime import date

from layers.risk.modifiers import (
    TraditionalModifier,
    TraditionalModifierResult,
    LossHistoryInput,
    PolicyYear,
    Claim,
    ExposureInput,
    LossHistoryModifier,
    ExposureModifier,
    ExternalRatingModifier,
)
from signal_architecture.signals.types import InferenceContext


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def inference_context():
    """Basic inference context for tests."""
    return InferenceContext(
        configuration={},
        coverage="aerospace",
        config_name="aerospace_general",
    )


@pytest.fixture
def loss_history_modifier():
    """Default loss history modifier."""
    return LossHistoryModifier(
        full_credibility_premium=500_000,
        years_required=3,
        cap_factor=1.50,
        floor_factor=0.75,
    )


@pytest.fixture
def exposure_modifier():
    """Default exposure modifier."""
    return ExposureModifier(
        size_curve="iso_curve_2",
        growth_threshold=0.20,
    )


@pytest.fixture
def external_rating_modifier():
    """Enabled external rating modifier."""
    return ExternalRatingModifier(enabled=True)


# =============================================================================
# LOSS HISTORY MODIFIER TESTS
# =============================================================================

class TestLossHistoryModifier:
    """Tests for LossHistoryModifier."""

    def test_no_data_returns_neutral(self, loss_history_modifier, inference_context):
        """When no loss history, should return factor=1.0."""
        result = loss_history_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data={},
            context=inference_context,
        )

        assert result.factor == 1.0
        assert result.skipped is True
        assert result.confidence == 0.0
        assert "No loss history" in result.notes[0]

    def test_good_loss_history_gives_credit(self, loss_history_modifier, inference_context):
        """Good loss history (low loss ratio) should give credit."""
        submission_data = {
            "loss_history": {
                "policy_years": [
                    {"year": 2023, "premium": 200_000, "incurred_losses": 50_000},
                    {"year": 2022, "premium": 180_000, "incurred_losses": 40_000},
                    {"year": 2021, "premium": 170_000, "incurred_losses": 30_000},
                ],
            }
        }

        result = loss_history_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor < 1.0  # Credit
        assert result.skipped is False
        assert result.confidence > 0.5  # Reasonable credibility

    def test_poor_loss_history_gives_loading(self, loss_history_modifier, inference_context):
        """Poor loss history (high loss ratio) should give loading."""
        submission_data = {
            "loss_history": {
                "policy_years": [
                    {"year": 2023, "premium": 200_000, "incurred_losses": 300_000},
                    {"year": 2022, "premium": 180_000, "incurred_losses": 250_000},
                    {"year": 2021, "premium": 170_000, "incurred_losses": 200_000},
                ],
            }
        }

        result = loss_history_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor > 1.0  # Loading
        assert result.skipped is False

    def test_cap_is_applied(self, loss_history_modifier, inference_context):
        """Very poor loss history should be capped."""
        submission_data = {
            "loss_history": {
                "policy_years": [
                    {"year": 2023, "premium": 500_000, "incurred_losses": 2_000_000},
                    {"year": 2022, "premium": 500_000, "incurred_losses": 1_500_000},
                    {"year": 2021, "premium": 500_000, "incurred_losses": 1_000_000},
                ],
            }
        }

        result = loss_history_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor == 1.50  # Capped at max
        assert "capped" in str(result.notes).lower()

    def test_floor_is_applied(self, loss_history_modifier, inference_context):
        """Very good loss history should have floor applied."""
        submission_data = {
            "loss_history": {
                "policy_years": [
                    {"year": 2023, "premium": 500_000, "incurred_losses": 0},
                    {"year": 2022, "premium": 500_000, "incurred_losses": 0},
                    {"year": 2021, "premium": 500_000, "incurred_losses": 0},
                ],
            }
        }

        result = loss_history_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor == 0.75  # Floor applied

    def test_disabled_modifier_returns_neutral(self, inference_context):
        """Disabled modifier should return neutral."""
        modifier = LossHistoryModifier(enabled=False)

        result = modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data={"loss_history": {"policy_years": [{"year": 2023, "premium": 100000, "incurred_losses": 50000}]}},
            context=inference_context,
        )

        assert result.factor == 1.0
        assert "disabled" in result.notes[0].lower()


# =============================================================================
# EXPOSURE MODIFIER TESTS
# =============================================================================

class TestExposureModifier:
    """Tests for ExposureModifier."""

    def test_no_data_returns_neutral(self, exposure_modifier, inference_context):
        """When no exposure data, should return factor=1.0."""
        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data={},
            context=inference_context,
        )

        assert result.factor == 1.0
        assert result.skipped is True

    def test_streamlined_mode_with_tiv_only(self, exposure_modifier, inference_context):
        """Streamlined mode with only TIV should work."""
        submission_data = {
            "tiv": 50_000_000,
        }

        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.skipped is False
        assert result.confidence == 0.70  # Streamlined confidence
        assert "Streamlined" in str(result.notes)

    def test_streamlined_mode_with_revenue_only(self, exposure_modifier, inference_context):
        """Streamlined mode with only revenue should work."""
        submission_data = {
            "revenue": 10_000_000,
        }

        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.skipped is False
        assert result.confidence == 0.70

    def test_full_mode_with_rich_data(self, exposure_modifier, inference_context):
        """Full mode with multiple metrics."""
        submission_data = {
            "tiv": 50_000_000,
            "revenue": 25_000_000,
            "employee_count": 500,
            "locations_count": 3,
            "prior_year_revenue": 22_000_000,
        }

        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.skipped is False
        assert result.confidence > 0.70  # Higher than streamlined
        assert "Full" in str(result.notes)

    def test_small_exposure_gets_loading(self, exposure_modifier, inference_context):
        """Small exposures should get higher relativity."""
        submission_data = {"tiv": 500_000}  # Small

        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor > 1.0  # Loading for small risk

    def test_large_exposure_gets_credit(self, exposure_modifier, inference_context):
        """Large exposures should get lower relativity."""
        submission_data = {"tiv": 500_000_000}  # Large

        result = exposure_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor < 1.0  # Credit for large risk


# =============================================================================
# EXTERNAL RATING MODIFIER TESTS
# =============================================================================

class TestExternalRatingModifier:
    """Tests for ExternalRatingModifier."""

    def test_disabled_by_default(self, inference_context):
        """External rating modifier should be disabled by default."""
        modifier = ExternalRatingModifier()  # Default: enabled=False

        result = modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data={"credit_score": 750},
            context=inference_context,
        )

        assert result.factor == 1.0
        assert result.skipped is True
        assert "disabled" in result.notes[0].lower()

    def test_no_data_returns_neutral(self, external_rating_modifier, inference_context):
        """When no rating data, should return neutral."""
        result = external_rating_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data={},
            context=inference_context,
        )

        assert result.factor == 1.0
        assert result.skipped is True

    def test_good_credit_score_gives_credit(self, external_rating_modifier, inference_context):
        """High credit score should give credit."""
        submission_data = {"credit_score": 780}

        result = external_rating_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor < 1.0  # Credit

    def test_poor_credit_score_gives_loading(self, external_rating_modifier, inference_context):
        """Low credit score should give loading."""
        submission_data = {"credit_score": 550}

        result = external_rating_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor > 1.0  # Loading

    def test_financial_strength_rating(self, external_rating_modifier, inference_context):
        """FSR rating should affect factor."""
        submission_data = {"fsr": "A++"}

        result = external_rating_modifier.calculate(
            entity_id="test_entity",
            coverage="aerospace",
            submission_data=submission_data,
            context=inference_context,
        )

        assert result.factor < 1.0  # Credit for A++


# =============================================================================
# INPUT TYPE TESTS
# =============================================================================

class TestExposureInput:
    """Tests for ExposureInput dataclass."""

    def test_has_minimal_data_with_tiv(self):
        """TIV alone should enable streamlined mode."""
        exposure = ExposureInput(tiv=1_000_000)
        assert exposure.has_minimal_data is True
        assert exposure.mode == "streamlined"

    def test_has_minimal_data_with_revenue(self):
        """Revenue alone should enable streamlined mode."""
        exposure = ExposureInput(revenue=5_000_000)
        assert exposure.has_minimal_data is True
        assert exposure.mode == "streamlined"

    def test_no_data_mode_none(self):
        """No data should result in mode='none'."""
        exposure = ExposureInput()
        assert exposure.has_minimal_data is False
        assert exposure.mode == "none"

    def test_full_mode_with_multiple_fields(self):
        """Multiple fields should enable full mode."""
        exposure = ExposureInput(
            tiv=10_000_000,
            employee_count=100,
            payroll=5_000_000,
        )
        assert exposure.mode == "full"

    def test_from_submission_extracts_data(self):
        """from_submission should extract exposure data."""
        submission = {
            "tiv": 50_000_000,
            "revenue": 25_000_000,
            "employees": 500,
        }
        exposure = ExposureInput.from_submission(submission)

        assert exposure.tiv == 50_000_000
        assert exposure.revenue == 25_000_000
        assert exposure.employee_count == 500


class TestLossHistoryInput:
    """Tests for LossHistoryInput dataclass."""

    def test_has_data_with_policy_years(self):
        """Policy years should indicate data is available."""
        loss_input = LossHistoryInput(
            policy_years=[PolicyYear(year=2023, premium=100_000, incurred_losses=50_000, paid_losses=40_000)]
        )
        assert loss_input.has_data is True

    def test_no_data_without_policy_years(self):
        """Empty policy years should indicate no data."""
        loss_input = LossHistoryInput()
        assert loss_input.has_data is False

    def test_overall_loss_ratio_calculation(self):
        """Overall loss ratio should be calculated correctly."""
        loss_input = LossHistoryInput(
            policy_years=[
                PolicyYear(year=2023, premium=100_000, incurred_losses=50_000, paid_losses=40_000),
                PolicyYear(year=2022, premium=100_000, incurred_losses=50_000, paid_losses=40_000),
            ]
        )
        assert loss_input.overall_loss_ratio == 0.5  # 100k / 200k


class TestTraditionalModifierResult:
    """Tests for TraditionalModifierResult dataclass."""

    def test_has_impact_true_when_factor_differs(self):
        """has_impact should be True when factor != 1.0."""
        result = TraditionalModifierResult(
            modifier_type="test",
            factor=1.15,
            confidence=0.8,
        )
        assert result.has_impact is True

    def test_has_impact_false_when_neutral(self):
        """has_impact should be False when factor == 1.0."""
        result = TraditionalModifierResult(
            modifier_type="test",
            factor=1.0,
            confidence=0.8,
        )
        assert result.has_impact is False

    def test_has_impact_false_when_skipped(self):
        """has_impact should be False when skipped."""
        result = TraditionalModifierResult(
            modifier_type="test",
            factor=1.15,  # Non-neutral factor
            confidence=0.0,
            skipped=True,
        )
        assert result.has_impact is False

    def test_neutral_factory(self):
        """neutral() should create a skipped result."""
        result = TraditionalModifierResult.neutral("test", "No data")
        assert result.factor == 1.0
        assert result.skipped is True
        assert result.confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
