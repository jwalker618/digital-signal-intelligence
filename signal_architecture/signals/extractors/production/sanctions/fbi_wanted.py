"""
DSI Production Extractor - FBI Most Wanted

Queries the FBI Most Wanted public API.
FREE - Official FBI public API.

FBI Most Wanted Data:
    - Ten Most Wanted Fugitives
    - Fugitives
    - Missing Persons
    - Seeking Information
    - Kidnappings
    - White Collar crimes

Data Source:
    https://www.fbi.gov/wanted
    API: https://api.fbi.gov/

Coverage:
    - United States federal wanted persons
    - International fugitives sought by FBI

Scoring Implications:
    - FBI Most Wanted match = Critical (95+ risk)
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


class FBIMostWantedExtractor(ProductionExtractor):
    """
    Queries FBI Most Wanted public API.

    No authentication required - public access.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'subjects': [
                {
                    'uid': str,
                    'title': str,
                    'description': str,
                    'subjects': [...],
                    'aliases': [...],
                    'nationality': str,
                    'race': str,
                    'sex': str,
                    'dates_of_birth_used': [...],
                    'warning_message': str,
                    'caution': str,
                    'reward_text': str,
                    'url': str,
                }
            ],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "fbi_most_wanted"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # FBI API endpoint
    API_BASE = "https://api.fbi.gov"
    WANTED_ENDPOINT = "/@wanted"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for FBIMostWantedExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search FBI Most Wanted for an individual."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            subjects = self._search_wanted(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"FBI API error: {e}")

        if not subjects:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'subjects': [],
                'fbi_wanted_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in FBI Most Wanted',
            })

        risk_score = self._calculate_risk_score(subjects)

        data = {
            'searched_term': search_term,
            'total_matches': len(subjects),
            'subjects': subjects[:10],
            'fbi_wanted_hit': True,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.95)

    def _search_wanted(self, name: str) -> List[Dict]:
        """Search FBI Most Wanted by name."""
        subjects = []

        try:
            response = requests.get(
                f"{self.API_BASE}{self.WANTED_ENDPOINT}",
                params={
                    'title': name,
                    'pageSize': 20,
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (security-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                for item in items:
                    subject = self._parse_subject(item)
                    if subject:
                        subjects.append(subject)

        except Exception as e:
            logger.debug(f"FBI search error: {e}")

        return subjects

    def _parse_subject(self, item: Dict) -> Optional[Dict]:
        """Parse subject data from API response."""
        return {
            'uid': item.get('uid', ''),
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'subjects': item.get('subjects', []),
            'aliases': item.get('aliases', []),
            'nationality': item.get('nationality', ''),
            'race': item.get('race', ''),
            'sex': item.get('sex', ''),
            'dates_of_birth_used': item.get('dates_of_birth_used', []),
            'warning_message': item.get('warning_message', ''),
            'caution': item.get('caution', ''),
            'reward_text': item.get('reward_text', ''),
            'url': item.get('url', ''),
        }

    def _calculate_risk_score(self, subjects: List[Dict]) -> float:
        """Calculate risk score from FBI matches."""
        if not subjects:
            return 0.0

        score = 95.0

        # Check for reward (indicates high priority)
        for subject in subjects:
            if subject.get('reward_text'):
                score = min(100.0, score + 3)
                break

        return score
