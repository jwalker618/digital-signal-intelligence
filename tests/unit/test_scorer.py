"""
Unit tests for ModelScorer.

Tests signal extraction, composite score calculation, and condition evaluation
(Steps 4-6 of the workflow).
"""

import pytest
from datetime import datetime
from typing import Any

from layers.risk.scorer import ModelScorer
from layers.risk.types import (
    CoverageConfig,
    SignalGroupConfig,
    SignalConfig,
    SignalCondition,
    TierConfig,
    ScoringResult,
    SignalOutput,
    ConditionAction,
    DecisionType,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_inference_registry():
    """Create mock inference functions for testing."""
    def mock_safety_signal(entity_id: str, context: dict) -> dict:
        return {"score": 85.0, "confidence": 0.95, "data_sources": ["faa"]}

    def mock_financial_signal(entity_id: str, context: dict) -> dict:
        return {"score": 70.0, "confidence": 0.90, "data_sources": ["credit_agency"]}

    def mock_poor_signal(entity_id: str, context: dict) -> dict:
        return {"score": 25.0, "confidence": 0.85, "data_sources": ["public_records"]}

    def mock_error_signal(entity_id: str, context: dict) -> dict:
        raise RuntimeError("Signal extraction failed")

    def mock_numeric_result(entity_id: str, context: dict) -> float:
        return 75.0

    return {
        "infer_safety_record": mock_safety_signal,
        "infer_financial_strength": mock_financial_signal,
        "infer_poor_indicator": mock_poor_signal,
        "infer_error_signal": mock_error_signal,
        "infer_numeric_result": mock_numeric_result,
    }


@pytest.fixture
def scorer(mock_inference_registry):
    """Create a ModelScorer with mock registry."""
    return ModelScorer(inference_registry=mock_inference_registry)


@pytest.fixture
def sample_config():
    """Create a sample coverage config for testing."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="test-hash",
        required_inputs=["entity_id"],
        signal_groups=[
            SignalGroupConfig(
                name="safety_signals",
                weight=0.6,
                signals=[
                    SignalConfig(
                        name="safety_record",
                        weight=0.6,
                        inference_function="infer_safety_record",
                        categorizer_type="threshold_bucket",
                        categorizer_params={},
                        conditions=[]
                    ),
                    SignalConfig(
                        name="financial_strength",
                        weight=0.4,
                        inference_function="infer_financial_strength",
                        categorizer_type="threshold_bucket",
                        categorizer_params={},
                        conditions=[]
                    )
                ],
                conditions=[]
            ),
            SignalGroupConfig(
                name="risk_signals",
                weight=0.4,
                signals=[
                    SignalConfig(
                        name="risk_indicator",
                        weight=1.0,
                        inference_function="infer_poor_indicator",
                        categorizer_type="threshold_bucket",
                        categorizer_params={},
                        conditions=[]
                    )
                ],
                conditions=[]
            )
        ],
        direct_queries=[],
        categorical_groups=[],
        categorical_features={},
        tier_thresholds=[
            TierConfig(tier=1, min_score=800, max_score=1000, base_premium=25000, decision=DecisionType.APPROVE),
            TierConfig(tier=2, min_score=600, max_score=799, base_premium=35000, decision=DecisionType.APPROVE),
            TierConfig(tier=3, min_score=400, max_score=599, base_premium=50000, decision=DecisionType.REFER),
            TierConfig(tier=4, min_score=200, max_score=399, base_premium=75000, decision=DecisionType.REFER),
            TierConfig(tier=5, min_score=0, max_score=199, base_premium=100000, decision=DecisionType.DECLINE),
        ],
        limit_bands=[],
        deductible_credits={},
        metadata={}
    )


@pytest.fixture
def config_with_conditions():
    """Create a config with signal conditions for testing."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="test-hash-conditions",
        required_inputs=["entity_id"],
        signal_groups=[
            SignalGroupConfig(
                name="safety_signals",
                weight=1.0,
                signals=[
                    SignalConfig(
                        name="safety_record",
                        weight=1.0,
                        inference_function="infer_poor_indicator",
                        categorizer_type="threshold_bucket",
                        categorizer_params={},
                        conditions=[
                            SignalCondition(
                                condition_type="threshold_below",
                                condition_value=30,
                                action=ConditionAction.TIER_OVERRIDE,
                                action_value=5
                            ),
                            SignalCondition(
                                condition_type="threshold_below",
                                condition_value=40,
                                action=ConditionAction.REFERRAL,
                                action_value="Low safety score"
                            ),
                            SignalCondition(
                                condition_type="threshold_below",
                                condition_value=50,
                                action=ConditionAction.NOTE,
                                action_value="Safety score below threshold"
                            )
                        ]
                    )
                ],
                conditions=[
                    SignalCondition(
                        condition_type="threshold_below",
                        condition_value=300,
                        action=ConditionAction.REFERRAL,
                        action_value="Group score below threshold"
                    )
                ]
            )
        ],
        direct_queries=[],
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
# SIGNAL EXTRACTION TESTS (Step 4)
# =============================================================================

class TestSignalExtraction:
    """Tests for Step 4: Signal extraction."""

    def test_extract_signals_returns_outputs(self, scorer, sample_config):
        """Should extract signals and return SignalOutput list."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        assert isinstance(outputs, list)
        assert len(outputs) == 3  # 2 safety + 1 risk
        assert all(isinstance(o, SignalOutput) for o in outputs)

    def test_extract_signals_populates_fields(self, scorer, sample_config):
        """Should populate all SignalOutput fields correctly."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        safety_output = next(o for o in outputs if o.signal_name == "safety_record")

        assert safety_output.signal_name == "safety_record"
        assert safety_output.group_name == "safety_signals"
        assert safety_output.raw_score == 85.0
        assert safety_output.confidence == 0.95
        assert safety_output.signal_weight == 0.6
        assert safety_output.group_weight == 0.6
        assert "faa" in safety_output.data_sources

    def test_extract_signals_calculates_weighted_score(self, scorer, sample_config):
        """Should calculate weighted score correctly."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        safety_output = next(o for o in outputs if o.signal_name == "safety_record")

        # weighted_score = raw_score * signal_weight * group_weight * 10
        # = 85.0 * 0.6 * 0.6 * 10 = 306.0
        expected = 85.0 * 0.6 * 0.6 * 10
        assert abs(safety_output.weighted_score - expected) < 0.01

    def test_extract_signals_handles_missing_function(self, scorer, sample_config):
        """Should handle missing inference function gracefully."""
        # Modify config to reference non-existent function
        sample_config.signal_groups[0].signals[0].inference_function = "nonexistent_function"

        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        failed_output = next(o for o in outputs if o.signal_name == "safety_record")
        assert failed_output.raw_score == 0.0
        assert failed_output.confidence == 0.0
        assert len(failed_output.conditions_triggered) > 0

    def test_extract_signals_handles_function_error(self, scorer, sample_config):
        """Should handle inference function errors gracefully."""
        sample_config.signal_groups[0].signals[0].inference_function = "infer_error_signal"

        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        failed_output = next(o for o in outputs if o.signal_name == "safety_record")
        assert failed_output.raw_score == 0.0
        assert failed_output.confidence == 0.0

    def test_extract_signals_handles_numeric_result(self, scorer, sample_config):
        """Should handle plain numeric inference results."""
        sample_config.signal_groups[0].signals[0].inference_function = "infer_numeric_result"

        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        output = next(o for o in outputs if o.signal_name == "safety_record")
        assert output.raw_score == 75.0
        assert output.confidence == 1.0

    def test_extract_signals_parallel_mode(self, scorer, sample_config):
        """Should work in parallel extraction mode."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={},
            parallel=True
        )

        assert len(outputs) == 3

    def test_extract_signals_sequential_mode(self, scorer, sample_config):
        """Should work in sequential extraction mode."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            submission_data={},
            parallel=False
        )

        assert len(outputs) == 3


# =============================================================================
# COMPOSITE SCORE TESTS (Step 5)
# =============================================================================

class TestCompositeScore:
    """Tests for Step 5: Composite score calculation."""

    def test_calculate_composite_returns_tuple(self, scorer, sample_config):
        """Should return (score, group_scores, confidence) tuple."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config
        )

        result = scorer.calculate_composite(outputs, sample_config)

        assert isinstance(result, tuple)
        assert len(result) == 3
        composite, group_scores, confidence = result
        assert isinstance(composite, float)
        assert isinstance(group_scores, dict)
        assert isinstance(confidence, float)

    def test_calculate_composite_score_range(self, scorer, sample_config):
        """Composite score should be in 0-1000 range."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config
        )

        composite, _, _ = scorer.calculate_composite(outputs, sample_config)

        assert 0 <= composite <= 1000

    def test_calculate_composite_group_scores(self, scorer, sample_config):
        """Should calculate group scores correctly."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config
        )

        _, group_scores, _ = scorer.calculate_composite(outputs, sample_config)

        assert "safety_signals" in group_scores
        assert "risk_signals" in group_scores
        assert group_scores["safety_signals"] > 0
        assert group_scores["risk_signals"] > 0

    def test_calculate_composite_confidence(self, scorer, sample_config):
        """Should calculate aggregate confidence correctly."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config
        )

        _, _, confidence = scorer.calculate_composite(outputs, sample_config)

        assert 0 <= confidence <= 1.0

    def test_calculate_composite_empty_outputs(self, scorer, sample_config):
        """Should handle empty signal outputs."""
        composite, group_scores, confidence = scorer.calculate_composite([], sample_config)

        assert composite == 0.0
        assert confidence == 0.0


# =============================================================================
# CONDITION EVALUATION TESTS (Step 6)
# =============================================================================

class TestConditionEvaluation:
    """Tests for Step 6: Signal conditions evaluation."""

    def test_evaluate_conditions_returns_tuple(self, scorer, config_with_conditions):
        """Should return tuple of (conditions, tier_overrides, referrals, notes, modifiers)."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=config_with_conditions
        )
        _, group_scores, _ = scorer.calculate_composite(outputs, config_with_conditions)

        result = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions
        )

        assert isinstance(result, tuple)
        assert len(result) == 5
        conditions, tier_overrides, referrals, notes, modifiers = result
        assert isinstance(conditions, list)
        assert isinstance(tier_overrides, list)
        assert isinstance(referrals, list)
        assert isinstance(notes, list)
        assert isinstance(modifiers, list)

    def test_evaluate_conditions_triggers_tier_override(self, scorer, config_with_conditions):
        """Should trigger tier override when condition met."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=config_with_conditions
        )
        _, group_scores, _ = scorer.calculate_composite(outputs, config_with_conditions)

        _, tier_overrides, _, _, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions
        )

        # Poor signal returns score of 25, which is below 30 threshold
        assert 5 in tier_overrides

    def test_evaluate_conditions_triggers_referral(self, scorer, config_with_conditions):
        """Should trigger referral when condition met."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=config_with_conditions
        )
        _, group_scores, _ = scorer.calculate_composite(outputs, config_with_conditions)

        _, _, referrals, _, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions
        )

        # Score of 25 is below 40 threshold
        assert "Low safety score" in referrals

    def test_evaluate_conditions_triggers_note(self, scorer, config_with_conditions):
        """Should trigger note when condition met."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=config_with_conditions
        )
        _, group_scores, _ = scorer.calculate_composite(outputs, config_with_conditions)

        _, _, _, notes, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions
        )

        # Score of 25 is below 50 threshold
        assert "Safety score below threshold" in notes

    def test_evaluate_group_level_conditions(self, scorer, config_with_conditions):
        """Should evaluate group-level conditions."""
        outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=config_with_conditions
        )
        _, group_scores, _ = scorer.calculate_composite(outputs, config_with_conditions)

        _, _, referrals, _, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions
        )

        # Group score will be low (25 * 1.0 * 1.0 * 10 = 250), below 300 threshold
        assert "Group score below threshold" in referrals


# =============================================================================
# FULL SCORING PIPELINE TESTS
# =============================================================================

class TestFullScoringPipeline:
    """Tests for complete score_entity method."""

    def test_score_entity_returns_result(self, scorer, sample_config):
        """Should return complete ScoringResult."""
        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config,
            submission_data={}
        )

        assert isinstance(result, ScoringResult)
        assert result.entity_id == "test-entity"
        assert result.coverage == "aerospace"

    def test_score_entity_populates_all_fields(self, scorer, sample_config):
        """Should populate all ScoringResult fields."""
        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config
        )

        assert len(result.signal_outputs) == 3
        assert 0 <= result.pure_composite_score <= 1000
        assert 0 <= result.aggregate_confidence <= 1.0
        assert "safety_signals" in result.group_scores
        assert result.duration_ms > 0

    def test_score_entity_with_conditions(self, scorer, config_with_conditions):
        """Should capture triggered conditions."""
        result = scorer.score_entity(
            entity_id="test-entity",
            config=config_with_conditions
        )

        assert len(result.signal_conditions_triggered) > 0
        assert len(result.tier_overrides_from_signals) > 0
        assert len(result.referrals_from_signals) > 0


# =============================================================================
# CONDITION TYPE TESTS
# =============================================================================

class TestConditionTypes:
    """Tests for different condition type evaluations."""

    def test_threshold_below_condition(self, scorer):
        """Should evaluate threshold_below condition correctly."""
        condition = SignalCondition(
            condition_type="threshold_below",
            condition_value=50,
            action=ConditionAction.NOTE,
            action_value="Below threshold"
        )

        assert scorer._evaluate_condition(condition, 40) is True
        assert scorer._evaluate_condition(condition, 50) is False
        assert scorer._evaluate_condition(condition, 60) is False

    def test_threshold_above_condition(self, scorer):
        """Should evaluate threshold_above condition correctly."""
        condition = SignalCondition(
            condition_type="threshold_above",
            condition_value=50,
            action=ConditionAction.NOTE,
            action_value="Above threshold"
        )

        assert scorer._evaluate_condition(condition, 60) is True
        assert scorer._evaluate_condition(condition, 50) is False
        assert scorer._evaluate_condition(condition, 40) is False

    def test_equals_condition(self, scorer):
        """Should evaluate equals condition correctly."""
        condition = SignalCondition(
            condition_type="equals",
            condition_value=50,
            action=ConditionAction.NOTE,
            action_value="Equals value"
        )

        assert scorer._evaluate_condition(condition, 50) is True
        assert scorer._evaluate_condition(condition, 50.0001) is True  # Within tolerance
        assert scorer._evaluate_condition(condition, 51) is False

    def test_in_range_condition(self, scorer):
        """Should evaluate in_range condition correctly."""
        condition = SignalCondition(
            condition_type="in_range",
            condition_value=[40, 60],
            action=ConditionAction.NOTE,
            action_value="In range"
        )

        assert scorer._evaluate_condition(condition, 50) is True
        assert scorer._evaluate_condition(condition, 40) is True
        assert scorer._evaluate_condition(condition, 60) is True
        assert scorer._evaluate_condition(condition, 39) is False
        assert scorer._evaluate_condition(condition, 61) is False

    def test_not_in_range_condition(self, scorer):
        """Should evaluate not_in_range condition correctly."""
        condition = SignalCondition(
            condition_type="not_in_range",
            condition_value=[40, 60],
            action=ConditionAction.NOTE,
            action_value="Not in range"
        )

        assert scorer._evaluate_condition(condition, 50) is False
        assert scorer._evaluate_condition(condition, 30) is True
        assert scorer._evaluate_condition(condition, 70) is True

    def test_in_list_condition(self, scorer):
        """Should evaluate in_list condition correctly."""
        condition = SignalCondition(
            condition_type="in_list",
            condition_value=[25, 50, 75],
            action=ConditionAction.NOTE,
            action_value="In list"
        )

        assert scorer._evaluate_condition(condition, 50) is True
        assert scorer._evaluate_condition(condition, 60) is False


# =============================================================================
# SIGNAL BREAKDOWN TESTS
# =============================================================================

class TestSignalBreakdown:
    """Tests for signal breakdown utility method."""

    def test_get_signal_breakdown(self, scorer, sample_config):
        """Should return detailed breakdown dict."""
        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config
        )

        breakdown = scorer.get_signal_breakdown(result)

        assert isinstance(breakdown, dict)
        assert breakdown["entity_id"] == "test-entity"
        assert breakdown["coverage"] == "aerospace"
        assert "composite_score" in breakdown
        assert "groups" in breakdown
        assert "safety_signals" in breakdown["groups"]

    def test_breakdown_includes_signal_details(self, scorer, sample_config):
        """Breakdown should include individual signal details."""
        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config
        )

        breakdown = scorer.get_signal_breakdown(result)

        safety_group = breakdown["groups"]["safety_signals"]
        assert "signals" in safety_group
        assert len(safety_group["signals"]) == 2

        signal = safety_group["signals"][0]
        assert "name" in signal
        assert "raw_score" in signal
        assert "confidence" in signal
        assert "weight" in signal
