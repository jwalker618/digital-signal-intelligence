"""
DSI Production Extractors - Network Infrastructure

This module provides production extractors for network infrastructure analysis.
These are FREE to use - based on DNS queries, HTTP requests, and IP analysis.

Extractors:
    - CloudInfraExtractor: Detect cloud providers from IP ranges
    - CDNUsageExtractor: Detect CDN from CNAME records
    - WAFPresenceExtractor: Detect WAF from HTTP headers
    - TLSConfigExtractor: Analyze TLS/SSL configuration

Requirements:
    - dnspython: pip install dnspython
    - requests: pip install requests

Usage:
    from signals.extractors.production.network import (
        CloudInfraExtractor,
        CDNUsageExtractor,
        WAFPresenceExtractor,
        TLSConfigExtractor,
    )

    extractor = CloudInfraExtractor()
    result = extractor.extract('example.com')
"""

from .cloud_infra import CloudInfraExtractor
from .cdn_usage import CDNUsageExtractor
from .waf_presence import WAFPresenceExtractor
from .tls_config import TLSConfigExtractor
from ..factory import register_production

__all__ = [
    'CloudInfraExtractor',
    'CDNUsageExtractor',
    'WAFPresenceExtractor',
    'TLSConfigExtractor',
    'register_all',
]


def register_all():
    """Register all network extractors with the factory."""
    register_production('cloud_infra', CloudInfraExtractor)
    register_production('cdn_usage', CDNUsageExtractor)
    register_production('waf_presence', WAFPresenceExtractor)
    register_production('tls_config', TLSConfigExtractor)
