"""
Tests for DSI Multi-Coverage Orchestration (Phase 10)

Tests multi-coverage pricing, locale detection, and results aggregation.
"""

import pytest
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Optional

from orchestration import (
    # Types
    MultiCoverageRequest,
    MultiCoverageResult,
    ExecutionPlan,
    PlannedRun,
    CoverageResult,
    ExecutionStatus,
    LocaleDetectionMode,
    PackageDiscount,
    OrchestrationConfig,
    SharedSignalCache,
    # Components
    MultiCoverageOrchestrator,
    LocaleDetector,
    LocaleDetectorConfig,
    LocaleMatch,
    ResultsAggregator,
    AggregatedAnalysis,
    summarize_result,
)


# =============================================================================
# MOCK OBJECTS
# =============================================================================

@dataclass
class MockWorkflowResult:
    """Mock workflow result for testing."""
    entity_id: str
    coverage: str
    final_premium: float = 50000.0
    dsi_score: int = 750
    tier: int = 2
    referred: bool = False
    signals_executed: int = 20
    signals_from_cache: int = 5


@dataclass
class MockDiscoveryResult:
    """Mock discovery result for testing."""
    domain: str = "example.com"
    headquarters: Optional[str] = None
    registration_country: Optional[str] = None
    address: Optional[str] = None
    company_info: Optional[dict] = None


def mock_workflow_factory(coverage: str, locale: str, shared_cache=None):
    """Factory that creates mock workflows."""
    class MockWorkflow:
        def run(self, entity_name: str, domain: str = None, submission_data=None):
            return MockWorkflowResult(
                entity_id=entity_name,
                coverage=coverage,
                final_premium=50000 + (ord(coverage[0]) * 1000),
            )
    return MockWorkflow()


# =============================================================================
# MULTI-COVERAGE REQUEST TESTS
# =============================================================================

class TestMultiCoverageRequest:
    """Tests for MultiCoverageRequest."""

    def test_default_request(self):
        """Should create request with defaults."""
        request = MultiCoverageRequest(entity_name="Test Corp")

        assert request.entity_name == "Test Corp"
        assert request.coverages is None  # Auto-detect
        assert request.locales is None  # Auto-detect
        assert request.parallel is True
        assert request.share_cache is True

    def test_explicit_coverages(self):
        """Should accept explicit coverages."""
        request = MultiCoverageRequest(
            entity_name="Test Corp",
            coverages=["fi", "cyber", "do"],
            locales=["US"],
        )

        assert request.coverages == ["fi", "cyber", "do"]
        assert request.locales == ["US"]

    def test_cost_control_options(self):
        """Should configure cost control."""
        request = MultiCoverageRequest(
            entity_name="Test Corp",
            max_cost_units=100,
            require_approval_above=25,
        )

        assert request.max_cost_units == 100
        assert request.require_approval_above == 25


# =============================================================================
# EXECUTION PLAN TESTS
# =============================================================================

class TestExecutionPlan:
    """Tests for ExecutionPlan."""

    def test_plan_properties(self):
        """Should calculate plan properties."""
        plan = ExecutionPlan(
            runs=[
                PlannedRun(coverage="fi", locale="US", configuration="fi_us", estimated_signals=25, estimated_cost=25),
                PlannedRun(coverage="fi", locale="UK", configuration="fi_uk", estimated_signals=25, estimated_cost=25),
                PlannedRun(coverage="cyber", locale="US", configuration="cyber_us", estimated_signals=20, estimated_cost=20),
            ],
            estimated_cost_units=60,
            estimated_duration_seconds=15.0,
            shared_signals=["company_profile"],
            requires_approval=True,
        )

        assert plan.total_runs == 3
        assert set(plan.coverages) == {"fi", "cyber"}
        assert set(plan.locales) == {"US", "UK"}


class TestPlannedRun:
    """Tests for PlannedRun."""

    def test_auto_run_id(self):
        """Should auto-generate run ID."""
        run = PlannedRun(
            coverage="fi",
            locale="US",
            configuration="fi_us",
            estimated_signals=25,
            estimated_cost=25,
        )

        assert run.run_id == "fi_US"
        assert run.status == ExecutionStatus.PENDING


# =============================================================================
# ORCHESTRATOR TESTS
# =============================================================================

