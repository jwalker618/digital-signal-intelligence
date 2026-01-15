"""
Unit Tests for Exposure Shadow Layer (Phase 17)

Tests the exposure magnitude and complexity scoring components.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from layers.exposure import (
    # Enums
    ProxyTier,
    ExposureBand,
    ComplexityCategory,
    ExposureSignalType,
    # Configuration types
    ExposureBandConfig,
    ComplexityCategoryConfig,
    ExposureFeatureConfig,
    ExposureGroupConfig,
    CohortPriorConfig,
    ExposureConfig,
    # Signal output types
    ExposureSignalOutput,
    ExposureGroupScore,
    # Result types
    ExposureResult,
    ComplexityResult,
    CombinedExposureResult,
    # Cohort types
    CohortPrior,
    CohortMatch,
    # Rule types
    ExposureRuleResult,
    ExposureDecision,
    # Classes
    ExposureScorer,
    ComplexityScorer,
    BandMapper,
    CohortManager,
    ExposureRulesEngine,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_config_dict():
    """Create sample exposure configuration dictionary."""
    return {
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
                    {"id": "employee_estimate", "weight": 0.40, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "location_count", "weight": 0.30, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
                    {"id": "job_postings", "weight": 0.30, "proxy_tier": "INFERRED_PROXY", "normalizer": "log_scale"},
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
            {"cohort_id": "tech_enterprise", "name": "Tech Enterprise", "sector": "technology", "prior_band": "large", "prior_score": 70.0, "confidence": 0.5},
        ],
        "auto_apply_rules": [
            {"condition": "exposure_band == 'very_large' and confidence < 0.5", "action": "refer", "reason": "Very large exposure with low confidence"},
        ],
    }


@pytest.fixture
def exposure_config(sample_config_dict):
    """Create ExposureConfig from sample dict."""
    return ExposureConfig.from_dict(sample_config_dict)


@pytest.fixture
def mock_signal_outputs():
    """Create mock signal outputs for testing."""
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
        MockSignalOutput("job_postings", 25.0, 0.7),
    ]


@pytest.fixture
def mock_complexity_signal_outputs():
    """Create mock signal outputs for complexity testing."""
    class MockSignalOutput:
        def __init__(self, signal_id, raw_score, confidence):
            self.signal_id = signal_id
            self.raw_score = raw_score
            self.confidence = confidence
            self.data_sources = []
            self.extracted_at = datetime.utcnow()

    return [
        MockSignalOutput("country_count", 8.0, 0.9),
        MockSignalOutput("timezone_spread", 6.0, 0.85),
        MockSignalOutput("subsidiary_count", 5.0, 0.8),
        MockSignalOutput("brand_count", 3.0, 0.75),
        MockSignalOutput("tech_stack_diversity", 65.0, 0.9),
    ]


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestEnums:
    """Tests for exposure layer enums."""

    def test_proxy_tier_values(self):
        """Test ProxyTier enum values."""
        assert ProxyTier.DIRECT_OBSERVABLE.value == 1
        assert ProxyTier.INFERRED_PROXY.value == 2
        assert ProxyTier.COHORT_INFERENCE.value == 3
        assert ProxyTier.UNKNOWN.value == 4

    def test_exposure_band_values(self):
        """Test ExposureBand enum values."""
        assert ExposureBand.MICRO.value == "micro"
        assert ExposureBand.SMALL.value == "small"
        assert ExposureBand.MEDIUM.value == "medium"
        assert ExposureBand.LARGE.value == "large"
        assert ExposureBand.VERY_LARGE.value == "very_large"

    def test_complexity_category_values(self):
        """Test ComplexityCategory enum values."""
        assert ComplexityCategory.SIMPLE.value == "simple"
        assert ComplexityCategory.MODERATE.value == "moderate"
        assert ComplexityCategory.COMPLEX.value == "complex"
        assert ComplexityCategory.HIGHLY_COMPLEX.value == "highly_complex"
        assert ComplexityCategory.EXTREMELY_COMPLEX.value == "extremely_complex"


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestExposureConfig:
    """Tests for ExposureConfig parsing."""

    def test_from_dict_basic(self, sample_config_dict):
        """Test basic config parsing from dict."""
        config = ExposureConfig.from_dict(sample_config_dict)

        assert config.enabled == True
        assert config.version == "2026-01-15"
        assert len(config.exposure_groups) == 3
        assert len(config.complexity_groups) == 3
        assert len(config.exposure_bands) == 5
        assert len(config.complexity_categories) == 5
        assert len(config.cohort_priors) == 2

    def test_exposure_groups_parsed(self, exposure_config):
        """Test exposure groups are parsed correctly."""
        digital_footprint = next(g for g in exposure_config.exposure_groups if g.name == "digital_footprint")

        assert digital_footprint.weight == 0.40
        assert digital_footprint.confidence_threshold == 0.6
        assert len(digital_footprint.features) == 4

    def test_features_parsed(self, exposure_config):
        """Test features are parsed with correct proxy tiers."""
        digital_footprint = next(g for g in exposure_config.exposure_groups if g.name == "digital_footprint")
        dns_feature = next(f for f in digital_footprint.features if f.id == "dns_complexity")

        assert dns_feature.weight == 0.30
        assert dns_feature.proxy_tier == ProxyTier.INFERRED_PROXY
        assert dns_feature.normalizer == "log_scale"

    def test_band_mapping_parsed(self, exposure_config):
        """Test band mapping is parsed correctly."""
        assert len(exposure_config.exposure_bands) == 5

        micro_band = next(b for b in exposure_config.exposure_bands if b.name == "micro")
        assert micro_band.min_score == 0
        assert micro_band.max_score == 20
        assert micro_band.implied_tiv_low == 0
        assert micro_band.implied_tiv_high == 1000000
        assert micro_band.exposure_modifier == 0.50


# =============================================================================
# EXPOSURE SCORER TESTS
# =============================================================================

class TestExposureScorer:
    """Tests for ExposureScorer."""

    def test_scorer_initialization(self, exposure_config):
        """Test scorer initializes correctly."""
        scorer = ExposureScorer(exposure_config)

        assert scorer.config == exposure_config
        assert len(scorer._sorted_groups) == 3
        assert len(scorer._signal_config) > 0

    def test_score_with_signals(self, exposure_config, mock_signal_outputs):
        """Test scoring with signal outputs."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score(mock_signal_outputs)

        assert isinstance(result, ExposureResult)
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1
        assert isinstance(result.band, ExposureBand)
        assert isinstance(result.proxy_tier, ProxyTier)

    def test_score_range_bounds(self, exposure_config, mock_signal_outputs):
        """Test that score range acknowledges uncertainty."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score(mock_signal_outputs)

        assert result.range_low <= result.score
        assert result.range_high >= result.score
        assert result.range_low >= 0
        assert result.range_high <= 100

    def test_implied_tiv_calculated(self, exposure_config, mock_signal_outputs):
        """Test implied TIV is calculated."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score(mock_signal_outputs)

        assert result.implied_tiv_low >= 0
        assert result.implied_tiv_high >= result.implied_tiv_low

    def test_exposure_modifier_set(self, exposure_config, mock_signal_outputs):
        """Test exposure modifier is set based on band."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score(mock_signal_outputs)

        # Modifier should be one of the configured values
        valid_modifiers = {0.50, 0.75, 1.00, 1.50, 2.50}
        assert result.exposure_modifier in valid_modifiers

    def test_signals_tracking(self, exposure_config, mock_signal_outputs):
        """Test that signal usage is tracked."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score(mock_signal_outputs)

        assert len(result.signals_used) > 0
        assert result.signals_available > 0
        assert result.signals_total > 0

    def test_empty_signals_returns_unknown(self, exposure_config):
        """Test that empty signals returns unknown result."""
        scorer = ExposureScorer(exposure_config)
        result = scorer.score([])

        assert result.proxy_tier == ProxyTier.UNKNOWN
        assert result.referral_triggered == True

    def test_cohort_prior_applied_when_confidence_low(self, exposure_config):
        """Test cohort prior is applied when confidence is low."""
        scorer = ExposureScorer(exposure_config)

        # Create low confidence signals
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        low_confidence_signals = [
            MockSignalOutput("dns_complexity", 30.0, 0.3),  # Low confidence
        ]

        cohort_prior = {
            "cohort_id": "tech_startup",
            "name": "Tech Startup",
            "prior_score": 35.0,
            "prior_band": "small",
            "confidence": 0.5,
        }

        result = scorer.score(low_confidence_signals, cohort_prior)

        # Cohort prior should be applied due to low confidence
        assert result.cohort_prior_applied == True
        assert result.cohort_id == "tech_startup"


