"""
DSI Test Framework - Base Classes and Fixtures
==============================================

Provides foundational test infrastructure for structural, functional,
and actuarial validity testing.

Author: John Walker
Version: 1.1.0

"""


import pytest
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abs import ABC, abstractmethod

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# TEST DATA GENERATORS
# =============================================================================

class TestEntityProfile(Enum):
    """Predefined entity profiles for actuarial validity testing."""

    # Excellent profiles (should get Tier 1-2)
    EXCELLENT_SAFETY = "excellent_safety"
    EXCELLENT_SECURITY = "excellent_security"
    STRONG_GOVERNANCE = "strong_governance"
    WELL_CAPITALIZED = "well_capitalized"

    # Average profiles (should get Tier 2-3)
    AVERAGE_SAFETY = "average_safety"
    AVERAGE_SECURITY = "average_security"
    STANDARD_GOVERNANCE = "standard_governance"
    ADEQUATE_CAPITAL = "adequate_capital"

    # Poor profiles (should get Tier 4-5)
    POOR_SAFETY = "poor_safety"
    POOR_SECURITY = "poor_security"
    WEAK_GOVERNANCE = "weak_governance"
    UNDERCAPITALIZED = "undercapitalized"

    # Edge cases
    MINIMAL_SIGNALS = "minimal_signals"
    MIXED_SIGNALS = "mixed_signals"
    NO_HISTORY = "no_history"


@dataclass
class TestSignalSet:
    """A complete set of test signals for an entity."""
    entity_id: str
    entity_name: str
    profile: TestEntityProfile
    signals: Dict[str, Any]
    expected_tier_range: Tuple[int, int]  # (min_tier, max_tier)
    expected_score_range: Tuple[int, int]  # (min_score, max_score)
    description: str
    coverage_type: str = ""

@dataclass
class HistoricalCase:
    """A historical incident case for retrospective validation testing."""
    case_id: str
    case_name: str
    incident_date: str
    incident_type: str
    pre_incident_signals: Dict[str, Any]
    expected_min_tier: int
    expected_flags: List[str]
    description: str    


