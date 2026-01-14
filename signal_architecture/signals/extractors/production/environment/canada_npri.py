"""
DSI Production Extractor - Canada NPRI

Queries the Canadian National Pollutant Release Inventory.
FREE - Public Canadian environmental data.

NPRI Data:
    - Facility pollutant releases to air, water, and land
    - Pollutant transfers for disposal and recycling
    - Facility location and industry classification
    - Substance quantities by year

Data Source:
    https://open.canada.ca/data/en/dataset/40e01423-7728-429c-ac9d-2954385ccdfb
    NPRI Data Search: https://pollution-waste.canada.ca/national-release-inventory/

Coverage:
    - All Canadian facilities meeting reporting thresholds
    - Manufacturing, energy, mining sectors
    - 300+ reportable substances

Scoring Implications:
    - Clean record / minimal releases = Positive
    - High volume releases = Concerning
    - Reportable spills/accidents = High concern
    - No data = Neutral (may not meet thresholds)
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


class CanadaNPRIExtractor(ProductionExtractor):
    """
    Queries Canadian National Pollutant Release Inventory for facility data.

    Searches for facilities and their pollutant release reports.

    Output:
        {
            'searched_term': str,
            'facility_found': bool,
            'facilities': [
                {
                    'name': str,
                    'npri_id': str,
                    'city': str,
                    'province': str,
                    'naics_code': str,
                    'naics_description': str,
                }
            ],
            'releases': {
                'total_air': float,
                'total_water': float,
                'total_land': float,
                'reporting_years': [...],
            },
            'substances': [...],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "canada_npri"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # NPRI API endpoints
    NPRI_API = "https://pollution-waste.canada.ca/national-release-inventory/api/v1"
    OPEN_DATA_URL = "https://open.canada.ca/data/api/action/datastore_search"
    NPRI_RESOURCE_ID = "40e01423-7728-429c-ac9d-2954385ccdfb"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for CanadaNPRIExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search NPRI for a facility/company."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Search for facilities
            facilities = self._search_facilities(search_term)

            if not facilities:
                return self._create_success_result({
                    'searched_term': search_term,
                    'facility_found': False,
                    'facilities': [],
                    'risk_score': 0.0,
                    'note': 'No facilities found in NPRI (may not meet reporting thresholds)',
                })

            # Get release data for top facilities
            releases = self._get_releases(facilities[:5])

            # Calculate risk score
            risk_score = self._calculate_risk_score(facilities, releases)

            data = {
                'searched_term': search_term,
                'facility_found': True,
                'facilities': facilities[:10],
                'total_facilities': len(facilities),
                'releases': releases,
                'risk_score': round(risk_score, 1),
            }

            return self._create_success_result(data, confidence=0.85)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"NPRI search error: {e}")

    def _search_facilities(self, name: str) -> List[Dict]:
        """Search NPRI for facilities by company name."""
        facilities = []

        # Try the NPRI API
        try:
            response = requests.get(
                f"{self.NPRI_API}/facilities",
                params={
                    'facilityName': name,
                    'limit': 20,
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (environmental-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', data.get('facilities', [])):
                    facilities.append({
                        'name': item.get('facilityName', item.get('name', '')),
                        'npri_id': item.get('npriId', item.get('id', '')),
                        'city': item.get('city', ''),
                        'province': item.get('province', item.get('prov', '')),
                        'naics_code': item.get('naicsCode', ''),
                        'naics_description': item.get('naicsDescription', ''),
                    })

        except Exception as e:
            logger.debug(f"NPRI API error: {e}")

        # Fall back to Open Canada data portal
        if not facilities:
            facilities = self._search_open_canada(name)

        return facilities

    def _search_open_canada(self, name: str) -> List[Dict]:
        """Search via Open Canada data portal."""
        try:
            response = requests.get(
                self.OPEN_DATA_URL,
                params={
                    'resource_id': self.NPRI_RESOURCE_ID,
                    'q': name,
                    'limit': 20,
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'DSI-Framework/1.0 (environmental-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                records = data.get('result', {}).get('records', [])

                facilities = []
                seen_ids = set()

                for record in records:
                    npri_id = record.get('NPRI_ID', record.get('npri_id', ''))
                    if npri_id and npri_id not in seen_ids:
                        seen_ids.add(npri_id)
                        facilities.append({
                            'name': record.get('Facility_Name', record.get('facility_name', '')),
                            'npri_id': npri_id,
                            'city': record.get('City', record.get('city', '')),
                            'province': record.get('Province', record.get('province', '')),
                            'naics_code': record.get('NAICS', record.get('naics', '')),
                            'naics_description': record.get('NAICS_Description', ''),
                        })

                return facilities

        except Exception as e:
            logger.debug(f"Open Canada search error: {e}")

        return []

    def _get_releases(self, facilities: List[Dict]) -> Dict[str, Any]:
        """Get release totals for facilities."""
        releases = {
            'total_air': 0.0,
            'total_water': 0.0,
            'total_land': 0.0,
            'reporting_years': [],
            'top_substances': [],
        }

        if not facilities:
            return releases

        years = set()
        substances = {}

        for facility in facilities:
            npri_id = facility.get('npri_id', '')
            if not npri_id:
                continue

            try:
                response = requests.get(
                    f"{self.NPRI_API}/facilities/{npri_id}/releases",
                    headers={
                        'Accept': 'application/json',
                        'User-Agent': 'DSI-Framework/1.0 (environmental-research)',
                    },
                    timeout=self._timeout,
                )

                if response.status_code == 200:
                    data = response.json()

                    for release in data.get('releases', data.get('data', [])):
                        # Sum by media type
                        media = (release.get('media', release.get('releaseMedia', '')) or '').lower()
                        quantity = float(release.get('quantity', release.get('totalRelease', 0)) or 0)

                        if 'air' in media:
                            releases['total_air'] += quantity
                        elif 'water' in media:
                            releases['total_water'] += quantity
                        elif 'land' in media:
                            releases['total_land'] += quantity

                        # Track years
                        year = release.get('reportingYear', release.get('year'))
                        if year:
                            years.add(int(year))

                        # Track substances
                        substance = release.get('substanceName', release.get('substance', ''))
                        if substance:
                            substances[substance] = substances.get(substance, 0) + quantity

            except Exception as e:
                logger.debug(f"Release data error for {npri_id}: {e}")

        releases['reporting_years'] = sorted(years)[-5:] if years else []

        # Top 5 substances by quantity
        sorted_substances = sorted(substances.items(), key=lambda x: x[1], reverse=True)[:5]
        releases['top_substances'] = [{'name': s[0], 'quantity': s[1]} for s in sorted_substances]

        return releases

    def _calculate_risk_score(self, facilities: List[Dict], releases: Dict) -> float:
        """Calculate risk score from NPRI data."""
        score = 0.0

        # Number of facilities (more = larger industrial footprint)
        if len(facilities) > 5:
            score += 15
        elif len(facilities) > 2:
            score += 10

        # Release volumes (tonnes)
        total_releases = (
            releases.get('total_air', 0) +
            releases.get('total_water', 0) +
            releases.get('total_land', 0)
        )

        if total_releases > 10000:  # 10,000+ tonnes
            score += 30
        elif total_releases > 1000:  # 1,000+ tonnes
            score += 20
        elif total_releases > 100:   # 100+ tonnes
            score += 10
        elif total_releases > 0:
            score += 5

        # Water releases are often more concerning
        if releases.get('total_water', 0) > 100:
            score += 10

        # Check for high-risk sectors
        high_risk_naics = ['324', '325', '211', '212', '331', '322']  # Oil, chemicals, mining, metals, paper
        for facility in facilities:
            naics = str(facility.get('naics_code', ''))[:3]
            if naics in high_risk_naics:
                score += 10
                break

        # Recent reporting is positive (compliance)
        years = releases.get('reporting_years', [])
        if years and max(years) >= datetime.now().year - 1:
            score -= 5  # Recent reporting shows compliance

        return max(0.0, min(100.0, score))
