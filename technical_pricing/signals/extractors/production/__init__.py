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
    ├── tls/             # TLS/SSL extractors
    ├── http/            # HTTP header extractors
    ├── regulatory/      # Government database extractors
    ├── sec/             # SEC EDGAR extractors
    └── breach/          # Breach database extractors

Usage:
    from technical_pricing.signals.extractors.production import (
        ExtractorFactory,
        get_extractor,
    )

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
]
