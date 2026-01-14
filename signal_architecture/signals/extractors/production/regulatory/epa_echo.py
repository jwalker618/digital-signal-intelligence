"""
DSI Production Extractor - EPA ECHO

Queries EPA's ECHO (Enforcement and Compliance History Online) database.
This is a FREE extractor - EPA ECHO is a public database.

EPA ECHO Data:
    - Facility compliance/enforcement history
    - Environmental permits
    - Inspection results
    - Violations and penalties
    - Covers: Clean Air Act, Clean Water Act, RCRA, SDWA, etc.

API Documentation:
    https://echo.epa.gov/tools/web-services

Scoring Implications:
    - Significant violations = Negative signal
    - Recent enforcement actions = Concerning
    - Clean compliance history = Positive signal
    - No data = Neutral (may not have EPA-regulated facilities)
"""

import logging
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


class EPAEchoExtractor(ProductionExtractor):
    """
    Extracts EPA ECHO compliance and enforcement data.

    Searches by facility name, location, or permit IDs.
    Returns compliance status, violations, and enforcement actions.

    Output:
        {
            'searched_name': str,
            'facilities_found': int,
            'facilities': [
                {
                    'name': str,
                    'registry_id': str,
                    'address': str,
                    'programs': [...],  # CAA, CWA, RCRA, etc.
                    'compliance_status': str,
                    'violations': {
                        'current': int,
                        'significant': bool,
                        'quarters_in_nc': int,  # Non-compliance
                    },
                    'inspections': {
                        'count_5yr': int,
                        'last_date': str,
                    },
                    'enforcement': {
                        'informal_count': int,
                        'formal_count': int,
                        'penalties': float,
                    },
                }
            ],
            'aggregate': {
                'total_violations': int,
                'total_penalties': float,
                'significant_violator': bool,
            },
        }
    """

    SOURCE_NAME = "epa_echo"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 2.0  # EPA is generous but be respectful
    COST_TIER = "free"

    # EPA ECHO API endpoints
    BASE_URL = "https://echodata.epa.gov/echo"
    FACILITY_SEARCH_URL = f"{BASE_URL}/dfr_rest_services.get_dfr"
    FACILITY_LIST_URL = f"{BASE_URL}/echo_rest_services.get_facility_info"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for EPAEchoExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search EPA ECHO for facility compliance data."""
        search_name = entity_id.strip()

        if not search_name:
            return self._create_error_result("Empty search name provided")

        # Search for facilities
        try:
            facilities = self._search_facilities(search_name, **kwargs)
        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"EPA API error: {e}")

        if not facilities:
            # No facilities found - not an error
            return self._create_success_result({
                'searched_name': search_name,
                'facilities_found': 0,
                'facilities': [],
                'aggregate': {
                    'total_violations': 0,
                    'total_penalties': 0.0,
                    'significant_violator': False,
                },
                'note': 'No EPA-regulated facilities found for this entity',
            })

        # Get detailed compliance info for each facility
        detailed_facilities = []
        for facility in facilities[:10]:  # Limit to top 10
            try:
                detail = self._get_facility_details(facility.get('registry_id'))
                if detail:
                    facility.update(detail)
            except Exception as e:
                logger.warning(f"Error getting facility details: {e}")
            detailed_facilities.append(facility)

        # Calculate aggregates
        aggregate = self._calculate_aggregates(detailed_facilities)

        data = {
            'searched_name': search_name,
            'facilities_found': len(facilities),
            'facilities': detailed_facilities,
            'aggregate': aggregate,
        }

        return self._create_success_result(data, confidence=0.90)

    def _search_facilities(self, name: str, **kwargs) -> List[Dict[str, Any]]:
        """Search for facilities by name."""
        # Try facility name search first
        params = {
            'output': 'JSON',
            'p_fn': name,  # Facility name
            'p_act': 'Y',  # Active facilities
        }

        # Add optional location filters
        if kwargs.get('state'):
            params['p_st'] = kwargs['state']
        if kwargs.get('city'):
            params['p_ct'] = kwargs['city']
        if kwargs.get('zip'):
            params['p_zip'] = kwargs['zip']

        response = requests.get(
            self.FACILITY_LIST_URL,
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (compliance-research)'},
        )
        response.raise_for_status()

        data = response.json()
        facilities = []

        # Parse response (EPA ECHO has nested structure)
        results = data.get('Results', {})

        # Check for facilities in various possible locations
        facility_list = (
            results.get('Facilities', []) or
            results.get('FacilityInfo', []) or
            []
        )

        for fac in facility_list:
            facilities.append({
                'name': fac.get('FacName') or fac.get('FAC_NAME', ''),
                'registry_id': fac.get('RegistryId') or fac.get('REGISTRY_ID', ''),
                'address': self._format_address(fac),
                'city': fac.get('FacCity') or fac.get('FAC_CITY', ''),
                'state': fac.get('FacState') or fac.get('FAC_STATE', ''),
                'zip': fac.get('FacZip') or fac.get('FAC_ZIP', ''),
                'programs': self._parse_programs(fac),
            })

        return facilities

    def _get_facility_details(self, registry_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed compliance info for a facility."""
        if not registry_id:
            return None

        params = {
            'output': 'JSON',
            'p_id': registry_id,
        }

        response = requests.get(
            self.FACILITY_SEARCH_URL,
            params=params,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (compliance-research)'},
        )
        response.raise_for_status()

        data = response.json()
        results = data.get('Results', {})

        # Parse compliance info
        compliance = self._parse_compliance(results)
        inspections = self._parse_inspections(results)
        enforcement = self._parse_enforcement(results)
        violations = self._parse_violations(results)

        return {
            'compliance_status': compliance.get('status', 'Unknown'),
            'violations': violations,
            'inspections': inspections,
            'enforcement': enforcement,
            'last_updated': datetime.utcnow().isoformat(),
        }

    def _format_address(self, fac: Dict) -> str:
        """Format facility address."""
        parts = []
        if fac.get('FacStreet') or fac.get('FAC_STREET'):
            parts.append(fac.get('FacStreet') or fac.get('FAC_STREET', ''))
        if fac.get('FacCity') or fac.get('FAC_CITY'):
            parts.append(fac.get('FacCity') or fac.get('FAC_CITY', ''))
        if fac.get('FacState') or fac.get('FAC_STATE'):
            parts.append(fac.get('FacState') or fac.get('FAC_STATE', ''))
        if fac.get('FacZip') or fac.get('FAC_ZIP'):
            parts.append(fac.get('FacZip') or fac.get('FAC_ZIP', ''))
        return ', '.join(filter(None, parts))

    def _parse_programs(self, fac: Dict) -> List[str]:
        """Parse EPA programs the facility is subject to."""
        programs = []

        # Check various program flags
        program_flags = {
            'CAAFlag': 'CAA (Clean Air Act)',
            'CWAFlag': 'CWA (Clean Water Act)',
            'RCRAFlag': 'RCRA (Hazardous Waste)',
            'SDWAFlag': 'SDWA (Safe Drinking Water)',
            'AIRFlag': 'Air',
            'TRIFlag': 'TRI (Toxic Release Inventory)',
        }

        for flag, name in program_flags.items():
            if fac.get(flag, '').upper() in ('Y', 'YES', 'TRUE', '1'):
                programs.append(name)

        # Also check program string if present
        program_str = fac.get('Programs', '') or fac.get('PROGRAMS', '')
        if program_str:
            programs.extend(program_str.split(','))

        return list(set(programs))

    def _parse_compliance(self, results: Dict) -> Dict[str, Any]:
        """Parse overall compliance status."""
        compliance = {
            'status': 'Unknown',
            'in_compliance': True,
        }

        # Look for compliance summary in various locations
        summary = results.get('ComplianceSummary', {}) or results.get('Compliance', {})

        if summary.get('InSignificantViolation') or summary.get('SVFlag'):
            compliance['status'] = 'Significant Violation'
            compliance['in_compliance'] = False
        elif summary.get('InViolation') or summary.get('ViolFlag'):
            compliance['status'] = 'In Violation'
            compliance['in_compliance'] = False
        elif summary.get('InCompliance'):
            compliance['status'] = 'In Compliance'
            compliance['in_compliance'] = True

        return compliance

    def _parse_violations(self, results: Dict) -> Dict[str, Any]:
        """Parse violation information."""
        violations = {
            'current': 0,
            'significant': False,
            'quarters_in_nc': 0,  # Non-compliance quarters
        }

        # Try various data locations
        viol_data = (
            results.get('Violations', {}) or
            results.get('ViolationHistory', {}) or
            {}
        )

        if isinstance(viol_data, list) and viol_data:
            violations['current'] = len(viol_data)
        elif isinstance(viol_data, dict):
            violations['current'] = viol_data.get('ViolationCount', 0)
            violations['significant'] = viol_data.get('SVFlag', 'N').upper() == 'Y'
            violations['quarters_in_nc'] = viol_data.get('QuartersInNC', 0)

        # Check for significant violation flag elsewhere
        if results.get('SVFlag', 'N').upper() == 'Y':
            violations['significant'] = True

        return violations

    def _parse_inspections(self, results: Dict) -> Dict[str, Any]:
        """Parse inspection history."""
        inspections = {
            'count_5yr': 0,
            'last_date': None,
        }

        insp_data = results.get('Inspections', {}) or results.get('InspectionHistory', {})

        if isinstance(insp_data, list):
            inspections['count_5yr'] = len(insp_data)
            if insp_data:
                # Get most recent
                dates = [i.get('InspectionDate') for i in insp_data if i.get('InspectionDate')]
                if dates:
                    inspections['last_date'] = max(dates)
        elif isinstance(insp_data, dict):
            inspections['count_5yr'] = insp_data.get('Insp5yrCnt', 0)
            inspections['last_date'] = insp_data.get('LastInspDate')

        return inspections

    def _parse_enforcement(self, results: Dict) -> Dict[str, Any]:
        """Parse enforcement action history."""
        enforcement = {
            'informal_count': 0,
            'formal_count': 0,
            'penalties': 0.0,
        }

        enf_data = results.get('Enforcement', {}) or results.get('EnforcementActions', {})

        if isinstance(enf_data, dict):
            enforcement['informal_count'] = enf_data.get('InformalCount', 0)
            enforcement['formal_count'] = enf_data.get('FormalCount', 0)
            enforcement['penalties'] = float(enf_data.get('Penalties', 0) or 0)
        elif isinstance(enf_data, list):
            for action in enf_data:
                if action.get('ActionType', '').lower() == 'informal':
                    enforcement['informal_count'] += 1
                else:
                    enforcement['formal_count'] += 1
                enforcement['penalties'] += float(action.get('Penalty', 0) or 0)

        return enforcement

    def _calculate_aggregates(self, facilities: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate statistics across all facilities."""
        total_violations = 0
        total_penalties = 0.0
        significant_violator = False

        for fac in facilities:
            violations = fac.get('violations', {})
            enforcement = fac.get('enforcement', {})

            total_violations += violations.get('current', 0)
            total_penalties += enforcement.get('penalties', 0)

            if violations.get('significant'):
                significant_violator = True

        return {
            'total_violations': total_violations,
            'total_penalties': round(total_penalties, 2),
            'significant_violator': significant_violator,
            'facility_count': len(facilities),
        }
