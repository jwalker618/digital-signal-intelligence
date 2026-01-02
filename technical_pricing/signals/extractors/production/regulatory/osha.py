"""
DSI Production Extractor - OSHA Violations

Searches OSHA (Occupational Safety and Health Administration) violation data.
This is a FREE extractor - OSHA data is public.

OSHA Data:
    - Establishment inspections
    - Citations and violations
    - Penalties assessed
    - Accident investigations
    - Fatality/catastrophe reports

Data Sources:
    - OSHA Enforcement Data: https://enforcedata.dol.gov/views/search.php
    - OSHA Data API: https://enforcedata.dol.gov/
    - Direct data downloads: https://www.osha.gov/data

Scoring Implications:
    - Willful violations = Critical negative
    - Repeat violations = Major negative
    - Fatalities = Critical negative
    - High penalty amounts = Concerning
    - No violations = Positive (if in relevant industry)
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


# Violation type severity
VIOLATION_SEVERITY = {
    'willful': 5,
    'repeat': 4,
    'serious': 3,
    'other': 2,
    'unclassified': 1,
}


class OSHAViolationsExtractor(ProductionExtractor):
    """
    Searches OSHA violation/inspection data for a company.

    Uses the DOL enforcement data API to find violations.

    Output:
        {
            'searched_name': str,
            'inspections_found': int,
            'inspections': [
                {
                    'activity_nr': str,
                    'establishment_name': str,
                    'site_address': str,
                    'open_date': str,
                    'close_date': str,
                    'violations': {
                        'willful': int,
                        'repeat': int,
                        'serious': int,
                        'other': int,
                    },
                    'total_penalties': float,
                    'fatalities': int,
                }
            ],
            'summary': {
                'total_inspections': int,
                'total_violations': int,
                'total_penalties': float,
                'fatalities': int,
                'willful_count': int,
            },
            'risk_score': float,
        }
    """

    SOURCE_NAME = "osha_violations"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # DOL Enforcement Data API
    API_BASE = "https://enforcedata.dol.gov/api"
    SEARCH_URL = f"{API_BASE}/osha/inspection"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for OSHAViolationsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._lookback_years = config.get('lookback_years', 5) if config else 5

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search OSHA data for a company."""
        company_name = entity_id.strip()

        if not company_name:
            return self._create_error_result("Empty company name provided")

        try:
            inspections = self._search_inspections(company_name, **kwargs)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"OSHA API error: {e}")

        if not inspections:
            return self._create_success_result({
                'searched_name': company_name,
                'inspections_found': 0,
                'inspections': [],
                'summary': {
                    'total_inspections': 0,
                    'total_violations': 0,
                    'total_penalties': 0.0,
                    'fatalities': 0,
                    'willful_count': 0,
                },
                'risk_score': 0.0,
                'note': 'No OSHA inspections found (may not be in OSHA-regulated industry)',
            })

        # Process inspections
        processed = []
        for insp in inspections[:50]:  # Limit
            processed.append(self._process_inspection(insp))

        # Calculate summary
        summary = self._calculate_summary(processed)

        # Calculate risk score
        risk_score = self._calculate_risk_score(summary, len(processed))

        data = {
            'searched_name': company_name,
            'inspections_found': len(inspections),
            'inspections': processed[:20],  # Limit response
            'summary': summary,
            'risk_score': round(risk_score, 1),
            'lookback_years': self._lookback_years,
        }

        return self._create_success_result(data, confidence=0.85)

    def _search_inspections(self, company_name: str, **kwargs) -> List[Dict]:
        """Search for OSHA inspections."""
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self._lookback_years * 365)

        # Try the DOL API
        try:
            results = self._search_dol_api(company_name, start_date, end_date)
            if results:
                return results
        except Exception as e:
            logger.debug(f"DOL API search failed: {e}")

        # Fallback to alternative search method
        return self._search_alternative(company_name)

    def _search_dol_api(
        self,
        company_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Search using DOL enforcement data API."""
        # The DOL API uses OData-style filtering
        # Note: This is a simplified implementation - actual API may require registration

        params = {
            '$filter': f"contains(estab_name,'{company_name}')",
            '$top': 100,
            '$orderby': 'open_date desc',
        }

        headers = {
            'User-Agent': 'DSI-Framework/1.0 (safety-research)',
            'Accept': 'application/json',
        }

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=headers,
            timeout=self._timeout,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get('value', data.get('results', []))

        return []

    def _search_alternative(self, company_name: str) -> List[Dict]:
        """Alternative search method using OSHA's public search."""
        # This uses OSHA's establishment search
        url = "https://www.osha.gov/pls/imis/establishment.search"

        params = {
            'p_logger': '',
            'establishment': company_name,
            'State': 'all',
            'officetype': 'all',
            'Office': 'all',
            'endmonth': '12',
            'endday': '31',
            'endyear': str(datetime.utcnow().year),
            'startmonth': '01',
            'startday': '01',
            'startyear': str(datetime.utcnow().year - self._lookback_years),
            'owner': '',
            'scope': '',
            'FedAgency': '',
            'p_start': '',
            'p_finish': '100',
            'p_sort': '',
            'p_desc': 'DESC',
            'p_direction': 'Next',
            'p_show': '',
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers={'User-Agent': 'DSI-Framework/1.0 (safety-research)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_osha_html(response.text)
        except Exception as e:
            logger.debug(f"Alternative OSHA search failed: {e}")

        return []

    def _parse_osha_html(self, html: str) -> List[Dict]:
        """Parse OSHA search results HTML."""
        inspections = []

        # Look for inspection activity numbers in the HTML
        # Pattern: Activity Nr links
        activity_pattern = r'establishment\.inspection_detail\?id=(\d+)'
        activities = re.findall(activity_pattern, html)

        # Look for establishment names
        estab_pattern = r'<td[^>]*>([^<]+)</td>'

        # This is a simplified parser - would need to be enhanced for production
        for activity_nr in activities[:50]:
            inspections.append({
                'activity_nr': activity_nr,
                'estab_name': '',  # Would need more parsing
                'parsed_from_html': True,
            })

        return inspections

    def _process_inspection(self, inspection: Dict) -> Dict[str, Any]:
        """Process a single inspection record."""
        return {
            'activity_nr': inspection.get('activity_nr', ''),
            'establishment_name': inspection.get('estab_name', inspection.get('establishment_name', '')),
            'site_address': self._format_address(inspection),
            'city': inspection.get('site_city', ''),
            'state': inspection.get('site_state', ''),
            'open_date': inspection.get('open_date', ''),
            'close_date': inspection.get('close_case_date', inspection.get('close_date', '')),
            'inspection_type': inspection.get('insp_type', ''),
            'violations': {
                'willful': int(inspection.get('nr_in_viol_willful', 0) or 0),
                'repeat': int(inspection.get('nr_in_viol_repeat', 0) or 0),
                'serious': int(inspection.get('nr_in_viol_serious', 0) or 0),
                'other': int(inspection.get('nr_in_viol_other', 0) or 0),
            },
            'total_penalties': float(inspection.get('total_current_penalty', 0) or 0),
            'initial_penalties': float(inspection.get('total_initial_penalty', 0) or 0),
            'fatalities': int(inspection.get('total_fatalities', 0) or 0),
            'hospitalized': int(inspection.get('total_hospitalized', 0) or 0),
            'naics_code': inspection.get('naics_code', ''),
            'sic_code': inspection.get('sic_code', ''),
        }

    def _format_address(self, inspection: Dict) -> str:
        """Format inspection site address."""
        parts = []
        if inspection.get('site_address'):
            parts.append(inspection['site_address'])
        if inspection.get('site_city'):
            parts.append(inspection['site_city'])
        if inspection.get('site_state'):
            parts.append(inspection['site_state'])
        if inspection.get('site_zip'):
            parts.append(inspection['site_zip'])
        return ', '.join(parts)

    def _calculate_summary(self, inspections: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from inspections."""
        summary = {
            'total_inspections': len(inspections),
            'total_violations': 0,
            'total_penalties': 0.0,
            'fatalities': 0,
            'hospitalized': 0,
            'willful_count': 0,
            'repeat_count': 0,
            'serious_count': 0,
        }

        for insp in inspections:
            violations = insp.get('violations', {})
            summary['willful_count'] += violations.get('willful', 0)
            summary['repeat_count'] += violations.get('repeat', 0)
            summary['serious_count'] += violations.get('serious', 0)
            summary['total_violations'] += sum(violations.values())

            summary['total_penalties'] += insp.get('total_penalties', 0)
            summary['fatalities'] += insp.get('fatalities', 0)
            summary['hospitalized'] += insp.get('hospitalized', 0)

        summary['total_penalties'] = round(summary['total_penalties'], 2)

        return summary

    def _calculate_risk_score(self, summary: Dict, inspection_count: int) -> float:
        """Calculate risk score from summary data."""
        score = 0.0

        # Fatalities are most serious
        score += summary.get('fatalities', 0) * 25

        # Willful violations
        score += summary.get('willful_count', 0) * 15

        # Repeat violations
        score += summary.get('repeat_count', 0) * 10

        # Serious violations
        score += summary.get('serious_count', 0) * 3

        # Penalty amounts (normalized)
        penalties = summary.get('total_penalties', 0)
        if penalties > 1000000:
            score += 20
        elif penalties > 500000:
            score += 15
        elif penalties > 100000:
            score += 10
        elif penalties > 50000:
            score += 5

        # Many inspections may indicate issues
        if inspection_count > 20:
            score += 10
        elif inspection_count > 10:
            score += 5

        return min(100.0, score)
