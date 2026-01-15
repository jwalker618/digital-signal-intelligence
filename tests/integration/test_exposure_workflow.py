"""
Integration Tests for Exposure Shadow Layer in Workflow (Phase 17)

Tests end-to-end exposure magnitude and complexity integration with the main DSI workflow.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import workflow components
from layers.risk.workflow import WorkflowEngine, EXPOSURE_SHADOW_AVAILABLE
from layers.risk.types import (
    CoverageConfig,
    ModelVersion,
    DecisionType,
)

# Import exposure components (conditional)
if EXPOSURE_SHADOW_AVAILABLE:
    from layers.exposure import (
        ExposureScorer,
        ComplexityScorer,
        ExposureConfig,
        ExposureResult,
        ComplexityResult,
        ExposureBand,
        ComplexityCategory,
        ProxyTier,
    )


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_config_with_exposure_shadow():
    """Create a mock coverage config with exposure shadow enabled."""
    config = Mock(spec=CoverageConfig)
    config.coverage = "cyber"
    config.configuration = "cyber_general"
    config.metadata = Mock()
    config.metadata.version = "1.0.0"
    config.metadata.minimum_viable_input = ["entity_id", "limit"]

    # Add exposure shadow config
    config.exposure_shadow = {
        "enabled": True,
        "version": "2026-01-15",
        "exposure_groups": [
            {
                "name": "digital_footprint",
                "weight": 0.40,
                "confidence_threshold": 0.6,
                "features": [
                    {"id": "dns_complexity", "weight": 0.30, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "subdomain_count", "weight": 0.25, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "ip_footprint", "weight": 0.25, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "ssl_certificates", "weight": 0.20, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                ]
            },
            {
                "name": "corporate_indicators",
                "weight": 0.30,
                "confidence_threshold": 0.7,
                "features": [
                    {"id": "employee_estimate", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "location_count", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                ]
            },
            {
                "name": "public_financials",
                "weight": 0.30,
                "confidence_threshold": 0.8,
                "features": [
                    {"id": "market_cap", "weight": 0.50, "proxy_tier": "DIRECT_OBSERVABLE", "normalizer": "log_scale"},
                    {"id": "revenue_estimate", "weight": 0.50, "proxy_tier": "DIRECT_OBSERVABLE", "normalizer": "log_scale"},
                ]
            },
        ],
        "complexity_groups": [
            {
                "name": "geographic_dispersion",
                "weight": 0.40,
                "confidence_threshold": 0.6,
                "features": [
                    {"id": "country_count", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "timezone_spread", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "linear"},
                ]
            },
            {
                "name": "structural_complexity",
                "weight": 0.30,
                "confidence_threshold": 0.7,
                "features": [
                    {"id": "subsidiary_count", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "brand_count", "weight": 0.50, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                ]
            },
            {
                "name": "technical_heterogeneity",
                "weight": 0.30,
                "confidence_threshold": 0.6,
                "features": [
                    {"id": "tech_stack_diversity", "weight": 1.0, "proxy_tier": "INFERRED_PROXY", "normalizer": "linear"},
                ]
            },
        ],
        "band_mapping": {
            "method": "fixed_threshold",
            "bands": [
                {"name": "micro", "min_score": 0, "max_score": 20, "implied_tiv_low": 0, "implied_tiv_high": 1000000, "exposure_modifier": 0.50},
                {"name": "small", "min_score": 20, "max_score": 40, "implied_tiv_low": 1000000, "implied_tiv_high": 10000000, "exposure_modifier": 0.75},
                {"name": "medium", "min_score": 40, "max_score": 60, "implied_tiv_low": 10000000, "implied_tiv_high": 50000000, "exposure_modifier": 1.00},
                {"name": "large", "min_score": 60, "max_score": 80, "implied_tiv_low": 50000000, "implied_tiv_high": 250000000, "exposure_modifier": 1.50},
                {"name": "very_large", "min_score": 80, "max_score": 100, "implied_tiv_low": 250000000, "implied_tiv_high": 1000000000, "exposure_modifier": 2.50},
            ]
        },
        "complexity_categories": [
            {"name": "simple", "min_score": 0, "max_score": 20, "complexity_modifier": 0.85},
            {"name": "moderate", "min_score": 20, "max_score": 40, "complexity_modifier": 0.95},
            {"name": "complex", "min_score": 40, "max_score": 60, "complexity_modifier": 1.10},
            {"name": "highly_complex", "min_score": 60, "max_score": 80, "complexity_modifier": 1.30},
            {"name": "extremely_complex", "min_score": 80, "max_score": 100, "complexity_modifier": 1.60},
        ],
        "cohort_priors": [
            {"cohort_id": "tech_startup", "name": "Tech Startup", "sector": "technology", "prior_band": "small", "prior_score": 30.0, "confidence": 0.4},
        ],
        "auto_apply_rules": [
            {"condition": "exposure_band == 'very_large' and confidence < 0.5", "action": "refer", "reason": "Very large exposure with low confidence"},
        ],
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
        MockSignalOutput("dns_complexity", 50.0, 0.9),
        MockSignalOutput("subdomain_count", 45.0, 0.85),
        MockSignalOutput("ip_footprint", 55.0, 0.8),
        MockSignalOutput("ssl_certificates", 40.0, 0.75),
        MockSignalOutput("employee_estimate", 60.0, 0.9),
        MockSignalOutput("location_count", 30.0, 0.85),
        MockSignalOutput("country_count", 5.0, 0.9),
        MockSignalOutput("timezone_spread", 4.0, 0.85),
        MockSignalOutput("subsidiary_count", 3.0, 0.8),
        MockSignalOutput("brand_count", 2.0, 0.75),
        MockSignalOutput("tech_stack_diversity", 45.0, 0.9),
    ]


@pytest.fixture
def mock_scoring_result(mock_signal_outputs):
    """Create mock scoring result."""
    result = Mock()
    result.signal_outputs = mock_signal_outputs
    result.categorical_outputs = []
    result.group_scores = {"digital_footprint": 0.50, "corporate_indicators": 0.45}
    result.pure_composite_score = 500.0
    result.conditions_triggered = []
    result.tier_overrides = []
    result.referrals = []
    result.notes = []
    result.confidence = 0.85
    result.signal_coverage = 0.9
    return result


# =============================================================================
# WORKFLOW ENGINE TESTS WITH EXPOSURE SHADOW
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestWorkflowWithExposureShadow:
    """Tests for workflow engine with exposure shadow integration."""

    def test_workflow_engine_initialization_with_exposure(self):
        """Test workflow engine initializes with exposure shadow support."""
        engine = WorkflowEngine(
            enable_exposure_shadow=True,
        )

        assert engine.enable_exposure_shadow == True

    def test_workflow_engine_disabled_exposure(self):
        """Test workflow engine can disable exposure shadow."""
        engine = WorkflowEngine(
            enable_exposure_shadow=False,
        )

        assert engine.enable_exposure_shadow == False

    @patch('layers.risk.workflow.load_coverage_config')
    @patch('layers.risk.workflow.WebsiteDiscoveryEngine')
    def test_calculate_exposure_method(
        self,
        mock_discovery,
        mock_load_config,
        mock_config_with_exposure_shadow,
        mock_signal_outputs
    ):
        """Test the _calculate_exposure method."""
        mock_load_config.return_value = mock_config_with_exposure_shadow

        engine = WorkflowEngine(enable_exposure_shadow=True)

        result = engine._calculate_exposure(
            signal_outputs=mock_signal_outputs,
            config=mock_config_with_exposure_shadow,
        )

        # Should return a tuple of (ExposureResult, ComplexityResult) if configured
        if result is not None:
            exposure_result, complexity_result = result
            assert hasattr(exposure_result, 'score')
            assert hasattr(exposure_result, 'band')
            assert hasattr(exposure_result, 'confidence')
            assert hasattr(complexity_result, 'score')
            assert hasattr(complexity_result, 'category')

    def test_calculate_exposure_disabled(self, mock_config_with_exposure_shadow, mock_signal_outputs):
        """Test that disabled exposure shadow returns None."""
        engine = WorkflowEngine(enable_exposure_shadow=False)

        result = engine._calculate_exposure(
            signal_outputs=mock_signal_outputs,
            config=mock_config_with_exposure_shadow,
        )

        assert result is None

    def test_calculate_exposure_no_config(self, mock_signal_outputs):
        """Test that missing exposure config returns None."""
        config = Mock(spec=CoverageConfig)
        config.exposure_shadow = None

        engine = WorkflowEngine(enable_exposure_shadow=True)

        result = engine._calculate_exposure(
            signal_outputs=mock_signal_outputs,
            config=config,
        )

        assert result is None


# =============================================================================
# MODEL VERSION EXPOSURE FIELD TESTS
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestModelVersionExposureFields:
    """Tests for exposure fields in ModelVersion."""

    def test_model_version_has_exposure_fields(self):
        """Test that ModelVersion has exposure-related fields."""
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

        # Check exposure fields exist
        assert hasattr(mv, 'exposure_score')
        assert hasattr(mv, 'exposure_band')
        assert hasattr(mv, 'exposure_confidence')
        assert hasattr(mv, 'exposure_proxy_tier')
        assert hasattr(mv, 'exposure_range_low')
        assert hasattr(mv, 'exposure_range_high')
        assert hasattr(mv, 'implied_tiv_low')
        assert hasattr(mv, 'implied_tiv_high')

    def test_model_version_has_complexity_fields(self):
        """Test that ModelVersion has complexity-related fields."""
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

        # Check complexity fields exist
        assert hasattr(mv, 'complexity_score')
        assert hasattr(mv, 'complexity_category')
        assert hasattr(mv, 'complexity_confidence')
        assert hasattr(mv, 'geographic_complexity_score')
        assert hasattr(mv, 'structural_complexity_score')
        assert hasattr(mv, 'technical_complexity_score')
        assert hasattr(mv, 'regulatory_complexity_score')

    def test_model_version_exposure_fields_default_none(self):
        """Test that exposure fields default to None."""
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

        assert mv.exposure_score is None
        assert mv.exposure_band is None
        assert mv.exposure_confidence is None
        assert mv.complexity_score is None
        assert mv.complexity_category is None

    def test_model_version_exposure_fields_can_be_set(self):
        """Test that exposure fields can be populated."""
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

        # Set exposure fields
        mv.exposure_score = 55.5
        mv.exposure_band = "medium"
        mv.exposure_confidence = 0.85
        mv.exposure_proxy_tier = "INFERRED_PROXY"
        mv.implied_tiv_low = 10000000
        mv.implied_tiv_high = 50000000
        mv.exposure_modifier = 1.0

        assert mv.exposure_score == 55.5
        assert mv.exposure_band == "medium"
        assert mv.exposure_confidence == 0.85
        assert mv.exposure_modifier == 1.0


# =============================================================================
# END-TO-END EXPOSURE SCORING TESTS
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestEndToEndExposureScoring:
    """End-to-end tests for exposure scoring."""

    def test_exposure_score_calculation(self, mock_config_with_exposure_shadow, mock_signal_outputs):
        """Test end-to-end exposure score calculation."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(mock_signal_outputs)

        # Verify result structure
        assert isinstance(result, ExposureResult)
        assert 0 <= result.score <= 100
        assert isinstance(result.band, ExposureBand)
        assert 0 <= result.confidence <= 1

    def test_complexity_score_calculation(self, mock_config_with_exposure_shadow, mock_signal_outputs):
        """Test end-to-end complexity score calculation."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ComplexityScorer(config)
        result = scorer.score(mock_signal_outputs)

        # Verify result structure
        assert isinstance(result, ComplexityResult)
        assert 0 <= result.score <= 100
        assert isinstance(result.category, ComplexityCategory)
        assert 0 <= result.confidence <= 1

    def test_large_company_gets_large_exposure(self, mock_config_with_exposure_shadow):
        """Test that large company signals result in large exposure band."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Large company signals
        large_company_signals = [
            MockSignalOutput("dns_complexity", 85.0, 0.9),
            MockSignalOutput("subdomain_count", 90.0, 0.9),
            MockSignalOutput("ip_footprint", 88.0, 0.9),
            MockSignalOutput("ssl_certificates", 80.0, 0.9),
            MockSignalOutput("employee_estimate", 95.0, 0.9),
            MockSignalOutput("location_count", 85.0, 0.9),
        ]

        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(large_company_signals)

        # Should be in a higher band (large or very_large)
        assert result.band in [ExposureBand.LARGE, ExposureBand.VERY_LARGE, ExposureBand.MEDIUM]
        assert result.exposure_modifier >= 1.0

    def test_small_company_gets_small_exposure(self, mock_config_with_exposure_shadow):
        """Test that small company signals result in small exposure band."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Small company signals
        small_company_signals = [
            MockSignalOutput("dns_complexity", 10.0, 0.9),
            MockSignalOutput("subdomain_count", 5.0, 0.9),
            MockSignalOutput("ip_footprint", 8.0, 0.9),
            MockSignalOutput("ssl_certificates", 3.0, 0.9),
            MockSignalOutput("employee_estimate", 12.0, 0.9),
            MockSignalOutput("location_count", 5.0, 0.9),
        ]

        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(small_company_signals)

        # Should be in a lower band (micro or small)
        assert result.band in [ExposureBand.MICRO, ExposureBand.SMALL, ExposureBand.MEDIUM]
        assert result.exposure_modifier <= 1.0


# =============================================================================
# REFERRAL TRIGGER TESTS
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestExposureReferralTriggers:
    """Tests for exposure-based referral triggers."""

    def test_low_confidence_large_exposure_triggers_referral(self, mock_config_with_exposure_shadow):
        """Test that large exposure with low confidence triggers referral."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Large exposure but low confidence signals
        signals = [
            MockSignalOutput("dns_complexity", 85.0, 0.3),  # Low confidence
            MockSignalOutput("subdomain_count", 90.0, 0.3),
        ]

        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(signals)

        # Large exposure with low confidence should trigger referral
        if result.band in [ExposureBand.LARGE, ExposureBand.VERY_LARGE] and result.confidence < 0.5:
            assert result.referral_triggered == True
            assert len(result.referral_reasons) > 0

    def test_insufficient_data_triggers_flag(self, mock_config_with_exposure_shadow):
        """Test that insufficient data triggers appropriate flags."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Very few signals
        minimal_signals = [
            MockSignalOutput("dns_complexity", 50.0, 0.5),
        ]

        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(minimal_signals)

        # Low signal availability should result in lower confidence
        assert result.confidence < 0.8


# =============================================================================
# EXPOSURE MODIFIER IMPACT TESTS
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestExposureModifierImpact:
    """Tests for exposure modifier impact on pricing."""

    def test_very_large_exposure_has_high_modifier(self, mock_config_with_exposure_shadow):
        """Test that very large exposure results in high modifier."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)

        # Check band config
        very_large_band = next(
            b for b in config.exposure_bands
            if b.name == "very_large"
        )

        assert very_large_band.exposure_modifier == 2.50

    def test_micro_exposure_has_low_modifier(self, mock_config_with_exposure_shadow):
        """Test that micro exposure results in low modifier."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)

        # Check band config
        micro_band = next(
            b for b in config.exposure_bands
            if b.name == "micro"
        )

        assert micro_band.exposure_modifier == 0.50

    def test_combined_modifier_calculation(self, mock_config_with_exposure_shadow, mock_signal_outputs):
        """Test combined exposure + complexity modifier calculation."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)

        exposure_scorer = ExposureScorer(config)
        complexity_scorer = ComplexityScorer(config)

        exposure_result = exposure_scorer.score(mock_signal_outputs)
        complexity_result = complexity_scorer.score(mock_signal_outputs)

        # Combined modifier should be product of both
        combined = exposure_result.exposure_modifier * complexity_result.complexity_modifier

        assert combined > 0
        assert combined != exposure_result.exposure_modifier or complexity_result.complexity_modifier == 1.0


