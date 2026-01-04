"""
DSI Production Extractor - Security Headers

Analyzes HTTP security headers to assess web application security posture.
This is a FREE extractor - no API keys required.

Headers Checked:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection (deprecated but still checked)
    - Referrer-Policy
    - Permissions-Policy
    - Cross-Origin headers (CORP, COEP, COOP)

Scoring Implications:
    - All recommended headers present with strong values = Excellent
    - Most headers present = Good
    - Basic headers only = Moderate
    - Missing critical headers = Poor
"""

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class SecurityHeadersExtractor(ProductionExtractor):
    """
    Extracts and analyzes HTTP security headers.

    Makes an HTTP request to the target domain and analyzes the
    security-related headers in the response.

    Output:
        {
            'url': str,
            'status_code': int,
            'headers': {
                'strict_transport_security': {...},
                'content_security_policy': {...},
                'x_frame_options': {...},
                ...
            },
            'score': float,
            'grade': str,  # A+, A, B, C, D, F
            'issues': [...],
            'recommendations': [...],
        }
    """

    SOURCE_NAME = "http_security_headers"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 2.0  # Be gentle with target servers
    COST_TIER = "free"

    # Header weights for scoring
    HEADER_WEIGHTS = {
        'strict_transport_security': 0.20,
        'content_security_policy': 0.25,
        'x_frame_options': 0.10,
        'x_content_type_options': 0.10,
        'referrer_policy': 0.10,
        'permissions_policy': 0.10,
        'cross_origin_opener_policy': 0.05,
        'cross_origin_resource_policy': 0.05,
        'cross_origin_embedder_policy': 0.05,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SecurityHeadersExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 10) if config else 10
        self._user_agent = config.get(
            'user_agent',
            'DSI-SecurityScanner/1.0 (security research)'
        ) if config else 'DSI-SecurityScanner/1.0 (security research)'

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract security headers for a domain."""
        domain = self._normalize_domain(entity_id)
        url = f'https://{domain}'

        try:
            response = requests.get(
                url,
                timeout=self._timeout,
                headers={'User-Agent': self._user_agent},
                allow_redirects=True,
                verify=True,
            )

            headers = self._analyze_headers(response.headers)
            score, grade = self._calculate_score(headers)
            issues, recommendations = self._generate_recommendations(headers)

            data = {
                'domain': domain,
                'url': response.url,
                'status_code': response.status_code,
                'headers': headers,
                'score': score,
                'grade': grade,
                'issues': issues,
                'recommendations': recommendations,
                'server': response.headers.get('Server', 'Unknown'),
                'redirected': response.url != url,
            }

            return self._create_success_result(data, confidence=0.95)

        except requests.exceptions.SSLError as e:
            return self._create_error_result(f'SSL error: {e}')
        except requests.exceptions.ConnectionError as e:
            return self._create_error_result(f'Connection error: {e}')
        except requests.exceptions.Timeout:
            return self._create_error_result('Request timed out')
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f'Request error: {e}')

    def _analyze_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze all security-related headers."""
        result = {}

        # Strict-Transport-Security
        hsts = headers.get('Strict-Transport-Security')
        result['strict_transport_security'] = self._parse_hsts(hsts)

        # Content-Security-Policy
        csp = headers.get('Content-Security-Policy')
        result['content_security_policy'] = self._parse_csp(csp)

        # X-Frame-Options
        xfo = headers.get('X-Frame-Options')
        result['x_frame_options'] = self._parse_xfo(xfo)

        # X-Content-Type-Options
        xcto = headers.get('X-Content-Type-Options')
        result['x_content_type_options'] = {
            'present': xcto is not None,
            'value': xcto,
            'valid': xcto and xcto.lower() == 'nosniff',
        }

        # X-XSS-Protection (deprecated but still in use)
        xxss = headers.get('X-XSS-Protection')
        result['x_xss_protection'] = {
            'present': xxss is not None,
            'value': xxss,
            'note': 'Deprecated - CSP is preferred',
        }

        # Referrer-Policy
        rp = headers.get('Referrer-Policy')
        result['referrer_policy'] = self._parse_referrer_policy(rp)

        # Permissions-Policy (formerly Feature-Policy)
        pp = headers.get('Permissions-Policy') or headers.get('Feature-Policy')
        result['permissions_policy'] = {
            'present': pp is not None,
            'value': pp[:500] if pp else None,
            'is_feature_policy': 'Feature-Policy' in headers,
        }

        # Cross-Origin headers
        result['cross_origin_opener_policy'] = {
            'present': 'Cross-Origin-Opener-Policy' in headers,
            'value': headers.get('Cross-Origin-Opener-Policy'),
        }
        result['cross_origin_resource_policy'] = {
            'present': 'Cross-Origin-Resource-Policy' in headers,
            'value': headers.get('Cross-Origin-Resource-Policy'),
        }
        result['cross_origin_embedder_policy'] = {
            'present': 'Cross-Origin-Embedder-Policy' in headers,
            'value': headers.get('Cross-Origin-Embedder-Policy'),
        }

        return result

    def _parse_hsts(self, value: Optional[str]) -> Dict[str, Any]:
        """Parse Strict-Transport-Security header."""
        result = {
            'present': value is not None,
            'value': value,
            'max_age': None,
            'include_subdomains': False,
            'preload': False,
            'valid': False,
        }

        if not value:
            return result

        # Parse max-age
        max_age_match = re.search(r'max-age=(\d+)', value, re.IGNORECASE)
        if max_age_match:
            result['max_age'] = int(max_age_match.group(1))
            result['valid'] = True

        # Check for includeSubDomains
        result['include_subdomains'] = 'includesubdomains' in value.lower()

        # Check for preload
        result['preload'] = 'preload' in value.lower()

        return result

    def _parse_csp(self, value: Optional[str]) -> Dict[str, Any]:
        """Parse Content-Security-Policy header."""
        result = {
            'present': value is not None,
            'value': value[:1000] if value else None,  # Truncate long CSP
            'directives': {},
            'uses_nonces': False,
            'uses_hashes': False,
            'has_default_src': False,
            'has_script_src': False,
            'allows_unsafe_inline': False,
            'allows_unsafe_eval': False,
            'report_uri': None,
        }

        if not value:
            return result

        # Parse directives
        for directive in value.split(';'):
            directive = directive.strip()
            if not directive:
                continue
            parts = directive.split(None, 1)
            name = parts[0].lower()
            values = parts[1] if len(parts) > 1 else ''
            result['directives'][name] = values

        # Analyze CSP quality
        result['has_default_src'] = 'default-src' in result['directives']
        result['has_script_src'] = 'script-src' in result['directives']

        # Check for nonces and hashes
        csp_lower = value.lower()
        result['uses_nonces'] = "'nonce-" in csp_lower
        result['uses_hashes'] = any(h in csp_lower for h in ["'sha256-", "'sha384-", "'sha512-"])

        # Check for unsafe directives
        result['allows_unsafe_inline'] = "'unsafe-inline'" in csp_lower
        result['allows_unsafe_eval'] = "'unsafe-eval'" in csp_lower

        # Check for report-uri/report-to
        result['report_uri'] = result['directives'].get('report-uri') or result['directives'].get('report-to')

        return result

    def _parse_xfo(self, value: Optional[str]) -> Dict[str, Any]:
        """Parse X-Frame-Options header."""
        result = {
            'present': value is not None,
            'value': value,
            'valid': False,
            'policy': None,
        }

        if not value:
            return result

        value_upper = value.upper()
        if value_upper in ('DENY', 'SAMEORIGIN'):
            result['valid'] = True
            result['policy'] = value_upper
        elif value_upper.startswith('ALLOW-FROM'):
            result['valid'] = True
            result['policy'] = 'ALLOW-FROM'
            result['allowed_origin'] = value.split(None, 1)[1] if ' ' in value else None

        return result

    def _parse_referrer_policy(self, value: Optional[str]) -> Dict[str, Any]:
        """Parse Referrer-Policy header."""
        valid_policies = {
            'no-referrer',
            'no-referrer-when-downgrade',
            'origin',
            'origin-when-cross-origin',
            'same-origin',
            'strict-origin',
            'strict-origin-when-cross-origin',
            'unsafe-url',
        }

        result = {
            'present': value is not None,
            'value': value,
            'valid': False,
            'secure': False,
        }

        if not value:
            return result

        # Can have multiple policies (fallback)
        policies = [p.strip().lower() for p in value.split(',')]
        result['valid'] = any(p in valid_policies for p in policies)

        # Check if it's a secure policy
        secure_policies = {'no-referrer', 'same-origin', 'strict-origin', 'strict-origin-when-cross-origin'}
        result['secure'] = any(p in secure_policies for p in policies)

        return result

    def _calculate_score(self, headers: Dict[str, Any]) -> tuple:
        """Calculate overall security score and grade."""
        score = 0.0

        # HSTS
        hsts = headers.get('strict_transport_security', {})
        if hsts.get('present') and hsts.get('valid'):
            hsts_score = 0.10
            if hsts.get('max_age', 0) >= 31536000:  # 1 year
                hsts_score += 0.05
            if hsts.get('include_subdomains'):
                hsts_score += 0.03
            if hsts.get('preload'):
                hsts_score += 0.02
            score += hsts_score

        # CSP
        csp = headers.get('content_security_policy', {})
        if csp.get('present'):
            csp_score = 0.10
            if csp.get('has_default_src'):
                csp_score += 0.05
            if csp.get('has_script_src'):
                csp_score += 0.03
            if not csp.get('allows_unsafe_inline'):
                csp_score += 0.04
            if not csp.get('allows_unsafe_eval'):
                csp_score += 0.03
            score += csp_score

        # X-Frame-Options
        xfo = headers.get('x_frame_options', {})
        if xfo.get('present') and xfo.get('valid'):
            score += 0.10

        # X-Content-Type-Options
        xcto = headers.get('x_content_type_options', {})
        if xcto.get('valid'):
            score += 0.10

        # Referrer-Policy
        rp = headers.get('referrer_policy', {})
        if rp.get('present') and rp.get('valid'):
            score += 0.05
            if rp.get('secure'):
                score += 0.05

        # Permissions-Policy
        pp = headers.get('permissions_policy', {})
        if pp.get('present'):
            score += 0.10

        # Cross-Origin headers (bonus)
        if headers.get('cross_origin_opener_policy', {}).get('present'):
            score += 0.05
        if headers.get('cross_origin_resource_policy', {}).get('present'):
            score += 0.05

        # Calculate grade
        if score >= 0.90:
            grade = 'A+'
        elif score >= 0.80:
            grade = 'A'
        elif score >= 0.70:
            grade = 'B'
        elif score >= 0.55:
            grade = 'C'
        elif score >= 0.40:
            grade = 'D'
        else:
            grade = 'F'

        return min(score, 1.0), grade

    def _generate_recommendations(self, headers: Dict[str, Any]) -> tuple:
        """Generate issues and recommendations."""
        issues = []
        recommendations = []

        # HSTS
        hsts = headers.get('strict_transport_security', {})
        if not hsts.get('present'):
            issues.append('Missing Strict-Transport-Security header')
            recommendations.append('Add HSTS header with max-age of at least 1 year')
        elif hsts.get('max_age', 0) < 31536000:
            issues.append('HSTS max-age is less than 1 year')
            recommendations.append('Increase HSTS max-age to at least 31536000 (1 year)')

        # CSP
        csp = headers.get('content_security_policy', {})
        if not csp.get('present'):
            issues.append('Missing Content-Security-Policy header')
            recommendations.append('Implement a Content Security Policy')
        else:
            if csp.get('allows_unsafe_inline'):
                issues.append("CSP allows 'unsafe-inline'")
                recommendations.append("Remove 'unsafe-inline' from CSP, use nonces or hashes instead")
            if csp.get('allows_unsafe_eval'):
                issues.append("CSP allows 'unsafe-eval'")
                recommendations.append("Remove 'unsafe-eval' from CSP if possible")

        # X-Frame-Options
        xfo = headers.get('x_frame_options', {})
        if not xfo.get('present'):
            issues.append('Missing X-Frame-Options header')
            recommendations.append("Add X-Frame-Options: DENY or SAMEORIGIN")

        # X-Content-Type-Options
        xcto = headers.get('x_content_type_options', {})
        if not xcto.get('valid'):
            issues.append('Missing or invalid X-Content-Type-Options header')
            recommendations.append("Add X-Content-Type-Options: nosniff")

        return issues, recommendations
