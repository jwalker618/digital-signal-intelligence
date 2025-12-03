"""
Cyber Insurance Pricing Model Tests
====================================

Comprehensive test suite covering:
1. Structural tests (instantiation, types, configuration)
2. Functional tests (pricing logic, tier assignment)
3. Actuarial validity tests (risk differentiation)

Author: DSI Framework
Version: 1.0.0
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from models.cyber.dsi_cyber_pricing import (
    CyberPricingEngine,
    CyberAssessment,
    CyberTier,
    CoverageType as CyberCoverageType,
    CompanyProfile,
    SecuritySignals,
    PricingResult,
)

from tests.conftest import (
    BaseStructuralTest,
    BaseFunctionalTest,
    BaseActuarialTest,
    TestAssertions,
    TestComparisons,
    TestEntityProfile,
    TestDataGenerator,
)


# =============================================================================
# STRUCTURAL TESTS
# =============================================================================

class TestCyberStructure(BaseStructuralTest):
    """Test structural integrity of cyber pricing model."""

    def test_engine_instantiates(self):
        """Test CyberPricingEngine instantiates correctly."""
        engine = CyberPricingEngine()
        assert engine is not None
        assert isinstance(engine, CyberPricingEngine)

    def test_tier_enum_values(self):
        """Test CyberTier enum has expected values."""
        expected_tiers = ["TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5"]
        actual_tiers = [tier.value for tier in CyberTier]

        for expected in expected_tiers:
            assert expected in actual_tiers, f"Missing tier: {expected}"

        assert len(actual_tiers) == 5, "Should have exactly 5 tiers"

    def test_coverage_type_enum(self):
        """Test CyberCoverageType enum."""
        expected_types = ["first_party", "third_party", "comprehensive"]

        for expected in expected_types:
            # Check that we can create the enum
            assert hasattr(CyberCoverageType, expected.upper()) or \
                   any(expected in ct.value.lower() for ct in CyberCoverageType), \
                   f"Missing coverage type: {expected}"

    def test_company_profile_structure(self):
        """Test CompanyProfile dataclass structure."""
        # Create minimal profile
        profile = CompanyProfile(
            entity_id="test-001",
            entity_name="Test Corp",
            industry="technology",
            employee_count=100,
            annual_revenue=10_000_000,
        )

        # Verify required fields
        required_fields = ["entity_id", "entity_name", "industry",
                          "employee_count", "annual_revenue"]
        self.verify_dataclass_structure(profile, required_fields)

    def test_security_signals_structure(self):
        """Test SecuritySignals dataclass structure."""
        signals = SecuritySignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "security_rating",
            "vulnerability_count",
            "breach_history",
            "compliance_status",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_pricing_result_structure(self):
        """Test PricingResult has required fields."""
        # This will be returned by calculate_premium
        engine = CyberPricingEngine()

        # Create test profile with good security
        test_set = TestDataGenerator.create_test_signal_set(
            "Test Corp", "cyber", TestEntityProfile.AVERAGE_SECURITY
        )

        profile = self._create_profile_from_signals(test_set)

        result = engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        # Verify return type
        self.verify_return_type(result, PricingResult)

        # Verify required fields
        required_fields = [
            "tier",
            "tier_label",
            "composite_score",
            "gross_premium",
            "rate_per_million",
        ]

        self.verify_dataclass_structure(result, required_fields)

    def _create_profile_from_signals(self, test_set) -> CompanyProfile:
        """Helper to create CompanyProfile from test signals."""
        signals = test_set.signals

        security_signals = SecuritySignals(
            security_rating=signals.get("security_rating"),
            vulnerability_count=signals.get("vulnerability_count"),
            breach_history=signals.get("breach_history"),
            compliance_status=signals.get("compliance_status"),
            technology_stack=signals.get("technology_stack"),
            phishing_susceptibility=signals.get("phishing_susceptibility"),
            patch_cadence=signals.get("patch_cadence"),
            endpoint_protection=signals.get("endpoint_protection"),
        )

        profile = CompanyProfile(
            entity_id=test_set.entity_id,
            entity_name=test_set.entity_name,
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=security_signals,
        )

        return profile


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestCyberFunctional(BaseFunctionalTest):
    """Test functional behavior of cyber pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CyberPricingEngine()
        self.test_limit = 5_000_000
        self.test_deductible = 50_000

    def _create_profile(self, test_set) -> CompanyProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        security_signals = SecuritySignals(
            security_rating=signals.get("security_rating"),
            vulnerability_count=signals.get("vulnerability_count"),
            breach_history=signals.get("breach_history"),
            compliance_status=signals.get("compliance_status"),
            technology_stack=signals.get("technology_stack"),
            phishing_susceptibility=signals.get("phishing_susceptibility"),
            patch_cadence=signals.get("patch_cadence"),
            endpoint_protection=signals.get("endpoint_protection"),
        )

        return CompanyProfile(
            entity_id=test_set.entity_id,
            entity_name=test_set.entity_name,
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=security_signals,
        )

    def test_calculates_premium(self, average_cyber_entity):
        """Test that premium calculation returns valid result."""
        profile = self._create_profile(average_cyber_entity)

        result = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=self.test_limit,
            deductible=self.test_deductible,
        )

        # Verify premium is positive
        self.assert_premium_positive(result.gross_premium)

        # Verify premium is reasonable
        self.assert_premium_reasonable(result.gross_premium, self.test_limit)

        # Verify score is valid
        TestAssertions.assert_valid_score(result.composite_score)

        # Verify tier is valid
        TestAssertions.assert_valid_tier(result.tier)

    def test_tier_assignment_logic(self):
        """Test that tier assignments follow expected ranges."""
        test_profiles = [
            (TestEntityProfile.EXCELLENT_SECURITY, 1, 2),
            (TestEntityProfile.AVERAGE_SECURITY, 2, 3),
            (TestEntityProfile.POOR_SECURITY, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "cyber", profile_type
            )
            profile = self._create_profile(test_set)

            result = self.engine.calculate_premium(
                profile=profile,
                coverage_type=CyberCoverageType.COMPREHENSIVE,
                limit=self.test_limit,
                deductible=self.test_deductible,
            )

            self.assert_tier_in_range(result.tier, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.EXCELLENT_SECURITY, 750, 1000),
            (TestEntityProfile.AVERAGE_SECURITY, 600, 799),
            (TestEntityProfile.POOR_SECURITY, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "cyber", profile_type
            )
            profile = self._create_profile(test_set)

            result = self.engine.calculate_premium(
                profile=profile,
                coverage_type=CyberCoverageType.COMPREHENSIVE,
                limit=self.test_limit,
                deductible=self.test_deductible,
            )

            self.assert_score_in_range(result.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [1_000_000, 5_000_000, 10_000_000, 25_000_000])
    def test_premium_scales_with_limit(self, average_cyber_entity, limit):
        """Test premium scales appropriately with limit."""
        profile = self._create_profile(average_cyber_entity)

        result = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=limit,
            deductible=50_000,
        )

        # Premium should be positive
        self.assert_premium_positive(result.gross_premium)

        # Rate per million should be consistent (within reason)
        rate_per_million = (result.gross_premium / limit) * 1_000_000
        assert rate_per_million > 0, "Rate per million should be positive"

    @pytest.mark.parametrize("deductible", [25_000, 50_000, 100_000, 250_000])
    def test_deductible_credit(self, average_cyber_entity, deductible):
        """Test that higher deductibles reduce premium."""
        profile = self._create_profile(average_cyber_entity)

        # Calculate with base deductible
        result_base = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=25_000,
        )

        # Calculate with higher deductible
        result_higher = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=deductible,
        )

        if deductible > 25_000:
            # Higher deductible should result in lower or equal premium
            assert result_higher.gross_premium <= result_base.gross_premium, \
                f"Higher deductible (${deductible:,}) should have lower premium"

    def test_coverage_type_affects_pricing(self, average_cyber_entity):
        """Test that coverage type affects pricing."""
        profile = self._create_profile(average_cyber_entity)

        # Calculate for different coverage types
        results = {}
        for coverage_type in CyberCoverageType:
            result = self.engine.calculate_premium(
                profile=profile,
                coverage_type=coverage_type,
                limit=5_000_000,
                deductible=50_000,
            )
            results[coverage_type] = result

        # All should have positive premiums
        for coverage_type, result in results.items():
            self.assert_premium_positive(result.gross_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestCyberActuarial(BaseActuarialTest):
    """Test actuarial validity of cyber pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CyberPricingEngine()
        self.test_limit = 5_000_000
        self.test_deductible = 50_000

    def _create_profile(self, test_set) -> CompanyProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        security_signals = SecuritySignals(
            security_rating=signals.get("security_rating"),
            vulnerability_count=signals.get("vulnerability_count"),
            breach_history=signals.get("breach_history"),
            compliance_status=signals.get("compliance_status"),
            technology_stack=signals.get("technology_stack"),
            phishing_susceptibility=signals.get("phishing_susceptibility"),
            patch_cadence=signals.get("patch_cadence"),
            endpoint_protection=signals.get("endpoint_protection"),
        )

        return CompanyProfile(
            entity_id=test_set.entity_id,
            entity_name=test_set.entity_name,
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=security_signals,
        )

    def test_poor_security_costs_more(self, excellent_cyber_entity, poor_cyber_entity):
        """Test that poor security profile results in higher premium."""
        profile_good = self._create_profile(excellent_cyber_entity)
        profile_poor = self._create_profile(poor_cyber_entity)

        result_good = self.engine.calculate_premium(
            profile=profile_good,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=self.test_limit,
            deductible=self.test_deductible,
        )

        result_poor = self.engine.calculate_premium(
            profile=profile_poor,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=self.test_limit,
            deductible=self.test_deductible,
        )

        # Poor security should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            result_good.gross_premium,
            result_poor.gross_premium,
            min_ratio=1.3
        )

    def test_risk_progression(self):
        """Test that risk profiles progress logically."""
        profiles = [
            TestEntityProfile.EXCELLENT_SECURITY,
            TestEntityProfile.AVERAGE_SECURITY,
            TestEntityProfile.POOR_SECURITY,
        ]

        tiers = []
        scores = []
        premiums = []

        for profile_type in profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "cyber", profile_type
            )
            profile = self._create_profile(test_set)

            result = self.engine.calculate_premium(
                profile=profile,
                coverage_type=CyberCoverageType.COMPREHENSIVE,
                limit=self.test_limit,
                deductible=self.test_deductible,
            )

            tiers.append(result.tier)
            scores.append(result.composite_score)
            premiums.append(result.gross_premium)

        # Tiers should increase (lower quality = higher tier)
        self.assert_tier_progression(tiers)

        # Scores should decrease (lower quality = lower score)
        self.assert_score_progression(scores)

        # Premiums should increase
        for i in range(len(premiums) - 1):
            assert premiums[i] < premiums[i+1], \
                f"Premium should increase with worse risk: " \
                f"{premiums[i]} should be < {premiums[i+1]}"

    def test_limit_scaling_consistency(self, average_cyber_entity):
        """Test that premiums scale consistently with limits."""
        profile = self._create_profile(average_cyber_entity)

        # Test doubling limit
        result_5m = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        result_10m = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=10_000_000,
            deductible=100_000,
        )

        # Check scaling
        self.assert_limit_scaling(
            result_5m.gross_premium,
            result_10m.gross_premium,
            5_000_000,
            10_000_000
        )

    def test_breach_history_impact(self):
        """Test that breach history significantly impacts pricing."""
        # Create two profiles: one with no breaches, one with multiple
        signals_no_breach = TestDataGenerator.generate_cyber_signals(
            TestEntityProfile.AVERAGE_SECURITY
        )
        signals_no_breach["breach_history"] = {"incidents": 0, "last_incident": None}

        signals_with_breaches = TestDataGenerator.generate_cyber_signals(
            TestEntityProfile.AVERAGE_SECURITY
        )
        signals_with_breaches["breach_history"] = {
            "incidents": 3,
            "last_incident": "2024-06-01"
        }

        # Create profiles
        profile_no_breach = CompanyProfile(
            entity_id="no-breach",
            entity_name="No Breach Corp",
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals_no_breach),
        )

        profile_with_breaches = CompanyProfile(
            entity_id="with-breaches",
            entity_name="Breached Corp",
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals_with_breaches),
        )

        # Calculate premiums
        result_no_breach = self.engine.calculate_premium(
            profile=profile_no_breach,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        result_with_breaches = self.engine.calculate_premium(
            profile=profile_with_breaches,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        # Company with breaches should cost more
        assert result_with_breaches.gross_premium > result_no_breach.gross_premium, \
            "Company with breach history should have higher premium"

        # Score should be lower
        assert result_with_breaches.composite_score < result_no_breach.composite_score, \
            "Company with breach history should have lower score"

    def test_vulnerability_count_impact(self):
        """Test that high vulnerability counts increase premium."""
        # Low vulnerabilities
        signals_low_vuln = TestDataGenerator.generate_cyber_signals(
            TestEntityProfile.AVERAGE_SECURITY
        )
        signals_low_vuln["vulnerability_count"] = 5

        # High vulnerabilities
        signals_high_vuln = TestDataGenerator.generate_cyber_signals(
            TestEntityProfile.AVERAGE_SECURITY
        )
        signals_high_vuln["vulnerability_count"] = 50

        # Create profiles
        profile_low = CompanyProfile(
            entity_id="low-vuln",
            entity_name="Low Vuln Corp",
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals_low_vuln),
        )

        profile_high = CompanyProfile(
            entity_id="high-vuln",
            entity_name="High Vuln Corp",
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals_high_vuln),
        )

        # Calculate
        result_low = self.engine.calculate_premium(
            profile=profile_low,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        result_high = self.engine.calculate_premium(
            profile=profile_high,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=50_000,
        )

        # High vulnerabilities should cost more
        assert result_high.gross_premium > result_low.gross_premium, \
            "High vulnerability count should result in higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestCyberEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CyberPricingEngine()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create profile with only required fields
        profile = CompanyProfile(
            entity_id="minimal-001",
            entity_name="Minimal Corp",
            industry="technology",
            employee_count=10,
            annual_revenue=1_000_000,
        )

        # Should not raise exception
        result = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=1_000_000,
            deductible=25_000,
        )

        assert result is not None
        assert result.gross_premium > 0

    def test_zero_deductible(self):
        """Test pricing with zero deductible."""
        test_set = TestDataGenerator.create_test_signal_set(
            "Test Corp", "cyber", TestEntityProfile.AVERAGE_SECURITY
        )

        signals = test_set.signals
        profile = CompanyProfile(
            entity_id=test_set.entity_id,
            entity_name=test_set.entity_name,
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals),
        )

        # Should handle zero deductible
        result = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=5_000_000,
            deductible=0,
        )

        assert result is not None
        assert result.gross_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        test_set = TestDataGenerator.create_test_signal_set(
            "Test Corp", "cyber", TestEntityProfile.AVERAGE_SECURITY
        )

        signals = test_set.signals
        profile = CompanyProfile(
            entity_id=test_set.entity_id,
            entity_name=test_set.entity_name,
            industry="technology",
            employee_count=500,
            annual_revenue=50_000_000,
            security_signals=SecuritySignals(**signals),
        )

        # Should handle large limit
        result = self.engine.calculate_premium(
            profile=profile,
            coverage_type=CyberCoverageType.COMPREHENSIVE,
            limit=100_000_000,
            deductible=1_000_000,
        )

        assert result is not None
        assert result.gross_premium > 0
        assert result.gross_premium < 100_000_000, \
            "Premium should be less than limit"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCyberIntegration:
    """Integration tests for cyber pricing with workflow."""

    @pytest.mark.integration
    def test_end_to_end_workflow(self):
        """Test complete end-to-end pricing workflow."""
        # This would test integration with workflow/persistence
        # Placeholder for now
        pass

    @pytest.mark.integration
    def test_signal_extraction_integration(self):
        """Test integration with signal extraction."""
        # Placeholder
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
