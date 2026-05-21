"""
DSI Production Extractor - Australia ABN Lookup

Queries the Australian Business Register (ABR) ABN Lookup service.
FREE - Official Australian Government business registry.

ABN Lookup Data:
    - Australian Business Number (ABN) validation
    - Business name and trading names
    - GST registration status
    - Entity type (company, trust, sole trader, etc.)
    - Business location (state/territory)
    - ABN status (active, cancelled)

Data Source:
    https://abr.business.gov.au/
    API: ABN Lookup web services

Coverage:
    - All Australian businesses with ABN
    - GST-registered entities
    - ASIC-registered companies
    - Trusts, partnerships, sole traders

Scoring Implications:
    - Active ABN with GST = Positive
    - ABN cancelled = Concerning
    - No ABN found = Moderate concern (may not be AU business)
"""

import logging
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


class AustraliaABNExtractor(ProductionExtractor):
    """
    Queries Australian Business Register for ABN/business information.

    Free API access via ABN Lookup web services.

    Output:
        {
            'searched_term': str,
            'search_type': str,  # 'abn', 'name', 'acn'
            'business_found': bool,
            'business': {
                'abn': str,
                'abn_status': str,
                'abn_status_effective_from': str,
                'entity_name': str,
                'entity_type': str,
                'entity_type_code': str,
                'business_names': [...],
                'gst_registered': bool,
                'gst_effective_from': str,
                'state': str,
                'postcode': str,
                'acn': str,
            },
            'risk_score': float,
        }
    """
    # V7 Phase 2: authoritative register source.
    MAX_EVIDENCE_GRADE = "structured_attested"


    SOURCE_NAME = "australia_abn"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400 * 7  # 1 week
    RATE_LIMIT = 2.0
    COST_TIER = "free"

    # ABN Lookup API endpoints
    ABN_LOOKUP_URL = "https://abr.business.gov.au/ABRXMLSearch/AbrXMLSearch.asmx"
    ABN_SEARCH_BY_ABN = "SearchByABNv202001"
    ABN_SEARCH_BY_NAME = "SearchByNameAdvanced2017"
    ABN_SEARCH_BY_ACN = "SearchByASICv201408"

    # GUID for anonymous access (limited)
    ANONYMOUS_GUID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests is required for AustraliaABNExtractor. "
                "Install with: pip install requests"
            )
        super().__init__(config)
        self._timeout = config.get('timeout', 30) if config else 30
        # GUID can be registered for free at abr.business.gov.au
        self._guid = config.get('guid', self.ANONYMOUS_GUID) if config else self.ANONYMOUS_GUID

    def get_required_config(self) -> List[str]:
        return []  # GUID is optional

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Search ABN Lookup for a business."""
        search_term = entity_id.strip()

        if not search_term:
            return self._create_error_result("Empty search term provided")

        # Determine search type
        search_type = self._determine_search_type(search_term)

        try:
            if search_type == 'abn':
                result = self._search_by_abn(search_term)
            elif search_type == 'acn':
                result = self._search_by_acn(search_term)
            else:
                result = self._search_by_name(search_term)

        except requests.exceptions.RequestException as e:
            return self._create_error_result(f"ABN Lookup error: {e}")

        if not result:
            return self._create_success_result({
                'searched_term': search_term,
                'search_type': search_type,
                'business_found': False,
                'risk_score': 20.0,  # Not finding ABN is slight concern
                'note': 'No matching business found in Australian Business Register',
            })

        # Calculate risk score
        risk_score = self._calculate_risk_score(result)

        data = {
            'searched_term': search_term,
            'search_type': search_type,
            'business_found': True,
            'business': result,
            'risk_score': round(risk_score, 1),
        }

        return self._create_success_result(data, confidence=0.90)

    def _determine_search_type(self, term: str) -> str:
        """Determine if search term is ABN, ACN, or name."""
        # Remove spaces and non-digits for number detection
        digits_only = ''.join(c for c in term if c.isdigit())

        # ABN is 11 digits
        if len(digits_only) == 11:
            return 'abn'

        # ACN is 9 digits
        if len(digits_only) == 9:
            return 'acn'

        return 'name'

    def _search_by_abn(self, abn: str) -> Optional[Dict]:
        """Search by ABN number."""
        # Clean ABN
        abn_clean = ''.join(c for c in abn if c.isdigit())

        # Build SOAP request
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{self.ABN_SEARCH_BY_ABN} xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <searchString>{abn_clean}</searchString>
      <includeHistoricalDetails>Y</includeHistoricalDetails>
      <authenticationGuid>{self._guid}</authenticationGuid>
    </{self.ABN_SEARCH_BY_ABN}>
  </soap:Body>
</soap:Envelope>"""

        return self._make_soap_request(soap_body)

    def _search_by_acn(self, acn: str) -> Optional[Dict]:
        """Search by ACN number."""
        acn_clean = ''.join(c for c in acn if c.isdigit())

        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{self.ABN_SEARCH_BY_ACN} xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <searchString>{acn_clean}</searchString>
      <includeHistoricalDetails>Y</includeHistoricalDetails>
      <authenticationGuid>{self._guid}</authenticationGuid>
    </{self.ABN_SEARCH_BY_ACN}>
  </soap:Body>
