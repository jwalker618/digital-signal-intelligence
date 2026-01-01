"""
DSI Production Extractors - DNS-based

This module provides production extractors that query DNS records.
These are FREE to use - no API keys required.

Extractors:
    - EmailAuthExtractor: SPF, DKIM, DMARC records
    - DNSSECExtractor: DNSSEC validation status
    - DNSRecordsExtractor: General DNS record lookup

Requirements:
    - dnspython: pip install dnspython

Usage:
    from technical_pricing.signals.extractors.production.dns import (
        EmailAuthExtractor,
        DNSSECExtractor,
    )

    extractor = EmailAuthExtractor()
    result = extractor.extract('example.com')
    print(result.data)
    # {'spf': {'exists': True, 'record': 'v=spf1 include:_spf.google.com ~all', ...}, ...}
"""

from .email_auth import EmailAuthExtractor
from .dnssec import DNSSECExtractor
from .records import DNSRecordsExtractor
from ..factory import register_production

__all__ = [
    'EmailAuthExtractor',
    'DNSSECExtractor',
    'DNSRecordsExtractor',
    'register_all',
]


def register_all():
    """Register all DNS extractors with the factory."""
    register_production('email_auth', EmailAuthExtractor)
    register_production('dnssec', DNSSECExtractor)
    register_production('dns_records', DNSRecordsExtractor)
