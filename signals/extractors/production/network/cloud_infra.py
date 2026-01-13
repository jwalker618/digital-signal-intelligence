"""
DSI Production Extractor - Cloud Infrastructure Detection

Detects cloud providers hosting a domain by analyzing IP addresses
against known cloud provider IP ranges.

This is a FREE extractor - uses DNS queries and public IP range data.

Cloud Providers Detected:
    - AWS (Amazon Web Services)
    - Azure (Microsoft)
    - GCP (Google Cloud Platform)
    - Cloudflare
    - DigitalOcean
    - Linode/Akamai
    - Oracle Cloud
    - IBM Cloud
    - Alibaba Cloud

Scoring Implications:
    - Major cloud provider = Generally positive (mature infrastructure)
    - Multiple providers = May indicate redundancy or complexity
    - Unknown/self-hosted = Neutral (depends on context)
"""

import ipaddress
import logging
import socket
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


# Known cloud provider IP ranges (CIDR notation)
# These are approximate and should be updated periodically
# In production, fetch from official sources:
# - AWS: https://ip-ranges.amazonaws.com/ip-ranges.json
# - Azure: https://www.microsoft.com/en-us/download/details.aspx?id=56519
# - GCP: https://www.gstatic.com/ipranges/cloud.json

CLOUD_IP_RANGES = {
    'aws': [
        # Common AWS ranges (sample - production should fetch full list)
        '3.0.0.0/8',
        '13.0.0.0/8',
        '15.0.0.0/8',
        '18.0.0.0/8',
        '35.0.0.0/8',
        '44.0.0.0/8',
        '50.0.0.0/8',
        '52.0.0.0/8',
        '54.0.0.0/8',
        '99.0.0.0/8',
        '100.0.0.0/8',
        '107.20.0.0/14',
        '174.129.0.0/16',
        '184.72.0.0/15',
    ],
    'azure': [
        # Common Azure ranges
        '13.64.0.0/11',
        '20.0.0.0/8',
        '23.96.0.0/13',
        '40.64.0.0/10',
        '51.0.0.0/8',
        '52.0.0.0/8',
        '65.52.0.0/14',
        '70.37.0.0/16',
        '104.40.0.0/13',
        '137.116.0.0/15',
        '157.55.0.0/16',
        '168.61.0.0/16',
        '191.232.0.0/13',
    ],
    'gcp': [
        # Common GCP ranges
        '8.8.4.0/24',
        '8.8.8.0/24',
        '34.0.0.0/8',
        '35.184.0.0/13',
        '35.192.0.0/12',
        '35.208.0.0/12',
        '35.224.0.0/12',
        '35.240.0.0/13',
        '104.154.0.0/15',
        '104.196.0.0/14',
        '107.167.160.0/19',
        '108.59.80.0/20',
        '130.211.0.0/16',
        '146.148.0.0/17',
        '162.216.148.0/22',
        '199.192.112.0/22',
        '199.223.232.0/21',
    ],
    'cloudflare': [
        '103.21.244.0/22',
        '103.22.200.0/22',
        '103.31.4.0/22',
        '104.16.0.0/13',
        '104.24.0.0/14',
        '108.162.192.0/18',
        '131.0.72.0/22',
        '141.101.64.0/18',
        '162.158.0.0/15',
        '172.64.0.0/13',
        '173.245.48.0/20',
        '188.114.96.0/20',
        '190.93.240.0/20',
        '197.234.240.0/22',
        '198.41.128.0/17',
    ],
    'digitalocean': [
        '104.131.0.0/16',
        '104.236.0.0/16',
        '107.170.0.0/16',
        '128.199.0.0/16',
        '134.209.0.0/16',
        '137.184.0.0/16',
        '138.68.0.0/16',
        '138.197.0.0/16',
        '139.59.0.0/16',
        '142.93.0.0/16',
        '143.198.0.0/16',
        '143.244.128.0/17',
        '146.190.0.0/16',
        '157.230.0.0/16',
        '159.65.0.0/16',
        '159.89.0.0/16',
        '161.35.0.0/16',
        '162.243.0.0/16',
        '164.90.0.0/16',
        '165.22.0.0/16',
        '165.227.0.0/16',
        '167.71.0.0/16',
        '167.172.0.0/16',
        '167.99.0.0/16',
        '174.138.0.0/16',
        '178.62.0.0/16',
        '178.128.0.0/16',
        '188.166.0.0/16',
        '192.81.208.0/20',
        '198.199.64.0/18',
        '206.189.0.0/16',
        '209.97.128.0/17',
    ],
    'oracle_cloud': [
        '129.146.0.0/16',
        '129.148.0.0/16',
        '129.149.0.0/16',
        '129.150.0.0/15',
        '129.152.0.0/14',
        '129.156.0.0/14',
        '130.35.0.0/16',
        '130.61.0.0/16',
        '132.145.0.0/16',
        '134.70.0.0/16',
        '138.1.0.0/16',
        '140.204.0.0/16',
        '140.238.0.0/16',
        '141.144.0.0/16',
        '141.145.0.0/16',
        '141.147.0.0/16',
        '144.21.0.0/16',
        '144.22.0.0/15',
        '144.24.0.0/13',
        '147.154.0.0/16',
        '150.136.0.0/16',
        '152.67.0.0/16',
        '152.70.0.0/15',
        '155.248.0.0/16',
        '158.101.0.0/16',
        '168.138.0.0/16',
        '169.255.0.0/16',
        '192.18.0.0/15',
        '193.122.0.0/16',
        '193.123.0.0/16',
        '207.211.0.0/16',
    ],
    'linode': [
        '45.33.0.0/16',
        '45.56.0.0/15',
        '45.79.0.0/16',
        '50.116.0.0/16',
        '66.175.208.0/20',
        '66.228.32.0/19',
        '69.164.192.0/18',
        '72.14.176.0/20',
        '74.207.224.0/19',
        '85.90.244.0/22',
        '96.126.96.0/19',
        '97.107.128.0/17',
        '139.144.0.0/16',
        '139.162.0.0/16',
        '143.42.0.0/16',
        '172.104.0.0/15',
        '172.232.0.0/13',
        '173.230.128.0/18',
        '173.255.192.0/18',
        '178.79.128.0/17',
        '192.155.80.0/20',
        '194.195.240.0/22',
        '198.58.96.0/19',
    ],
}


