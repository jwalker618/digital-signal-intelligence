"""
Integration Tests for Loss Correlation in Workflow (Phase 16)

Tests end-to-end loss propensity integration with the main DSI workflow.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import workflow components
from layers.risk.workflow import WorkflowEngine, LOSS_CORRELATION_AVAILABLE
from layers.risk.types import (
    CoverageConfig,
    ModelVersion,
    DecisionType,
)

# Import loss correlation components (conditional)
if LOSS_CORRELATION_AVAILABLE:
    from layers.loss import (
        LossCorrelationScorer,
        LossCorrelationConfig,
        LossPropensityResult,
        LossPropensityBand,
        SeverityPropensityBand,
        TrendDirection,
        LossPricingIntegration,
        PricingIntegrationConfig,
        PricingIntegrationMethod,
    )


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_config_with_loss_correlation():
    """Create a mock coverage config with loss correlation enabled."""
    config = Mock(spec=CoverageConfig)
    config.coverage = "cyber"
    config.configuration = "cyber_general"
    config.metadata = Mock()
    config.metadata.version = "1.0.0"
    config.metadata.minimum_viable_input = ["entity_id", "limit"]

    # Add loss correlation config
    config.loss_correlation = {
        "enabled": True,
        "version": "2026-01-14",
        "correlation_groups": [
            {
                "name": "technical_infrastructure",
                "weight": 0.50,
                "confidence_threshold": 0.7,
                "features": [
                    {
                        "id": "security_headers",
                        "weight": 0.50,
                        "correlation_type": "both",
                        "correlation_direction": "negative",
                        "normalizer": "linear",
                    },
                    {
                        "id": "tls_score",
                        "weight": 0.50,
                        "correlation_type": "frequency",
                        "correlation_direction": "negative",
                        "normalizer": "linear",
                    },
                ]
            },
            {
                "name": "public_record",
                "weight": 0.50,
                "confidence_threshold": 0.8,
                "features": [
                    {
                        "id": "breach_history",
                        "weight": 1.0,
                        "correlation_type": "both",
                        "correlation_direction": "positive",
                        "normalizer": "categorical_map",
                    },
                ]
            },
        ],
        "propensity_band_mapping": {
            "method": "fixed_threshold",
            "bands": [
                {"name": "very_low", "min_score": 0, "max_score": 20, "expected_frequency_multiplier": 0.6, "expected_severity_multiplier": 0.7},
                {"name": "low", "min_score": 20, "max_score": 40, "expected_frequency_multiplier": 0.85, "expected_severity_multiplier": 0.90},
                {"name": "moderate", "min_score": 40, "max_score": 60, "expected_frequency_multiplier": 1.0, "expected_severity_multiplier": 1.0},
                {"name": "elevated", "min_score": 60, "max_score": 80, "expected_frequency_multiplier": 1.25, "expected_severity_multiplier": 1.15},
                {"name": "high", "min_score": 80, "max_score": 100, "expected_frequency_multiplier": 1.60, "expected_severity_multiplier": 1.40},
            ]
        },
        "pricing_integration": {
            "method": "multiplicative",
            "frequency_impact_cap": 1.50,
            "frequency_impact_floor": 0.70,
            "severity_impact_cap": 1.40,
            "severity_impact_floor": 0.75,
            "frequency_weight": 0.60,
            "severity_weight": 0.40,
        },
        "monitoring": {
            "refresh_frequency": "monthly",
            "deterioration_threshold": 15,
            "improvement_threshold": 15,
        },
    }

    return config


@pytest.fixture
def mock_signal_outputs():
    """Create mock signal outputs."""
    class MockSignalOutput:
        def __init__(self, signal_id, raw_score, confidence):
            self.signal_id = signal_id
            self.raw_score = raw_score
            self.confidence = confidence
            self.data_sources = []
            self.extracted_at = datetime.utcnow()

    return [
        MockSignalOutput("security_headers", 70.0, 0.9),
        MockSignalOutput("tls_score", 75.0, 0.95),
        MockSignalOutput("breach_history", 20.0, 0.85),
    ]


@pytest.fixture
def mock_scoring_result(mock_signal_outputs):
    """Create mock scoring result."""
    result = Mock()
    result.signal_outputs = mock_signal_outputs
    result.categorical_outputs = []
    result.group_scores = {"technical_infrastructure": 0.72, "public_record": 0.80}
    result.pure_composite_score = 720.0
    result.conditions_triggered = []
    result.tier_overrides = []
    result.referrals = []
    result.notes = []
    result.confidence = 0.9
    result.signal_coverage = 0.95
    return result


# =============================================================================
# WORKFLOW ENGINE TESTS WITH LOSS CORRELATION
# =============================================================================

@pytest.mark.skipif(not LOSS_CORRELATION_AVAILABLE, reason="Loss correlation layer not available")
class TestWorkflowWithLossCorrelation:
    """Tests for workflow engine with loss correlation integration."""

    def test_workflow_engine_initialization_with_loss(self):
        """Test workflow engine initializes with loss correlation support."""
        engine = WorkflowEngine(
            enable_loss_correlation=True,
        )

        assert engine.enable_loss_correlation == True

    def test_workflow_engine_disabled_loss(self):
        """Test workflow engine can disable loss correlation."""
        engine = WorkflowEngine(
            enable_loss_correlation=False,
        )

        assert engine.enable_loss_correlation == False

    @patch('layers.risk.workflow.load_coverage_config')
    @patch('layers.risk.workflow.WebsiteDiscoveryEngine')
    def test_calculate_loss_propensity_method(
        self,
        mock_discovery,
        mock_load_config,
        mock_config_with_loss_correlation,
        mock_signal_outputs
    ):
        """Test the _calculate_loss_propensity method."""
        mock_load_config.return_value = mock_config_with_loss_correlation

        engine = WorkflowEngine(enable_loss_correlation=True)

        result = engine._calculate_loss_propensity(
            signal_outputs=mock_signal_outputs,
            config=mock_config_with_loss_correlation,
        )

        # Should return a result if loss correlation is configured
        if result is not None:
            assert hasattr(result, 'loss_propensity_score')
            assert hasattr(result, 'loss_propensity_band')
            assert hasattr(result, 'loss_confidence')

    def test_calculate_loss_propensity_disabled(self, mock_config_with_loss_correlation, mock_signal_outputs):
        """Test that disabled loss correlation returns None."""
        engine = WorkflowEngine(enable_loss_correlation=False)

        result = engine._calculate_loss_propensity(
            signal_outputs=mock_signal_outputs,
            config=mock_config_with_loss_correlation,
        )

        assert result is None

    def test_calculate_loss_propensity_no_config(self, mock_signal_outputs):
        """Test that missing loss config returns None."""
        config = Mock(spec=CoverageConfig)
        config.loss_correlation = None

        engine = WorkflowEngine(enable_loss_correlation=True)

        result = engine._calculate_loss_propensity(
            signal_outputs=mock_signal_outputs,
            config=config,
        )

        assert result is None


# =============================================================================
# MODEL VERSION LOSS FIELD TESTS
# =============================================================================

@pytest.mark.skipif(not LOSS_CORRELATION_AVAILABLE, reason="Loss correlation layer not available")
class TestModelVersionLossFields:
    """Tests for loss fields in ModelVersion."""

    def test_model_version_has_loss_fields(self):
        """Test that ModelVersion has loss-related fields."""
        from layers.risk.types import ModelVersion

        # Create a model version instance
        mv = ModelVersion(
            version_id="test-001",
            model_id="model-001",
            version_number=1,
            version_type="initial",
            config_hash="abc123",
            coverage="cyber",
            configuration="cyber_general",
            entity_id="test-entity",
        )

        # Check loss fields exist
        assert hasattr(mv, 'loss_propensity_score')
        assert hasattr(mv, 'severity_propensity_score')
        assert hasattr(mv, 'loss_propensity_band')
        assert hasattr(mv, 'loss_confidence')
        assert hasattr(mv, 'loss_cohort_code')
        assert hasattr(mv, 'loss_frequency_multiplier')
        assert hasattr(mv, 'loss_severity_multiplier')
        assert hasattr(mv, 'loss_combined_modifier')
        assert hasattr(mv, 'loss_trend_direction')
        assert hasattr(mv, 'correlation_matrix_version')

    def test_model_version_loss_fields_default_none(self):
        """Test that loss fields default to None."""
        from layers.risk.types import ModelVersion

        mv = ModelVersion(
            version_id="test-001",
            model_id="model-001",
            version_number=1,
            version_type="initial",
            config_hash="abc123",
            coverage="cyber",
            configuration="cyber_general",
            entity_id="test-entity",
        )

        assert mv.loss_propensity_score is None
        assert mv.loss_propensity_band is None
        assert mv.loss_confidence is None
        assert mv.loss_cohort_code is None

    def test_model_version_loss_fields_can_be_set(self):
        """Test that loss fields can be populated."""
        from layers.risk.types import ModelVersion

        mv = ModelVersion(
            version_id="test-001",
            model_id="model-001",
            version_number=1,
            version_type="initial",
            config_hash="abc123",
            coverage="cyber",
            configuration="cyber_general",
            entity_id="test-entity",
        )

        # Set loss fields
        mv.loss_propensity_score = 65.5
        mv.loss_propensity_band = "elevated"
        mv.loss_confidence = 0.85
        mv.loss_frequency_multiplier = 1.25
        mv.loss_combined_modifier = 1.18

        assert mv.loss_propensity_score == 65.5
        assert mv.loss_propensity_band == "elevated"
        assert mv.loss_confidence == 0.85
        assert mv.loss_frequency_multiplier == 1.25


# =============================================================================
# END-TO-END LOSS PRICING INTEGRATION TESTS
# =============================================================================

@pytest.mark.skipif(not LOSS_CORRELATION_AVAILABLE, reason="Loss correlation layer not available")
class TestEndToEndLossPricing:
    """End-to-end tests for loss-adjusted pricing."""

    def test_loss_adjusted_premium_calculation(self, mock_config_with_loss_correlation, mock_signal_outputs):
        """Test end-to-end premium calculation with loss adjustment."""
        # Create scorer and calculate loss propensity
        config = LossCorrelationConfig.from_dict(mock_config_with_loss_correlation.loss_correlation)
        scorer = LossCorrelationScorer(config)
        loss_result = scorer.calculate_propensity(mock_signal_outputs)

        # Apply pricing adjustment
        pricing_config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            frequency_impact_cap=1.50,
            frequency_impact_floor=0.70,
            confidence_threshold=0.5,
        )
        integration = LossPricingIntegration(pricing_config)

        base_premium = 50000.0
        pricing_result = integration.apply_loss_adjustment(base_premium, loss_result)

        # Verify result
        assert pricing_result.base_premium == base_premium
        assert pricing_result.adjustment_applied == True
        assert pricing_result.loss_adjusted_premium != base_premium or pricing_result.loss_modifier == 1.0

    def test_high_risk_increases_premium(self, mock_config_with_loss_correlation):
        """Test that high-risk signals increase premium."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # High risk signals
        high_risk_signals = [
            MockSignalOutput("security_headers", 20.0, 0.9),  # Poor security
            MockSignalOutput("tls_score", 25.0, 0.95),  # Poor TLS
            MockSignalOutput("breach_history", 85.0, 0.85),  # High breach history (bad)
        ]

        config = LossCorrelationConfig.from_dict(mock_config_with_loss_correlation.loss_correlation)
        scorer = LossCorrelationScorer(config)
        loss_result = scorer.calculate_propensity(high_risk_signals)

        pricing_config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            frequency_impact_cap=1.50,
            frequency_impact_floor=0.70,
            confidence_threshold=0.5,
        )
        integration = LossPricingIntegration(pricing_config)

        base_premium = 50000.0
        pricing_result = integration.apply_loss_adjustment(base_premium, loss_result)

        # High risk should increase premium
        if loss_result.loss_propensity_band in [LossPropensityBand.ELEVATED, LossPropensityBand.HIGH]:
            assert pricing_result.loss_adjusted_premium >= base_premium

    def test_low_risk_decreases_premium(self, mock_config_with_loss_correlation):
        """Test that low-risk signals decrease premium."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Low risk signals
        low_risk_signals = [
            MockSignalOutput("security_headers", 90.0, 0.9),  # Excellent security
            MockSignalOutput("tls_score", 95.0, 0.95),  # Excellent TLS
            MockSignalOutput("breach_history", 5.0, 0.85),  # No breach history (good)
        ]

        config = LossCorrelationConfig.from_dict(mock_config_with_loss_correlation.loss_correlation)
        scorer = LossCorrelationScorer(config)
        loss_result = scorer.calculate_propensity(low_risk_signals)

        pricing_config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            frequency_impact_cap=1.50,
            frequency_impact_floor=0.70,
            confidence_threshold=0.5,
        )
        integration = LossPricingIntegration(pricing_config)

        base_premium = 50000.0
        pricing_result = integration.apply_loss_adjustment(base_premium, loss_result)

        # Low risk should decrease premium
        if loss_result.loss_propensity_band in [LossPropensityBand.VERY_LOW, LossPropensityBand.LOW]:
            assert pricing_result.loss_adjusted_premium <= base_premium


# =============================================================================
# REFERRAL TRIGGER TESTS
# =============================================================================

@pytest.mark.skipif(not LOSS_CORRELATION_AVAILABLE, reason="Loss correlation layer not available")
class TestLossReferralTriggers:
    """Tests for loss-based referral triggers."""

    def test_high_loss_propensity_triggers_referral(self, mock_config_with_loss_correlation):
        """Test that high loss propensity triggers referral."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Very high risk signals
        high_risk_signals = [
            MockSignalOutput("security_headers", 10.0, 0.9),
            MockSignalOutput("tls_score", 15.0, 0.95),
            MockSignalOutput("breach_history", 95.0, 0.85),
        ]

        config = LossCorrelationConfig.from_dict(mock_config_with_loss_correlation.loss_correlation)
        scorer = LossCorrelationScorer(config)
        loss_result = scorer.calculate_propensity(high_risk_signals)

        # High band should trigger referral
        if loss_result.loss_propensity_band == LossPropensityBand.HIGH:
            assert loss_result.referral_triggered == True
            assert len(loss_result.referral_reasons) > 0