class TestMultiCoverageOrchestrator:
    """Tests for MultiCoverageOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for testing."""
        return MultiCoverageOrchestrator(
            workflow_factory=mock_workflow_factory,
            config=OrchestrationConfig.default(),
        )

    def test_create_plan_explicit_coverages(self, orchestrator):
        """Should create plan for explicit coverages."""
        request = MultiCoverageRequest(
            entity_name="Test Bank",
            coverages=["fi", "do"],
            locales=["US"],
        )

        plan = orchestrator.create_plan(request)

        assert plan.total_runs == 2
        assert len(plan.runs) == 2
        assert set(r.coverage for r in plan.runs) == {"fi", "do"}

    def test_create_plan_multi_locale(self, orchestrator):
        """Should create plan for multiple locales."""
        request = MultiCoverageRequest(
            entity_name="Global Corp",
            coverages=["cyber"],
            locales=["US", "UK", "EU"],
        )

        plan = orchestrator.create_plan(request)

        assert plan.total_runs == 3
        assert set(r.locale for r in plan.runs) == {"US", "UK", "EU"}

    def test_create_plan_shared_signals(self, orchestrator):
        """Should identify shared signals."""
        request = MultiCoverageRequest(
            entity_name="Test Corp",
            coverages=["fi", "cyber", "do"],
            locales=["US"],
        )

        plan = orchestrator.create_plan(request)

        assert len(plan.shared_signals) > 0
        assert "company_profile" in plan.shared_signals

    def test_create_plan_approval_threshold(self, orchestrator):
        """Should flag plans requiring approval."""
        request = MultiCoverageRequest(
            entity_name="Complex Corp",
            coverages=["fi", "cyber", "do", "pi"],
            locales=["US", "UK"],
            require_approval_above=10,  # Low threshold
        )

        plan = orchestrator.create_plan(request)

        assert plan.requires_approval is True

    def test_execute_basic(self, orchestrator):
        """Should execute multi-coverage pricing."""
        request = MultiCoverageRequest(
            entity_name="Test Bank",
            coverages=["fi", "cyber"],
            locales=["US"],
        )

        result = orchestrator.execute(request)

        assert result.entity_name == "Test Bank"
        assert result.total_runs == 2
        assert result.successful_runs == 2
        assert result.failed_runs == 0

    def test_execute_parallel(self, orchestrator):
        """Should execute runs in parallel."""
        request = MultiCoverageRequest(
            entity_name="Test Corp",
            coverages=["fi", "cyber", "do"],
            locales=["US"],
            parallel=True,
        )

        result = orchestrator.execute(request)

        assert result.successful_runs == 3

    def test_execute_sequential(self, orchestrator):
        """Should execute runs sequentially."""
        request = MultiCoverageRequest(
            entity_name="Test Corp",
            coverages=["fi", "cyber"],
            locales=["US"],
            parallel=False,
        )

        result = orchestrator.execute(request)

        assert result.successful_runs == 2

    def test_execute_with_plan(self, orchestrator):
        """Should execute with pre-created plan."""
        request = MultiCoverageRequest(
            entity_name="Planned Corp",
            coverages=["fi"],
            locales=["US"],
        )

        plan = orchestrator.create_plan(request)
        plan.approved = True

        result = orchestrator.execute(request, plan=plan)

        assert result.successful_runs == 1

    def test_approve_plan(self, orchestrator):
        """Should approve execution plan."""
        request = MultiCoverageRequest(
            entity_name="Approval Corp",
            coverages=["fi"],
            locales=["US"],
        )

        plan = orchestrator.create_plan(request)
        assert plan.approved is False

        approved = orchestrator.approve_plan(plan, "test_user")
        assert approved.approved is True
        assert approved.approved_by == "test_user"


# =============================================================================
# LOCALE DETECTION TESTS
# =============================================================================

class TestLocaleDetector:
    """Tests for LocaleDetector."""

    @pytest.fixture
    def detector(self):
        """Create locale detector for testing."""
        return LocaleDetector()

    def test_detect_from_tld_us(self, detector):
        """Should detect US from .com domain."""
        discovery = MockDiscoveryResult(domain="example.com")

        locale = detector.detect_locale(discovery)

        assert locale == "US"

    def test_detect_from_tld_uk(self, detector):
        """Should detect UK from .co.uk domain."""
        discovery = MockDiscoveryResult(domain="example.co.uk")

        locale = detector.detect_locale(discovery)

        assert locale == "UK"

    def test_detect_from_headquarters(self, detector):
        """Should detect locale from headquarters."""
        discovery = MockDiscoveryResult(
            domain="example.com",
            headquarters="London, United Kingdom",
        )

        matches = detector.detect_locales(discovery)

        # Should find UK from headquarters with high confidence
        uk_match = next((m for m in matches if m.locale == "UK"), None)
        assert uk_match is not None
        assert uk_match.source == "headquarters"

    def test_detect_from_registration(self, detector):
        """Should detect locale from registration country."""
        discovery = MockDiscoveryResult(
            domain="example.de",
            registration_country="Germany",
        )

        matches = detector.detect_locales(discovery)

        eu_match = next((m for m in matches if m.locale == "EU"), None)
        assert eu_match is not None

    def test_fallback_locale(self, detector):
        """Should use fallback when no detection."""
        discovery = MockDiscoveryResult(domain="example.xyz")

        locale = detector.detect_locale(discovery)

        assert locale == "US"  # Default fallback

    def test_detect_all_locales(self, detector):
        """Should return all detected locales."""
        discovery = MockDiscoveryResult(
            domain="example.co.uk",
            headquarters="Germany",
        )

        matches = detector.detect_locales(discovery, max_locales=5)

        assert len(matches) >= 2
        locales = [m.locale for m in matches]
        assert "UK" in locales
        assert "EU" in locales

    def test_get_locale_info(self, detector):
        """Should return locale information."""
        info = detector.get_locale_info("UK")

        assert info["name"] == "United Kingdom"
        assert info["currency"] == "GBP"