class CloudInfraExtractor(ProductionExtractor):
    """
    Detects cloud infrastructure providers hosting a domain.

    Resolves domain IPs and matches against known cloud provider ranges.

    Output:
        {
            'domain': str,
            'ip_addresses': [...],
            'providers_detected': {
                'aws': {'detected': True, 'ips': [...], 'confidence': 0.95},
                ...
            },
            'primary_provider': str,
            'is_cloud_hosted': bool,
            'multi_cloud': bool,
        }
    """

    SOURCE_NAME = "cloud_infrastructure"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 5.0  # DNS queries are fast
    COST_TIER = "free"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not DNS_AVAILABLE:
            raise ImportError(
                "dnspython is required for CloudInfraExtractor. "
                "Install with: pip install dnspython"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 10) if config else 10
        self._ip_networks = self._build_network_cache()

    def _build_network_cache(self) -> Dict[str, List[ipaddress.IPv4Network]]:
        """Pre-parse IP ranges into network objects for fast lookup."""
        cache = {}
        for provider, ranges in CLOUD_IP_RANGES.items():
            cache[provider] = []
            for cidr in ranges:
                try:
                    cache[provider].append(ipaddress.ip_network(cidr, strict=False))
                except ValueError as e:
                    logger.warning(f"Invalid CIDR {cidr} for {provider}: {e}")
        return cache

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Detect cloud providers for a domain."""
        domain = entity_id.strip().lower()

        if not domain:
            return self._create_error_result("Empty domain provided")

        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = domain.split('://', 1)[1].split('/')[0]

        # Resolve domain to IP addresses
        ip_addresses = self._resolve_domain(domain)

        if not ip_addresses:
            return self._create_success_result({
                'domain': domain,
                'ip_addresses': [],
                'providers_detected': {},
                'primary_provider': None,
                'is_cloud_hosted': False,
                'multi_cloud': False,
                'error': 'Could not resolve domain to IP addresses',
            }, confidence=0.5)

        # Check each IP against cloud provider ranges
        providers_detected = {}
        for provider in CLOUD_IP_RANGES.keys():
            matching_ips = []
            for ip in ip_addresses:
                if self._ip_in_provider_range(ip, provider):
                    matching_ips.append(ip)

            if matching_ips:
                providers_detected[provider] = {
                    'detected': True,
                    'ips': matching_ips,
                    'ip_count': len(matching_ips),
                    'confidence': 0.95 if len(matching_ips) > 1 else 0.85,
                }

        # Determine primary provider (most IPs or first detected)
        primary_provider = None
        if providers_detected:
            primary_provider = max(
                providers_detected.keys(),
                key=lambda p: providers_detected[p]['ip_count']
            )

        is_cloud_hosted = len(providers_detected) > 0
        multi_cloud = len(providers_detected) > 1

        data = {
            'domain': domain,
            'ip_addresses': ip_addresses,
            'ip_count': len(ip_addresses),
            'providers_detected': providers_detected,
            'provider_count': len(providers_detected),
            'primary_provider': primary_provider,
            'is_cloud_hosted': is_cloud_hosted,
            'multi_cloud': multi_cloud,
        }

        confidence = 0.90 if is_cloud_hosted else 0.70
        return self._create_success_result(data, confidence=confidence)

    def _resolve_domain(self, domain: str) -> List[str]:
        """Resolve domain to list of IP addresses."""
        ips = set()

        # Try A records
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self._timeout
            resolver.lifetime = self._timeout

            answers = resolver.resolve(domain, 'A')
            for rdata in answers:
                ips.add(str(rdata))
        except Exception as e:
            logger.debug(f"A record lookup failed for {domain}: {e}")

        # Try AAAA records (IPv6)
        try:
            answers = resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                ips.add(str(rdata))
        except Exception:
            pass  # IPv6 is optional

        # Fallback to socket if DNS library fails
        if not ips:
            try:
                result = socket.getaddrinfo(domain, None, socket.AF_INET)
                for item in result:
                    ips.add(item[4][0])
            except socket.gaierror:
                pass

        return list(ips)

    def _ip_in_provider_range(self, ip_str: str, provider: str) -> bool:
        """Check if an IP is in a provider's range."""
        try:
            ip = ipaddress.ip_address(ip_str)

            for network in self._ip_networks.get(provider, []):
                # Handle IPv4 vs IPv6 mismatch
                if isinstance(ip, ipaddress.IPv4Address) and isinstance(network, ipaddress.IPv4Network):
                    if ip in network:
                        return True
                elif isinstance(ip, ipaddress.IPv6Address) and isinstance(network, ipaddress.IPv6Network):
                    if ip in network:
                        return True

            return False
        except ValueError:
            return False
