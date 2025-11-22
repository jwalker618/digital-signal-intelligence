"""
Example: Cyber Insurance Pricing

Demonstrates how to use the DSI Cyber Insurance Pricing Model
"""

import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent / "models"))

from cyber.dsi_cyber_pricing import (  # noqa: E402
    CompanySize,
    CyberCompanyProfile,
    CyberCoverageType,
    CyberInsurancePricingModel,
    CyberSecuritySignals,
    IndustryVertical,
)


def example_tech_company():
    """Example: Technology company with strong security posture"""
    print("=" * 80)
    print("EXAMPLE 1: Secure Technology Company")
    print("=" * 80)

    # Create strong security signals
    signals = CyberSecuritySignals(
        ssl_certificate=95,
        tls_version=100,
        security_headers=90,
        dnssec_implementation=85,
        spf_dmarc_dkim=92,
        web_application_firewall=88,
        open_ports_score=90,
        outdated_software=88,
        known_vulnerabilities=92,
        exposed_databases=100,
        leaked_credentials=95,
        breached_history=100,
        security_certifications=90,
        privacy_policy_quality=88,
        incident_response_plan=85,
        bug_bounty_program=92,
        security_team_visibility=87,
        security_blog_activity=80,
        vendor_security_standards=85,
        supply_chain_transparency=82,
        cloud_provider_quality=95,
        third_party_integrations=88,
        data_processor_agreements=85,
        patch_discipline=90,
        security_investment=88,
        employee_training=85,
        mfa_adoption=95,
        backup_procedures=90,
        monitoring_capabilities=92,
    )

    # Create company profile
    company = CyberCompanyProfile(
        company_name="SecureTech Inc",
        industry=IndustryVertical.TECHNOLOGY,
        country="United States",
        annual_revenue=100_000_000,
        employees=500,
        size_category=CompanySize.SMALL,
        records_stored=1_000_000,
        pii_volume="medium",
        phi_handler=False,
        pci_scope=False,
        cloud_percentage=85,
        legacy_systems=False,
        bring_your_own_device=False,
        remote_workforce_pct=50,
        prior_incidents=0,
        cyber_insurance_history=2,
        it_budget_pct=15.0,
        signals=signals,
    )

    # Calculate pricing
    model = CyberInsurancePricingModel(coverage_type=CyberCoverageType.COMPREHENSIVE)
    result = model.calculate_premium(company)

    # Display results
    print(f"\nCompany: {result.company_name}")
    print(f"Composite Score: {result.composite_score:.0f}/1000")
    print(f"Risk Tier: {result.risk_tier}")
    print(f"Annual Premium: ${result.annual_premium:,.2f}")
    print(f"Recommended Limit: ${result.recommended_limit:,.0f}")
    print(f"Recommended Retention: ${result.recommended_retention:,.0f}")
    print(f"Breach Probability: {result.breach_probability:.1%}")
    print(f"Recommendation: {result.recommendation}")
    print("\nKey Recommendations:")
    for rec in result.recommendations[:5]:
        print(f"  • {rec}")