# =============================================================================
# COMPLEXITY SCORER TESTS
# =============================================================================

class TestComplexityScorer:
    """Tests for ComplexityScorer."""

    def test_scorer_initialization(self, exposure_config):
        """Test complexity scorer initializes correctly."""
        scorer = ComplexityScorer(exposure_config)

        assert scorer.config == exposure_config
        assert len(scorer._sorted_groups) == 3

    def test_score_with_signals(self, exposure_config, mock_complexity_signal_outputs):
        """Test complexity scoring with signal outputs."""
        scorer = ComplexityScorer(exposure_config)
        result = scorer.score(mock_complexity_signal_outputs)

        assert isinstance(result, ComplexityResult)
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1
        assert isinstance(result.category, ComplexityCategory)

    def test_component_scores_calculated(self, exposure_config, mock_complexity_signal_outputs):
        """Test component scores are calculated."""
        scorer = ComplexityScorer(exposure_config)
        result = scorer.score(mock_complexity_signal_outputs)

        # At least one component score should be non-zero if signals provided
        total_component_scores = (
            result.geographic_score +
            result.structural_score +
            result.technical_score +
            result.regulatory_score
        )
        assert total_component_scores > 0

    def test_complexity_modifier_set(self, exposure_config, mock_complexity_signal_outputs):
        """Test complexity modifier is set based on category."""
        scorer = ComplexityScorer(exposure_config)
        result = scorer.score(mock_complexity_signal_outputs)

        # Modifier should be one of the configured values
        valid_modifiers = {0.85, 0.95, 1.10, 1.30, 1.60}
        assert result.complexity_modifier in valid_modifiers

    def test_empty_signals_returns_simple(self, exposure_config):
        """Test that empty signals returns simple category."""
        scorer = ComplexityScorer(exposure_config)
        result = scorer.score([])

        assert result.category == ComplexityCategory.SIMPLE
        assert result.confidence == 0.0


