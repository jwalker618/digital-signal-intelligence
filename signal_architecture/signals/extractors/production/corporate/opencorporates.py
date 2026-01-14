"""
DSI Production Extractor - OpenCorporates

Queries the OpenCorporates database - the largest open database of companies.
FREE for non-commercial/open data use - 235M+ companies in 145 jurisdictions.

OpenCorporates Coverage:
    - United States (all states)
    - United Kingdom
    - European Union countries
    - Canada (federal + provinces)
    - Australia
    - And 140+ more jurisdictions

Data Available:
    - Company name and registration number
    - Incorporation date and jurisdiction
    - Company status (active, dissolved, etc.)
    - Registered address
    - Officers and directors
    - Previous names
    - Branch relationships

Data Source:
    https://opencorporates.com/
    API: https://api.opencorporates.com/

Scoring Implications:
    - Company found and active = Positive
    - Company dissolved/struck off = Concerning
    - No record found = Moderate concern (may be unregistered)
    - Multiple jurisdictions = Neutral to positive
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


class OpenCorporatesExtractor(ProductionExtractor):
    """
    Queries OpenCorporates for company information across 145 jurisdictions.

    Free API access for non-commercial use. API key optional but recommended.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'companies': [
                {
                    'name': str,
                    'company_number': str,
                    'jurisdiction_code': str,
                    'jurisdiction': str,
                    'incorporation_date': str,
                    'dissolution_date': str,
                    'company_type': str,
                    'status': str,
                    'registered_address': str,
                    'opencorporates_url': str,
                    'officers': [...],
                    'previous_names': [...],
                }
            ],
            'jurisdictions_found': [...],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "opencorporates"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0  # Conservative for free tier
    COST_TIER = "free"

    # OpenCorporates API
    API_BASE = "https://api.opencorporates.com/v0.4"
    SEARCH_ENDPOINT = "/companies/search"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for OpenCorporatesExtractor. "
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
        """Search OpenCorporates for a company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Optional jurisdiction filter
        jurisdiction = kwargs.get('jurisdiction', None)

        try:
            companies = self._search_companies(search_term, jurisdiction)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"OpenCorporates API error: {e}")

        if not companies:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'companies': [],
                'jurisdictions_found': [],
                'company_found': False,
                'risk_score': 25.0,  # Slight concern for unregistered entity
                'note': 'No matching companies found in OpenCorporates',
            })

        # Get unique jurisdictions
        jurisdictions = list(set(c.get('jurisdiction', '') for c in companies if c.get('jurisdiction')))

        # Calculate risk score
        risk_score = self._calculate_risk_score(companies)

        data = {
            'searched_term': search_term,
            'total_matches': len(companies),
            'companies': companies[:10],  # Top 10 matches
            'jurisdictions_found': jurisdictions,
            'company_found': True,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_companies(
        self, query: str, jurisdiction: Optional[str] = None
    ) -> List[Dict]:
        """Search OpenCorporates for companies."""
        params = {
            'q': query,
            'per_page': 30,
            'order': 'score',
        }

        if jurisdiction:
            params['jurisdiction_code'] = jurisdiction

        if self._api_key:
            params['api_token'] = self._api_key

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DSI-Framework/1.0 (corporate-research)',
        }

        try:
            response = requests.get(
                f"{self.API_BASE}{self.SEARCH_ENDPOINT}",
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', {}).get('companies', [])

                companies = []
                for result in results:
                    company_data = result.get('company', {})
                    company = self._parse_company(company_data)
                    if company:
                        companies.append(company)

                return companies

            elif response.status_code == 401:
                logger.warning("OpenCorporates API key invalid or missing")
                return []

            elif response.status_code == 429:
                logger.warning("OpenCorporates rate limit reached")
                return []

            else:
                logger.debug(f"OpenCorporates search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.debug(f"OpenCorporates search error: {e}")
            return []

    def _parse_company(self, data: Dict) -> Optional[Dict]:
        """Parse company data from API response."""
        if not data:
            return None

        company = {
            'name': data.get('name', ''),
            'company_number': data.get('company_number', ''),
            'jurisdiction_code': data.get('jurisdiction_code', ''),
            'jurisdiction': self._get_jurisdiction_name(data.get('jurisdiction_code', '')),
            'incorporation_date': data.get('incorporation_date', ''),
            'dissolution_date': data.get('dissolution_date', ''),
            'company_type': data.get('company_type', ''),
            'status': data.get('current_status', data.get('status', '')),
            'registered_address': self._format_address(data.get('registered_address', {})),
            'opencorporates_url': data.get('opencorporates_url', ''),
        }

        # Get officers if available
        officers = []
        for officer in data.get('officers', [])[:5]:
            officer_data = officer.get('officer', {})
            officers.append({
                'name': officer_data.get('name', ''),
                'position': officer_data.get('position', ''),
                'start_date': officer_data.get('start_date', ''),
            })
        company['officers'] = officers

        # Get previous names if available
        previous_names = []
        for name_change in data.get('previous_names', [])[:3]:
            previous_names.append(name_change.get('company_name', ''))
        company['previous_names'] = previous_names

        return company if company.get('name') else None

    def _get_jurisdiction_name(self, code: str) -> str:
        """Convert jurisdiction code to human-readable name."""
        jurisdictions = {
            'us': 'United States',
            'us_de': 'Delaware, USA',
            'us_ca': 'California, USA',
            'us_ny': 'New York, USA',
            'us_tx': 'Texas, USA',
            'gb': 'United Kingdom',
            'ca': 'Canada',
            'ca_on': 'Ontario, Canada',
            'ca_bc': 'British Columbia, Canada',
            'au': 'Australia',
            'de': 'Germany',
            'fr': 'France',
            'nl': 'Netherlands',
            'ie': 'Ireland',
            'lu': 'Luxembourg',
            'ch': 'Switzerland',
            'sg': 'Singapore',
            'hk': 'Hong Kong',
            'jp': 'Japan',
            'nz': 'New Zealand',
        }
        return jurisdictions.get(code.lower(), code.upper())

    def _format_address(self, address: Dict) -> str:
        """Format address dictionary to string."""
        if isinstance(address, str):
            return address

        parts = []
        for field in ['street_address', 'locality', 'region', 'postal_code', 'country']:
            if address.get(field):
                parts.append(address[field])

        return ', '.join(parts) if parts else ''

    def _calculate_risk_score(self, companies: List[Dict]) -> float:
        """Calculate risk score from company data."""
        if not companies:
            return 25.0  # No record is slight concern

        score = 0.0
        top_company = companies[0]

        # Check status
        status = (top_company.get('status') or '').lower()
        if 'active' in status or 'good standing' in status:
            score += 0  # Active is good
        elif 'dissolved' in status or 'struck' in status or 'liquidat' in status:
            score += 40  # Dissolved is concerning
        elif 'inactive' in status or 'dormant' in status:
            score += 20  # Inactive is moderate concern
        else:
            score += 10  # Unknown status

        # Check incorporation date (very new companies may be higher risk)
        inc_date = top_company.get('incorporation_date', '')
        if inc_date:
            try:
                inc_dt = datetime.strptime(inc_date, '%Y-%m-%d')
                age_days = (datetime.now() - inc_dt).days
                if age_days < 90:
                    score += 15  # Very new
                elif age_days < 365:
                    score += 10  # Less than a year
                elif age_days > 365 * 10:
                    score -= 5  # Established company
            except ValueError:
                pass

        # Check jurisdiction (some are higher risk)
        jurisdiction = (top_company.get('jurisdiction_code') or '').lower()
        high_risk_jurisdictions = ['vg', 'ky', 'bz', 'pa', 'sc', 'ws']  # Tax havens
        if jurisdiction in high_risk_jurisdictions:
            score += 15

        # Name changes can indicate issues
        if len(top_company.get('previous_names', [])) > 2:
            score += 10

        return max(0.0, min(100.0, score))
