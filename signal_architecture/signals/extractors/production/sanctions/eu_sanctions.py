"""
DSI Production Extractor - EU Financial Sanctions

Queries the EU Consolidated Financial Sanctions list.
FREE - Official EU sanctions data from data.europa.eu.

EU Sanctions Data:
    - Persons subject to EU financial sanctions
    - Entities subject to EU financial sanctions
    - Groups/organizations under sanctions
    - Restrictive measures per EU Council Regulations

Data Source:
    https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions
    https://webgate.ec.europa.eu/fsd/fsf

Scoring Implications:
    - Match on EU sanctions = Critical (85+ risk)
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


class EUSanctionsExtractor(ProductionExtractor):
    """
    Queries EU Consolidated Financial Sanctions list.

    Downloads and searches the official EU sanctions XML file.

    Output:
        {
            'searched_term': str,
            'total_matches': int,
            'matches': [
                {
                    'name': str,
                    'type': str,  # 'P' (Person), 'E' (Entity)
                    'eu_reference': str,
                    'programme': str,  # Sanctions programme
                    'remark': str,
                    'aliases': [...],
                }
            ],
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "eu_sanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 1 day
    RATE_LIMIT = 1.0
    COST_TIER = "free"

    # EU Sanctions download URL
    EU_SANCTIONS_XML_URL = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"
    EU_SANCTIONS_CSV_URL = "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList/content"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for EUSanctionsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 60) if config else 60
        self._sanctions_cache = None
        self._cache_time = None

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search EU sanctions list for an entity."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        try:
            # Get sanctions data
            sanctions_data = self._get_sanctions_list()

            if sanctions_data is None:
                return self._create_error_result("Could not retrieve EU sanctions list")

            # Search for matches
            matches = self._search_sanctions(search_term, sanctions_data)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"EU sanctions search error: {e}")

        if not matches:
            return self._create_success_result({
                'searched_term': search_term,
                'total_matches': 0,
                'matches': [],
                'sanctions_hit': False,
                'risk_score': 0.0,
                'note': 'No matches found in EU sanctions list',
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
        """Download and parse EU sanctions list."""
        # Check cache
        if self._sanctions_cache and self._cache_time:
            cache_age = (datetime.utcnow() - self._cache_time).total_seconds()
            if cache_age < 3600:  # 1 hour cache
                return self._sanctions_cache

        try:
            response = requests.get(
                self.EU_SANCTIONS_XML_URL,
                headers={'User-Agent': 'DSI-Framework/1.0 (sanctions-screening)'},
                timeout=self._timeout,
            )

            if response.status_code == 200:
                sanctions = self._parse_eu_xml(response.text)
                if sanctions:
                    self._sanctions_cache = sanctions
                    self._cache_time = datetime.utcnow()
                    return sanctions

        except Exception as e:
            logger.debug(f"Failed to fetch EU sanctions XML: {e}")

        return None

    def _parse_eu_xml(self, xml_content: str) -> List[Dict]:
        """Parse EU sanctions list XML."""
        sanctions = []

        try:
            root = ET.fromstring(xml_content)

            # Define namespace if present
            ns = {}
            if root.tag.startswith('{'):
                ns_uri = root.tag[1:root.tag.index('}')]
                ns = {'eu': ns_uri}

            # Find all sanctioned entities
            for entity in root.findall('.//sanctionEntity', ns) or root.findall('.//entity'):
                sanction = self._parse_entity(entity, ns)
                if sanction:
                    sanctions.append(sanction)

            # Also check for different XML structures
            if not sanctions:
                for entity in root.iter():
                    if 'Entity' in entity.tag or 'Subject' in entity.tag:
                        sanction = self._parse_generic_entity(entity)
                        if sanction:
                            sanctions.append(sanction)

        except ET.ParseError as e:
            logger.debug(f"EU XML parse error: {e}")

        return sanctions

    def _parse_entity(self, entity: ET.Element, ns: Dict) -> Optional[Dict]:
        """Parse a sanctioned entity element."""
        sanction = {}

        # Try to get name from various possible elements
        name_elem = (
            entity.find('.//wholeName', ns) or
            entity.find('.//name', ns) or
            entity.find('.//nameAlias', ns)
        )

        if name_elem is not None:
            if name_elem.text:
                sanction['name'] = name_elem.text
            else:
                # Name might be in child elements
                name_parts = []
                for child in name_elem:
                    if child.text:
                        name_parts.append(child.text)
                if name_parts:
                    sanction['name'] = ' '.join(name_parts)

        # Get type
        subject_type = entity.get('subjectType') or entity.get('type')
        if subject_type:
            sanction['type'] = 'Person' if subject_type == 'P' else 'Entity'

        # Get EU reference
        eu_ref = entity.get('euReferenceNumber') or entity.get('logicalId')
        if eu_ref:
            sanction['eu_reference'] = eu_ref

        # Get programme/regulation
        programme = entity.find('.//programme', ns) or entity.find('.//regulation', ns)
        if programme is not None and programme.text:
            sanction['programme'] = programme.text

        # Get aliases
        aliases = []
        for alias in entity.findall('.//nameAlias', ns) or entity.findall('.//alias', ns):
            if alias.text and alias.text != sanction.get('name'):
                aliases.append(alias.text)
            elif alias.find('.//wholeName', ns) is not None:
                alias_name = alias.find('.//wholeName', ns)
                if alias_name.text and alias_name.text != sanction.get('name'):
                    aliases.append(alias_name.text)
        sanction['aliases'] = aliases

        # Get remark
        remark = entity.find('.//remark', ns)
        if remark is not None and remark.text:
            sanction['remark'] = remark.text[:500]  # Truncate long remarks

        return sanction if sanction.get('name') else None

    def _parse_generic_entity(self, entity: ET.Element) -> Optional[Dict]:
        """Parse entity from generic XML structure."""
        sanction = {}

        # Look for name in any child element with 'name' in tag
        for child in entity.iter():
            tag_lower = child.tag.lower()
            if 'name' in tag_lower and child.text:
                if 'alias' not in tag_lower:
                    sanction['name'] = child.text
                    break

        if not sanction.get('name'):
            # Try text content directly
            if entity.text and entity.text.strip():
                sanction['name'] = entity.text.strip()

        return sanction if sanction.get('name') else None

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
        if query == target:
            return True
        if query in target:
            return True

        target_parts = set(target.split())
        if query_parts and query_parts.issubset(target_parts):
            return True

        if query_parts and target_parts:
            overlap = len(query_parts & target_parts)
            if overlap >= min(2, len(query_parts)):
                return True

        return False

    def _calculate_risk_score(self, matches: List[Dict]) -> float:
        """Calculate risk score from matches."""
        if not matches:
            return 0.0

        score = 85.0

        if len(matches) > 3:
            score += 10
        elif len(matches) > 1:
            score += 5

        return min(100.0, score)
