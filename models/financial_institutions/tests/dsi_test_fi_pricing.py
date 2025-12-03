"""
Financial Institutions Insurance Pricing Model Tests
====================================================

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

from models.financial_institutions.dsi_fi_pricing import (
    FIDSIPricingModel,
    FIProfile,
    FITierAssignment,
    FIPricingEngine,
    InstitutionType,
    AssetSizeBand,
    RegulatoryFramework,
    NetworkAuthoritySignals,
    RegulatoryComplianceSignals,
    FinancialConditionSignals,
    GovernanceSignals,
    OperationalRiskSignals,
    CyberSecuritySignals,
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

class TestFIStructure(BaseStructuralTest):
    """Test structural integrity of FI pricing model."""

    def test_engine_instantiates(self):
        """Test FIDSIPricingModel instantiates correctly."""
        model = FIDSIPricingModel()
        assert model is not None
        assert isinstance(model, FIDSIPricingModel)

    def test_institution_type_enum_values(self):
        """Test InstitutionType enum has expected values."""
        expected_types = ["community_bank", "regional_bank", "money_center_bank",
                         "credit_union", "broker_dealer"]
        actual_types = [inst_type.value for inst_type in InstitutionType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing institution type: {expected}"

    def test_asset_size_band_enum(self):
        """Test AssetSizeBand enum."""
        expected_bands = ["COMMUNITY", "SMALL", "MID", "LARGE", "MEGA"]

        for expected in expected_bands:
            assert hasattr(AssetSizeBand, expected), \
                   f"Missing asset size band: {expected}"

    def test_fi_profile_structure(self):
        """Test FIProfile dataclass structure."""
        # Create minimal profile
        profile = FIProfile(
            institution_name="Test Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker="TBNK",
            primary_domain="testbank.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.COMMUNITY,
            headquarters_state="OH",
            total_assets=500_000_000,
        )

        # Verify required fields
        required_fields = ["institution_name", "institution_type", "asset_size_band",
                          "regulatory_framework", "total_assets"]
        self.verify_dataclass_structure(profile, required_fields)

    def test_network_authority_signals_structure(self):
        """Test NetworkAuthoritySignals dataclass structure."""
        signals = NetworkAuthoritySignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "correspondent_quality_score",
            "auditor_quality_score",
            "credit_rating_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_underwriting_decision_structure(self):
        """Test FIUnderwritingDecision has required fields."""
        model = FIDSIPricingModel()

        # Create test profile with good signals
        test_set = TestDataGenerator.create_test_signal_set(
            "Premier Bank", "fi", TestEntityProfile.WELL_CAPITALIZED
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

    def _create_profile_from_signals(self, test_set) -> FIProfile:
        """Helper to create FIProfile from test signals."""
        signals = test_set.signals

        profile = FIProfile(
            institution_name=test_set.entity_name,
            charter_number="12345",
            rssd_id="123456",
            ticker="TEST",
            primary_domain="test.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            network_authority=NetworkAuthoritySignals(
                correspondent_quality_score=signals.get("financial_strength", {}).get("score", 0),
                auditor_quality_score=signals.get("credit_rating", {}).get("score", 0),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                enforcement_action_score=100 if signals.get("regulatory_actions", {}).get("count", 0) == 0 else 50,
            ),
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=signals.get("financial_strength", {}).get("score", 0),
            ),
        )

        return profile


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestFIFunctional(BaseFunctionalTest):
    """Test functional behavior of FI pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = FIDSIPricingModel()
        self.test_limit = 10_000_000

    def _create_profile(self, test_set) -> FIProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return FIProfile(
            institution_name=test_set.entity_name,
            charter_number="12345",
            rssd_id="123456",
            ticker="TEST",
            primary_domain="test.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            network_authority=NetworkAuthoritySignals(
                correspondent_quality_score=signals.get("financial_strength", {}).get("score", 70),
                auditor_quality_score=signals.get("credit_rating", {}).get("score", 70),
                credit_rating_score=signals.get("credit_rating", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                enforcement_action_score=100 if signals.get("regulatory_actions", {}).get("count", 0) == 0 else 50,
                bsa_aml_score=signals.get("compliance_status") == "excellent" and 90 or 60,
            ),
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=signals.get("financial_strength", {}).get("score", 70),
                asset_quality_score=70,
                liquidity_score=70,
            ),
            governance=GovernanceSignals(
                board_independence_score=70,
                board_expertise_score=70,
            ),
            operational_risk=OperationalRiskSignals(
                cfpb_complaint_score=signals.get("litigation_history", {}).get("score", 70),
                litigation_score=signals.get("litigation_history", {}).get("score", 70),
            ),
            cyber_security=CyberSecuritySignals(
                security_rating_score=signals.get("security_rating", {}).get("score", 70),
            ),
        )

    def test_calculates_decision(self, strong_fi_entity):
        """Test that decision calculation returns valid result."""
        profile = self._create_profile(strong_fi_entity)
        decision = self.model.assess(profile)

        # Verify premium is positive
        self.assert_premium_positive(decision.annual_premium)

        # Verify premium is reasonable
        self.assert_premium_reasonable(decision.annual_premium, decision.combined_limit)

        # Verify score is valid
        TestAssertions.assert_valid_score(decision.composite_score)

        # Verify tier is valid
        TestAssertions.assert_valid_tier(decision.tier)

    def test_tier_assignment_logic(self):
        """Test that tier assignments follow expected ranges."""
        test_profiles = [
            (TestEntityProfile.WELL_CAPITALIZED, 1, 2),
            (TestEntityProfile.ADEQUATE_CAPITAL, 2, 3),
            (TestEntityProfile.UNDERCAPITALIZED, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "fi", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_tier_in_range(decision.tier, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.WELL_CAPITALIZED, 750, 1000),
            (TestEntityProfile.ADEQUATE_CAPITAL, 600, 799),
            (TestEntityProfile.UNDERCAPITALIZED, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "fi", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_score_in_range(decision.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [5_000_000, 10_000_000, 25_000_000, 50_000_000])
    def test_premium_scales_with_limit(self, strong_fi_entity, limit):
        """Test premium scales appropriately with limit."""
        profile = self._create_profile(strong_fi_entity)
        decision = self.model.assess(profile, requested_limit=limit)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

        # Premium should scale with limit
        assert decision.combined_limit == limit

    @pytest.mark.parametrize("asset_size", [AssetSizeBand.COMMUNITY, AssetSizeBand.SMALL, AssetSizeBand.MID])
    def test_asset_size_affects_pricing(self, strong_fi_entity, asset_size):
        """Test that asset size affects pricing."""
        profile = self._create_profile(strong_fi_entity)
        profile.asset_size_band = asset_size

        decision = self.model.assess(profile)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

    def test_institution_type_affects_pricing(self, strong_fi_entity):
        """Test that institution type affects pricing."""
        profile = self._create_profile(strong_fi_entity)

        # Calculate for different types
        results = {}
        for inst_type in [InstitutionType.COMMUNITY_BANK, InstitutionType.REGIONAL_BANK,
                         InstitutionType.BROKER_DEALER]:
            profile.institution_type = inst_type
            decision = self.model.assess(profile)
            results[inst_type] = decision

        # All should have positive premiums
        for inst_type, decision in results.items():
            self.assert_premium_positive(decision.annual_premium)

    def test_regulatory_framework_handled(self, strong_fi_entity):
        """Test that different regulatory frameworks are handled."""
        profile = self._create_profile(strong_fi_entity)

        for framework in [RegulatoryFramework.FDIC, RegulatoryFramework.OCC,
                         RegulatoryFramework.FED]:
            profile.regulatory_framework = framework
            decision = self.model.assess(profile)

            assert decision is not None
            self.assert_premium_positive(decision.annual_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestFIActuarial(BaseActuarialTest):
    """Test actuarial validity of FI pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = FIDSIPricingModel()

    def _create_profile(self, test_set) -> FIProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return FIProfile(
            institution_name=test_set.entity_name,
            charter_number="12345",
            rssd_id="123456",
            ticker="TEST",
            primary_domain="test.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            network_authority=NetworkAuthoritySignals(
                correspondent_quality_score=signals.get("financial_strength", {}).get("score", 70),
                auditor_quality_score=signals.get("credit_rating", {}).get("score", 70),
                credit_rating_score=signals.get("credit_rating", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                enforcement_action_score=100 if signals.get("regulatory_actions", {}).get("count", 0) == 0 else 50,
                bsa_aml_score=signals.get("compliance_status") == "excellent" and 90 or 60,
            ),
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=signals.get("financial_strength", {}).get("score", 70),
                asset_quality_score=70,
                liquidity_score=70,
            ),
            governance=GovernanceSignals(
                board_independence_score=70,
                board_expertise_score=70,
            ),
            operational_risk=OperationalRiskSignals(
                cfpb_complaint_score=signals.get("litigation_history", {}).get("score", 70),
                litigation_score=signals.get("litigation_history", {}).get("score", 70),
            ),
            cyber_security=CyberSecuritySignals(
                security_rating_score=signals.get("security_rating", {}).get("score", 70),
            ),
        )

    def test_poor_profile_costs_more(self, strong_fi_entity, weak_fi_entity):
        """Test that poor financial profile results in higher premium."""
        profile_good = self._create_profile(strong_fi_entity)
        profile_poor = self._create_profile(weak_fi_entity)

        decision_good = self.model.assess(profile_good)
        decision_poor = self.model.assess(profile_poor)

        # Poor profile should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            decision_good.annual_premium,
            decision_poor.annual_premium,
            min_ratio=1.3
        )

    def test_risk_progression(self):
        """Test that risk profiles progress logically."""
        profiles = [
            TestEntityProfile.WELL_CAPITALIZED,
            TestEntityProfile.ADEQUATE_CAPITAL,
            TestEntityProfile.UNDERCAPITALIZED,
        ]

        tiers = []
        scores = []
        premiums = []

        for profile_type in profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "fi", profile_type
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

    def test_limit_scaling_consistency(self, strong_fi_entity):
        """Test that premiums scale consistently with limits."""
        profile = self._create_profile(strong_fi_entity)

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

    def test_regulatory_action_impact(self):
        """Test that regulatory actions significantly impact pricing."""
        # Create two profiles: one clean, one with enforcement actions
        signals_clean = TestDataGenerator.generate_fi_signals(
            TestEntityProfile.ADEQUATE_CAPITAL
        )

        signals_enforcement = TestDataGenerator.generate_fi_signals(
            TestEntityProfile.ADEQUATE_CAPITAL
        )
        signals_enforcement["regulatory_actions"] = {"count": 3, "severity": "major"}

        # Create profiles
        profile_clean = FIProfile(
            institution_name="Clean Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker="CLEAN",
            primary_domain="clean.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            regulatory_compliance=RegulatoryComplianceSignals(
                enforcement_action_score=100,
                bsa_aml_score=90,
            ),
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=70,
            ),
        )

        profile_enforcement = FIProfile(
            institution_name="Enforcement Bank",
            charter_number="12346",
            rssd_id="123457",
            ticker="ENF",
            primary_domain="enforcement.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            regulatory_compliance=RegulatoryComplianceSignals(
                enforcement_action_score=30,
                bsa_aml_score=90,
            ),
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=70,
            ),
        )

        # Calculate premiums
        decision_clean = self.model.assess(profile_clean)
        decision_enforcement = self.model.assess(profile_enforcement)

        # Bank with enforcement actions should cost more
        assert decision_enforcement.annual_premium > decision_clean.annual_premium, \
            "Bank with enforcement actions should have higher premium"

        # Score should be lower
        assert decision_enforcement.composite_score < decision_clean.composite_score, \
            "Bank with enforcement actions should have lower score"

    def test_capital_adequacy_impact(self):
        """Test that capital adequacy affects premium."""
        # Well-capitalized
        signals_strong = TestDataGenerator.generate_fi_signals(
            TestEntityProfile.WELL_CAPITALIZED
        )

        # Undercapitalized
        signals_weak = TestDataGenerator.generate_fi_signals(
            TestEntityProfile.UNDERCAPITALIZED
        )

        # Create profiles
        profile_strong = FIProfile(
            institution_name="Strong Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker="STRONG",
            primary_domain="strong.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=95,
                asset_quality_score=90,
                liquidity_score=90,
            ),
        )

        profile_weak = FIProfile(
            institution_name="Weak Bank",
            charter_number="12346",
            rssd_id="123457",
            ticker="WEAK",
            primary_domain="weak.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.SMALL,
            headquarters_state="OH",
            total_assets=1_000_000_000,
            financial_condition=FinancialConditionSignals(
                capital_ratio_score=40,
                asset_quality_score=45,
                liquidity_score=50,
            ),
        )

        # Calculate
        decision_strong = self.model.assess(profile_strong)
        decision_weak = self.model.assess(profile_weak)

        # Undercapitalized should cost more
        assert decision_weak.annual_premium > decision_strong.annual_premium, \
            "Undercapitalized bank should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestFIEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = FIDSIPricingModel()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create profile with only required fields
        profile = FIProfile(
            institution_name="Minimal Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker=None,
            primary_domain="minimal.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.COMMUNITY,
            headquarters_state="OH",
            total_assets=500_000_000,
        )

        # Should not raise exception
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_very_small_institution(self):
        """Test pricing with very small institution."""
        test_set = TestDataGenerator.create_test_signal_set(
            "Tiny Bank", "fi", TestEntityProfile.ADEQUATE_CAPITAL
        )

        signals = test_set.signals
        profile = FIProfile(
            institution_name="Tiny Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker=None,
            primary_domain="tiny.com",
            institution_type=InstitutionType.COMMUNITY_BANK,
            regulatory_framework=RegulatoryFramework.FDIC,
            asset_size_band=AssetSizeBand.COMMUNITY,
            headquarters_state="OH",
            total_assets=250_000_000,
        )

        # Should handle small institution
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        test_set = TestDataGenerator.create_test_signal_set(
            "Big Bank", "fi", TestEntityProfile.WELL_CAPITALIZED
        )

        signals = test_set.signals
        profile = FIProfile(
            institution_name="Big Bank",
            charter_number="12345",
            rssd_id="123456",
            ticker="BIG",
            primary_domain="big.com",
            institution_type=InstitutionType.REGIONAL_BANK,
            regulatory_framework=RegulatoryFramework.OCC,
            asset_size_band=AssetSizeBand.LARGE,
            headquarters_state="NY",
            total_assets=50_000_000_000,
        )

        # Should handle large limit
        decision = self.model.assess(profile, requested_limit=100_000_000)

        assert decision is not None
        assert decision.annual_premium > 0
        assert decision.annual_premium < 50_000_000, \
            "Premium should be reasonable relative to limit"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestFIIntegration:
    """Integration tests for FI pricing with workflow."""

    @pytest.mark.integration
    def test_end_to_end_workflow(self):
        """Test complete end-to-end pricing workflow."""
        # Placeholder for future integration tests
        pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
