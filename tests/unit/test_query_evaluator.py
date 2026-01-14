"""
Unit tests for QueryEvaluator.

Tests direct query evaluation (Step 7 of the workflow).
"""

import pytest

from layers.risk.query_evaluator import QueryEvaluator
from layers.risk.types import (
    CoverageConfig,
    DirectQueryConfig,
    DirectQueryImpact,
    QueryEvaluationResult,
    TierConfig,
    ConditionAction,
    DecisionType,
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
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="test-hash",
        required_inputs=["entity_id"],
        signal_groups=[],
        direct_queries=[
            DirectQueryConfig(
                id="pending_claims",
                question="Are there any pending claims exceeding $1M?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.REFERRAL,
                        value="Pending claims require review",
                        trigger_on=True
                    )
                ]
            ),
            DirectQueryConfig(
                id="regulatory_action",
                question="Is there any pending regulatory enforcement?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.TIER_OVERRIDE,
                        value=5,
                        trigger_on=True
                    ),
                    DirectQueryImpact(
                        impact_type=ConditionAction.NOTE,
                        value="Regulatory enforcement pending",
                        trigger_on=True
                    )
                ]
            ),
            DirectQueryConfig(
                id="wet_lease",
                question="Do you operate under wet lease arrangements?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.MODIFIER,
                        value=1.15,
                        trigger_on=True
                    )
                ]
            ),
            DirectQueryConfig(
                id="safety_certified",
                question="Does the operator hold IOSA certification?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.MODIFIER,
                        value=0.90,
                        trigger_on=True
                    ),
                    DirectQueryImpact(
                        impact_type=ConditionAction.TIER_OVERRIDE,
                        value=4,
                        trigger_on=False  # Trigger when NOT certified
                    )
                ]
            )
        ],
        categorical_groups=[],
        categorical_features={},
        tier_thresholds=[
            TierConfig(tier=1, min_score=800, max_score=1000, base_premium=25000, decision=DecisionType.APPROVE),
            TierConfig(tier=5, min_score=0, max_score=199, base_premium=100000, decision=DecisionType.DECLINE),
        ],
        limit_bands=[],
        deductible_credits={},
        metadata={}
    )


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
        """Should track all evaluated queries."""
        responses = {
            "pending_claims": False,
            "regulatory_action": False,
            "wet_lease": True
        }
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.queries_evaluated) == 4  # All 4 queries evaluated
        evaluated_ids = [q["id"] for q in result.queries_evaluated]
        assert "pending_claims" in evaluated_ids
        assert "regulatory_action" in evaluated_ids
        assert "wet_lease" in evaluated_ids
        assert "safety_certified" in evaluated_ids

    def test_evaluate_queries_skips_missing_responses(self, evaluator, sample_config):
        """Should skip queries without responses."""
        responses = {"pending_claims": False}  # Missing other queries
        result = evaluator.evaluate_queries(responses, sample_config)

        skipped = [q for q in result.queries_evaluated if q.get("skipped")]
        assert len(skipped) == 3  # 3 queries skipped


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

        # regulatory_action triggers on True, so False should not trigger
        query_overrides = [5]  # The override value from regulatory_action
        assert 5 not in result.tier_overrides

    def test_tier_override_on_false_trigger(self, evaluator, sample_config):
        """Should trigger tier override when trigger_on=False and response is False."""
        responses = {"safety_certified": False}  # trigger_on=False for tier override
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
        # Add another query with referral
        sample_config.direct_queries.append(
            DirectQueryConfig(
                id="bankruptcy",
                question="Has the entity filed for bankruptcy?",
                impacts=[
                    DirectQueryImpact(
                        impact_type=ConditionAction.REFERRAL,
                        value="Bankruptcy history",
                        trigger_on=True
                    )
                ]
            )
        )

        responses = {"pending_claims": True, "bankruptcy": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.referrals) == 2


# =============================================================================
# NOTE TESTS
# =============================================================================

class TestNotes:
    """Tests for note impacts."""

    def test_trigger_note(self, evaluator, sample_config):
        """Should trigger note when condition met."""
        responses = {"regulatory_action": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert "Regulatory enforcement pending" in result.notes

    def test_no_note_when_false(self, evaluator, sample_config):
        """Should not trigger note when response is False."""
        responses = {"regulatory_action": False}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.notes) == 0


# =============================================================================
# MODIFIER TESTS
# =============================================================================

