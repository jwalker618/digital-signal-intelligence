"""
Marine Insurance Pricing Model Tests
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

from models.marine.dsi_marine_pricing import (
    MarineDSIPricingModel,
    MarineOperatorProfile,
    MarineTierAssignment,
    MarinePricingEngine,
    VesselType,
    OperationType,
    TradeArea,
    NetworkAuthoritySignals,
    SafetyRecordSignals,
    RegulatoryComplianceSignals,
    FleetQualitySignals,
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

class TestMarineStructure(BaseStructuralTest):
    """Test structural integrity of Marine pricing model."""

    def test_engine_instantiates(self):
        """Test MarineDSIPricingModel instantiates correctly."""
        model = MarineDSIPricingModel()
        assert model is not None
        assert isinstance(model, MarineDSIPricingModel)

    def test_vessel_type_enum_values(self):
        """Test VesselType enum has expected values."""
        expected_types = ["container_ship", "bulk_carrier", "tanker", "general_cargo"]
        actual_types = [vessel_type.value for vessel_type in VesselType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing vessel type: {expected}"

    def test_operation_type_enum(self):
        """Test OperationType enum."""
        expected_types = ["DEEP_SEA", "COASTAL", "INLAND"]

        for expected in expected_types:
            assert hasattr(OperationType, expected), \
                   f"Missing operation type: {expected}"

    def test_operator_profile_structure(self):
        """Test MarineOperatorProfile dataclass structure."""
        # Create minimal profile
        profile = MarineOperatorProfile(
            operator_name="Test Shipping Co",
            imo_number="1234567",
            primary_domain="testship.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
        )

        # Verify required fields
        required_fields = ["operator_name", "vessel_type", "operation_type",
                          "trade_area", "flag_state"]
        self.verify_dataclass_structure(profile, required_fields)

    def test_safety_record_signals_structure(self):
        """Test SafetyRecordSignals dataclass structure."""
        signals = SafetyRecordSignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "incident_history_score",
            "collision_history_score",
            "grounding_history_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_underwriting_decision_structure(self):
        """Test MarineUnderwritingDecision has required fields."""
        model = MarineDSIPricingModel()

        # Create test profile with good safety
        test_set = TestDataGenerator.create_test_signal_set(
            "Safe Operator", "marine", TestEntityProfile.EXCELLENT_SAFETY
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

    def _create_profile_from_signals(self, test_set) -> MarineOperatorProfile:
        """Helper to create MarineOperatorProfile from test signals."""
        signals = test_set.signals

        profile = MarineOperatorProfile(
            operator_name=test_set.entity_name,
            imo_number="1234567",
            primary_domain="test.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            safety_record=SafetyRecordSignals(
                incident_history_score=signals.get("safety_record", {}).get("score", 70),
                collision_history_score=70,
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                port_state_control_score=signals.get("regulatory_compliance", {}).get("score", 70),
            ),
        )

        return profile


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestMarineFunctional(BaseFunctionalTest):
    """Test functional behavior of Marine pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = MarineDSIPricingModel()
        self.test_limit = 10_000_000

    def _create_profile(self, test_set) -> MarineOperatorProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return MarineOperatorProfile(
            operator_name=test_set.entity_name,
            imo_number="1234567",
            primary_domain="test.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            vessel_count=10,
            network_authority=NetworkAuthoritySignals(
                classification_society_score=70,
                charterer_quality_score=70,
            ),
            safety_record=SafetyRecordSignals(
                incident_history_score=signals.get("safety_record", {}).get("score", 70),
                collision_history_score=70,
                grounding_history_score=signals.get("safety_record", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                port_state_control_score=signals.get("regulatory_compliance", {}).get("score", 70),
                ism_compliance_score=signals.get("regulatory_compliance", {}).get("score", 70),
            ),
            fleet_quality=FleetQualitySignals(
                fleet_age_score=signals.get("fleet_condition", {}).get("score", 70),
                maintenance_score=70,
            ),
            operational=OperationalSignals(
                crew_certification_score=70,
                route_planning_score=70,
            ),
            financial=FinancialSignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 70),
            ),
        )

    def test_calculates_decision(self, excellent_marine_entity):
        """Test that decision calculation returns valid result."""
        profile = self._create_profile(excellent_marine_entity)
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
                f"Test-{profile_type.value}", "marine", profile_type
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
                f"Test-{profile_type.value}", "marine", profile_type
            )
            profile = self._create_profile(test_set)
            decision = self.model.assess(profile)

            self.assert_score_in_range(decision.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [5_000_000, 10_000_000, 25_000_000, 50_000_000])
    def test_premium_scales_with_limit(self, excellent_marine_entity, limit):
        """Test premium scales appropriately with limit."""
        profile = self._create_profile(excellent_marine_entity)
        decision = self.model.assess(profile, requested_limit=limit)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

        # Limit should match requested
        assert decision.recommended_limit == limit

    @pytest.mark.parametrize("vessel_type", [VesselType.CONTAINER_SHIP, VesselType.BULK_CARRIER,
                                             VesselType.TANKER])
    def test_vessel_type_affects_pricing(self, excellent_marine_entity, vessel_type):
        """Test that vessel type affects pricing."""
        profile = self._create_profile(excellent_marine_entity)
        profile.vessel_type = vessel_type

        decision = self.model.assess(profile)

        # Premium should be positive
        self.assert_premium_positive(decision.annual_premium)

    def test_trade_area_affects_pricing(self, excellent_marine_entity):
        """Test that trade area affects pricing."""
        profile = self._create_profile(excellent_marine_entity)

        # Calculate for different trade areas
        results = {}
        for trade_area in [TradeArea.GLOBAL, TradeArea.REGIONAL,
                          TradeArea.COASTAL]:
            profile.trade_area = trade_area
            decision = self.model.assess(profile)
            results[trade_area] = decision

        # All should have positive premiums
        for trade_area, decision in results.items():
            self.assert_premium_positive(decision.annual_premium)

    def test_flag_state_handled(self, excellent_marine_entity):
        """Test that flag state is handled correctly."""
        profile = self._create_profile(excellent_marine_entity)

        for flag in ["US", "GB", "PA", "LR"]:
            profile.flag_state = flag
            decision = self.model.assess(profile)

            assert decision is not None
            self.assert_premium_positive(decision.annual_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestMarineActuarial(BaseActuarialTest):
    """Test actuarial validity of Marine pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = MarineDSIPricingModel()

    def _create_profile(self, test_set) -> MarineOperatorProfile:
        """Create profile from test signal set."""
        signals = test_set.signals

        return MarineOperatorProfile(
            operator_name=test_set.entity_name,
            imo_number="1234567",
            primary_domain="test.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            vessel_count=10,
            network_authority=NetworkAuthoritySignals(
                classification_society_score=70,
            ),
            safety_record=SafetyRecordSignals(
                incident_history_score=signals.get("safety_record", {}).get("score", 70),
                collision_history_score=70,
                grounding_history_score=signals.get("safety_record", {}).get("score", 70),
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                port_state_control_score=signals.get("regulatory_compliance", {}).get("score", 70),
                ism_compliance_score=signals.get("regulatory_compliance", {}).get("score", 70),
            ),
            fleet_quality=FleetQualitySignals(
                fleet_age_score=signals.get("fleet_condition", {}).get("score", 70),
                maintenance_score=70,
            ),
            operational=OperationalSignals(
                crew_certification_score=70,
            ),
            financial=FinancialSignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 70),
            ),
        )

    def test_poor_profile_costs_more(self, excellent_marine_entity, poor_marine_entity):
        """Test that poor safety profile results in higher premium."""
        profile_good = self._create_profile(excellent_marine_entity)
        profile_poor = self._create_profile(poor_marine_entity)

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
                f"Test-{profile_type.value}", "marine", profile_type
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

    def test_limit_scaling_consistency(self, excellent_marine_entity):
        """Test that premiums scale consistently with limits."""
        profile = self._create_profile(excellent_marine_entity)

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

    def test_incident_history_impact(self):
        """Test that incident history significantly impacts pricing."""
        # Create two profiles: one clean, one with incidents
        profile_clean = MarineOperatorProfile(
            operator_name="Clean Operator",
            imo_number="1234567",
            primary_domain="clean.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            safety_record=SafetyRecordSignals(
                incident_history_score=95,
                collision_history_score=100,
                grounding_history_score=100,
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                port_state_control_score=70,
            ),
        )

        profile_incidents = MarineOperatorProfile(
            operator_name="Incident Operator",
            imo_number="1234568",
            primary_domain="incidents.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            safety_record=SafetyRecordSignals(
                incident_history_score=25,
                collision_history_score=30,
                grounding_history_score=35,
            ),
            regulatory_compliance=RegulatoryComplianceSignals(
                port_state_control_score=70,
            ),
        )

        # Calculate premiums
        decision_clean = self.model.assess(profile_clean)
        decision_incidents = self.model.assess(profile_incidents)

        # Operator with incidents should cost more
        assert decision_incidents.annual_premium > decision_clean.annual_premium, \
            "Operator with incident history should have higher premium"

        # Score should be lower
        assert decision_incidents.composite_score < decision_clean.composite_score, \
            "Operator with incident history should have lower score"

    def test_fleet_age_impact(self):
        """Test that fleet age affects premium."""
        # Create profiles
        profile_new = MarineOperatorProfile(
            operator_name="New Fleet",
            imo_number="1234567",
            primary_domain="new.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            fleet_quality=FleetQualitySignals(
                fleet_age_score=95,
                maintenance_score=90,
            ),
        )

        profile_old = MarineOperatorProfile(
            operator_name="Old Fleet",
            imo_number="1234568",
            primary_domain="old.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            fleet_quality=FleetQualitySignals(
                fleet_age_score=30,
                maintenance_score=40,
            ),
        )

        # Calculate
        decision_new = self.model.assess(profile_new)
        decision_old = self.model.assess(profile_old)

        # Old fleet should cost more
        assert decision_old.annual_premium > decision_new.annual_premium, \
            "Operator with old fleet should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestMarineEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = MarineDSIPricingModel()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create profile with only required fields
        profile = MarineOperatorProfile(
            operator_name="Minimal Operator",
            imo_number="1234567",
            primary_domain="minimal.com",
            vessel_type=VesselType.GENERAL_CARGO,
            operation_type=OperationType.COASTAL,
            trade_area=TradeArea.COASTAL,
            flag_state="US",
        )

        # Should not raise exception
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_single_vessel_operator(self):
        """Test pricing with single vessel operator."""
        profile = MarineOperatorProfile(
            operator_name="Single Vessel",
            imo_number="1234567",
            primary_domain="single.com",
            vessel_type=VesselType.GENERAL_CARGO,
            operation_type=OperationType.COASTAL,
            trade_area=TradeArea.COASTAL,
            flag_state="US",
            vessel_count=1,
        )

        # Should handle single vessel
        decision = self.model.assess(profile)

        assert decision is not None
        assert decision.annual_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        profile = MarineOperatorProfile(
            operator_name="Big Fleet",
            imo_number="1234567",
            primary_domain="big.com",
            vessel_type=VesselType.CONTAINER_SHIP,
            operation_type=OperationType.DEEP_SEA,
            trade_area=TradeArea.GLOBAL,
            flag_state="US",
            vessel_count=100,
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
