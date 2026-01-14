"""
DSI Production Extractor - UK Companies House

Queries the UK Companies House registry for company information.
This is a FREE extractor - Companies House has a free API.

Companies House Data:
    - Company registration details
    - Director/officer information
    - Filing history
    - Accounts status
    - Charges (mortgages/security interests)
    - Insolvency history

API Documentation:
    https://developer.company-information.service.gov.uk/

API Key:
    Free API key available from Companies House Developer Hub
    Rate limit: 600 requests per 5 minutes without key

Scoring Implications:
    - Active company = Positive
    - Recent filings = Positive
    - Late filings = Concerning
    - Insolvency proceedings = Critical negative
    - Dissolved/struck off = Critical negative
"""

import logging
import base64
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


class CompaniesHouseExtractor(ProductionExtractor):
    """
    Queries UK Companies House for company information.

    Uses the Companies House API to retrieve registration and filing data.

    Output:
        {
            'searched_name': str,
            'company_found': bool,
            'company': {
                'name': str,
                'number': str,
                'status': str,
                'type': str,
                'incorporated_date': str,
                'address': str,
                'sic_codes': [...],
            },
            'officers': {
                'count': int,
                'active_directors': int,
            },
            'filings': {
                'last_accounts': str,
                'next_accounts_due': str,
                'overdue': bool,
            },
            'charges': {
                'count': int,
                'outstanding': int,
            },
            'insolvency': {
                'has_insolvency_history': bool,
                'cases': [...],
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "companies_house"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 2.0  # 600 per 5 min = 2/sec
    COST_TIER = "free"

    # Companies House API
    API_BASE = "https://api.company-information.service.gov.uk"
    SEARCH_URL = f"{API_BASE}/search/companies"
    COMPANY_URL = f"{API_BASE}/company"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for CompaniesHouseExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._api_key = config.get('companies_house_api_key') if config else None

    def get_required_config(self) -> List[str]:
        return []  # API key is optional

    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication header for API requests."""
        headers = {
            'User-Agent': 'DSI-Framework/1.0 (company-research)',
        }

        if self._api_key:
            # Companies House uses API key as username with blank password
            auth = base64.b64encode(f"{self._api_key}:".encode()).decode()
            headers['Authorization'] = f'Basic {auth}'

        return headers

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search Companies House for a company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search for company
            company = self._search_company(search_term)

            if not company:
                return self._create_success_result({
                    'searched_name': search_term,
                    'company_found': False,
                    'note': 'No UK company found with this name',
                })

            # Get detailed information
            company_number = company.get('company_number')
            details = self._get_company_details(company_number)
            officers = self._get_officers(company_number)
            charges = self._get_charges(company_number)
            insolvency = self._get_insolvency(company_number)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"Companies House API error: {e}")

        # Calculate risk score
        risk_score = self._calculate_risk_score(details, officers, charges, insolvency)

        data = {
            'searched_name': search_term,
            'company_found': True,
            'company': details,
            'officers': officers,
            'charges': charges,
            'insolvency': insolvency,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.95)

    def _search_company(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for a company by name."""
        response = requests.get(
            self.SEARCH_URL,
            params={'q': name, 'items_per_page': 10},
            headers=self._get_auth_header(),
            timeout=self._timeout,
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])

            if items:
                # Return best match (first active company or first result)
                for item in items:
                    if item.get('company_status') == 'active':
                        return item
                return items[0]

        return None

    def _get_company_details(self, company_number: str) -> Dict[str, Any]:
        """Get detailed company information."""
        response = requests.get(
            f"{self.COMPANY_URL}/{company_number}",
            headers=self._get_auth_header(),
            timeout=self._timeout,
        )

        if response.status_code == 200:
            data = response.json()

            # Parse address
            address_parts = []
            registered_office = data.get('registered_office_address', {})
            for field in ['address_line_1', 'address_line_2', 'locality', 'region', 'postal_code', 'country']:
                if registered_office.get(field):
                    address_parts.append(registered_office[field])

            # Parse accounts
            accounts = data.get('accounts', {})
            last_accounts = accounts.get('last_accounts', {})
            next_due = accounts.get('next_due')
            overdue = accounts.get('overdue', False)

            return {
                'name': data.get('company_name', ''),
                'number': company_number,
                'status': data.get('company_status', ''),
                'type': data.get('type', ''),
                'incorporated_date': data.get('date_of_creation', ''),
                'address': ', '.join(address_parts),
                'sic_codes': data.get('sic_codes', []),
                'has_charges': data.get('has_charges', False),
                'has_insolvency_history': data.get('has_insolvency_history', False),
                'accounts': {
                    'last_made_up_to': last_accounts.get('made_up_to'),
                    'next_due': next_due,
                    'overdue': overdue,
                },
                'confirmation_statement': {
                    'next_due': data.get('confirmation_statement', {}).get('next_due'),
                    'overdue': data.get('confirmation_statement', {}).get('overdue', False),
                },
            }

        return {'number': company_number}

    def _get_officers(self, company_number: str) -> Dict[str, Any]:
        """Get officer information."""
        result = {
            'count': 0,
            'active_directors': 0,
            'resigned_count': 0,
            'officers': [],
        }

        try:
            response = requests.get(
                f"{self.COMPANY_URL}/{company_number}/officers",
                headers=self._get_auth_header(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                result['count'] = len(items)

                for officer in items[:10]:  # Limit
                    is_active = officer.get('resigned_on') is None

                    if is_active and officer.get('officer_role') in ['director', 'corporate-director']:
                        result['active_directors'] += 1
                    elif not is_active:
                        result['resigned_count'] += 1

                    result['officers'].append({
                        'name': officer.get('name', ''),
                        'role': officer.get('officer_role', ''),
                        'appointed': officer.get('appointed_on', ''),
                        'resigned': officer.get('resigned_on'),
                        'is_active': is_active,
                    })

        except Exception as e:
            logger.debug(f"Officer lookup failed: {e}")

        return result

    def _get_charges(self, company_number: str) -> Dict[str, Any]:
        """Get charges (mortgages/security interests)."""
        result = {
            'count': 0,
            'outstanding': 0,
            'satisfied': 0,
            'charges': [],
        }

        try:
            response = requests.get(
                f"{self.COMPANY_URL}/{company_number}/charges",
                headers=self._get_auth_header(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                result['count'] = len(items)

                for charge in items[:10]:
                    status = charge.get('status', '')

                    if status == 'outstanding':
                        result['outstanding'] += 1
                    elif status in ['fully-satisfied', 'part-satisfied']:
                        result['satisfied'] += 1

                    result['charges'].append({
                        'status': status,
                        'created': charge.get('created_on', ''),
                        'delivered': charge.get('delivered_on', ''),
                        'persons_entitled': charge.get('persons_entitled', []),
                    })

        except Exception as e:
            logger.debug(f"Charges lookup failed: {e}")

        return result

    def _get_insolvency(self, company_number: str) -> Dict[str, Any]:
        """Get insolvency information."""
        result = {
            'has_insolvency_history': False,
            'cases': [],
        }

        try:
            response = requests.get(
                f"{self.COMPANY_URL}/{company_number}/insolvency",
                headers=self._get_auth_header(),
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                cases = data.get('cases', [])

                result['has_insolvency_history'] = len(cases) > 0

                for case in cases[:5]:
                    result['cases'].append({
                        'type': case.get('type', ''),
                        'dates': case.get('dates', []),
                        'practitioners': [
                            p.get('name') for p in case.get('practitioners', [])
                        ],
                    })

        except Exception as e:
            logger.debug(f"Insolvency lookup failed: {e}")

        return result

    def _calculate_risk_score(
        self,
        details: Dict,
        officers: Dict,
        charges: Dict,
        insolvency: Dict
    ) -> float:
        """Calculate risk score for the company."""
        score = 0.0

        # Company status
        status = details.get('status', '').lower()
        if status == 'dissolved':
            score += 50
        elif status == 'liquidation':
            score += 45
        elif status == 'administration':
            score += 40
        elif status == 'receivership':
            score += 40
        elif status != 'active':
            score += 20

        # Accounts status
        accounts = details.get('accounts', {})
        if accounts.get('overdue'):
            score += 15

        confirmation = details.get('confirmation_statement', {})
        if confirmation.get('overdue'):
            score += 10

        # Officers
        if officers.get('active_directors', 0) == 0:
            score += 20  # No active directors is concerning

        # Insolvency
        if insolvency.get('has_insolvency_history'):
            score += 25
            score += min(15, len(insolvency.get('cases', [])) * 5)

        # Charges (not necessarily negative, but many outstanding can be)
        outstanding = charges.get('outstanding', 0)
        if outstanding > 10:
            score += 10
        elif outstanding > 5:
            score += 5

        return min(100.0, score)
