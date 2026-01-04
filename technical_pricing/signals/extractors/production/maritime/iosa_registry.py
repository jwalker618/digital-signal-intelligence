"""
DSI Production Extractor - IATA IOSA Registry

Queries the IATA IOSA (IATA Operational Safety Audit) Registry.
This is a FREE extractor - IOSA Registry is publicly searchable.

IOSA Program:
    - Internationally recognized safety audit program
    - Assesses operational management and control systems
    - Required for IATA membership
    - Voluntary for non-IATA carriers

Data Source:
    https://www.iata.org/en/programs/safety/audit/iosa/registry/

Scoring Implications:
    - IOSA registered = Strong positive signal
    - Registration expired = Concerning
    - Never registered = Moderate concern (for airlines)
    - Multiple renewal cycles = Very positive
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


class IOSARegistryExtractor(ProductionExtractor):
    """
    Queries IATA IOSA Registry for airline safety audit status.

    Searches by airline name, IATA code, or ICAO code.

    Output:
        {
            'searched_term': str,
            'airline_found': bool,
            'airline': {
                'name': str,
                'iata_code': str,
                'icao_code': str,
                'country': str,
            },
            'iosa_status': {
                'is_registered': bool,
                'registration_date': str,
                'expiry_date': str,
                'renewal_count': int,
                'audit_type': str,  # 'IOSA' or 'IOSA Enhanced'
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "iosa_registry"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # IATA IOSA Registry URL
    IOSA_REGISTRY_URL = "https://www.iata.org/en/programs/safety/audit/iosa/registry/"
    IOSA_SEARCH_API = "https://www.iata.org/contentassets/4d9b4b9a50f64f84bbd03cf1cc0e2f9c/iosa-registry.json"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for IOSARegistryExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._registry_cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search IOSA Registry for an airline."""
        search_term = entity_id.strip().upper()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Try to get the registry data
            registry = self._get_registry()

            if registry is None:
                # Fall back to HTML scraping
                result = self._search_registry_html(search_term)
            else:
                result = self._search_registry_json(search_term, registry)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"IOSA Registry search error: {e}")

        if not result:
            return self._create_success_result({
                'searched_term': search_term,
                'airline_found': False,
                'iosa_status': {
                    'is_registered': False,
                },
                'note': 'Airline not found in IOSA Registry (may not be IOSA certified)',
                'risk_score': 30.0,  # Moderate concern for unregistered airlines
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(result)

        data = {
            'searched_term': search_term,
            'airline_found': True,
            'airline': result.get('airline', {}),
            'iosa_status': result.get('iosa_status', {}),
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _get_registry(self) -> Optional[List[Dict]]:
        """Get IOSA registry data (with caching)."""
        # Check cache
        if self._registry_cache and self._cache_time:
            cache_age = (datetime.utcnow() - self._cache_time).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return self._registry_cache

        try:
            response = requests.get(
                self.IOSA_SEARCH_API,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (aviation-safety-research)',
                    'Accept': 'application/json',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                self._registry_cache = data
                self._cache_time = datetime.utcnow()
                return data

        except Exception as e:
            logger.debug(f"Failed to fetch IOSA JSON registry: {e}")

        return None

    def _search_registry_json(
        self, search_term: str, registry: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Search the JSON registry for an airline."""
        search_lower = search_term.lower()

        for entry in registry:
            # Check various fields
            airline_name = entry.get('AirlineName', '').lower()
            iata_code = entry.get('IATACode', '').upper()
            icao_code = entry.get('ICAOCode', '').upper()

            if (search_lower in airline_name or
                search_term == iata_code or
                search_term == icao_code):

                return self._parse_registry_entry(entry)

        return None

    def _parse_registry_entry(self, entry: Dict) -> Dict[str, Any]:
        """Parse a registry entry into our format."""
        # Parse dates
        reg_date = entry.get('RegistrationDate', '')
        exp_date = entry.get('ExpiryDate', '')

        # Determine if currently registered
        is_registered = True
        if exp_date:
            try:
                expiry = datetime.strptime(exp_date, '%Y-%m-%d')
                is_registered = expiry > datetime.utcnow()
            except ValueError:
                try:
                    expiry = datetime.strptime(exp_date, '%d/%m/%Y')
                    is_registered = expiry > datetime.utcnow()
                except ValueError:
                    pass

        return {
            'airline': {
                'name': entry.get('AirlineName', ''),
                'iata_code': entry.get('IATACode', ''),
                'icao_code': entry.get('ICAOCode', ''),
                'country': entry.get('Country', ''),
            },
            'iosa_status': {
                'is_registered': is_registered,
                'registration_date': reg_date,
                'expiry_date': exp_date,
                'renewal_count': entry.get('RenewalCount', 0),
                'audit_type': entry.get('AuditType', 'IOSA'),
            },
        }

    def _search_registry_html(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Search the HTML registry page (fallback)."""
        try:
            response = requests.get(
                self.IOSA_REGISTRY_URL,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (aviation-safety-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_registry_html(response.text, search_term)

        except Exception as e:
            logger.debug(f"IOSA HTML search error: {e}")

        return None

    def _parse_registry_html(self, html: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Parse airline data from IOSA registry HTML."""
        search_lower = search_term.lower()

        # Check if airline is mentioned
        if search_lower not in html.lower():
            return None

        # Try to find the table row containing the airline
        # IATA typically uses table structure for registry

        # Look for table rows
        row_pattern = r'<tr[^>]*>.*?</tr>'
        rows = re.findall(row_pattern, html, re.IGNORECASE | re.DOTALL)

        for row in rows:
            if search_lower in row.lower():
                return self._parse_airline_row(row)

        return None

    def _parse_airline_row(self, row_html: str) -> Optional[Dict[str, Any]]:
        """Parse a single airline row from the registry."""
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

        if len(cells) >= 4:
            # Typical structure: Airline Name, IATA Code, ICAO Code, Country, Dates

            # Try to find dates
            reg_date = ''
            exp_date = ''
            for cell in cells:
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', cell)
                if date_match:
                    if not reg_date:
                        reg_date = date_match.group(1)
                    else:
                        exp_date = date_match.group(1)

            return {
                'airline': {
                    'name': cells[0] if cells else '',
                    'iata_code': cells[1] if len(cells) > 1 else '',
                    'icao_code': cells[2] if len(cells) > 2 else '',
                    'country': cells[3] if len(cells) > 3 else '',
                },
                'iosa_status': {
                    'is_registered': True,
                    'registration_date': reg_date,
                    'expiry_date': exp_date,
                    'renewal_count': 0,  # Can't determine from HTML easily
                    'audit_type': 'IOSA',
                },
            }

        return None

    def _calculate_risk_score(self, result: Dict) -> float:
        """Calculate risk score from IOSA status."""
        score = 0.0

        iosa_status = result.get('iosa_status', {})

        # Registration status
        if not iosa_status.get('is_registered'):
            score += 30  # Expired or not registered

        # Check expiry proximity
        exp_date = iosa_status.get('expiry_date', '')
        if exp_date:
            try:
                for fmt in ['%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        expiry = datetime.strptime(exp_date, fmt)
                        days_until = (expiry - datetime.utcnow()).days

                        if days_until < 0:
                            score += 25  # Expired
                        elif days_until < 30:
                            score += 15  # Expiring soon
                        elif days_until < 90:
                            score += 5   # Approaching expiry
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        # Renewal history (more renewals = more established)
        renewals = iosa_status.get('renewal_count', 0)
        if renewals >= 5:
            score -= 10  # Very established, reduce risk
        elif renewals >= 3:
            score -= 5   # Established

        # If registered and not expiring, that's positive
        if iosa_status.get('is_registered'):
            score -= 10  # Being IOSA registered is positive

        return max(0.0, min(100.0, score))
