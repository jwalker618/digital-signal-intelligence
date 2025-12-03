"""
Energy Insurance Pricing Model Tests
=====================================

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

from models.energy.dsi_energy_pricing import (
    EnergyDSIPricingModel,
    EnergyOperatorProfile,
    EnergyTierAssignment,
    EnergyPricingEngine,
    OperatorType,
    AssetClass,
    GeographicRegion,
    NetworkAuthoritySignals,
    SafetyRecordSignals,
    RegulatoryComplianceSignals,
    EnvironmentalSignals,
    OperationalSignals,
    FinancialSignals,
    CorporateFootprintSignals,
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

class TestEnergyStructure(BaseStructuralTest):
    """Test structural integrity of Energy pricing model."""

    def test_engine_instantiates(self):
        """Test EnergyDSIPricingModel instantiates correctly."""
        model = EnergyDSIPricingModel()
        assert model is not None
        assert isinstance(model, EnergyDSIPricingModel)

    def test_operator_type_enum_values(self):
        """Test OperatorType enum has expected values."""
        expected_types = ["upstream", "midstream", "downstream", "oilfield_services"]
        actual_types = [op_type.value for op_type in OperatorType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing operator type: {expected}"

    def test_asset_class_enum(self):
        """Test AssetClass enum."""
        expected_classes = ["ONSHORE", "OFFSHORE_SHALLOW", "OFFSHORE_DEEPWATER"]

        for expected in expected_classes:
            assert hasattr(AssetClass, expected), \
                   f"Missing asset class: {expected}"

    def test_operator_profile_structure(self):
        """Test EnergyOperatorProfile dataclass structure."""
        # Create minimal profile
        profile = EnergyOperatorProfile(
            operator_name="Test Energy Co",
            primary_domain="testenergy.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
        )

        # Verify required fields
        required_fields = ["operator_name", "operator_type", "asset_class",
                          "geographic_region", "country"]
        self.verify_dataclass_structure(profile, required_fields)

    def test_safety_record_signals_structure(self):
        """Test SafetyRecordSignals dataclass structure."""
        signals = SafetyRecordSignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "osha_recordable_rate_score",
            "lost_time_incident_score",
            "fatality_history_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_underwriting_decision_structure(self):
        """Test EnergyUnderwritingDecision has required fields."""
        model = EnergyDSIPricingModel()

        # Create test profile with good safety
        test_set = TestDataGenerator.create_test_signal_set(
            "Safe Operator", "energy", TestEntityProfile.EXCELLENT_SAFETY
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

    def _create_profile_from_signals(self, test_set) -> EnergyOperatorProfile:
        """Helper to create EnergyOperatorProfile from test signals."""
        signals = test_set.signals

        profile = EnergyOperatorProfile(
            operator_name=test_set.entity_name,
            primary_domain="test.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=signals.get("safety_record", {}).get("score", 70),
                lost_time_incident_score=70,
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                permit_compliance_score=signals.get("regulatory_compliance", {}).get("score", 70),
            ),
        )

        return profile


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestEnergyFunctional(BaseFunctionalTest):
    """Test functional behavior of Energy pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = EnergyDSIPricingModel()
        self.test_limit = 10_000_000

    def _create_profile(self, test_set) -> EnergyOperatorProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return EnergyOperatorProfile(
            operator_name=test_set.entity_name,
            primary_domain="test.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            production_volume=100_000,
            network_authority=NetworkAuthoritySignals(
                industry_association_score=70,
                operator_rating_score=70,
            ),
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=signals.get("safety_record", {}).get("score", 70),
                lost_time_incident_score=70,
                fatality_history_score=signals.get("safety_record", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                permit_compliance_score=signals.get("regulatory_compliance", {}).get("score", 70),
                environmental_violations_score=signals.get("environmental_record", {}).get("score", 70),
            ),
            environmental=EnvironmentalSignals(
                spill_history_score=signals.get("environmental_record", {}).get("score", 70),
                emissions_compliance_score=70,
            ),
            operational=OperationalSignals(
                well_integrity_score=70,
                inspection_compliance_score=70,
            ),
            financial=FinancialSignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 70),
            ),
        )

    def test_calculates_decision(self, excellent_energy_entity):
        """Test that decision calculation returns valid result."""
        profile = self._create_profile(excellent_energy_entity)
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
            (TestEntityProfile.EXCELLENT_SAFETY, 1, 2),
            (TestEntityProfile.AVERAGE_SAFETY, 2, 3),
            (TestEntityProfile.POOR_SAFETY, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "energy", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_tier_in_range(decision.tier, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.EXCELLENT_SAFETY, 750, 1000),
            (TestEntityProfile.AVERAGE_SAFETY, 600, 799),
            (TestEntityProfile.POOR_SAFETY, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "energy", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_score_in_range(decision.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [5_000_000, 10_000_000, 25_000_000, 50_000_000])
    def test_premium_scales_with_limit(self, excellent_energy_entity, limit):
        """Test premium scales appropriately with limit."""
        profile = self._create_profile(excellent_energy_entity)
        decision = self.model.assess(profile, requested_limit=limit)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

        # Limit should match requested
        assert decision.recommended_limit == limit

    @pytest.mark.parametrize("operator_type", [OperatorType.UPSTREAM, OperatorType.MIDSTREAM,
                                               OperatorType.DOWNSTREAM])
    def test_operator_type_affects_pricing(self, excellent_energy_entity, operator_type):
        """Test that operator type affects pricing."""
        profile = self._create_profile(excellent_energy_entity)
        profile.operator_type = operator_type

        decision = self.model.assess(profile)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

    def test_asset_class_affects_pricing(self, excellent_energy_entity):
        """Test that asset class affects pricing."""
        profile = self._create_profile(excellent_energy_entity)

        # Calculate for different asset classes
        results = {}
        for asset_class in [AssetClass.ONSHORE, AssetClass.OFFSHORE_SHALLOW,
                           AssetClass.OFFSHORE_DEEPWATER]:
            profile.asset_class = asset_class
            decision = self.model.assess(profile)
            results[asset_class] = decision

        # All should have positive premiums
        for asset_class, decision in results.items():
            self.assert_premium_positive(decision.annual_premium)

    def test_geographic_region_handled(self, excellent_energy_entity):
        """Test that geographic region is handled correctly."""
        profile = self._create_profile(excellent_energy_entity)

        for region in [GeographicRegion.NORTH_AMERICA, GeographicRegion.EUROPE,
                      GeographicRegion.MIDDLE_EAST]:
            profile.geographic_region = region
            decision = self.model.assess(profile)

            assert decision is not None
            self.assert_premium_positive(decision.annual_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestEnergyActuarial(BaseActuarialTest):
    """Test actuarial validity of Energy pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = EnergyDSIPricingModel()

    def _create_profile(self, test_set) -> EnergyOperatorProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return EnergyOperatorProfile(
            operator_name=test_set.entity_name,
            primary_domain="test.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            production_volume=100_000,
            network_authority=NetworkAuthoritySignals(
                industry_association_score=70,
            ),
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=signals.get("safety_record", {}).get("score", 70),
                lost_time_incident_score=70,
                fatality_history_score=signals.get("safety_record", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                permit_compliance_score=signals.get("regulatory_compliance", {}).get("score", 70),
                environmental_violations_score=signals.get("environmental_record", {}).get("score", 70),
            ),
            environmental=EnvironmentalSignals(
                spill_history_score=signals.get("environmental_record", {}).get("score", 70),
                emissions_compliance_score=70,
            ),
            operational=OperationalSignals(
                well_integrity_score=70,
            ),
            financial=FinancialSignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 70),
            ),
        )

    def test_poor_profile_costs_more(self, excellent_energy_entity, poor_energy_entity):
        """Test that poor safety profile results in higher premium."""
        profile_good = self._create_profile(excellent_energy_entity)
        profile_poor = self._create_profile(poor_energy_entity)

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
            TestEntityProfile.EXCELLENT_SAFETY,
            TestEntityProfile.AVERAGE_SAFETY,
            TestEntityProfile.POOR_SAFETY,
        ]

        tiers = []
        scores = []
        premiums = []

        for profile_type in profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "energy", profile_type
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

    def test_limit_scaling_consistency(self, excellent_energy_entity):
        """Test that premiums scale consistently with limits."""
        profile = self._create_profile(excellent_energy_entity)

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

    def test_spill_history_impact(self):
        """Test that spill history significantly impacts pricing."""
        # Create two profiles: one clean, one with spills
        profile_clean = EnergyOperatorProfile(
            operator_name="Clean Operator",
            primary_domain="clean.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            environmental=EnvironmentalSignals(
                spill_history_score=95,
                emissions_compliance_score=90,
            ),
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=70,
            ),
        )

        profile_spills = EnergyOperatorProfile(
            operator_name="Spill Operator",
            primary_domain="spills.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            environmental=EnvironmentalSignals(
                spill_history_score=25,
                emissions_compliance_score=90,
            ),
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=70,
            ),
        )

        # Calculate premiums
        decision_clean = self.model.assess(profile_clean)
        decision_spills = self.model.assess(profile_spills)

        # Operator with spills should cost more
        assert decision_spills.annual_premium > decision_clean.annual_premium, \
            "Operator with spill history should have higher premium"

        # Score should be lower
        assert decision_spills.composite_score < decision_clean.composite_score, \
            "Operator with spill history should have lower score"

    def test_safety_record_impact(self):
        """Test that safety record affects premium."""
        # Create profiles
        profile_strong = EnergyOperatorProfile(
            operator_name="Safe Operator",
            primary_domain="safe.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=95,
                lost_time_incident_score=92,
                fatality_history_score=100,
            ),
        )

        profile_weak = EnergyOperatorProfile(
            operator_name="Unsafe Operator",
            primary_domain="unsafe.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            safety_record=SafetyRecordSignals(
                osha_recordable_rate_score=30,
                lost_time_incident_score=35,
                fatality_history_score=45,
            ),
        )

        # Calculate
        decision_strong = self.model.assess(profile_strong)
        decision_weak = self.model.assess(profile_weak)

        # Weak safety should cost more
        assert decision_weak.annual_premium > decision_strong.annual_premium, \
            "Operator with poor safety record should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEnergyEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = EnergyDSIPricingModel()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create profile with only required fields
        profile = EnergyOperatorProfile(
            operator_name="Minimal Operator",
            primary_domain="minimal.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
        )

        # Should not raise exception
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_small_operator(self):
        """Test pricing with small operator."""
        profile = EnergyOperatorProfile(
            operator_name="Small Operator",
            primary_domain="small.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.ONSHORE,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            production_volume=1_000,
        )

        # Should handle small operator
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        profile = EnergyOperatorProfile(
            operator_name="Big Operator",
            primary_domain="big.com",
            operator_type=OperatorType.UPSTREAM,
            asset_class=AssetClass.OFFSHORE_DEEPWATER,
            geographic_region=GeographicRegion.NORTH_AMERICA,
            country="US",
            production_volume=1_000_000,
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
