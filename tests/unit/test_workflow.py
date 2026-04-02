"""
Unit tests for WorkflowEngine.

Tests the complete 14-step workflow orchestration.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime

from layers.risk.workflow import WorkflowEngine, get_workflow_engine, run_assessment
from layers.risk.model_data import ModelDataManager
from layers.risk.scorer import ModelScorer
from layers.risk.query_evaluator import QueryEvaluator
from layers.risk.pricer import ModelPricer
from layers.risk.types import (
    WorkflowResult,
    ModelVersion,
    SignalOutput,
    CategoricalOutput,
    ScoringResult,
    TriggeredCondition,
    DecisionType,
    utcnow,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_config():
    """Create a mock CoverageConfig."""
    config = MagicMock()
    config.coverage_id = "aerospace"
    config.config_id = "aerospace_general"
    config.metadata.version = "1.0.0"
    config.metadata.minimum_viable_input = []
    config.groups.three_layer_assessment = []
    config.signal_registry = []

    # get_tier_band returns a tier with APPROVE action
    tier_band = MagicMock()
    tier_band.interpretation.action = MagicMock()
    tier_band.interpretation.action.value = "APPROVE"
    # Make TierAction comparison work
    from infrastructure.models.config_schema import TierAction
    tier_band.interpretation.action = TierAction.APPROVE
    config.get_tier_band.return_value = tier_band

    return config


@pytest.fixture
def mock_data_manager():
    """Create mock ModelDataManager."""
    manager = Mock(spec=ModelDataManager)

    version = ModelVersion(
        version_id="test-version-id",
        model_id="test-model-id",
        version_number=1,
        version_type="initial",
        config_hash="test-hash",
        coverage="aerospace",
        configuration="aerospace_general",
        entity_id="test-entity",
    )

    manager.create_model.return_value = "test-model-id"
    manager.create_version.return_value = version
    manager.get_latest_version.return_value = version

    return manager


@pytest.fixture
def mock_scorer():
    """Create mock ModelScorer."""
    scorer = Mock(spec=ModelScorer)

    result = ScoringResult(
        signal_outputs=[
            SignalOutput(
                signal_id="sig-1",
                signal_name="Safety Record",
                group_id="safety_signals",
                raw_score=85.0,
                confidence=0.95,
                weight=1.0,
                weighted_score=85.0,
                data_sources=["test"],
                extracted_at=utcnow(),
            )
        ],
        categorical_outputs=[],
        group_scores={"safety_signals": {"risk_score": 85.0, "risk_weight": 1.0, "risk_contribution": 850.0, "risk_contribution_formula": "85.0 × 1.0 × 10 = 850.0"}},
        pure_composite_score=850.0,
        confidence=0.95,
        signal_coverage=1.0,
        conditions_triggered=[],
        tier_overrides=[],
        referrals=[],
        notes=[],
        modifiers=[],
    )

    scorer.score_entity.return_value = result
    return scorer


@pytest.fixture
def mock_query_evaluator():
    """Create mock QueryEvaluator."""
    evaluator = Mock(spec=QueryEvaluator)

    result = MagicMock()
    result.tier_overrides = []
    result.referrals = []
    result.notes = []
    result.modifiers = []
    result.conditions_triggered = []

    evaluator.evaluate_queries.return_value = result
    return evaluator


@pytest.fixture
def mock_pricer():
    """Create mock ModelPricer."""
    pricer = Mock(spec=ModelPricer)

    result = MagicMock()
    result.score_based_tier = 1
    result.final_tier = 1
    result.tier_label = "PREFERRED"
    result.tier_margin = 0.8
    result.base_premium = 25000.0
    result.base_premium_method = "PREMIUM_BASE"
    result.base_premium_derivation = {}
    result.modifiers_applied = []
    result.premium_after_modifiers = 25000.0
    result.limit_premiums = {1000000: 25000.0, 5000000: 62500.0}
    result.limit_premium_details = []
    result.final_premium = 25000.0
    result.uncapped_premium = None
    result.tier_overrides_considered = []

    pricer.price_submission.return_value = result
    return pricer


@pytest.fixture
def mock_discovery_engine():
    """Create mock WebsiteDiscoveryEngine."""
    engine = MagicMock()
    # discover returns None by default (skip discovery)
    engine.discover.return_value = None
    return engine


@pytest.fixture
def workflow_engine(mock_data_manager, mock_scorer, mock_query_evaluator, mock_pricer, mock_discovery_engine):
    """Create WorkflowEngine with mocked dependencies."""
    return WorkflowEngine(
        data_manager=mock_data_manager,
        scorer=mock_scorer,
        query_evaluator=mock_query_evaluator,
        pricer=mock_pricer,
        discovery_engine=mock_discovery_engine,
        traditional_modifiers=[],
        enable_loss_correlation=False,
    )


# =============================================================================
# WORKFLOW EXECUTION TESTS
# =============================================================================

class TestWorkflowExecution:
    """Tests for run_workflow method."""

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_returns_result(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
    ):
        """Should return WorkflowResult."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        result = workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert isinstance(result, WorkflowResult)

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_creates_model(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config, mock_data_manager,
    ):
        """Should create model in data manager."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        mock_data_manager.create_model.assert_called_once()

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_scores_entity(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config, mock_scorer,
    ):
        """Should score entity using scorer."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        mock_scorer.score_entity.assert_called_once()

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_evaluates_queries(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config, mock_query_evaluator,
    ):
        """Should evaluate direct queries."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        mock_query_evaluator.evaluate_queries.assert_called_once()

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_calculates_pricing(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config, mock_pricer,
    ):
        """Should calculate pricing."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        mock_pricer.price_submission.assert_called_once()

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_populates_result(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
    ):
        """Should populate WorkflowResult fields."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        result = workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert result.entity_id == "test-entity-001"
        assert result.coverage == "aerospace"
        assert result.decision in (DecisionType.APPROVE, DecisionType.REFER, DecisionType.DECLINE)
        assert result.model_version is not None

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_run_workflow_with_preloaded_config(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
    ):
        """Should use preloaded config when provided."""
        mock_appetite.return_value = MagicMock(fit=True)

        result = workflow_engine.run_workflow(
            entity_id="test-entity-001",
            coverage="aerospace",
            config=mock_config,
            skip_discovery=True,
            skip_input_validation=True,
        )

        # Should NOT call get_config when config is provided
        mock_get_config.assert_not_called()
        assert isinstance(result, WorkflowResult)


# =============================================================================
# CONFIG ERROR HANDLING TESTS
# =============================================================================

class TestConfigErrorHandling:
    """Tests for configuration error handling."""

    @patch("layers.risk.workflow.evaluate_appetite")
    @patch("layers.risk.workflow.get_config")
    def test_quarantined_config_returns_decline(
        self, mock_get_config, mock_appetite, workflow_engine,
    ):
        """Should return decline result when config is quarantined."""
        from infrastructure.models.compiler import ConfigQuarantinedError
        mock_appetite.return_value = MagicMock(fit=True)
        mock_get_config.side_effect = ConfigQuarantinedError("aerospace", "aerospace_general", "Config failed health checks")

        result = workflow_engine.run_workflow(
            entity_id="test-entity",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert result.decision == DecisionType.DECLINE


# =============================================================================
# INPUT VERIFICATION TESTS
# =============================================================================

class TestInputVerification:
    """Tests for Step 3: Input verification."""

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_missing_inputs_returns_refer(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
    ):
        """Should return REFER when required inputs missing."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        # Make verify_inputs return missing fields
        mvi_field = MagicMock()
        mvi_field.field = "total_insured_value"
        mock_config.metadata.minimum_viable_input = [mvi_field]

        result = workflow_engine.run_workflow(
            entity_id="test-entity",
            coverage="aerospace",
            submission_data={},  # Empty - will be missing required inputs
            skip_discovery=True,
        )

        assert result.decision == DecisionType.REFER
        assert not result.is_valid


