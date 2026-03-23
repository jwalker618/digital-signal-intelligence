"""
Unit tests for ModelScorer.

Tests signal extraction, composite score calculation, and condition evaluation
(Steps 4-6 of the workflow).
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from layers.risk.scorer import ModelScorer
from layers.risk.types import (
    SignalOutput,
    CategoricalOutput,
    ScoringResult,
    TriggeredCondition,
    ConditionAction,
    utcnow,
)

from infrastructure.models.config_schema import (
    CoverageConfig,
    ConfigMetadata,
    Groups,
    ThreeLayerAssessmentGroup,
    GroupDimension,
    SignalDefinition,
    ThreeLayerAssessment,
    DimensionBlock,
    CorrelationDirection,
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
    ScoreCondition,
    ComparisonOperator,
    ScoreConditionAction,
)

from signal_architecture.signals.types import InferenceContext


# =============================================================================
# HELPERS
# =============================================================================

def _make_tier_band(
    tier_id, label, min_score, max_score, action,
    method=PricingMethod.PREMIUM_BASE, value=None,
):
    return RiskTierBand(
        id=tier_id,
        label=label,
        description=f"Tier {tier_id}",
        interpretation=RiskTierInterpretation(
            bands=TierBandRange(min=min_score, max=max_score),
            action=action,
            application=RiskTierApplication(method=method, value=value),
        ),
    )


def _base_config(
    signal_defs=None,
    groups_tla=None,
    tiers=None,
    pricing=None,
):
    """Build a minimal valid CoverageConfig for testing."""
    if signal_defs is None:
        signal_defs = [
            SignalDefinition(
                id="safety_record",
                inference_utility_function="infer_safety_record",
                three_layer_assessment=ThreeLayerAssessment(
                    group_id="safety_signals",
                    risk=DimensionBlock(weight=0.6),
                ),
            ),
            SignalDefinition(
                id="financial_strength",
                inference_utility_function="infer_financial_strength",
                three_layer_assessment=ThreeLayerAssessment(
                    group_id="safety_signals",
                    risk=DimensionBlock(weight=0.4),
                ),
            ),
            SignalDefinition(
                id="risk_indicator",
                inference_utility_function="infer_risk_indicator",
                three_layer_assessment=ThreeLayerAssessment(
                    group_id="risk_signals",
                    risk=DimensionBlock(weight=1.0),
                ),
            ),
        ]

    if groups_tla is None:
        groups_tla = [
            ThreeLayerAssessmentGroup(
                id="safety_signals",
                label="Safety Signals",
                risk=GroupDimension(weight=0.6),
            ),
            ThreeLayerAssessmentGroup(
                id="risk_signals",
                label="Risk Signals",
                risk=GroupDimension(weight=0.4),
            ),
        ]

    if tiers is None:
        tiers = RiskTierBands(bands=[
            _make_tier_band(1, "PREFERRED", 800, 1000, TierAction.APPROVE, value=25000),
            _make_tier_band(2, "STANDARD", 600, 799, TierAction.APPROVE, value=35000),
            _make_tier_band(3, "MODERATE", 400, 599, TierAction.REFER, value=50000),
            _make_tier_band(4, "HIGH", 200, 399, TierAction.REFER, value=75000),
            _make_tier_band(5, "DECLINE", 0, 199, TierAction.DECLINE, value=100000),
        ])

    if pricing is None:
        pricing = Pricing(
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
                    ],
                ),
            },
        )

    return CoverageConfig(
        coverage_id="aerospace",
        config_id="aerospace_general",
        metadata=ConfigMetadata(
            name="Aerospace Test",
            version="1.0.0",
            product_types=["liability"],
        ),
        signal_registry=signal_defs,
        groups=Groups(three_layer_assessment=groups_tla),
        risk_tier_bands=tiers,
        pricing=pricing,
        guardrails=Guardrails(),
    )


def _make_signal_output(
    signal_id, group_id, raw_score, confidence=0.95, weight=1.0,
):
    """Create a SignalOutput for testing."""
    return SignalOutput(
        signal_id=signal_id,
        signal_name=signal_id.replace("_", " ").title(),
        group_id=group_id,
        raw_score=raw_score,
        confidence=confidence,
        weight=weight,
        weighted_score=raw_score * weight,
        data_sources=["test_source"],
        extracted_at=utcnow(),
    )


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def scorer():
    """Create a ModelScorer."""
    return ModelScorer()


@pytest.fixture
def sample_config():
    """Create a sample coverage config for testing."""
    return _base_config()


@pytest.fixture
def sample_signal_outputs():
    """Pre-built signal outputs for testing composite/conditions."""
    return [
        _make_signal_output("safety_record", "safety_signals", 85.0, 0.95, 0.6),
        _make_signal_output("financial_strength", "safety_signals", 70.0, 0.90, 0.4),
        _make_signal_output("risk_indicator", "risk_signals", 25.0, 0.85, 1.0),
    ]


@pytest.fixture
def config_with_conditions():
    """Create a config with signal conditions for testing."""
    signal_defs = [
        SignalDefinition(
            id="safety_record",
            inference_utility_function="infer_safety_record",
            three_layer_assessment=ThreeLayerAssessment(
                group_id="safety_signals",
                risk=DimensionBlock(
                    weight=1.0,
                    score_conditions=[
                        ScoreCondition(
                            threshold=30,
                            comparison=ComparisonOperator.LT,
                            action=ScoreConditionAction.REFER,
                            note="Low safety score requires referral",
                        ),
                        ScoreCondition(
                            threshold=50,
                            comparison=ComparisonOperator.LT,
                            action=ScoreConditionAction.FLAG,
                            note="Safety score below threshold",
                        ),
                    ],
                ),
            ),
        ),
    ]

    groups_tla = [
        ThreeLayerAssessmentGroup(
            id="safety_signals",
            label="Safety Signals",
            risk=GroupDimension(
                weight=1.0,
                score_conditions=[
                    ScoreCondition(
                        threshold=50,
                        comparison=ComparisonOperator.LT,
                        action=ScoreConditionAction.REFER,
                        note="Group score below threshold",
                    ),
                ],
            ),
        ),
    ]

    return _base_config(signal_defs=signal_defs, groups_tla=groups_tla)


# =============================================================================
# COMPOSITE SCORE TESTS (Step 5)
# =============================================================================

class TestCompositeScore:
    """Tests for Step 5: Composite score calculation."""

    def test_calculate_composite_returns_tuple(self, scorer, sample_config, sample_signal_outputs):
        """Should return (score, group_scores, confidence, coverage) tuple."""
        result = scorer.calculate_composite(sample_signal_outputs, sample_config)

        assert isinstance(result, tuple)
        assert len(result) == 4
        composite, group_scores, confidence, coverage = result
        assert isinstance(composite, float)
        assert isinstance(group_scores, dict)
        assert isinstance(confidence, float)
        assert isinstance(coverage, float)

    def test_calculate_composite_score_range(self, scorer, sample_config, sample_signal_outputs):
        """Composite score should be in 0-1000 range."""
        composite, _, _, _ = scorer.calculate_composite(sample_signal_outputs, sample_config)
        assert 0 <= composite <= 1000

    def test_calculate_composite_group_scores(self, scorer, sample_config, sample_signal_outputs):
        """Should calculate group scores correctly."""
        _, group_scores, _, _ = scorer.calculate_composite(sample_signal_outputs, sample_config)

        assert "safety_signals" in group_scores
        assert "risk_signals" in group_scores
        assert group_scores["safety_signals"]["risk_score"] > 0
        assert group_scores["risk_signals"]["risk_score"] > 0

    def test_calculate_composite_confidence(self, scorer, sample_config, sample_signal_outputs):
        """Should calculate aggregate confidence correctly."""
        _, _, confidence, _ = scorer.calculate_composite(sample_signal_outputs, sample_config)
        assert 0 <= confidence <= 1.0

    def test_calculate_composite_empty_outputs(self, scorer, sample_config):
        """Should handle empty signal outputs."""
        composite, group_scores, confidence, coverage = scorer.calculate_composite([], sample_config)

        # With no signals, groups still exist but use default score
        assert isinstance(composite, float)

    def test_group_risk_weights_affect_score(self, scorer, sample_signal_outputs):
        """Different group risk weights should change composite score."""
        config_equal = _base_config(groups_tla=[
            ThreeLayerAssessmentGroup(id="safety_signals", risk=GroupDimension(weight=0.5)),
            ThreeLayerAssessmentGroup(id="risk_signals", risk=GroupDimension(weight=0.5)),
        ])

        config_safety_heavy = _base_config(groups_tla=[
            ThreeLayerAssessmentGroup(id="safety_signals", risk=GroupDimension(weight=0.9)),
            ThreeLayerAssessmentGroup(id="risk_signals", risk=GroupDimension(weight=0.1)),
        ])

        score_equal, _, _, _ = scorer.calculate_composite(sample_signal_outputs, config_equal)
        score_heavy, _, _, _ = scorer.calculate_composite(sample_signal_outputs, config_safety_heavy)

        # Safety signals have higher raw scores, so weighting them more should increase composite
        assert score_heavy > score_equal


# =============================================================================
# CONDITION EVALUATION TESTS (Step 6)
# =============================================================================

class TestConditionEvaluation:
    """Tests for Step 6: Signal conditions evaluation."""

    def test_evaluate_conditions_returns_tuple(self, scorer, config_with_conditions):
        """Should return tuple of (conditions, tier_overrides, referrals, notes, modifiers)."""
        outputs = [_make_signal_output("safety_record", "safety_signals", 25.0)]
        _, group_scores, _, _ = scorer.calculate_composite(outputs, config_with_conditions)

        result = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions,
        )

        assert isinstance(result, tuple)
        assert len(result) == 5
        conditions, tier_overrides, referrals, notes, modifiers = result
        assert isinstance(conditions, list)
        assert isinstance(tier_overrides, list)
        assert isinstance(referrals, list)
        assert isinstance(notes, list)
        assert isinstance(modifiers, list)

    def test_evaluate_conditions_triggers_referral(self, scorer, config_with_conditions):
        """Should trigger referral when condition met."""
        outputs = [_make_signal_output("safety_record", "safety_signals", 25.0)]
        _, group_scores, _, _ = scorer.calculate_composite(outputs, config_with_conditions)

        conditions, _, referrals, _, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions,
        )

        # Score 25 is < 30 threshold (signal-level) and < 50 (group-level)
        assert len(referrals) > 0

    def test_evaluate_conditions_triggers_flag(self, scorer, config_with_conditions):
        """Should trigger flag note when condition met."""
        outputs = [_make_signal_output("safety_record", "safety_signals", 40.0)]
        _, group_scores, _, _ = scorer.calculate_composite(outputs, config_with_conditions)

        conditions, _, _, notes, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions,
        )

        # Score 40 is < 50 threshold but >= 30 (only flag, not referral at signal level)
        assert len(conditions) > 0

    def test_no_conditions_for_good_score(self, scorer, config_with_conditions):
        """Should not trigger conditions when score is above thresholds."""
        outputs = [_make_signal_output("safety_record", "safety_signals", 80.0)]
        _, group_scores, _, _ = scorer.calculate_composite(outputs, config_with_conditions)

        conditions, _, referrals, _, _ = scorer.evaluate_signal_conditions(
            signal_outputs=outputs,
            group_scores=group_scores,
            config=config_with_conditions,
        )

        # Score 80 is above all thresholds — no signal or group conditions should trigger
        assert len(conditions) == 0
        assert len(referrals) == 0


# =============================================================================
# EXTRACT SIGNALS TESTS (Step 4) - with mocked inference
# =============================================================================

class TestSignalExtraction:
    """Tests for Step 4: Signal extraction with mocked inference."""

    @patch("layers.risk.scorer.get_inference_function")
    def test_extract_signals_returns_outputs(self, mock_get_fn, scorer, sample_config):
        """Should extract signals and return (signal_outputs, categorical_outputs)."""
        def mock_inference(entity_id, context):
            from signal_architecture.signals.types import SignalResult
            return SignalResult(signal_id="test", score=85.0, confidence=0.95, metadata={"extractor": "test"})

        mock_get_fn.return_value = mock_inference

        context = InferenceContext(configuration={}, coverage="aerospace", config_name="aerospace_general")
        signal_outputs, categorical_outputs = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            context=context,
        )

        assert isinstance(signal_outputs, list)
        assert len(signal_outputs) == 3  # 2 safety + 1 risk
        assert all(isinstance(o, SignalOutput) for o in signal_outputs)

    @patch("layers.risk.scorer.get_inference_function")
    def test_extract_signals_populates_fields(self, mock_get_fn, scorer, sample_config):
        """Should populate SignalOutput fields correctly."""
        def mock_inference(entity_id, context):
            from signal_architecture.signals.types import SignalResult
            return SignalResult(signal_id="test", score=85.0, confidence=0.95, metadata={"extractor": "faa"})

        mock_get_fn.return_value = mock_inference

        context = InferenceContext(configuration={}, coverage="aerospace", config_name="aerospace_general")
        signal_outputs, _ = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            context=context,
        )

        safety_output = next(o for o in signal_outputs if o.signal_id == "safety_record")

        assert safety_output.signal_id == "safety_record"
        assert safety_output.group_id == "safety_signals"
        assert safety_output.raw_score == 85.0
        assert safety_output.confidence == 0.95

    @patch("layers.risk.scorer.get_inference_function")
    def test_extract_signals_handles_function_error(self, mock_get_fn, scorer, sample_config):
        """Should handle inference function errors gracefully."""
        def mock_inference(entity_id, context):
            raise RuntimeError("Signal extraction failed")

        mock_get_fn.return_value = mock_inference

        context = InferenceContext(configuration={}, coverage="aerospace", config_name="aerospace_general")
        signal_outputs, _ = scorer.extract_signals(
            entity_id="test-entity",
            config=sample_config,
            context=context,
        )

        # Errors should be caught and output should have error markers
        for o in signal_outputs:
            assert o.error is not None or o.raw_score == scorer.default_score


# =============================================================================
# FULL SCORING PIPELINE TESTS
# =============================================================================

class TestFullScoringPipeline:
    """Tests for complete score_entity method."""

    @patch("layers.risk.scorer.get_inference_function")
    def test_score_entity_returns_result(self, mock_get_fn, scorer, sample_config):
        """Should return complete ScoringResult."""
        def mock_inference(entity_id, context):
            from signal_architecture.signals.types import SignalResult
            return SignalResult(signal_id="test", score=85.0, confidence=0.95, metadata={"extractor": "test"})

        mock_get_fn.return_value = mock_inference

        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config,
        )

        assert isinstance(result, ScoringResult)

    @patch("layers.risk.scorer.get_inference_function")
    def test_score_entity_populates_all_fields(self, mock_get_fn, scorer, sample_config):
        """Should populate all ScoringResult fields."""
        def mock_inference(entity_id, context):
            from signal_architecture.signals.types import SignalResult
            return SignalResult(signal_id="test", score=85.0, confidence=0.95, metadata={"extractor": "test"})

        mock_get_fn.return_value = mock_inference

        result = scorer.score_entity(
            entity_id="test-entity",
            config=sample_config,
        )

        assert len(result.signal_outputs) == 3
        assert 0 <= result.pure_composite_score <= 1000
        assert 0 <= result.confidence <= 1.0
        assert "safety_signals" in result.group_scores

    @patch("layers.risk.scorer.get_inference_function")
    def test_score_entity_with_conditions(self, mock_get_fn, scorer, config_with_conditions):
        """Should capture triggered conditions."""
        def mock_inference(entity_id, context):
            from signal_architecture.signals.types import SignalResult
            return SignalResult(signal_id="test", score=25.0, confidence=0.85, metadata={"extractor": "test"})

        mock_get_fn.return_value = mock_inference

        result = scorer.score_entity(
            entity_id="test-entity",
            config=config_with_conditions,
        )

        # Score of 25 should trigger conditions
        assert len(result.conditions_triggered) > 0
        assert len(result.referrals) > 0
