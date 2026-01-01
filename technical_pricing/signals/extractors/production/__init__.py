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
    ├── sec/             # SEC EDGAR extractors
    └── regulatory/      # Government database extractors (OFAC, EPA, CFPB)

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
    - etc.

Available Free Extractors:
    DNS:
        - email_auth: SPF, DKIM, DMARC analysis
        - dnssec: DNSSEC validation status
        - dns_records: General DNS records and infrastructure

    HTTP:
        - security_headers: HTTP security header analysis
        - security_txt: RFC 9116 security.txt validation

    SEC:
        - sec_filings: SEC EDGAR filings (10-K, 10-Q, 8-K)
        - sec_financials: SEC EDGAR XBRL financial data

    Regulatory:
        - ofac_sanctions: OFAC SDN list search
        - epa_echo: EPA ECHO compliance data
        - cfpb_complaints: CFPB consumer complaint data
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
