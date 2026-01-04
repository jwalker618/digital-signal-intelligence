"""
DSI Production Extractor - UK OFSI Sanctions

Queries the UK Office of Financial Sanctions Implementation sanctions list.
FREE - Official UK government sanctions data.

UK OFSI Data:
    - Asset freeze targets
    - Financial sanctions designations
    - UN-derived UK sanctions
    - Autonomous UK sanctions regimes

Data Source:
    https://www.gov.uk/government/publications/the-uk-sanctions-list
    Search: https://sanctionssearchapp.ofsi.hmtreasury.gov.uk/

Note: The OFSI Consolidated List is merging into the UK Sanctions List
as of January 2026.

Scoring Implications:
    - Match on UK sanctions = Critical (85+ risk)
    - No match = Positive signal
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class UKOFSIExtractor(ProductionExtractor):
    """
    Queries UK OFSI/HMT sanctions list for designated entities.

    Downloads and searches the official UK sanctions XML file.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'matches': [
                {
                    'name': str,
                    'type': str,  # 'Individual', 'Entity'
                    'regime': str,  # Sanctions regime
                    'designation_date': str,
                    'uk_sanctions_list_ref': str,
                    'aliases': [...],
                }
            ],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "uk_ofsi"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # UK Sanctions List download URLs
    SANCTIONS_XML_URL = "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/UK_Sanctions_List.xml"
    OFSI_CONSOLIDATED_URL = "https://ofsistorage.blob.core.windows.net/publishlive/ConList.xml"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for UKOFSIExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 60) if config else 60
        self._sanctions_cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search UK sanctions list for an entity."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Get sanctions data
            sanctions_data = self._get_sanctions_list()

            if sanctions_data is None:
                return self._create_error_result("Could not retrieve UK sanctions list")

            # Search for matches
            matches = self._search_sanctions(search_term, sanctions_data)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"UK OFSI search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'sanctions_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in UK sanctions list',
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(matches)

        data = {
            'searched_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:10],
            'sanctions_hit': True,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _get_sanctions_list(self) -> Optional[List[Dict]]:
        """Download and parse UK sanctions list."""
        # Check cache
        if self._sanctions_cache and self._cache_time:
            cache_age = (datetime.utcnow() - self._cache_time).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return self._sanctions_cache

        # Try OFSI consolidated list first
        try:
            response = requests.get(
                self.OFSI_CONSOLIDATED_URL,
                headers={'User-Agent': 'DSI-Framework/1.0 (sanctions-screening)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_ofsi_xml(response.text)
                if sanctions:
                    self._sanctions_cache = sanctions
                    self._cache_time = datetime.utcnow()
                    return sanctions

        except Exception as e:
            logger.debug(f"Failed to fetch OFSI consolidated list: {e}")

        # Fall back to UK Sanctions List
        try:
            response = requests.get(
                self.SANCTIONS_XML_URL,
                headers={'User-Agent': 'DSI-Framework/1.0 (sanctions-screening)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_uk_sanctions_xml(response.text)
                if sanctions:
                    self._sanctions_cache = sanctions
                    self._cache_time = datetime.utcnow()
                    return sanctions

        except Exception as e:
            logger.debug(f"Failed to fetch UK sanctions list: {e}")

        return None

    def _parse_ofsi_xml(self, xml_content: str) -> List[Dict]:
        """Parse OFSI consolidated list XML."""
        sanctions = []

        try:
            root = ET.fromstring(xml_content)

            # Find all designated entries
            for entry in root.findall('.//FinancialSanctionsTarget'):
                sanction = {}

                # Get names
                names = []
                for name_elem in entry.findall('.//Name'):
                    name_parts = []
                    for part in ['Name1', 'Name2', 'Name3', 'Name4', 'Name5', 'Name6']:
                        elem = name_elem.find(part)
                        if elem is not None and elem.text:
                            name_parts.append(elem.text)
                    if name_parts:
                        names.append(' '.join(name_parts))

                if names:
                    sanction['name'] = names[0]
                    sanction['aliases'] = names[1:] if len(names) > 1 else []

                # Get type
                group_type = entry.find('.//GroupTypeDescription')
                if group_type is not None and group_type.text:
                    sanction['type'] = group_type.text

                # Get regime
                regime = entry.find('.//RegimeName')
                if regime is not None and regime.text:
                    sanction['regime'] = regime.text

                # Get designation date
                date_elem = entry.find('.//DateDesignated')
                if date_elem is not None and date_elem.text:
                    sanction['designation_date'] = date_elem.text

                # Get reference
                ref = entry.find('.//UKSL_ref')
                if ref is not None and ref.text:
                    sanction['uk_sanctions_list_ref'] = ref.text

                if sanction.get('name'):
                    sanctions.append(sanction)

        except ET.ParseError as e:
            logger.debug(f"XML parse error: {e}")

        return sanctions

    def _parse_uk_sanctions_xml(self, xml_content: str) -> List[Dict]:
        """Parse UK Sanctions List XML (newer format)."""
        sanctions = []

        try:
            root = ET.fromstring(xml_content)

            for entry in root.findall('.//Designation'):
                sanction = {}

                # Get primary name
                name = entry.find('.//PrimaryName')
                if name is not None and name.text:
                    sanction['name'] = name.text

                # Get aliases
                aliases = []
                for alias in entry.findall('.//Alias'):
                    if alias.text:
                        aliases.append(alias.text)
                sanction['aliases'] = aliases

                # Get type
                entry_type = entry.find('.//DesignationType')
                if entry_type is not None and entry_type.text:
                    sanction['type'] = entry_type.text

                # Get regime
                regime = entry.find('.//Regime')
                if regime is not None and regime.text:
                    sanction['regime'] = regime.text

                if sanction.get('name'):
                    sanctions.append(sanction)

        except ET.ParseError as e:
            logger.debug(f"UK Sanctions XML parse error: {e}")

        return sanctions

    def _search_sanctions(self, query: str, sanctions: List[Dict]) -> List[Dict]:
        """Search sanctions list for matching entries."""
        query_lower = query.lower()
        query_parts = set(query_lower.split())
        matches = []

        for sanction in sanctions:
            # Check primary name
            name = sanction.get('name', '').lower()
            if self._is_match(query_lower, query_parts, name):
                matches.append(sanction)
                continue

            # Check aliases
            for alias in sanction.get('aliases', []):
                if self._is_match(query_lower, query_parts, alias.lower()):
                    matches.append(sanction)
                    break

        return matches

    def _is_match(self, query: str, query_parts: set, target: str) -> bool:
        """Check if query matches target name."""
        # Exact match
        if query == target:
            return True

        # Query contained in target
        if query in target:
            return True

        # All query parts in target
        target_parts = set(target.split())
        if query_parts and query_parts.issubset(target_parts):
            return True

        # Significant overlap (for fuzzy matching)
        if query_parts and target_parts:
            overlap = len(query_parts & target_parts)
            if overlap >= min(2, len(query_parts)):
                return True

        return False

    def _calculate_risk_score(self, matches: List[Dict]) -> float:
        """Calculate risk score from matches."""
        if not matches:
            return 0.0

        # Any UK sanctions match is serious
        score = 85.0

        # Multiple matches increase concern
        if len(matches) > 3:
            score += 10
        elif len(matches) > 1:
            score += 5

        return min(100.0, score)
