"""
Unit tests for QueryEvaluator.

Tests direct query evaluation (Step 7 of the workflow).
"""

import pytest
from unittest.mock import MagicMock

from layers.risk.query_evaluator import QueryEvaluator
from layers.risk.types import (
    QueryEvaluationResult,
    TriggeredCondition,
    ConditionAction,
)
from infrastructure.models.config_schema import (
    CoverageConfig,
    ConfigMetadata,
    Groups,
    RiskTierBands,
    RiskTierBand,
    RiskTierInterpretation,
    RiskTierApplication,
    TierBandRange,
    TierAction,
    PricingMethod,
    Pricing,
    ProductTypePricing,
    ILFCurve,
    DeductibleFactor,
    Guardrails,
    DirectQuery,
    QueryCondition,
    ScoreConditionAction,
)


# =============================================================================
# HELPERS
# =============================================================================

def _minimal_config(direct_queries=None):
    """Build a minimal CoverageConfig with specified direct queries."""
    if direct_queries is None:
        direct_queries = []

    return CoverageConfig(
        coverage_id="aerospace",
        config_id="aerospace_general",
        metadata=ConfigMetadata(
            name="Test",
            version="1.0.0",
            product_types=["liability"],
        ),
        signal_registry=[],
        groups=Groups(),
        risk_tier_bands=RiskTierBands(bands=[
            RiskTierBand(
                id=1, label="T1", description="Tier 1",
                interpretation=RiskTierInterpretation(
                    bands=TierBandRange(min=0, max=1000),
                    action=TierAction.APPROVE,
                    application=RiskTierApplication(method=PricingMethod.PREMIUM_BASE, value=25000),
                ),
            ),
        ]),
        direct_queries=direct_queries,
        pricing=Pricing(
            base_limit_reference=1000000,
            base_deductible_reference=25000,
            by_product_type={
                "liability": ProductTypePricing(
                    ilf_curve=ILFCurve(anchor_limit=1000000, curve="power", params={"alpha": 0.569}),
                    deductible_factors=[DeductibleFactor(deductible=25000, factor=1.0)],
                ),
            },
        ),
        guardrails=Guardrails(),
    )


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def evaluator():
    """Create a QueryEvaluator instance."""
    return QueryEvaluator()


@pytest.fixture
def sample_config():
    """Create a sample config with direct queries."""
    return _minimal_config(direct_queries=[
        DirectQuery(
            id="pending_claims",
            question="Are there any pending claims exceeding $1M?",
            query_condition=[
                QueryCondition(
                    return_value=True,
                    action=ScoreConditionAction.REFER,
                    note="Pending claims require review",
                ),
            ],
        ),
        DirectQuery(
            id="regulatory_action",
            question="Is there any pending regulatory enforcement?",
            query_condition=[
                QueryCondition(
                    return_value=True,
                    action=ScoreConditionAction.REFER,
                    override=5,
                    note="Regulatory enforcement pending",
                ),
            ],
        ),
        DirectQuery(
            id="wet_lease",
            question="Do you operate under wet lease arrangements?",
            query_condition=[
                QueryCondition(
                    return_value=True,
                    action=ScoreConditionAction.MODIFIER,
                    applied=1.15,
                ),
            ],
        ),
        DirectQuery(
            id="safety_certified",
            question="Does the operator hold IOSA certification?",
            query_condition=[
                QueryCondition(
                    return_value=True,
                    action=ScoreConditionAction.MODIFIER,
                    applied=0.90,
                ),
                QueryCondition(
                    return_value=False,
                    action=ScoreConditionAction.REFER,
                    override=4,
                    note="Not IOSA certified",
                ),
            ],
        ),
    ])


# =============================================================================
# BASIC EVALUATION TESTS
# =============================================================================

