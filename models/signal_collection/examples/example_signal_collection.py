"""
Example usage of Signal Collection Module

This example demonstrates how to use the signal collection module
to extract model-specific information from corporate websites.
"""

import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, "..")  # noqa: E402

from signal_collection import (
    CyberConfig,
    CyberSignalCollector,
    EnergyConfig,
    EnergySignalCollector,
    FinancialConfig,
    FinancialInstitutionSignalCollector,
)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}\n")


def example_1_cyber_collection():
    """Example 1: Collect cyber security signals"""
    print_section("EXAMPLE 1: Cyber Security Signal Collection")

    # Configure for cyber insurance
    config = CyberConfig(
        max_pages=15,  # Crawl up to 15 pages
        max_depth=2,  # Go 2 levels deep
        time_window_months=12,  # Last 12 months
        priority_urls=["/blog", "/news", "/security", "/press"],
    )

    # Create collector
    collector = CyberSignalCollector(config, timeout=10)

    # Collect signals from a corporate website
    print("Collecting cyber signals from corporate website...")
    print("(This would normally use a real website URL)\n")

    # For demonstration, we'll show what the result structure looks like
    print("Expected Output:")
    print("  Company: Example Tech Corp")
    print("  Pages Crawled: 15")
    print("  Signals Found: 8")
    print("  Collection Time: 12.5s")
    print("\n  Top Signals:")
    print("    1. Security Breach (Score: 0.92)")
    print("       'We detected a security breach affecting...'")
    print("       Source: blog, Date: 2024-10-15")
    print("\n    2. CISO Appointed (Score: 0.88)")
    print("       'John Smith appointed as Chief Information Security Officer...'")
    print("       Source: hire, Date: 2024-09-20")
    print("\n  Use Cases:")
    print("    - Identify recent security incidents for risk assessment")
    print("    - Track IT leadership changes")
    print("    - Monitor security posture improvements")

    # Real usage (commented out - requires website access):
    # result = collector.collect("Example Tech Corp", "https://example-tech.com")
    # if result.success:
    #     for signal in sorted(result.signals, key=lambda s: s.relevance_score, reverse=True)[:5]:
    #         print(f"  - {signal.keyword} (Score: {signal.relevance_score:.2f})")
    #         print(f"    {signal.context[:100]}...")
    #         print(f"    Source: {signal.source_type}, Date: {signal.date}")


def example_2_financial_collection():
    """Example 2: Collect financial institution signals"""
    print_section("EXAMPLE 2: Financial Institution Signal Collection")

    # Configure for financial institutions
    config = FinancialConfig(
        max_pages=20,
        max_depth=3,
        document_types=["Annual Report", "Integrated Report", "Financial Results"],
        priority_urls=[
            "/investors",
            "/reports",
            "/financial-information",
            "/results",
        ],
    )

    # Create collector
    collector = FinancialInstitutionSignalCollector(config, timeout=15)

    print("Collecting financial signals from bank website...")
    print("(This would normally use a real website URL)\n")

    print("Expected Output:")
    print("  Company: Example Bank plc")
    print("  Pages Crawled: 20")
    print("  Documents Found: 5")
    print("  Signals Found: 12")
    print("  Collection Time: 18.3s")
    print("\n  Documents Found:")
    print("    1. /reports/annual-report-2023.pdf")
    print("    2. /reports/integrated-report-2023.pdf")
    print("    3. /investors/results-q3-2024.pdf")
    print("\n  Key Metrics Extracted:")
    print("    - Total Assets: £450 billion")
    print("    - Net Income: £2.3 billion")
    print("    - Capital Ratio: 15.2%")
    print("    - NPL Ratio: 2.1%")
    print("\n  Use Cases:")
    print("    - Extract key financial metrics for underwriting")
    print("    - Identify regulatory compliance status")
    print("    - Monitor capital adequacy")
    print("    - Track asset quality trends")

    # Real usage:
    # result = collector.collect("Example Bank", "https://example-bank.com")
    # if result.success:
    #     print(f"\nDocuments Found: {len(result.documents_found)}")
    #     for doc in result.documents_found:
    #         print(f"  - {doc}")


