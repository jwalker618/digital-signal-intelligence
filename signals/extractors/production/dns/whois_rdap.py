"""
DSI Production Extractor - Domain WHOIS/RDAP

Queries domain registration data via RDAP (Registration Data Access Protocol).
FREE - RDAP is the standardized successor to WHOIS.

RDAP/WHOIS Data:
    - Domain registration date
    - Expiration date
    - Registrar information
    - Nameservers
    - Domain status (clientHold, serverHold, etc.)
    - Registrant info (often redacted for privacy)

Data Source:
    RDAP bootstrap: https://data.iana.org/rdap/dns.json
    Individual registry RDAP servers

Coverage:
    - All gTLDs (.com, .org, .net, etc.)
    - Many ccTLDs with RDAP support

Scoring Implications:
    - Recently registered domain = Moderate concern
    - Domain expiring soon = Moderate concern
    - Privacy protected = Neutral (common practice)
    - Domain on hold = High concern
    - Long-established domain = Positive
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class WHOISRDAPExtractor(ProductionExtractor):
    """
    Queries domain registration data via RDAP.

    Uses IANA bootstrap to find correct RDAP server.

    Output:
        {
            'domain': str,
            'registered': bool,
            'registration_date': str,
            'expiration_date': str,
            'last_updated': str,
            'registrar': str,
            'nameservers': [...],
            'status': [...],
            'domain_age_days': int,
            'days_until_expiry': int,
            'privacy_protected': bool,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "whois_rdap"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # RDAP bootstrap
    IANA_RDAP_DNS = "https://data.iana.org/rdap/dns.json"

    # Fallback RDAP servers for common TLDs
    RDAP_SERVERS = {
        'com': 'https://rdap.verisign.com/com/v1/domain/',
        'net': 'https://rdap.verisign.com/net/v1/domain/',
        'org': 'https://rdap.publicinterestregistry.org/rdap/domain/',
        'io': 'https://rdap.nic.io/domain/',
        'co': 'https://rdap.nic.co/domain/',
        'uk': 'https://rdap.nominet.uk/uk/domain/',
        'de': 'https://rdap.denic.de/domain/',
        'eu': 'https://rdap.eurid.eu/domain/',
        'nl': 'https://rdap.sidn.nl/domain/',
        'au': 'https://rdap.auda.org.au/domain/',
        'ca': 'https://rdap.ca.fury.ca/rdap/domain/',
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for WHOISRDAPExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 15) if config else 15
        self._rdap_cache = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Query RDAP for domain registration data."""
        domain = entity_id.strip().lower()

        # Clean domain
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]

        if not domain or '.' not in domain:
            return self._create_error_result("Invalid domain provided")

        try:
            rdap_data = self._query_rdap(domain)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"RDAP query error: {e}")

        if not rdap_data:
            return self._create_success_result({
                'domain': domain,
                'registered': False,
                'risk_score': 30.0,
                'note': 'Domain not found or RDAP not available for this TLD',
            })

        # Parse dates
        reg_date = rdap_data.get('registration_date', '')
        exp_date = rdap_data.get('expiration_date', '')

        domain_age = None
        days_until_expiry = None

        if reg_date:
            try:
                reg_dt = datetime.fromisoformat(reg_date.replace('Z', '+00:00'))
                domain_age = (datetime.now(reg_dt.tzinfo) - reg_dt).days
            except (ValueError, TypeError):
                pass

        if exp_date:
            try:
                exp_dt = datetime.fromisoformat(exp_date.replace('Z', '+00:00'))
                days_until_expiry = (exp_dt - datetime.now(exp_dt.tzinfo)).days
            except (ValueError, TypeError):
                pass

        # Calculate risk score
        risk_score = self._calculate_risk_score(rdap_data, domain_age, days_until_expiry)

        data = {
            'domain': domain,
            'registered': True,
            'registration_date': reg_date,
            'expiration_date': exp_date,
            'last_updated': rdap_data.get('last_updated', ''),
            'registrar': rdap_data.get('registrar', ''),
            'nameservers': rdap_data.get('nameservers', []),
            'status': rdap_data.get('status', []),
            'domain_age_days': domain_age,
            'days_until_expiry': days_until_expiry,
            'privacy_protected': rdap_data.get('privacy_protected', False),
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _query_rdap(self, domain: str) -> Optional[Dict]:
        """Query RDAP for domain data."""
        tld = domain.split('.')[-1]

        # Get RDAP server URL
        rdap_url = self._get_rdap_server(tld)

        if not rdap_url:
            return None

        try:
            response = requests.get(
                f"{rdap_url}{domain}",
                headers={
                    'Accept': 'application/rdap+json',
                    'User-Agent': 'DSI-Framework/1.0 (domain-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_rdap_response(data)

            elif response.status_code == 404:
                return None  # Domain not registered

        except Exception as e:
            logger.debug(f"RDAP query error for {domain}: {e}")

        return None

    def _get_rdap_server(self, tld: str) -> Optional[str]:
        """Get RDAP server URL for a TLD."""
        # Check cache
        if tld in self.RDAP_SERVERS:
            return self.RDAP_SERVERS[tld]

        # Try IANA bootstrap
        try:
            if not self._rdap_cache:
                response = requests.get(
                    self.IANA_RDAP_DNS,
                    timeout=10,
                )
                if response.status_code == 200:
                    self._rdap_cache = response.json()

            if self._rdap_cache:
                services = self._rdap_cache.get('services', [])
                for service in services:
                    if len(service) >= 2:
                        tlds, urls = service[0], service[1]
                        if tld in tlds and urls:
                            return urls[0]

        except Exception as e:
            logger.debug(f"IANA bootstrap error: {e}")

        return None

    def _parse_rdap_response(self, data: Dict) -> Dict:
        """Parse RDAP response."""
        result = {
            'registration_date': '',
            'expiration_date': '',
            'last_updated': '',
            'registrar': '',
            'nameservers': [],
            'status': [],
            'privacy_protected': False,
        }

        # Parse events
        for event in data.get('events', []):
            action = event.get('eventAction', '')
            date = event.get('eventDate', '')

            if action == 'registration':
                result['registration_date'] = date
            elif action == 'expiration':
                result['expiration_date'] = date
            elif action == 'last changed' or action == 'last update of RDAP database':
                result['last_updated'] = date

        # Parse status
        result['status'] = data.get('status', [])

        # Parse nameservers
        for ns in data.get('nameservers', []):
            if isinstance(ns, dict):
                result['nameservers'].append(ns.get('ldhName', ''))
            else:
                result['nameservers'].append(str(ns))

        # Parse registrar
        for entity in data.get('entities', []):
            roles = entity.get('roles', [])
            if 'registrar' in roles:
                vcard = entity.get('vcardArray', [])
                if len(vcard) > 1:
                    for item in vcard[1]:
                        if item[0] == 'fn':
                            result['registrar'] = item[3]
                            break

            # Check for privacy proxy
            if 'registrant' in roles:
                vcard = entity.get('vcardArray', [])
                if vcard:
                    vcard_str = str(vcard).lower()
                    privacy_terms = ['privacy', 'proxy', 'redacted', 'whoisguard', 'domains by proxy']
                    if any(term in vcard_str for term in privacy_terms):
                        result['privacy_protected'] = True

        return result

    def _calculate_risk_score(
        self, data: Dict, domain_age: Optional[int], days_until_expiry: Optional[int]
    ) -> float:
        """Calculate risk score from domain data."""
        score = 0.0

        # Domain age
        if domain_age is not None:
            if domain_age < 30:
                score += 30  # Very new - high risk
            elif domain_age < 90:
                score += 20  # New - moderate risk
            elif domain_age < 365:
                score += 10  # Less than a year
            elif domain_age > 365 * 5:
                score -= 5  # Established domain

        # Expiration
        if days_until_expiry is not None:
            if days_until_expiry < 0:
                score += 40  # Expired
            elif days_until_expiry < 30:
                score += 25  # Expiring soon
            elif days_until_expiry < 90:
                score += 10

        # Status flags
        status = data.get('status', [])
        concerning_statuses = [
            'clienthold', 'serverhold', 'pendingdelete',
            'redemptionperiod', 'pendingrestore',
        ]
        for s in status:
            s_lower = s.lower()
            if any(cs in s_lower for cs in concerning_statuses):
                score += 30
                break

        return max(0.0, min(100.0, score))