class TestLocaleMatch:
    """Tests for LocaleMatch."""

    def test_locale_match_creation(self):
        """Should create locale match."""
        match = LocaleMatch(
            locale="US",
            confidence=0.9,
            source="tld",
        )

        assert match.locale == "US"
        assert match.confidence == 0.9
        assert match.source == "tld"


# =============================================================================
# COVERAGE RESULT TESTS
# =============================================================================

class TestCoverageResult:
    """Tests for CoverageResult."""

    def test_success_property(self):
        """Should determine success correctly."""
        result = CoverageResult(
            coverage="fi",
            locale="US",
            configuration="fi_us",
            status=ExecutionStatus.COMPLETED,
        )

        assert result.success is True

    def test_failure_property(self):
        """Should detect failure."""
        result = CoverageResult(
            coverage="fi",
            locale="US",
            configuration="fi_us",
            status=ExecutionStatus.FAILED,
            error="Connection error",
        )

        assert result.success is False

    def test_cache_hit_rate(self):
        """Should calculate cache hit rate."""
        result = CoverageResult(
            coverage="fi",
            locale="US",
            configuration="fi_us",
            status=ExecutionStatus.COMPLETED,
            signals_executed=15,
            signals_from_cache=5,
        )

        assert result.cache_hit_rate == 0.25  # 5 / 20


# =============================================================================
# MULTI-COVERAGE RESULT TESTS
# =============================================================================

class TestMultiCoverageResult:
    """Tests for MultiCoverageResult."""

    def test_success_property(self):
        """Should determine overall success."""
        result = MultiCoverageResult(
            entity_name="Test Corp",
            successful_runs=3,
            failed_runs=0,
        )

        assert result.success is True

    def test_partial_success(self):
        """Should detect partial success."""
        result = MultiCoverageResult(
            entity_name="Test Corp",
            successful_runs=2,
            failed_runs=1,
        )

        assert result.success is False
        assert result.partial_success is True

    def test_get_result_by_coverage(self):
        """Should get result by coverage."""
        result = MultiCoverageResult(
            entity_name="Test Corp",
            coverage_results={
                "fi_US": CoverageResult(coverage="fi", locale="US", configuration="fi_us"),
                "cyber_US": CoverageResult(coverage="cyber", locale="US", configuration="cyber_us"),
            },
            best_locale_per_coverage={"fi": "US", "cyber": "US"},
        )

        fi_result = result.get_result("fi")
        assert fi_result is not None
        assert fi_result.coverage == "fi"


# =============================================================================
# RESULTS AGGREGATOR TESTS
# =============================================================================

class TestResultsAggregator:
    """Tests for ResultsAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator for testing."""
        return ResultsAggregator()

    @pytest.fixture
    def sample_result(self):
        """Create sample multi-coverage result."""
        return MultiCoverageResult(
            entity_name="Test Bank",
            coverage_results={
                "fi_US": CoverageResult(
                    coverage="fi",
                    locale="US",
                    configuration="fi_us",
                    status=ExecutionStatus.COMPLETED,
                    workflow_result=MockWorkflowResult(entity_id="Test", coverage="fi", tier=2),
                ),
                "do_US": CoverageResult(
                    coverage="do",
                    locale="US",
                    configuration="do_us",
                    status=ExecutionStatus.COMPLETED,
                    workflow_result=MockWorkflowResult(entity_id="Test", coverage="do", tier=2),
                ),
            },
            individual_premiums={"fi": 50000, "do": 40000},
            combined_premium=81000,  # 10% discount
            package_discount=0.10,
            total_savings=9000,
            recommended_package=["fi", "do"],
            successful_runs=2,
            failed_runs=0,
        )

    def test_aggregate_basic(self, aggregator, sample_result):
        """Should aggregate results."""
        analysis = aggregator.aggregate(sample_result)

        assert analysis.total_coverages == 2
        assert analysis.successful_coverages == 2
        assert analysis.total_premium == 90000
        assert analysis.discounted_premium == 81000

    def test_find_best_package(self, aggregator):
        """Should find best package discount."""
        package, discount, savings = aggregator.find_best_package(
            available_coverages=["fi", "do", "cyber"],
            premiums={"fi": 50000, "do": 40000, "cyber": 30000},
        )

        # Should match the fi+do+cyber package with 10% discount
        assert discount == 0.10
        assert savings > 0

    def test_tier_consistency(self, aggregator, sample_result):
        """Should calculate tier consistency."""
        analysis = aggregator.aggregate(sample_result)

        # Same tiers = high consistency
        assert analysis.tier_consistency > 0.9


