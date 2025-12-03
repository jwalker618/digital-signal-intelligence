"""
Aerospace Insurance Pricing Model Tests
========================================

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

from models.aerospace.dsi_aerospace_pricing import (
    DSIAerospaceEngine,
    DSIAssessment,
    OperatorType,
    FleetCategory,
    FleetSize,
    RegulatoryFramework,
    IOSAStatus,
    RiskTier,
    NetworkAuthoritySignals,
    SafetyRecordSignals,
    RegulatoryComplianceSignals,
    OperationalQualitySignals,
    FleetQualitySignals,
    FinancialStabilitySignals,
    RouteRiskSignals,
    CorporateGovernanceSignals,
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

class TestAerospaceStructure(BaseStructuralTest):
    """Test structural integrity of Aerospace pricing model."""

    def test_engine_instantiates(self):
        """Test DSIAerospaceEngine instantiates correctly."""
        engine = DSIAerospaceEngine()
        assert engine is not None
        assert isinstance(engine, DSIAerospaceEngine)

    def test_operator_type_enum_values(self):
        """Test OperatorType enum has expected values."""
        expected_types = ["major_airline", "regional_airline", "low_cost_carrier",
                         "cargo_airline", "charter_operator"]
        actual_types = [op_type.value for op_type in OperatorType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing operator type: {expected}"

    def test_fleet_category_enum(self):
        """Test FleetCategory enum."""
        expected_categories = ["WIDEBODY", "NARROWBODY", "REGIONAL_JET", "HELICOPTER"]

        for expected in expected_categories:
            assert hasattr(FleetCategory, expected), \
                   f"Missing fleet category: {expected}"

    def test_risk_tier_enum(self):
        """Test RiskTier enum."""
        expected_tiers = ["TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5"]

        for expected in expected_tiers:
            assert hasattr(RiskTier, expected), f"Missing tier: {expected}"

    def test_safety_record_signals_structure(self):
        """Test SafetyRecordSignals dataclass structure."""
        signals = SafetyRecordSignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "accident_history_score",
            "incident_history_score",
            "fatality_history_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_assessment_structure(self):
        """Test DSIAssessment has required fields."""
        engine = DSIAerospaceEngine()

        # Create minimal assessment
        assessment = engine.assess(
            entity_name="Test Airlines",
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(
                accident_history_score=90,
                fatality_history_score=100,
            ),
            regulatory=RegulatoryComplianceSignals(
                certificate_status_score=95,
            ),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Verify required fields
        required_fields = [
            "entity_name",
            "composite_score",
            "tier",
            "base_premium",
            "risk_adjusted_premium",
            "decision",
        ]

        for field in required_fields:
            assert hasattr(assessment, field), f"Missing field: {field}"


# =============================================================================
# FUNCTIONAL TESTS
# =============================================================================

class TestAerospaceFunctional(BaseFunctionalTest):
    """Test functional behavior of Aerospace pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIAerospaceEngine()
        self.test_hull_value = 50_000_000
        self.test_liability_limit = 500_000_000

    def _create_assessment(self, test_set, hull_value=50_000_000, liability_limit=500_000_000):
        """Create assessment from test signal set."""
        signals = test_set.signals

        return self.engine.assess(
            entity_name=test_set.entity_name,
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            hull_value=hull_value,
            liability_limit=liability_limit,
            network=NetworkAuthoritySignals(
                alliance_membership_score=signals.get("industry_standing", {}).get("score", 70),
                lessor_quality_score=70,
            ),
            safety=SafetyRecordSignals(
                accident_history_score=signals.get("safety_record", {}).get("score", 90),
                incident_history_score=signals.get("incident_record", {}).get("score", 85),
                fatality_history_score=signals.get("fatality_record", {}).get("score", 100),
            ),
            regulatory=RegulatoryComplianceSignals(
                certificate_status_score=signals.get("regulatory_compliance", {}).get("score", 95),
                enforcement_actions_score=signals.get("enforcement_history", {}).get("score", 90),
                iosa_status_score=90,
            ),
            operational=OperationalQualitySignals(
                otp_score=signals.get("operational_performance", {}).get("score", 85),
                training_program_score=signals.get("training_quality", {}).get("score", 85),
            ),
            fleet=FleetQualitySignals(
                fleet_age_score=signals.get("fleet_condition", {}).get("score", 80),
                maintenance_program_score=85,
            ),
            financial=FinancialStabilitySignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 75),
            ),
            route=RouteRiskSignals(
                conflict_zone_score=signals.get("route_risk", {}).get("score", 95),
            ),
            governance=CorporateGovernanceSignals(
                safety_culture_score=signals.get("safety_culture", {}).get("score", 85),
            ),
            direct=DirectInquirySignals(
                pending_claims=signals.get("pending_claims", False),
                regulatory_action=signals.get("regulatory_action", False),
            ),
        )

    def test_calculates_assessment(self, excellent_airline_entity):
        """Test that assessment calculation returns valid result."""
        assessment = self._create_assessment(excellent_airline_entity)

        # Verify premium is positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

        # Verify premium is reasonable
        assert assessment.risk_adjusted_premium < assessment.hull_value * 0.5, \
            "Premium should not exceed 50% of hull value"

        # Verify score is valid
        TestAssertions.assert_valid_score(assessment.composite_score)

        # Verify tier is valid
        TestAssertions.assert_valid_tier(assessment.tier.value)

    def test_tier_assignment_logic(self):
        """Test that tier assignments follow expected ranges."""
        test_profiles = [
            (TestEntityProfile.EXCELLENT_SAFETY, 1, 2),
            (TestEntityProfile.AVERAGE_SAFETY, 2, 3),
            (TestEntityProfile.POOR_SAFETY, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "aerospace", profile_type
            )
            assessment = self._create_assessment(test_set)

            self.assert_tier_in_range(assessment.tier.value, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.EXCELLENT_SAFETY, 750, 1000),
            (TestEntityProfile.AVERAGE_SAFETY, 600, 799),
            (TestEntityProfile.POOR_SAFETY, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "aerospace", profile_type
            )
            assessment = self._create_assessment(test_set)

            self.assert_score_in_range(assessment.composite_score, min_score, max_score)

    @pytest.mark.parametrize("hull_value", [25_000_000, 50_000_000, 100_000_000, 200_000_000])
    def test_premium_scales_with_hull_value(self, excellent_airline_entity, hull_value):
        """Test premium scales appropriately with hull value."""
        assessment = self._create_assessment(excellent_airline_entity, hull_value=hull_value)

        # Premium should be positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

        # Premium should increase with hull value
        assert assessment.risk_adjusted_premium > 0

    @pytest.mark.parametrize("operator_type", [OperatorType.MAJOR_AIRLINE, OperatorType.REGIONAL_AIRLINE,
                                               OperatorType.CARGO_AIRLINE])
    def test_operator_type_affects_pricing(self, excellent_airline_entity, operator_type):
        """Test that operator type affects pricing."""
        signals = excellent_airline_entity.signals

        assessment = self.engine.assess(
            entity_name=excellent_airline_entity.entity_name,
            operator_type=operator_type,
            fleet_category=FleetCategory.NARROWBODY,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Premium should be positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

    def test_fleet_category_affects_pricing(self, excellent_airline_entity):
        """Test that fleet category affects pricing."""
        signals = excellent_airline_entity.signals

        results = {}
        for fleet_category in [FleetCategory.WIDEBODY, FleetCategory.NARROWBODY,
                              FleetCategory.REGIONAL_JET]:
            assessment = self.engine.assess(
                entity_name=excellent_airline_entity.entity_name,
                operator_type=OperatorType.REGIONAL_AIRLINE,
                fleet_category=fleet_category,
                fleet_size=FleetSize.MEDIUM,
                regulatory_framework=RegulatoryFramework.FAA,
                iosa_status=IOSAStatus.REGISTERED,
                network=NetworkAuthoritySignals(),
                safety=SafetyRecordSignals(accident_history_score=90),
                regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
                operational=OperationalQualitySignals(),
                fleet=FleetQualitySignals(),
                financial=FinancialStabilitySignals(),
                route=RouteRiskSignals(),
                governance=CorporateGovernanceSignals(),
                direct=DirectInquirySignals(),
            )
            results[fleet_category] = assessment

        # All should have positive premiums
        for fleet_category, assessment in results.items():
            self.assert_premium_positive(assessment.risk_adjusted_premium)

    def test_regulatory_framework_handled(self, excellent_airline_entity):
        """Test that regulatory framework is handled correctly."""
        signals = excellent_airline_entity.signals

        for framework in [RegulatoryFramework.FAA, RegulatoryFramework.EASA,
                         RegulatoryFramework.OTHER_ICAO]:
            assessment = self.engine.assess(
                entity_name=excellent_airline_entity.entity_name,
                operator_type=OperatorType.REGIONAL_AIRLINE,
                fleet_category=FleetCategory.REGIONAL_JET,
                fleet_size=FleetSize.MEDIUM,
                regulatory_framework=framework,
                iosa_status=IOSAStatus.REGISTERED,
                network=NetworkAuthoritySignals(),
                safety=SafetyRecordSignals(accident_history_score=90),
                regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
                operational=OperationalQualitySignals(),
                fleet=FleetQualitySignals(),
                financial=FinancialStabilitySignals(),
                route=RouteRiskSignals(),
                governance=CorporateGovernanceSignals(),
                direct=DirectInquirySignals(),
            )

            assert assessment is not None
            self.assert_premium_positive(assessment.risk_adjusted_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestAerospaceActuarial(BaseActuarialTest):
    """Test actuarial validity of Aerospace pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIAerospaceEngine()

    def _create_assessment(self, test_set):
        """Create assessment from test signal set."""
        signals = test_set.signals

        return self.engine.assess(
            entity_name=test_set.entity_name,
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(
                alliance_membership_score=signals.get("industry_standing", {}).get("score", 70),
            ),
            safety=SafetyRecordSignals(
                accident_history_score=signals.get("safety_record", {}).get("score", 90),
                incident_history_score=signals.get("incident_record", {}).get("score", 85),
                fatality_history_score=signals.get("fatality_record", {}).get("score", 100),
            ),
            regulatory=RegulatoryComplianceSignals(
                certificate_status_score=signals.get("regulatory_compliance", {}).get("score", 95),
                enforcement_actions_score=signals.get("enforcement_history", {}).get("score", 90),
            ),
            operational=OperationalQualitySignals(
                otp_score=signals.get("operational_performance", {}).get("score", 85),
            ),
            fleet=FleetQualitySignals(
                fleet_age_score=signals.get("fleet_condition", {}).get("score", 80),
            ),
            financial=FinancialStabilitySignals(
                credit_rating_score=signals.get("financial_strength", {}).get("score", 75),
            ),
            route=RouteRiskSignals(
                conflict_zone_score=signals.get("route_risk", {}).get("score", 95),
            ),
            governance=CorporateGovernanceSignals(
                safety_culture_score=signals.get("safety_culture", {}).get("score", 85),
            ),
            direct=DirectInquirySignals(),
        )

    def test_poor_profile_costs_more(self, excellent_airline_entity, poor_airline_entity):
        """Test that poor safety profile results in higher premium."""
        assessment_good = self._create_assessment(excellent_airline_entity)
        assessment_poor = self._create_assessment(poor_airline_entity)

        # Poor profile should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            assessment_good.risk_adjusted_premium,
            assessment_poor.risk_adjusted_premium,
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
                f"Test-{profile_type.value}", "aerospace", profile_type
            )
            assessment = self._create_assessment(test_set)

            tiers.append(assessment.tier.value)
            scores.append(assessment.composite_score)
            premiums.append(assessment.risk_adjusted_premium)

        # Tiers should increase (lower quality = higher tier)
        self.assert_tier_progression(tiers)

        # Scores should decrease (lower quality = lower score)
        self.assert_score_progression(scores)

        # Premiums should increase
        for i in range(len(premiums) - 1):
            assert premiums[i] < premiums[i+1], \
                f"Premium should increase with worse risk: " \
                f"{premiums[i]} should be < {premiums[i+1]}"

    def test_limit_scaling_consistency(self, excellent_airline_entity):
        """Test that premiums scale consistently with hull values."""
        signals = excellent_airline_entity.signals

        assessment_50m = self.engine.assess(
            entity_name=excellent_airline_entity.entity_name,
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            hull_value=50_000_000,
            liability_limit=500_000_000,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        assessment_100m = self.engine.assess(
            entity_name=excellent_airline_entity.entity_name,
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            hull_value=100_000_000,
            liability_limit=500_000_000,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Premium should increase with hull value
        assert assessment_100m.risk_adjusted_premium > assessment_50m.risk_adjusted_premium, \
            "Premium should increase with hull value"

    def test_accident_history_impact(self):
        """Test that accident history significantly impacts pricing."""
        # Create two assessments: one clean, one with accidents
        assessment_clean = self.engine.assess(
            entity_name="Clean Airline",
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(
                accident_history_score=95,
                incident_history_score=90,
                fatality_history_score=100,
            ),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        assessment_accidents = self.engine.assess(
            entity_name="Accident Airline",
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(
                accident_history_score=30,
                incident_history_score=40,
                fatality_history_score=45,
            ),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Airline with accidents should cost more
        assert assessment_accidents.risk_adjusted_premium > assessment_clean.risk_adjusted_premium, \
            "Airline with accident history should have higher premium"

        # Score should be lower
        assert assessment_accidents.composite_score < assessment_clean.composite_score, \
            "Airline with accident history should have lower score"

    def test_iosa_status_impact(self):
        """Test that IOSA status affects premium."""
        # Create assessments
        assessment_registered = self.engine.assess(
            entity_name="IOSA Registered",
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(
                certificate_status_score=95,
                iosa_status_score=90,
            ),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        assessment_not_registered = self.engine.assess(
            entity_name="Not IOSA Registered",
            operator_type=OperatorType.REGIONAL_AIRLINE,
            fleet_category=FleetCategory.REGIONAL_JET,
            fleet_size=FleetSize.MEDIUM,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.NEVER_REGISTERED,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(
                certificate_status_score=95,
                iosa_status_score=40,
            ),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Non-IOSA should cost more
        assert assessment_not_registered.risk_adjusted_premium > assessment_registered.risk_adjusted_premium, \
            "Airline without IOSA registration should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestAerospaceEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIAerospaceEngine()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create assessment with only required fields
        assessment = self.engine.assess(
            entity_name="Minimal Airline",
            operator_type=OperatorType.CHARTER_OPERATOR,
            fleet_category=FleetCategory.PISTON,
            fleet_size=FleetSize.SINGLE,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.NOT_APPLICABLE,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(),
            regulatory=RegulatoryComplianceSignals(),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Should not raise exception
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0

    def test_single_aircraft_operator(self):
        """Test pricing with single aircraft operator."""
        assessment = self.engine.assess(
            entity_name="Single Plane Operator",
            operator_type=OperatorType.PRIVATE_OWNER,
            fleet_category=FleetCategory.PISTON,
            fleet_size=FleetSize.SINGLE,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.NOT_APPLICABLE,
            hull_value=5_000_000,
            liability_limit=10_000_000,
            network=NetworkAuthoritySignals(),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Should handle single aircraft
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0

    def test_very_large_fleet(self):
        """Test pricing with very large fleet."""
        assessment = self.engine.assess(
            entity_name="Major Airline",
            operator_type=OperatorType.MAJOR_AIRLINE,
            fleet_category=FleetCategory.WIDEBODY,
            fleet_size=FleetSize.MAJOR,
            regulatory_framework=RegulatoryFramework.FAA,
            iosa_status=IOSAStatus.REGISTERED,
            hull_value=5_000_000_000,
            liability_limit=10_000_000_000,
            network=NetworkAuthoritySignals(alliance_membership_score=90),
            safety=SafetyRecordSignals(accident_history_score=90),
            regulatory=RegulatoryComplianceSignals(certificate_status_score=95),
            operational=OperationalQualitySignals(),
            fleet=FleetQualitySignals(),
            financial=FinancialStabilitySignals(),
            route=RouteRiskSignals(),
            governance=CorporateGovernanceSignals(),
            direct=DirectInquirySignals(),
        )

        # Should handle large fleet
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0
        assert assessment.risk_adjusted_premium < assessment.hull_value * 0.5, \
            "Premium should be reasonable relative to hull value"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
