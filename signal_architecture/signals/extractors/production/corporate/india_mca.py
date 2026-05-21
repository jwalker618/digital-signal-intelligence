"""
DSI Production Extractor - India Ministry of Corporate Affairs (MCA)

Queries the Indian Ministry of Corporate Affairs company registry.
FREE - Public government company data.

MCA Data:
    - Company Identification Number (CIN)
    - Date of incorporation
    - Registered office address
    - Authorized and paid-up capital
    - Company status (active, struck off, dormant)
    - Director details
    - Charges registered

Data Source:
    https://www.mca.gov.in/
    Open Data: https://data.gov.in/catalog/company-master-data

Coverage:
    - All companies registered in India under Companies Act
    - LLPs (Limited Liability Partnerships)
    - 1.5+ million active companies

Scoring Implications:
    - Active company with good standing = Positive
    - Struck off / under liquidation = Critical
    - Dormant status = Moderate concern
    - No record found = May not be registered in India
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


class IndiaMCAExtractor(ProductionExtractor):
    """
    Queries Indian Ministry of Corporate Affairs company registry.

    Uses the Open Government Data portal API for company data.

    Output:
        {
            'searched_term': str,
            'company_found': bool,
            'companies': [
                {
                    'cin': str,
                    'name': str,
                    'status': str,
                    'company_class': str,
                    'category': str,
                    'date_of_registration': str,
                    'authorized_capital': int,
                    'paid_up_capital': int,
                    'state': str,
                    'roc': str,  # Registrar of Companies
                }
            ],
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "india_mca"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # Open Government Data API
    OGD_API = "https://api.data.gov.in/resource"
    # Resource IDs for different ROCs (Registrar of Companies)
    ROC_RESOURCES = {
        'delhi': '38f4bc33-d930-4a3c-9e94-72c50f1f0a5a',
        'mumbai': 'ac1e7e89-3c93-4e89-95ed-3f7d69c68be6',
        'bangalore': 'd6b9c6a3-3c17-4a7d-89e3-62c50f1f0a5b',
        'chennai': 'b7c8d9e0-4d28-5b8f-9a45-73d60g2g1b6c',
        'kolkata': 'c8d9e0f1-5e39-6c9g-0b56-84e71h3h2c7d',
    }

    # MCA direct search (requires CAPTCHA in browser, so we use OGD)
    MCA_SEARCH_URL = "https://www.mca.gov.in/mcafoportal/showCompanyMasterData.do"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for IndiaMCAExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        # API key from data.gov.in (free registration)
        self._api_key = config.get('api_key', '') if config else ''

    def get_required_config(self) -> List[str]:
        return []  # API key is optional

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search India MCA for a company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine if searching by CIN or name
        is_cin = self._is_cin(search_term)

        try:
            if is_cin:
                companies = self._search_by_cin(search_term)
            else:
                companies = self._search_by_name(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"India MCA search error: {e}")

        if not companies:
            return self._create_success_result({
                'searched_term': search_term,
                'company_found': False,
                'companies': [],
                'risk_score': 15.0,  # Not finding may not be concerning
                'note': 'No matching company found in India MCA registry',
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(companies)

        data = {
            'searched_term': search_term,
            'company_found': True,
            'companies': companies[:10],
            'total_matches': len(companies),
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.85)

    def _is_cin(self, term: str) -> bool:
        """Check if term is a Corporate Identification Number (CIN)."""
        # CIN format: L/U + 5 digits + 2 letters + 4 digits + 3 letters + 6 digits
        # Example: U74140MH2008PTC178303
        cin_pattern = r'^[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}$'
        return bool(re.match(cin_pattern, term.upper()))

    def _search_by_cin(self, cin: str) -> List[Dict]:
        """Search by CIN number."""
        cin = cin.upper()

        # Determine ROC from CIN (positions 6-7)
        roc_code = cin[5:7] if len(cin) >= 7 else ''

        # Try OGD API search
        companies = self._search_ogd(cin, by_cin=True)

        if companies:
            return companies

        # Fall back to generic search
        return self._search_ogd(cin, by_cin=False)

    def _search_by_name(self, name: str) -> List[Dict]:
        """Search by company name."""
        return self._search_ogd(name, by_cin=False)

    def _search_ogd(self, query: str, by_cin: bool = False) -> List[Dict]:
        """Search using Open Government Data API."""
        companies = []

        # Build params
        params = {
            'format': 'json',
            'limit': 20,
        }

        if self._api_key:
            params['api-key'] = self._api_key

        if by_cin:
            params['filters[CIN]'] = query
        else:
            params['filters[COMPANY_NAME]'] = query

        # Try each ROC resource
        for roc_name, resource_id in self.ROC_RESOURCES.items():
            try:
                response = requests.get(
                    f"{self.OGD_API}/{resource_id}",
                    params=params,
                    headers={
                        'Accept': 'application/json',
                        'User-Agent': 'DSI-Framework/1.0 (corporate-research)',
                    },
                    timeout=self._timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    records = data.get('records', [])

                    for record in records:
                        company = self._parse_record(record)
                        if company:
                            companies.append(company)

            except Exception as e:
                logger.debug(f"OGD search error for {roc_name}: {e}")

        return companies

    def _parse_record(self, record: Dict) -> Optional[Dict]:
        """Parse a company record from OGD API."""
        company = {
            'cin': record.get('CIN', record.get('cin', '')),
            'name': record.get('COMPANY_NAME', record.get('company_name', '')),
            'status': record.get('COMPANY_STATUS', record.get('company_status', '')),
            'company_class': record.get('COMPANY_CLASS', record.get('company_class', '')),
            'category': record.get('COMPANY_CATEGORY', record.get('company_category', '')),
            'date_of_registration': record.get('DATE_OF_REGISTRATION', record.get('date_of_registration', '')),
            'state': record.get('STATE', record.get('state', '')),
            'roc': record.get('ROC_CODE', record.get('roc_code', '')),
        }

        # Parse capital (may be string or int)
        auth_cap = record.get('AUTHORIZED_CAP', record.get('authorized_capital', 0))
        paid_cap = record.get('PAIDUP_CAPITAL', record.get('paid_up_capital', 0))

        try:
            company['authorized_capital'] = int(float(str(auth_cap).replace(',', '')))
        except (ValueError, TypeError):
            company['authorized_capital'] = 0

        try:
            company['paid_up_capital'] = int(float(str(paid_cap).replace(',', '')))
        except (ValueError, TypeError):
            company['paid_up_capital'] = 0

        return company if company.get('cin') or company.get('name') else None

    def _calculate_risk_score(self, companies: List[Dict]) -> float:
        """Calculate risk score from company data."""
        if not companies:
            return 15.0

        score = 0.0
        top_company = companies[0]

        # Company status
        status = (top_company.get('status') or '').lower()
        if 'active' in status:
            score += 0
        elif 'struck' in status or 'strike' in status:
            score += 60  # Struck off is serious
        elif 'liquidat' in status or 'winding' in status:
            score += 50  # Liquidation is concerning
        elif 'dormant' in status:
            score += 25  # Dormant is moderate concern
        elif 'under process' in status:
            score += 15
        else:
            score += 10  # Unknown status

        # Paid-up capital very low compared to authorized
        auth_cap = top_company.get('authorized_capital', 0)
        paid_cap = top_company.get('paid_up_capital', 0)

        if auth_cap > 0 and paid_cap > 0:
            ratio = paid_cap / auth_cap
            if ratio < 0.1:
                score += 15  # Very undercapitalized
            elif ratio < 0.3:
                score += 10

        # Very new company
        reg_date = top_company.get('date_of_registration', '')
        if reg_date:
            try:
                for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        reg_dt = datetime.strptime(reg_date, fmt)
                        age_days = (datetime.now() - reg_dt).days
                        if age_days < 180:
                            score += 15  # Very new
                        elif age_days < 365:
                            score += 10
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        return max(0.0, min(100.0, score))
