"""
Complete D&O Coverage Example (Phase 14)

Demonstrates:
- Directors & Officers liability assessment
- Governance signal extraction
- Corporate structure analysis
- Litigation risk evaluation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layers.risk.workflow import run_assessment
from examples.utils import print_full_report


def run_example():
    """Run D&O coverage example."""
    print("\n" + "=" * 60)
    print("D&O COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example public company with strong governance
    result = run_assessment(
        entity_id="microsoft-example",
        coverage="do",
        entity_name="Microsoft Corporation",
        domain_hint="microsoft.com",
        country_hint="US",
        submission_data={
            "market_cap": 2_800_000_000_000,
            "annual_revenue": 211_000_000_000,
            "employee_count": 221_000,
            "limit_requested": 100_000_000,
            "public_company": True,
            "years_public": 38,
            "board_size": 12,
            "independent_directors": 11,
            "audit_committee": True,
            "compensation_committee": True,
        },
        direct_query_responses={
            "sec_investigation": False,
            "shareholder_litigation": False,
            "bankruptcy_filed": False,
            "restatement_3yr": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_ipo_example():
    """Run pre-IPO company example."""
    print("\n" + "=" * 60)
    print("PRE-IPO COMPANY EXAMPLE")
    print("=" * 60 + "\n")

    # Pre-IPO tech company with higher risk
    result = run_assessment(
        entity_id="tech-ipo-corp",
        coverage="do",
        entity_name="TechIPO Corp",
        domain_hint="techipo.com",
        country_hint="US",
        submission_data={
            "market_cap": 5_000_000_000,  # Estimated
            "annual_revenue": 500_000_000,
            "employee_count": 2000,
            "limit_requested": 50_000_000,
            "public_company": False,
            "years_public": 0,
            "board_size": 7,
            "independent_directors": 2,
            "audit_committee": True,
            "compensation_committee": False,
            "ipo_planned": True,
        },
        direct_query_responses={
            "sec_investigation": False,
            "shareholder_litigation": False,
            "bankruptcy_filed": False,
            "restatement_3yr": False,
            "venture_backed": True,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running D&O Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_ipo_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nMicrosoft (established public):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nTechIPO (pre-IPO):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
