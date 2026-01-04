"""
DSI Production Extractor - FAA Certificate Database

Queries FAA certificate databases for air carrier and airman certification.
This is a FREE extractor - FAA data is public.

FAA Data Sources:
    - Air Carrier Certificate Information (OpSpec holders)
    - Aircraft Registry
    - Airman Certification
    - Service Difficulty Reports
    - Accident/Incident Data

Data Source:
    https://www.faa.gov/licenses_certificates/
    https://registry.faa.gov/

Scoring Implications:
    - Active operating certificate = Required for air operations
    - Certificate actions/revocations = Critical negative
    - Service difficulty reports = May indicate maintenance issues
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


class FAACertificateExtractor(ProductionExtractor):
    """
    Queries FAA certificate database for air carrier certification.

    Searches for operating certificates, certificate actions, and
    regulatory compliance history.

    Output:
        {
            'searched_name': str,
            'certificate_found': bool,
            'certificate': {
                'holder_name': str,
                'certificate_number': str,
                'certificate_type': str,
                'status': str,
                'issue_date': str,
                'operations': [...],
            },
            'actions': [
                {
                    'date': str,
                    'type': str,
                    'description': str,
                }
            ],
            'aircraft_count': int,
            'risk_score': float,
        }
    """

    SOURCE_NAME = "faa_certificate"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # FAA data URLs
    REGISTRY_URL = "https://registry.faa.gov/AircraftInquiry/Search/NNumberResult"
    CERT_SEARCH_URL = "https://av-info.faa.gov/OperatingCertSearch.asp"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for FAACertificateExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search FAA databases for an operator."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search for operating certificate
            cert_data = self._search_certificate(search_term)

            # Search for aircraft if we have a certificate
            aircraft_count = 0
            if cert_data and cert_data.get('certificate_number'):
                aircraft_count = self._count_aircraft(cert_data['certificate_number'])

            # Search for enforcement actions
            actions = self._search_actions(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"FAA API error: {e}")

        if not cert_data:
            return self._create_success_result({
                'searched_name': search_term,
                'certificate_found': False,
                'certificate': None,
                'actions': actions,
                'aircraft_count': 0,
                'risk_score': 0.0 if not actions else 30.0,
                'note': 'No FAA operating certificate found',
            }, confidence=0.70)

        # Calculate risk score
        risk_score = self._calculate_risk_score(cert_data, actions)

        data = {
            'searched_name': search_term,
            'certificate_found': True,
            'certificate': cert_data,
            'actions': actions[:10],
            'action_count': len(actions),
            'aircraft_count': aircraft_count,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_certificate(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for FAA operating certificate."""
        try:
            # Search the operating certificate database
            response = requests.get(
                self.CERT_SEARCH_URL,
                params={'name': name},
                headers={
                    'User-Agent': 'DSI-Framework/1.0 (aviation-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_certificate_html(response.text, name)

        except Exception as e:
            logger.debug(f"Certificate search failed: {e}")

        return None

    def _parse_certificate_html(self, html: str, search_name: str) -> Optional[Dict[str, Any]]:
        """Parse certificate data from HTML response."""
        # Look for certificate information in the HTML
        cert_data = {
            'holder_name': '',
            'certificate_number': '',
            'certificate_type': '',
            'status': 'Unknown',
            'issue_date': '',
            'operations': [],
            'address': '',
        }

        # Search for name match
        name_pattern = rf'<[^>]*>([^<]*{re.escape(search_name[:15])}[^<]*)</[^>]*>'
        name_match = re.search(name_pattern, html, re.IGNORECASE)
        if name_match:
            cert_data['holder_name'] = name_match.group(1).strip()

        # Look for certificate number patterns
        cert_pattern = r'(?:Certificate|Cert)[^:]*:\s*([A-Z0-9]+)'
        cert_match = re.search(cert_pattern, html, re.IGNORECASE)
        if cert_match:
            cert_data['certificate_number'] = cert_match.group(1)

        # Look for status
        if 'active' in html.lower():
            cert_data['status'] = 'Active'
        elif 'revoked' in html.lower():
            cert_data['status'] = 'Revoked'
        elif 'suspended' in html.lower():
            cert_data['status'] = 'Suspended'

        # Look for certificate type
        if 'Part 121' in html:
            cert_data['certificate_type'] = 'Part 121 (Scheduled Air Carrier)'
            cert_data['operations'].append('Scheduled passenger/cargo')
        if 'Part 135' in html:
            cert_data['certificate_type'] = 'Part 135 (Commuter/On-Demand)'
            cert_data['operations'].append('On-demand/charter')
        if 'Part 145' in html:
            cert_data['certificate_type'] = 'Part 145 (Repair Station)'
            cert_data['operations'].append('Maintenance/repair')

        if cert_data['holder_name'] or cert_data['certificate_number']:
            return cert_data

        return None

    def _count_aircraft(self, cert_number: str) -> int:
        """Count registered aircraft for a certificate holder."""
        try:
            # This would query the aircraft registry
            # For now, return 0 as placeholder
            return 0
        except Exception:
            return 0

    def _search_actions(self, name: str) -> List[Dict[str, Any]]:
        """Search for FAA enforcement actions."""
        actions = []

        try:
            # Search FAA enforcement database
            # This is a simplified implementation
            # Full implementation would query the enforcement database

            # Check for any enforcement indicators in name search
            pass

        except Exception as e:
            logger.debug(f"Action search failed: {e}")

        return actions

    def _calculate_risk_score(self, cert_data: Dict, actions: List) -> float:
        """Calculate risk score for the certificate holder."""
        score = 0.0

        # Status
        status = cert_data.get('status', '').lower()
        if status == 'revoked':
            score += 50
        elif status == 'suspended':
            score += 40
        elif status != 'active':
            score += 20

        # Enforcement actions
        score += min(30, len(actions) * 10)

        # Critical action types
        for action in actions:
            action_type = action.get('type', '').lower()
            if 'emergency' in action_type:
                score += 15
            if 'revocation' in action_type:
                score += 20
            if 'civil penalty' in action_type:
                score += 10

        return min(100.0, score)
