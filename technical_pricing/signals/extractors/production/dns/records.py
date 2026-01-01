"""
DSI Production Extractor - DNS Records

General DNS record lookup for infrastructure analysis.
This is a FREE extractor - no API keys required.

Use Cases:
    - Identify hosting providers (A, AAAA records)
    - Detect CDN usage (CNAME analysis)
    - Find mail servers (MX records)
    - Discover subdomains (NS records)
"""

import logging
import re
from typing import Any, Dict, List, Optional

try:
    import dns.resolver
    import dns.exception
    import dns.reversename
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class DNSRecordsExtractor(ProductionExtractor):
    """
    Extracts general DNS records for infrastructure analysis.

    Queries:
        - A records (IPv4 addresses)
        - AAAA records (IPv6 addresses)
        - MX records (mail servers)
        - NS records (name servers)
        - CNAME records (aliases)
        - TXT records (various metadata)

    Output:
        {
            'a_records': [{'ip': '1.2.3.4', 'provider': 'AWS', ...}],
            'aaaa_records': [...],
            'mx_records': [{'host': 'mail.example.com', 'priority': 10, 'provider': 'Google'}],
            'ns_records': [{'host': 'ns1.example.com', 'provider': 'Cloudflare'}],
            'cname_records': [...],
            'txt_records': [...],
            'infrastructure': {
                'hosting_provider': 'AWS',
                'cdn_provider': 'Cloudflare',
                'email_provider': 'Google Workspace',
                'dns_provider': 'Cloudflare',
            },
        }
    """

    SOURCE_NAME = "dns_records"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    RATE_LIMIT = 10.0
    COST_TIER = "free"

    # Known provider patterns
    HOSTING_PROVIDERS = {
        'amazonaws.com': 'AWS',
        'cloudfront.net': 'AWS CloudFront',
        'azure': 'Microsoft Azure',
        'googleusercontent.com': 'Google Cloud',
        'google.com': 'Google',
        'cloudflare': 'Cloudflare',
        'fastly': 'Fastly',
        'akamai': 'Akamai',
        'edgecast': 'Edgecast/Verizon',
        'stackpath': 'StackPath',
        'digitalocean': 'DigitalOcean',
        'linode': 'Linode',
        'vultr': 'Vultr',
        'heroku': 'Heroku',
        'netlify': 'Netlify',
        'vercel': 'Vercel',
        'github': 'GitHub Pages',
        'shopify': 'Shopify',
        'squarespace': 'Squarespace',
        'wix': 'Wix',
    }

    EMAIL_PROVIDERS = {
        'google.com': 'Google Workspace',
        'googlemail.com': 'Google Workspace',
        'outlook.com': 'Microsoft 365',
        'protection.outlook.com': 'Microsoft 365',
        'pphosted.com': 'Proofpoint',
        'mimecast': 'Mimecast',
        'barracuda': 'Barracuda',
        'mailgun': 'Mailgun',
        'sendgrid': 'SendGrid',
        'amazonses': 'Amazon SES',
        'zoho': 'Zoho Mail',
    }

    DNS_PROVIDERS = {
        'cloudflare': 'Cloudflare',
        'awsdns': 'AWS Route 53',
        'azure-dns': 'Azure DNS',
        'googledomains': 'Google Domains',
        'ns.google.com': 'Google Cloud DNS',
        'domaincontrol': 'GoDaddy',
        'registrar-servers': 'Namecheap',
        'dnsmadeeasy': 'DNS Made Easy',
        'ultradns': 'UltraDNS',
        'nsone': 'NS1',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not DNS_AVAILABLE:
            raise ImportError(
                "dnspython is required for DNSRecordsExtractor. "
                "Install with: pip install dnspython"
            )
        super().__init__(config)
        self._resolver = dns.resolver.Resolver()
        if config and config.get('dns_resolver'):
            self._resolver.nameservers = [config['dns_resolver']]
        self._resolver.timeout = config.get('timeout', 5) if config else 5
        self._resolver.lifetime = config.get('timeout', 10) if config else 10

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract DNS records for a domain."""
        domain = self._normalize_domain(entity_id)

        # Query all record types
        a_records = self._query_a(domain)
        aaaa_records = self._query_aaaa(domain)
        mx_records = self._query_mx(domain)
        ns_records = self._query_ns(domain)
        cname_records = self._query_cname(domain)
        txt_records = self._query_txt(domain)

        # Analyze infrastructure
        infrastructure = self._analyze_infrastructure(
            a_records, mx_records, ns_records, cname_records
        )

        data = {
            'domain': domain,
            'a_records': a_records,
            'aaaa_records': aaaa_records,
            'mx_records': mx_records,
            'ns_records': ns_records,
            'cname_records': cname_records,
            'txt_records': txt_records,
            'infrastructure': infrastructure,
            'ipv6_enabled': len(aaaa_records) > 0,
            'record_counts': {
                'a': len(a_records),
                'aaaa': len(aaaa_records),
                'mx': len(mx_records),
                'ns': len(ns_records),
                'cname': len(cname_records),
                'txt': len(txt_records),
            },
        }

        return self._create_success_result(data, confidence=0.95)

    def _query_a(self, domain: str) -> List[Dict[str, Any]]:
        """Query A records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'A')
            for rdata in answers:
                ip = str(rdata)
                records.append({
                    'ip': ip,
                    'provider': self._identify_ip_provider(ip),
                })
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _query_aaaa(self, domain: str) -> List[Dict[str, Any]]:
        """Query AAAA records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                ip = str(rdata)
                records.append({'ip': ip})
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _query_mx(self, domain: str) -> List[Dict[str, Any]]:
        """Query MX records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'MX')
            for rdata in answers:
                host = str(rdata.exchange).rstrip('.')
                records.append({
                    'host': host,
                    'priority': rdata.preference,
                    'provider': self._identify_email_provider(host),
                })
            # Sort by priority
            records.sort(key=lambda x: x['priority'])
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _query_ns(self, domain: str) -> List[Dict[str, Any]]:
        """Query NS records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'NS')
            for rdata in answers:
                host = str(rdata).rstrip('.')
                records.append({
                    'host': host,
                    'provider': self._identify_dns_provider(host),
                })
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _query_cname(self, domain: str) -> List[Dict[str, Any]]:
        """Query CNAME records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                target = str(rdata).rstrip('.')
                records.append({
                    'target': target,
                    'provider': self._identify_cname_provider(target),
                })
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _query_txt(self, domain: str) -> List[Dict[str, Any]]:
        """Query TXT records."""
        records = []
        try:
            answers = self._resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt = str(rdata).strip('"')
                record_type = self._classify_txt_record(txt)
                records.append({
                    'value': txt[:500],  # Truncate long records
                    'type': record_type,
                })
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
            pass
        return records

    def _identify_ip_provider(self, ip: str) -> Optional[str]:
        """Try to identify the hosting provider from an IP."""
        # This is a simplified version - production would use IP databases
        # For now, return None (would need MaxMind or similar)
        return None

    def _identify_email_provider(self, host: str) -> Optional[str]:
        """Identify email provider from MX host."""
        host_lower = host.lower()
        for pattern, provider in self.EMAIL_PROVIDERS.items():
            if pattern in host_lower:
                return provider
        return None

    def _identify_dns_provider(self, host: str) -> Optional[str]:
        """Identify DNS provider from NS host."""
        host_lower = host.lower()
        for pattern, provider in self.DNS_PROVIDERS.items():
            if pattern in host_lower:
                return provider
        return None

    def _identify_cname_provider(self, target: str) -> Optional[str]:
        """Identify CDN/hosting provider from CNAME target."""
        target_lower = target.lower()
        for pattern, provider in self.HOSTING_PROVIDERS.items():
            if pattern in target_lower:
                return provider
        return None

    def _classify_txt_record(self, txt: str) -> str:
        """Classify the type of TXT record."""
        if txt.startswith('v=spf1'):
            return 'spf'
        elif txt.startswith('v=DMARC1'):
            return 'dmarc'
        elif txt.startswith('v=DKIM1') or 'DKIM' in txt.upper():
            return 'dkim'
        elif 'google-site-verification' in txt:
            return 'google_verification'
        elif 'ms=' in txt or 'MS=' in txt:
            return 'microsoft_verification'
        elif 'facebook-domain-verification' in txt:
            return 'facebook_verification'
        elif 'apple-domain-verification' in txt:
            return 'apple_verification'
        elif 'docusign' in txt.lower():
            return 'docusign'
        elif 'atlassian' in txt.lower():
            return 'atlassian_verification'
        elif txt.startswith('ca3-'):
            return 'caa'
        else:
            return 'other'

    def _analyze_infrastructure(
        self,
        a_records: List[Dict],
        mx_records: List[Dict],
        ns_records: List[Dict],
        cname_records: List[Dict],
    ) -> Dict[str, Any]:
        """Analyze DNS records to determine infrastructure providers."""
        infrastructure = {
            'hosting_provider': None,
            'cdn_provider': None,
            'email_provider': None,
            'dns_provider': None,
        }

        # Email provider (from MX records)
        if mx_records:
            providers = [r.get('provider') for r in mx_records if r.get('provider')]
            if providers:
                infrastructure['email_provider'] = providers[0]

        # DNS provider (from NS records)
        if ns_records:
            providers = [r.get('provider') for r in ns_records if r.get('provider')]
            if providers:
                infrastructure['dns_provider'] = providers[0]

        # CDN/Hosting (from CNAME records)
        if cname_records:
            providers = [r.get('provider') for r in cname_records if r.get('provider')]
            if providers:
                # Check if it's a CDN vs hosting
                cdn_keywords = ['cloudflare', 'fastly', 'akamai', 'cloudfront', 'edgecast']
                provider = providers[0]
                if any(kw in provider.lower() for kw in cdn_keywords):
                    infrastructure['cdn_provider'] = provider
                else:
                    infrastructure['hosting_provider'] = provider

        return infrastructure
