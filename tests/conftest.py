"""
DSI Test Framework - Base Classes and Fixtures
==============================================

Provides foundational test infrastructure for structural, functional,
and actuarial validity testing.

Author: John Walker
Version: 1.0.0
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# TEST DATA GENERATORS
# =============================================================================

class TestEntityProfile(Enum):
    """Predefined entity profiles for actuarial validity testing."""

    # Excellent profiles (should get Tier 1-2)
    EXCELLENT_SECURITY = "excellent_security"
    STRONG_GOVERNANCE = "strong_governance"
    WELL_CAPITALIZED = "well_capitalized"

    # Average profiles (should get Tier 2-3)
    AVERAGE_SECURITY = "average_security"
    STANDARD_GOVERNANCE = "standard_governance"
    ADEQUATE_CAPITAL = "adequate_capital"

    # Poor profiles (should get Tier 4-5)
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
    expected_tier_range: tuple  # (min_tier, max_tier)
    expected_score_range: tuple  # (min_score, max_score)
    description: str


class TestDataGenerator:
    """Generates consistent test data for all coverage types."""

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
