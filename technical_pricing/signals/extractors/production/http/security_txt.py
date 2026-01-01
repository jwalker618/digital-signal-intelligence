"""
DSI Production Extractor - security.txt (RFC 9116)

Checks for the presence and validity of a security.txt file.
This is a FREE extractor - no API keys required.

RFC 9116 Specification:
    - Location: /.well-known/security.txt (preferred) or /security.txt
    - Required fields: Contact
    - Recommended fields: Expires, Encryption, Preferred-Languages
    - Optional fields: Acknowledgments, Canonical, Policy, Hiring

Scoring Implications:
    - Valid security.txt with all recommended fields = Excellent
    - Basic security.txt with required fields = Good
    - security.txt present but invalid = Moderate
    - No security.txt = Neutral (not necessarily bad, but a missed opportunity)
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor, utcnow
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class SecurityTxtExtractor(ProductionExtractor):
    """
    Extracts and validates security.txt file per RFC 9116.

    Checks both standard locations:
        - /.well-known/security.txt (RFC 9116 standard)
        - /security.txt (legacy location)

    Output:
        {
            'found': bool,
            'location': str,  # URL where found
            'signed': bool,  # PGP signed
            'valid': bool,  # Has required fields
            'fields': {
                'contact': [...],
                'expires': str,
                'encryption': [...],
                'acknowledgments': str,
                'preferred_languages': [...],
                'canonical': [...],
                'policy': str,
                'hiring': str,
            },
            'issues': [...],
            'score': float,
        }
    """

    SOURCE_NAME = "http_security_txt"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # Standard locations to check
    LOCATIONS = [
        '/.well-known/security.txt',
        '/security.txt',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SecurityTxtExtractor. "
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
        """Extract security.txt for a domain."""
        domain = self._normalize_domain(entity_id)

        # Try each location
        content = None
        location = None

        for path in self.LOCATIONS:
            url = f'https://{domain}{path}'
            try:
                response = requests.get(
                    url,
                    timeout=self._timeout,
                    headers={'User-Agent': self._user_agent},
                    allow_redirects=True,
                )

                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/plain' in content_type or 'text/html' not in content_type:
                        content = response.text
                        location = url
                        break

            except requests.exceptions.RequestException:
                continue

        if not content:
            return self._create_success_result({
                'domain': domain,
                'found': False,
                'location': None,
                'signed': False,
                'valid': False,
                'fields': {},
                'issues': ['No security.txt file found'],
                'score': 0.0,
            })

        # Parse the security.txt content
        parsed = self._parse_security_txt(content)
        issues = self._validate(parsed)
        score = self._calculate_score(parsed, issues)

        data = {
            'domain': domain,
            'found': True,
            'location': location,
            'signed': parsed.get('signed', False),
            'valid': len(issues) == 0 or all('warning' in i.lower() for i in issues),
            'fields': parsed.get('fields', {}),
            'issues': issues,
            'score': score,
            'raw_content': content[:2000],  # Truncate for storage
        }

        return self._create_success_result(data, confidence=0.95)

    def _parse_security_txt(self, content: str) -> Dict[str, Any]:
        """Parse security.txt content according to RFC 9116."""
        result = {
            'signed': False,
            'fields': {
                'contact': [],
                'expires': None,
                'encryption': [],
                'acknowledgments': None,
                'preferred_languages': [],
                'canonical': [],
                'policy': None,
                'hiring': None,
            },
            'comments': [],
            'unknown_fields': [],
        }

        # Check if PGP signed
        if '-----BEGIN PGP SIGNED MESSAGE-----' in content:
            result['signed'] = True
            # Extract the signed content (between headers and signature)
            match = re.search(
                r'-----BEGIN PGP SIGNED MESSAGE-----.*?Hash:.*?\n\n(.*?)-----BEGIN PGP SIGNATURE-----',
                content,
                re.DOTALL
            )
            if match:
                content = match.group(1)

        # Parse line by line
        for line in content.split('\n'):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Comments
            if line.startswith('#'):
                result['comments'].append(line[1:].strip())
                continue

            # Parse field: value
            if ':' in line:
                field, _, value = line.partition(':')
                field = field.strip().lower()
                value = value.strip()

                if field == 'contact':
                    result['fields']['contact'].append(value)
                elif field == 'expires':
                    result['fields']['expires'] = value
                elif field == 'encryption':
                    result['fields']['encryption'].append(value)
                elif field == 'acknowledgments' or field == 'acknowledgements':
                    result['fields']['acknowledgments'] = value
                elif field == 'preferred-languages':
                    result['fields']['preferred_languages'] = [
                        lang.strip() for lang in value.split(',')
                    ]
                elif field == 'canonical':
                    result['fields']['canonical'].append(value)
                elif field == 'policy':
                    result['fields']['policy'] = value
                elif field == 'hiring':
                    result['fields']['hiring'] = value
                else:
                    result['unknown_fields'].append({'field': field, 'value': value})

        return result

    def _validate(self, parsed: Dict[str, Any]) -> List[str]:
        """Validate the parsed security.txt against RFC 9116."""
        issues = []
        fields = parsed.get('fields', {})

        # Required: Contact
        if not fields.get('contact'):
            issues.append('Missing required field: Contact')
        else:
            # Validate contact format (should be URI)
            for contact in fields['contact']:
                if not (contact.startswith('mailto:') or
                        contact.startswith('https://') or
                        contact.startswith('tel:')):
                    issues.append(f'Contact should be a URI (mailto:, https:, or tel:): {contact}')

        # Recommended: Expires
        if not fields.get('expires'):
            issues.append('Warning: Missing recommended field: Expires')
        else:
            # Validate expires format (ISO 8601)
            try:
                expires = fields['expires']
                # Try parsing ISO 8601 format
                if expires.endswith('Z'):
                    exp_date = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                else:
                    exp_date = datetime.fromisoformat(expires)

                # Check if expired
                if exp_date.replace(tzinfo=None) < utcnow().replace(tzinfo=None):
                    issues.append('security.txt has expired')
            except ValueError:
                issues.append(f'Invalid Expires date format: {fields["expires"]}')

        # Validate encryption URIs
        for enc in fields.get('encryption', []):
            if not (enc.startswith('https://') or enc.startswith('openpgp4fpr:')):
                issues.append(f'Encryption should be https:// or openpgp4fpr: URI: {enc}')

        # Validate canonical URIs
        for canonical in fields.get('canonical', []):
            if not canonical.startswith('https://'):
                issues.append(f'Canonical should be https:// URI: {canonical}')

        # Check for unknown fields (not an error, just informational)
        for unknown in parsed.get('unknown_fields', []):
            issues.append(f'Warning: Unknown field: {unknown["field"]}')

        return issues

    def _calculate_score(self, parsed: Dict[str, Any], issues: List[str]) -> float:
        """Calculate a score for security.txt quality."""
        score = 0.0
        fields = parsed.get('fields', {})

        # Base score for having a security.txt
        score += 0.20

        # Contact (required, high weight)
        if fields.get('contact'):
            score += 0.25
            # Bonus for multiple contact methods
            if len(fields['contact']) > 1:
                score += 0.05

        # Expires (recommended)
        if fields.get('expires'):
            # Check if not expired
            try:
                expires = fields['expires']
                if expires.endswith('Z'):
                    exp_date = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                else:
                    exp_date = datetime.fromisoformat(expires)
                if exp_date.replace(tzinfo=None) > utcnow().replace(tzinfo=None):
                    score += 0.15
            except ValueError:
                pass

        # Encryption key
        if fields.get('encryption'):
            score += 0.10

        # Policy
        if fields.get('policy'):
            score += 0.10

        # Canonical
        if fields.get('canonical'):
            score += 0.05

        # PGP signed (shows extra effort)
        if parsed.get('signed'):
            score += 0.10

        # Penalty for critical issues
        critical_issues = [i for i in issues if 'warning' not in i.lower()]
        score -= len(critical_issues) * 0.05

        return max(0.0, min(1.0, score))
