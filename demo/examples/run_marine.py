"""
Complete Marine Coverage Example (Phase 14)

Demonstrates:
- Marine cargo/hull risk assessment
- Fleet safety evaluation
- Route risk analysis
- Vessel condition assessment
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from layers.risk.workflow import run_assessment
from demo.examples.utils import print_full_report


def run_example():
    """Run marine coverage example."""
    print("\n" + "=" * 60)
    print("MARINE COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example major shipping company
    result = run_assessment(
        entity_id="maersk-example",
        coverage="marine",
        entity_name="Maersk Line",
        domain_hint="maersk.com",
        country_hint="DK",
        submission_data={
            "fleet_size": 700,
            "total_capacity_teu": 4_300_000,
            "annual_revenue": 81_000_000_000,
            "employee_count": 110_000,
            "limit_requested": 100_000_000,
            "average_vessel_age": 8,
            "class_society": "DNV",
            "ism_certified": True,
            "years_operating": 120,
            "high_risk_routes_pct": 0.05,
        },
        direct_query_responses={
            "total_loss_5yr": False,
            "piracy_incident": False,
            "port_detention": False,
            "cargo_claims_major": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_coastal_example():
    """Run coastal shipping example."""
    print("\n" + "=" * 60)
    print("COASTAL SHIPPING EXAMPLE")
    print("=" * 60 + "\n")

    # Smaller coastal operator
    result = run_assessment(
        entity_id="coastal-shipping",
        coverage="marine",
        entity_name="Pacific Coast Shipping",
        domain_hint="pacificcoast-shipping.com",
        country_hint="US",
        submission_data={
            "fleet_size": 25,
            "total_capacity_teu": 50_000,
            "annual_revenue": 150_000_000,
            "employee_count": 500,
            "limit_requested": 25_000_000,
            "average_vessel_age": 15,
            "class_society": "ABS",
            "ism_certified": True,
            "years_operating": 30,
            "high_risk_routes_pct": 0.0,
        },
        direct_query_responses={
            "total_loss_5yr": False,
            "piracy_incident": False,
            "port_detention": True,  # Minor detention
            "cargo_claims_major": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Marine Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_coastal_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nMaersk (global shipping):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nPacific Coast (coastal):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
