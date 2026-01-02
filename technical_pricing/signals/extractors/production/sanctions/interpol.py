"""
DSI Production Extractor - Interpol Red Notices

Queries the Interpol public Red Notices database.
FREE - Public Interpol API with no authentication required.

Interpol Red Notices:
    - International arrest warrants
    - Persons wanted by member countries
    - Serious criminal offenses
    - Updated hourly

Data Source:
    https://www.interpol.int/en/How-we-work/Notices/Red-Notices
    API: https://ws-public.interpol.int/notices/v1/red

Coverage:
    - 195 Interpol member countries
    - All publicly disclosed Red Notices

Scoring Implications:
    - Red Notice match = Critical (95+ risk)
    - No match = Positive signal
"""

import logging
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


class InterpolRedNoticesExtractor(ProductionExtractor):
    """
    Queries Interpol public Red Notices API.

    No authentication required - public access.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'notices': [
                {
                    'entity_id': str,
                    'forename': str,
                    'name': str,
                    'date_of_birth': str,
                    'nationalities': [...],
                    'sex': str,
                    'country_of_arrest_warrant': str,
                    'thumbnail_url': str,
                    'link': str,
                }
            ],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "interpol_red_notices"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour (updated hourly)
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # Interpol API endpoints
    API_BASE = "https://ws-public.interpol.int/notices/v1"
    RED_NOTICES_ENDPOINT = "/red"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for InterpolRedNoticesExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []  # No authentication required

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search Interpol Red Notices for an individual."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search by name
            notices = self._search_notices(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"Interpol API error: {e}")

        if not notices:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'notices': [],
                'red_notice_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in Interpol Red Notices',
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(notices)

        data = {
            'searched_term': search_term,
            'total_matches': len(notices),
            'notices': notices[:10],
            'red_notice_hit': True,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.95)

    def _search_notices(self, name: str) -> List[Dict]:
        """Search Interpol Red Notices by name."""
        notices = []

        # Parse name into parts
        name_parts = name.strip().split()

        # Try different search strategies
        search_params = []

        if len(name_parts) >= 2:
            # Assume first is forename, rest is surname
            search_params.append({
                'forename': name_parts[0],
                'name': ' '.join(name_parts[1:]),
            })
            # Also try reversed
            search_params.append({
                'forename': name_parts[-1],
                'name': ' '.join(name_parts[:-1]),
            })
        else:
            # Single name - search as surname
            search_params.append({'name': name})
            search_params.append({'forename': name})

        # Also do a free text search
        search_params.append({'freeText': name})

        seen_ids = set()

        for params in search_params:
            try:
                params['resultPerPage'] = 50

                response = requests.get(
                    f"{self.API_BASE}{self.RED_NOTICES_ENDPOINT}",
                    params=params,
                    headers={
                        'Accept': 'application/json',
                        'User-Agent': 'DSI-Framework/1.0 (security-research)',
                    },
                    timeout=self._timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    embedded = data.get('_embedded', {})
                    results = embedded.get('notices', [])

                    for notice in results:
                        entity_id = notice.get('entity_id', '')
                        if entity_id and entity_id not in seen_ids:
                            seen_ids.add(entity_id)
                            notices.append(self._parse_notice(notice))

            except Exception as e:
                logger.debug(f"Interpol search error for params {params}: {e}")

        return notices

    def _parse_notice(self, notice: Dict) -> Dict:
        """Parse notice data from API response."""
        links = notice.get('_links', {})
        self_link = links.get('self', {}).get('href', '')
        thumbnail = links.get('thumbnail', {}).get('href', '')

        return {
            'entity_id': notice.get('entity_id', ''),
            'forename': notice.get('forename', ''),
            'name': notice.get('name', ''),
            'date_of_birth': notice.get('date_of_birth', ''),
            'nationalities': notice.get('nationalities', []),
            'sex': notice.get('sex', ''),
            'country_of_arrest_warrant': notice.get('country_id', ''),
            'thumbnail_url': thumbnail,
            'link': self_link,
        }

    def _calculate_risk_score(self, notices: List[Dict]) -> float:
        """Calculate risk score from Red Notice matches."""
        if not notices:
            return 0.0

        # Any Red Notice match is critical
        score = 95.0

        # Multiple matches increase concern slightly
        if len(notices) > 1:
            score = min(100.0, score + 3)

        return score
