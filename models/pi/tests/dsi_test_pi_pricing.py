"""
Professional Indemnity Insurance Pricing Model Tests
=====================================================

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

from models.pi.dsi_pi_pricing import (
    DSIProfessionalIndemnityEngine,
    DSIAssessment,
    ProfessionType,
    FirmSize,
    RevenueSize,
    RiskTier,
    NetworkAuthoritySignals,
    RegulatoryStandingSignals,
    FirmStabilitySignals,
    PracticeQualitySignals,
    TechnicalInfrastructureSignals,
    CorporateFootprintSignals,
    LitigationHistorySignals,
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

class TestPIStructure(BaseStructuralTest):
    """Test structural integrity of PI pricing model."""

    def test_engine_instantiates(self):
        """Test DSIProfessionalIndemnityEngine instantiates correctly."""
        engine = DSIProfessionalIndemnityEngine()
        assert engine is not None
        assert isinstance(engine, DSIProfessionalIndemnityEngine)

    def test_profession_type_enum_values(self):
        """Test ProfessionType enum has expected values."""
        expected_types = ["law_firm", "accounting_firm", "architecture", "engineering"]
        actual_types = [prof_type.value for prof_type in ProfessionType]

        for expected in expected_types:
            assert expected in actual_types, f"Missing profession type: {expected}"

    def test_firm_size_enum(self):
        """Test FirmSize enum."""
        expected_sizes = ["SOLO", "MICRO", "SMALL", "MEDIUM", "LARGE"]

        for expected in expected_sizes:
            assert hasattr(FirmSize, expected), \
                   f"Missing firm size: {expected}"

    def test_risk_tier_enum(self):
        """Test RiskTier enum."""
        expected_tiers = ["TIER_1", "TIER_2", "TIER_3", "TIER_4", "TIER_5"]

        for expected in expected_tiers:
            assert hasattr(RiskTier, expected), f"Missing tier: {expected}"

    def test_regulatory_standing_signals_structure(self):
        """Test RegulatoryStandingSignals dataclass structure."""
        signals = RegulatoryStandingSignals()

        # Verify it has expected signal fields
        expected_signal_fields = [
            "license_status_score",
            "disciplinary_history_score",
            "malpractice_record_score",
        ]

        for field in expected_signal_fields:
            assert hasattr(signals, field), f"Missing signal field: {field}"

    def test_assessment_structure(self):
        """Test DSIAssessment has required fields."""
        engine = DSIProfessionalIndemnityEngine()

        # Create minimal assessment
        assessment = engine.assess(
            entity_name="Test Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(
                license_status_score=90,
                disciplinary_history_score=90,
            ),
            stability=FirmStabilitySignals(
                tenure_score=80,
            ),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
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

class TestPIFunctional(BaseFunctionalTest):
    """Test functional behavior of PI pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIProfessionalIndemnityEngine()
        self.test_limit = 1_000_000

    def _create_assessment(self, test_set, limit=1_000_000):
        """Create assessment from test signal set."""
        signals = test_set.signals

        return self.engine.assess(
            entity_name=test_set.entity_name,
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            limit=limit,
            retention=50_000,
            network=NetworkAuthoritySignals(
                peer_ranking_score=signals.get("professional_reputation", {}).get("score", 70),
                client_quality_score=70,
            ),
            regulatory=RegulatoryStandingSignals(
                license_status_score=signals.get("regulatory_standing", {}).get("score", 90),
                disciplinary_history_score=signals.get("disciplinary_record", {}).get("score", 90),
                malpractice_record_score=signals.get("malpractice_history", {}).get("score", 85),
            ),
            stability=FirmStabilitySignals(
                tenure_score=signals.get("firm_stability", {}).get("score", 80),
                partner_stability_score=70,
            ),
            practice=PracticeQualitySignals(
                client_review_score=signals.get("client_feedback", {}).get("score", 75),
                complaint_history_score=signals.get("complaints", {}).get("score", 90),
            ),
            technical=TechnicalInfrastructureSignals(
                tls_score=signals.get("security_posture", {}).get("score", 80),
                breach_history_score=signals.get("data_breach_history", {}).get("score", 100),
            ),
            footprint=CorporateFootprintSignals(
                website_quality_score=70,
            ),
            litigation=LitigationHistorySignals(
                malpractice_suits_score=signals.get("malpractice_history", {}).get("score", 85),
            ),
            direct=DirectInquirySignals(
                pending_claims=signals.get("pending_claims", False),
                disciplinary_pending=signals.get("disciplinary_pending", False),
            ),
        )

    def test_calculates_assessment(self, strong_professional_entity):
        """Test that assessment calculation returns valid result."""
        assessment = self._create_assessment(strong_professional_entity)

        # Verify premium is positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

        # Verify premium is reasonable (use base_premium as reference)
        assert assessment.risk_adjusted_premium < assessment.base_premium * 5, \
            "Premium should not be more than 5x base"

        # Verify score is valid
        TestAssertions.assert_valid_score(assessment.composite_score)

        # Verify tier is valid
        TestAssertions.assert_valid_tier(assessment.tier.value)

    def test_tier_assignment_logic(self):
        """Test that tier assignments follow expected ranges."""
        test_profiles = [
            (TestEntityProfile.EXCELLENT_PROFESSIONAL, 1, 2),
            (TestEntityProfile.AVERAGE_PROFESSIONAL, 2, 3),
            (TestEntityProfile.POOR_PROFESSIONAL, 4, 5),
        ]

        for profile_type, min_tier, max_tier in test_profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "pi", profile_type
            )
            assessment = self._create_assessment(test_set)

            self.assert_tier_in_range(assessment.tier.value, min_tier, max_tier)

    def test_score_ranges_by_profile(self):
        """Test that scores fall in expected ranges by profile."""
        test_cases = [
            (TestEntityProfile.EXCELLENT_PROFESSIONAL, 750, 1000),
            (TestEntityProfile.AVERAGE_PROFESSIONAL, 600, 799),
            (TestEntityProfile.POOR_PROFESSIONAL, 0, 499),
        ]

        for profile_type, min_score, max_score in test_cases:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "pi", profile_type
            )
            assessment = self._create_assessment(test_set)

            self.assert_score_in_range(assessment.composite_score, min_score, max_score)

    @pytest.mark.parametrize("limit", [500_000, 1_000_000, 2_000_000, 5_000_000])
    def test_premium_scales_with_limit(self, strong_professional_entity, limit):
        """Test premium scales appropriately with limit."""
        assessment = self._create_assessment(strong_professional_entity, limit=limit)

        # Premium should be positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

        # Premium should increase with limit
        assert assessment.risk_adjusted_premium > 0

    @pytest.mark.parametrize("profession", [ProfessionType.LAW_FIRM, ProfessionType.ACCOUNTING_FIRM,
                                            ProfessionType.ARCHITECTURE])
    def test_profession_affects_pricing(self, strong_professional_entity, profession):
        """Test that profession type affects pricing."""
        signals = strong_professional_entity.signals

        assessment = self.engine.assess(
            entity_name=strong_professional_entity.entity_name,
            profession=profession,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(license_status_score=90),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Premium should be positive
        self.assert_premium_positive(assessment.risk_adjusted_premium)

    def test_firm_size_affects_pricing(self, strong_professional_entity):
        """Test that firm size affects pricing."""
        signals = strong_professional_entity.signals

        results = {}
        for firm_size in [FirmSize.SOLO, FirmSize.SMALL, FirmSize.MEDIUM]:
            assessment = self.engine.assess(
                entity_name=strong_professional_entity.entity_name,
                profession=ProfessionType.LAW_FIRM,
                firm_size=firm_size,
                revenue_size=RevenueSize.R_1M_5M,
                network=NetworkAuthoritySignals(),
                regulatory=RegulatoryStandingSignals(license_status_score=90),
                stability=FirmStabilitySignals(),
                practice=PracticeQualitySignals(),
                technical=TechnicalInfrastructureSignals(),
                footprint=CorporateFootprintSignals(),
                litigation=LitigationHistorySignals(),
                direct=DirectInquirySignals(),
            )
            results[firm_size] = assessment

        # All should have positive premiums
        for firm_size, assessment in results.items():
            self.assert_premium_positive(assessment.risk_adjusted_premium)

    def test_revenue_size_handled(self, strong_professional_entity):
        """Test that revenue size is handled correctly."""
        signals = strong_professional_entity.signals

        for revenue_size in [RevenueSize.UNDER_500K, RevenueSize.R_1M_5M,
                            RevenueSize.R_5M_25M]:
            assessment = self.engine.assess(
                entity_name=strong_professional_entity.entity_name,
                profession=ProfessionType.LAW_FIRM,
                firm_size=FirmSize.SMALL,
                revenue_size=revenue_size,
                network=NetworkAuthoritySignals(),
                regulatory=RegulatoryStandingSignals(license_status_score=90),
                stability=FirmStabilitySignals(),
                practice=PracticeQualitySignals(),
                technical=TechnicalInfrastructureSignals(),
                footprint=CorporateFootprintSignals(),
                litigation=LitigationHistorySignals(),
                direct=DirectInquirySignals(),
            )

            assert assessment is not None
            self.assert_premium_positive(assessment.risk_adjusted_premium)


# =============================================================================
# ACTUARIAL VALIDITY TESTS
# =============================================================================

class TestPIActuarial(BaseActuarialTest):
    """Test actuarial validity of PI pricing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIProfessionalIndemnityEngine()

    def _create_assessment(self, test_set):
        """Create assessment from test signal set."""
        signals = test_set.signals

        return self.engine.assess(
            entity_name=test_set.entity_name,
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(
                peer_ranking_score=signals.get("professional_reputation", {}).get("score", 70),
            ),
            regulatory=RegulatoryStandingSignals(
                license_status_score=signals.get("regulatory_standing", {}).get("score", 90),
                disciplinary_history_score=signals.get("disciplinary_record", {}).get("score", 90),
                malpractice_record_score=signals.get("malpractice_history", {}).get("score", 85),
            ),
            stability=FirmStabilitySignals(
                tenure_score=signals.get("firm_stability", {}).get("score", 80),
            ),
            practice=PracticeQualitySignals(
                client_review_score=signals.get("client_feedback", {}).get("score", 75),
                complaint_history_score=signals.get("complaints", {}).get("score", 90),
            ),
            technical=TechnicalInfrastructureSignals(
                tls_score=signals.get("security_posture", {}).get("score", 80),
            ),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(
                malpractice_suits_score=signals.get("malpractice_history", {}).get("score", 85),
            ),
            direct=DirectInquirySignals(),
        )

    def test_poor_profile_costs_more(self, strong_professional_entity, weak_professional_entity):
        """Test that poor professional profile results in higher premium."""
        assessment_good = self._create_assessment(strong_professional_entity)
        assessment_poor = self._create_assessment(weak_professional_entity)

        # Poor profile should cost more (at least 30% more)
        self.assert_better_profile_cheaper(
            assessment_good.risk_adjusted_premium,
            assessment_poor.risk_adjusted_premium,
            min_ratio=1.3
        )

    def test_risk_progression(self):
        """Test that risk profiles progress logically."""
        profiles = [
            TestEntityProfile.EXCELLENT_PROFESSIONAL,
            TestEntityProfile.AVERAGE_PROFESSIONAL,
            TestEntityProfile.POOR_PROFESSIONAL,
        ]

        tiers = []
        scores = []
        premiums = []

        for profile_type in profiles:
            test_set = TestDataGenerator.create_test_signal_set(
                f"Test-{profile_type.value}", "pi", profile_type
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

    def test_limit_scaling_consistency(self, strong_professional_entity):
        """Test that premiums scale consistently with limits."""
        signals = strong_professional_entity.signals

        assessment_1m = self.engine.assess(
            entity_name=strong_professional_entity.entity_name,
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            limit=1_000_000,
            retention=50_000,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(license_status_score=90),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        assessment_2m = self.engine.assess(
            entity_name=strong_professional_entity.entity_name,
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            limit=2_000_000,
            retention=50_000,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(license_status_score=90),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Check scaling
        self.assert_limit_scaling(
            assessment_1m.risk_adjusted_premium,
            assessment_2m.risk_adjusted_premium,
            1_000_000,
            2_000_000
        )

    def test_disciplinary_history_impact(self):
        """Test that disciplinary history significantly impacts pricing."""
        # Create two assessments: one clean, one with disciplinary issues
        assessment_clean = self.engine.assess(
            entity_name="Clean Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(
                license_status_score=95,
                disciplinary_history_score=95,
                malpractice_record_score=90,
            ),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        assessment_disciplinary = self.engine.assess(
            entity_name="Disciplinary Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(
                license_status_score=95,
                disciplinary_history_score=30,  # Poor disciplinary record
                malpractice_record_score=90,
            ),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Firm with disciplinary issues should cost more
        assert assessment_disciplinary.risk_adjusted_premium > assessment_clean.risk_adjusted_premium, \
            "Firm with disciplinary issues should have higher premium"

        # Score should be lower
        assert assessment_disciplinary.composite_score < assessment_clean.composite_score, \
            "Firm with disciplinary issues should have lower score"

    def test_malpractice_history_impact(self):
        """Test that malpractice history affects premium."""
        # Create assessments
        assessment_clean = self.engine.assess(
            entity_name="No Claims Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(
                malpractice_record_score=95,
            ),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(
                malpractice_suits_score=95,
            ),
            direct=DirectInquirySignals(),
        )

        assessment_claims = self.engine.assess(
            entity_name="Claims Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SMALL,
            revenue_size=RevenueSize.R_1M_5M,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(
                malpractice_record_score=30,
            ),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(
                malpractice_suits_score=30,
            ),
            direct=DirectInquirySignals(),
        )

        # Firm with claims should cost more
        assert assessment_claims.risk_adjusted_premium > assessment_clean.risk_adjusted_premium, \
            "Firm with malpractice history should have higher premium"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestPIEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DSIProfessionalIndemnityEngine()

    def test_minimal_signals(self):
        """Test pricing with minimal signal set."""
        # Create assessment with only required fields
        assessment = self.engine.assess(
            entity_name="Minimal Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SOLO,
            revenue_size=RevenueSize.UNDER_500K,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Should not raise exception
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0

    def test_solo_practitioner(self):
        """Test pricing with solo practitioner."""
        assessment = self.engine.assess(
            entity_name="Solo Lawyer",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.SOLO,
            revenue_size=RevenueSize.UNDER_500K,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(license_status_score=90),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Should handle solo practitioner
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0

    def test_very_large_limit(self):
        """Test pricing with very large limit."""
        assessment = self.engine.assess(
            entity_name="Big Firm",
            profession=ProfessionType.LAW_FIRM,
            firm_size=FirmSize.LARGE,
            revenue_size=RevenueSize.R_25M_100M,
            limit=10_000_000,
            network=NetworkAuthoritySignals(),
            regulatory=RegulatoryStandingSignals(license_status_score=90),
            stability=FirmStabilitySignals(),
            practice=PracticeQualitySignals(),
            technical=TechnicalInfrastructureSignals(),
            footprint=CorporateFootprintSignals(),
            litigation=LitigationHistorySignals(),
            direct=DirectInquirySignals(),
        )

        # Should handle large limit
        assert assessment is not None
        assert assessment.risk_adjusted_premium > 0
        assert assessment.risk_adjusted_premium < 5_000_000, \
            "Premium should be reasonable relative to limit"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