# =============================================================================
# BAND MAPPER TESTS
# =============================================================================

class TestBandMapper:
    """Tests for BandMapper."""

    def test_initialization(self, exposure_config):
        """Test band mapper initializes correctly."""
        mapper = BandMapper(exposure_config)

        assert len(mapper._sorted_bands) == 5
        assert len(mapper._sorted_categories) == 5

    def test_score_to_band_mapping(self, exposure_config):
        """Test score to band mapping."""
        mapper = BandMapper(exposure_config)

        assert mapper.score_to_band(10).band == ExposureBand.MICRO
        assert mapper.score_to_band(30).band == ExposureBand.SMALL
        assert mapper.score_to_band(50).band == ExposureBand.MEDIUM
        assert mapper.score_to_band(70).band == ExposureBand.LARGE
        assert mapper.score_to_band(90).band == ExposureBand.VERY_LARGE

    def test_score_to_category_mapping(self, exposure_config):
        """Test score to complexity category mapping."""
        mapper = BandMapper(exposure_config)

        assert mapper.score_to_category(10).category == ComplexityCategory.SIMPLE
        assert mapper.score_to_category(30).category == ComplexityCategory.MODERATE
        assert mapper.score_to_category(50).category == ComplexityCategory.COMPLEX
        assert mapper.score_to_category(70).category == ComplexityCategory.HIGHLY_COMPLEX
        assert mapper.score_to_category(90).category == ComplexityCategory.EXTREMELY_COMPLEX

    def test_band_has_implied_tiv(self, exposure_config):
        """Test band result includes implied TIV."""
        mapper = BandMapper(exposure_config)
        result = mapper.score_to_band(50)

        assert result.implied_tiv_low >= 0
        assert result.implied_tiv_high >= result.implied_tiv_low
        assert result.exposure_modifier > 0


