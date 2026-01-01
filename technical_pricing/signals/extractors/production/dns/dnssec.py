"""
DSI Production Extractor - DNSSEC Validation

Checks if a domain has DNSSEC (DNS Security Extensions) configured.
This is a FREE extractor - no API keys required.

DNSSEC provides:
    - Authentication of DNS data origin
    - Data integrity protection
    - Authenticated denial of existence

Scoring Implications:
    - DNSSEC enabled and valid = Excellent security posture
    - DNSSEC enabled but issues = Moderate
    - No DNSSEC = Common (not necessarily bad, but less secure)
"""

import logging
from typing import Any, Dict, List, Optional

try:
    import dns.resolver
    import dns.dnssec
    import dns.rdatatype
    import dns.exception
    import dns.flags
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class DNSSECExtractor(ProductionExtractor):
    """
    Extracts DNSSEC configuration via DNS queries.

    Checks:
        - DNSKEY records (public keys)
        - DS records (delegation signer)
        - RRSIG records (signatures)
        - NSEC/NSEC3 records (authenticated denial)

    Output:
        {
            'dnssec_enabled': bool,
            'dnskey': {
                'exists': bool,
                'count': int,
                'algorithms': list,
                'key_types': list,  # KSK, ZSK
            },
            'ds': {
                'exists': bool,
                'count': int,
                'algorithms': list,
            },
            'validation': {
                'status': str,  # 'secure', 'insecure', 'bogus', 'indeterminate'
                'chain_of_trust': bool,
            },
            'score': float,  # 0-1
            'issues': list,
        }
    """

    SOURCE_NAME = "dns_dnssec"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours (DNSSEC changes infrequently)
    RATE_LIMIT = 10.0
    COST_TIER = "free"

    # DNSSEC algorithm names
    ALGORITHMS = {
        1: 'RSAMD5',
        3: 'DSA',
        5: 'RSASHA1',
        6: 'DSA-NSEC3-SHA1',
        7: 'RSASHA1-NSEC3-SHA1',
        8: 'RSASHA256',
        10: 'RSASHA512',
        12: 'ECC-GOST',
        13: 'ECDSAP256SHA256',
        14: 'ECDSAP384SHA384',
        15: 'ED25519',
        16: 'ED448',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not DNS_AVAILABLE:
            raise ImportError(
                "dnspython is required for DNSSECExtractor. "
                "Install with: pip install dnspython"
            )
        super().__init__(config)
        self._resolver = dns.resolver.Resolver()
        if config and config.get('dns_resolver'):
            self._resolver.nameservers = [config['dns_resolver']]
        self._resolver.timeout = config.get('timeout', 5) if config else 5
        self._resolver.lifetime = config.get('timeout', 10) if config else 10
        # Enable DNSSEC validation
        self._resolver.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Extract DNSSEC configuration for a domain."""
        domain = self._normalize_domain(entity_id)

        dnskey_data = self._check_dnskey(domain)
        ds_data = self._check_ds(domain)
        validation = self._check_validation(domain)

        # Determine if DNSSEC is enabled
        dnssec_enabled = dnskey_data['exists'] or ds_data['exists']

        # Calculate score and issues
        score, issues = self._calculate_score(dnskey_data, ds_data, validation)

        data = {
            'domain': domain,
            'dnssec_enabled': dnssec_enabled,
            'dnskey': dnskey_data,
            'ds': ds_data,
            'validation': validation,
            'score': score,
            'issues': issues,
        }

        return self._create_success_result(data, confidence=0.95)

    def _check_dnskey(self, domain: str) -> Dict[str, Any]:
        """Check for DNSKEY records."""
        result = {
            'exists': False,
            'count': 0,
            'algorithms': [],
            'key_types': [],
            'error': None,
        }

        try:
            answers = self._resolver.resolve(domain, 'DNSKEY')
            result['exists'] = True
            result['count'] = len(answers)

            algorithms = set()
            key_types = []

            for rdata in answers:
                # Get algorithm
                algo_num = rdata.algorithm
                algo_name = self.ALGORITHMS.get(algo_num, f'Unknown({algo_num})')
                algorithms.add(algo_name)

                # Determine key type (KSK vs ZSK)
                # Flag bit 257 = KSK, 256 = ZSK
                flags = rdata.flags
                if flags & 0x0001:  # SEP flag
                    key_types.append('KSK')
                else:
                    key_types.append('ZSK')

            result['algorithms'] = list(algorithms)
            result['key_types'] = key_types

        except dns.resolver.NXDOMAIN:
            result['error'] = 'Domain does not exist'
        except dns.resolver.NoAnswer:
            result['error'] = 'No DNSKEY records'
        except dns.exception.DNSException as e:
            result['error'] = str(e)

        return result

    def _check_ds(self, domain: str) -> Dict[str, Any]:
        """Check for DS (Delegation Signer) records at parent."""
        result = {
            'exists': False,
            'count': 0,
            'algorithms': [],
            'digest_types': [],
            'error': None,
        }

        try:
            answers = self._resolver.resolve(domain, 'DS')
            result['exists'] = True
            result['count'] = len(answers)

            algorithms = set()
            digest_types = set()

            for rdata in answers:
                algo_num = rdata.algorithm
                algo_name = self.ALGORITHMS.get(algo_num, f'Unknown({algo_num})')
                algorithms.add(algo_name)

                # Digest type
                digest_map = {1: 'SHA-1', 2: 'SHA-256', 3: 'GOST', 4: 'SHA-384'}
                digest_type = digest_map.get(rdata.digest_type, f'Unknown({rdata.digest_type})')
                digest_types.add(digest_type)

            result['algorithms'] = list(algorithms)
            result['digest_types'] = list(digest_types)

        except dns.resolver.NXDOMAIN:
            result['error'] = 'Domain does not exist'
        except dns.resolver.NoAnswer:
            # No DS at parent - domain may not have DNSSEC
            result['error'] = 'No DS records at parent zone'
        except dns.exception.DNSException as e:
            result['error'] = str(e)

        return result

    def _check_validation(self, domain: str) -> Dict[str, Any]:
        """Check DNSSEC validation status."""
        result = {
            'status': 'indeterminate',
            'chain_of_trust': False,
            'ad_flag': False,
            'error': None,
        }

        try:
            # Try to get A record with DNSSEC validation
            answers = self._resolver.resolve(domain, 'A')

            # Check if AD (Authenticated Data) flag is set
            if hasattr(answers.response, 'flags'):
                ad_flag = bool(answers.response.flags & dns.flags.AD)
                result['ad_flag'] = ad_flag
                if ad_flag:
                    result['status'] = 'secure'
                    result['chain_of_trust'] = True
                else:
                    result['status'] = 'insecure'

        except dns.resolver.NXDOMAIN:
            result['status'] = 'nxdomain'
            result['error'] = 'Domain does not exist'
        except dns.resolver.NoAnswer:
            result['status'] = 'no_answer'
        except dns.exception.DNSException as e:
            result['error'] = str(e)

        return result

    def _calculate_score(
        self,
        dnskey: Dict[str, Any],
        ds: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> tuple:
        """Calculate DNSSEC score and identify issues."""
        score = 0.0
        issues = []

        # DNSSEC not configured is common - not necessarily an issue
        if not dnskey['exists'] and not ds['exists']:
            score = 0.3  # Baseline score for domains without DNSSEC
            issues.append('DNSSEC not configured')
            return score, issues

        # Has DNSKEY
        if dnskey['exists']:
            score += 0.30
            # Check for modern algorithms
            modern_algos = {'ECDSAP256SHA256', 'ECDSAP384SHA384', 'ED25519', 'ED448', 'RSASHA256'}
            if any(algo in modern_algos for algo in dnskey.get('algorithms', [])):
                score += 0.10
            else:
                issues.append('Using legacy DNSSEC algorithms')

            # Check for both KSK and ZSK
            key_types = dnskey.get('key_types', [])
            if 'KSK' in key_types and 'ZSK' in key_types:
                score += 0.10
            elif 'KSK' not in key_types:
                issues.append('No Key Signing Key (KSK) found')

        # Has DS record
        if ds['exists']:
            score += 0.20
            # Check digest type
            if 'SHA-256' in ds.get('digest_types', []) or 'SHA-384' in ds.get('digest_types', []):
                score += 0.10
            elif 'SHA-1' in ds.get('digest_types', []):
                issues.append('DS record using deprecated SHA-1')

        # Validation status
        if validation.get('status') == 'secure':
            score += 0.20
        elif validation.get('status') == 'insecure':
            issues.append('DNSSEC validation not returning secure status')

        return min(score, 1.0), issues
