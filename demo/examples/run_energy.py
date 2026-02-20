"""
Complete Energy Coverage Example (Phase 14)

Demonstrates:
- Energy sector risk assessment
- Environmental compliance signals
- Operational safety evaluation
- Asset value assessment
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from layers.risk.workflow import run_assessment
from demo.examples.utils import print_full_report


def run_example():
    """Run energy coverage example."""
    print("\n" + "=" * 60)
    print("ENERGY COVERAGE EXAMPLE")
    print("=" * 60 + "\n")

    # Example major energy company
    result = run_assessment(
        entity_id="chevron-example",
        coverage="energy",
        entity_name="Chevron Corporation",
        domain_hint="chevron.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 246_000_000_000,
            "total_assets": 257_000_000_000,
            "employee_count": 43_846,
            "limit_requested": 500_000_000,
            "barrels_per_day": 3_100_000,
            "refineries": 6,
            "offshore_platforms": 15,
            "pipeline_miles": 12_000,
            "years_operating": 145,
            "safety_rating": "A",
            "environmental_certifications": ["ISO14001", "API"],
        },
        direct_query_responses={
            "major_spill_5yr": False,
            "regulatory_violations": False,
            "worker_fatality_3yr": False,
            "active_litigation": True,  # Common for large energy
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


def run_renewable_example():
    """Run renewable energy example."""
    print("\n" + "=" * 60)
    print("RENEWABLE ENERGY EXAMPLE")
    print("=" * 60 + "\n")

    # Renewable energy company
    result = run_assessment(
        entity_id="nextera-example",
        coverage="energy",
        entity_name="NextEra Energy",
        domain_hint="nexteraenergy.com",
        country_hint="US",
        submission_data={
            "annual_revenue": 21_000_000_000,
            "total_assets": 150_000_000_000,
            "employee_count": 15_000,
            "limit_requested": 200_000_000,
            "wind_turbines": 10_000,
            "solar_capacity_mw": 5_000,
            "battery_storage_mwh": 1_000,
            "years_operating": 35,
            "safety_rating": "A",
            "renewable_pct": 0.85,
        },
        direct_query_responses={
            "major_spill_5yr": False,
            "regulatory_violations": False,
            "worker_fatality_3yr": False,
            "active_litigation": False,
        },
        skip_discovery=True,
    )

    print_full_report(result)

    return result


if __name__ == "__main__":
    print("Running Energy Coverage Examples...")

    result1 = run_example()
    print("\n\n")
    result2 = run_renewable_example()

    # Comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"\nChevron (traditional energy):")
    print(f"  Score: {result1.composite_score:.0f}")
    print(f"  Tier: {result1.tier} ({result1.tier_label})")
    print(f"  Decision: {result1.decision.value}")
    print(f"  Premium: ${result1.recommended_premium:,.0f}")

    print(f"\nNextEra (renewable energy):")
    print(f"  Score: {result2.composite_score:.0f}")
    print(f"  Tier: {result2.tier} ({result2.tier_label})")
    print(f"  Decision: {result2.decision.value}")
    print(f"  Premium: ${result2.recommended_premium:,.0f}")
