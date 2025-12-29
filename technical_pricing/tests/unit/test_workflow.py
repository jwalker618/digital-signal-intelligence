"""
Unit tests for WorkflowEngine.

Tests the complete 14-step workflow orchestration.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from technical_pricing.model.workflow import WorkflowEngine, create_workflow_engine, run_model
from technical_pricing.model.config_manager import ConfigManager
from technical_pricing.model.model_data import ModelDataManager
from technical_pricing.model.scorer import ModelScorer
from technical_pricing.model.query_evaluator import QueryEvaluator
from technical_pricing.model.pricer import ModelPricer
from technical_pricing.model.types import (
    WorkflowResult,
    ModelVersion,
    CoverageConfig,
    SignalGroupConfig,
    SignalConfig,
    TierConfig,
    LimitBand,
    ScoringResult,
    SignalOutput,
    QueryEvaluationResult,
    PricingResult,
    SubmissionRequest,
    ModifierApplication,
    VersionType,
    DecisionType,
    PremiumMethod,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_config():
    """Create a sample coverage config."""
    return CoverageConfig(
        coverage="aerospace",
        configuration="aerospace_general",
        version="1.0.0",
        config_hash="test-hash",
        required_inputs=["entity_id", "tiv"],
        signal_groups=[
            SignalGroupConfig(
                name="safety_signals",
                weight=1.0,
                signals=[
                    SignalConfig(
                        name="safety_record",
                        weight=1.0,
                        inference_function="infer_safety",
                        categorizer_type="threshold_bucket",
                        conditions=[]
                    )
                ],
                conditions=[]
            )
        ],
        direct_queries=[],
        categorical_groups=["operator_type"],
        categorical_features={
            "operator_type": {"major_airline": 0.85, "charter": 1.25}
        },
        tier_thresholds=[
            TierConfig(tier=1, min_score=800, max_score=1000, base_premium=25000, decision=DecisionType.APPROVE),
            TierConfig(tier=2, min_score=600, max_score=799, base_premium=35000, decision=DecisionType.APPROVE),
            TierConfig(tier=3, min_score=400, max_score=599, base_premium=50000, decision=DecisionType.REFER),
            TierConfig(tier=4, min_score=200, max_score=399, base_premium=75000, decision=DecisionType.REFER),
            TierConfig(tier=5, min_score=0, max_score=199, base_premium=100000, decision=DecisionType.DECLINE),
        ],
        limit_bands=[
            LimitBand(limit=1000000, ilf=1.0),
            LimitBand(limit=5000000, ilf=2.5),
        ],
        deductible_credits={},
        metadata={"min_premium": 15000}
    )


@pytest.fixture
def mock_config_manager(sample_config):
    """Create mock ConfigManager."""
    manager = Mock(spec=ConfigManager)
    manager.load_from_file.return_value = sample_config
    manager.validate_config.return_value = []
    manager.verify_required_inputs.return_value = (True, [])
    return manager


@pytest.fixture
def mock_data_manager():
    """Create mock ModelDataManager."""
    manager = Mock(spec=ModelDataManager)

    version = ModelVersion(
        version_id="test-version-id",
        model_id="test-model-id",
        version_number=1,
        version_type=VersionType.INITIAL,
        entity_id="test-entity"
    )

    manager.create_model.return_value = "test-model-id"
    manager.create_initial_version.return_value = version
    manager.update_version_scoring.return_value = version
    manager.update_version_queries.return_value = version
    manager.update_version_pricing.return_value = version
    manager.update_version_decision.return_value = version
    manager.get_latest_version.return_value = version
    manager.create_referral_version.return_value = version

    return manager


@pytest.fixture
def mock_scorer():
    """Create mock ModelScorer."""
    scorer = Mock(spec=ModelScorer)

    result = ScoringResult(
        entity_id="test-entity",
        coverage="aerospace",
        signal_outputs=[
            SignalOutput(
                signal_id="sig-1",
                signal_name="safety_record",
                group_name="safety_signals",
                raw_score=85.0,
                confidence=0.95,
                signal_weight=1.0,
                group_weight=1.0,
                weighted_score=850.0,
                extracted_at=datetime.utcnow()
            )
        ],
        group_scores={"safety_signals": 850.0},
        pure_composite_score=850.0,
        aggregate_confidence=0.95,
        tier_overrides_from_signals=[],
        referrals_from_signals=[],
        notes_from_signals=[]
    )

    scorer.score_entity.return_value = result
    return scorer


@pytest.fixture
def mock_query_evaluator():
    """Create mock QueryEvaluator."""
    evaluator = Mock(spec=QueryEvaluator)

    result = QueryEvaluationResult(
        tier_overrides=[],
        referrals=[],
        notes=[],
        modifiers=[]
    )

    evaluator.evaluate_queries.return_value = result
    return evaluator


@pytest.fixture
def mock_pricer():
    """Create mock ModelPricer."""
    pricer = Mock(spec=ModelPricer)

    result = PricingResult(
        score_based_tier=1,
        final_tier=1,
        base_premium=25000.0,
        base_premium_method=PremiumMethod.PURE,
        modifiers_applied=[],
        premium_after_modifiers=25000.0,
        limit_premiums={1000000: 25000.0, 5000000: 62500.0}
    )

    pricer.price_submission.return_value = result
    return pricer


@pytest.fixture
def workflow_engine(mock_config_manager, mock_data_manager, mock_scorer, mock_query_evaluator, mock_pricer):
    """Create WorkflowEngine with mocked dependencies."""
    return WorkflowEngine(
        config_manager=mock_config_manager,
        data_manager=mock_data_manager,
        scorer=mock_scorer,
        query_evaluator=mock_query_evaluator,
        pricer=mock_pricer
    )


@pytest.fixture
def sample_request():
    """Create sample submission request."""
    return SubmissionRequest(
        entity_id="test-entity-001",
        coverage="aerospace",
        submission_data={"tiv": 10000000, "entity_id": "test-entity-001"},
        direct_query_responses={},
        categorical_selections={"operator_type": "major_airline"},
        user="test_user"
    )


# =============================================================================
# WORKFLOW EXECUTION TESTS
# =============================================================================

class TestWorkflowExecution:
    """Tests for run_workflow method."""

    def test_run_workflow_returns_result(self, workflow_engine, sample_request):
        """Should return WorkflowResult."""
        result = workflow_engine.run_workflow(sample_request)

        assert isinstance(result, WorkflowResult)

    def test_run_workflow_loads_config(self, workflow_engine, sample_request, mock_config_manager):
        """Should load config from file."""
        workflow_engine.run_workflow(sample_request)

        mock_config_manager.load_from_file.assert_called_once_with("aerospace")

    def test_run_workflow_creates_model(self, workflow_engine, sample_request, mock_data_manager):
        """Should create model in data manager."""
        workflow_engine.run_workflow(sample_request)

        mock_data_manager.create_model.assert_called_once()
        call_args = mock_data_manager.create_model.call_args
        assert call_args.kwargs["entity_id"] == "test-entity-001"
        assert call_args.kwargs["coverage"] == "aerospace"

    def test_run_workflow_scores_entity(self, workflow_engine, sample_request, mock_scorer):
        """Should score entity using scorer."""
        workflow_engine.run_workflow(sample_request)

        mock_scorer.score_entity.assert_called_once()

    def test_run_workflow_evaluates_queries(self, workflow_engine, sample_request, mock_query_evaluator):
        """Should evaluate direct queries."""
        workflow_engine.run_workflow(sample_request)

        mock_query_evaluator.evaluate_queries.assert_called_once()

    def test_run_workflow_calculates_pricing(self, workflow_engine, sample_request, mock_pricer):
        """Should calculate pricing."""
        workflow_engine.run_workflow(sample_request)

        mock_pricer.price_submission.assert_called_once()

    def test_run_workflow_updates_version(self, workflow_engine, sample_request, mock_data_manager):
        """Should update version through workflow steps."""
        workflow_engine.run_workflow(sample_request)

        mock_data_manager.update_version_scoring.assert_called_once()
        mock_data_manager.update_version_queries.assert_called_once()
        mock_data_manager.update_version_pricing.assert_called_once()
        mock_data_manager.update_version_decision.assert_called_once()

    def test_run_workflow_populates_result(self, workflow_engine, sample_request):
        """Should populate WorkflowResult fields."""
        result = workflow_engine.run_workflow(sample_request)

        assert result.decision == DecisionType.APPROVE
        assert result.auto_approve is True
        assert result.model_version is not None
        assert len(result.premium_options) > 0


# =============================================================================
# CONFIG ERROR HANDLING TESTS
# =============================================================================

class TestConfigErrorHandling:
    """Tests for configuration error handling."""

    def test_missing_config_returns_error_result(self, workflow_engine, sample_request, mock_config_manager):
        """Should return error result when config not found."""
        mock_config_manager.load_from_file.side_effect = FileNotFoundError("Config not found")

        result = workflow_engine.run_workflow(sample_request)

        assert result.decision == DecisionType.DECLINE
        assert "Configuration not found" in result.validation_errors[0]

    def test_invalid_config_returns_error_result(self, workflow_engine, sample_request, mock_config_manager):
        """Should return error result when config is invalid."""
        mock_config_manager.validate_config.return_value = ["Weight sum != 1.0"]

        result = workflow_engine.run_workflow(sample_request)

        assert result.decision == DecisionType.DECLINE
        assert "Invalid configuration" in result.validation_errors[0]


# =============================================================================
# INPUT VERIFICATION TESTS
# =============================================================================

class TestInputVerification:
    """Tests for Step 3: Input verification."""

    def test_missing_inputs_returns_refer(self, workflow_engine, sample_request, mock_config_manager):
        """Should return REFER when required inputs missing."""
        mock_config_manager.verify_required_inputs.return_value = (False, ["tiv"])

        result = workflow_engine.run_workflow(sample_request)

        assert result.decision == DecisionType.REFER
        assert "tiv" in result.missing_inputs
        assert "Missing required inputs" in result.referral_reasons

    def test_verify_inputs_delegates(self, workflow_engine, sample_config, mock_config_manager):
        """verify_inputs should delegate to config_manager."""
        submission_data = {"entity_id": "test", "tiv": 1000000}
        mock_config_manager.verify_required_inputs.return_value = (True, [])

        is_valid, missing = workflow_engine.verify_inputs(submission_data, sample_config)

        mock_config_manager.verify_required_inputs.assert_called_with(sample_config, submission_data)
        assert is_valid is True
        assert len(missing) == 0


# =============================================================================
# DECISION DETERMINATION TESTS
# =============================================================================

class TestDecisionDetermination:
    """Tests for Step 13: Decision determination."""

    def test_tier_1_approves(self, workflow_engine, sample_config):
        """Tier 1 with no referrals should approve."""
        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=1,
            referral_reasons=[],
            config=sample_config
        )

        assert decision == DecisionType.APPROVE
        assert auto_approve is True

    def test_tier_5_decline_decision(self, workflow_engine):
        """Tier with decline decision should decline."""
        config = CoverageConfig(
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
                TierConfig(tier=5, min_score=0, max_score=199, base_premium=100000, decision=DecisionType.DECLINE)
            ],
            limit_bands=[],
            deductible_credits={},
            metadata={}
        )

        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=5,
            referral_reasons=[],
            config=config
        )

        assert decision == DecisionType.DECLINE
        assert auto_approve is False

    def test_referral_reasons_trigger_refer(self, workflow_engine, sample_config):
        """Any referral reasons should trigger REFER."""
        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=1,
            referral_reasons=["Low safety score"],
            config=sample_config
        )

        assert decision == DecisionType.REFER
        assert auto_approve is False

    def test_tier_refer_decision(self, workflow_engine, sample_config):
        """Tier with refer decision should refer."""
        decision, auto_approve = workflow_engine.determine_decision(
            final_tier=3,  # Tier 3 has REFER decision
            referral_reasons=[],
            config=sample_config
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
        mock_data_manager.get_latest_version.return_value = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type=VersionType.INITIAL,
            entity_id="test"
        )

        workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="approve"
        )

        mock_data_manager.create_referral_version.assert_called_once()

    def test_process_referral_approves(self, workflow_engine, mock_data_manager):
        """Reviewer can approve referred submission."""
        version = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type=VersionType.INITIAL,
            entity_id="test",
            limit_premiums={1000000: 25000.0}
        )
        mock_data_manager.get_latest_version.return_value = version
        mock_data_manager.create_referral_version.return_value = version
        mock_data_manager.update_version_decision.return_value = version

        result = workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="approve"
        )

        assert result.decision == DecisionType.APPROVE
        assert result.auto_approve is True

    def test_process_referral_declines(self, workflow_engine, mock_data_manager):
        """Reviewer can decline referred submission."""
        version = ModelVersion(
            version_id="v1",
            model_id="model-1",
            version_number=1,
            version_type=VersionType.INITIAL,
            entity_id="test",
            limit_premiums={1000000: 25000.0}
        )
        mock_data_manager.get_latest_version.return_value = version
        mock_data_manager.create_referral_version.return_value = version
        mock_data_manager.update_version_decision.return_value = version

        result = workflow_engine.process_referral(
            model_id="model-1",
            reviewer="reviewer1",
            decision="decline"
        )

        assert result.decision == DecisionType.DECLINE

    def test_process_referral_invalid_model_raises(self, workflow_engine, mock_data_manager):
        """Should raise for non-existent model."""
        mock_data_manager.get_latest_version.return_value = None

        with pytest.raises(ValueError, match="Model not found"):
            workflow_engine.process_referral(
                model_id="invalid",
                reviewer="reviewer",
                decision="approve"
            )


# =============================================================================
# WORKFLOW SUMMARY TESTS
# =============================================================================

class TestWorkflowSummary:
    """Tests for workflow summary generation."""

    def test_get_workflow_summary(self, workflow_engine, sample_request):
        """Should return summary dict."""
        result = workflow_engine.run_workflow(sample_request)
        summary = workflow_engine.get_workflow_summary(result)

        assert isinstance(summary, dict)
        assert "model_id" in summary
        assert "version_id" in summary
        assert "decision" in summary
        assert "scoring" in summary
        assert "pricing" in summary
        assert "premium_options" in summary

    def test_summary_includes_scoring_details(self, workflow_engine, sample_request):
        """Summary should include scoring details."""
        result = workflow_engine.run_workflow(sample_request)
        summary = workflow_engine.get_workflow_summary(result)

        scoring = summary["scoring"]
        assert "composite_score" in scoring
        assert "confidence" in scoring
        assert "score_based_tier" in scoring
        assert "final_tier" in scoring

    def test_summary_includes_pricing_details(self, workflow_engine, sample_request):
        """Summary should include pricing details."""
        result = workflow_engine.run_workflow(sample_request)
        summary = workflow_engine.get_workflow_summary(result)

        pricing = summary["pricing"]
        assert "base_premium" in pricing
        assert "final_premium" in pricing
        assert "modifiers_count" in pricing


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory and convenience functions."""

    def test_create_workflow_engine_returns_engine(self):
        """Factory should create WorkflowEngine."""
        engine = create_workflow_engine(config_dir="coverages")

        assert isinstance(engine, WorkflowEngine)
        assert engine.config_manager is not None
        assert engine.data_manager is not None
        assert engine.scorer is not None
        assert engine.query_evaluator is not None
        assert engine.pricer is not None

    def test_create_workflow_engine_with_registry(self):
        """Factory should accept inference registry."""
        registry = {"test_func": lambda x, y: {"score": 50}}
        engine = create_workflow_engine(
            config_dir="coverages",
            inference_registry=registry
        )

        assert engine.scorer.inference_registry == registry


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_workflow_with_empty_premium_options(self, workflow_engine, sample_request, mock_pricer):
        """Should handle empty premium options."""
        mock_pricer.price_submission.return_value = PricingResult(
            score_based_tier=1,
            final_tier=1,
            base_premium=25000.0,
            premium_after_modifiers=25000.0,
            limit_premiums={}  # Empty
        )

        result = workflow_engine.run_workflow(sample_request)

        assert result.recommended_limit == 0
        assert result.recommended_premium == 0

    def test_workflow_with_single_premium_option(self, workflow_engine, sample_request, mock_pricer):
        """Should handle single premium option."""
        mock_pricer.price_submission.return_value = PricingResult(
            score_based_tier=1,
            final_tier=1,
            base_premium=25000.0,
            premium_after_modifiers=25000.0,
            limit_premiums={1000000: 25000.0}
        )

        result = workflow_engine.run_workflow(sample_request)

        assert result.recommended_limit == 1000000
        assert result.recommended_premium == 25000.0

    def test_workflow_accumulates_referral_reasons(self, workflow_engine, sample_request, mock_scorer, mock_query_evaluator):
        """Should accumulate referral reasons from all sources."""
        mock_scorer.score_entity.return_value.referrals_from_signals = ["Signal referral"]
        mock_query_evaluator.evaluate_queries.return_value.referrals = ["Query referral"]

        result = workflow_engine.run_workflow(sample_request)

        assert "Signal referral" in result.referral_reasons
        assert "Query referral" in result.referral_reasons

    def test_workflow_accumulates_notes(self, workflow_engine, sample_request, mock_scorer, mock_query_evaluator):
        """Should accumulate notes from all sources."""
        mock_scorer.score_entity.return_value.notes_from_signals = ["Signal note"]
        mock_query_evaluator.evaluate_queries.return_value.notes = ["Query note"]

        result = workflow_engine.run_workflow(sample_request)

        assert "Signal note" in result.notes
        assert "Query note" in result.notes


# =============================================================================
# RECOMMENDED LIMIT TESTS
# =============================================================================

class TestRecommendedLimit:
    """Tests for recommended limit selection."""

    def test_recommends_middle_limit(self, workflow_engine, sample_config):
        """Should recommend middle limit when multiple options."""
        premium_options = {
            1000000: 25000.0,
            5000000: 62500.0,
            10000000: 100000.0
        }

        recommended = workflow_engine._get_recommended_limit(premium_options, sample_config)

        # Should select middle option
        assert recommended == 5000000

    def test_recommends_first_limit_for_two_options(self, workflow_engine, sample_config):
        """Should recommend first limit when only two options."""
        premium_options = {
            1000000: 25000.0,
            5000000: 62500.0
        }

        recommended = workflow_engine._get_recommended_limit(premium_options, sample_config)

        assert recommended == 1000000

    def test_handles_empty_premium_options(self, workflow_engine, sample_config):
        """Should return 0 for empty premium options."""
        recommended = workflow_engine._get_recommended_limit({}, sample_config)

        assert recommended == 0.0
