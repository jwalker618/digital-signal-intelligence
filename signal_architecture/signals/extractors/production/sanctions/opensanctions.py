"""
DSI Production Extractor - OpenSanctions

Queries the OpenSanctions consolidated sanctions database.
FREE for non-commercial use - covers 85+ global sanctions sources.

OpenSanctions consolidates:
    - UN Security Council sanctions
    - US OFAC SDN/Consolidated lists
    - UK OFSI sanctions
    - EU Financial Sanctions
    - World Bank debarred entities
    - National sanctions from 50+ countries
    - PEP (Politically Exposed Persons) lists
    - Wanted lists and criminal databases

Data Source:
    https://www.opensanctions.org/
    API: https://api.opensanctions.org/

Scoring Implications:
    - Match on consolidated sanctions = Critical (80-100 risk)
    - Match on PEP list = High concern (50-70 risk)
    - Match on crime/wanted = Critical (70-90 risk)
    - No matches = Positive signal (0 risk from this source)
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


class OpenSanctionsExtractor(ProductionExtractor):
    """
    Queries OpenSanctions API for consolidated global sanctions data.

    Covers 85+ data sources including UN, US, UK, EU sanctions.
    Free for non-commercial use.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'matches': [
                {
                    'id': str,
                    'caption': str,
                    'schema': str,  # 'Person', 'Company', 'Organization'
                    'score': float,  # Match confidence 0-1
                    'datasets': [...],  # Source lists
                    'properties': {...},
                    'first_seen': str,
                    'last_seen': str,
                }
            ],
            'datasets_checked': [...],
            'sanctions_hit': bool,
            'pep_hit': bool,
            'crime_hit': bool,
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "opensanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 2.0  # Conservative rate limit
    COST_TIER = "free"

    # OpenSanctions API
    API_BASE = "https://api.opensanctions.org"
    MATCH_ENDPOINT = "/match/default"
    SEARCH_ENDPOINT = "/search/default"

    # Dataset categories
    SANCTIONS_DATASETS = [
        'un_sc_sanctions', 'us_ofac_sdn', 'us_ofac_cons', 'eu_fsf',
        'gb_hmt_sanctions', 'au_dfat_sanctions', 'ca_dfatd_sema_sanctions',
        'ch_seco_sanctions', 'jp_mof_sanctions', 'ua_nsdc_sanctions',
    ]
    PEP_DATASETS = [
        'everypolitician', 'wd_peps', 'ru_rupep', 'ua_nazk_pep',
    ]
    CRIME_DATASETS = [
        'interpol_red_notices', 'us_fbi_most_wanted', 'eu_most_wanted',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for OpenSanctionsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        # API key is optional but increases rate limits
        self._api_key = None
        if config:
            self._api_key = config.get('api_key')

    def get_required_config(self) -> List[str]:
        return []  # API key is optional

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search OpenSanctions for an entity."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine entity type hint if provided
        schema = kwargs.get('schema', None)  # 'Person', 'Company', 'Organization'

        try:
            # Use match API for better fuzzy matching
            matches = self._search_entity(search_term, schema)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"OpenSanctions API error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'sanctions_hit': False,
                'pep_hit': False,
                'crime_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in OpenSanctions database',
            })

        # Analyze matches
        sanctions_hit = False
        pep_hit = False
        crime_hit = False

        for match in matches:
            datasets = match.get('datasets', [])
            for ds in datasets:
                if ds in self.SANCTIONS_DATASETS or 'sanction' in ds.lower():
                    sanctions_hit = True
                if ds in self.PEP_DATASETS or 'pep' in ds.lower():
                    pep_hit = True
                if ds in self.CRIME_DATASETS or 'wanted' in ds.lower():
                    crime_hit = True

        # Calculate risk score
        risk_score = self._calculate_risk_score(matches, sanctions_hit, pep_hit, crime_hit)

        # Get unique datasets
        all_datasets = set()
        for match in matches:
            all_datasets.update(match.get('datasets', []))

        data = {
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],  # Limit to top 10
            'datasets_checked': list(all_datasets),
            'sanctions_hit': sanctions_hit,
            'pep_hit': pep_hit,
            'crime_hit': crime_hit,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _search_entity(self, query: str, schema: Optional[str] = None) -> List[Dict]:
        """Search OpenSanctions for an entity."""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DSI-Framework/1.0 (sanctions-screening)',
        }

        if self._api_key:
            headers['Authorization'] = f'Bearer {self._api_key}'

        params = {
            'q': query,
            'limit': 25,
        }

        if schema:
            params['schema'] = schema

        try:
            response = requests.get(
                f"{self.API_BASE}{self.SEARCH_ENDPOINT}",
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])

                # Parse results
                matches = []
                for result in results:
                    match = {
                        'id': result.get('id', ''),
                        'caption': result.get('caption', ''),
                        'schema': result.get('schema', ''),
                        'score': result.get('score', 0),
                        'datasets': result.get('datasets', []),
                        'properties': result.get('properties', {}),
                        'first_seen': result.get('first_seen', ''),
                        'last_seen': result.get('last_seen', ''),
                    }
                    matches.append(match)

                return matches

            elif response.status_code == 429:
                logger.warning("OpenSanctions rate limit reached")
                return []

            else:
                logger.debug(f"OpenSanctions search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.debug(f"OpenSanctions search error: {e}")
            return []

    def _calculate_risk_score(
        self,
        matches: List[Dict],
        sanctions_hit: bool,
        pep_hit: bool,
        crime_hit: bool
    ) -> float:
        """Calculate risk score from matches."""
        if not matches:
            return 0.0

        score = 0.0

        # Base score from match quality
        top_match_score = matches[0].get('score', 0) if matches else 0

        # Sanctions are most critical
        if sanctions_hit:
            score += 60 + (top_match_score * 30)  # 60-90 range

        # Crime/wanted lists are very serious
        if crime_hit:
            score += 50 + (top_match_score * 25)  # 50-75 range

        # PEP is a concern but not always disqualifying
        if pep_hit and not sanctions_hit:
            score += 30 + (top_match_score * 20)  # 30-50 range

        # Multiple matches increase concern
        if len(matches) > 5:
            score += 10
        elif len(matches) > 2:
            score += 5

        # Cap at 100
        return min(100.0, score)