class TestDataGenerator:
    """Generates consistent test data for all coverage types."""

    # =======================================================================
    # AEROSPACE SIGNALS
    # =======================================================================
    
    @staticmethod
    def generate_aerospace_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate aerospace sector test signals."""

        if profile == TestEntityProfile.EXCELLENT_SAFETY:
            return {
                # Safety signals
                "safety_record": {"score": 95, "accidents_5yr": 0, "hull_losses": 0},
                "incident_record": {"score": 92, "incidents_5yr": 1, "severity": "minor"},
                "fatality_record": {"score": 100, "fatalities_10yr": 0},

                # Regulatory signals
                "regulatory_compliance": {"score": 95, "status": "excellent"},
                "enforcement_history": {"score": 92, "actions_5yr": 0},
                "iosa_status": {"score": 95, "status": "registered", "audit_date": "2024-03"},

                # Operational signals
                "operational_performance": {"score": 90, "otp_rate": 0.87, "completion_rate": 0.995},
                "training_quality": {"score": 88, "program_rating": "A", "sim_hours": 120},
                "crew_experience": {"score": 85, "avg_hours_pic": 8500, "turnover_rate": 0.08},

                # Fleet signals
                "fleet_condition": {"score": 88, "avg_age": 6.2, "maintenance_ratio": 0.98},
                "fleet_modernization": {"score": 85, "new_gen_pct": 0.65},

                # Financial signals
                "financial_strength": {"score": 88, "rating": "A-", "debt_ratio": 0.45},
                "liquidity": {"score": 85, "cash_months": 8},

                # Route/operational risk
                "route_risk": {"score": 92, "conflict_exposure": 0.02, "terrain_challenging": 0.15},
                "weather_exposure": {"score": 88, "severe_weather_pct": 0.08},

                # Governance signals
                "safety_culture": {"score": 90, "sms_maturity": 4, "reporting_rate": 12.5},
                "management_stability": {"score": 88, "ceo_tenure": 6, "safety_director_tenure": 4},

                # Industry standing
                "industry_standing": {"score": 85, "alliance_member": True, "awards": 3},
                "market_position": {"score": 82, "market_share": 0.12},
            }

        elif profile == TestEntityProfile.AVERAGE_SAFETY:
            return {
                "safety_record": {"score": 72, "accidents_5yr": 1, "hull_losses": 0},
                "incident_record": {"score": 68, "incidents_5yr": 5, "severity": "moderate"},
                "fatality_record": {"score": 85, "fatalities_10yr": 0},

                "regulatory_compliance": {"score": 70, "status": "adequate"},
                "enforcement_history": {"score": 68, "actions_5yr": 2},
                "iosa_status": {"score": 70, "status": "registered", "audit_date": "2023-08"},

                "operational_performance": {"score": 68, "otp_rate": 0.76, "completion_rate": 0.98},
                "training_quality": {"score": 65, "program_rating": "B", "sim_hours": 80},
                "crew_experience": {"score": 62, "avg_hours_pic": 5200, "turnover_rate": 0.15},

                "fleet_condition": {"score": 65, "avg_age": 14.5, "maintenance_ratio": 0.92},
                "fleet_modernization": {"score": 55, "new_gen_pct": 0.30},

                "financial_strength": {"score": 68, "rating": "BBB", "debt_ratio": 0.62},
                "liquidity": {"score": 60, "cash_months": 4},

                "route_risk": {"score": 72, "conflict_exposure": 0.08, "terrain_challenging": 0.25},
                "weather_exposure": {"score": 68, "severe_weather_pct": 0.15},

                "safety_culture": {"score": 65, "sms_maturity": 3, "reporting_rate": 6.2},
                "management_stability": {"score": 62, "ceo_tenure": 2, "safety_director_tenure": 1.5},

                "industry_standing": {"score": 55, "alliance_member": False, "awards": 0},
                "market_position": {"score": 48, "market_share": 0.03},
            }

        elif profile == TestEntityProfile.POOR_SAFETY:
            return {
                "safety_record": {"score": 35, "accidents_5yr": 3, "hull_losses": 1},
                "incident_record": {"score": 32, "incidents_5yr": 18, "severity": "serious"},
                "fatality_record": {"score": 45, "fatalities_10yr": 12},

                "regulatory_compliance": {"score": 38, "status": "deficient"},
                "enforcement_history": {"score": 30, "actions_5yr": 8},
                "iosa_status": {"score": 25, "status": "removed", "audit_date": None},

                "operational_performance": {"score": 42, "otp_rate": 0.58, "completion_rate": 0.92},
                "training_quality": {"score": 35, "program_rating": "D", "sim_hours": 40},
                "crew_experience": {"score": 38, "avg_hours_pic": 2800, "turnover_rate": 0.35},

                "fleet_condition": {"score": 32, "avg_age": 24.5, "maintenance_ratio": 0.78},
                "fleet_modernization": {"score": 20, "new_gen_pct": 0.05},

                "financial_strength": {"score": 35, "rating": "B-", "debt_ratio": 0.85},
                "liquidity": {"score": 28, "cash_months": 1.5},

                "route_risk": {"score": 42, "conflict_exposure": 0.22, "terrain_challenging": 0.45},
                "weather_exposure": {"score": 45, "severe_weather_pct": 0.28},

                "safety_culture": {"score": 32, "sms_maturity": 1, "reporting_rate": 1.8},
                "management_stability": {"score": 28, "ceo_tenure": 0.5, "safety_director_tenure": 0.3},

                "industry_standing": {"score": 25, "alliance_member": False, "awards": 0},
                "market_position": {"score": 22, "market_share": 0.005},
            }
        elif profile == TestEntityProfile.MINIMAL_SIGNALS:
            return {
                "safety_record": {"score": 70},
                "regulatory_compliance": {"score": 70},
            }

        elif profile == TestEntityProfile.NO_HISTORY:
            return {
                "safety_record": {"score": 60, "accidents_5yr": 0, "hull_losses": 0},
                "incident_record": {"score": 60, "incidents_5yr": 0},
                "fatality_record": {"score": 100, "fatalities_10yr": 0},
                "regulatory_compliance": {"score": 65, "status": "new_entrant"},
                "enforcement_history": {"score": 70, "actions_5yr": 0},
                "fleet_condition": {"score": 80, "avg_age": 2.0},
                "financial_strength": {"score": 55, "rating": "NR"},
                "industry_standing": {"score": 40, "alliance_member": False},
            }
            
        else:
            return TestDataGenerator.generate_aerospace_signals(TestEntityProfile.AVERAGE_SAFETY)
    
    # =======================================================================
    # CYBER SIGNALS
    # =======================================================================
    
    @staticmethod
    def generate_cyber_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate cyber-specific test signals."""

        if profile == TestEntityProfile.EXCELLENT_SECURITY:
            return {
                "security_rating": {"score": 95, "grade": "A+"},
                "vulnerability_count": 2,
                "breach_history": {"incidents": 0, "last_incident": None},
                "compliance_status": "fully_compliant",
                "technology_stack": {"modern": True, "score": 90},
                "phishing_susceptibility": {"score": 92, "click_rate": 0.02},
                "patch_cadence": {"avg_days": 7, "score": 95},
                "endpoint_protection": {"coverage": 100, "score": 95},
            }

        elif profile == TestEntityProfile.AVERAGE_SECURITY:
            return {
                "security_rating": {"score": 70, "grade": "B"},
                "vulnerability_count": 15,
                "breach_history": {"incidents": 1, "last_incident": "2023-06-15"},
                "compliance_status": "partial",
                "technology_stack": {"modern": True, "score": 68},
                "phishing_susceptibility": {"score": 65, "click_rate": 0.08},
                "patch_cadence": {"avg_days": 21, "score": 70},
                "endpoint_protection": {"coverage": 85, "score": 72},
            }

        elif profile == TestEntityProfile.POOR_SECURITY:
            return {
                "security_rating": {"score": 42, "grade": "D"},
                "vulnerability_count": 45,
                "breach_history": {"incidents": 3, "last_incident": "2024-08-22"},
                "compliance_status": "non_compliant",
                "technology_stack": {"modern": False, "score": 35},
                "phishing_susceptibility": {"score": 38, "click_rate": 0.22},
                "patch_cadence": {"avg_days": 90, "score": 40},
                "endpoint_protection": {"coverage": 45, "score": 42},
            }

        else:
            # Default to average
            return TestDataGenerator.generate_cyber_signals(TestEntityProfile.AVERAGE_SECURITY)

    
    # =======================================================================
    # D&O INSTITUTIONS SIGNALS
    # =======================================================================
    
    @staticmethod
    def generate_do_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate D&O test signals."""

        if profile == TestEntityProfile.STRONG_GOVERNANCE:
            return {
                "financial_strength": {"rating": "A", "score": 90},
                "executive_turnover": {"rate": 0.05, "score": 92},
                "stock_volatility": {"beta": 0.8, "score": 88},
                "shareholder_activism": {"incidents": 0, "score": 95},
                "board_composition": {"independence": 0.85, "score": 90},
                "litigation_history": {"securities_cases": 0, "score": 95},
            }

        elif profile == TestEntityProfile.STANDARD_GOVERNANCE:
            return {
                "financial_strength": {"rating": "B", "score": 70},
                "executive_turnover": {"rate": 0.15, "score": 68},
                "stock_volatility": {"beta": 1.2, "score": 65},
                "shareholder_activism": {"incidents": 1, "score": 70},
                "board_composition": {"independence": 0.65, "score": 68},
                "litigation_history": {"securities_cases": 1, "score": 65},
            }

        elif profile == TestEntityProfile.WEAK_GOVERNANCE:
            return {
                "financial_strength": {"rating": "C", "score": 45},
                "executive_turnover": {"rate": 0.40, "score": 35},
                "stock_volatility": {"beta": 2.5, "score": 30},
                "shareholder_activism": {"incidents": 5, "score": 25},
                "board_composition": {"independence": 0.35, "score": 40},
                "litigation_history": {"securities_cases": 6, "score": 28},
            }

        else:
            return TestDataGenerator.generate_do_signals(TestEntityProfile.STANDARD_GOVERNANCE)

    # =======================================================================
    # ENERGY SIGNALS
    # =======================================================================
    
    @staticmethod
    def generate_energy_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate energy sector test signals."""

        if profile == TestEntityProfile.EXCELLENT_SECURITY:
            return {
                "safety_record": {"incidents": 0, "trir": 0.5, "score": 95},
                "environmental_violations": {"count": 0, "score": 95},
                "equipment_age": {"avg_years": 3, "score": 92},
                "maintenance_record": {"compliance": 0.98, "score": 94},
                "compliance_status": "excellent",
                "financial_strength": {"rating": "A", "score": 90},
            }

        elif profile == TestEntityProfile.AVERAGE_SECURITY:
            return {
                "safety_record": {"incidents": 2, "trir": 2.5, "score": 68},
                "environmental_violations": {"count": 1, "score": 70},
                "equipment_age": {"avg_years": 12, "score": 65},
                "maintenance_record": {"compliance": 0.85, "score": 70},
                "compliance_status": "adequate",
                "financial_strength": {"rating": "B", "score": 68},
            }

        elif profile == TestEntityProfile.POOR_SECURITY:
            return {
                "safety_record": {"incidents": 8, "trir": 6.2, "score": 35},
                "environmental_violations": {"count": 6, "score": 30},
                "equipment_age": {"avg_years": 25, "score": 32},
                "maintenance_record": {"compliance": 0.62, "score": 40},
                "compliance_status": "deficient",
                "financial_strength": {"rating": "C", "score": 42},
            }

        else:
            return TestDataGenerator.generate_energy_signals(TestEntityProfile.AVERAGE_SECURITY)
    
    
    # =======================================================================
    # FINANCIAL INSTITUTIONS SIGNALS
    # =======================================================================
    
    @staticmethod
    def generate_fi_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate financial institutions test signals."""

        if profile == TestEntityProfile.WELL_CAPITALIZED:
            return {
                "financial_strength": {"rating": "A+", "score": 95},
                "credit_rating": {"rating": "AA", "score": 90},
                "regulatory_actions": {"count": 0, "severity": "none"},
                "litigation_history": {"active_cases": 0, "score": 95},
                "compliance_status": "excellent",
                "security_rating": {"score": 88, "grade": "A"},
            }

        elif profile == TestEntityProfile.ADEQUATE_CAPITAL:
            return {
                "financial_strength": {"rating": "B+", "score": 70},
                "credit_rating": {"rating": "BBB", "score": 68},
                "regulatory_actions": {"count": 1, "severity": "minor"},
                "litigation_history": {"active_cases": 2, "score": 65},
                "compliance_status": "adequate",
                "security_rating": {"score": 70, "grade": "B"},
            }

        elif profile == TestEntityProfile.UNDERCAPITALIZED:
            return {
                "financial_strength": {"rating": "C", "score": 42},
                "credit_rating": {"rating": "BB-", "score": 45},
                "regulatory_actions": {"count": 4, "severity": "major"},
                "litigation_history": {"active_cases": 8, "score": 38},
                "compliance_status": "deficient",
                "security_rating": {"score": 50, "grade": "C"},
            }

        else:
            return TestDataGenerator.generate_fi_signals(TestEntityProfile.ADEQUATE_CAPITAL)

    # ==========================================================================
    # MARINE SIGNALS
    # ==========================================================================

    @staticmethod
    def generate_marine_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate marine/cargo test signals."""

        if profile == TestEntityProfile.EXCELLENT_SAFETY:
            return {
                "vessel_condition": {"score": 92, "avg_age": 5, "class_status": "current"},
                "safety_record": {"score": 95, "incidents_5yr": 0, "detentions": 0},
                "flag_state": {"score": 90, "state": "marshall_islands", "whitelist": True},
                "crew_quality": {"score": 88, "certification": "full", "experience_avg": 12},
                "financial_strength": {"score": 85, "rating": "A"},
                "route_risk": {"score": 90, "piracy_exposure": 0.02, "weather_risk": "low"},
            }

        elif profile == TestEntityProfile.AVERAGE_SAFETY:
            return {
                "vessel_condition": {"score": 68, "avg_age": 15, "class_status": "current"},
                "safety_record": {"score": 65, "incidents_5yr": 2, "detentions": 1},
                "flag_state": {"score": 65, "state": "liberia", "whitelist": True},
                "crew_quality": {"score": 62, "certification": "partial", "experience_avg": 6},
                "financial_strength": {"score": 60, "rating": "BBB"},
                "route_risk": {"score": 65, "piracy_exposure": 0.10, "weather_risk": "moderate"},
            }

        elif profile == TestEntityProfile.POOR_SAFETY:
            return {
                "vessel_condition": {"score": 35, "avg_age": 28, "class_status": "expired"},
                "safety_record": {"score": 30, "incidents_5yr": 8, "detentions": 5},
                "flag_state": {"score": 25, "state": "unknown", "whitelist": False},
                "crew_quality": {"score": 32, "certification": "minimal", "experience_avg": 2},
                "financial_strength": {"score": 30, "rating": "CCC"},
                "route_risk": {"score": 35, "piracy_exposure": 0.35, "weather_risk": "high"},
            }

        else:
            return TestDataGenerator.generate_marine_signals(TestEntityProfile.AVERAGE_SAFETY)

    # ==========================================================================
    # PI (PROFESSIONAL INDEMNITY) SIGNALS
    # ==========================================================================

    @staticmethod
    def generate_pi_signals(profile: TestEntityProfile) -> Dict[str, Any]:
        """Generate professional indemnity test signals."""

        if profile == TestEntityProfile.STRONG_GOVERNANCE:
            return {
                "claims_history": {"score": 95, "claims_5yr": 0, "severity": "none"},
                "professional_standing": {"score": 92, "disciplinary": 0, "complaints": 0},
                "qualification_level": {"score": 90, "certifications": ["CPA", "CFA"]},
                "experience": {"score": 88, "years": 18, "specialization": "high"},
                "client_concentration": {"score": 85, "top_client_pct": 0.08},
                "revenue_stability": {"score": 88, "growth_rate": 0.12, "volatility": "low"},
            }

        elif profile == TestEntityProfile.STANDARD_GOVERNANCE:
            return {
                "claims_history": {"score": 68, "claims_5yr": 2, "severity": "minor"},
                "professional_standing": {"score": 65, "disciplinary": 0, "complaints": 2},
                "qualification_level": {"score": 70, "certifications": ["CPA"]},
                "experience": {"score": 62, "years": 8, "specialization": "moderate"},
                "client_concentration": {"score": 58, "top_client_pct": 0.25},
                "revenue_stability": {"score": 62, "growth_rate": 0.05, "volatility": "moderate"},
            }

        elif profile == TestEntityProfile.WEAK_GOVERNANCE:
            return {
                "claims_history": {"score": 32, "claims_5yr": 6, "severity": "major"},
                "professional_standing": {"score": 28, "disciplinary": 2, "complaints": 12},
                "qualification_level": {"score": 45, "certifications": []},
                "experience": {"score": 38, "years": 3, "specialization": "low"},
                "client_concentration": {"score": 30, "top_client_pct": 0.55},
                "revenue_stability": {"score": 35, "growth_rate": -0.15, "volatility": "high"},
            }

        else:
            return TestDataGenerator.generate_pi_signals(TestEntityProfile.AVERAGE_GOVERNANCE)


    @staticmethod
    def create_test_signal_set(
        entity_name: str,
        coverage_type: str,
        profile: TestEntityProfile
    ) -> TestSignalSet:
        """Create a complete test signal set."""

        # Generate signals based on coverage type
        if coverage_type == "cyber":
            signals = TestDataGenerator.generate_cyber_signals(profile)
        elif coverage_type == "fi":
            signals = TestDataGenerator.generate_fi_signals(profile)
        elif coverage_type == "do":
            signals = TestDataGenerator.generate_do_signals(profile)
        elif coverage_type == "energy":
            signals = TestDataGenerator.generate_energy_signals(profile)
        else:
            signals = {}

        # Define expected outcomes based on profile
        if "excellent" in profile.value or "strong" in profile.value or "well" in profile.value:
            expected_tier = (1, 2)
            expected_score = (750, 1000)
        elif "average" in profile.value or "standard" in profile.value or "adequate" in profile.value:
            expected_tier = (2, 3)
            expected_score = (600, 799)
        elif "poor" in profile.value or "weak" in profile.value or "under" in profile.value:
            expected_tier = (4, 5)
            expected_score = (0, 499)
        else:
            expected_tier = (2, 4)
            expected_score = (400, 799)

        return TestSignalSet(
            entity_id=f"test-{entity_name.lower().replace(' ', '-')}",
            entity_name=entity_name,
            profile=profile,
            signals=signals,
            expected_tier_range=expected_tier,
            expected_score_range=expected_score,
            description=f"{entity_name} with {profile.value} profile"
        )


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture
def excellent_cyber_entity():
    """Entity with excellent cyber security profile."""
    return TestDataGenerator.create_test_signal_set(
        "SecureTech Corp",
        "cyber",
        TestEntityProfile.EXCELLENT_SECURITY
    )