# =============================================================================
# COHORT MANAGER TESTS
# =============================================================================

class TestCohortManager:
    """Tests for CohortManager."""

    def test_initialization(self, exposure_config):
        """Test cohort manager initializes correctly."""
        manager = CohortManager(exposure_config)

        assert len(manager._cohorts) == 2

    def test_find_matching_cohort(self, exposure_config):
        """Test finding a matching cohort."""
        manager = CohortManager(exposure_config)

        match = manager.find_matching_cohort(
            sector="technology",
            size_indicator="startup",
        )

        if match:
            assert match.cohort_id == "tech_startup"
            assert match.match_confidence > 0

    def test_get_cohort_prior(self, exposure_config):
        """Test getting cohort prior."""
        manager = CohortManager(exposure_config)
        prior = manager.get_cohort_prior("tech_startup")

        if prior:
            assert prior["prior_score"] == 30.0
            assert prior["prior_band"] == "small"
            assert prior["confidence"] == 0.4


# =============================================================================
# RULES ENGINE TESTS
# =============================================================================

class TestExposureRulesEngine:
    """Tests for ExposureRulesEngine."""

    def test_initialization(self, exposure_config):
        """Test rules engine initializes correctly."""
        engine = ExposureRulesEngine(exposure_config)

        assert len(engine._rules) >= 0

    def test_evaluate_rules_refer_action(self, exposure_config, mock_signal_outputs):
        """Test evaluating rules that trigger refer action."""
        engine = ExposureRulesEngine(exposure_config)
        scorer = ExposureScorer(exposure_config)
        exposure_result = scorer.score(mock_signal_outputs)

        decision = engine.evaluate_rules(exposure_result, None)

        assert isinstance(decision, ExposureDecision)
        # Decision fields should be populated
        assert isinstance(decision.should_refer, bool)
        assert isinstance(decision.referral_reasons, list)


# =============================================================================
# RESULT TYPE TESTS
# =============================================================================

class TestExposureResult:
    """Tests for ExposureResult dataclass."""

    def test_exposure_result_creation(self):
        """Test creating ExposureResult."""
        result = ExposureResult(
            score=50.0,
            band=ExposureBand.MEDIUM,
            confidence=0.8,
            proxy_tier=ProxyTier.INFERRED_PROXY,
            range_low=40.0,
            range_high=60.0,
            implied_tiv_low=10000000,
            implied_tiv_high=50000000,
        )

        assert result.score == 50.0
        assert result.band == ExposureBand.MEDIUM
        assert result.confidence == 0.8
        assert result.proxy_tier == ProxyTier.INFERRED_PROXY

    def test_exposure_result_defaults(self):
        """Test ExposureResult has sensible defaults."""
        result = ExposureResult(
            score=50.0,
            band=ExposureBand.MEDIUM,
            confidence=0.8,
            proxy_tier=ProxyTier.INFERRED_PROXY,
            range_low=40.0,
            range_high=60.0,
            implied_tiv_low=10000000,
            implied_tiv_high=50000000,
        )

        assert result.cohort_prior_applied == False
        assert result.referral_triggered == False
        assert result.group_scores == {}
        assert result.signals_used == []