def example_3_energy_collection():
    """Example 3: Collect energy company signals"""
    print_section("EXAMPLE 3: Energy Company Signal Collection")

    # Configure for energy companies
    config = EnergyConfig(
        max_pages=15,
        max_depth=2,
        time_window_months=24,  # Last 2 years for safety incidents
        document_types=["Safety Report", "Sustainability Report", "ESG Report"],
        priority_urls=[
            "/sustainability",
            "/safety",
            "/environment",
            "/esg",
            "/responsibility",
        ],
    )

    # Create collector
    collector = EnergySignalCollector(config, timeout=10)

    print("Collecting energy signals from oil & gas company...")
    print("(This would normally use a real website URL)\n")

    print("Expected Output:")
    print("  Company: Example Energy Corp")
    print("  Pages Crawled: 15")
    print("  Documents Found: 4")
    print("  Incidents Found: 2")
    print("  Signals Found: 10")
    print("  Collection Time: 14.2s")
    print("\n  Safety Incidents (Last 24 months):")
    print("    1. Minor Oil Spill - Offshore Facility")
    print("       Date: 2024-06-15, Severity: Low")
    print("       'A minor spill was contained within 2 hours...'")
    print("\n    2. Equipment Failure - Refinery")
    print("       Date: 2023-12-03, Severity: Medium")
    print("       'Routine maintenance identified potential issue...'")
    print("\n  Sustainability Signals:")
    print("    - Carbon reduction target: 50% by 2030")
    print("    - Renewable investment: $2B announced")
    print("    - Safety record: 0 fatalities in 2023")
    print("\n  Use Cases:")
    print("    - Assess environmental risk exposure")
    print("    - Track safety incident frequency and severity")
    print("    - Monitor ESG commitments and progress")
    print("    - Identify regulatory compliance issues")


def example_4_custom_configuration():
    """Example 4: Custom configuration for specific use case"""
    print_section("EXAMPLE 4: Custom Configuration")

    # Create highly customized configuration
    custom_config = CyberConfig(
        max_pages=30,
        max_depth=3,
        delay=2.0,  # Be polite - 2 second delay
        time_window_months=6,  # Only last 6 months
        priority_urls=[
            "/security-blog",
            "/technical-blog",
            "/engineering-blog",
        ],
        keywords=[
            "breach",
            "vulnerability",
            "patch",
            "zero-day",
            "ransomware",
            "phishing",
            "ddos",
        ],
        incident_keywords=["breach", "attack", "exploit", "compromise", "hack"],
        hire_keywords=[
            "appointed",
            "hired",
            "joins",
            "welcomes",
            "new ciso",
            "new cto",
        ],
    )

    print("Custom Configuration Created:")
    print(f"  Max Pages: {custom_config.max_pages}")
    print(f"  Max Depth: {custom_config.max_depth}")
    print(f"  Time Window: {custom_config.time_window_months} months")
    print(f"  Priority URLs: {', '.join(custom_config.priority_urls)}")
    print(f"  Keywords: {len(custom_config.keywords)} configured")
    print(f"  Incident Keywords: {len(custom_config.incident_keywords)} configured")
    print(f"  Hire Keywords: {len(custom_config.hire_keywords)} configured")

    print("\n  Use Cases:")
    print("    - Deep dive into specific company")
    print("    - Recent incident focus (6 months)")
    print("    - Expanded keyword coverage")
    print("    - Engineering/technical blog analysis")

    collector = CyberSignalCollector(custom_config)
    print(f"\n  Collector ready with custom configuration")


def example_5_batch_collection():
    """Example 5: Batch collection for multiple companies"""
    print_section("EXAMPLE 5: Batch Collection")

    # List of companies to analyze
    companies = {
        "Tech Corp": "https://techcorp.com",
        "FinTech Ltd": "https://fintech-ltd.com",
        "Cyber Solutions": "https://cybersolutions.com",
    }

    config = CyberConfig(max_pages=10, max_depth=2, time_window_months=12)
    collector = CyberSignalCollector(config, timeout=10)

    print("Batch Collection Setup:")
    print(f"  Companies: {len(companies)}")
    print(f"  Configuration: {config.max_pages} pages, {config.max_depth} depth")
    print(f"  Time Window: {config.time_window_months} months\n")

    print("Processing companies (demonstration):")
    for company_name, website_url in companies.items():
        print(f"\n  {company_name}:")
        print(f"    URL: {website_url}")
        print(f"    Status: Would collect signals...")
        print(f"    Expected: 8-15 signals, 2-5 documents")

        # Real usage:
        # result = collector.collect(company_name, website_url)
        # if result.success:
        #     print(f"    Found: {len(result.signals)} signals")
        #     print(f"    Top Signal: {result.signals[0].keyword if result.signals else 'None'}")
        # else:
        #     print(f"    Error: {', '.join(result.errors)}")

    print("\n  Use Cases:")
    print("    - Portfolio-wide risk assessment")
    print("    - Comparative analysis across insureds")
    print("    - Renewal preparation")
    print("    - Market intelligence gathering")