class TestModifiers:
    """Tests for modifier impacts (unique to direct queries)."""

    def test_trigger_modifier(self, evaluator, sample_config):
        """Should trigger modifier when condition met."""
        responses = {"wet_lease": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        assert len(result.modifiers) == 1
        modifier = result.modifiers[0]
        assert modifier["factor"] == 1.15
        assert modifier["source"] == "direct_query"
        assert modifier["query_id"] == "wet_lease"

    def test_modifier_name_format(self, evaluator, sample_config):
        """Modifier name should follow query_{id} format."""
        responses = {"wet_lease": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        modifier = result.modifiers[0]
        assert modifier["name"] == "query_wet_lease"

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

        # regulatory_action has tier_override and note
        assert 5 in result.tier_overrides
        assert "Regulatory enforcement pending" in result.notes

    def test_query_with_different_trigger_conditions(self, evaluator, sample_config):
        """Query can have impacts with different trigger_on values."""
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
# VALIDATION TESTS
# =============================================================================

class TestResponseValidation:
    """Tests for response validation."""

    def test_validate_valid_responses(self, evaluator, sample_config):
        """Should pass validation for valid responses."""
        responses = {
            "pending_claims": True,
            "regulatory_action": False
        }

        is_valid, errors = evaluator.validate_responses(responses, sample_config)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_unknown_query_id(self, evaluator, sample_config):
        """Should fail for unknown query IDs."""
        responses = {
            "unknown_query": True
        }

        is_valid, errors = evaluator.validate_responses(responses, sample_config)

        assert is_valid is False
        assert any("Unknown query ID" in e for e in errors)

    def test_validate_non_boolean_response(self, evaluator, sample_config):
        """Should fail for non-boolean responses."""
        responses = {
            "pending_claims": "yes"  # String instead of bool
        }

        is_valid, errors = evaluator.validate_responses(responses, sample_config)

        assert is_valid is False
        assert any("must be boolean" in e for e in errors)


# =============================================================================
# REQUIRED QUERIES TESTS
# =============================================================================

class TestRequiredQueries:
    """Tests for getting required queries."""

    def test_get_required_queries(self, evaluator, sample_config):
        """Should return list of query definitions."""
        queries = evaluator.get_required_queries(sample_config)

        assert isinstance(queries, list)
        assert len(queries) == 4

        query = queries[0]
        assert "id" in query
        assert "question" in query


# =============================================================================
# IMPACT SUMMARY TESTS
# =============================================================================

class TestImpactSummary:
    """Tests for impact summarization."""

    def test_summarize_impacts(self, evaluator, sample_config):
        """Should summarize impacts correctly."""
        responses = {
            "pending_claims": True,
            "regulatory_action": True,
            "wet_lease": True,
            "safety_certified": True
        }
        result = evaluator.evaluate_queries(responses, sample_config)

        summary = evaluator.summarize_impacts(result)

        assert summary["total_queries"] == 4
        assert summary["queries_with_impacts"] == 4
        assert summary["tier_overrides"] == 1  # regulatory_action only
        assert summary["referrals"] == 1  # pending_claims only
        assert summary["notes"] == 1  # regulatory_action only
        assert summary["modifiers"] == 2  # wet_lease + safety_certified

    def test_calculate_modifier_total(self, evaluator, sample_config):
        """Should calculate combined modifier factor."""
        responses = {"wet_lease": True, "safety_certified": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        summary = evaluator.summarize_impacts(result)

        # 1.15 * 0.90 = 1.035
        expected = 1.15 * 0.90
        assert abs(summary["modifier_total"] - expected) < 0.001

    def test_modifier_total_no_modifiers(self, evaluator, sample_config):
        """Modifier total should be 1.0 when no modifiers."""
        responses = {"pending_claims": True}
        result = evaluator.evaluate_queries(responses, sample_config)

        summary = evaluator.summarize_impacts(result)

        assert summary["modifier_total"] == 1.0


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
        empty_config = CoverageConfig(
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
            deductible_credits={},
            metadata={}
        )

        result = evaluator.evaluate_queries({"some_query": True}, empty_config)

        assert len(result.queries_evaluated) == 0

    def test_query_with_no_impacts(self, evaluator):
        """Should handle query with no impacts defined."""
        config = CoverageConfig(
            coverage="test",
            configuration="test",
            version="1.0.0",
            config_hash="hash",
            required_inputs=[],
            signal_groups=[],
            direct_queries=[
                DirectQueryConfig(
                    id="informational",
                    question="Is this for informational purposes only?",
                    impacts=[]  # No impacts
                )
            ],
            categorical_groups=[],
            categorical_features={},
            tier_thresholds=[
                TierConfig(tier=1, min_score=0, max_score=1000, base_premium=10000, decision=DecisionType.APPROVE)
            ],
            limit_bands=[],
            deductible_credits={},
            metadata={}
        )

        result = evaluator.evaluate_queries({"informational": True}, config)

        # Query should be evaluated but no impacts triggered
        assert len(result.queries_evaluated) == 1
        assert len(result.tier_overrides) == 0
        assert len(result.referrals) == 0
        assert len(result.notes) == 0
        assert len(result.modifiers) == 0