@pytest.fixture
def poor_cyber_entity():
    """Entity with poor cyber security profile."""
    return TestDataGenerator.create_test_signal_set(
        "InsecureTech Inc",
        "cyber",
        TestEntityProfile.POOR_SECURITY
    )


@pytest.fixture
def average_cyber_entity():
    """Entity with average cyber security profile."""
    return TestDataGenerator.create_test_signal_set(
        "MidTech Solutions",
        "cyber",
        TestEntityProfile.AVERAGE_SECURITY
    )


@pytest.fixture
def strong_fi_entity():
    """Financial institution with strong profile."""
    return TestDataGenerator.create_test_signal_set(
        "Premier Bank",
        "fi",
        TestEntityProfile.WELL_CAPITALIZED
    )


@pytest.fixture
def weak_fi_entity():
    """Financial institution with weak profile."""
    return TestDataGenerator.create_test_signal_set(
        "Risky Bank",
        "fi",
        TestEntityProfile.UNDERCAPITALIZED
    )


@pytest.fixture
def strong_governance_entity():
    """Entity with strong governance (D&O)."""
    return TestDataGenerator.create_test_signal_set(
        "GoodGov Corp",
        "do",
        TestEntityProfile.STRONG_GOVERNANCE
    )


@pytest.fixture
def weak_governance_entity():
    """Entity with weak governance (D&O)."""
    return TestDataGenerator.create_test_signal_set(
        "BadGov Inc",
        "do",
        TestEntityProfile.WEAK_GOVERNANCE
    )


