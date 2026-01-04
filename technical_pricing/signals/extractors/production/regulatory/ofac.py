"""
DSI Production Extractor - OFAC Sanctions

Searches the OFAC Specially Designated Nationals (SDN) list.
This is a FREE extractor - OFAC data is public.

OFAC SDN List:
    - Maintained by US Treasury
    - Contains individuals and entities under sanctions
    - Updated regularly (usually within 24 hours of changes)

Data Sources:
    - OFAC Sanctions List Search: https://sanctionssearch.ofac.treas.gov/
    - SDN List XML: https://www.treasury.gov/ofac/downloads/sdn.xml
    - Consolidated List: https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml

Scoring Implications:
    - Match found = Critical risk signal
    - Partial match = Requires investigation
    - No match = Positive signal (but not definitive clearance)
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


class OFACSanctionsExtractor(ProductionExtractor):
    """
    Searches OFAC SDN list for sanctions matches.

    Uses the OFAC Sanctions List Search API or downloads the SDN list
    for local fuzzy matching.

    Output:
        {
            'searched_name': str,
            'match_found': bool,
            'exact_matches': [...],
            'partial_matches': [...],
            'search_score': float,  # 0-1, higher = riskier
            'programs': [...],  # Sanctions programs if matched
            'list_date': str,
        }
    """

    SOURCE_NAME = "ofac_sanctions"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 1.0  # Be respectful
    COST_TIER = "free"

    # OFAC data sources
    SDN_XML_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    CONSOLIDATED_XML_URL = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml"

    # Fuzzy match threshold
    EXACT_THRESHOLD = 0.95
    PARTIAL_THRESHOLD = 0.75

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for OFACSanctionsExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        self._sdn_cache = None
        self._use_consolidated = config.get('use_consolidated', False) if config else False

    def get_required_config(self) -> List[str]:
        return []  # No API key needed

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search OFAC SDN list for an entity."""
        search_name = entity_id.strip()

        if not search_name:
            return self._create_error_result("Empty search name provided")

        try:
            # Load SDN list (cached)
            sdn_entries = self._load_sdn_list()
        except Exception as e:
            return self._create_error_result(f"Error loading SDN list: {e}")

        if not sdn_entries:
            return self._create_error_result("Failed to load SDN list")

        # Search for matches
        exact_matches = []
        partial_matches = []

        normalized_search = self._normalize_name(search_name)

        for entry in sdn_entries:
            entry_name = entry.get('name', '')
            normalized_entry = self._normalize_name(entry_name)

            # Calculate similarity
            similarity = self._calculate_similarity(normalized_search, normalized_entry)

            if similarity >= self.EXACT_THRESHOLD:
                exact_matches.append({
                    'name': entry_name,
                    'similarity': round(similarity, 3),
                    'sdn_type': entry.get('sdn_type'),
                    'program': entry.get('program'),
                    'remarks': entry.get('remarks'),
                    'uid': entry.get('uid'),
                })
            elif similarity >= self.PARTIAL_THRESHOLD:
                partial_matches.append({
                    'name': entry_name,
                    'similarity': round(similarity, 3),
                    'sdn_type': entry.get('sdn_type'),
                    'program': entry.get('program'),
                })

            # Also check aliases
            for alias in entry.get('aliases', []):
                alias_name = alias.get('name', '')
                normalized_alias = self._normalize_name(alias_name)
                alias_similarity = self._calculate_similarity(normalized_search, normalized_alias)

                if alias_similarity >= self.EXACT_THRESHOLD:
                    exact_matches.append({
                        'name': alias_name,
                        'primary_name': entry_name,
                        'similarity': round(alias_similarity, 3),
                        'sdn_type': entry.get('sdn_type'),
                        'program': entry.get('program'),
                        'is_alias': True,
                    })
                elif alias_similarity >= self.PARTIAL_THRESHOLD:
                    partial_matches.append({
                        'name': alias_name,
                        'primary_name': entry_name,
                        'similarity': round(alias_similarity, 3),
                        'is_alias': True,
                    })

        # Sort by similarity
        exact_matches.sort(key=lambda x: x['similarity'], reverse=True)
        partial_matches.sort(key=lambda x: x['similarity'], reverse=True)

        # Limit results
        exact_matches = exact_matches[:10]
        partial_matches = partial_matches[:20]

        # Calculate risk score
        if exact_matches:
            search_score = 1.0  # Maximum risk
        elif partial_matches:
            search_score = max(m['similarity'] for m in partial_matches) * 0.8
        else:
            search_score = 0.0  # No risk signal

        # Get unique programs from matches
        programs = list(set(
            m.get('program') for m in exact_matches + partial_matches
            if m.get('program')
        ))

        data = {
            'searched_name': search_name,
            'match_found': len(exact_matches) > 0,
            'exact_matches': exact_matches,
            'partial_matches': partial_matches,
            'exact_match_count': len(exact_matches),
            'partial_match_count': len(partial_matches),
            'search_score': round(search_score, 3),
            'programs': programs,
            'sdn_list_size': len(sdn_entries),
        }

        confidence = 0.90 if exact_matches else 0.85
        return self._create_success_result(data, confidence=confidence)

    def _load_sdn_list(self) -> List[Dict[str, Any]]:
        """Load and parse the SDN XML list."""
        if self._sdn_cache is not None:
            return self._sdn_cache

        url = self.CONSOLIDATED_XML_URL if self._use_consolidated else self.SDN_XML_URL

        response = requests.get(
            url,
            timeout=self._timeout,
            headers={'User-Agent': 'DSI-Framework/1.0 (sanctions-screening)'},
        )
        response.raise_for_status()

        # Parse XML
        entries = []
        root = ElementTree.fromstring(response.content)

        # Find namespace
        ns = {'ofac': 'http://www.un.org/sanctions/1.0'}

        # Try to find SDN entries
        # The structure varies slightly between SDN and consolidated lists
        for entry in root.iter():
            if 'sdnEntry' in entry.tag or 'Entry' in entry.tag:
                parsed = self._parse_sdn_entry(entry)
                if parsed:
                    entries.append(parsed)

        # If standard parsing didn't work, try alternative
        if not entries:
            entries = self._parse_sdn_simple(root)

        self._sdn_cache = entries
        logger.info(f"Loaded {len(entries)} SDN entries")
        return entries

    def _parse_sdn_entry(self, entry: ElementTree.Element) -> Optional[Dict[str, Any]]:
        """Parse a single SDN entry element."""
        result = {
            'uid': None,
            'name': None,
            'sdn_type': None,
            'program': None,
            'remarks': None,
            'aliases': [],
        }

        for child in entry:
            tag = child.tag.split('}')[-1].lower()  # Remove namespace

            if tag == 'uid':
                result['uid'] = child.text
            elif tag in ('firstname', 'lastName', 'sdnName'):
                # Build name from parts
                if result['name']:
                    result['name'] += ' ' + (child.text or '')
                else:
                    result['name'] = child.text or ''
            elif tag == 'sdntype':
                result['sdn_type'] = child.text
            elif tag == 'programlist':
                programs = []
                for prog in child:
                    if prog.text:
                        programs.append(prog.text)
                result['program'] = ', '.join(programs)
            elif tag == 'remarks':
                result['remarks'] = child.text
            elif tag == 'akalist':
                for aka in child:
                    alias_name = ''
                    for aka_part in aka:
                        part_tag = aka_part.tag.split('}')[-1].lower()
                        if 'name' in part_tag and aka_part.text:
                            alias_name += ' ' + aka_part.text
                    if alias_name.strip():
                        result['aliases'].append({'name': alias_name.strip()})

        if result['name']:
            result['name'] = result['name'].strip()
            return result
        return None

    def _parse_sdn_simple(self, root: ElementTree.Element) -> List[Dict[str, Any]]:
        """Simple fallback parser for SDN XML."""
        entries = []

        for elem in root.iter():
            tag = elem.tag.split('}')[-1].lower()

            if tag == 'sdnentry':
                name = None
                sdn_type = None
                program = None

                for child in elem:
                    child_tag = child.tag.split('}')[-1].lower()
                    if child_tag == 'lastname' or child_tag == 'sdnname':
                        name = child.text
                    elif child_tag == 'sdntype':
                        sdn_type = child.text
                    elif child_tag == 'programlist':
                        progs = [p.text for p in child if p.text]
                        program = ', '.join(progs)

                if name:
                    entries.append({
                        'name': name,
                        'sdn_type': sdn_type,
                        'program': program,
                        'aliases': [],
                    })

        return entries

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        if not name:
            return ''
        # Lowercase
        name = name.lower()
        # Remove punctuation and extra whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two normalized names."""
        if not name1 or not name2:
            return 0.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, name1, name2).ratio()