# =============================================================================
# DECISION DETERMINATION TESTS
# =============================================================================

class TestDecisionDetermination:
    """Tests for Step 13: Decision determination."""

    def test_approve_tier_approves(self, workflow_engine, mock_config):
        """Approve-action tier with no referrals should approve."""
        from infrastructure.models.config_schema import TierAction
        tier_band = MagicMock()
        tier_band.interpretation.action = TierAction.APPROVE
        mock_config.get_tier_band.return_value = tier_band

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=1,
            referral_reasons=[],
            config=mock_config,
        )

        assert decision == DecisionType.APPROVE
        assert auto_approve is True

    def test_decline_tier_declines(self, workflow_engine, mock_config):
        """Decline-action tier should decline."""
        from infrastructure.models.config_schema import TierAction
        tier_band = MagicMock()
        tier_band.interpretation.action = TierAction.DECLINE
        mock_config.get_tier_band.return_value = tier_band

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=5,
            referral_reasons=[],
            config=mock_config,
        )

        assert decision == DecisionType.DECLINE
        assert auto_approve is False

    def test_referral_reasons_trigger_refer(self, workflow_engine, mock_config):
        """Any referral reasons should trigger REFER."""
        from infrastructure.models.config_schema import TierAction
        tier_band = MagicMock()
        tier_band.interpretation.action = TierAction.APPROVE
        mock_config.get_tier_band.return_value = tier_band

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=1,
            referral_reasons=["Low safety score"],
            config=mock_config,
        )

        assert decision == DecisionType.REFER
        assert auto_approve is False

    def test_refer_tier_decision(self, workflow_engine, mock_config):
        """Tier with refer action should refer."""
        from infrastructure.models.config_schema import TierAction
        tier_band = MagicMock()
        tier_band.interpretation.action = TierAction.REFER
        mock_config.get_tier_band.return_value = tier_band

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=3,
            referral_reasons=[],
            config=mock_config,
        )

        assert decision == DecisionType.REFER
        assert auto_approve is False

    def test_missing_tier_band_defaults_refer(self, workflow_engine, mock_config):
        """Missing tier band should default to REFER."""
        mock_config.get_tier_band.return_value = None

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=99,
            referral_reasons=[],
            config=mock_config,
        )

        assert decision == DecisionType.REFER
        assert auto_approve is False