@pytest.fixture
def excellent_energy_entity():
    """Energy company with excellent safety profile."""
    return TestDataGenerator.create_test_signal_set(
        "SafeEnergy Co",
        "energy",
        TestEntityProfile.EXCELLENT_SECURITY
    )


@pytest.fixture
def poor_energy_entity():
    """Energy company with poor safety profile."""
    return TestDataGenerator.create_test_signal_set(
        "RiskyEnergy Inc",
        "energy",
        TestEntityProfile.POOR_SECURITY
    )


@pytest.fixture
def test_limits():
    """Standard test limits for pricing tests."""
    return {
        "small": 1_000_000,
        "medium": 5_000_000,
        "large": 10_000_000,
        "xlarge": 25_000_000,
    }


@pytest.fixture
def test_deductibles():
    """Standard test deductibles."""
    return {
        "small": 10_000,
        "medium": 50_000,
        "large": 100_000,
        "xlarge": 250_000,
    }


# =============================================================================
# BASE TEST CLASSES
# =============================================================================

class BaseStructuralTest:
    """Base class for structural tests."""

    def verify_dataclass_structure(self, instance, expected_fields: List[str]):
        """Verify a dataclass has expected fields."""
        for field in expected_fields:
            assert hasattr(instance, field), f"Missing field: {field}"

    def verify_enum_values(self, enum_class, expected_values: List[str]):
        """Verify an enum has expected values."""
        actual_values = [e.value for e in enum_class]
        for expected in expected_values:
            assert expected in actual_values, f"Missing enum value: {expected}"

    def verify_return_type(self, value, expected_type):
        """Verify return type matches expected."""
        assert isinstance(value, expected_type), \
            f"Expected {expected_type}, got {type(value)}"