def example_6_integration_with_pricing():
    """Example 6: Integration with pricing workflow"""
    print_section("EXAMPLE 6: Integration with Pricing Workflow")

    print("Signal Collection in Pricing Workflow:\n")

    # Step 1: Discover website
    print("Step 1: Discover Corporate Website")
    print("  Input: Company name")
    print("  Output: corporate.example.com")
    print("  (Using Website Discovery Module)")

    # Step 2: Collect signals
    print("\nStep 2: Collect Signals")
    print("  Input: Corporate website URL")
    print("  Output: Collection result with signals")

    config = CyberConfig()
    collector = CyberSignalCollector(config)

    print(f"  Collector: CyberSignalCollector")
    print(f"  Config: {config.max_pages} pages, {config.time_window_months} months")

    # Step 3: Analyze signals for pricing
    print("\nStep 3: Analyze Signals for Pricing")
    print("  Signals found: 12")
    print("  Analysis:")
    print("    - Security incidents: 2 (medium severity)")
    print("    - Key hires: 1 (CISO appointment)")
    print("    - Security improvements: 3 mentions")
    print("    - Vulnerability disclosures: 1")

    # Step 4: Risk adjustments
    print("\nStep 4: Risk Adjustments")
    print("  Base Premium: £100,000")
    print("  Adjustments:")
    print("    - Recent breach detected: +15%")
    print("    - New CISO hired: -5%")
    print("    - Security improvements: -3%")
    print("  Final Premium: £107,000")

    print("\n  Integration Points:")
    print("    1. Website Discovery → Signal Collection")
    print("    2. Signal Collection → Risk Assessment")
    print("    3. Risk Assessment → Premium Calculation")
    print("    4. Premium Calculation → Quote Generation")

    print("\n  Code Example:")
    print("    # Step 1: Discover")
    print("    discovery_result = website_discovery.discover(company_name)")
    print("    website_url = discovery_result.best_match.url")
    print()
    print("    # Step 2: Collect")
    print("    collection_result = collector.collect(company_name, website_url)")
    print()
    print("    # Step 3: Analyze")
    print("    risk_factors = analyze_signals(collection_result.signals)")
    print()
    print("    # Step 4: Price")
    print("    premium = calculate_premium(base_profile, risk_factors)")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("SIGNAL COLLECTION MODULE - EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating configurable signal collection from corporate websites")
    print("for insurance pricing across different models.")

    # Run examples
    example_1_cyber_collection()
    example_2_financial_collection()
    example_3_energy_collection()
    example_4_custom_configuration()
    example_5_batch_collection()
    example_6_integration_with_pricing()

    # Summary
    print_section("SUMMARY")
    print("The Signal Collection Module provides:")
    print("\n  1. Model-Specific Collectors")
    print("     - CyberSignalCollector: Security incidents, IT hires")
    print("     - FinancialInstitutionSignalCollector: Reports, metrics")
    print("     - EnergySignalCollector: Safety incidents, ESG")
    print("\n  2. Configurable Extraction")
    print("     - Custom keywords per model")
    print("     - Priority URLs for efficient crawling")
    print("     - Time windows for relevance")
    print("     - Document type targeting")
    print("\n  3. Intelligent Analysis")
    print("     - Date-aware filtering")
    print("     - Relevance scoring")
    print("     - Context extraction")
    print("     - Pattern matching")
    print("\n  4. Integration Ready")
    print("     - Works with Website Discovery")
    print("     - Feeds into Pricing Models")
    print("     - Batch processing support")
    print("     - Structured results")

    print("\n" + "=" * 80)
    print("For real usage, replace demonstration URLs with actual corporate websites.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
