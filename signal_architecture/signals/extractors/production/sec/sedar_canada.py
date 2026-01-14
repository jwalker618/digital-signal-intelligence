"""
DSI Production Extractor - SEDAR+ Canada

Queries the Canadian Securities Administrators SEDAR+ system.
FREE - Public Canadian securities filings database.

SEDAR+ Data:
    - Securities disclosure documents
    - Financial statements and annual reports
    - Material change reports
    - Insider reports
    - Prospectuses and offering documents
    - Cease trade orders
    - Disciplined persons list

Data Source:
    https://www.sedarplus.ca/
    Replaces legacy SEDAR, SEDI, CTO, and NRD systems

Coverage:
    - All Canadian public companies
    - Investment funds
    - Exempt market issuers
    - Foreign issuers with Canadian presence

Scoring Implications:
    - Active filer with recent filings = Positive
    - Cease trade order = Critical
    - Late/deficient filings = Concerning
    - No filings found = Moderate concern
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class SEDARCanadaExtractor(ProductionExtractor):
    """
    Queries SEDAR+ for Canadian securities filings information.

    Searches for issuers and their filings on the public SEDAR+ system.

    Output:
        {
            'searched_term': str,
            'issuer_found': bool,
            'issuer': {
                'name': str,
                'sedar_id': str,
                'jurisdiction': str,
                'status': str,
                'issuer_type': str,
            },
            'filings': [
                {
                    'type': str,
                    'date': str,
                    'description': str,
                }
            ],
            'cease_trade_orders': [...],
            'last_filing_date': str,
            'filing_frequency': str,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "sedar_canada"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # SEDAR+ URLs
    SEDAR_BASE = "https://www.sedarplus.ca"
    SEARCH_API = f"{SEDAR_BASE}/csa-party/search/party"
    FILINGS_API = f"{SEDAR_BASE}/csa-document/search/document"
    CTO_API = f"{SEDAR_BASE}/cto/search/order"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for SEDARCanadaExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search SEDAR+ for a Canadian issuer."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search for issuer
            issuer = self._search_issuer(search_term)

            if not issuer:
                return self._create_success_result({
                    'searched_term': search_term,
                    'issuer_found': False,
                    'risk_score': 25.0,
                    'note': 'No issuer found in SEDAR+ (may not be Canadian public issuer)',
                })

            # Get filings
            filings = self._get_filings(issuer.get('sedar_id', ''))

            # Check for cease trade orders
            cto_orders = self._check_cease_trade_orders(search_term)

            # Analyze filing frequency
            filing_analysis = self._analyze_filings(filings)

            # Calculate risk score
            risk_score = self._calculate_risk_score(issuer, filings, cto_orders, filing_analysis)

            data = {
                'searched_term': search_term,
                'issuer_found': True,
                'issuer': issuer,
                'filings': filings[:20],  # Most recent 20
                'cease_trade_orders': cto_orders,
                'last_filing_date': filing_analysis.get('last_filing_date'),
                'filing_frequency': filing_analysis.get('frequency'),
                'risk_score': round(risk_score, 1),
            }

            return self._create_success_result(data, confidence=0.85)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"SEDAR+ search error: {e}")

    def _search_issuer(self, name: str) -> Optional[Dict]:
        """Search SEDAR+ for an issuer by name."""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DSI-Framework/1.0 (securities-research)',
        }

        # SEDAR+ uses a specific search format
        params = {
            'keyword': name,
            'partyType': 'ISSUER',
            'size': 10,
        }

        try:
            response = requests.get(
                self.SEARCH_API,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('content', data.get('results', []))

                if results:
                    # Return best match
                    match = results[0]
                    return {
                        'name': match.get('partyName', match.get('name', '')),
                        'sedar_id': match.get('partyId', match.get('id', '')),
                        'jurisdiction': match.get('jurisdiction', ''),
                        'status': match.get('status', ''),
                        'issuer_type': match.get('issuerType', match.get('type', '')),
                    }

        except Exception as e:
            logger.debug(f"SEDAR+ issuer search error: {e}")

        # Fall back to HTML search
        return self._search_issuer_html(name)

    def _search_issuer_html(self, name: str) -> Optional[Dict]:
        """Fall back to HTML search on SEDAR+ website."""
        try:
            search_url = f"{self.SEDAR_BASE}/csa-party/search?keyword={requests.utils.quote(name)}"

            response = requests.get(
                search_url,
                headers={'User-Agent': 'DSI-Framework/1.0 (securities-research)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                html = response.text

                # Look for issuer in results
                name_match = re.search(r'partyName["\']?\s*:\s*["\']([^"\']+)', html)
                id_match = re.search(r'partyId["\']?\s*:\s*["\']?(\d+)', html)

                if name_match:
                    return {
                        'name': name_match.group(1),
                        'sedar_id': id_match.group(1) if id_match else '',
                        'jurisdiction': '',
                        'status': 'Found',
                        'issuer_type': '',
                    }

        except Exception as e:
            logger.debug(f"SEDAR+ HTML search error: {e}")

        return None

    def _get_filings(self, sedar_id: str) -> List[Dict]:
        """Get recent filings for an issuer."""
        if not sedar_id:
            return []

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DSI-Framework/1.0 (securities-research)',
        }

        params = {
            'partyId': sedar_id,
            'size': 50,
            'sort': 'filingDate,desc',
        }

        try:
            response = requests.get(
                self.FILINGS_API,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('content', data.get('results', []))

                filings = []
                for doc in results:
                    filings.append({
                        'type': doc.get('documentType', doc.get('type', '')),
                        'date': doc.get('filingDate', doc.get('date', '')),
                        'description': doc.get('description', doc.get('title', '')),
                    })

                return filings

        except Exception as e:
            logger.debug(f"SEDAR+ filings error: {e}")

        return []

    def _check_cease_trade_orders(self, name: str) -> List[Dict]:
        """Check for cease trade orders against an issuer."""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DSI-Framework/1.0 (securities-research)',
        }

        params = {
            'keyword': name,
            'size': 10,
        }

        try:
            response = requests.get(
                self.CTO_API,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('content', data.get('results', []))

                orders = []
                for order in results:
                    orders.append({
                        'issuer_name': order.get('issuerName', ''),
                        'order_date': order.get('orderDate', ''),
                        'order_type': order.get('orderType', ''),
                        'jurisdiction': order.get('jurisdiction', ''),
                        'status': order.get('status', ''),
                    })

                return orders

        except Exception as e:
            logger.debug(f"SEDAR+ CTO check error: {e}")

        return []

    def _analyze_filings(self, filings: List[Dict]) -> Dict[str, Any]:
        """Analyze filing patterns."""
        if not filings:
            return {
                'last_filing_date': None,
                'frequency': 'No filings',
                'days_since_last': None,
            }

        # Get most recent filing date
        last_filing = filings[0].get('date', '')
        days_since_last = None

        if last_filing:
            try:
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d-%m-%Y']:
                    try:
                        last_dt = datetime.strptime(last_filing[:10], fmt)
                        days_since_last = (datetime.now() - last_dt).days
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Determine frequency
        if len(filings) >= 4:
            frequency = 'Regular'
        elif len(filings) >= 2:
            frequency = 'Occasional'
        else:
            frequency = 'Minimal'

        if days_since_last and days_since_last > 365:
            frequency = 'Inactive'

        return {
            'last_filing_date': last_filing,
            'frequency': frequency,
            'days_since_last': days_since_last,
        }

    def _calculate_risk_score(
        self,
        issuer: Dict,
        filings: List[Dict],
        cto_orders: List[Dict],
        filing_analysis: Dict
    ) -> float:
        """Calculate risk score from SEDAR+ data."""
        score = 0.0

        # Cease trade orders are critical
        if cto_orders:
            active_cto = any(o.get('status', '').lower() in ['active', 'in effect'] for o in cto_orders)
            if active_cto:
                score += 70  # Active CTO is very serious
            else:
                score += 30  # Historical CTO is concerning

        # Filing recency
        days_since = filing_analysis.get('days_since_last')
        if days_since is not None:
            if days_since > 365:
                score += 25  # No filings in a year
            elif days_since > 180:
                score += 15  # No filings in 6 months
            elif days_since > 90:
                score += 5   # No filings in 3 months

        # Filing frequency
        frequency = filing_analysis.get('frequency', '')
        if frequency == 'Inactive':
            score += 20
        elif frequency == 'Minimal':
            score += 10

        # No filings at all
        if not filings:
            score += 25

        # Issuer status
        status = (issuer.get('status') or '').lower()
        if 'ceased' in status or 'inactive' in status:
            score += 30

        return min(100.0, score)
