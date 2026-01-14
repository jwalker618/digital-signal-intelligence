"""
DSI Production Extractors - HTTP-based

This module provides production extractors that analyze HTTP responses.
These are FREE to use - no API keys required.

Extractors:
    - SecurityHeadersExtractor: Security-related HTTP headers
    - SecurityTxtExtractor: RFC 9116 security.txt file
    - WAFPresenceExtractor: Web Application Firewall detection
    - CDNUsageExtractor: Content Delivery Network detection

Requirements:
    - requests: pip install requests

Usage:
    from signals.extractors.production.http import (
        SecurityHeadersExtractor,
        SecurityTxtExtractor,
    )

    extractor = SecurityHeadersExtractor()
    result = extractor.extract('example.com')
"""

from .security_headers import SecurityHeadersExtractor
from .security_txt import SecurityTxtExtractor
from ..factory import register_production

__all__ = [
    'SecurityHeadersExtractor',
    'SecurityTxtExtractor',
    'register_all',
]


def register_all():
    """Register all HTTP extractors with the factory."""
    register_production('security_headers', SecurityHeadersExtractor)
    register_production('security_txt', SecurityTxtExtractor)
