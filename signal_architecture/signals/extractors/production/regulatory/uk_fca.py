"""
DSI Production Extractor - UK Financial Conduct Authority (FCA) Register

Queries the UK FCA Financial Services Register.
FREE - Public FCA database.

FCA Register Data:
    - Authorized firms and individuals
    - Permissions and regulated activities
    - Appointed representatives
    - EEA passported firms
    - Enforcement actions and warnings

Data Source:
    https://register.fca.org.uk/
    API: https://register.fca.org.uk/services/

Coverage:
    - All FCA-authorized firms in UK
    - Individuals approved to perform controlled functions
    - Unauthorized firms warnings

Scoring Implications:
    - FCA authorized = Positive
    - Permissions withdrawn = Critical
    - Enforcement action = High concern
    - On warning list = Critical
    - Not found = May not need FCA authorization
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


class UKFCARegisterExtractor(ProductionExtractor):
    """
    Queries UK FCA Financial Services Register.

    Searches for authorized firms and individuals.

    Output:
        {
            'searched_term': str,
            'firm_found': bool,
            'firms': [
                {
                    'frn': str,  # Firm Reference Number
                    'name': str,
                    'status': str,
                    'status_effective_date': str,
                    'address': str,
                    'website': str,
                    'phone': str,
                    'permissions': [...],
                    'appointed_representatives': int,
                }
            ],
            'warnings': [...],  # Unauthorized firm warnings
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "uk_fca_register"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # FCA Register endpoints
    FCA_SEARCH_URL = "https://register.fca.org.uk/s/search"
    FCA_API_URL = "https://register.fca.org.uk/services/V0.1"
    FCA_WARNING_URL = "https://www.fca.org.uk/consumers/warning-list-unauthorised-firms"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for UKFCARegisterExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search FCA Register for a firm or individual."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Check if FRN (Firm Reference Number)
        is_frn = search_term.isdigit() and len(search_term) <= 8

        try:
            if is_frn:
                firms = self._search_by_frn(search_term)
            else:
                firms = self._search_by_name(search_term)

            # Also check warning list
            warnings = self._check_warning_list(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"FCA Register error: {e}")

        if not firms and not warnings:
            return self._create_success_result({
                'searched_term': search_term,
                'firm_found': False,
                'firms': [],
                'warnings': [],
                'risk_score': 10.0,  # Not being on FCA may be fine
                'note': 'Not found on FCA Register (may not require FCA authorization)',
            })

        risk_score = self._calculate_risk_score(firms, warnings)

        data = {
            'searched_term': search_term,
            'firm_found': len(firms) > 0,
            'firms': firms[:10],
            'total_firms': len(firms),
            'warnings': warnings,
            'on_warning_list': len(warnings) > 0,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_by_frn(self, frn: str) -> List[Dict]:
        """Search by Firm Reference Number."""
        firms = []

        try:
            response = requests.get(
                f"{self.FCA_API_URL}/Firm/{frn}",
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (financial-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                firm = self._parse_firm(data)
                if firm:
                    firms.append(firm)

        except Exception as e:
            logger.debug(f"FCA FRN search error: {e}")

        return firms

    def _search_by_name(self, name: str) -> List[Dict]:
        """Search by firm name."""
        firms = []

        try:
            # Try the search API
            response = requests.get(
                self.FCA_SEARCH_URL,
                params={
                    'q': name,
                    'type': 'firms',
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (financial-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                # Parse HTML or JSON response
                content_type = response.headers.get('content-type', '')

                if 'json' in content_type:
                    data = response.json()
                    results = data.get('results', data.get('firms', []))
                    for result in results:
                        firm = self._parse_firm(result)
                        if firm:
                            firms.append(firm)
                else:
                    # Parse HTML for firm data
                    firms = self._parse_html_results(response.text, name)

        except Exception as e:
            logger.debug(f"FCA name search error: {e}")

        return firms

    def _parse_firm(self, data: Dict) -> Optional[Dict]:
        """Parse firm data from API response."""
        firm = {
            'frn': str(data.get('FRN', data.get('frn', data.get('firmReferenceNumber', '')))),
            'name': data.get('Name', data.get('name', data.get('organisationName', ''))),
            'status': data.get('Status', data.get('status', data.get('currentStatus', ''))),
            'status_effective_date': data.get('StatusEffectiveDate', data.get('effectiveDate', '')),
            'address': data.get('Address', data.get('address', '')),
            'website': data.get('Website', data.get('website', '')),
            'phone': data.get('Phone', data.get('phone', '')),
        }

        # Get permissions if available
        permissions = data.get('Permissions', data.get('permissions', []))
        if isinstance(permissions, list):
            firm['permissions'] = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in permissions[:10]]
        else:
            firm['permissions'] = []

        firm['appointed_representatives'] = data.get('AppointedRepresentatives', 0)

        return firm if firm.get('frn') or firm.get('name') else None

    def _parse_html_results(self, html: str, query: str) -> List[Dict]:
        """Parse firm data from HTML search results."""
        firms = []

        # Look for FRN patterns
        frn_pattern = r'FRN[:\s]*(\d{6,8})'
        frns = re.findall(frn_pattern, html)

        # Look for firm names near FRNs
        name_pattern = r'<[^>]*>([^<]*' + re.escape(query[:10]) + r'[^<]*)</[^>]*>'
        names = re.findall(name_pattern, html, re.IGNORECASE)

        for i, frn in enumerate(frns[:10]):
            firm = {
                'frn': frn,
                'name': names[i] if i < len(names) else '',
                'status': 'Found on Register',
                'permissions': [],
            }
            firms.append(firm)

        return firms

    def _check_warning_list(self, name: str) -> List[Dict]:
        """Check FCA warning list for unauthorized firms."""
        warnings = []

        try:
            response = requests.get(
                self.FCA_WARNING_URL,
                params={'q': name},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (financial-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                html = response.text.lower()
                name_lower = name.lower()

                if name_lower in html:
                    # Found on warning list
                    warnings.append({
                        'firm_name': name,
                        'warning_type': 'Unauthorized firm',
                        'note': 'Appears on FCA warning list',
                    })

        except Exception as e:
            logger.debug(f"FCA warning check error: {e}")

        return warnings

    def _calculate_risk_score(self, firms: List[Dict], warnings: List[Dict]) -> float:
        """Calculate risk score from FCA data."""
        score = 0.0

        # Warning list is critical
        if warnings:
            score += 80

        if firms:
            top_firm = firms[0]
            status = (top_firm.get('status') or '').lower()

            if 'authorised' in status or 'authorized' in status:
                score += 0  # Good
            elif 'no longer authorised' in status or 'cancelled' in status:
                score += 50  # Permissions withdrawn
            elif 'appointed representative' in status:
                score += 5  # Generally OK
            else:
                score += 10

        return max(0.0, min(100.0, score))
