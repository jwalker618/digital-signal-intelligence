"""
DSI Signal Architecture - Production Extractors

This module contains production-ready extractor implementations that connect
to real external data sources (APIs, databases, web scraping, etc.).

Structure:
    production/
    ├── base.py          # ProductionExtractor base class
    ├── factory.py       # Factory for swapping stub/production
    ├── config.py        # Configuration and API keys
    ├── dns/             # DNS-based extractors (SPF, DKIM, DMARC, DNSSEC)
    ├── http/            # HTTP header extractors
    ├── network/         # Network infrastructure extractors (cloud, CDN, WAF, TLS)
    ├── sec/             # SEC EDGAR extractors (filings, financials, litigation, governance)
    ├── regulatory/      # Government database extractors (OFAC, EPA, CFPB, OSHA, FAA, EU, FDIC)
    ├── security/        # Security/vulnerability extractors (NVD CVE, HHS Breach)
    └── industry/        # Industry-specific registries (PCAOB, Aviation Safety)

Usage:
    from technical_pricing.signals.extractors.production import (
        ExtractorFactory,
        get_extractor,
        register_all_extractors,
    )

    # Register all production extractors
    register_all_extractors()

    # Get extractor (uses production if available, falls back to stub)
    extractor = get_extractor('email_auth', mode='production')
    result = extractor.extract(entity_id='example.com')

    # Or explicitly use stub
    extractor = get_extractor('email_auth', mode='stub')

Configuration:
    Set environment variables or use config.py for API keys:
    - DSI_EXTRACTOR_MODE: 'production' | 'stub' | 'hybrid'
    - DSI_SHODAN_API_KEY: Shodan API key
    - DSI_SSL_LABS_EMAIL: SSL Labs registration email
    - DSI_NVD_API_KEY: NVD API key (optional, increases rate limit)
    - etc.

Available Free Extractors (28 total):
    DNS (3):
        - email_auth: SPF, DKIM, DMARC analysis
        - dnssec: DNSSEC validation status
        - dns_records: General DNS records and infrastructure

    HTTP (2):
        - security_headers: HTTP security header analysis
        - security_txt: RFC 9116 security.txt validation

    Network (4):
        - cloud_infra: Cloud provider detection (AWS, Azure, GCP, etc.)
        - cdn_usage: CDN detection (Cloudflare, Akamai, Fastly, etc.)
        - waf_presence: WAF detection (Cloudflare, AWS WAF, Imperva, etc.)
        - tls_config: TLS/SSL configuration analysis

    SEC (4):
        - sec_filings: SEC EDGAR filings (10-K, 10-Q, 8-K)
        - sec_financials: SEC EDGAR XBRL financial data
        - sec_litigation: SEC 8-K litigation/legal disclosures
        - sec_governance: SEC DEF 14A governance analysis

    Regulatory (8):
        - ofac_sanctions: OFAC SDN list search
        - epa_echo: EPA ECHO compliance data
        - cfpb_complaints: CFPB consumer complaint data
        - osha_violations: OSHA workplace safety violations
        - faa_certificate: FAA operating certificate status
        - eu_safety_list: EU Air Safety banned airlines list
        - fdic_enforcement: FDIC/OCC/Fed bank enforcement actions
        - bsee_incidents: BSEE offshore drilling incidents

    Security (2):
        - nvd_cve: NIST NVD vulnerability database search
        - hhs_breach: HHS HIPAA breach portal

    Industry (2):
        - pcaob: PCAOB registered auditor status
        - aviation_safety: Aviation Safety Network accident database

    Corporate (1):
        - companies_house: UK Companies House registry

    Maritime/Aviation (2):
        - imo_gisis: IMO GISIS ship registry
        - iosa_registry: IATA IOSA airline safety registry
"""

from .base import ProductionExtractor
from .factory import ExtractorFactory, get_extractor, set_default_mode
from .config import ExtractorConfig

__all__ = [
    'ProductionExtractor',
    'ExtractorFactory',
    'ExtractorConfig',
    'get_extractor',
    'set_default_mode',
    'register_all_extractors',
]


def register_all_extractors():
    """
    Register all production extractors with the factory.

    Call this at application startup to make all production
    extractors available via get_extractor().
    """
    # Import and register DNS extractors
    try:
        from .dns import register_all as register_dns
        register_dns()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register DNS extractors: {e}")

    # Import and register HTTP extractors
    try:
        from .http import register_all as register_http
        register_http()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register HTTP extractors: {e}")

    # Import and register SEC extractors
    try:
        from .sec import register_all as register_sec
        register_sec()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register SEC extractors: {e}")

    # Import and register regulatory extractors
    try:
        from .regulatory import register_all as register_regulatory
        register_regulatory()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register regulatory extractors: {e}")

    # Import and register network extractors
    try:
        from .network import register_all as register_network
        register_network()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register network extractors: {e}")

    # Import and register security extractors
    try:
        from .security import register_all as register_security
        register_security()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register security extractors: {e}")

    # Import and register industry extractors
    try:
        from .industry import register_all as register_industry
        register_industry()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register industry extractors: {e}")

    # Import and register corporate extractors
    try:
        from .corporate import register_all as register_corporate
        register_corporate()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register corporate extractors: {e}")

    # Import and register maritime extractors
    try:
        from .maritime import register_all as register_maritime
        register_maritime()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not register maritime extractors: {e}")
