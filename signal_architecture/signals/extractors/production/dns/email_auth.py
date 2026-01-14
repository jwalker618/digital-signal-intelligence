"""
DSI Production Extractor - Email Authentication (SPF, DKIM, DMARC)

Queries DNS TXT records to check email authentication configuration.
This is a FREE extractor - no API keys required.

Checks:
    - SPF (Sender Policy Framework): Authorizes sending servers
    - DKIM (DomainKeys Identified Mail): Cryptographic signing
    - DMARC (Domain-based Message Authentication): Policy enforcement

Scoring Implications:
    - All three configured with strict policy = Excellent
    - SPF + DMARC = Good
    - SPF only = Basic
    - None = Poor (potential phishing risk)
"""

import logging
import re
from typing import Any, Dict, List, Optional

try:
    import dns.resolver
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class EmailAuthExtractor(ProductionExtractor):
    """
    Extracts email authentication configuration via DNS.

    Queries:
        - TXT record at domain (for SPF)
        - TXT record at _dmarc.domain (for DMARC)
        - TXT record at selector._domainkey.domain (for DKIM, if selector known)

    Output:
        {
            'spf': {
                'exists': bool,
                'record': str or None,
                'mechanisms': list,
                'policy': str,  # 'fail', 'softfail', 'neutral', 'pass'
                'includes': list,
            },
            'dmarc': {
                'exists': bool,
                'record': str or None,
                'policy': str,  # 'none', 'quarantine', 'reject'
                'subdomain_policy': str,
                'pct': int,
                'rua': list,  # Aggregate report addresses
                'ruf': list,  # Forensic report addresses
            },
            'dkim': {
                'selectors_checked': list,
                'selectors_found': list,
                'exists': bool,
            },
            'score': float,  # 0-1 composite score
            'issues': list,  # List of identified issues
        }
    """

    SOURCE_NAME = "dns_email_auth"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    RATE_LIMIT = 10.0  # DNS queries are fast
    COST_TIER = "free"

    # Common DKIM selectors to check
    COMMON_DKIM_SELECTORS = [
        'default', 'dkim', 'mail', 'email', 'k1', 'key1',
        'google', 'selector1', 'selector2',  # Microsoft
        's1', 's2', 'mx', 'smtp',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not DNS_AVAILABLE:
            raise ImportError(
                "dnspython is required for EmailAuthExtractor. "
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
        """Extract email authentication data for a domain."""
        domain = self._normalize_domain(entity_id)

        spf_data = self._check_spf(domain)
        dmarc_data = self._check_dmarc(domain)
        dkim_data = self._check_dkim(domain, kwargs.get('dkim_selectors'))

        # Calculate score and issues
        score, issues = self._calculate_score(spf_data, dmarc_data, dkim_data)

        data = {
            'domain': domain,
            'spf': spf_data,
            'dmarc': dmarc_data,
            'dkim': dkim_data,
            'score': score,
            'issues': issues,
        }

        return self._create_success_result(data, confidence=0.95)

    def _check_spf(self, domain: str) -> Dict[str, Any]:
        """Check SPF record."""
        result = {
            'exists': False,
            'record': None,
            'mechanisms': [],
            'policy': None,
            'includes': [],
            'redirects': [],
            'error': None,
        }

        try:
            answers = self._resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=spf1'):
                    result['exists'] = True
                    result['record'] = txt
                    result['mechanisms'] = self._parse_spf_mechanisms(txt)
                    result['policy'] = self._extract_spf_policy(txt)
                    result['includes'] = self._extract_spf_includes(txt)
                    result['redirects'] = self._extract_spf_redirects(txt)
                    break
        except dns.resolver.NXDOMAIN:
            result['error'] = 'Domain does not exist'
        except dns.resolver.NoAnswer:
            result['error'] = 'No TXT records'
        except dns.exception.DNSException as e:
            result['error'] = str(e)

        return result

    def _check_dmarc(self, domain: str) -> Dict[str, Any]:
        """Check DMARC record."""
        result = {
            'exists': False,
            'record': None,
            'policy': None,
            'subdomain_policy': None,
            'pct': 100,
            'rua': [],
            'ruf': [],
            'aspf': 'r',  # relaxed by default
            'adkim': 'r',  # relaxed by default
            'error': None,
        }

        dmarc_domain = f'_dmarc.{domain}'

        try:
            answers = self._resolver.resolve(dmarc_domain, 'TXT')
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=DMARC1'):
                    result['exists'] = True
                    result['record'] = txt
                    result.update(self._parse_dmarc(txt))
                    break
        except dns.resolver.NXDOMAIN:
            result['error'] = 'DMARC record not found'
        except dns.resolver.NoAnswer:
            result['error'] = 'No DMARC record'
        except dns.exception.DNSException as e:
            result['error'] = str(e)

        return result

    def _check_dkim(
        self,
        domain: str,
        selectors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check DKIM records for common selectors."""
        selectors_to_check = selectors or self.COMMON_DKIM_SELECTORS
        found_selectors = []

        for selector in selectors_to_check:
            dkim_domain = f'{selector}._domainkey.{domain}'
            try:
                answers = self._resolver.resolve(dkim_domain, 'TXT')
                for rdata in answers:
                    txt = str(rdata).strip('"')
                    if 'v=DKIM1' in txt or 'k=' in txt:
                        found_selectors.append({
                            'selector': selector,
                            'record': txt[:200],  # Truncate long records
                        })
                        break
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
                continue

        return {
            'exists': len(found_selectors) > 0,
            'selectors_checked': selectors_to_check,
            'selectors_found': found_selectors,
            'count': len(found_selectors),
        }

    def _parse_spf_mechanisms(self, spf: str) -> List[str]:
        """Extract mechanisms from SPF record."""
        mechanisms = []
        parts = spf.split()
        for part in parts[1:]:  # Skip v=spf1
            if part in ('-all', '~all', '?all', '+all', 'all'):
                continue
            mechanisms.append(part)
        return mechanisms

    def _extract_spf_policy(self, spf: str) -> str:
        """Extract the policy (all mechanism) from SPF."""
        if '-all' in spf:
            return 'fail'
        elif '~all' in spf:
            return 'softfail'
        elif '?all' in spf:
            return 'neutral'
        elif '+all' in spf:
            return 'pass'
        return 'unknown'

    def _extract_spf_includes(self, spf: str) -> List[str]:
        """Extract include domains from SPF."""
        includes = re.findall(r'include:([^\s]+)', spf)
        return includes

    def _extract_spf_redirects(self, spf: str) -> List[str]:
        """Extract redirect domains from SPF."""
        redirects = re.findall(r'redirect=([^\s]+)', spf)
        return redirects

    def _parse_dmarc(self, dmarc: str) -> Dict[str, Any]:
        """Parse DMARC record tags."""
        result = {}

        # Extract policy (p=)
        p_match = re.search(r'\bp=(\w+)', dmarc)
        if p_match:
            result['policy'] = p_match.group(1).lower()

        # Subdomain policy (sp=)
        sp_match = re.search(r'\bsp=(\w+)', dmarc)
        if sp_match:
            result['subdomain_policy'] = sp_match.group(1).lower()

        # Percentage (pct=)
        pct_match = re.search(r'\bpct=(\d+)', dmarc)
        if pct_match:
            result['pct'] = int(pct_match.group(1))

        # Aggregate reports (rua=)
        rua_match = re.search(r'\brua=([^;]+)', dmarc)
        if rua_match:
            result['rua'] = [addr.strip() for addr in rua_match.group(1).split(',')]

        # Forensic reports (ruf=)
        ruf_match = re.search(r'\bruf=([^;]+)', dmarc)
        if ruf_match:
            result['ruf'] = [addr.strip() for addr in ruf_match.group(1).split(',')]

        # SPF alignment (aspf=)
        aspf_match = re.search(r'\baspf=([rs])', dmarc)
        if aspf_match:
            result['aspf'] = aspf_match.group(1)

        # DKIM alignment (adkim=)
        adkim_match = re.search(r'\badkim=([rs])', dmarc)
        if adkim_match:
            result['adkim'] = adkim_match.group(1)

        return result

    def _calculate_score(
        self,
        spf: Dict[str, Any],
        dmarc: Dict[str, Any],
        dkim: Dict[str, Any]
    ) -> tuple:
        """Calculate a composite score and identify issues."""
        score = 0.0
        issues = []

        # SPF scoring (up to 0.35)
        if spf['exists']:
            score += 0.15
            if spf['policy'] == 'fail':
                score += 0.20
            elif spf['policy'] == 'softfail':
                score += 0.10
            else:
                issues.append('SPF policy is too permissive')
        else:
            issues.append('No SPF record configured')

        # DMARC scoring (up to 0.40)
        if dmarc['exists']:
            score += 0.15
            if dmarc['policy'] == 'reject':
                score += 0.25
            elif dmarc['policy'] == 'quarantine':
                score += 0.15
            elif dmarc['policy'] == 'none':
                score += 0.05
                issues.append('DMARC policy is set to none (monitoring only)')
            if dmarc.get('rua'):
                score += 0.05  # Bonus for having reporting
        else:
            issues.append('No DMARC record configured')

        # DKIM scoring (up to 0.25)
        if dkim['exists']:
            score += 0.25
        else:
            issues.append('No DKIM records found (checked common selectors)')

        return min(score, 1.0), issues
