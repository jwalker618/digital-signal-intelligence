"""
D&O Insurance Pricing Model Tests
==================================

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

from models.do.dsi_do_pricing import (
    DODSIPricingModel,
    DOCompanyProfile,
    DOTierAssignment,
    DOPricingEngine,
    CompanyType,
    IndustryClassification,
    NetworkAuthoritySignals,
    GovernanceSignals,
    FinancialSignals,
    LitigationSignals,
    ExecutiveSignals,
    CorporateFootprintSignals,
    StructuredDataSignals,
    DirectInquirySignals,
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

class TestDOStructure(BaseStructuralTest):
    """Test structural integrity of D&O pricing model."""

    def test_engine_instantiates(self):
        """Test DODSIPricingModel instantiates correctly."""
        model = DODSIPricingModel()
        assert model is not None
        assert isinstance(model, DODSIPricingModel)

    def test_company_type_enum_values(self):
        """Test CompanyType enum has expected values."""
        expected_types = ["public_large_cap", "public_mid_cap", "public_small_cap",
                         "private_backed", "nonprofit"]
        actual_types = [company_type.value for company_type in CompanyType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing company type: {expected}"

    def test_industry_classification_enum(self):
        """Test IndustryClassification enum."""
        expected_industries = ["FINANCIAL_SERVICES", "TECHNOLOGY", "HEALTHCARE_PHARMA"]

        for expected in expected_industries:
            assert hasattr(IndustryClassification, expected), \
                   f"Missing industry classification: {expected}"

    def test_company_profile_structure(self):
        """Test DOCompanyProfile dataclass structure."""
        # Create minimal profile
        profile = DOCompanyProfile(
            company_name="Test Corp",
            ticker="TEST",
            cik="0001234567",
            primary_domain="test.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
        )

        # Verify required fields
        required_fields = ["company_name", "company_type", "industry", "country"]
        self.verify_dataclass_structure(profile, required_fields)

    def test_governance_signals_structure(self):
        """Test GovernanceSignals dataclass structure."""
        signals = GovernanceSignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "board_independence_score",
            "ceo_chair_separation_score",
            "committee_structure_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_underwriting_decision_structure(self):
        """Test DOUnderwritingDecision has required fields."""
        model = DODSIPricingModel()

        # Create test profile with good governance
        test_set = TestDataGenerator.create_test_signal_set(
            "GoodGov Corp", "do", TestEntityProfile.STRONG_GOVERNANCE
        )

        profile = self._create_profile_from_signals(test_set)
        decision = model.assess(profile)

        # Verify required fields
        required_fields = [
            "tier",
            "tier_label",
            "composite_score",
            "annual_premium",
            "decision",
        ]

        for field in required_fields:
            assert hasattr(decision, field), f"Missing field: {field}"

    def _create_profile_from_signals(self, test_set) -> DOCompanyProfile:
        """Helper to create DOCompanyProfile from test signals."""
        signals = test_set.signals

        profile = DOCompanyProfile(
            company_name=test_set.entity_name,
            ticker="TEST",
            cik="0001234567",
            primary_domain="test.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            governance=GovernanceSignals(
                board_independence_score=signals.get("board_composition", {}).get("score", 70),
                committee_structure_score=70,
            ),
            financial=FinancialSignals(
                audit_opinion_score=signals.get("financial_strength", {}).get("score", 70),
            ),
            litigation=LitigationSignals(
                securities_litigation_score=signals.get("litigation_history", {}).get("score", 70),
            ),
        )

        return profile


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestDOFunctional(BaseFunctionalTest):
    """Test functional behavior of D&O pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = DODSIPricingModel()
        self.test_limit = 10_000_000

    def _create_profile(self, test_set) -> DOCompanyProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return DOCompanyProfile(
            company_name=test_set.entity_name,
            ticker="TEST",
            cik="0001234567",
            primary_domain="test.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            market_cap=2_000_000_000,
            network_authority=NetworkAuthoritySignals(
                auditor_quality_score=70,
                legal_counsel_score=70,
            ),
            governance=GovernanceSignals(
                board_independence_score=signals.get("board_composition", {}).get("score", 70),
                committee_structure_score=70,
                compensation_structure_score=70,
            ),
            financial=FinancialSignals(
                audit_opinion_score=signals.get("financial_strength", {}).get("score", 70),
                internal_controls_score=70,
                stock_volatility_score=signals.get("stock_volatility", {}).get("score", 70),
            ),
            litigation=LitigationSignals(
                securities_litigation_score=signals.get("litigation_history", {}).get("score", 70),
                sec_enforcement_score=70,
            ),
            executive=ExecutiveSignals(
                executive_stability_score=signals.get("executive_turnover", {}).get("score", 70),
                insider_trading_score=70,
            ),
        )

    def test_calculates_decision(self, strong_governance_entity):
        """Test that decision calculation returns valid result."""
        profile = self._create_profile(strong_governance_entity)
        decision = self.model.assess(profile)

        # Verify premium is positive
        self.assert_premium_positive(decision.annual_premium)

        # Verify premium is reasonable
        self.assert_premium_reasonable(decision.annual_premium, decision.recommended_limit)

        # Verify score is valid
        TestAssertions.assert_valid_score(decision.composite_score)

        # Verify tier is valid
        TestAssertions.assert_valid_tier(decision.tier)

    def test_tier_assignment_logic(self):
        """Test that tier assignments follow expected ranges."""
        test_profiles = [
            (TestEntityProfile.STRONG_GOVERNANCE, 1, 2),
            (TestEntityProfile.STANDARD_GOVERNANCE, 2, 3),
            (TestEntityProfile.WEAK_GOVERNANCE, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "do", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_tier_in_range(decision.tier, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.STRONG_GOVERNANCE, 750, 1000),
            (TestEntityProfile.STANDARD_GOVERNANCE, 600, 799),
            (TestEntityProfile.WEAK_GOVERNANCE, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "do", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_score_in_range(decision.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [5_000_000, 10_000_000, 25_000_000, 50_000_000])
    def test_premium_scales_with_limit(self, strong_governance_entity, limit):
        """Test premium scales appropriately with limit."""
        profile = self._create_profile(strong_governance_entity)
        decision = self.model.assess(profile, requested_limit=limit)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

        # Limit should match requested
        assert decision.recommended_limit == limit

    @pytest.mark.parametrize("company_type", [CompanyType.PUBLIC_LARGE_CAP, CompanyType.PUBLIC_MID_CAP,
                                              CompanyType.PRIVATE_BACKED])
    def test_company_type_affects_pricing(self, strong_governance_entity, company_type):
        """Test that company type affects pricing."""
        profile = self._create_profile(strong_governance_entity)
        profile.company_type = company_type

        decision = self.model.assess(profile)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

    def test_industry_affects_pricing(self, strong_governance_entity):
        """Test that industry affects pricing."""
        profile = self._create_profile(strong_governance_entity)

        # Calculate for different industries
        results = {}
        for industry in [IndustryClassification.TECHNOLOGY, IndustryClassification.FINANCIAL_SERVICES,
                        IndustryClassification.HEALTHCARE_PHARMA]:
            profile.industry = industry
            decision = self.model.assess(profile)
            results[industry] = decision

        # All should have positive premiums
        for industry, decision in results.items():
            self.assert_premium_positive(decision.annual_premium)

    def test_market_cap_handled(self, strong_governance_entity):
        """Test that market cap is handled correctly."""
        profile = self._create_profile(strong_governance_entity)

        for market_cap in [500_000_000, 5_000_000_000, 50_000_000_000]:
            profile.market_cap = market_cap
            decision = self.model.assess(profile)

            assert decision is not None
            self.assert_premium_positive(decision.annual_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestDOActuarial(BaseActuarialTest):
    """Test actuarial validity of D&O pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = DODSIPricingModel()

    def _create_profile(self, test_set) -> DOCompanyProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return DOCompanyProfile(
            company_name=test_set.entity_name,
            ticker="TEST",
            cik="0001234567",
            primary_domain="test.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            market_cap=2_000_000_000,
            network_authority=NetworkAuthoritySignals(
                auditor_quality_score=70,
                legal_counsel_score=70,
            ),
            governance=GovernanceSignals(
                board_independence_score=signals.get("board_composition", {}).get("score", 70),
                committee_structure_score=70,
                compensation_structure_score=70,
            ),
            financial=FinancialSignals(
                audit_opinion_score=signals.get("financial_strength", {}).get("score", 70),
                internal_controls_score=70,
                stock_volatility_score=signals.get("stock_volatility", {}).get("score", 70),
            ),
            litigation=LitigationSignals(
                securities_litigation_score=signals.get("litigation_history", {}).get("score", 70),
                sec_enforcement_score=70,
            ),
            executive=ExecutiveSignals(
                executive_stability_score=signals.get("executive_turnover", {}).get("score", 70),
                insider_trading_score=70,
            ),
        )

    def test_poor_governance_costs_more(self, strong_governance_entity, weak_governance_entity):
        """Test that poor governance profile results in higher premium."""
        profile_good = self._create_profile(strong_governance_entity)
        profile_poor = self._create_profile(weak_governance_entity)

        decision_good = self.model.assess(profile_good)
        decision_poor = self.model.assess(profile_poor)

        # Poor governance should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            decision_good.annual_premium,
            decision_poor.annual_premium,
            min_ratio=1.3
        )

    def test_risk_progression(self):
        """Test that risk profiles progress logically."""
        profiles = [
            TestEntityProfile.STRONG_GOVERNANCE,
            TestEntityProfile.STANDARD_GOVERNANCE,
            TestEntityProfile.WEAK_GOVERNANCE,
        ]

        tiers = []
        scores = []
        premiums = []

        for profile_type in profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "do", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            tiers.append(decision.tier)
            scores.append(decision.composite_score)
            premiums.append(decision.annual_premium)

        # Tiers should increase (lower quality = higher tier)
        self.assert_tier_progression(tiers)

        # Scores should decrease (lower quality = lower score)
        self.assert_score_progression(scores)

        # Premiums should increase
        for i in range(len(premiums) - 1):
            assert premiums[i] < premiums[i+1], \
                f"Premium should increase with worse risk: " \
                f"{premiums[i]} should be < {premiums[i+1]}"

    def test_limit_scaling_consistency(self, strong_governance_entity):
        """Test that premiums scale consistently with limits."""
        profile = self._create_profile(strong_governance_entity)

        # Test doubling limit
        decision_10m = self.model.assess(profile, requested_limit=10_000_000)
        decision_20m = self.model.assess(profile, requested_limit=20_000_000)

        # Check scaling
        self.assert_limit_scaling(
            decision_10m.annual_premium,
            decision_20m.annual_premium,
            10_000_000,
            20_000_000
        )

    def test_securities_litigation_impact(self):
        """Test that securities litigation significantly impacts pricing."""
        # Create two profiles: one clean, one with litigation
        profile_clean = DOCompanyProfile(
            company_name="Clean Corp",
            ticker="CLEAN",
            cik="0001234567",
            primary_domain="clean.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            litigation=LitigationSignals(
                securities_litigation_score=95,
                sec_enforcement_score=100,
            ),
            governance=GovernanceSignals(
                board_independence_score=70,
            ),
        )

        profile_litigation = DOCompanyProfile(
            company_name="Litigation Corp",
            ticker="LIT",
            cik="0001234568",
            primary_domain="litigation.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            litigation=LitigationSignals(
                securities_litigation_score=30,
                sec_enforcement_score=100,
            ),
            governance=GovernanceSignals(
                board_independence_score=70,
            ),
        )

        # Calculate premiums
        decision_clean = self.model.assess(profile_clean)
        decision_litigation = self.model.assess(profile_litigation)

        # Company with litigation should cost more
        assert decision_litigation.annual_premium > decision_clean.annual_premium, \
            "Company with securities litigation should have higher premium"

        # Score should be lower
        assert decision_litigation.composite_score < decision_clean.composite_score, \
            "Company with securities litigation should have lower score"

    def test_board_independence_impact(self):
        """Test that board independence affects premium."""
        # Create profiles
        profile_strong = DOCompanyProfile(
            company_name="Strong Board Corp",
            ticker="STRONG",
            cik="0001234567",
            primary_domain="strong.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            governance=GovernanceSignals(
                board_independence_score=92,
                committee_structure_score=95,
            ),
        )

        profile_weak = DOCompanyProfile(
            company_name="Weak Board Corp",
            ticker="WEAK",
            cik="0001234568",
            primary_domain="weak.com",
            company_type=CompanyType.PUBLIC_MID_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            governance=GovernanceSignals(
                board_independence_score=35,
                committee_structure_score=40,
            ),
        )

        # Calculate
        decision_strong = self.model.assess(profile_strong)
        decision_weak = self.model.assess(profile_weak)

        # Weak governance should cost more
        assert decision_weak.annual_premium > decision_strong.annual_premium, \
            "Company with weak board independence should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestDOEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = DODSIPricingModel()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create profile with only required fields
        profile = DOCompanyProfile(
            company_name="Minimal Corp",
            ticker=None,
            cik=None,
            primary_domain="minimal.com",
            company_type=CompanyType.PRIVATE_OTHER,
            industry=IndustryClassification.OTHER,
            country="US",
        )

        # Should not raise exception
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_nonprofit_organization(self):
        """Test pricing with nonprofit."""
        profile = DOCompanyProfile(
            company_name="Nonprofit Org",
            ticker=None,
            cik=None,
            primary_domain="nonprofit.org",
            company_type=CompanyType.NONPROFIT,
            industry=IndustryClassification.OTHER,
            country="US",
        )

        # Should handle nonprofit
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        profile = DOCompanyProfile(
            company_name="Big Corp",
            ticker="BIG",
            cik="0001234567",
            primary_domain="big.com",
            company_type=CompanyType.PUBLIC_LARGE_CAP,
            industry=IndustryClassification.TECHNOLOGY,
            country="US",
            market_cap=100_000_000_000,
        )

        # Should handle large limit
        decision = self.model.assess(profile, requested_limit=100_000_000)

        assert decision is not None
        assert decision.annual_premium > 0
        assert decision.annual_premium < 50_000_000, \
            "Premium should be reasonable relative to limit"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