</soap:Envelope>"""

        return self._make_soap_request(soap_body)

    def _search_by_name(self, name: str) -> Optional[Dict]:
        """Search by business name."""
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{self.ABN_SEARCH_BY_NAME} xmlns="http://abr.business.gov.au/ABRXMLSearch/">
      <name>{name}</name>
      <postcode></postcode>
      <legalName>Y</legalName>
      <tradingName>Y</tradingName>
      <NSW>Y</NSW>
      <SA>Y</SA>
      <ACT>Y</ACT>
      <VIC>Y</VIC>
      <WA>Y</WA>
      <NT>Y</NT>
      <QLD>Y</QLD>
      <TAS>Y</TAS>
      <authenticationGuid>{self._guid}</authenticationGuid>
    </{self.ABN_SEARCH_BY_NAME}>
  </soap:Body>
</soap:Envelope>"""

        return self._make_soap_request(soap_body)

    def _make_soap_request(self, soap_body: str) -> Optional[Dict]:
        """Make SOAP request to ABN Lookup."""
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"http://abr.business.gov.au/ABRXMLSearch/ABRSearchByABN"',
            'User-Agent': 'DSI-Framework/1.0 (business-verification)',
        }

        try:
            response = requests.post(
                self.ABN_LOOKUP_URL,
                data=soap_body.encode('utf-8'),
                headers=headers,
                timeout=self._timeout,
            )

            if response.status_code == 200:
                return self._parse_soap_response(response.text)

        except Exception as e:
            logger.debug(f"ABN Lookup SOAP error: {e}")

        return None

    def _parse_soap_response(self, xml_content: str) -> Optional[Dict]:
        """Parse SOAP response from ABN Lookup."""
        try:
            # Remove namespaces for easier parsing
            xml_clean = xml_content
            for ns in ['soap:', 'xsi:', 'xsd:', 'xmlns']:
                xml_clean = xml_clean.replace(ns, '')

            root = ET.fromstring(xml_clean)

            # Find the business record
            business_entity = root.find('.//businessEntity') or root.find('.//searchResultsRecord')

            if business_entity is None:
                return None

            result = {}

            # ABN
            abn_elem = business_entity.find('.//ABN/identifierValue')
            if abn_elem is not None and abn_elem.text:
                result['abn'] = abn_elem.text

            # ABN Status
            abn_status = business_entity.find('.//ABN/identifierStatus')
            if abn_status is not None and abn_status.text:
                result['abn_status'] = abn_status.text

            # Entity name (try multiple locations)
            for name_path in ['.//mainName/organisationName', './/mainTradingName/organisationName',
                              './/legalName/fullName', './/entityDescription/entityDescription']:
                name_elem = business_entity.find(name_path)
                if name_elem is not None and name_elem.text:
                    result['entity_name'] = name_elem.text
                    break

            # Entity type
            entity_type = business_entity.find('.//entityType/entityDescription')
            if entity_type is not None and entity_type.text:
                result['entity_type'] = entity_type.text

            entity_type_code = business_entity.find('.//entityType/entityTypeCode')
            if entity_type_code is not None and entity_type_code.text:
                result['entity_type_code'] = entity_type_code.text

            # GST status
            gst_elem = business_entity.find('.//goodsAndServicesTax/effectiveFrom')
            if gst_elem is not None and gst_elem.text:
                result['gst_registered'] = True
                result['gst_effective_from'] = gst_elem.text
            else:
                result['gst_registered'] = False

            # Business names
            business_names = []
            for bn in business_entity.findall('.//businessName/organisationName'):
                if bn.text:
                    business_names.append(bn.text)
            result['business_names'] = business_names

            # Location
            for loc_path in ['.//mainBusinessPhysicalAddress', './/businessAddress']:
                loc = business_entity.find(loc_path)
                if loc is not None:
                    state = loc.find('.//stateCode')
                    postcode = loc.find('.//postcode')
                    if state is not None and state.text:
                        result['state'] = state.text
                    if postcode is not None and postcode.text:
                        result['postcode'] = postcode.text
                    break

            # ACN (if company)
            acn = business_entity.find('.//ASICNumber')
            if acn is not None and acn.text:
                result['acn'] = acn.text

            return result if result.get('abn') or result.get('entity_name') else None

        except ET.ParseError as e:
            logger.debug(f"XML parse error: {e}")
            return None

    def _calculate_risk_score(self, business: Dict) -> float:
        """Calculate risk score from business data."""
        score = 0.0

        # ABN status
        status = (business.get('abn_status') or '').lower()
        if 'active' in status:
            score += 0  # Active is good
        elif 'cancelled' in status:
            score += 50  # Cancelled is concerning
        else:
            score += 15  # Unknown status

        # GST registration (expected for established businesses)
        if not business.get('gst_registered'):
            score += 10  # No GST might indicate small/new business

        # Entity type (some types are higher risk)
        entity_type = (business.get('entity_type') or '').lower()
        if 'trust' in entity_type:
            score += 10  # Trusts can obscure ownership
        elif 'sole trader' in entity_type or 'individual' in entity_type:
            score += 5  # Less formal structure

        return max(0.0, min(100.0, score))
