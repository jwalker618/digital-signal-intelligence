"""
DSI Production Extractor - GLEIF Legal Entity Identifier (LEI)

Queries the Global Legal Entity Identifier Foundation database.
FREE - Public GLEIF API with no authentication required.

GLEIF LEI Data:
    - Legal Entity Identifier (20-character code)
    - Entity legal name and address
    - Jurisdiction of formation
    - Entity status (active, inactive, merged, etc.)
    - Parent/child relationships
    - Registration authority

Data Source:
    https://www.gleif.org/
    API: https://api.gleif.org/api/v1/

Coverage:
    - 2.5+ million legal entities globally
    - Required for securities trading in many jurisdictions
    - ISO 17442 standard

Scoring Implications:
    - Valid active LEI = Positive (legitimate entity)
    - Lapsed/expired LEI = Moderate concern
    - No LEI found = Neutral (not all entities need LEI)
    - LEI with compliance issues = Concerning
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


class GLEIFLEIExtractor(ProductionExtractor):
    """
    Queries GLEIF API for Legal Entity Identifier data.

    No authentication required - public access.

    Output:
        {
            'searched_term': str,
            'search_type': str,  # 'lei', 'name'
            'entity_found': bool,
            'entities': [
                {
                    'lei': str,
                    'legal_name': str,
                    'other_names': [...],
                    'legal_address': {...},
                    'headquarters_address': {...},
                    'jurisdiction': str,
                    'entity_status': str,
                    'registration_status': str,
                    'initial_registration_date': str,
                    'last_update_date': str,
                    'next_renewal_date': str,
                    'managing_lou': str,
                }
            ],
            'risk_score': float,
        }
    """

    SOURCE_NAME = "gleif_lei"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # GLEIF API
    API_BASE = "https://api.gleif.org/api/v1"
    LEI_RECORDS = "/lei-records"
    FUZZY_COMPLETIONS = "/fuzzy-completions"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for GLEIFLEIExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search GLEIF for a legal entity."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine if searching by LEI or name
        is_lei = self._is_lei(search_term)
        search_type = 'lei' if is_lei else 'name'

        try:
            if is_lei:
                entities = self._search_by_lei(search_term)
            else:
                entities = self._search_by_name(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"GLEIF API error: {e}")

        if not entities:
            return self._create_success_result({
                'searched_term': search_term,
                'search_type': search_type,
                'entity_found': False,
                'entities': [],
                'risk_score': 10.0,  # No LEI is not necessarily bad
                'note': 'No LEI found (entity may not have registered for LEI)',
            })

        risk_score = self._calculate_risk_score(entities)

        data = {
            'searched_term': search_term,
            'search_type': search_type,
            'entity_found': True,
            'entities': entities[:10],
            'total_matches': len(entities),
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _is_lei(self, term: str) -> bool:
        """Check if term is a valid LEI format (20 alphanumeric characters)."""
        clean = term.replace(' ', '').replace('-', '')
        return len(clean) == 20 and clean.isalnum()

    def _search_by_lei(self, lei: str) -> List[Dict]:
        """Search by LEI number."""
        lei_clean = lei.replace(' ', '').replace('-', '').upper()

        try:
            response = requests.get(
                f"{self.API_BASE}{self.LEI_RECORDS}/{lei_clean}",
                headers={
                    'Accept': 'application/vnd.api+json',
                    'User-Agent': 'DSI-Framework/1.0 (corporate-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                record = data.get('data', {})
                if record:
                    entity = self._parse_lei_record(record)
                    return [entity] if entity else []

        except Exception as e:
            logger.debug(f"GLEIF LEI search error: {e}")

        return []

    def _search_by_name(self, name: str) -> List[Dict]:
        """Search by entity name."""
        entities = []

        try:
            # Use fuzzy search endpoint
            response = requests.get(
                f"{self.API_BASE}{self.LEI_RECORDS}",
                params={
                    'filter[entity.legalName]': name,
                    'page[size]': 20,
                },
                headers={
                    'Accept': 'application/vnd.api+json',
                    'User-Agent': 'DSI-Framework/1.0 (corporate-research)',
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])

                for record in records:
                    entity = self._parse_lei_record(record)
                    if entity:
                        entities.append(entity)

        except Exception as e:
            logger.debug(f"GLEIF name search error: {e}")

        return entities

    def _parse_lei_record(self, record: Dict) -> Optional[Dict]:
        """Parse LEI record from API response."""
        attributes = record.get('attributes', {})
        entity_data = attributes.get('entity', {})
        registration = attributes.get('registration', {})

        legal_address = entity_data.get('legalAddress', {})
        hq_address = entity_data.get('headquartersAddress', {})

        return {
            'lei': attributes.get('lei', ''),
            'legal_name': entity_data.get('legalName', {}).get('name', ''),
            'other_names': [
                n.get('name', '') for n in entity_data.get('otherNames', [])
            ],
            'legal_address': {
                'address': ', '.join(legal_address.get('addressLines', [])),
                'city': legal_address.get('city', ''),
                'region': legal_address.get('region', ''),
                'country': legal_address.get('country', ''),
                'postal_code': legal_address.get('postalCode', ''),
            },
            'headquarters_address': {
                'address': ', '.join(hq_address.get('addressLines', [])),
                'city': hq_address.get('city', ''),
                'country': hq_address.get('country', ''),
            },
            'jurisdiction': entity_data.get('jurisdiction', ''),
            'entity_status': entity_data.get('status', ''),
            'entity_category': entity_data.get('category', ''),
            'registration_status': registration.get('status', ''),
            'initial_registration_date': registration.get('initialRegistrationDate', ''),
            'last_update_date': registration.get('lastUpdateDate', ''),
            'next_renewal_date': registration.get('nextRenewalDate', ''),
            'managing_lou': registration.get('managingLou', ''),
        }

    def _calculate_risk_score(self, entities: List[Dict]) -> float:
        """Calculate risk score from LEI data."""
        if not entities:
            return 10.0

        score = 0.0
        top_entity = entities[0]

        # Registration status
        reg_status = (top_entity.get('registration_status') or '').upper()
        if reg_status == 'ISSUED':
            score += 0  # Good - active LEI
        elif reg_status == 'LAPSED':
            score += 25  # Concerning - not maintained
        elif reg_status == 'RETIRED':
            score += 15  # Entity may have merged/dissolved
        elif reg_status == 'PENDING_TRANSFER':
            score += 10
        else:
            score += 5

        # Entity status
        entity_status = (top_entity.get('entity_status') or '').upper()
        if entity_status == 'ACTIVE':
            score += 0
        elif entity_status == 'INACTIVE':
            score += 30
        else:
            score += 10

        # Check renewal date
        renewal_date = top_entity.get('next_renewal_date', '')
        if renewal_date:
            try:
                renewal_dt = datetime.strptime(renewal_date[:10], '%Y-%m-%d')
                if renewal_dt < datetime.now():
                    score += 15  # Overdue for renewal
            except ValueError:
                pass

        return max(0.0, min(100.0, score))