class BaseFunctionalTest:
    """Base class for functional tests."""

    def assert_tier_in_range(self, tier: int, min_tier: int, max_tier: int):
        """Assert tier is within expected range."""
        assert min_tier <= tier <= max_tier, \
            f"Tier {tier} not in expected range [{min_tier}, {max_tier}]"

    def assert_score_in_range(self, score: float, min_score: float, max_score: float):
        """Assert score is within expected range."""
        assert min_score <= score <= max_score, \
            f"Score {score} not in expected range [{min_score}, {max_score}]"

    def assert_premium_positive(self, premium: float):
        """Assert premium is positive."""
        assert premium > 0, f"Premium must be positive, got {premium}"

    def assert_premium_reasonable(self, premium: float, limit: float, max_rate: float = 0.10):
        """Assert premium is reasonable relative to limit."""
        rate = premium / limit
        assert rate <= max_rate, \
            f"Premium rate {rate:.2%} exceeds maximum {max_rate:.2%}"


class BaseActuarialTest:
    """Base class for actuarial validity tests."""

    def assert_better_profile_cheaper(self,
                                       premium_good: float,
                                       premium_poor: float,
                                       min_ratio: float = 1.3):
        """Assert better risk profile results in lower premium."""
        ratio = premium_poor / premium_good
        assert ratio >= min_ratio, \
            f"Poor risk premium should be at least {min_ratio}x higher than good risk. " \
            f"Got ratio: {ratio:.2f} (Poor: ${premium_poor:,.2f}, Good: ${premium_good:,.2f})"

    def assert_tier_progression(self, tiers: List[int]):
        """Assert tiers progress logically (higher risk = higher tier)."""
        for i in range(len(tiers) - 1):
            assert tiers[i] <= tiers[i+1], \
                f"Tier progression violated: {tiers[i]} should be <= {tiers[i+1]}"

    def assert_score_progression(self, scores: List[float]):
        """Assert scores progress logically (better risk = higher score)."""
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1], \
                f"Score progression violated: {scores[i]} should be >= {scores[i+1]}"

    def assert_limit_scaling(self,
                            premium_low: float,
                            premium_high: float,
                            limit_low: float,
                            limit_high: float):
        """Assert premium scales appropriately with limit."""
        expected_ratio = limit_high / limit_low
        actual_ratio = premium_high / premium_low

        # Premium should scale roughly linearly with limit (within 20%)
        assert 0.8 * expected_ratio <= actual_ratio <= 1.2 * expected_ratio, \
            f"Premium scaling incorrect. Expected ~{expected_ratio:.2f}x, got {actual_ratio:.2f}x"


