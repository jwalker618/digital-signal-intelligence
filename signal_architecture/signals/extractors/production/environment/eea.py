"""
DSI Production Extractor - European Environment Agency (EEA)

Queries the European Environment Agency's environmental databases.
FREE - Public EU environmental data.

EEA Data Coverage:
    - Industrial emissions (E-PRTR)
    - Air quality data
    - Water quality indicators
    - Climate/emissions data
    - Environmental compliance

Data Source:
    https://www.eea.europa.eu/en/datahub
    API: https://www.eea.europa.eu/code/api

Geographic Coverage:
    - 38 EEA member/cooperating countries
    - EU-27 member states
    - EEA countries (Iceland, Liechtenstein, Norway)
    - Cooperating countries (Switzerland, Turkey, etc.)

Scoring Implications:
    - Clean compliance record = Positive
    - E-PRTR reported releases = Depends on volumes
    - Exceedances or violations = Concerning
    - No data = Neutral (may not be industrial facility)
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


class EEAEnvironmentExtractor(ProductionExtractor):
    """
    Queries EEA environmental databases for facility/company data.

    Searches E-PRTR (European Pollutant Release and Transfer Register)
    and other EEA data sources.

    Output:
        {
            'searched_term': str,
            'facility_found': bool,
            'facilities': [
                {
                    'name': str,
                    'country': str,
                    'city': str,
                    'sector': str,
                    'reporting_year': int,
                    'releases': {...},
                }
            ],
            'total_facilities': int,
            'countries': [...],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "eea_environment"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # EEA API endpoints
    EEA_API_BASE = "https://www.eea.europa.eu/api"
    EPRTR_SPARQL = "http://semantic.eea.europa.eu/sparql"
    DISCOMAP_API = "https://discomap.eea.europa.eu/arcgis/rest/services"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for EEAEnvironmentExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search EEA databases for a facility/company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search E-PRTR database
            facilities = self._search_eprtr(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"EEA search error: {e}")

        if not facilities:
            return self._create_success_result({
                'searched_term': search_term,
                'facility_found': False,
                'facilities': [],
                'total_facilities': 0,
                'risk_score': 0.0,
                'note': 'No facilities found in E-PRTR database (may not be EU industrial facility)',
            })

        # Get unique countries
        countries = list(set(f.get('country', '') for f in facilities if f.get('country')))

        # Calculate risk score
        risk_score = self._calculate_risk_score(facilities)

        data = {
            'searched_term': search_term,
            'facility_found': True,
            'facilities': facilities[:10],
            'total_facilities': len(facilities),
            'countries': countries,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.80)

    def _search_eprtr(self, name: str) -> List[Dict]:
        """Search E-PRTR database for facilities."""
        facilities = []

        # Try SPARQL query
        sparql_results = self._query_sparql(name)
        if sparql_results:
            facilities.extend(sparql_results)

        # Try REST API search
        if not facilities:
            api_results = self._search_eea_api(name)
            facilities.extend(api_results)

        return facilities

    def _query_sparql(self, name: str) -> List[Dict]:
        """Query EEA SPARQL endpoint for E-PRTR data."""
        # E-PRTR SPARQL query
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX eprtr: <http://prtr.ec.europa.eu/schema/>

        SELECT DISTINCT ?facility ?name ?country ?city ?sector ?year
        WHERE {{
            ?facility a eprtr:Facility .
            ?facility rdfs:label ?name .
            FILTER (CONTAINS(LCASE(?name), LCASE("{name}")))
            OPTIONAL {{ ?facility eprtr:countryCode ?country }}
            OPTIONAL {{ ?facility eprtr:city ?city }}
            OPTIONAL {{ ?facility eprtr:mainActivityCode ?sector }}
            OPTIONAL {{ ?facility eprtr:reportingYear ?year }}
        }}
        LIMIT 20
        """

        try:
            response = requests.get(
                self.EPRTR_SPARQL,
                params={
                    'query': query,
                    'format': 'application/json',
                },
                headers={
                    'Accept': 'application/sparql-results+json',
                    'User-Agent': 'DSI-Framework/1.0 (environmental-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                bindings = data.get('results', {}).get('bindings', [])

                facilities = []
                for b in bindings:
                    facility = {
                        'name': b.get('name', {}).get('value', ''),
                        'country': b.get('country', {}).get('value', ''),
                        'city': b.get('city', {}).get('value', ''),
                        'sector': b.get('sector', {}).get('value', ''),
                        'reporting_year': int(b.get('year', {}).get('value', 0) or 0),
                    }
                    if facility['name']:
                        facilities.append(facility)

                return facilities

        except Exception as e:
            logger.debug(f"SPARQL query error: {e}")

        return []

    def _search_eea_api(self, name: str) -> List[Dict]:
        """Search EEA REST API."""
        try:
            # Try EEA content search
            response = requests.get(
                f"{self.EEA_API_BASE}/SITE/en/search",
                params={
                    'q': name,
                    'portal_type': 'Data',
                    'b_size': 20,
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (environmental-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                facilities = []
                for item in items:
                    if 'facility' in item.get('title', '').lower() or name.lower() in item.get('description', '').lower():
                        facilities.append({
                            'name': item.get('title', ''),
                            'country': '',
                            'city': '',
                            'sector': item.get('subject', [''])[0] if item.get('subject') else '',
                            'reporting_year': 0,
                            'description': item.get('description', ''),
                        })

                return facilities

        except Exception as e:
            logger.debug(f"EEA API search error: {e}")

        return []

    def _calculate_risk_score(self, facilities: List[Dict]) -> float:
        """Calculate risk score from facility data."""
        if not facilities:
            return 0.0

        score = 0.0

        # Multiple facilities suggests significant industrial presence
        if len(facilities) > 5:
            score += 15
        elif len(facilities) > 2:
            score += 10

        # Check for high-risk sectors
        high_risk_sectors = [
            'chemical', 'refiner', 'mineral', 'metal',
            'waste', 'power', 'cement', 'steel',
        ]

        for facility in facilities:
            sector = (facility.get('sector') or '').lower()
            if any(hs in sector for hs in high_risk_sectors):
                score += 5
                break

        # Recent reporting is actually positive (compliance)
        recent_years = [f.get('reporting_year', 0) for f in facilities]
        current_year = datetime.now().year
        if recent_years and max(recent_years) >= current_year - 2:
            score -= 5  # Recent reporting is good

        return max(0.0, min(100.0, score))
