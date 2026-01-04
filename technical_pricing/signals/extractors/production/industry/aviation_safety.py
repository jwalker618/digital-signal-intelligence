"""
DSI Production Extractor - Aviation Safety Network Database

Searches the Aviation Safety Network (ASN) database for aviation
accidents and incidents.

This is a FREE extractor - ASN is publicly accessible.

Aviation Safety Network:
    - Comprehensive database of aviation accidents since 1919
    - Covers commercial, military, and general aviation
    - Includes hull losses, fatalities, and incident details
    - Maintained by Flight Safety Foundation

Data Source:
    https://aviation-safety.net/

Scoring Implications:
    - Recent fatal accidents = Critical negative
    - Multiple accidents = Major concern
    - Hull losses = Significant concern
    - Minor incidents = Moderate concern
    - Clean record = Positive signal
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


class AviationSafetyExtractor(ProductionExtractor):
    """
    Searches Aviation Safety Network database for accident history.

    Searches by airline name or aircraft registration.

    Output:
        {
            'searched_name': str,
            'accidents_found': int,
            'accidents': [
                {
                    'date': str,
                    'location': str,
                    'aircraft_type': str,
                    'registration': str,
                    'fatalities': int,
                    'hull_loss': bool,
                    'phase_of_flight': str,
                    'description': str,
                }
            ],
            'summary': {
                'total_fatalities': int,
                'hull_losses': int,
                'fatal_accidents': int,
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "aviation_safety"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0  # Be conservative with ASN
    COST_TIER = "free"

    # ASN URLs
    ASN_BASE_URL = "https://aviation-safety.net"
    ASN_SEARCH_URL = f"{ASN_BASE_URL}/database/dblist.php"
    ASN_OPERATOR_URL = f"{ASN_BASE_URL}/database/operator/"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for AviationSafetyExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._lookback_years = config.get('lookback_years', 10) if config else 10

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search ASN for an airline's accident history."""
        airline_name = entity_id.strip()

        if not airline_name:
            return self._create_error_result("Empty airline name provided")

        try:
            accidents = self._search_accidents(airline_name)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"ASN search error: {e}")

        if not accidents:
            return self._create_success_result({
                'searched_name': airline_name,
                'accidents_found': 0,
                'accidents': [],
                'summary': {
                    'total_fatalities': 0,
                    'hull_losses': 0,
                    'fatal_accidents': 0,
                },
                'risk_score': 0.0,
                'note': 'No accidents found in Aviation Safety Network database',
            })

        # Calculate summary
        summary = self._calculate_summary(accidents)

        # Calculate risk score
        risk_score = self._calculate_risk_score(accidents, summary)

        data = {
            'searched_name': airline_name,
            'accidents_found': len(accidents),
            'accidents': accidents[:20],  # Limit response
            'summary': summary,
            'risk_score': round(risk_score, 1),
            'lookback_years': self._lookback_years,
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_accidents(self, airline_name: str) -> List[Dict[str, Any]]:
        """Search ASN for accidents involving an airline."""
        accidents = []

        try:
            # Search the ASN database
            params = {
                'operator': airline_name,
                'sort': 'datekey',
                'order': 'desc',
            }

            response = requests.get(
                self.ASN_SEARCH_URL,
                params=params,
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (aviation-safety-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                accidents = self._parse_search_results(response.text, airline_name)

        except Exception as e:
            logger.debug(f"ASN search error: {e}")

        return accidents

    def _parse_search_results(self, html: str, airline_name: str) -> List[Dict[str, Any]]:
        """Parse accident data from ASN search results."""
        accidents = []
        airline_lower = airline_name.lower()

        # Check if airline is mentioned
        if airline_lower not in html.lower():
            return accidents

        # ASN typically displays results in tables
        # Look for accident entries

        # Pattern for table rows containing accident data
        row_pattern = r'<tr[^>]*class="[^"]*list[^"]*"[^>]*>.*?</tr>'
        rows = re.findall(row_pattern, html, re.IGNORECASE | re.DOTALL)

        for row in rows:
            if airline_lower in row.lower():
                accident = self._parse_accident_row(row)
                if accident:
                    accidents.append(accident)

        # If table parsing fails, try alternative approach
        if not accidents:
            accidents = self._parse_accidents_alternative(html, airline_name)

        return accidents

    def _parse_accident_row(self, row_html: str) -> Optional[Dict[str, Any]]:
        """Parse a single accident row from ASN results."""
        accident = {
            'date': '',
            'location': '',
            'aircraft_type': '',
            'registration': '',
            'operator': '',
            'fatalities': 0,
            'hull_loss': False,
            'phase_of_flight': '',
            'description': '',
        }

        # Extract table cells
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

        if len(cells) >= 4:
            accident['date'] = cells[0] if cells else ''
            accident['aircraft_type'] = cells[1] if len(cells) > 1 else ''
            accident['registration'] = cells[2] if len(cells) > 2 else ''
            accident['location'] = cells[3] if len(cells) > 3 else ''

            # Look for fatality count
            fatality_pattern = r'(\d+)\s*(?:killed|fatal|dead|f)'
            for cell in cells:
                match = re.search(fatality_pattern, cell, re.IGNORECASE)
                if match:
                    accident['fatalities'] = int(match.group(1))
                    break

            # Check for hull loss indicators
            row_lower = row_html.lower()
            if 'hull loss' in row_lower or 'written off' in row_lower or 'destroyed' in row_lower:
                accident['hull_loss'] = True

            return accident

        return None

    def _parse_accidents_alternative(self, html: str, airline_name: str) -> List[Dict[str, Any]]:
        """Alternative parsing method for ASN results."""
        accidents = []

        # Look for accident links/entries
        accident_pattern = r'<a[^>]*href="[^"]*record[^"]*"[^>]*>([^<]+)</a>'
        matches = re.findall(accident_pattern, html, re.IGNORECASE)

        for match in matches:
            if airline_name.lower() in match.lower():
                # Extract date if present
                date_match = re.search(r'(\d{1,2}[- ]\w{3}[- ]\d{4}|\d{4})', match)

                accidents.append({
                    'date': date_match.group(1) if date_match else '',
                    'location': '',
                    'aircraft_type': '',
                    'registration': '',
                    'operator': airline_name,
                    'fatalities': 0,
                    'hull_loss': False,
                    'description': match,
                    'parsed_from_link': True,
                })

        return accidents

    def _calculate_summary(self, accidents: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from accidents."""
        total_fatalities = sum(a.get('fatalities', 0) for a in accidents)
        hull_losses = sum(1 for a in accidents if a.get('hull_loss'))
        fatal_accidents = sum(1 for a in accidents if a.get('fatalities', 0) > 0)

        return {
            'total_accidents': len(accidents),
            'total_fatalities': total_fatalities,
            'hull_losses': hull_losses,
            'fatal_accidents': fatal_accidents,
        }

    def _calculate_risk_score(self, accidents: List[Dict], summary: Dict) -> float:
        """Calculate risk score from accident history."""
        score = 0.0

        # Score based on fatal accidents
        fatal = summary.get('fatal_accidents', 0)
        if fatal >= 3:
            score += 30
        elif fatal >= 1:
            score += 20

        # Score based on total fatalities
        fatalities = summary.get('total_fatalities', 0)
        if fatalities >= 100:
            score += 25
        elif fatalities >= 50:
            score += 20
        elif fatalities >= 10:
            score += 10

        # Score based on hull losses
        hull_losses = summary.get('hull_losses', 0)
        score += min(20, hull_losses * 5)

        # Recency factor
        for accident in accidents[:5]:
            date_str = accident.get('date', '')
            if date_str:
                try:
                    # Try various date formats
                    for fmt in ['%d-%b-%Y', '%d %b %Y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            acc_date = datetime.strptime(date_str, fmt)
                            years_ago = (datetime.utcnow() - acc_date).days / 365
                            if years_ago < 2:
                                score += 15  # Very recent
                            elif years_ago < 5:
                                score += 10  # Recent
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

        return min(100.0, score)
