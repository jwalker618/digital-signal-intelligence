"""
DSI Production Extractor - NIST NVD CVE Database

Queries the NIST National Vulnerability Database (NVD) for CVE data.
This is a FREE extractor - NVD is a public database.

NVD API 2.0:
    - No API key required (rate limited to 5 req/30s)
    - With API key: 50 req/30s
    - Comprehensive CVE data since 1999

Search Capabilities:
    - By product/vendor name (CPE match)
    - By keyword
    - By CVE ID
    - By severity (CVSS score range)

API Documentation:
    https://nvd.nist.gov/developers/vulnerabilities

Scoring Implications:
    - Critical CVEs (CVSS 9.0+) = Major concern
    - High CVEs (CVSS 7.0-8.9) = Significant concern
    - Many unpatched vulnerabilities = Negative signal
"""

import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class NVDCVEExtractor(ProductionExtractor):
    """
    Searches NVD for vulnerabilities affecting a product/vendor.

    Uses the NVD API 2.0 to search for CVEs by keyword or CPE.

    Output:
        {
            'search_term': str,
            'total_results': int,
            'vulnerabilities': [
                {
                    'cve_id': str,
                    'description': str,
                    'severity': str,
                    'cvss_score': float,
                    'cvss_version': str,
                    'published': str,
                    'modified': str,
                    'exploited': bool,
                    'references': [...],
                }
            ],
            'severity_counts': {
                'critical': int,
                'high': int,
                'medium': int,
                'low': int,
            },
            'recent_count': int,  # Last 90 days
            'risk_score': float,  # Calculated risk score 0-100
        }
    """

    SOURCE_NAME = "nvd_cve"
    SOURCE_VERSION = "2.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 0.17  # ~5 requests per 30 seconds without API key
    COST_TIER = "free"

    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for NVDCVEExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._api_key = config.get('nvd_api_key') if config else None
        self._max_results = config.get('max_results', 100) if config else 100

        # If API key provided, use higher rate limit
        if self._api_key:
            self.RATE_LIMIT = 0.6  # ~50 req/30s with API key

    def get_required_config(self) -> List[str]:
        return []  # API key is optional

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search NVD for vulnerabilities."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine search type
        is_cve_id = bool(re.match(r'^CVE-\d{4}-\d+$', search_term, re.IGNORECASE))

        try:
            if is_cve_id:
                vulnerabilities = self._search_by_cve_id(search_term.upper())
            else:
                vulnerabilities = self._search_by_keyword(search_term, **kwargs)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"NVD API error: {e}")

        if not vulnerabilities:
            return self._create_success_result({
                'search_term': search_term,
                'search_type': 'cve_id' if is_cve_id else 'keyword',
                'total_results': 0,
                'vulnerabilities': [],
                'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                'recent_count': 0,
                'risk_score': 0.0,
            })

        # Calculate severity counts
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        recent_cutoff = datetime.utcnow() - timedelta(days=90)
        recent_count = 0

        for vuln in vulnerabilities:
            severity = vuln.get('severity', '').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

            # Check if recent
            published = vuln.get('published')
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    if pub_date.replace(tzinfo=None) > recent_cutoff:
                        recent_count += 1
                except ValueError:
                    pass

        # Calculate risk score
        risk_score = self._calculate_risk_score(vulnerabilities, severity_counts)

        data = {
            'search_term': search_term,
            'search_type': 'cve_id' if is_cve_id else 'keyword',
            'total_results': len(vulnerabilities),
            'vulnerabilities': vulnerabilities[:50],  # Limit response size
            'severity_counts': severity_counts,
            'recent_count': recent_count,
            'risk_score': round(risk_score, 1),
            'has_critical': severity_counts['critical'] > 0,
            'has_exploited': any(v.get('exploited') for v in vulnerabilities),
        }

        return self._create_success_result(data, confidence=0.95)

    def _search_by_cve_id(self, cve_id: str) -> List[Dict[str, Any]]:
        """Search for a specific CVE by ID."""
        params = {'cveId': cve_id}
        return self._make_nvd_request(params)

    def _search_by_keyword(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """Search for CVEs by keyword."""
        params = {
            'keywordSearch': keyword,
            'resultsPerPage': min(self._max_results, 2000),
        }

        # Optional filters
        if kwargs.get('severity'):
            severity_map = {
                'critical': 'CRITICAL',
                'high': 'HIGH',
                'medium': 'MEDIUM',
                'low': 'LOW',
            }
            params['cvssV3Severity'] = severity_map.get(kwargs['severity'].lower())

        if kwargs.get('start_date'):
            params['pubStartDate'] = kwargs['start_date']

        if kwargs.get('end_date'):
            params['pubEndDate'] = kwargs['end_date']

        return self._make_nvd_request(params)

    def _make_nvd_request(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make request to NVD API."""
        headers = {
            'User-Agent': 'DSI-Framework/1.0 (vulnerability-research)',
        }

        if self._api_key:
            headers['apiKey'] = self._api_key

        response = requests.get(
            self.NVD_API_URL,
            params=params,
            headers=headers,
            timeout=self._timeout,
        )
        response.raise_for_status()

        data = response.json()
        vulnerabilities = []

        for item in data.get('vulnerabilities', []):
            cve = item.get('cve', {})
            parsed = self._parse_cve(cve)
            if parsed:
                vulnerabilities.append(parsed)

        return vulnerabilities

    def _parse_cve(self, cve: Dict) -> Optional[Dict[str, Any]]:
        """Parse a CVE entry from NVD API response."""
        cve_id = cve.get('id')
        if not cve_id:
            return None

        # Get description (prefer English)
        descriptions = cve.get('descriptions', [])
        description = ''
        for desc in descriptions:
            if desc.get('lang') == 'en':
                description = desc.get('value', '')
                break
        if not description and descriptions:
            description = descriptions[0].get('value', '')

        # Get CVSS score (prefer v3.1, then v3.0, then v2)
        metrics = cve.get('metrics', {})
        cvss_score = None
        cvss_version = None
        severity = 'unknown'

        # Try CVSS 3.1
        cvss31 = metrics.get('cvssMetricV31', [])
        if cvss31:
            cvss_data = cvss31[0].get('cvssData', {})
            cvss_score = cvss_data.get('baseScore')
            cvss_version = '3.1'
            severity = cvss_data.get('baseSeverity', '').lower()

        # Try CVSS 3.0
        if cvss_score is None:
            cvss30 = metrics.get('cvssMetricV30', [])
            if cvss30:
                cvss_data = cvss30[0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_version = '3.0'
                severity = cvss_data.get('baseSeverity', '').lower()

        # Try CVSS 2.0
        if cvss_score is None:
            cvss2 = metrics.get('cvssMetricV2', [])
            if cvss2:
                cvss_data = cvss2[0].get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_version = '2.0'
                # Map v2 score to severity
                if cvss_score:
                    if cvss_score >= 9.0:
                        severity = 'critical'
                    elif cvss_score >= 7.0:
                        severity = 'high'
                    elif cvss_score >= 4.0:
                        severity = 'medium'
                    else:
                        severity = 'low'

        # Get dates
        published = cve.get('published', '')
        modified = cve.get('lastModified', '')

        # Check for known exploited (CISA KEV)
        exploited = False
        vulnStatus = cve.get('vulnStatus', '')
        if 'Undergoing Analysis' in vulnStatus or 'Awaiting Analysis' in vulnStatus:
            pass  # Not yet analyzed

        # Check references for exploit indicators
        references = []
        for ref in cve.get('references', [])[:10]:
            url = ref.get('url', '')
            tags = ref.get('tags', [])
            references.append({
                'url': url,
                'tags': tags,
            })
            if 'Exploit' in tags:
                exploited = True

        # Get affected products (CPE)
        affected_products = []
        configurations = cve.get('configurations', [])
        for config in configurations[:5]:
            for node in config.get('nodes', []):
                for cpe_match in node.get('cpeMatch', []):
                    if cpe_match.get('vulnerable'):
                        criteria = cpe_match.get('criteria', '')
                        # Parse CPE string: cpe:2.3:a:vendor:product:version:...
                        parts = criteria.split(':')
                        if len(parts) >= 5:
                            affected_products.append({
                                'vendor': parts[3],
                                'product': parts[4],
                                'version': parts[5] if len(parts) > 5 else '*',
                            })

        # Get weaknesses (CWE)
        weaknesses = []
        for weakness in cve.get('weaknesses', []):
            for desc in weakness.get('description', []):
                if desc.get('lang') == 'en':
                    weaknesses.append(desc.get('value', ''))

        return {
            'cve_id': cve_id,
            'description': description[:500],  # Truncate
            'severity': severity,
            'cvss_score': cvss_score,
            'cvss_version': cvss_version,
            'published': published,
            'modified': modified,
            'exploited': exploited,
            'status': vulnStatus,
            'affected_products': affected_products[:10],
            'weaknesses': weaknesses[:5],
            'references': references,
        }

    def _calculate_risk_score(
        self,
        vulnerabilities: List[Dict],
        severity_counts: Dict[str, int]
    ) -> float:
        """Calculate aggregate risk score from vulnerabilities."""
        if not vulnerabilities:
            return 0.0

        score = 0.0

        # Weight by severity
        score += severity_counts.get('critical', 0) * 10
        score += severity_counts.get('high', 0) * 5
        score += severity_counts.get('medium', 0) * 2
        score += severity_counts.get('low', 0) * 0.5

        # Bonus for exploited vulnerabilities
        exploited_count = sum(1 for v in vulnerabilities if v.get('exploited'))
        score += exploited_count * 15

        # Cap at 100
        return min(100.0, score)
