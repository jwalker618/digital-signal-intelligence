"""
DSI Production Extractor - PCAOB Registered Firm Status

Checks the PCAOB (Public Company Accounting Oversight Board) registered
firm database for auditor standing and enforcement history.

This is a FREE extractor - PCAOB data is public.

PCAOB Data:
    - Registered accounting firm status
    - Registration date and jurisdiction
    - Inspection reports and deficiencies
    - Enforcement actions and sanctions
    - Issuer audit clients

Data Source:
    https://pcaobus.org/registration/firms

Scoring Implications:
    - Active registration = Required for public company audits
    - Recent inspection deficiencies = Concerning
    - Enforcement actions = Critical negative
    - Revoked/suspended = Critical negative
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


class PCAOBExtractor(ProductionExtractor):
    """
    Checks PCAOB registered firm database.

    Searches for accounting firms and returns registration status,
    inspection history, and enforcement actions.

    Output:
        {
            'searched_name': str,
            'firm_found': bool,
            'firm': {
                'name': str,
                'id': str,
                'status': str,  # 'Registered', 'Revoked', etc.
                'registration_date': str,
                'headquarters': str,
                'country': str,
            },
            'inspections': {
                'last_inspection': str,
                'total_inspections': int,
                'deficiencies_found': bool,
            },
            'enforcement': {
                'actions': int,
                'sanctions': [...],
            },
            'issuer_clients': int,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "pcaob"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # PCAOB website URLs
    FIRM_SEARCH_URL = "https://pcaobus.org/registration/firms"
    FIRM_API_URL = "https://pcaobus.org/api/Registration/Firms"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for PCAOBExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search PCAOB for a firm."""
        firm_name = entity_id.strip()

        if not firm_name:
            return self._create_error_result("Empty firm name provided")

        try:
            firm_data = self._search_firm(firm_name)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"PCAOB search error: {e}")

        if not firm_data:
            return self._create_success_result({
                'searched_name': firm_name,
                'firm_found': False,
                'note': 'No PCAOB registered firm found with this name',
            }, confidence=0.80)

        # Get additional details if available
        enforcement = self._get_enforcement_history(firm_data.get('id'))
        inspections = self._get_inspection_history(firm_data.get('id'))

        # Calculate risk score
        risk_score = self._calculate_risk_score(firm_data, enforcement, inspections)

        data = {
            'searched_name': firm_name,
            'firm_found': True,
            'firm': firm_data,
            'inspections': inspections,
            'enforcement': enforcement,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _search_firm(self, firm_name: str) -> Optional[Dict[str, Any]]:
        """Search for a firm in PCAOB database."""
        # Try the API first
        try:
            params = {
                'search': firm_name,
                'pageSize': 10,
                'page': 1,
            }

            response = requests.get(
                self.FIRM_API_URL,
                params=params,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (audit-research)',
                    'Accept': 'application/json',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                firms = data.get('items', data.get('results', []))

                if firms:
                    # Return best match
                    best_match = self._find_best_match(firms, firm_name)
                    if best_match:
                        return self._parse_firm(best_match)

        except Exception as e:
            logger.debug(f"PCAOB API search failed: {e}")

        # Fallback to scraping the search page
        return self._search_firm_fallback(firm_name)

    def _search_firm_fallback(self, firm_name: str) -> Optional[Dict[str, Any]]:
        """Fallback search using web scraping."""
        try:
            response = requests.get(
                self.FIRM_SEARCH_URL,
                params={'search': firm_name},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (audit-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_search_results(response.text, firm_name)

        except Exception as e:
            logger.debug(f"PCAOB fallback search failed: {e}")

        return None

    def _find_best_match(self, firms: List[Dict], search_name: str) -> Optional[Dict]:
        """Find the best matching firm from search results."""
        search_lower = search_name.lower()

        for firm in firms:
            firm_name = firm.get('name', firm.get('firmName', '')).lower()
            if search_lower in firm_name or firm_name in search_lower:
                return firm

        # Return first result if no exact match
        return firms[0] if firms else None

    def _parse_firm(self, firm: Dict) -> Dict[str, Any]:
        """Parse firm data from API response."""
        return {
            'name': firm.get('name', firm.get('firmName', '')),
            'id': firm.get('id', firm.get('firmId', '')),
            'status': firm.get('status', firm.get('registrationStatus', 'Unknown')),
            'registration_date': firm.get('registrationDate', firm.get('effectiveDate', '')),
            'headquarters': firm.get('headquarters', firm.get('city', '')),
            'state': firm.get('state', ''),
            'country': firm.get('country', firm.get('countryName', 'USA')),
            'is_active': firm.get('status', '').lower() == 'registered',
            'issuer_clients': firm.get('issuerAuditClients', firm.get('numberOfIssuerClients', 0)),
        }

    def _parse_search_results(self, html: str, firm_name: str) -> Optional[Dict[str, Any]]:
        """Parse firm data from HTML search results."""
        # Look for firm entries in the HTML
        # This is a simplified parser

        # Try to find firm name pattern
        name_pattern = rf'<[^>]*>([^<]*{re.escape(firm_name[:20])}[^<]*)</[^>]*>'
        name_match = re.search(name_pattern, html, re.IGNORECASE)

        if name_match:
            # Try to extract registration status
            status = 'Unknown'
            if 'registered' in html.lower():
                status = 'Registered'
            elif 'revoked' in html.lower():
                status = 'Revoked'

            return {
                'name': name_match.group(1).strip(),
                'id': '',
                'status': status,
                'registration_date': '',
                'headquarters': '',
                'country': 'USA',
                'is_active': status == 'Registered',
                'parsed_from_html': True,
            }

        return None

    def _get_enforcement_history(self, firm_id: str) -> Dict[str, Any]:
        """Get enforcement actions against a firm."""
        enforcement = {
            'actions': 0,
            'sanctions': [],
            'has_actions': False,
        }

        if not firm_id:
            return enforcement

        try:
            # PCAOB enforcement search
            url = f"https://pcaobus.org/api/Enforcement/SearchActions"
            params = {'firmId': firm_id}

            response = requests.get(
                url,
                params=params,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (audit-research)',
                    'Accept': 'application/json',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                actions = data.get('items', [])

                enforcement['actions'] = len(actions)
                enforcement['has_actions'] = len(actions) > 0

                for action in actions[:5]:
                    enforcement['sanctions'].append({
                        'date': action.get('orderDate', ''),
                        'type': action.get('actionType', ''),
                        'description': action.get('description', '')[:200],
                    })

        except Exception as e:
            logger.debug(f"Enforcement lookup failed: {e}")

        return enforcement

    def _get_inspection_history(self, firm_id: str) -> Dict[str, Any]:
        """Get inspection reports for a firm."""
        inspections = {
            'total_inspections': 0,
            'last_inspection': None,
            'deficiencies_found': False,
            'reports': [],
        }

        if not firm_id:
            return inspections

        try:
            # PCAOB inspection reports
            url = f"https://pcaobus.org/api/Inspections/Reports"
            params = {'firmId': firm_id}

            response = requests.get(
                url,
                params=params,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (audit-research)',
                    'Accept': 'application/json',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                reports = data.get('items', [])

                inspections['total_inspections'] = len(reports)

                if reports:
                    # Get most recent
                    latest = max(reports, key=lambda r: r.get('reportDate', ''))
                    inspections['last_inspection'] = latest.get('reportDate', '')

                    # Check for deficiencies
                    for report in reports:
                        if report.get('hasDeficiencies') or report.get('deficiencyCitations', 0) > 0:
                            inspections['deficiencies_found'] = True

                        inspections['reports'].append({
                            'date': report.get('reportDate', ''),
                            'year': report.get('inspectionYear', ''),
                            'has_deficiencies': report.get('hasDeficiencies', False),
                        })

        except Exception as e:
            logger.debug(f"Inspection lookup failed: {e}")

        return inspections

    def _calculate_risk_score(
        self,
        firm: Dict,
        enforcement: Dict,
        inspections: Dict
    ) -> float:
        """Calculate risk score for the auditor."""
        score = 0.0

        # Registration status
        status = firm.get('status', '').lower()
        if status == 'revoked':
            score += 50
        elif status == 'suspended':
            score += 40
        elif status != 'registered':
            score += 20

        # Enforcement actions
        actions = enforcement.get('actions', 0)
        score += min(30, actions * 15)

        # Inspection deficiencies
        if inspections.get('deficiencies_found'):
            score += 15

        # No recent inspections may be a flag
        last_inspection = inspections.get('last_inspection')
        if last_inspection:
            try:
                insp_date = datetime.strptime(last_inspection[:10], '%Y-%m-%d')
                years_since = (datetime.utcnow() - insp_date).days / 365
                if years_since > 4:
                    score += 10
            except ValueError:
                pass

        return min(100.0, score)
