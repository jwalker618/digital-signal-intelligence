"""
DSI Production Extractor - CDN Usage Detection

Detects Content Delivery Network (CDN) usage by analyzing DNS CNAME records
and HTTP response headers.

This is a FREE extractor - uses DNS queries and HTTP requests.

CDN Providers Detected:
    - Cloudflare
    - Akamai
    - Fastly
    - CloudFront (AWS)
    - Azure CDN
    - Google Cloud CDN
    - Bunny CDN
    - KeyCDN
    - StackPath
    - Imperva/Incapsula
    - Sucuri
    - Limelight

Scoring Implications:
    - CDN present = Positive (performance, DDoS protection)
    - Enterprise CDN (Akamai, Cloudflare Enterprise) = Very positive
    - No CDN = May indicate smaller scale or self-hosted
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


# CDN detection patterns - CNAME suffixes and header signatures
CDN_SIGNATURES = {
    'cloudflare': {
        'cname_patterns': [
            r'\.cloudflare\.net$',
            r'\.cloudflare\.com$',
            r'\.cloudflaressl\.com$',
        ],
        'header_patterns': {
            'server': [r'^cloudflare$'],
            'cf-ray': [r'.+'],
            'cf-cache-status': [r'.+'],
        },
        'tier': 'enterprise',
    },
    'akamai': {
        'cname_patterns': [
            r'\.akamai\.net$',
            r'\.akamaiedge\.net$',
            r'\.akamaihd\.net$',
            r'\.akamaitech\.net$',
            r'\.edgesuite\.net$',
            r'\.edgekey\.net$',
        ],
        'header_patterns': {
            'x-akamai-transformed': [r'.+'],
            'x-akamai-request-id': [r'.+'],
            'server': [r'.*akamai.*'],
        },
        'tier': 'enterprise',
    },
    'fastly': {
        'cname_patterns': [
            r'\.fastly\.net$',
            r'\.fastlylb\.net$',
            r'\.global\.prod\.fastly\.net$',
        ],
        'header_patterns': {
            'x-served-by': [r'cache-'],
            'x-fastly-request-id': [r'.+'],
            'via': [r'.*varnish.*'],
            'x-cache': [r'.+'],
        },
        'tier': 'enterprise',
    },
    'cloudfront': {
        'cname_patterns': [
            r'\.cloudfront\.net$',
        ],
        'header_patterns': {
            'x-amz-cf-id': [r'.+'],
            'x-amz-cf-pop': [r'.+'],
            'via': [r'.*cloudfront.*'],
            'x-cache': [r'.+(cloudfront|hit|miss).*'],
        },
        'tier': 'enterprise',
    },
    'azure_cdn': {
        'cname_patterns': [
            r'\.azureedge\.net$',
            r'\.azurefd\.net$',
            r'\.trafficmanager\.net$',
            r'\.vo\.msecnd\.net$',
        ],
        'header_patterns': {
            'x-ms-request-id': [r'.+'],
            'x-azure-ref': [r'.+'],
        },
        'tier': 'enterprise',
    },
    'google_cdn': {
        'cname_patterns': [
            r'\.googleapis\.com$',
            r'\.googlevideo\.com$',
            r'\.googleusercontent\.com$',
            r'\.gstatic\.com$',
        ],
        'header_patterns': {
            'x-goog-': [r'.+'],
            'via': [r'.*google.*'],
        },
        'tier': 'enterprise',
    },
    'bunny_cdn': {
        'cname_patterns': [
            r'\.b-cdn\.net$',
            r'\.bunny\.net$',
            r'\.bunnycdn\.com$',
        ],
        'header_patterns': {
            'server': [r'bunny.*'],
            'cdn-pullzone': [r'.+'],
            'cdn-uid': [r'.+'],
        },
        'tier': 'standard',
    },
    'keycdn': {
        'cname_patterns': [
            r'\.kxcdn\.com$',
            r'\.keycdn\.com$',
        ],
        'header_patterns': {
            'server': [r'keycdn.*'],
            'x-edge-location': [r'.+'],
        },
        'tier': 'standard',
    },
    'stackpath': {
        'cname_patterns': [
            r'\.stackpathdns\.com$',
            r'\.stackpathcdn\.com$',
            r'\.hwcdn\.net$',  # Highwinds (now StackPath)
        ],
        'header_patterns': {
            'x-hw': [r'.+'],
            'x-sp-': [r'.+'],
        },
        'tier': 'enterprise',
    },
    'imperva': {
        'cname_patterns': [
            r'\.incapdns\.net$',
            r'\.impervadns\.net$',
        ],
        'header_patterns': {
            'x-iinfo': [r'.+'],
            'x-cdn': [r'.*imperva.*|.*incapsula.*'],
        },
        'tier': 'enterprise',
    },
    'sucuri': {
        'cname_patterns': [
            r'\.sucuri\.net$',
            r'\.sucuridns\.com$',
        ],
        'header_patterns': {
            'x-sucuri-id': [r'.+'],
            'server': [r'.*sucuri.*'],
        },
        'tier': 'standard',
    },
    'limelight': {
        'cname_patterns': [
            r'\.llnwd\.net$',
            r'\.llnw\.net$',
            r'\.limelight\.com$',
        ],
        'header_patterns': {
            'x-limelight-': [r'.+'],
        },
        'tier': 'enterprise',
    },
    'jsdelivr': {
        'cname_patterns': [
            r'\.jsdelivr\.net$',
        ],
        'header_patterns': {
            'x-jsd-': [r'.+'],
        },
        'tier': 'free',
    },
    'unpkg': {
        'cname_patterns': [
            r'\.unpkg\.com$',
        ],
        'header_patterns': {},
        'tier': 'free',
    },
}


class CDNUsageExtractor(ProductionExtractor):
    """
    Detects CDN usage from DNS CNAME records and HTTP headers.

    Output:
        {
            'domain': str,
            'cdn_detected': bool,
            'providers': [
                {
                    'name': str,
                    'tier': str,  # 'enterprise', 'standard', 'free'
                    'detection_method': str,  # 'cname' or 'header'
                    'evidence': str,
                }
            ],
            'cname_chain': [...],
            'primary_cdn': str,
        }
    """

    SOURCE_NAME = "cdn_usage"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 3.0
    COST_TIER = "free"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not DNS_AVAILABLE:
            raise ImportError(
                "dnspython is required for CDNUsageExtractor. "
                "Install with: pip install dnspython"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 10) if config else 10
        self._check_headers = config.get('check_headers', True) if config else True

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Detect CDN usage for a domain."""
        domain = entity_id.strip().lower()

        if not domain:
            return self._create_error_result("Empty domain provided")

        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = domain.split('://', 1)[1].split('/')[0]

        providers_found = []
        cname_chain = []

        # Check CNAME chain
        try:
            cname_chain = self._get_cname_chain(domain)
            for cname in cname_chain:
                for cdn_name, signatures in CDN_SIGNATURES.items():
                    for pattern in signatures['cname_patterns']:
                        if re.search(pattern, cname, re.IGNORECASE):
                            providers_found.append({
                                'name': cdn_name,
                                'tier': signatures['tier'],
                                'detection_method': 'cname',
                                'evidence': cname,
                            })
                            break
        except Exception as e:
            logger.debug(f"CNAME lookup failed for {domain}: {e}")

        # Check HTTP headers if enabled
        if self._check_headers and REQUESTS_AVAILABLE:
            try:
                header_detections = self._check_http_headers(domain)
                providers_found.extend(header_detections)
            except Exception as e:
                logger.debug(f"HTTP header check failed for {domain}: {e}")

        # Deduplicate providers
        seen = set()
        unique_providers = []
        for p in providers_found:
            if p['name'] not in seen:
                seen.add(p['name'])
                unique_providers.append(p)

        # Determine primary CDN (prefer CNAME detection, then enterprise tier)
        primary_cdn = None
        if unique_providers:
            # Prefer CNAME detection
            cname_detected = [p for p in unique_providers if p['detection_method'] == 'cname']
            if cname_detected:
                # Prefer enterprise tier
                enterprise = [p for p in cname_detected if p['tier'] == 'enterprise']
                primary_cdn = enterprise[0]['name'] if enterprise else cname_detected[0]['name']
            else:
                enterprise = [p for p in unique_providers if p['tier'] == 'enterprise']
                primary_cdn = enterprise[0]['name'] if enterprise else unique_providers[0]['name']

        data = {
            'domain': domain,
            'cdn_detected': len(unique_providers) > 0,
            'provider_count': len(unique_providers),
            'providers': unique_providers,
            'cname_chain': cname_chain,
            'primary_cdn': primary_cdn,
            'has_enterprise_cdn': any(p['tier'] == 'enterprise' for p in unique_providers),
        }

        confidence = 0.95 if unique_providers else 0.70
        return self._create_success_result(data, confidence=confidence)

    def _get_cname_chain(self, domain: str, max_depth: int = 10) -> List[str]:
        """Follow CNAME chain and return all CNAMEs."""
        chain = []
        current = domain
        seen = set()

        resolver = dns.resolver.Resolver()
        resolver.timeout = self._timeout
        resolver.lifetime = self._timeout

        for _ in range(max_depth):
            if current in seen:
                break  # Avoid loops
            seen.add(current)

            try:
                answers = resolver.resolve(current, 'CNAME')
                for rdata in answers:
                    cname = str(rdata.target).rstrip('.')
                    chain.append(cname)
                    current = cname
                    break
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                break
            except Exception:
                break

        return chain

    def _check_http_headers(self, domain: str) -> List[Dict[str, Any]]:
        """Check HTTP response headers for CDN signatures."""
        detections = []

        try:
            # Try HTTPS first, then HTTP
            for protocol in ['https', 'http']:
                try:
                    response = requests.head(
                        f"{protocol}://{domain}",
                        timeout=self._timeout,
                        allow_redirects=True,
                        headers={'User-Agent': 'DSI-Framework/1.0 (cdn-detection)'},
                    )

                    headers = {k.lower(): v for k, v in response.headers.items()}

                    for cdn_name, signatures in CDN_SIGNATURES.items():
                        for header_name, patterns in signatures.get('header_patterns', {}).items():
                            header_name_lower = header_name.lower()

                            # Check exact header match
                            if header_name_lower in headers:
                                for pattern in patterns:
                                    if re.search(pattern, headers[header_name_lower], re.IGNORECASE):
                                        detections.append({
                                            'name': cdn_name,
                                            'tier': signatures['tier'],
                                            'detection_method': 'header',
                                            'evidence': f"{header_name}: {headers[header_name_lower][:100]}",
                                        })
                                        break
                            else:
                                # Check for prefix match (e.g., 'x-goog-' matches 'x-goog-hash')
                                if header_name_lower.endswith('-'):
                                    for h in headers:
                                        if h.startswith(header_name_lower):
                                            detections.append({
                                                'name': cdn_name,
                                                'tier': signatures['tier'],
                                                'detection_method': 'header',
                                                'evidence': f"{h}: {headers[h][:100]}",
                                            })
                                            break

                    if response.status_code < 400:
                        break  # Success, don't try HTTP

                except requests.exceptions.SSLError:
                    continue
                except requests.exceptions.RequestException:
                    continue

        except Exception as e:
            logger.debug(f"Header check error for {domain}: {e}")

        return detections