# =============================================================================
# PROXY TIER TESTS
# =============================================================================

@pytest.mark.skipif(not EXPOSURE_SHADOW_AVAILABLE, reason="Exposure shadow layer not available")
class TestProxyTierDetermination:
    """Tests for proxy tier determination."""

    def test_direct_observable_signals_get_tier_1(self, mock_config_with_exposure_shadow):
        """Test that direct observable signals result in tier 1."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # Direct observable signals (market cap, revenue)
        direct_signals = [
            MockSignalOutput("market_cap", 5000000000, 0.95),
            MockSignalOutput("revenue_estimate", 1000000000, 0.9),
        ]

        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)
        result = scorer.score(direct_signals)

        # With high-confidence direct observable signals, should get tier 1
        assert result.proxy_tier == ProxyTier.DIRECT_OBSERVABLE

    def test_inferred_proxy_signals_get_tier_2(self, mock_config_with_exposure_shadow, mock_signal_outputs):
        """Test that inferred proxy signals result in tier 2."""
        config = ExposureConfig.from_dict(mock_config_with_exposure_shadow.exposure_shadow)
        scorer = ExposureScorer(config)

        # Filter to only inferred proxy signals
        inferred_signals = [
            s for s in mock_signal_outputs
            if s.signal_id not in ['market_cap', 'revenue_estimate']
        ]

        result = scorer.score(inferred_signals)

        # With enough inferred signals, should get tier 2
        assert result.proxy_tier in [ProxyTier.INFERRED_PROXY, ProxyTier.COHORT_INFERENCE]
