"""
Unified Output Schemas for Signal Types

These schemas define the standardized output format for each signal category.
Regardless of which extractor(s) provide data, the aggregated output conforms
to these schemas, enabling consistent downstream processing.

Benefits:
- Consistent data structure across jurisdictions
- Simplified downstream processing
- Clear data contracts
- Source attribution for audit trails
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional


class SanctionsMatchType(str, Enum):
    """Type of sanctions match."""
    EXACT = "exact"           # Exact name match
    FUZZY = "fuzzy"           # Fuzzy/similar name
    ALIAS = "alias"           # Known alias match
    ASSOCIATED = "associated"  # Associated entity


class SanctionsProgram(str, Enum):
    """Common sanctions programs."""
    OFAC_SDN = "ofac_sdn"
    OFAC_CONSOLIDATED = "ofac_consolidated"
    UK_SANCTIONS = "uk_sanctions"
    EU_SANCTIONS = "eu_sanctions"
    UN_SANCTIONS = "un_sanctions"
    INTERPOL = "interpol"
    FBI = "fbi"
    MDB_DEBARMENT = "mdb_debarment"
    OTHER = "other"


class RiskLevel(str, Enum):
    """Standardized risk levels."""
    CRITICAL = "critical"  # Confirmed match on major list
    HIGH = "high"          # Strong match or multiple lists
    MEDIUM = "medium"      # Fuzzy match or minor list
    LOW = "low"            # Weak match, likely false positive
    CLEAR = "clear"        # No matches found


@dataclass
class SanctionsMatch:
    """
    A single sanctions match from any source.

    Normalized from various extractor formats into a common structure.
    """
    # Core match info
    matched_name: str
    match_type: SanctionsMatchType
    match_score: float  # 0-100, confidence of match

    # Source attribution
    source: str          # Extractor that found this (e.g., 'opensanctions')
    source_list: str     # Specific list (e.g., 'OFAC SDN', 'UK OFSI')
    source_url: Optional[str] = None
    source_id: Optional[str] = None  # ID in source system

    # Sanctions details
    program: SanctionsProgram = SanctionsProgram.OTHER
    designation_date: Optional[date] = None
    reason: Optional[str] = None
    country: Optional[str] = None

    # Entity details from source
    entity_type: Optional[str] = None  # person, organization, vessel, etc.
    aliases: List[str] = field(default_factory=list)
    nationalities: List[str] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)
    identifiers: Dict[str, str] = field(default_factory=dict)  # passport, tax_id, etc.

    # Raw data for debugging
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SanctionsResult:
    """
    Unified sanctions check result aggregated from multiple sources.

    This is the standardized output format for sanctions signals.
    """
    # Summary
    entity_searched: str
    risk_level: RiskLevel
    total_matches: int
    sources_checked: List[str]
    sources_with_matches: List[str]

    # Matches grouped by source
    matches: List[SanctionsMatch]

    # Aggregate scores
    highest_match_score: float  # Best match confidence
    confirmed_sanctioned: bool  # True if high-confidence match exists

    # Metadata
    checked_at: datetime = field(default_factory=datetime.utcnow)
    check_duration_ms: float = 0.0

    # Warnings (e.g., sources that failed)
    warnings: List[str] = field(default_factory=list)
    failed_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'entity_searched': self.entity_searched,
            'risk_level': self.risk_level.value,
            'total_matches': self.total_matches,
            'sources_checked': self.sources_checked,
            'sources_with_matches': self.sources_with_matches,
            'matches': [
                {
                    'matched_name': m.matched_name,
                    'match_type': m.match_type.value,
                    'match_score': m.match_score,
                    'source': m.source,
                    'source_list': m.source_list,
                    'program': m.program.value,
                    'designation_date': m.designation_date.isoformat() if m.designation_date else None,
                    'reason': m.reason,
                    'entity_type': m.entity_type,
                    'aliases': m.aliases,
                }
                for m in self.matches
            ],
            'highest_match_score': self.highest_match_score,
            'confirmed_sanctioned': self.confirmed_sanctioned,
            'checked_at': self.checked_at.isoformat(),
            'warnings': self.warnings,
            'failed_sources': self.failed_sources,
        }


@dataclass
class CorporateRecord:
    """
    A corporate registration record from any registry.
    """
    # Core identity
    name: str
    jurisdiction: str  # Country/state of registration
    registration_number: Optional[str] = None
    lei: Optional[str] = None  # Legal Entity Identifier

    # Source attribution
    source: str = ""  # e.g., 'companies_house', 'opencorporates'
    source_url: Optional[str] = None

    # Status
    status: Optional[str] = None  # active, dissolved, etc.
    status_normalized: Optional[str] = None  # active, inactive, unknown
    incorporation_date: Optional[date] = None
    dissolution_date: Optional[date] = None

    # Entity type
    company_type: Optional[str] = None  # Ltd, PLC, Inc, etc.
    company_type_normalized: Optional[str] = None  # private, public, llp, etc.

    # Address
    registered_address: Optional[str] = None
    country: Optional[str] = None

    # Officers/directors
    officers: List[Dict[str, Any]] = field(default_factory=list)
    director_count: int = 0

    # Financial
    share_capital: Optional[float] = None
    currency: Optional[str] = None

    # Flags
    is_active: bool = True
    has_filings: bool = False
    has_charges: bool = False  # UK-specific: outstanding charges

    # Raw data
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorporateResult:
    """
    Unified corporate registry result aggregated from multiple sources.
    """
    # Query info
    entity_searched: str
    search_type: str  # name, registration_number, lei

    # Results
    records_found: int
    sources_checked: List[str]
    sources_with_results: List[str]

    # Primary record (best match)
    primary_record: Optional[CorporateRecord] = None

    # All records
    records: List[CorporateRecord] = field(default_factory=list)

    # Aggregate status
    any_active: bool = False
    any_dissolved: bool = False

    # LEI info (if found)
    lei: Optional[str] = None
    lei_status: Optional[str] = None  # ISSUED, LAPSED, etc.

    # Metadata
    checked_at: datetime = field(default_factory=datetime.utcnow)
    warnings: List[str] = field(default_factory=list)
    failed_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'entity_searched': self.entity_searched,
            'search_type': self.search_type,
            'records_found': self.records_found,
            'sources_checked': self.sources_checked,
            'sources_with_results': self.sources_with_results,
            'primary_record': {
                'name': self.primary_record.name,
                'jurisdiction': self.primary_record.jurisdiction,
                'registration_number': self.primary_record.registration_number,
                'status': self.primary_record.status,
                'status_normalized': self.primary_record.status_normalized,
                'incorporation_date': self.primary_record.incorporation_date.isoformat() if self.primary_record.incorporation_date else None,
                'is_active': self.primary_record.is_active,
                'source': self.primary_record.source,
            } if self.primary_record else None,
            'any_active': self.any_active,
            'any_dissolved': self.any_dissolved,
            'lei': self.lei,
            'lei_status': self.lei_status,
            'checked_at': self.checked_at.isoformat(),
            'warnings': self.warnings,
        }


@dataclass
class RegulatoryViolation:
    """
    A regulatory violation/enforcement action from any source.
    """
    # Core info
    violation_type: str  # environmental, safety, financial, etc.
    description: str
    severity: Optional[str] = None  # critical, major, minor

    # Source
    source: str = ""
    source_url: Optional[str] = None
    case_id: Optional[str] = None

    # Dates
    violation_date: Optional[date] = None
    resolution_date: Optional[date] = None
    is_resolved: bool = False

    # Penalties
    penalty_amount: Optional[float] = None
    penalty_currency: str = "USD"

    # Location
    facility: Optional[str] = None
    location: Optional[str] = None

    # Raw data
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegulatoryResult:
    """
    Unified regulatory check result aggregated from multiple sources.
    """
    entity_searched: str
    total_violations: int
    open_violations: int
    sources_checked: List[str]
    sources_with_violations: List[str]

    # Violations by category
    violations: List[RegulatoryViolation] = field(default_factory=list)
    violations_by_type: Dict[str, int] = field(default_factory=dict)

    # Aggregate
    total_penalties: float = 0.0
    penalty_currency: str = "USD"
    most_recent_violation: Optional[date] = None

    # Risk assessment
    risk_level: RiskLevel = RiskLevel.CLEAR

    # Metadata
    checked_at: datetime = field(default_factory=datetime.utcnow)
    warnings: List[str] = field(default_factory=list)
    failed_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_searched': self.entity_searched,
            'total_violations': self.total_violations,
            'open_violations': self.open_violations,
            'sources_checked': self.sources_checked,
            'risk_level': self.risk_level.value,
            'violations_by_type': self.violations_by_type,
            'total_penalties': self.total_penalties,
            'most_recent_violation': self.most_recent_violation.isoformat() if self.most_recent_violation else None,
            'checked_at': self.checked_at.isoformat(),
        }


@dataclass
class DomainRecord:
    """
    Domain/WHOIS registration record.
    """
    domain: str
    tld: str
    registered: bool = False

    # Registration dates
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    domain_age_days: Optional[int] = None

    # Registrant
    registrant_name: Optional[str] = None
    registrant_org: Optional[str] = None
    registrant_country: Optional[str] = None
    privacy_protected: bool = False

    # Technical
    registrar: Optional[str] = None
    nameservers: List[str] = field(default_factory=list)
    dnssec: bool = False

    # Source
    source: str = ""  # whois, rdap
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainResult:
    """
    Unified domain/WHOIS result.
    """
    domain_searched: str
    found: bool = False
    record: Optional[DomainRecord] = None

    # Quick stats
    domain_age_days: Optional[int] = None
    expires_soon: bool = False  # Within 30 days
    recently_created: bool = False  # Within 1 year

    # Risk indicators
    privacy_protected: bool = False
    new_domain: bool = False  # Less than 180 days old

    # Metadata
    checked_at: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'domain_searched': self.domain_searched,
            'found': self.found,
            'domain_age_days': self.domain_age_days,
            'expires_soon': self.expires_soon,
            'recently_created': self.recently_created,
            'privacy_protected': self.privacy_protected,
            'registrar': self.record.registrar if self.record else None,
            'registrant_country': self.record.registrant_country if self.record else None,
            'checked_at': self.checked_at.isoformat(),
        }


# Schema registry for validation
SIGNAL_SCHEMAS = {
    'sanctions': SanctionsResult,
    'corporate': CorporateResult,
    'regulatory': RegulatoryResult,
    'domain': DomainResult,
}


def get_schema(signal_type: str):
    """Get the schema class for a signal type."""
    return SIGNAL_SCHEMAS.get(signal_type)
