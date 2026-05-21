"""
DSI Production Extractor - BSEE Incident Data

Queries the Bureau of Safety and Environmental Enforcement (BSEE) incident
database for offshore drilling safety incidents.

This is a FREE extractor - BSEE data is public.

BSEE Data:
    - Offshore oil and gas incidents on the Outer Continental Shelf
    - Injuries, fatalities, fires, explosions, collisions
    - Pollution events and spills
    - Equipment failures

Data Source:
    https://www.bsee.gov/stats-facts/offshore-incident-statistics

Scoring Implications:
    - Fatalities = Critical negative
    - Major pollution events = Critical negative
    - Multiple incidents = Concerning
    - Clean record = Positive (for offshore operators)
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


class BSEEIncidentExtractor(ProductionExtractor):
    """
    Searches BSEE incident database for offshore drilling incidents.

    Searches by operator name or lease number.

    Output:
        {
            'searched_name': str,
            'incidents_found': int,
            'incidents': [
                {
                    'date': str,
                    'incident_type': str,
                    'location': str,
                    'injuries': int,
                    'fatalities': int,
                    'pollution': bool,
                    'description': str,
                }
            ],
            'summary': {
                'total_incidents': int,
                'total_fatalities': int,
                'total_injuries': int,
                'pollution_events': int,
            },
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "bsee_incidents"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # BSEE data URLs
    BSEE_STATS_URL = "https://www.bsee.gov/stats-facts/offshore-incident-statistics"
    BSEE_DATA_URL = "https://www.data.bsee.gov/Main/Incidents.aspx"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for BSEEIncidentExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._lookback_years = config.get('lookback_years', 10) if config else 10

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search BSEE for incidents involving an operator."""
        operator_name = entity_id.strip()

        if not operator_name:
            return self._create_error_result("Empty operator name provided")

        try:
            incidents = self._search_incidents(operator_name)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"BSEE search error: {e}")

        if not incidents:
            return self._create_success_result({
                'searched_name': operator_name,
                'incidents_found': 0,
                'incidents': [],
                'summary': {
                    'total_incidents': 0,
                    'total_fatalities': 0,
                    'total_injuries': 0,
                    'pollution_events': 0,
                },
                'risk_score': 0.0,
                'note': 'No BSEE incidents found (operator may not have OCS operations)',
            })

        # Calculate summary
        summary = self._calculate_summary(incidents)

        # Calculate risk score
        risk_score = self._calculate_risk_score(incidents, summary)

        data = {
            'searched_name': operator_name,
            'incidents_found': len(incidents),
            'incidents': incidents[:20],  # Limit response
            'summary': summary,
            'risk_score': round(risk_score, 1),
            'lookback_years': self._lookback_years,
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_incidents(self, operator_name: str) -> List[Dict[str, Any]]:
        """Search BSEE for incidents."""
        incidents = []

        try:
            # Try to fetch incident data
            response = requests.get(
                self.BSEE_DATA_URL,
                params={'operator': operator_name},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (offshore-safety-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                incidents = self._parse_incidents(response.text, operator_name)

        except Exception as e:
            logger.debug(f"BSEE search error: {e}")

        return incidents

    def _parse_incidents(self, html: str, operator_name: str) -> List[Dict[str, Any]]:
        """Parse incident data from BSEE response."""
        incidents = []
        operator_lower = operator_name.lower()

        # Check if operator is mentioned
        if operator_lower not in html.lower():
            return incidents

        # Look for incident entries in tables
        row_pattern = r'<tr[^>]*>.*?</tr>'
        rows = re.findall(row_pattern, html, re.IGNORECASE | re.DOTALL)

        for row in rows:
            if operator_lower in row.lower():
                incident = self._parse_incident_row(row)
                if incident:
                    incidents.append(incident)

        return incidents

    def _parse_incident_row(self, row_html: str) -> Optional[Dict[str, Any]]:
        """Parse a single incident row."""
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]

        if len(cells) >= 4:
            # Determine incident type from content
            incident_type = 'Unknown'
            row_lower = row_html.lower()

            if 'fatality' in row_lower or 'death' in row_lower:
                incident_type = 'Fatality'
            elif 'injury' in row_lower:
                incident_type = 'Injury'
            elif 'fire' in row_lower:
                incident_type = 'Fire'
            elif 'explosion' in row_lower:
                incident_type = 'Explosion'
            elif 'spill' in row_lower or 'pollution' in row_lower:
                incident_type = 'Pollution'
            elif 'collision' in row_lower:
                incident_type = 'Collision'
            elif 'blowout' in row_lower:
                incident_type = 'Blowout'

            # Extract numbers
            fatalities = 0
            injuries = 0
            for cell in cells:
                if 'fatal' in cell.lower():
                    num_match = re.search(r'(\d+)', cell)
                    if num_match:
                        fatalities = int(num_match.group(1))
                elif 'injur' in cell.lower():
                    num_match = re.search(r'(\d+)', cell)
                    if num_match:
                        injuries = int(num_match.group(1))

            return {
                'date': cells[0] if cells else '',
                'incident_type': incident_type,
                'location': cells[1] if len(cells) > 1 else '',
                'operator': cells[2] if len(cells) > 2 else '',
                'injuries': injuries,
                'fatalities': fatalities,
                'pollution': 'spill' in row_lower or 'pollution' in row_lower,
                'description': cells[-1] if cells else '',
            }

        return None

    def _calculate_summary(self, incidents: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        return {
            'total_incidents': len(incidents),
            'total_fatalities': sum(i.get('fatalities', 0) for i in incidents),
            'total_injuries': sum(i.get('injuries', 0) for i in incidents),
            'pollution_events': sum(1 for i in incidents if i.get('pollution')),
            'fires_explosions': sum(1 for i in incidents if i.get('incident_type') in ['Fire', 'Explosion']),
        }

    def _calculate_risk_score(self, incidents: List[Dict], summary: Dict) -> float:
        """Calculate risk score."""
        score = 0.0

        # Fatalities are most serious
        score += summary.get('total_fatalities', 0) * 25

        # Injuries
        score += min(20, summary.get('total_injuries', 0) * 3)

        # Pollution events
        score += summary.get('pollution_events', 0) * 10

        # Fires/explosions
        score += summary.get('fires_explosions', 0) * 8

        # General incident count
        count = len(incidents)
        if count >= 10:
            score += 15
        elif count >= 5:
            score += 10
        elif count >= 1:
            score += 5

        return min(100.0, score)