class TestQueryEvaluation:
    """Tests for basic query evaluation."""

    def test_evaluate_queries_returns_result(self, evaluator, sample_config):
        """Should return QueryEvaluationResult."""
        responses = {"pending_claims": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert isinstance(result, QueryEvaluationResult)

    def test_evaluate_queries_tracks_evaluated(self, evaluator, sample_config):
        """Should track triggered conditions."""
        responses = {
            "pending_claims": True,
            "regulatory_action": True,
            "wet_lease": True,
            "safety_certified": True,
        }
        result = evaluator.evaluate_queries(responses, sample_config)

        # All True: pending_claims (refer), regulatory_action (refer+override),
        # wet_lease (modifier), safety_certified (modifier)
        assert len(result.conditions_triggered) == 4

    def test_evaluate_queries_skips_missing_responses(self, evaluator, sample_config):
        """Should skip queries without responses."""
        responses = {"pending_claims": True}  # Only 1 of 4 queries answered
        result = evaluator.evaluate_queries(responses, sample_config)

        # Only pending_claims should trigger
        assert len(result.conditions_triggered) == 1


# =============================================================================
# TIER OVERRIDE TESTS
# =============================================================================

class TestTierOverrides:
    """Tests for tier override impacts."""

    def test_trigger_tier_override_on_true(self, evaluator, sample_config):
        """Should trigger tier override when response is True."""
        responses = {"regulatory_action": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert 5 in result.tier_overrides

    def test_no_tier_override_on_false(self, evaluator, sample_config):
        """Should not trigger tier override when response is False."""
        responses = {"regulatory_action": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert 5 not in result.tier_overrides

    def test_tier_override_on_false_trigger(self, evaluator, sample_config):
        """Should trigger tier override when return_value=False and response is False."""
        responses = {"safety_certified": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert 4 in result.tier_overrides


# =============================================================================
# REFERRAL TESTS
# =============================================================================

class TestReferrals:
    """Tests for referral impacts."""

    def test_trigger_referral(self, evaluator, sample_config):
        """Should trigger referral when condition met."""
        responses = {"pending_claims": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert "Pending claims require review" in result.referrals

    def test_no_referral_when_false(self, evaluator, sample_config):
        """Should not trigger referral when response is False."""
        responses = {"pending_claims": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.referrals) == 0

    def test_multiple_referrals(self, evaluator, sample_config):
        """Should accumulate multiple referrals."""
        responses = {"pending_claims": True, "regulatory_action": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.referrals) == 2


# =============================================================================
# NOTE TESTS
# =============================================================================

class TestNotes:
    """Tests for note impacts."""

    def test_trigger_note(self, evaluator, sample_config):
        """Should add note from regulatory enforcement."""
        responses = {"regulatory_action": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        # REFER action with note - note goes to referrals not notes
        assert "Regulatory enforcement pending" in result.referrals

    def test_no_note_when_false(self, evaluator, sample_config):
        """Should not trigger note when response is False."""
        responses = {"regulatory_action": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.notes) == 0
        assert len(result.referrals) == 0


# =============================================================================
# MODIFIER TESTS
# =============================================================================

class TestModifiers:
    """Tests for modifier impacts."""

    def test_trigger_modifier(self, evaluator, sample_config):
        """Should trigger modifier when condition met."""
        responses = {"wet_lease": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.modifiers) == 1
        modifier = result.modifiers[0]
        assert modifier["factor"] == 1.15
        assert modifier["source"] == "direct_query"

    def test_modifier_name_format(self, evaluator, sample_config):
        """Modifier should include query question."""
        responses = {"wet_lease": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        modifier = result.modifiers[0]
        assert modifier["source_id"] == "wet_lease"

    def test_multiple_modifiers(self, evaluator, sample_config):
        """Should accumulate multiple modifiers."""
        responses = {"wet_lease": True, "safety_certified": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.modifiers) == 2
        factors = [m["factor"] for m in result.modifiers]
        assert 1.15 in factors
        assert 0.90 in factors


# =============================================================================
# MULTIPLE IMPACTS PER QUERY TESTS
# =============================================================================

class TestMultipleImpacts:
    """Tests for queries with multiple impacts."""

    def test_query_with_multiple_impacts(self, evaluator, sample_config):
        """Single query can trigger multiple impacts."""
        responses = {"regulatory_action": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        # regulatory_action has REFER with override=5
        assert 5 in result.tier_overrides
        assert len(result.referrals) > 0

    def test_query_with_different_trigger_conditions(self, evaluator, sample_config):
        """Query can have conditions with different return_value."""
        # safety_certified: modifier triggers on True, tier_override triggers on False
        responses = {"safety_certified": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        # Should get modifier but not tier override
        assert len(result.modifiers) == 1
        assert 4 not in result.tier_overrides

        # Now test False response
        responses = {"safety_certified": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        # Should get tier override but not modifier
        assert 4 in result.tier_overrides
        assert len(result.modifiers) == 0


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_responses(self, evaluator, sample_config):
        """Should handle empty responses dict."""
        result = evaluator.evaluate_queries({}, sample_config)

        assert len(result.tier_overrides) == 0
        assert len(result.referrals) == 0
        assert len(result.notes) == 0
        assert len(result.modifiers) == 0

    def test_config_with_no_queries(self, evaluator):
        """Should handle config with no direct queries."""
        config = _minimal_config(direct_queries=[])

        result = evaluator.evaluate_queries({"some_query": True}, config)

        assert len(result.conditions_triggered) == 0
