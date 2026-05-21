"""
DSI Production Extractor - EU Air Safety List

Checks the European Union Air Safety List (banned airlines list).
This is a FREE extractor - EU data is public.

EU Air Safety List:
    - Airlines banned from operating in EU airspace
    - Updated regularly by the European Commission
    - Includes both full bans and operational restrictions

Data Source:
    https://transport.ec.europa.eu/transport-themes/eu-air-safety-list_en

Scoring Implications:
    - Airline on ban list = Critical negative
    - Airline from banned country = Major concern
    - Operational restrictions = Significant concern
    - Not on list = Positive signal (for aviation entities)
"""

import logging
import re
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


# Known banned countries/airlines (sample - should be updated from official source)
# This is a simplified list - production should fetch from EU website
BANNED_COUNTRIES = [
    'Afghanistan', 'Angola', 'Armenia', 'Congo (Brazzaville)',
    'Congo (Kinshasa)', 'Djibouti', 'Equatorial Guinea', 'Eritrea',
    'Kyrgyzstan', 'Liberia', 'Libya', 'Nepal', 'São Tomé and Príncipe',
    'Sierra Leone', 'Sudan',
]

RESTRICTED_AIRLINES = {
    # Airlines with operational restrictions (sample data)
    'Air Koryo': 'North Korea - restricted to specific aircraft',
    'Iran Air': 'Iran - restricted to specific aircraft types',
}


class EUSafetyListExtractor(ProductionExtractor):
    """
    Checks EU Air Safety List for banned/restricted airlines.

    Searches for airlines and countries on the EU ban list.

    Output:
        {
            'searched_name': str,
            'on_ban_list': bool,
            'ban_type': str,  # 'full_ban', 'operational_restriction', 'country_ban', 'none'
            'details': {
                'airline_name': str,
                'country': str,
                'restriction_type': str,
                'reason': str,
                'effective_date': str,
            },
            'country_status': {
                'country': str,
                'all_airlines_banned': bool,
            },
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "eu_safety_list"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week (list updated periodically)
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # EU Air Safety List URL
    EU_SAFETY_LIST_URL = "https://transport.ec.europa.eu/transport-themes/eu-air-safety-list_en"
    EU_SAFETY_LIST_PDF = "https://transport.ec.europa.eu/system/files/2023-11/list_en.pdf"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for EUSafetyListExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._banned_list = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Check EU Air Safety List for an airline or country."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Load the banned list if not cached
        if self._banned_list is None:
            self._banned_list = self._load_banned_list()

        # Check if it's a country search
        is_country = kwargs.get('is_country', False) or self._is_country(search_term)

        if is_country:
            result = self._check_country(search_term)
        else:
            result = self._check_airline(search_term)

        return self._create_success_result(result, confidence=0.85)

    def _load_banned_list(self) -> Dict[str, Any]:
        """Load the current EU Air Safety List."""
        banned_list = {
            'countries': [],
            'airlines': {},
            'restrictions': {},
            'last_updated': None,
        }

        try:
            # Try to fetch the current list from EU website
            response = requests.get(
                self.EU_SAFETY_LIST_URL,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (aviation-safety-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                # Parse the HTML for ban list data
                banned_list = self._parse_safety_list_html(response.text)

        except Exception as e:
            logger.debug(f"Could not fetch EU Safety List: {e}")

        # Use fallback data if fetch failed
        if not banned_list['countries']:
            banned_list['countries'] = BANNED_COUNTRIES
            banned_list['airlines'] = RESTRICTED_AIRLINES

        return banned_list

    def _parse_safety_list_html(self, html: str) -> Dict[str, Any]:
        """Parse EU Safety List from HTML."""
        result = {
            'countries': [],
            'airlines': {},
            'restrictions': {},
            'last_updated': None,
        }

        # Look for country names in banned list sections
        for country in BANNED_COUNTRIES:
            if country.lower() in html.lower():
                result['countries'].append(country)

        # Look for update date
        date_pattern = r'(?:updated|effective)[^:]*:\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})'
        date_match = re.search(date_pattern, html, re.IGNORECASE)
        if date_match:
            result['last_updated'] = date_match.group(1)

        # Extract airline names from tables if present
        airline_pattern = r'<td[^>]*>([^<]+(?:Air|Airlines|Airways|Aviation)[^<]*)</td>'
        airlines = re.findall(airline_pattern, html, re.IGNORECASE)
        for airline in airlines:
            airline_clean = airline.strip()
            if airline_clean and len(airline_clean) > 3:
                result['airlines'][airline_clean] = 'On EU Air Safety List'

        return result

    def _is_country(self, search_term: str) -> bool:
        """Check if search term appears to be a country name."""
        search_lower = search_term.lower()
        for country in BANNED_COUNTRIES + ['usa', 'uk', 'china', 'russia', 'india']:
            if country.lower() == search_lower:
                return True
        return False

    def _check_country(self, country: str) -> Dict[str, Any]:
        """Check if a country's airlines are banned."""
        country_lower = country.lower()

        is_banned = False
        for banned in self._banned_list.get('countries', []):
            if banned.lower() == country_lower or country_lower in banned.lower():
                is_banned = True
                break

        risk_score = 100.0 if is_banned else 0.0

        return {
            'searched_name': country,
            'search_type': 'country',
            'on_ban_list': is_banned,
            'ban_type': 'country_ban' if is_banned else 'none',
            'details': {
                'country': country,
                'all_airlines_banned': is_banned,
                'reason': 'All air carriers certified in this country are banned' if is_banned else None,
            },
            'country_status': {
                'country': country,
                'all_airlines_banned': is_banned,
            },
            'risk_score': risk_score,
        }

    def _check_airline(self, airline: str) -> Dict[str, Any]:
        """Check if an airline is on the ban list."""
        airline_lower = airline.lower()

        # Check for exact match or partial match in airlines list
        ban_type = 'none'
        details = None
        risk_score = 0.0

        # Check full bans
        for banned_airline, reason in self._banned_list.get('airlines', {}).items():
            if airline_lower in banned_airline.lower() or banned_airline.lower() in airline_lower:
                ban_type = 'full_ban'
                details = {
                    'airline_name': banned_airline,
                    'restriction_type': 'Full Ban',
                    'reason': reason,
                }
                risk_score = 100.0
                break

        # Check restrictions
        if ban_type == 'none':
            for restricted, reason in RESTRICTED_AIRLINES.items():
                if airline_lower in restricted.lower() or restricted.lower() in airline_lower:
                    ban_type = 'operational_restriction'
                    details = {
                        'airline_name': restricted,
                        'restriction_type': 'Operational Restriction',
                        'reason': reason,
                    }
                    risk_score = 60.0
                    break

        return {
            'searched_name': airline,
            'search_type': 'airline',
            'on_ban_list': ban_type != 'none',
            'ban_type': ban_type,
            'details': details,
            'country_status': None,
            'risk_score': risk_score,
        }