def example_healthcare_vulnerable():
    """Example: Healthcare company with security vulnerabilities"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Healthcare Company with Vulnerabilities")
    print("=" * 80)

    # Create vulnerable signals
    signals = CyberSecuritySignals(
        ssl_certificate=75,
        tls_version=60,
        security_headers=55,
        dnssec_implementation=40,
        spf_dmarc_dkim=50,
        web_application_firewall=45,
        open_ports_score=45,
        outdated_software=38,
        known_vulnerabilities=35,
        exposed_databases=40,
        leaked_credentials=30,
        breached_history=35,
        security_certifications=55,
        privacy_policy_quality=60,
        incident_response_plan=45,
        bug_bounty_program=0,
        security_team_visibility=50,
        security_blog_activity=30,
        vendor_security_standards=48,
        supply_chain_transparency=42,
        cloud_provider_quality=65,
        third_party_integrations=50,
        data_processor_agreements=45,
        patch_discipline=35,
        security_investment=40,
        employee_training=45,
        mfa_adoption=50,
        backup_procedures=55,
        monitoring_capabilities=48,
    )

    # Create company profile
    company = CyberCompanyProfile(
        company_name="Regional Hospital",
        industry=IndustryVertical.HEALTHCARE,
        country="United States",
        annual_revenue=500_000_000,
        employees=3000,
        size_category=CompanySize.MEDIUM,
        records_stored=5_000_000,
        pii_volume="critical",
        phi_handler=True,
        pci_scope=True,
        cloud_percentage=40,
        legacy_systems=True,
        bring_your_own_device=True,
        remote_workforce_pct=30,
        prior_incidents=2,
        cyber_insurance_history=1,
        it_budget_pct=5.0,
        signals=signals,
    )

    # Calculate pricing
    model = CyberInsurancePricingModel(coverage_type=CyberCoverageType.COMPREHENSIVE)
    result = model.calculate_premium(company)

    # Display results
    print(f"\nCompany: {result.company_name}")
    print(f"Composite Score: {result.composite_score:.0f}/1000")
    print(f"Risk Tier: {result.risk_tier}")
    print(f"Annual Premium: ${result.annual_premium:,.2f}")
    print(f"Recommended Limit: ${result.recommended_limit:,.0f}")
    print(f"Recommended Retention: ${result.recommended_retention:,.0f}")
    print(f"Breach Probability: {result.breach_probability:.1%}")
    print(f"Recommendation: {result.recommendation}")
    print("\nCritical Recommendations:")
    for rec in result.recommendations[:8]:
        print(f"  • {rec}")


def example_api_usage():
    """Example: Using the API for batch pricing"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Batch Pricing with API")
    print("=" * 80)

    companies = [
        ("FinTech Startup", IndustryVertical.FINANCIAL, 50_000_000, 200, 500_000),
        ("E-commerce Platform", IndustryVertical.RETAIL, 200_000_000, 1000, 10_000_000),
        ("SaaS Provider", IndustryVertical.TECHNOLOGY, 75_000_000, 300, 2_000_000),
    ]

    print("\nBatch Pricing Results:")
    print("-" * 80)
    print(f"{'Company':<25} {'Score':<10} {'Tier':<10} {'Premium':<15} {'Prob':<10}")
    print("-" * 80)

    for name, industry, revenue, employees, records in companies:
        # Create moderate signals
        signals = CyberSecuritySignals(
            ssl_certificate=75,
            tls_version=80,
            security_headers=70,
            dnssec_implementation=65,
            spf_dmarc_dkim=70,
            web_application_firewall=65,
            open_ports_score=70,
            outdated_software=68,
            known_vulnerabilities=72,
            exposed_databases=75,
            leaked_credentials=70,
            breached_history=75,
            security_certifications=70,
            privacy_policy_quality=68,
            incident_response_plan=65,
            bug_bounty_program=60,
            security_team_visibility=67,
            security_blog_activity=60,
            vendor_security_standards=68,
            supply_chain_transparency=62,
            cloud_provider_quality=75,
            third_party_integrations=68,
            data_processor_agreements=65,
            patch_discipline=70,
            security_investment=68,
            employee_training=65,
            mfa_adoption=72,
            backup_procedures=70,
            monitoring_capabilities=68,
        )

        company = CyberCompanyProfile(
            company_name=name,
            industry=industry,
            country="United States",
            annual_revenue=revenue,
            employees=employees,
            size_category=CompanySize.SMALL,
            records_stored=records,
            pii_volume="medium",
            phi_handler=False,
            pci_scope=False,
            cloud_percentage=70,
            legacy_systems=False,
            bring_your_own_device=True,
            remote_workforce_pct=40,
            prior_incidents=0,
            cyber_insurance_history=0,
            it_budget_pct=8.0,
            signals=signals,
        )

        model = CyberInsurancePricingModel(coverage_type=CyberCoverageType.THIRD_PARTY)
        result = model.calculate_premium(company)

        print(
            f"{name:<25} {result.composite_score:<10.0f} {result.risk_tier:<10} "
            f"${result.annual_premium:<14,.0f} {result.breach_probability:<10.1%}"
        )


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DSI CYBER INSURANCE PRICING EXAMPLES")
    print("=" * 80)

    example_tech_company()
    example_healthcare_vulnerable()
    example_api_usage()

    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80 + "\n")
