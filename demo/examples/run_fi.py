"""
Complete Financial Institutions Coverage Example (Phase 14)

Demonstrates:
- Financial institution risk assessment
- Regulatory compliance signals
- Capital adequacy evaluation
- Fraud prevention measures
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from layers.risk.workflow import run_assessment
from demo.examples.utils import print_full_report


def run_example():
    """Run FI coverage example."""
    print("\n" + "=" * 60)
    print("FINANCIAL INSTITUTIONS COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example large bank
    result = run_assessment(
        entity_id="jpmorgan-example",
        coverage="fi",
        entity_name="JPMorgan Chase",
        domain_hint="jpmorganchase.com",
        country_hint="US",
        submission_data={
            "total_assets": 3_700_000_000_000,
            "deposits": 2_400_000_000_000,
            "annual_revenue": 128_000_000_000,
            "employee_count": 293_000,
            "limit_requested": 250_000_000,
            "tier1_capital_ratio": 0.15,
            "branches": 4_700,
            "years_operating": 225,
            "fdic_insured": True,
            "systemically_important": True,
        },
        direct_query_responses={
            "regulatory_enforcement": False,
            "fraud_incident_3yr": False,
            "aml_violation": False,
            "data_breach": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_fintech_example():
    """Run fintech example."""
    print("\n" + "=" * 60)
    print("FINTECH COMPANY EXAMPLE")
    print("=" * 60 + "\n")

    # Fintech startup
    result = run_assessment(
        entity_id="fintech-startup",
        coverage="fi",
        entity_name="PayTech Solutions",
        domain_hint="paytech.io",
        country_hint="US",
        submission_data={
            "total_assets": 500_000_000,
            "transaction_volume": 50_000_000_000,
            "annual_revenue": 200_000_000,
            "employee_count": 500,
            "limit_requested": 25_000_000,
            "money_transmitter_license": True,
            "pci_compliant": True,
            "years_operating": 5,
            "fdic_insured": False,
            "venture_backed": True,
        },
        direct_query_responses={
            "regulatory_enforcement": False,
            "fraud_incident_3yr": True,  # Common for payment processors
            "aml_violation": False,
            "data_breach": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Financial Institutions Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_fintech_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nJPMorgan (major bank):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nPayTech (fintech):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
