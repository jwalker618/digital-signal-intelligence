"""
Phase B Tests — Scoring Completeness

B1: Loss/exposure score_conditions evaluation across all dimensions
B2: Exposure dimension breakdown (magnitude vs complexity)
B3: Loss field clarity (renamed combined fields + new per-dimension fields)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from infrastructure.models.config_schema import (
    CoverageConfig,
    ScoreCondition,
    ScoreConditionAction,
    ComparisonOperator,
    ThreeLayerAssessmentGroup,
    GroupDimension,
    Groups,
    SignalDefinition,
    ThreeLayerAssessment,
    DimensionBlock,
    LossDimension,
    ExposureDimension,
    CorrelationDirection,
)
from layers.risk.scorer import ModelScorer
from layers.risk.types import SignalOutput, ConditionAction
from layers.loss.types import (
    LossPropensityResult,
    LossPropensityBand,
    SeverityPropensityBand,
    TrendDirection,
    MonitoringConfig,
    DeteriorationAlert,
    MonitoringResult,
)
from layers.loss.scorer import LossCorrelationScorer
from layers.loss.monitoring import LossMonitoringEngine


# =============================================================================
# HELPERS
# =============================================================================

def _make_scorer():
    return ModelScorer(default_score=50.0)


def _make_signal_output(signal_id, raw_score=50.0, confidence=0.9, data_sources=None):
    return SignalOutput(
        signal_id=signal_id,
        signal_name=signal_id.replace("_", " ").title(),
        group_id="test_group",
        raw_score=raw_score,
        confidence=confidence,
        weighted_score=raw_score,
        weight=1.0,
        data_sources=data_sources or [],
    )


def _make_minimal_config(
    tla_groups=None,
    signal_registry=None,
):
    """Build a minimal CoverageConfig mock with Pydantic-compatible TLA groups."""
    config = MagicMock(spec=CoverageConfig)
    config.groups = MagicMock(spec=Groups)
    config.groups.three_layer_assessment = tla_groups or []
    config.signal_registry = signal_registry or []
    return config


def _make_loss_propensity_result(
    score=50.0,
    severity_score=40.0,
    band=LossPropensityBand.MODERATE,
    severity_band=SeverityPropensityBand.MODERATE,
    trend=TrendDirection.STABLE,
    combined_velocity=0.0,
    days_since=30,
    previous_combined=None,
    previous_frequency=None,
    previous_severity=None,
    freq_velocity=None,
    sev_velocity=None,
    calculated_at=None,
):
    """Helper to build a LossPropensityResult with sensible defaults."""
    return LossPropensityResult(
        loss_propensity_score=score,
        severity_propensity_score=severity_score,
        loss_propensity_band=band,
        severity_propensity_band=severity_band,
        loss_confidence=0.85,
        cohort_id="default",
        cohort_name="Default Cohort",
        cohort_confidence=0.9,
        group_scores={"tech": 50.0},
        group_confidences={"tech": 0.9},
        frequency_group_scores={"tech": 50.0},
        severity_group_scores={"tech": 40.0},
        frequency_multiplier=1.0,
        severity_multiplier=1.0,
        combined_loss_modifier=1.0,
        trend_direction=trend,
        combined_score_velocity=combined_velocity,
        days_since_last_assessment=days_since,
        previous_combined_score=previous_combined,
        referral_triggered=False,
        referral_reasons=[],
        flags=[],
        signal_results=[],
        calculated_at=calculated_at or datetime.utcnow(),
        config_version="1.0",
        previous_frequency_score=previous_frequency,
        previous_severity_score=previous_severity,
        frequency_score_velocity=freq_velocity,
        severity_score_velocity=sev_velocity,
    )


# =============================================================================
# B1 — GROUP-LEVEL SCORE_CONDITIONS ACROSS DIMENSIONS
# =============================================================================

class TestGroupLevelScoreConditions:
    """Test that score_conditions on loss and exposure group dimensions are evaluated."""

    def test_risk_dimension_condition_triggers(self):
        """Risk dimension score_conditions still work as before."""
        scorer = _make_scorer()
        group = ThreeLayerAssessmentGroup(
            id="infra",
            label="Infrastructure",
            risk=GroupDimension(
                weight=0.5,
                score_conditions=[
                    ScoreCondition(
                        threshold=30,
                        comparison=ComparisonOperator.LTE,
                        action=ScoreConditionAction.FLAG,
                        note="Risk score very low",
                    )
                ],
            ),
        )
        config = _make_minimal_config(tla_groups=[group])
        group_scores = {"infra": {"risk_score": 25.0}}

        conditions, _, _, notes, _ = scorer.evaluate_signal_conditions([], group_scores, config)

        assert len(conditions) == 1
        assert conditions[0].source_name == "Infrastructure (risk)"
        assert "Risk score very low" in notes

    def test_loss_dimension_condition_triggers(self):
        """Loss dimension score_conditions are now evaluated (B1 fix)."""
        scorer = _make_scorer()
        group = ThreeLayerAssessmentGroup(
            id="claims",
            label="Claims History",
            loss=GroupDimension(
                weight=0.6,
                score_conditions=[
                    ScoreCondition(
                        threshold=80,
                        comparison=ComparisonOperator.GTE,
                        action=ScoreConditionAction.REFER,
                        note="High loss propensity group",
                    )
                ],
            ),
        )
        config = _make_minimal_config(tla_groups=[group])
        group_scores = {"claims": {"risk_score": 85.0}}

        conditions, _, referrals, _, _ = scorer.evaluate_signal_conditions([], group_scores, config)

        assert len(conditions) == 1
        assert conditions[0].source_name == "Claims History (loss)"
        assert "High loss propensity group" in referrals

    def test_exposure_dimension_condition_triggers(self):
        """Exposure dimension score_conditions are now evaluated (B1 fix)."""
        scorer = _make_scorer()
        group = ThreeLayerAssessmentGroup(
            id="size_group",
            label="Size & Scale",
            exposure=GroupDimension(
                weight=0.4,
                score_conditions=[
                    ScoreCondition(
                        threshold=90,
                        comparison=ComparisonOperator.GTE,
                        action=ScoreConditionAction.MODIFIER,
                        applied=1.25,
                    )
                ],
            ),
        )
        config = _make_minimal_config(tla_groups=[group])
        group_scores = {"size_group": {"risk_score": 95.0}}

        conditions, _, _, _, modifiers = scorer.evaluate_signal_conditions([], group_scores, config)

        assert len(conditions) == 1
        assert conditions[0].source_name == "Size & Scale (exposure)"
        assert len(modifiers) == 1
        assert modifiers[0]["factor"] == 1.25

    def test_multiple_dimensions_on_same_group(self):
        """All three dimensions on one group can each trigger independently."""
        scorer = _make_scorer()
        group = ThreeLayerAssessmentGroup(
            id="multi",
            label="Multi-Dimension",
            risk=GroupDimension(
                weight=0.4,
                score_conditions=[
                    ScoreCondition(threshold=20, comparison=ComparisonOperator.LTE, action=ScoreConditionAction.FLAG, note="Low risk")
                ],
            ),
            loss=GroupDimension(
                weight=0.3,
                score_conditions=[
                    ScoreCondition(threshold=20, comparison=ComparisonOperator.LTE, action=ScoreConditionAction.FLAG, note="Low loss")
                ],
            ),
            exposure=GroupDimension(
                weight=0.3,
                score_conditions=[
                    ScoreCondition(threshold=20, comparison=ComparisonOperator.LTE, action=ScoreConditionAction.FLAG, note="Low exposure")
                ],
            ),
        )
        config = _make_minimal_config(tla_groups=[group])
        group_scores = {"multi": {"risk_score": 15.0}}

        conditions, _, _, notes, _ = scorer.evaluate_signal_conditions([], group_scores, config)

        assert len(conditions) == 3
        dimension_labels = {c.source_name for c in conditions}
        assert "Multi-Dimension (risk)" in dimension_labels
        assert "Multi-Dimension (loss)" in dimension_labels
        assert "Multi-Dimension (exposure)" in dimension_labels

    def test_no_conditions_no_alerts(self):
        """Groups without score_conditions produce no triggered conditions."""
        scorer = _make_scorer()
        group = ThreeLayerAssessmentGroup(
            id="clean",
            label="Clean Group",
            risk=GroupDimension(weight=1.0),
        )
        config = _make_minimal_config(tla_groups=[group])
        group_scores = {"clean": {"risk_score": 50.0}}

        conditions, overrides, referrals, notes, modifiers = scorer.evaluate_signal_conditions([], group_scores, config)

        assert len(conditions) == 0


# =============================================================================
# B1 — SIGNAL-LEVEL SCORE_CONDITIONS ACROSS DIMENSIONS
# =============================================================================

class TestSignalLevelScoreConditions:
    """Test that signal-level score_conditions on loss/exposure sub-dimensions are evaluated."""

    def test_loss_severity_signal_condition(self):
        """Signal-level loss.severity score_conditions are evaluated."""
        scorer = _make_scorer()
        signal = SignalDefinition(
            id="litigation_history",
            inference_utility_function="infer_litigation",
            three_layer_assessment=ThreeLayerAssessment(
                group_id="legal",
                loss=LossDimension(
                    severity=DimensionBlock(
                        weight=0.5,
                        correlation_direction=CorrelationDirection.POSITIVE,
                        score_conditions=[
                            ScoreCondition(
                                threshold=70,
                                comparison=ComparisonOperator.GTE,
                                action=ScoreConditionAction.FLAG,
                                note="High severity signal",
                            )
                        ],
                    ),
                ),
            ),
        )
        signal_output = _make_signal_output("litigation_history", raw_score=75.0)
        config = _make_minimal_config(signal_registry=[signal])

        conditions, _, _, notes, _ = scorer.evaluate_signal_conditions([signal_output], {}, config)

        assert len(conditions) == 1
        assert "loss_severity" in conditions[0].source_name
        assert "High severity signal" in notes

    def test_loss_frequency_signal_condition(self):
        """Signal-level loss.frequency score_conditions are evaluated."""
        scorer = _make_scorer()
        signal = SignalDefinition(
            id="claim_count",
            inference_utility_function="infer_claims",
            three_layer_assessment=ThreeLayerAssessment(
                group_id="claims",
                loss=LossDimension(
                    frequency=DimensionBlock(
                        weight=0.5,
                        correlation_direction=CorrelationDirection.POSITIVE,
                        score_conditions=[
                            ScoreCondition(
                                threshold=60,
                                comparison=ComparisonOperator.GTE,
                                action=ScoreConditionAction.REFER,
                                note="Frequent claimant",
                            )
                        ],
                    ),
                ),
            ),
        )
        signal_output = _make_signal_output("claim_count", raw_score=65.0)
        config = _make_minimal_config(signal_registry=[signal])

        conditions, _, referrals, _, _ = scorer.evaluate_signal_conditions([signal_output], {}, config)

        assert len(conditions) == 1
        assert "loss_frequency" in conditions[0].source_name
        assert "Frequent claimant" in referrals

    def test_exposure_size_signal_condition(self):
        """Signal-level exposure.size score_conditions are evaluated."""
        scorer = _make_scorer()
        signal = SignalDefinition(
            id="revenue",
            inference_utility_function="infer_revenue",
            three_layer_assessment=ThreeLayerAssessment(
                group_id="scale",
                exposure=ExposureDimension(
                    size=DimensionBlock(
                        weight=0.5,
                        correlation_direction=CorrelationDirection.POSITIVE,
                        score_conditions=[
                            ScoreCondition(
                                threshold=90,
                                comparison=ComparisonOperator.GTE,
                                action=ScoreConditionAction.MODIFIER,
                                applied=1.30,
                            )
                        ],
                    ),
                ),
            ),
        )
        signal_output = _make_signal_output("revenue", raw_score=95.0)
        config = _make_minimal_config(signal_registry=[signal])

        conditions, _, _, _, modifiers = scorer.evaluate_signal_conditions([signal_output], {}, config)

        assert len(conditions) == 1
        assert "exposure_size" in conditions[0].source_name
        assert modifiers[0]["factor"] == 1.30

    def test_exposure_complexity_signal_condition(self):
        """Signal-level exposure.complexity score_conditions are evaluated."""
        scorer = _make_scorer()
        signal = SignalDefinition(
            id="subsidiary_count",
            inference_utility_function="infer_subsidiaries",
            three_layer_assessment=ThreeLayerAssessment(
                group_id="scale",
                exposure=ExposureDimension(
                    complexity=DimensionBlock(
                        weight=0.5,
                        correlation_direction=CorrelationDirection.POSITIVE,
                        score_conditions=[
                            ScoreCondition(
                                threshold=80,
                                comparison=ComparisonOperator.GTE,
                                action=ScoreConditionAction.FLAG,
                                note="Complex entity structure",
                            )
                        ],
                    ),
                ),
            ),
        )
        signal_output = _make_signal_output("subsidiary_count", raw_score=85.0)
        config = _make_minimal_config(signal_registry=[signal])

        conditions, _, _, notes, _ = scorer.evaluate_signal_conditions([signal_output], {}, config)

        assert len(conditions) == 1
        assert "exposure_complexity" in conditions[0].source_name
        assert "Complex entity structure" in notes

    def test_signal_without_tla_is_skipped(self):
        """Signals without three_layer_assessment produce no conditions."""
        scorer = _make_scorer()
        signal = MagicMock(spec=SignalDefinition)
        signal.three_layer_assessment = None
        config = _make_minimal_config(signal_registry=[signal])

        conditions, _, _, _, _ = scorer.evaluate_signal_conditions([], {}, config)
        assert len(conditions) == 0


# =============================================================================
# B3 — LOSS FIELD CLARITY
# =============================================================================

class TestLossFieldClarity:
    """Test renamed combined fields and new per-dimension trend fields."""

    def test_combined_fields_exist(self):
        """LossPropensityResult has renamed combined fields."""
        result = _make_loss_propensity_result(
            combined_velocity=5.0,
            previous_combined=45.0,
        )
        assert result.combined_score_velocity == 5.0
        assert result.previous_combined_score == 45.0

    def test_individual_dimension_fields_default_none(self):
        """New per-dimension fields default to None."""
        result = _make_loss_propensity_result()
        assert result.previous_frequency_score is None
        assert result.previous_severity_score is None
        assert result.frequency_score_velocity is None
        assert result.severity_score_velocity is None

    def test_individual_dimension_fields_populated(self):
        """Per-dimension trend fields can be set."""
        result = _make_loss_propensity_result(
            previous_frequency=55.0,
            previous_severity=35.0,
            freq_velocity=3.0,
            sev_velocity=-2.0,
        )
        assert result.previous_frequency_score == 55.0
        assert result.previous_severity_score == 35.0
        assert result.frequency_score_velocity == 3.0
        assert result.severity_score_velocity == -2.0

    def test_monitoring_uses_combined_velocity(self):
        """LossMonitoringEngine checks combined_score_velocity for velocity spike alerts."""
        config = MonitoringConfig(
            alert_on_velocity_spike=True,
            velocity_spike_threshold=8.0,
        )
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        engine = LossMonitoringEngine(scorer=scorer_mock, config=config)

        current = _make_loss_propensity_result(
            score=70.0,
            combined_velocity=12.0,
            previous_combined=55.0,
        )
        previous = _make_loss_propensity_result(
            score=55.0,
            combined_velocity=2.0,
            calculated_at=datetime.utcnow() - timedelta(days=30),
        )

        alerts = engine._generate_alerts("ent_1", current, previous)

        # Should have velocity spike alert (12.0 >= 8.0 threshold)
        velocity_alerts = [a for a in alerts if "Rapid deterioration" in a.trigger_reason]
        assert len(velocity_alerts) == 1
        assert "12.0" in velocity_alerts[0].trigger_reason

    def test_deteriorating_entity_uses_combined_velocity(self):
        """get_deteriorating_entities uses combined_score_velocity."""
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        engine = LossMonitoringEngine(scorer=scorer_mock)

        # Cache a deteriorating entity
        engine.result_cache["ent_1"] = _make_loss_propensity_result(
            trend=TrendDirection.DETERIORATING,
            combined_velocity=2.0,  # 2 pts/month → 60 pts/year
        )

        # min_score_delta=10 → needs velocity >= 10/30 = 0.333 pts/month
        deteriorating = engine.get_deteriorating_entities(min_score_delta=10.0)
        assert "ent_1" in deteriorating

    def test_improving_entity_uses_combined_velocity(self):
        """get_improving_entities uses combined_score_velocity."""
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        engine = LossMonitoringEngine(scorer=scorer_mock)

        engine.result_cache["ent_2"] = _make_loss_propensity_result(
            trend=TrendDirection.IMPROVING,
            combined_velocity=-1.5,  # 1.5 pts/month improvement
        )

        improving = engine.get_improving_entities(min_score_delta=10.0)
        assert "ent_2" in improving


# =============================================================================
# B3 — MONITORING BAND MIGRATION & REFRESH
# =============================================================================

class TestMonitoringBandLogic:
    """Test monitoring alerts for band changes and refresh logic."""

    def test_band_deterioration_alert(self):
        """Band migration from low to elevated generates an alert."""
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        engine = LossMonitoringEngine(scorer=scorer_mock)

        current = _make_loss_propensity_result(
            score=65.0,
            band=LossPropensityBand.ELEVATED,
        )
        previous = _make_loss_propensity_result(
            score=35.0,
            band=LossPropensityBand.LOW,
            calculated_at=datetime.utcnow() - timedelta(days=30),
        )

        alerts = engine._generate_alerts("ent_3", current, previous)

        band_alerts = [a for a in alerts if "band changed" in a.trigger_reason]
        assert len(band_alerts) == 1
        assert "low" in band_alerts[0].trigger_reason
        assert "elevated" in band_alerts[0].trigger_reason

    def test_high_initial_assessment_alert(self):
        """First assessment in HIGH band generates alert."""
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        engine = LossMonitoringEngine(scorer=scorer_mock)

        current = _make_loss_propensity_result(
            score=90.0,
            band=LossPropensityBand.HIGH,
        )

        alerts = engine._generate_alerts("ent_new", current, None)

        assert len(alerts) == 1
        assert "Initial assessment" in alerts[0].trigger_reason
        assert alerts[0].alert_type == "warning"

    def test_faster_refresh_for_deteriorating(self):
        """Deteriorating entities get faster refresh schedule."""
        scorer_mock = MagicMock(spec=LossCorrelationScorer)
        config = MonitoringConfig(refresh_frequency="monthly")
        engine = LossMonitoringEngine(scorer=scorer_mock, config=config)

        deteriorating = _make_loss_propensity_result(
            trend=TrendDirection.DETERIORATING,
        )
        stable = _make_loss_propensity_result(
            trend=TrendDirection.STABLE,
            band=LossPropensityBand.LOW,
        )

        det_refresh = engine._next_refresh_date(deteriorating)
        stable_refresh = engine._next_refresh_date(stable)

        # Deteriorating should refresh sooner (half the normal frequency)
        det_days = (det_refresh - deteriorating.calculated_at).days
        stable_days = (stable_refresh - stable.calculated_at).days
        assert det_days < stable_days