# =============================================================================
# TEST UTILITIES
# =============================================================================

class TestAssertions:
    """Collection of common test assertions."""

    @staticmethod
    def assert_valid_tier(tier: int):
        """Assert tier is valid (1-5)."""
        assert 1 <= tier <= 5, f"Tier must be 1-5, got {tier}"

    @staticmethod
    def assert_valid_score(score: float):
        """Assert score is valid (0-1000)."""
        assert 0 <= score <= 1000, f"Score must be 0-1000, got {score}"

    @staticmethod
    def assert_valid_confidence(confidence: float):
        """Assert confidence is valid (0.0-1.0)."""
        assert 0.0 <= confidence <= 1.0, f"Confidence must be 0.0-1.0, got {confidence}"

    @staticmethod
    def assert_valid_tier_label(tier: int, tier_label: str):
        """Assert tier label matches tier."""
        expected_labels = {
            1: ["PREFERRED", "TIER_1"],
            2: ["STANDARD_PLUS", "STANDARD", "TIER_2"],
            3: ["STANDARD", "ELEVATED", "TIER_3"],
            4: ["SUBSTANDARD", "HIGH_RISK", "TIER_4"],
            5: ["DECLINE", "CRITICAL", "TIER_5"],
        }

        label_upper = tier_label.upper()
        assert any(exp in label_upper for exp in expected_labels.get(tier, [])), \
            f"Tier label '{tier_label}' doesn't match tier {tier}"

    @staticmethod
    def assert_flags_consistent(score: float, green_flags: int, red_flags: int):
        """Assert flags are consistent with score."""
        if score >= 800:
            assert green_flags > red_flags, \
                f"High score ({score}) should have more green flags than red"
        elif score <= 400:
            assert red_flags > green_flags, \
                f"Low score ({score}) should have more red flags than green"