# =============================================================================
# SHARED SIGNAL CACHE TESTS
# =============================================================================

class TestSharedSignalCache:
    """Tests for SharedSignalCache."""

    def test_cache_operations(self):
        """Should cache and retrieve signals."""
        cache = SharedSignalCache(entity_id="test")

        # Miss
        result = cache.get("signal_1")
        assert result is None

        # Set
        cache.set("signal_1", {"score": 85})

        # Hit
        result = cache.get("signal_1")
        assert result == {"score": 85}

    def test_hit_rate(self):
        """Should calculate hit rate."""
        cache = SharedSignalCache(entity_id="test")

        cache.set("signal_1", {"score": 85})

        cache.get("signal_1")  # Hit
        cache.get("signal_1")  # Hit
        cache.get("signal_2")  # Miss

        assert cache.hit_rate == pytest.approx(0.67, abs=0.01)

    def test_cache_size(self):
        """Should track cache size."""
        cache = SharedSignalCache(entity_id="test")

        cache.set("signal_1", {"score": 85})
        cache.set("signal_2", {"score": 90})

        assert cache.size == 2


# =============================================================================
# ORCHESTRATION CONFIG TESTS
# =============================================================================

class TestOrchestrationConfig:
    """Tests for OrchestrationConfig."""

    def test_default_config(self):
        """Should create default config."""
        config = OrchestrationConfig.default()

        assert "cyber" in config.default_coverages
        assert config.approval_threshold == 50
        assert len(config.package_discounts) > 0

    def test_package_discount_applies(self):
        """Should check if package discount applies."""
        discount = PackageDiscount(
            coverages=["fi", "do"],
            discount_rate=0.05,
        )

        assert discount.applies_to(["fi", "do"]) is True
        assert discount.applies_to(["fi", "do", "cyber"]) is True
        assert discount.applies_to(["fi", "cyber"]) is False


# =============================================================================
# SUMMARIZE RESULT TESTS
# =============================================================================

class TestSummarizeResult:
    """Tests for summarize_result helper."""

    def test_summarize(self):
        """Should create summary dict."""
        result = MultiCoverageResult(
            entity_name="Test Corp",
            discovered_domain="test.com",
            detected_locale="US",
            individual_premiums={"fi": 50000},
            combined_premium=50000,
            package_discount=0.0,
            total_savings=0,
            successful_runs=1,
            failed_runs=0,
            cache_hit_rate=0.25,
            total_duration_seconds=5.5,
        )

        summary = summarize_result(result)

        assert summary["entity"] == "Test Corp"
        assert summary["domain"] == "test.com"
        assert summary["coverages_priced"] == 1
        assert "25.0%" in summary["cache_efficiency"]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestOrchestrationIntegration:
    """Integration tests for orchestration workflow."""

    def test_full_workflow(self):
        """Test complete multi-coverage workflow."""
        # 1. Create orchestrator
        orchestrator = MultiCoverageOrchestrator(
            workflow_factory=mock_workflow_factory,
        )

        # 2. Create locale detector
        detector = LocaleDetector()

        # 3. Create request
        request = MultiCoverageRequest(
            entity_name="Integration Bank",
            domain_hint="integration.co.uk",
            coverages=["fi", "do"],
        )

        # 4. Detect locale
        discovery = MockDiscoveryResult(domain="integration.co.uk")
        locale = detector.detect_locale(discovery)
        assert locale == "UK"

        # 5. Create plan
        plan = orchestrator.create_plan(request, discovery)
        assert len(plan.runs) > 0

        # 6. Execute
        result = orchestrator.execute(request, plan, discovery)
        assert result.success or result.partial_success

        # 7. Aggregate
        aggregator = ResultsAggregator()
        analysis = aggregator.aggregate(result)
        assert analysis.total_coverages > 0

        # 8. Summarize
        summary = summarize_result(result)
        assert "entity" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