# =============================================================================
# REFERRAL PROCESSING TESTS
# =============================================================================

class TestReferralProcessing:
    """Tests for referral review processing."""

    def test_process_referral_creates_new_version(self, workflow_engine, mock_data_manager):
        """Should create new version for referral review."""
        version = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type="initial",
            config_hash="hash",
            coverage="aerospace",
            configuration="aerospace_general",
            entity_id="test",
        )
        mock_data_manager.get_latest_version.return_value = version

        workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="approve",
        )

        mock_data_manager.create_version.assert_called_once()

    def test_process_referral_approves(self, workflow_engine, mock_data_manager):
        """Reviewer can approve referred submission."""
        version = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type="initial",
            config_hash="hash",
            coverage="aerospace",
            configuration="aerospace_general",
            entity_id="test",
        )
        mock_data_manager.get_latest_version.return_value = version
        mock_data_manager.create_version.return_value = version

        result = workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="approve",
        )

        assert result.decision == DecisionType.APPROVE

    def test_process_referral_declines(self, workflow_engine, mock_data_manager):
        """Reviewer can decline referred submission."""
        version = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type="initial",
            config_hash="hash",
            coverage="aerospace",
            configuration="aerospace_general",
            entity_id="test",
        )
        mock_data_manager.get_latest_version.return_value = version
        mock_data_manager.create_version.return_value = version

        result = workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="decline",
        )

        assert result.decision == DecisionType.DECLINE


# =============================================================================
# APPETITE CHECK TESTS
# =============================================================================

class TestAppetiteCheck:
    """Tests for Step 0a: Appetite pre-qualification."""

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_outside_appetite_returns_decline(
        self, mock_appetite, mock_get_config, workflow_engine,
    ):
        """Should decline when submission is outside appetite."""
        mock_appetite.return_value = MagicMock(
            fit=False,
            reasons=["Revenue below minimum threshold"],
        )

        result = workflow_engine.run_workflow(
            entity_id="test-entity",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert result.decision == DecisionType.DECLINE
        # get_config should NOT be called since appetite failed first
        mock_get_config.assert_not_called()


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_workflow_accumulates_referral_reasons(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
        mock_scorer, mock_query_evaluator,
    ):
        """Should accumulate referral reasons from all sources."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        # Add referrals from scoring and queries
        mock_scorer.score_entity.return_value.referrals = ["Signal referral"]
        mock_query_evaluator.evaluate_queries.return_value.referrals = ["Query referral"]

        result = workflow_engine.run_workflow(
            entity_id="test-entity",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert "Signal referral" in result.referral_reasons
        assert "Query referral" in result.referral_reasons

    @patch("layers.risk.workflow.get_config")
    @patch("layers.risk.workflow.evaluate_appetite")
    def test_workflow_accumulates_notes(
        self, mock_appetite, mock_get_config, workflow_engine, mock_config,
        mock_scorer, mock_query_evaluator,
    ):
        """Should accumulate notes from all sources."""
        mock_get_config.return_value = mock_config
        mock_appetite.return_value = MagicMock(fit=True)

        mock_scorer.score_entity.return_value.notes = ["Signal note"]
        mock_query_evaluator.evaluate_queries.return_value.notes = ["Query note"]

        result = workflow_engine.run_workflow(
            entity_id="test-entity",
            coverage="aerospace",
            skip_discovery=True,
            skip_input_validation=True,
        )

        assert "Signal note" in result.notes
        assert "Query note" in result.notes
