"""
Sanctions Multi-Source Aggregator

Consolidates sanctions check results from multiple sources:
- OpenSanctions (85+ lists)
- OFAC SDN
- UK OFSI
- EU Sanctions
- Interpol Red Notices
- FBI Most Wanted
- World Bank Debarred
- MDB Exclusions (ADB, IDB, EBRD, AfDB)

Each source has different data formats - this aggregator normalizes
them into a unified SanctionsResult schema.
"""

import logging
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

from .multi_source import MultiSourceAggregator, calculate_risk_level
from .schemas import (
    RiskLevel,
    SanctionsMatch,
    SanctionsMatchType,
    SanctionsProgram,
    SanctionsResult,
)

logger = logging.getLogger(__name__)


class SanctionsAggregator(MultiSourceAggregator[SanctionsResult]):
    """
    Aggregates sanctions checks across multiple global sources.

    Handles the variance in data formats from different sanctions lists
    and consolidates into a unified SanctionsResult.

    Usage:
        from signals.routing import SanctionsAggregator

        aggregator = SanctionsAggregator()

        # Check a UK company against relevant sanctions lists
        result = aggregator.aggregate(
            entity_id='Acme Corporation Ltd',
            signal_type='sanctions',
            locale='UK'
        )

        print(f"Risk Level: {result.result.risk_level}")
        print(f"Sources checked: {result.result.sources_checked}")
        print(f"Matches found: {result.result.total_matches}")

        for match in result.result.matches:
            print(f"  - {match.matched_name} ({match.source_list})")
    """

    # Map extractor names to their SanctionsProgram enum
    EXTRACTOR_TO_PROGRAM = {
        'ofac_sanctions': SanctionsProgram.OFAC_SDN,
        'opensanctions': SanctionsProgram.OTHER,  # Multi-source
        'uk_ofsi': SanctionsProgram.UK_SANCTIONS,
        'eu_sanctions': SanctionsProgram.EU_SANCTIONS,
        'interpol_red_notices': SanctionsProgram.INTERPOL,
        'fbi_most_wanted': SanctionsProgram.FBI,
        'worldbank_debarred': SanctionsProgram.MDB_DEBARMENT,
        'adb_sanctions': SanctionsProgram.MDB_DEBARMENT,
        'idb_sanctions': SanctionsProgram.MDB_DEBARMENT,
        'ebrd_ineligible': SanctionsProgram.MDB_DEBARMENT,
        'afdb_sanctions': SanctionsProgram.MDB_DEBARMENT,
    }

    # Human-readable source list names
    SOURCE_LIST_NAMES = {
        'ofac_sanctions': 'OFAC SDN List',
        'opensanctions': 'OpenSanctions Consolidated',
        'uk_ofsi': 'UK OFSI Financial Sanctions',
        'eu_sanctions': 'EU Consolidated Sanctions',
        'interpol_red_notices': 'Interpol Red Notices',
        'fbi_most_wanted': 'FBI Most Wanted',
        'worldbank_debarred': 'World Bank Debarred Firms',
        'adb_sanctions': 'Asian Development Bank Sanctions',
        'idb_sanctions': 'Inter-American Development Bank Sanctions',
        'ebrd_ineligible': 'EBRD Ineligible Entities',
        'afdb_sanctions': 'African Development Bank Sanctions',
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
    ) -> List[SanctionsMatch]:
        """
        Normalize extractor output to SanctionsMatch list.

        Each extractor has its own format - we normalize here.
        """
        # Route to specific normalizer
        normalizer = getattr(self, f'_normalize_{extractor_name}', None)
        if normalizer:
            return normalizer(raw_data, entity_id)

        # Generic fallback
        return self._normalize_generic(extractor_name, raw_data, entity_id)

    def _normalize_opensanctions(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize OpenSanctions results."""
        matches = []
        results = raw_data.get('results', [])

        for item in results:
            match_score = item.get('score', 0) * 100  # 0-1 to 0-100

            # Determine match type from score
            if match_score >= 95:
                match_type = SanctionsMatchType.EXACT
            elif match_score >= 80:
                match_type = SanctionsMatchType.FUZZY
            else:
                match_type = SanctionsMatchType.FUZZY

            # Get datasets (which lists this entity appears on)
            datasets = item.get('datasets', [])
            source_list = ', '.join(datasets[:3]) if datasets else 'OpenSanctions'

            # Determine program from datasets
            program = SanctionsProgram.OTHER
            for ds in datasets:
                ds_lower = ds.lower()
                if 'ofac' in ds_lower:
                    program = SanctionsProgram.OFAC_SDN
                    break
                elif 'eu' in ds_lower or 'european' in ds_lower:
                    program = SanctionsProgram.EU_SANCTIONS
                    break
                elif 'uk' in ds_lower or 'ofsi' in ds_lower:
                    program = SanctionsProgram.UK_SANCTIONS
                    break
                elif 'un' in ds_lower:
                    program = SanctionsProgram.UN_SANCTIONS
                    break

            matches.append(SanctionsMatch(
                matched_name=item.get('caption', item.get('name', 'Unknown')),
                match_type=match_type,
                match_score=match_score,
                source='opensanctions',
                source_list=source_list,
                source_id=item.get('id'),
                source_url=item.get('url'),
                program=program,
                entity_type=item.get('schema', 'unknown').lower(),
                aliases=item.get('properties', {}).get('alias', []),
                nationalities=item.get('properties', {}).get('nationality', []),
                country=item.get('properties', {}).get('country', [None])[0],
                raw_data=item,
            ))

        return matches

    def _normalize_ofac_sanctions(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize OFAC SDN results."""
        matches = []
        results = raw_data.get('results', [])

        for item in results:
            match_score = item.get('score', 85)  # Default high for OFAC matches

            matches.append(SanctionsMatch(
                matched_name=item.get('name', 'Unknown'),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='ofac_sanctions',
                source_list='OFAC SDN List',
                source_id=item.get('uid'),
                program=SanctionsProgram.OFAC_SDN,
                entity_type=item.get('type', 'unknown').lower(),
                aliases=item.get('aliases', []),
                reason=item.get('program'),
                country=item.get('country'),
                raw_data=item,
            ))

        return matches

    def _normalize_uk_ofsi(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize UK OFSI results."""
        matches = []
        results = raw_data.get('results', [])

        for item in results:
            match_score = item.get('score', 85)

            # Parse designation date
            designation_date = None
            date_str = item.get('designation_date') or item.get('listed_on')
            if date_str:
                try:
                    designation_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass

            matches.append(SanctionsMatch(
                matched_name=item.get('name', 'Unknown'),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='uk_ofsi',
                source_list='UK OFSI Financial Sanctions',
                source_id=item.get('group_id'),
                program=SanctionsProgram.UK_SANCTIONS,
                designation_date=designation_date,
                entity_type=item.get('group_type', 'unknown').lower(),
                aliases=item.get('aliases', []),
                reason=item.get('regime'),
                raw_data=item,
            ))

        return matches

    def _normalize_eu_sanctions(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize EU Sanctions results."""
        matches = []
        results = raw_data.get('results', [])

        for item in results:
            match_score = item.get('score', 85)

            matches.append(SanctionsMatch(
                matched_name=item.get('name', item.get('whole_name', 'Unknown')),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='eu_sanctions',
                source_list='EU Consolidated Sanctions',
                source_id=item.get('logical_id'),
                program=SanctionsProgram.EU_SANCTIONS,
                entity_type=item.get('subject_type', 'unknown').lower(),
                aliases=item.get('aliases', []),
                reason=item.get('regulation_summary'),
                raw_data=item,
            ))

        return matches

    def _normalize_interpol_red_notices(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize Interpol Red Notices results."""
        matches = []
        results = raw_data.get('results', raw_data.get('notices', []))

        for item in results:
            match_score = item.get('score', 80)

            # Build name from forename + name
            name = item.get('name', '')
            forename = item.get('forename', '')
            full_name = f"{forename} {name}".strip() if forename else name

            matches.append(SanctionsMatch(
                matched_name=full_name or 'Unknown',
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='interpol_red_notices',
                source_list='Interpol Red Notices',
                source_id=item.get('entity_id'),
                source_url=item.get('_links', {}).get('self', {}).get('href'),
                program=SanctionsProgram.INTERPOL,
                entity_type='person',
                nationalities=item.get('nationalities', []),
                country=item.get('country_of_birth_id'),
                reason=item.get('charge'),
                raw_data=item,
            ))

        return matches

    def _normalize_fbi_most_wanted(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize FBI Most Wanted results."""
        matches = []
        results = raw_data.get('results', raw_data.get('items', []))

        for item in results:
            match_score = item.get('score', 80)

            matches.append(SanctionsMatch(
                matched_name=item.get('title', 'Unknown'),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='fbi_most_wanted',
                source_list='FBI Most Wanted',
                source_id=item.get('uid'),
                source_url=item.get('url'),
                program=SanctionsProgram.FBI,
                entity_type='person',
                aliases=item.get('aliases', []),
                reason=item.get('caution') or item.get('description'),
                raw_data=item,
            ))

        return matches

    def _normalize_worldbank_debarred(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Normalize World Bank Debarred results."""
        matches = []
        results = raw_data.get('results', [])

        for item in results:
            match_score = item.get('score', 85)

            # Parse dates
            from_date = None
            to_date = None
            if item.get('from_date'):
                try:
                    from_date = datetime.strptime(item['from_date'][:10], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass

            matches.append(SanctionsMatch(
                matched_name=item.get('firm_name', 'Unknown'),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source='worldbank_debarred',
                source_list='World Bank Debarred Firms',
                program=SanctionsProgram.MDB_DEBARMENT,
                designation_date=from_date,
                entity_type='organization',
                country=item.get('country'),
                reason=item.get('grounds'),
                addresses=[item.get('address')] if item.get('address') else [],
                raw_data=item,
            ))

        return matches

    def _normalize_mdb_sanctions(
        self,
        extractor_name: str,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Generic normalizer for MDB sanctions (ADB, IDB, EBRD, AfDB)."""
        matches = []
        results = raw_data.get('results', [])

        source_list = self.SOURCE_LIST_NAMES.get(extractor_name, f'{extractor_name.upper()} Sanctions')

        for item in results:
            match_score = item.get('score', 85)

            matches.append(SanctionsMatch(
                matched_name=item.get('name', item.get('firm_name', 'Unknown')),
                match_type=SanctionsMatchType.EXACT if match_score >= 95 else SanctionsMatchType.FUZZY,
                match_score=match_score,
                source=extractor_name,
                source_list=source_list,
                program=SanctionsProgram.MDB_DEBARMENT,
                entity_type=item.get('entity_type', 'unknown').lower(),
                country=item.get('country', item.get('nationality')),
                reason=item.get('grounds', item.get('sanction_type')),
                raw_data=item,
            ))

        return matches

    # Route MDB extractors to generic normalizer
    def _normalize_adb_sanctions(self, raw_data: Dict, entity_id: str) -> List[SanctionsMatch]:
        return self._normalize_mdb_sanctions('adb_sanctions', raw_data, entity_id)

    def _normalize_idb_sanctions(self, raw_data: Dict, entity_id: str) -> List[SanctionsMatch]:
        return self._normalize_mdb_sanctions('idb_sanctions', raw_data, entity_id)

    def _normalize_ebrd_ineligible(self, raw_data: Dict, entity_id: str) -> List[SanctionsMatch]:
        return self._normalize_mdb_sanctions('ebrd_ineligible', raw_data, entity_id)

    def _normalize_afdb_sanctions(self, raw_data: Dict, entity_id: str) -> List[SanctionsMatch]:
        return self._normalize_mdb_sanctions('afdb_sanctions', raw_data, entity_id)

    def _normalize_generic(
        self,
        extractor_name: str,
        raw_data: Dict[str, Any],
        entity_id: str,
    ) -> List[SanctionsMatch]:
        """Generic normalizer for unknown extractors."""
        matches = []

        # Try common result formats
        results = (
            raw_data.get('results', []) or
            raw_data.get('matches', []) or
            raw_data.get('items', []) or
            raw_data.get('data', [])
        )

        if isinstance(results, dict):
            results = [results]

        for item in results:
            if not isinstance(item, dict):
                continue

            # Try to extract a name
            name = (
                item.get('name') or
                item.get('title') or
                item.get('caption') or
                item.get('entity_name') or
                str(item)[:50]
            )

            match_score = item.get('score', 70)

            matches.append(SanctionsMatch(
                matched_name=name,
                match_type=SanctionsMatchType.FUZZY,
                match_score=match_score,
                source=extractor_name,
                source_list=self.SOURCE_LIST_NAMES.get(extractor_name, extractor_name),
                program=self.EXTRACTOR_TO_PROGRAM.get(extractor_name, SanctionsProgram.OTHER),
                raw_data=item,
            ))

        return matches

    def create_unified_result(
        self,
        entity_id: str,
        all_matches: List[SanctionsMatch],
        sources_checked: List[str],
        sources_with_matches: List[str],
        failed_sources: List[str],
        warnings: List[str],
        check_duration_ms: float,
    ) -> SanctionsResult:
        """Create unified SanctionsResult from all matches."""

        # Calculate risk level
        risk_level = calculate_risk_level(all_matches, sources_with_matches)

        # Get highest match score
        highest_score = max(
            (m.match_score for m in all_matches),
            default=0.0
        )

        # Determine if confirmed sanctioned (high score from major source)
        major_sources = {'ofac_sanctions', 'uk_ofsi', 'eu_sanctions', 'opensanctions'}
        confirmed = any(
            m.match_score >= 90 and m.source in major_sources
            for m in all_matches
        )

        return SanctionsResult(
            entity_searched=entity_id,
            risk_level=risk_level,
            total_matches=len(all_matches),
            sources_checked=sources_checked,
            sources_with_matches=sources_with_matches,
            matches=all_matches,
            highest_match_score=highest_score,
            confirmed_sanctioned=confirmed,
            checked_at=datetime.utcnow(),
            check_duration_ms=check_duration_ms,
            warnings=warnings,
            failed_sources=failed_sources,
        )
