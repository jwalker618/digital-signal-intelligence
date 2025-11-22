"""
Example: DSI API Client

Demonstrates how to interact with the DSI REST API
"""

from typing import Any, Dict

import requests


class DSIAPIClient:
    """Client for interacting with DSI API"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def cyber_quote(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get cyber insurance quote"""
        response = requests.post(
            f"{self.api_base}/cyber/quote",
            json=profile,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def energy_quote(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get energy insurance quote"""
        response = requests.post(
            f"{self.api_base}/energy/quote",
            json=profile,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def fi_quote(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get financial institution insurance quote"""
        response = requests.post(
            f"{self.api_base}/financial/quote",
            json=profile,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()


def example_cyber_api_call():
    """Example: Get a cyber insurance quote via API"""
    print("=" * 80)
    print("EXAMPLE: Cyber Insurance Quote via API")
    print("=" * 80)

    client = DSIAPIClient()

    # Check API health
    try:
        health = client.health_check()
        print(f"\nAPI Status: {health['status']}")
        print(f"Version: {health['version']}")
    except Exception:
        print("\nError: API not available. Please start the API server first.")
        print("Run: python -m api.server")
        return

    # Create quote request
    quote_request = {
        "company_name": "TechCorp",
        "industry": "TECHNOLOGY",
        "country": "United States",
        "annual_revenue": 50000000,
        "employees": 250,
        "records_stored": 500000,
        "coverage_type": "COMPREHENSIVE",
        "cloud_percentage": 80,
        "legacy_systems": False,
        "pii_volume": "medium",
        "phi_handler": False,
        "pci_scope": False,
        "prior_incidents": 0,
        "cyber_insurance_history": 1,
        "it_budget_pct": 10.0,
        "signals": {
            "ssl_certificate": 85,
            "tls_version": 90,
            "security_headers": 80,
            "dnssec_implementation": 75,
            "spf_dmarc_dkim": 82,
            "web_application_firewall": 78,
            "open_ports_score": 80,
            "outdated_software": 75,
            "known_vulnerabilities": 80,
            "exposed_databases": 90,
            "leaked_credentials": 85,
            "breached_history": 90,
            "security_certifications": 80,
            "privacy_policy_quality": 75,
            "incident_response_plan": 70,
            "bug_bounty_program": 75,
            "security_team_visibility": 72,
            "security_blog_activity": 65,
            "vendor_security_standards": 75,
            "supply_chain_transparency": 70,
            "cloud_provider_quality": 85,
            "third_party_integrations": 75,
            "data_processor_agreements": 72,
            "patch_discipline": 80,
            "security_investment": 75,
            "employee_training": 70,
            "mfa_adoption": 85,
            "backup_procedures": 80,
            "monitoring_capabilities": 78,
        },
    }

    try:
        # Get quote
        result = client.cyber_quote(quote_request)

        if result.get("success"):
            print("\n✅ Quote Generated Successfully")
            print(f"\nCompany: {result['company_name']}")
            print(f"Coverage: {result['coverage_type']}")
            print(f"Composite Score: {result['composite_score']:.0f}/1000")
            print(f"Risk Tier: {result['risk_tier']}")
            print(f"Annual Premium: ${result['annual_premium']:,.2f}")
            print(f"Recommended Limit: ${result['recommended_limit']:,.0f}")
            print(f"Breach Probability: {result['breach_probability']:.1%}")
            print(f"Recommendation: {result['recommendation']}")

            if result.get("recommendations"):
                print("\nTop Recommendations:")
                for rec in result["recommendations"][:3]:
                    print(f"  • {rec}")
        else:
            print(f"\n❌ Error: {result.get('error')}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {str(e)}")


def example_batch_quotes():
    """Example: Get multiple quotes in batch"""
    print("\n" + "=" * 80)
    print("EXAMPLE: Batch Quotes via API")
    print("=" * 80)

    client = DSIAPIClient()

    companies = [
        {
            "name": "StartupCo",
            "type": "cyber",
            "data": {
                "company_name": "StartupCo",
                "industry": "TECHNOLOGY",
                "country": "United States",
                "annual_revenue": 10000000,
                "employees": 50,
                "records_stored": 100000,
                "coverage_type": "FIRST_PARTY",
                "signals": {
                    "ssl_certificate": 70,
                    "tls_version": 75,
                    # ... minimal signals for example
                },
            },
        },
        # Add more companies as needed
    ]

    print(f"\nProcessing {len(companies)} quotes...")
    print("-" * 80)

    for company in companies:
        try:
            if company["type"] == "cyber":
                result = client.cyber_quote(company["data"])
            elif company["type"] == "energy":
                result = client.energy_quote(company["data"])
            elif company["type"] == "financial":
                result = client.fi_quote(company["data"])

            if result.get("success"):
                print(
                    f"✅ {company['name']}: ${result['annual_premium']:,.0f} "
                    f"({result['risk_tier']})"
                )
            else:
                print(f"❌ {company['name']}: {result.get('error')}")

        except Exception as e:
            print(f"❌ {company['name']}: {str(e)}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DSI API CLIENT EXAMPLES")
    print("=" * 80)
    print("\nNote: Make sure the API server is running:")
    print("  python -m api.server")
    print("  or")
    print("  docker-compose up")
    print()

    example_cyber_api_call()
    example_batch_quotes()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80 + "\n")
