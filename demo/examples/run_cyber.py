"""
Complete Cyber Coverage Example (Phase 14)

Demonstrates:
- Website discovery workflow
- Technical security signal extraction
- Composite scoring for cyber risk
- Tier assignment
- Premium calculation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technical_pricing.model.workflow import run_assessment
from examples.utils import print_full_report


def run_example():
    """Run cyber coverage example."""
    print("\n" + "=" * 60)
    print("CYBER COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example tech company with good security posture
    result = run_assessment(
        entity_id="stripe-example",
        coverage="cyber",
        entity_name="Stripe Inc",
        domain_hint="stripe.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 14_000_000_000,
            "employee_count": 8000,
            "records_stored": 500_000_000,
            "limit_requested": 50_000_000,
            "industry": "financial_technology",
            "pci_certified": True,
            "soc2_certified": True,
            "iso27001_certified": True,
            "security_budget_pct": 0.12,
        },
        direct_query_responses={
            "previous_breach": False,
            "ransomware_attack": False,
            "regulatory_fines": False,
            "security_audit_passed": True,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_vulnerable_example():
    """Run vulnerable company example."""
    print("\n" + "=" * 60)
    print("VULNERABLE COMPANY EXAMPLE")
    print("=" * 60 + "\n")

    # Company with poor security posture
    result = run_assessment(
        entity_id="legacy-retailer",
        coverage="cyber",
        entity_name="Legacy Retail Corp",
        domain_hint="legacyretail.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 500_000_000,
            "employee_count": 5000,
            "records_stored": 10_000_000,
            "limit_requested": 10_000_000,
            "industry": "retail",
            "pci_certified": False,
            "soc2_certified": False,
            "iso27001_certified": False,
            "security_budget_pct": 0.02,
        },
        direct_query_responses={
            "previous_breach": True,
            "ransomware_attack": True,
            "regulatory_fines": True,
            "security_audit_passed": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Cyber Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_vulnerable_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nStripe (excellent security):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nLegacy Retail (poor security):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
