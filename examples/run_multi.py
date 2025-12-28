"""
Multi-Coverage Orchestration Example (Phase 14)

Demonstrates:
- Multi-coverage request handling
- Locale detection
- Shared signal cache
- Package discounts
- Aggregated results
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technical_pricing.orchestration import (
    MultiCoverageOrchestrator,
    MultiCoverageRequest,
    CoverageRequest,
    LocaleDetector,
    ResultsAggregator,
)
from examples.utils import print_header


async def run_multi_coverage_example():
    """Run multi-coverage orchestration example."""
    print("\n" + "=" * 60)
    print("MULTI-COVERAGE ORCHESTRATION EXAMPLE")
    print("=" * 60 + "\n")

    # Create orchestrator
    orchestrator = MultiCoverageOrchestrator()

    # Create multi-coverage request for a tech company
    request = MultiCoverageRequest(
        entity_id="acme-tech-corp",
        entity_name="ACME Technology Corporation",
        domain_hint="acmetech.com",
        country_hint="US",
        coverages=[
            CoverageRequest(
                coverage="cyber",
                locale="US",
                submission_data={
                    "annual_revenue": 500_000_000,
                    "employee_count": 2000,
                    "records_stored": 50_000_000,
                    "limit_requested": 25_000_000,
                },
            ),
            CoverageRequest(
                coverage="do",
                locale="US",
                submission_data={
                    "market_cap": 2_000_000_000,
                    "annual_revenue": 500_000_000,
                    "employee_count": 2000,
                    "limit_requested": 25_000_000,
                    "public_company": True,
                },
            ),
            CoverageRequest(
                coverage="pi",
                locale="US",
                submission_data={
                    "annual_revenue": 500_000_000,
                    "employee_count": 2000,
                    "limit_requested": 10_000_000,
                },
            ),
        ],
        auto_detect_locales=False,
        apply_package_discounts=True,
    )

    # Execute multi-coverage assessment
    result = await orchestrator.execute(request)

    # Print results
    print_header("MULTI-COVERAGE RESULTS")
    print(f"Entity: {result.entity_id}")
    print(f"Total Coverages: {len(result.coverage_results)}")
    print(f"Execution Time: {result.total_execution_time_ms:.0f}ms")
    print()

    for coverage_id, coverage_result in result.coverage_results.items():
        print(f"\n{coverage_id.upper()} Coverage:")
        print(f"  Score: {coverage_result.composite_score:.0f}")
        print(f"  Tier: {coverage_result.tier} ({coverage_result.tier_label})")
        print(f"  Decision: {coverage_result.decision}")
        print(f"  Premium: ${coverage_result.recommended_premium:,.0f}")

    print()
    print_header("PACKAGE PRICING")
    print(f"Subtotal: ${result.subtotal_premium:,.0f}")
    if result.package_discount:
        print(f"Package Discount: {result.package_discount_rate:.0%}")
        print(f"Discount Amount: -${result.package_discount:,.0f}")
    print(f"Total Premium: ${result.total_premium:,.0f}")

    if result.shared_signals:
        print()
        print_header("SHARED SIGNALS")
        print(f"Signals cached and reused: {len(result.shared_signals)}")
        for signal_id in list(result.shared_signals.keys())[:5]:
            print(f"  - {signal_id}")
        if len(result.shared_signals) > 5:
            print(f"  ... and {len(result.shared_signals) - 5} more")

    return result


async def run_locale_detection_example():
    """Run locale detection example."""
    print("\n" + "=" * 60)
    print("LOCALE DETECTION EXAMPLE")
    print("=" * 60 + "\n")

    detector = LocaleDetector()

    # Test various entity scenarios
    test_cases = [
        {
            "entity_name": "Deutsche Bank AG",
            "domain_hint": "deutsche-bank.de",
            "country_hint": None,
        },
        {
            "entity_name": "HSBC Holdings",
            "domain_hint": "hsbc.co.uk",
            "country_hint": None,
        },
        {
            "entity_name": "Toyota Motor Corporation",
            "domain_hint": "toyota.co.jp",
            "country_hint": "JP",
        },
        {
            "entity_name": "Unknown Corp",
            "domain_hint": "unknown.com",
            "country_hint": None,
        },
    ]

    print("Detecting locales for various entities:\n")

    for case in test_cases:
        result = detector.detect_locale(
            entity_name=case["entity_name"],
            domain_hint=case["domain_hint"],
            country_hint=case["country_hint"],
        )

        print(f"{case['entity_name']}:")
        print(f"  Domain: {case['domain_hint']}")
        print(f"  Detected Locale: {result.primary_locale}")
        print(f"  Confidence: {result.confidence:.0%}")
        print(f"  Method: {result.detection_method}")
        if result.alternate_locales:
            print(f"  Alternates: {result.alternate_locales}")
        print()


async def run_aggregation_example():
    """Run results aggregation example."""
    print("\n" + "=" * 60)
    print("RESULTS AGGREGATION EXAMPLE")
    print("=" * 60 + "\n")

    # First run multi-coverage to get results
    orchestrator = MultiCoverageOrchestrator()
    aggregator = ResultsAggregator()

    request = MultiCoverageRequest(
        entity_id="multi-entity-test",
        entity_name="Multi Entity Test Corp",
        domain_hint="multitest.com",
        country_hint="US",
        coverages=[
            CoverageRequest(coverage="cyber", locale="US"),
            CoverageRequest(coverage="do", locale="US"),
        ],
    )

    result = await orchestrator.execute(request)

    # Aggregate results
    summary = aggregator.summarize(result)

    print_header("AGGREGATED SUMMARY")
    print(f"Entity: {summary.entity_id}")
    print(f"Total Coverages: {summary.coverage_count}")
    print()

    print("Score Distribution:")
    print(f"  Average: {summary.average_score:.0f}")
    print(f"  Min: {summary.min_score:.0f}")
    print(f"  Max: {summary.max_score:.0f}")
    print()

    print("Tier Distribution:")
    for tier, count in summary.tier_distribution.items():
        print(f"  Tier {tier}: {count} coverage(s)")
    print()

    print("Decision Summary:")
    for decision, count in summary.decision_distribution.items():
        print(f"  {decision}: {count} coverage(s)")
    print()

    print(f"Total Premium: ${summary.total_premium:,.0f}")

    if summary.referral_reasons:
        print()
        print("Referral Reasons (across all coverages):")
        for reason in summary.referral_reasons:
            print(f"  - {reason}")


async def main():
    """Run all multi-coverage examples."""
    print("Running Multi-Coverage Examples...")

    # Multi-coverage orchestration
    await run_multi_coverage_example()

    print("\n\n")

    # Locale detection
    await run_locale_detection_example()

    print("\n\n")

    # Results aggregation
    await run_aggregation_example()

    print("\n" + "=" * 60)
    print("ALL MULTI-COVERAGE EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
