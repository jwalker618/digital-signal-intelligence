"""
Corporate Registry Multi-Source Aggregator

Consolidates corporate registry lookups from multiple sources:
- OpenCorporates (145+ jurisdictions)
- GLEIF LEI (Global Legal Entity Identifiers)
- Companies House (UK)
- Australia ABN (Australian Business Register)
- India MCA (Ministry of Corporate Affairs)

Each source has different data formats - this aggregator normalizes
them into a unified CorporateResult schema.
"""

import logging
import re
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

from .multi_source import MultiSourceAggregator
from .schemas import CorporateRecord, CorporateResult

logger = logging.getLogger(__name__)


class CorporateAggregator(MultiSourceAggregator[CorporateResult]):
    """
    Aggregates corporate registry lookups across multiple sources.

    Handles the variance in data formats from different registries
    and consolidates into a unified CorporateResult.

    Usage:
        from technical_pricing.signals.routing import CorporateAggregator

        aggregator = CorporateAggregator()

        # Look up a UK company
        result = aggregator.aggregate(
            entity_id='Acme Corporation Ltd',
            signal_type='corporate',
            locale='UK'
        )

        print(f"Records found: {result.result.records_found}")
        if result.result.primary_record:
            print(f"Status: {result.result.primary_record.status}")
            print(f"Incorporated: {result.result.primary_record.incorporation_date}")
    """

    # Status normalization mapping
    STATUS_NORMALIZATIONS = {
        # Active states
        'active': 'active',
        'live': 'active',
        'registered': 'active',
        'in good standing': 'active',
        'current': 'active',
        'operating': 'active',

        # Inactive states
        'dissolved': 'inactive',
        'liquidation': 'inactive',
        'struck off': 'inactive',
        'removed': 'inactive',
        'closed': 'inactive',
        'inactive': 'inactive',
        'deregistered': 'inactive',
        'cancelled': 'inactive',
        'converted': 'inactive',

        # Unknown
        'unknown': 'unknown',
        '': 'unknown',
    }

    # Company type normalization
    COMPANY_TYPE_NORMALIZATIONS = {
        # Private limited
        'ltd': 'private_limited',
        'limited': 'private_limited',
        'private limited': 'private_limited',
        'private limited company': 'private_limited',
        'ltd.': 'private_limited',
        'pty ltd': 'private_limited',
        'gmbh': 'private_limited',
        'srl': 'private_limited',
        'bv': 'private_limited',
        'sarl': 'private_limited',
        'private company': 'private_limited',

        # Public limited
        'plc': 'public_limited',
        'public limited company': 'public_limited',
        'public company': 'public_limited',
        'ag': 'public_limited',
        'sa': 'public_limited',
        'nv': 'public_limited',
        'ab': 'public_limited',

        # LLP/Partnership
        'llp': 'llp',
        'limited liability partnership': 'llp',
        'lp': 'partnership',
        'partnership': 'partnership',
        'general partnership': 'partnership',

        # Corporation
        'inc': 'corporation',
        'inc.': 'corporation',
        'incorporated': 'corporation',
        'corp': 'corporation',
        'corp.': 'corporation',
        'corporation': 'corporation',
    }

    def get_extractor_func(self) -> Callable[[str], Any]:
        """Return function to get extractors."""
        from ..extractors.production.factory import get_extractor
        return lambda name: get_extractor(name, mode='production')

    def normalize_result(
        self,
        extractor_name: str,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize extractor output to CorporateRecord list."""
        normalizer = getattr(self, f'_normalize_{extractor_name}', None)
        if normalizer:
            return normalizer(raw_data, entity_id)
        return self._normalize_generic(extractor_name, raw_data, entity_id)

    def _normalize_status(self, status: Optional[str]) -> str:
        """Normalize company status to standard values."""
        if not status:
            return 'unknown'
        status_lower = status.lower().strip()
        return self.STATUS_NORMALIZATIONS.get(status_lower, 'unknown')

    def _normalize_company_type(self, company_type: Optional[str]) -> Optional[str]:
        """Normalize company type to standard values."""
        if not company_type:
            return None
        type_lower = company_type.lower().strip()

        # Direct match
        if type_lower in self.COMPANY_TYPE_NORMALIZATIONS:
            return self.COMPANY_TYPE_NORMALIZATIONS[type_lower]

        # Partial match
        for pattern, normalized in self.COMPANY_TYPE_NORMALIZATIONS.items():
            if pattern in type_lower:
                return normalized

        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse various date formats to date object."""
        if not date_str:
            return None

        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y%m%d',
            '%d-%m-%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(fmt.replace('%Y', '0000').replace('%m', '00').replace('%d', '00'))], fmt).date()
            except (ValueError, TypeError):
                continue

        return None

    def _normalize_opencorporates(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize OpenCorporates results."""
        records = []
        results = raw_data.get('results', {}).get('companies', [])

        if isinstance(results, dict):
            results = [results]

        for item in results:
            company = item.get('company', item)

            status = company.get('current_status', '')
            status_normalized = self._normalize_status(status)

            company_type = company.get('company_type', '')
            company_type_normalized = self._normalize_company_type(company_type)

            incorporation_date = self._parse_date(company.get('incorporation_date'))

            records.append(CorporateRecord(
                name=company.get('name', 'Unknown'),
                jurisdiction=company.get('jurisdiction_code', '').upper(),
                registration_number=company.get('company_number'),
                source='opencorporates',
                source_url=company.get('opencorporates_url'),
                status=status,
                status_normalized=status_normalized,
                incorporation_date=incorporation_date,
                company_type=company_type,
                company_type_normalized=company_type_normalized,
                registered_address=company.get('registered_address_in_full'),
                country=company.get('jurisdiction_code', '').split('_')[0].upper() if company.get('jurisdiction_code') else None,
                is_active=status_normalized == 'active',
                has_filings=company.get('number_of_employees') is not None or bool(company.get('previous_names')),
                raw_data=company,
            ))

        return records

    def _normalize_gleif_lei(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize GLEIF LEI results."""
        records = []
        results = raw_data.get('data', [])

        if isinstance(results, dict):
            results = [results]

        for item in results:
            attributes = item.get('attributes', {})
            entity = attributes.get('entity', {})
            registration = attributes.get('registration', {})

            legal_name = entity.get('legalName', {}).get('name', 'Unknown')

            # LEI status
            status = entity.get('status', '')
            lei_status = registration.get('status', '')

            # Get jurisdiction from legal address
            legal_address = entity.get('legalAddress', {})
            country = legal_address.get('country', '')

            # Get registration date
            initial_date = registration.get('initialRegistrationDate')
            incorporation_date = self._parse_date(initial_date)

            # Build address
            address_parts = [
                legal_address.get('addressLines', [''])[0] if legal_address.get('addressLines') else '',
                legal_address.get('city', ''),
                legal_address.get('postalCode', ''),
                country,
            ]
            full_address = ', '.join(p for p in address_parts if p)

            records.append(CorporateRecord(
                name=legal_name,
                jurisdiction=country,
                registration_number=None,  # LEI is separate
                lei=item.get('id'),
                source='gleif_lei',
                source_url=f"https://search.gleif.org/#/record/{item.get('id')}",
                status=status,
                status_normalized='active' if status == 'ACTIVE' else 'inactive',
                incorporation_date=incorporation_date,
                registered_address=full_address,
                country=country,
                is_active=status == 'ACTIVE',
                raw_data=item,
            ))

        return records

    def _normalize_companies_house(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize UK Companies House results."""
        records = []
        results = raw_data.get('items', [])

        if isinstance(results, dict):
            results = [results]

        for item in results:
            status = item.get('company_status', '')
            status_normalized = self._normalize_status(status)

            company_type = item.get('company_type', '')
            company_type_normalized = self._normalize_company_type(company_type)

            incorporation_date = self._parse_date(item.get('date_of_creation'))

            # Build address
            address = item.get('registered_office_address', {})
            if isinstance(address, dict):
                address_parts = [
                    address.get('address_line_1', ''),
                    address.get('address_line_2', ''),
                    address.get('locality', ''),
                    address.get('postal_code', ''),
                ]
                full_address = ', '.join(p for p in address_parts if p)
            else:
                full_address = str(address) if address else None

            records.append(CorporateRecord(
                name=item.get('title', item.get('company_name', 'Unknown')),
                jurisdiction='GB',
                registration_number=item.get('company_number'),
                source='companies_house',
                source_url=f"https://find-and-update.company-information.service.gov.uk/company/{item.get('company_number')}",
                status=status,
                status_normalized=status_normalized,
                incorporation_date=incorporation_date,
                company_type=company_type,
                company_type_normalized=company_type_normalized,
                registered_address=full_address,
                country='GB',
                is_active=status_normalized == 'active',
                has_charges=item.get('has_charges', False),
                raw_data=item,
            ))

        return records

    def _normalize_australia_abn(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize Australian Business Register results."""
        records = []
        results = raw_data.get('results', [])

        if isinstance(results, dict):
            results = [results]

        for item in results:
            # ABN status
            status = item.get('entityStatus', {}).get('entityStatusCode', '')
            status_normalized = 'active' if status == 'Active' else 'inactive'

            # Get registration date
            reg_date = item.get('entityStatus', {}).get('effectiveFrom')
            registration_date = self._parse_date(reg_date)

            # Get entity type
            entity_type = item.get('entityType', {}).get('entityTypeCode', '')

            # Get business address
            address = item.get('mainBusinessPhysicalAddress', {})
            state = address.get('stateCode', '')
            postcode = address.get('postcode', '')
            full_address = f"{state} {postcode}".strip() if state or postcode else None

            records.append(CorporateRecord(
                name=item.get('mainName', {}).get('organisationName', 'Unknown'),
                jurisdiction='AU',
                registration_number=item.get('ABN', {}).get('identifierValue'),
                source='australia_abn',
                source_url=f"https://abr.business.gov.au/ABN/View?id={item.get('ABN', {}).get('identifierValue')}",
                status=status,
                status_normalized=status_normalized,
                incorporation_date=registration_date,
                company_type=entity_type,
                registered_address=full_address,
                country='AU',
                is_active=status_normalized == 'active',
                raw_data=item,
            ))

        return records

    def _normalize_india_mca(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Normalize India MCA results."""
        records = []
        results = raw_data.get('results', [])

        if isinstance(results, dict):
            results = [results]

        for item in results:
            status = item.get('company_status', item.get('status', ''))
            status_normalized = self._normalize_status(status)

            # Get incorporation date
            inc_date = item.get('date_of_incorporation')
            incorporation_date = self._parse_date(inc_date)

            records.append(CorporateRecord(
                name=item.get('company_name', 'Unknown'),
                jurisdiction='IN',
                registration_number=item.get('cin', item.get('corporate_identity_number')),
                source='india_mca',
                status=status,
                status_normalized=status_normalized,
                incorporation_date=incorporation_date,
                company_type=item.get('company_type', item.get('company_class')),
                registered_address=item.get('registered_office_address'),
                country='IN',
                is_active=status_normalized == 'active',
                share_capital=item.get('authorized_capital'),
                currency='INR',
                raw_data=item,
            ))

        return records

    def _normalize_generic(
        self,
        extractor_name: str,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[CorporateRecord]:
        """Generic normalizer for unknown extractors."""
        records = []

        # Try common result formats
        results = (
            raw_data.get('results', []) or
            raw_data.get('companies', []) or
            raw_data.get('items', []) or
            raw_data.get('data', [])
        )

        if isinstance(results, dict):
            results = [results]

        for item in results:
            if not isinstance(item, dict):
                continue

            name = (
                item.get('name') or
                item.get('company_name') or
                item.get('title') or
                item.get('legal_name') or
                'Unknown'
            )

            status = item.get('status', item.get('company_status', ''))

            records.append(CorporateRecord(
                name=name,
                jurisdiction=item.get('jurisdiction', item.get('country', '')),
                registration_number=item.get('registration_number', item.get('company_number')),
                source=extractor_name,
                status=status,
                status_normalized=self._normalize_status(status),
                is_active=self._normalize_status(status) == 'active',
                raw_data=item,
            ))

        return records

    def create_unified_result(
        self,
        entity_id: str,
        all_matches: List[CorporateRecord],
        sources_checked: List[str],
        sources_with_matches: List[str],
        failed_sources: List[str],
        warnings: List[str],
        check_duration_ms: float,
    ) -> CorporateResult:
        """Create unified CorporateResult from all records."""

        # Find primary record (prefer active, then most complete)
        primary_record = None
        if all_matches:
            # Sort by: active status, then source priority
            source_priority = {
                'gleif_lei': 1,  # LEI is authoritative
                'companies_house': 2,
                'australia_abn': 2,
                'india_mca': 2,
                'opencorporates': 3,
            }

            sorted_records = sorted(
                all_matches,
                key=lambda r: (
                    0 if r.is_active else 1,  # Active first
                    source_priority.get(r.source, 10),  # Then by source priority
                )
            )
            primary_record = sorted_records[0]

        # Aggregate status
        any_active = any(r.is_active for r in all_matches)
        any_dissolved = any(not r.is_active for r in all_matches)

        # Find LEI if available
        lei = None
        lei_status = None
        for record in all_matches:
            if record.lei:
                lei = record.lei
                lei_status = record.status
                break

        # Determine search type
        search_type = 'name'
        if entity_id and len(entity_id) == 20 and entity_id.isalnum():
            search_type = 'lei'
        elif entity_id and re.match(r'^[A-Z]{2}\d+', entity_id):
            search_type = 'registration_number'

        return CorporateResult(
            entity_searched=entity_id,
            search_type=search_type,
            records_found=len(all_matches),
            sources_checked=sources_checked,
            sources_with_results=sources_with_matches,
            primary_record=primary_record,
            records=all_matches,
            any_active=any_active,
            any_dissolved=any_dissolved,
            lei=lei,
            lei_status=lei_status,
            checked_at=datetime.utcnow(),
            warnings=warnings,
            failed_sources=failed_sources,
        )
