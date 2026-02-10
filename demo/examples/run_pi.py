"""
Complete Professional Indemnity Coverage Example (Phase 14)

Demonstrates:
- Professional liability risk assessment
- Practice area evaluation
- Claims history analysis
- Professional credentials verification
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from layers.risk.workflow import run_assessment
from demo.examples.utils import print_full_report


def run_example():
    """Run PI coverage example."""
    print("\n" + "=" * 60)
    print("PROFESSIONAL INDEMNITY COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example large law firm
    result = run_assessment(
        entity_id="biglaw-firm",
        coverage="pi",
        entity_name="Sullivan & Cromwell LLP",
        domain_hint="sullcrom.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 1_800_000_000,
            "partner_count": 180,
            "employee_count": 900,
            "limit_requested": 50_000_000,
            "practice_areas": ["m&a", "securities", "litigation", "tax"],
            "years_operating": 140,
            "am_law_ranking": 15,
            "bar_complaints_3yr": 0,
            "malpractice_claims_5yr": 2,
        },
        direct_query_responses={
            "disciplinary_action": False,
            "partner_departure_major": False,
            "client_lawsuit": False,
            "regulatory_investigation": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_consulting_example():
    """Run consulting firm example."""
    print("\n" + "=" * 60)
    print("CONSULTING FIRM EXAMPLE")
    print("=" * 60 + "\n")

    # Management consulting firm
    result = run_assessment(
        entity_id="consulting-firm",
        coverage="pi",
        entity_name="Boutique Consulting Group",
        domain_hint="boutiqueconsulting.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 50_000_000,
            "partner_count": 10,
            "employee_count": 75,
            "limit_requested": 10_000_000,
            "practice_areas": ["strategy", "operations", "digital"],
            "years_operating": 12,
            "client_concentration_top3": 0.40,
            "professional_certifications": ["CPA", "CFA", "PMP"],
        },
        direct_query_responses={
            "disciplinary_action": False,
            "partner_departure_major": True,
            "client_lawsuit": False,
            "regulatory_investigation": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Professional Indemnity Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_consulting_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nSullivan & Cromwell (BigLaw):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nBoutique Consulting:")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