class TestComparisons:
    """Utilities for comparing test results."""

    @staticmethod
    def compare_pricing_results(result1: Dict, result2: Dict) -> Dict[str, float]:
        """Compare two pricing results."""
        return {
            "score_diff": result1["composite_score"] - result2["composite_score"],
            "tier_diff": result1["tier"] - result2["tier"],
            "premium_ratio": result1["gross_premium"] / result2["gross_premium"],
            "rate_diff": result1["rate_per_million"] - result2["rate_per_million"],
        }

    @staticmethod
    def assert_better_than(result_good: Dict, result_poor: Dict):
        """Assert good result is better than poor result."""
        assert result_good["composite_score"] > result_poor["composite_score"], \
            "Good profile should have higher score"
        assert result_good["tier"] <= result_poor["tier"], \
            "Good profile should have lower tier"
        assert result_good["gross_premium"] < result_poor["gross_premium"], \
            "Good profile should have lower premium"


# =============================================================================
# PARAMETRISED TEST DATA
# =============================================================================

# Coverage types for parametrised tests
COVERAGE_TYPES = ["cyber", "fi", "do", "energy", "marine", "pi", "aerospace"]

# Test limits by coverage type
TEST_LIMITS_BY_COVERAGE = {
    "cyber": [1_000_000, 5_000_000, 10_000_000],
    "fi": [5_000_000, 10_000_000, 25_000_000],
    "do": [5_000_000, 10_000_000, 25_000_000],
    "energy": [10_000_000, 25_000_000, 50_000_000],
    "marine": [5_000_000, 10_000_000, 25_000_000],
    "pi": [1_000_000, 5_000_000, 10_000_000],
    "aerospace": [10_000_000, 25_000_000, 50_000_000],
}

# Profile combinations for actuarial tests
ACTUARIAL_TEST_PROFILES = [
    (TestEntityProfile.EXCELLENT_SECURITY, TestEntityProfile.POOR_SECURITY),
    (TestEntityProfile.STRONG_GOVERNANCE, TestEntityProfile.WEAK_GOVERNANCE),
    (TestEntityProfile.WELL_CAPITALIZED, TestEntityProfile.UNDERCAPITALIZED),
]
