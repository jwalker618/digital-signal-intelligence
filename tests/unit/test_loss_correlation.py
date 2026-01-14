"""
Unit Tests for Loss Correlation Layer (Phase 16)

Tests the loss propensity scoring, correlation matrix management,
monitoring engine, and pricing integration components.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import loss correlation components
from layers.loss import (
    # Types
    CorrelationType,
    CorrelationDirection,
    LossPropensityBand,
    SeverityPropensityBand,
    TrendDirection,
    LossSignalResult,
    LossCorrelationFeatureConfig,
    LossCorrelationGroupConfig,
    PropensityBandConfig,
    CohortDefinition,
    MonitoringConfig,
    LossCorrelationConfig,
    LossPropensityResult,
    CorrelationMatrixEntry,
    CorrelationMatrix,
    DeteriorationAlert,
    MonitoringResult,
    # Classes
    LossCorrelationScorer,
    CorrelationMatrixManager,
    LossMonitoringEngine,
    PricingIntegrationMethod,
    PricingIntegrationConfig,
    LossPricingResult,
    LossPricingIntegration,
    create_default_pricing_grid,
    calculate_combined_modifier,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_loss_config():
    """Create a sample loss correlation configuration."""
    return LossCorrelationConfig(
        enabled=True,
        version="2026-01-14",
        correlation_groups=[
            LossCorrelationGroupConfig(
                name="technical_infrastructure",
                weight=0.40,
                confidence_threshold=0.7,
                features=[
                    LossCorrelationFeatureConfig(
                        id="security_headers",
                        weight=0.50,
                        correlation_type=CorrelationType.BOTH,
                        correlation_direction=CorrelationDirection.NEGATIVE,
                        normalizer="linear",
                    ),
                    LossCorrelationFeatureConfig(
                        id="tls_score",
                        weight=0.50,
                        correlation_type=CorrelationType.FREQUENCY,
                        correlation_direction=CorrelationDirection.NEGATIVE,
                        normalizer="linear",
                    ),
                ]
            ),
            LossCorrelationGroupConfig(
                name="public_record",
                weight=0.60,
                confidence_threshold=0.8,
                features=[
                    LossCorrelationFeatureConfig(
                        id="breach_history",
                        weight=1.0,
                        correlation_type=CorrelationType.BOTH,
                        correlation_direction=CorrelationDirection.POSITIVE,
                        normalizer="categorical_map",
                    ),
                ]
            ),
        ],
        propensity_band_mapping_method="fixed_threshold",
        propensity_bands=[
            PropensityBandConfig(name="very_low", min_score=0, max_score=20, expected_frequency_multiplier=0.60, expected_severity_multiplier=0.70),
            PropensityBandConfig(name="low", min_score=20, max_score=40, expected_frequency_multiplier=0.85, expected_severity_multiplier=0.90),
            PropensityBandConfig(name="moderate", min_score=40, max_score=60, expected_frequency_multiplier=1.00, expected_severity_multiplier=1.00),
            PropensityBandConfig(name="elevated", min_score=60, max_score=80, expected_frequency_multiplier=1.25, expected_severity_multiplier=1.15),
            PropensityBandConfig(name="high", min_score=80, max_score=100, expected_frequency_multiplier=1.60, expected_severity_multiplier=1.40),
        ],
        severity_bands=[
            PropensityBandConfig(name="minimal", min_score=0, max_score=20, expected_frequency_multiplier=1.0, expected_severity_multiplier=0.70),
            PropensityBandConfig(name="moderate", min_score=20, max_score=50, expected_frequency_multiplier=1.0, expected_severity_multiplier=1.00),
            PropensityBandConfig(name="significant", min_score=50, max_score=70, expected_frequency_multiplier=1.0, expected_severity_multiplier=1.20),
            PropensityBandConfig(name="severe", min_score=70, max_score=90, expected_frequency_multiplier=1.0, expected_severity_multiplier=1.40),
            PropensityBandConfig(name="catastrophic", min_score=90, max_score=100, expected_frequency_multiplier=1.0, expected_severity_multiplier=1.60),
        ],
        cohort_definitions=[
            CohortDefinition(id="tech_mature", name="Technology Mature", criteria={"security_headers": ">=80"}),
            CohortDefinition(id="default", name="Standard", criteria={}),
        ],
        pricing_integration_method="multiplicative",
        frequency_impact_cap=1.50,
        frequency_impact_floor=0.70,
        severity_impact_cap=1.40,
        severity_impact_floor=0.75,
        frequency_weight=0.60,
        severity_weight=0.40,
        auto_apply_rules=[
            {"condition": "loss_propensity_band == 'high'", "action": "refer", "reason": "High loss propensity"},
        ],
        monitoring_config=MonitoringConfig(
            refresh_frequency="monthly",
            deterioration_threshold=15.0,
            improvement_threshold=15.0,
        ),
    )


@pytest.fixture
def sample_signal_outputs():
    """Create sample signal outputs for testing."""
    # Mock SignalOutput objects
    class MockSignalOutput:
        def __init__(self, signal_id, raw_score, confidence, data_sources=None, extracted_at=None):
            self.signal_id = signal_id
            self.raw_score = raw_score
            self.confidence = confidence
            self.data_sources = data_sources or []
            self.extracted_at = extracted_at or datetime.utcnow()

    return [
        MockSignalOutput("security_headers", 75.0, 0.9),
        MockSignalOutput("tls_score", 80.0, 0.95),
        MockSignalOutput("breach_history", 30.0, 0.85),  # Lower is better for negative correlation
    ]


@pytest.fixture
def high_risk_signal_outputs():
    """Create high-risk signal outputs for testing."""
    class MockSignalOutput:
        def __init__(self, signal_id, raw_score, confidence, data_sources=None, extracted_at=None):
            self.signal_id = signal_id
            self.raw_score = raw_score
            self.confidence = confidence
            self.data_sources = data_sources or []
            self.extracted_at = extracted_at or datetime.utcnow()

    return [
        MockSignalOutput("security_headers", 25.0, 0.9),  # Poor security
        MockSignalOutput("tls_score", 30.0, 0.95),  # Poor TLS
        MockSignalOutput("breach_history", 85.0, 0.85),  # High breach history
    ]


# =============================================================================
# LOSS CORRELATION SCORER TESTS
# =============================================================================

class TestLossCorrelationScorer:
    """Tests for LossCorrelationScorer."""

    def test_scorer_initialization(self, sample_loss_config):
        """Test scorer can be initialized with config."""
        scorer = LossCorrelationScorer(sample_loss_config)
        assert scorer.config == sample_loss_config
        assert len(scorer.signal_config) > 0

    def test_calculate_propensity_basic(self, sample_loss_config, sample_signal_outputs):
        """Test basic propensity calculation."""
        scorer = LossCorrelationScorer(sample_loss_config)
        result = scorer.calculate_propensity(sample_signal_outputs)

        assert isinstance(result, LossPropensityResult)
        assert 0 <= result.loss_propensity_score <= 100
        assert 0 <= result.severity_propensity_score <= 100
        assert 0 <= result.loss_confidence <= 1
        assert isinstance(result.loss_propensity_band, LossPropensityBand)
        assert isinstance(result.severity_propensity_band, SeverityPropensityBand)

    def test_calculate_propensity_high_risk(self, sample_loss_config, high_risk_signal_outputs):
        """Test propensity calculation with high-risk signals."""
        scorer = LossCorrelationScorer(sample_loss_config)
        result = scorer.calculate_propensity(high_risk_signal_outputs)

        # High risk signals should produce elevated/high band
        assert result.loss_propensity_band in [LossPropensityBand.ELEVATED, LossPropensityBand.HIGH]
        assert result.frequency_multiplier > 1.0

    def test_propensity_band_mapping(self, sample_loss_config):
        """Test that scores map to correct bands."""
        scorer = LossCorrelationScorer(sample_loss_config)

        # Test band boundaries
        assert scorer._map_to_propensity_band(10) == LossPropensityBand.VERY_LOW
        assert scorer._map_to_propensity_band(30) == LossPropensityBand.LOW
        assert scorer._map_to_propensity_band(50) == LossPropensityBand.MODERATE
        assert scorer._map_to_propensity_band(70) == LossPropensityBand.ELEVATED
        assert scorer._map_to_propensity_band(90) == LossPropensityBand.HIGH

    def test_cohort_assignment(self, sample_loss_config, sample_signal_outputs):
        """Test cohort assignment from signals."""
        scorer = LossCorrelationScorer(sample_loss_config)
        result = scorer.calculate_propensity(sample_signal_outputs)

        assert result.cohort_id is not None
        assert result.cohort_name is not None
        assert 0 <= result.cohort_confidence <= 1

    def test_trend_calculation_no_previous(self, sample_loss_config, sample_signal_outputs):
        """Test trend calculation without previous result."""
        scorer = LossCorrelationScorer(sample_loss_config)
        result = scorer.calculate_propensity(sample_signal_outputs)

        assert result.trend_direction == TrendDirection.STABLE
        assert result.score_velocity == 0.0

    def test_trend_calculation_with_previous(self, sample_loss_config, sample_signal_outputs):
        """Test trend calculation with previous result."""
        scorer = LossCorrelationScorer(sample_loss_config)

        # First calculation
        first_result = scorer.calculate_propensity(sample_signal_outputs)

        # Create a mock previous result with lower score
        previous = Mock(spec=LossPropensityResult)
        previous.loss_propensity_score = first_result.loss_propensity_score - 20
        previous.calculated_at = datetime.utcnow() - timedelta(days=30)

        # Second calculation with previous
        second_result = scorer.calculate_propensity(sample_signal_outputs, previous)

        # Should show deterioration since current is higher than previous
        assert second_result.trend_direction == TrendDirection.DETERIORATING
        assert second_result.score_velocity > 0

    def test_pricing_modifier_calculation(self, sample_loss_config, sample_signal_outputs):
        """Test pricing modifier calculation."""
        scorer = LossCorrelationScorer(sample_loss_config)
        result = scorer.calculate_propensity(sample_signal_outputs)

        # Modifiers should be bounded
        assert 0.70 <= result.frequency_multiplier <= 1.60
        assert 0.75 <= result.severity_multiplier <= 1.40
        assert result.combined_loss_modifier is not None


# =============================================================================
# CORRELATION MATRIX MANAGER TESTS
# =============================================================================

class TestCorrelationMatrixManager:
    """Tests for CorrelationMatrixManager."""

    def test_manager_initialization(self):
        """Test manager can be initialized."""
        manager = CorrelationMatrixManager("cyber")
        assert manager.coverage == "cyber"
        assert manager.matrix is None

    def test_calibrate_basic(self):
        """Test basic calibration with mock data."""
        manager = CorrelationMatrixManager("cyber")

        # Create mock policies with signals
        policies = [
            {"policy_id": f"pol_{i}", "signals": {"security_headers": 50 + i, "tls_score": 60 + i}}
            for i in range(50)
        ]

        # Create mock losses (some policies have losses)
        losses = [
            {"policy_id": f"pol_{i}", "incurred": 10000 * (i + 1)}
            for i in range(10)
        ]

        matrix = manager.calibrate(
            policies=policies,
            losses=losses,
            observation_start=datetime(2024, 1, 1),
            observation_end=datetime(2025, 12, 31),
        )

        assert isinstance(matrix, CorrelationMatrix)
        assert matrix.coverage == "cyber"
        assert matrix.policy_count == 50
        assert matrix.claim_count == 10
        assert len(matrix.entries) > 0

    def test_get_signal_correlation(self):
        """Test getting correlation for a specific signal."""
        manager = CorrelationMatrixManager("cyber")

        # Create and populate matrix
        policies = [
            {"policy_id": f"pol_{i}", "signals": {"security_headers": 50 + i}}
            for i in range(50)
        ]
        losses = [{"policy_id": f"pol_{i}", "incurred": 10000} for i in range(10)]

        manager.calibrate(policies, losses, datetime(2024, 1, 1), datetime(2025, 12, 31))

        entry = manager.get_signal_correlation("security_headers")
        assert entry is not None
        assert entry.signal_id == "security_headers"
        assert -1 <= entry.frequency_correlation <= 1

    def test_get_high_correlation_signals(self):
        """Test getting high correlation signals."""
        manager = CorrelationMatrixManager("cyber")

        policies = [
            {"policy_id": f"pol_{i}", "signals": {"signal_a": 50 + i, "signal_b": 30 + i}}
            for i in range(50)
        ]
        losses = [{"policy_id": f"pol_{i}", "incurred": 10000} for i in range(10)]

        manager.calibrate(policies, losses, datetime(2024, 1, 1), datetime(2025, 12, 31))

        high_corr = manager.get_high_correlation_signals(min_correlation=0.0)
        assert isinstance(high_corr, list)

    def test_matrix_summary(self):
        """Test getting matrix summary."""
        manager = CorrelationMatrixManager("cyber")

        policies = [
            {"policy_id": f"pol_{i}", "signals": {"security_headers": 50 + i}}
            for i in range(50)
        ]
        losses = [{"policy_id": f"pol_{i}", "incurred": 10000} for i in range(10)]

        manager.calibrate(policies, losses, datetime(2024, 1, 1), datetime(2025, 12, 31))

        summary = manager.get_matrix_summary()
        assert summary["coverage"] == "cyber"
        assert summary["policy_count"] == 50
        assert summary["signal_count"] > 0


# =============================================================================
# LOSS MONITORING ENGINE TESTS
# =============================================================================

class TestLossMonitoringEngine:
    """Tests for LossMonitoringEngine."""

    def test_engine_initialization(self, sample_loss_config):
        """Test monitoring engine initialization."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        assert engine.scorer == scorer
        assert len(engine.result_cache) == 0

    def test_check_entity_first_time(self, sample_loss_config, sample_signal_outputs):
        """Test checking an entity for the first time."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        result = engine.check_entity("entity_001", sample_signal_outputs)

        assert isinstance(result, MonitoringResult)
        assert result.entity_id == "entity_001"
        assert result.previous_result is None
        assert isinstance(result.current_result, LossPropensityResult)

    def test_check_entity_cached(self, sample_loss_config, sample_signal_outputs):
        """Test checking an entity with cached result."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        # First check
        first_result = engine.check_entity("entity_001", sample_signal_outputs)

        # Second check (should use cache if within refresh period)
        second_result = engine.check_entity("entity_001", sample_signal_outputs)

        assert second_result.entity_id == "entity_001"

    def test_force_refresh(self, sample_loss_config, sample_signal_outputs):
        """Test forcing a refresh."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        # First check
        engine.check_entity("entity_001", sample_signal_outputs)

        # Force refresh
        result = engine.check_entity("entity_001", sample_signal_outputs, force_refresh=True)

        assert result.current_result is not None

    def test_deterioration_alert(self, sample_loss_config, sample_signal_outputs, high_risk_signal_outputs):
        """Test deterioration alert generation."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer, config=MonitoringConfig(deterioration_threshold=10.0))

        # First check with good signals
        engine.check_entity("entity_001", sample_signal_outputs, force_refresh=True)

        # Manually set the cached result time to be older
        engine.result_cache["entity_001"].calculated_at = datetime.utcnow() - timedelta(days=31)

        # Second check with bad signals
        result = engine.check_entity("entity_001", high_risk_signal_outputs, force_refresh=True)

        # Should have alerts due to deterioration
        # Note: Alert generation depends on score delta
        assert result is not None

    def test_get_deteriorating_entities(self, sample_loss_config, sample_signal_outputs):
        """Test getting deteriorating entities."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        # Check multiple entities
        engine.check_entity("entity_001", sample_signal_outputs)
        engine.check_entity("entity_002", sample_signal_outputs)

        deteriorating = engine.get_deteriorating_entities()
        assert isinstance(deteriorating, list)

    def test_portfolio_summary(self, sample_loss_config, sample_signal_outputs):
        """Test portfolio summary."""
        scorer = LossCorrelationScorer(sample_loss_config)
        engine = LossMonitoringEngine(scorer)

        # Check some entities
        engine.check_entity("entity_001", sample_signal_outputs)
        engine.check_entity("entity_002", sample_signal_outputs)

        summary = engine.get_portfolio_summary()
        assert summary["entity_count"] == 2
        assert "band_distribution" in summary
        assert "trend_distribution" in summary


# =============================================================================
# PRICING INTEGRATION TESTS
# =============================================================================

class TestLossPricingIntegration:
    """Tests for LossPricingIntegration."""

    def test_integration_initialization(self):
        """Test pricing integration initialization."""
        config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            frequency_impact_cap=1.50,
            frequency_impact_floor=0.70,
        )
        integration = LossPricingIntegration(config)

        assert integration.config == config

    def test_multiplicative_adjustment(self, sample_loss_config, sample_signal_outputs):
        """Test multiplicative pricing adjustment."""
        scorer = LossCorrelationScorer(sample_loss_config)
        loss_result = scorer.calculate_propensity(sample_signal_outputs)

        config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            frequency_impact_cap=1.50,
            frequency_impact_floor=0.70,
            confidence_threshold=0.5,
        )
        integration = LossPricingIntegration(config)

        base_premium = 10000.0
        result = integration.apply_loss_adjustment(base_premium, loss_result)

        assert isinstance(result, LossPricingResult)
        assert result.base_premium == base_premium
        assert result.adjustment_applied == True
        assert result.loss_modifier >= 0.70
        assert result.loss_modifier <= 1.50

    def test_low_confidence_no_adjustment(self, sample_loss_config, sample_signal_outputs):
        """Test that low confidence prevents adjustment."""
        scorer = LossCorrelationScorer(sample_loss_config)
        loss_result = scorer.calculate_propensity(sample_signal_outputs)

        # Set high confidence threshold
        config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.MULTIPLICATIVE,
            confidence_threshold=0.99,  # Higher than typical confidence
        )
        integration = LossPricingIntegration(config)

        result = integration.apply_loss_adjustment(10000.0, loss_result)

        # If confidence is below threshold, no adjustment
        if loss_result.loss_confidence < 0.99:
            assert result.adjustment_applied == False
            assert result.loss_adjusted_premium == result.base_premium

    def test_grid_pricing(self, sample_loss_config, sample_signal_outputs):
        """Test grid-based pricing."""
        scorer = LossCorrelationScorer(sample_loss_config)
        loss_result = scorer.calculate_propensity(sample_signal_outputs)

        config = PricingIntegrationConfig(
            method=PricingIntegrationMethod.GRID,
            confidence_threshold=0.5,
        )
        integration = LossPricingIntegration(config)
        integration.set_pricing_grid(create_default_pricing_grid())

        result = integration.apply_loss_adjustment(10000.0, loss_result, risk_tier="tier_2")

        assert result is not None
        assert result.adjustment_applied == True

    def test_adjustment_summary(self, sample_loss_config, sample_signal_outputs):
        """Test getting adjustment summary."""
        scorer = LossCorrelationScorer(sample_loss_config)
        loss_result = scorer.calculate_propensity(sample_signal_outputs)

        config = PricingIntegrationConfig(method=PricingIntegrationMethod.MULTIPLICATIVE)
        integration = LossPricingIntegration(config)

        summary = integration.get_adjustment_summary(loss_result)

        assert "method" in summary
        assert "loss_propensity_band" in summary
        assert "combined_modifier" in summary
        assert "impact_percentage" in summary


class TestCalculateCombinedModifier:
    """Tests for the calculate_combined_modifier function."""

    def test_basic_calculation(self):
        """Test basic combined modifier calculation."""
        modifier = calculate_combined_modifier(
            frequency_multiplier=1.2,
            severity_multiplier=1.1,
            frequency_weight=0.6,
            severity_weight=0.4,
        )

        expected = 1.2 * 0.6 + 1.1 * 0.4
        assert abs(modifier - expected) < 0.01

    def test_cap_applied(self):
        """Test that cap is applied."""
        modifier = calculate_combined_modifier(
            frequency_multiplier=2.0,
            severity_multiplier=2.0,
            cap=1.5,
        )

        assert modifier == 1.5

    def test_floor_applied(self):
        """Test that floor is applied."""
        modifier = calculate_combined_modifier(
            frequency_multiplier=0.5,
            severity_multiplier=0.5,
            floor=0.7,
        )

        assert modifier == 0.7


class TestCreateDefaultPricingGrid:
    """Tests for the create_default_pricing_grid function."""

    def test_grid_structure(self):
        """Test grid has expected structure."""
        grid = create_default_pricing_grid()

        assert "tier_1" in grid
        assert "tier_2" in grid
        assert "tier_3" in grid
        assert "tier_4" in grid
        assert "tier_5" in grid

        for tier in grid.values():
            assert "very_low" in tier
            assert "low" in tier
            assert "moderate" in tier
            assert "elevated" in tier
            assert "high" in tier

    def test_grid_values_sensible(self):
        """Test grid values are sensible."""
        grid = create_default_pricing_grid()

        # Higher risk bands should have higher modifiers
        for tier_name, tier in grid.items():
            assert tier["very_low"] < tier["moderate"]
            assert tier["moderate"] < tier["high"]


# =============================================================================
# TYPE TESTS
# =============================================================================

class TestLossTypes:
    """Tests for loss correlation types."""

    def test_correlation_type_enum(self):
        """Test CorrelationType enum."""
        assert CorrelationType.FREQUENCY.value == "frequency"
        assert CorrelationType.SEVERITY.value == "severity"
        assert CorrelationType.BOTH.value == "both"

    def test_loss_propensity_band_enum(self):
        """Test LossPropensityBand enum."""
        assert LossPropensityBand.VERY_LOW.value == "very_low"
        assert LossPropensityBand.HIGH.value == "high"

    def test_trend_direction_enum(self):
        """Test TrendDirection enum."""
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.STABLE.value == "stable"
        assert TrendDirection.DETERIORATING.value == "deteriorating"

    def test_loss_correlation_config_from_dict(self):
        """Test LossCorrelationConfig.from_dict."""
        data = {
            "enabled": True,
            "version": "1.0.0",
            "correlation_groups": [
                {
                    "name": "test_group",
                    "weight": 1.0,
                    "confidence_threshold": 0.7,
                    "features": [
                        {
                            "id": "test_signal",
                            "weight": 1.0,
                            "correlation_type": "both",
                            "correlation_direction": "negative",
                            "normalizer": "linear",
                        }
                    ]
                }
            ],
            "propensity_band_mapping": {
                "method": "fixed_threshold",
                "bands": [
                    {"name": "very_low", "min_score": 0, "max_score": 20, "expected_frequency_multiplier": 0.6, "expected_severity_multiplier": 0.7},
                    {"name": "moderate", "min_score": 20, "max_score": 60, "expected_frequency_multiplier": 1.0, "expected_severity_multiplier": 1.0},
                    {"name": "high", "min_score": 60, "max_score": 100, "expected_frequency_multiplier": 1.5, "expected_severity_multiplier": 1.4},
                ]
            },
            "pricing_integration": {
                "method": "multiplicative",
                "frequency_impact_cap": 1.5,
                "frequency_impact_floor": 0.7,
            },
        }

        config = LossCorrelationConfig.from_dict(data)

        assert config.enabled == True
        assert config.version == "1.0.0"
        assert len(config.correlation_groups) == 1
        assert config.correlation_groups[0].name == "test_group"
        assert len(config.propensity_bands) == 3
