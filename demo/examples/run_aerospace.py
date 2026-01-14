"""
Complete Aerospace Coverage Example (Phase 14)

Demonstrates:
- Website discovery workflow
- Signal extraction (stub mode)
- Composite scoring
- Tier assignment
- Premium calculation
- Full audit trail
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from layers.risk.workflow import run_assessment
from examples.utils import print_full_report


def run_example():
    """Run aerospace coverage example."""
    print("\n" + "=" * 60)
    print("AEROSPACE COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example aerospace entity - large commercial airline
    result = run_assessment(
        entity_id="boeing-example",
        coverage="aerospace",
        entity_name="Boeing Company",
        domain_hint="boeing.com",
        country_hint="US",
        submission_data={
            "tiv": 500_000_000,
            "fleet_size": 450,
            "annual_departures": 125_000,
            "limit_requested": 100_000_000,
            "hull_value": 200_000_000,
            "passenger_liability_limit": 300_000_000,
            "years_operating": 107,
            "maintenance_budget": 50_000_000,
        },
        direct_query_responses={
            "grounding_events": False,
            "regulatory_actions": False,
            "accident_history_3yr": False,
            "major_claims_5yr": False,
        },
        skip_discovery=True,  # Use domain hint directly
    )

    print_full_report(result)

    print("\n" + "=" * 60)
    print("EXAMPLE COMPLETE")
    print("=" * 60)

    return result


def run_high_risk_example():
    """Run high-risk aerospace example."""
    print("\n" + "=" * 60)
    print("HIGH-RISK AEROSPACE EXAMPLE")
    print("=" * 60 + "\n")

    # Example high-risk entity - startup with incidents
    result = run_assessment(
        entity_id="startup-airline",
        coverage="aerospace",
        entity_name="New Horizon Airlines",
        domain_hint="newhorizonair.com",
        country_hint="US",
        submission_data={
            "tiv": 50_000_000,
            "fleet_size": 12,
            "annual_departures": 8_000,
            "limit_requested": 25_000_000,
            "hull_value": 40_000_000,
            "passenger_liability_limit": 50_000_000,
            "years_operating": 3,
            "maintenance_budget": 2_000_000,
        },
        direct_query_responses={
            "grounding_events": True,  # Has had grounding
            "regulatory_actions": True,  # FAA action
            "accident_history_3yr": True,  # Recent incident
            "major_claims_5yr": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Aerospace Coverage Examples...")
    print()

    # Run standard example
    result1 = run_example()

    print("\n\n")

    # Run high-risk example
    result2 = run_high_risk_example()

    # Summary comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nBoeing (established):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nNew Horizon (high-risk startup):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
