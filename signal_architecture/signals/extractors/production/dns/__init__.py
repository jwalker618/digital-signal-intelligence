"""
DSI Production Extractors - DNS-based

This module provides production extractors that query DNS records.
These are FREE to use - no API keys required.

Extractors:
    - EmailAuthExtractor: SPF, DKIM, DMARC records
    - DNSSECExtractor: DNSSEC validation status
    - DNSRecordsExtractor: General DNS record lookup
    - WHOISRDAPExtractor: Domain WHOIS/RDAP registration data

Requirements:
    - dnspython: pip install dnspython
    - requests: pip install requests (for RDAP)

Usage:
    from signals.extractors.production.dns import (
        EmailAuthExtractor,
        DNSSECExtractor,
        WHOISRDAPExtractor,
    )

    extractor = EmailAuthExtractor()
    result = extractor.extract('example.com')
    print(result.data)
    # {'spf': {'exists': True, 'record': 'v=spf1 include:_spf.google.com ~all', ...}, ...}

    rdap = WHOISRDAPExtractor()
    result = rdap.extract('example.com')
    # {'domain': 'example.com', 'registered': True, 'domain_age_days': 9500, ...}
"""

from .email_auth import EmailAuthExtractor
from .dnssec import DNSSECExtractor
from .records import DNSRecordsExtractor
from .whois_rdap import WHOISRDAPExtractor
from ..factory import register_production

__all__ = [
    'EmailAuthExtractor',
    'DNSSECExtractor',
    'DNSRecordsExtractor',
    'WHOISRDAPExtractor',
    'register_all',
]


def register_all():
    """Register all DNS extractors with the factory."""
    register_production('email_auth', EmailAuthExtractor)
    register_production('dnssec', DNSSECExtractor)
    register_production('dns_records', DNSRecordsExtractor)
    register_production('whois_rdap', WHOISRDAPExtractor)
