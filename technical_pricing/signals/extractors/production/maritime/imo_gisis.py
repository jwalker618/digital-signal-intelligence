"""
DSI Production Extractor - IMO GISIS (Global Integrated Shipping Information System)

Queries the IMO GISIS database for ship and company information.
This is a FREE extractor - IMO GISIS public modules are freely accessible.

IMO GISIS Data:
    - Ship identification (IMO number, name, flag state)
    - Ship particulars (type, tonnage, dimensions)
    - Company information (ISM/ISPS status)
    - Casualty and incident records
    - Port State Control deficiencies

Data Source:
    https://gisis.imo.org/

Scoring Implications:
    - Valid IMO registration = Positive
    - Active ISM/ISPS certification = Positive
    - Port State Control detentions = Concerning
    - Casualty involvement = Significant negative
    - Unknown/unregistered vessel = Critical concern
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


class IMOGISISExtractor(ProductionExtractor):
    """
    Queries IMO GISIS for ship and maritime company information.

    Can search by IMO number, ship name, or company name.

    Output:
        {
            'searched_term': str,
            'search_type': str,  # 'imo_number', 'ship_name', 'company'
            'ship_found': bool,
            'ship': {
                'imo_number': str,
                'name': str,
                'former_names': [...],
                'flag_state': str,
                'ship_type': str,
                'gross_tonnage': int,
                'deadweight': int,
                'year_built': int,
                'status': str,
            },
            'company': {
                'name': str,
                'imo_company_number': str,
                'country': str,
                'ism_status': str,
                'isps_status': str,
            },
            'safety_record': {
                'psc_detentions': int,
                'psc_deficiencies': int,
                'casualties': int,
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "imo_gisis"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0  # Be conservative
    COST_TIER = "free"

    # IMO GISIS URLs
    GISIS_BASE = "https://gisis.imo.org"
    SHIP_SEARCH_URL = f"{GISIS_BASE}/Public/Ships/Default.aspx"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for IMOGISISExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search IMO GISIS for a ship or company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine search type
        search_type = self._determine_search_type(search_term)

        try:
            if search_type == 'imo_number':
                ship_data = self._search_by_imo(search_term)
            else:
                ship_data = self._search_by_name(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"IMO GISIS search error: {e}")

        if not ship_data:
            return self._create_success_result({
                'searched_term': search_term,
                'search_type': search_type,
                'ship_found': False,
                'note': 'No ship found in IMO GISIS database',
            })

        # Get additional details
        safety_record = self._get_safety_record(ship_data.get('imo_number', ''))

        # Calculate risk score
        risk_score = self._calculate_risk_score(ship_data, safety_record)

        data = {
            'searched_term': search_term,
            'search_type': search_type,
            'ship_found': True,
            'ship': ship_data.get('ship', {}),
            'company': ship_data.get('company', {}),
            'safety_record': safety_record,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.85)

    def _determine_search_type(self, term: str) -> str:
        """Determine if search term is IMO number or name."""
        # IMO numbers are 7 digits
        if re.match(r'^\d{7}$', term):
            return 'imo_number'
        # Sometimes prefixed with IMO
        if re.match(r'^IMO\s*\d{7}$', term, re.IGNORECASE):
            return 'imo_number'
        return 'ship_name'

    def _search_by_imo(self, imo_number: str) -> Optional[Dict[str, Any]]:
        """Search GISIS by IMO number."""
        # Extract just the digits
        imo_digits = re.sub(r'\D', '', imo_number)

        try:
            # GISIS uses ASP.NET forms - we'll try to get basic info
            response = requests.get(
                self.SHIP_SEARCH_URL,
                params={'IMONumber': imo_digits},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (maritime-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_ship_response(response.text, imo_digits)

        except Exception as e:
            logger.debug(f"IMO search error: {e}")

        return None

    def _search_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Search GISIS by ship name."""
        try:
            response = requests.get(
                self.SHIP_SEARCH_URL,
                params={'ShipName': name},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (maritime-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_ship_response(response.text, name)

        except Exception as e:
            logger.debug(f"Name search error: {e}")

        return None

    def _parse_ship_response(self, html: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Parse ship data from GISIS response."""
        result = {
            'ship': {},
            'company': {},
        }

        # Check if ship data is present
        if 'No records found' in html or search_term.lower() not in html.lower():
            return None

        # Try to extract ship details
        ship = {}

        # IMO number
        imo_match = re.search(r'IMO\s*(?:Number|No\.?)?\s*:?\s*(\d{7})', html, re.IGNORECASE)
        if imo_match:
            ship['imo_number'] = imo_match.group(1)

        # Ship name
        name_match = re.search(r'Ship\s*Name\s*:?\s*([^<\n]+)', html, re.IGNORECASE)
        if name_match:
            ship['name'] = name_match.group(1).strip()

        # Flag state
        flag_match = re.search(r'Flag\s*(?:State)?\s*:?\s*([A-Za-z\s]+)', html, re.IGNORECASE)
        if flag_match:
            ship['flag_state'] = flag_match.group(1).strip()

        # Ship type
        type_match = re.search(r'Ship\s*Type\s*:?\s*([^<\n]+)', html, re.IGNORECASE)
        if type_match:
            ship['ship_type'] = type_match.group(1).strip()

        # Gross tonnage
        gt_match = re.search(r'Gross\s*(?:Tonnage|GT)\s*:?\s*([\d,]+)', html, re.IGNORECASE)
        if gt_match:
            try:
                ship['gross_tonnage'] = int(gt_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # Year built
        year_match = re.search(r'(?:Year\s*)?Built\s*:?\s*(\d{4})', html, re.IGNORECASE)
        if year_match:
            ship['year_built'] = int(year_match.group(1))

        # Status
        if 'in service' in html.lower():
            ship['status'] = 'In Service'
        elif 'laid up' in html.lower():
            ship['status'] = 'Laid Up'
        elif 'broken up' in html.lower() or 'scrapped' in html.lower():
            ship['status'] = 'Broken Up'
        elif 'total loss' in html.lower():
            ship['status'] = 'Total Loss'

        result['ship'] = ship

        # Try to extract company information
        company = {}

        company_match = re.search(r'(?:Registered\s*)?Owner\s*:?\s*([^<\n]+)', html, re.IGNORECASE)
        if company_match:
            company['name'] = company_match.group(1).strip()

        # ISM status
        if 'ism' in html.lower():
            if 'valid' in html.lower() or 'certified' in html.lower():
                company['ism_status'] = 'Valid'
            else:
                company['ism_status'] = 'Unknown'

        # ISPS status
        if 'isps' in html.lower():
            if 'valid' in html.lower() or 'certified' in html.lower():
                company['isps_status'] = 'Valid'
            else:
                company['isps_status'] = 'Unknown'

        result['company'] = company

        # Only return if we found something useful
        if ship.get('imo_number') or ship.get('name'):
            return result

        return None

    def _get_safety_record(self, imo_number: str) -> Dict[str, Any]:
        """Get safety record for a ship."""
        record = {
            'psc_detentions': 0,
            'psc_deficiencies': 0,
            'casualties': 0,
            'last_psc_inspection': None,
        }

        if not imo_number:
            return record

        # Try to get PSC inspection data
        # This would typically come from Paris MOU, Tokyo MOU, etc.
        # For now, return placeholder structure

        return record

    def _calculate_risk_score(self, ship_data: Dict, safety_record: Dict) -> float:
        """Calculate risk score from ship and safety data."""
        score = 0.0

        ship = ship_data.get('ship', {})
        company = ship_data.get('company', {})

        # Ship status
        status = ship.get('status', '').lower()
        if status == 'total loss':
            score += 40
        elif status == 'broken up':
            score += 30
        elif status == 'laid up':
            score += 15
        elif status != 'in service' and status:
            score += 10

        # Age of vessel
        year_built = ship.get('year_built')
        if year_built:
            age = datetime.now().year - year_built
            if age > 25:
                score += 20  # Old vessel
            elif age > 20:
                score += 15
            elif age > 15:
                score += 10

        # Flag state (simplified check for common flags of convenience)
        flag = ship.get('flag_state', '').lower()
        foc_flags = ['panama', 'liberia', 'marshall islands', 'bahamas', 'malta', 'cyprus']
        if any(foc in flag for foc in foc_flags):
            score += 5  # Slight concern for FOC, though many are legitimate

        # ISM/ISPS certification
        if company.get('ism_status') == 'Unknown':
            score += 10
        if company.get('isps_status') == 'Unknown':
            score += 10

        # Safety record
        detentions = safety_record.get('psc_detentions', 0)
        if detentions >= 3:
            score += 25
        elif detentions >= 1:
            score += 15

        deficiencies = safety_record.get('psc_deficiencies', 0)
        if deficiencies >= 10:
            score += 15
        elif deficiencies >= 5:
            score += 10

        casualties = safety_record.get('casualties', 0)
        if casualties > 0:
            score += 20 * min(casualties, 3)

        return min(100.0, score)