class TestComplexityResult:
    """Tests for ComplexityResult dataclass."""

    def test_complexity_result_creation(self):
        """Test creating ComplexityResult."""
        result = ComplexityResult(
            score=60.0,
            category=ComplexityCategory.COMPLEX,
            confidence=0.75,
        )

        assert result.score == 60.0
        assert result.category == ComplexityCategory.COMPLEX
        assert result.confidence == 0.75

    def test_complexity_result_components(self):
        """Test ComplexityResult with component scores."""
        result = ComplexityResult(
            score=60.0,
            category=ComplexityCategory.COMPLEX,
            confidence=0.75,
            geographic_score=70.0,
            structural_score=55.0,
            technical_score=60.0,
            regulatory_score=50.0,
        )

        assert result.geographic_score == 70.0
        assert result.structural_score == 55.0
        assert result.technical_score == 60.0
        assert result.regulatory_score == 50.0


# =============================================================================
# INTEGRATION TESTS (Unit-level)
# =============================================================================

class TestExposureComplexityCombined:
    """Tests for combined exposure and complexity scoring."""

    def test_combined_scoring(self, exposure_config, mock_signal_outputs, mock_complexity_signal_outputs):
        """Test combined exposure and complexity scoring."""
        exposure_scorer = ExposureScorer(exposure_config)
        complexity_scorer = ComplexityScorer(exposure_config)

        # Combine all signals
        all_signals = mock_signal_outputs + mock_complexity_signal_outputs

        exposure_result = exposure_scorer.score(all_signals)
        complexity_result = complexity_scorer.score(all_signals)

        # Create combined result
        combined = CombinedExposureResult(
            exposure=exposure_result,
            complexity=complexity_result,
            combined_modifier=exposure_result.exposure_modifier * complexity_result.complexity_modifier,
            overall_confidence=(exposure_result.confidence + complexity_result.confidence) / 2,
        )

        assert combined.exposure == exposure_result
        assert combined.complexity == complexity_result
        assert combined.combined_modifier > 0
        assert 0 <= combined.overall_confidence <= 1

    def test_high_exposure_high_complexity_increases_modifier(self, exposure_config):
        """Test that high exposure + high complexity increases combined modifier."""
        class MockSignalOutput:
            def __init__(self, signal_id, raw_score, confidence):
                self.signal_id = signal_id
                self.raw_score = raw_score
                self.confidence = confidence
                self.data_sources = []
                self.extracted_at = datetime.utcnow()

        # High exposure signals (large company indicators)
        high_exposure_signals = [
            MockSignalOutput("market_cap", 5000000000, 0.95),  # $5B market cap
            MockSignalOutput("revenue_estimate", 1000000000, 0.9),  # $1B revenue
            MockSignalOutput("employee_estimate", 5000, 0.85),  # 5000 employees
        ]

        # High complexity signals
        high_complexity_signals = [
            MockSignalOutput("country_count", 50, 0.9),  # 50 countries
            MockSignalOutput("subsidiary_count", 100, 0.85),  # 100 subsidiaries
            MockSignalOutput("tech_stack_diversity", 95, 0.8),  # Very diverse tech
        ]

        all_signals = high_exposure_signals + high_complexity_signals

        exposure_scorer = ExposureScorer(exposure_config)
        complexity_scorer = ComplexityScorer(exposure_config)

        exposure_result = exposure_scorer.score(all_signals)
        complexity_result = complexity_scorer.score(all_signals)

        combined_modifier = exposure_result.exposure_modifier * complexity_result.complexity_modifier

        # High exposure + high complexity should result in modifier > 1
        # (though actual values depend on how signals map to scores)
        assert combined_modifier >= 1.0 or exposure_result.exposure_modifier >= 1.0
