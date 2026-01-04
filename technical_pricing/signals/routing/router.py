"""
Jurisdiction-Aware Signal Router

Routes signal extraction requests to appropriate data sources based on:
- Entity locale/jurisdiction
- Signal type (sanctions, corporate, regulatory, etc.)
- Routing strategy (locale-only, global-only, or combined)
- Extractor tier (free, paid, premium)

This module solves the problem of which extractors to call for a given entity,
optimizing for both coverage and efficiency.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Strategy for selecting extractors."""

    # Only use extractors specific to the entity's locale
    LOCALE_ONLY = "locale_only"

    # Only use global/multi-jurisdiction extractors
    GLOBAL_ONLY = "global_only"

    # Use locale-specific + global extractors (recommended)
    LOCALE_PLUS_GLOBAL = "locale_plus_global"

    # Use all available extractors regardless of locale
    ALL = "all"

    # Use primary source only (fastest, least comprehensive)
    PRIMARY_ONLY = "primary_only"


class ExtractorTier(str, Enum):
    """
    Pricing tier for extractors.

    Controls which extractors are available based on subscription level.
    """
    # Free extractors - no API keys or costs
    FREE = "free"

    # Paid basic - low-cost APIs with generous free tiers
    PAID_BASIC = "paid_basic"

    # Paid premium - commercial APIs with per-call costs
    PAID_PREMIUM = "paid_premium"

    # Enterprise - high-cost, high-value data sources
    ENTERPRISE = "enterprise"


# Extractor tier classification
# All current extractors are FREE tier
EXTRACTOR_TIERS: Dict[str, ExtractorTier] = {
    # DNS (all free)
    'email_auth': ExtractorTier.FREE,
    'dnssec': ExtractorTier.FREE,
    'dns_records': ExtractorTier.FREE,
    'whois_rdap': ExtractorTier.FREE,

    # HTTP (all free)
    'security_headers': ExtractorTier.FREE,
    'security_txt': ExtractorTier.FREE,

    # Network (all free)
    'cloud_infra': ExtractorTier.FREE,
    'cdn_usage': ExtractorTier.FREE,
    'waf_presence': ExtractorTier.FREE,
    'tls_config': ExtractorTier.FREE,

    # Securities (all free)
    'sec_filings': ExtractorTier.FREE,
    'sec_financials': ExtractorTier.FREE,
    'sec_litigation': ExtractorTier.FREE,
    'sec_governance': ExtractorTier.FREE,
    'sedar_canada': ExtractorTier.FREE,

    # Regulatory (all free)
    'ofac_sanctions': ExtractorTier.FREE,
    'epa_echo': ExtractorTier.FREE,
    'cfpb_complaints': ExtractorTier.FREE,
    'osha_violations': ExtractorTier.FREE,
    'faa_certificate': ExtractorTier.FREE,
    'eu_safety_list': ExtractorTier.FREE,
    'fdic_enforcement': ExtractorTier.FREE,
    'bsee_incidents': ExtractorTier.FREE,
    'uk_fca_register': ExtractorTier.FREE,

    # Sanctions (all free)
    'opensanctions': ExtractorTier.FREE,
    'uk_ofsi': ExtractorTier.FREE,
    'eu_sanctions': ExtractorTier.FREE,
    'worldbank_debarred': ExtractorTier.FREE,
    'interpol_red_notices': ExtractorTier.FREE,
    'fbi_most_wanted': ExtractorTier.FREE,
    'adb_sanctions': ExtractorTier.FREE,
    'idb_sanctions': ExtractorTier.FREE,
    'ebrd_ineligible': ExtractorTier.FREE,
    'afdb_sanctions': ExtractorTier.FREE,

    # Security (all free)
    'nvd_cve': ExtractorTier.FREE,
    'hhs_breach': ExtractorTier.FREE,

    # Industry (all free)
    'pcaob': ExtractorTier.FREE,
    'aviation_safety': ExtractorTier.FREE,

    # Corporate (all free)
    'companies_house': ExtractorTier.FREE,
    'opencorporates': ExtractorTier.FREE,
    'australia_abn': ExtractorTier.FREE,
    'india_mca': ExtractorTier.FREE,
    'gleif_lei': ExtractorTier.FREE,

    # Environment (all free)
    'eea_environment': ExtractorTier.FREE,
    'canada_npri': ExtractorTier.FREE,

    # Maritime/Aviation (all free)
    'imo_gisis': ExtractorTier.FREE,
    'iosa_registry': ExtractorTier.FREE,

    # =========================================================================
    # PAID EXTRACTORS (Future - not yet implemented)
    # =========================================================================
    # PAID_BASIC tier - APIs with generous free tiers or low per-call costs
    'shodan': ExtractorTier.PAID_BASIC,           # Network/security scanning
    'censys': ExtractorTier.PAID_BASIC,           # Internet-wide scanning
    'virustotal': ExtractorTier.PAID_BASIC,       # Malware/threat intel
    'ssllabs': ExtractorTier.PAID_BASIC,          # Deep SSL analysis
    'builtwith': ExtractorTier.PAID_BASIC,        # Technology profiling

    # PAID_PREMIUM tier - Commercial per-call APIs
    'dnb': ExtractorTier.PAID_PREMIUM,            # Dun & Bradstreet
    'experian': ExtractorTier.PAID_PREMIUM,       # Experian business
    'lexisnexis': ExtractorTier.PAID_PREMIUM,     # LexisNexis risk
    'refinitiv': ExtractorTier.PAID_PREMIUM,      # Refinitiv World-Check
    'moodys': ExtractorTier.PAID_PREMIUM,         # Moody's ratings
    'sp_global': ExtractorTier.PAID_PREMIUM,      # S&P Global
    'bureau_van_dijk': ExtractorTier.PAID_PREMIUM,  # Orbis/BvD

    # ENTERPRISE tier - Premium data sources
    'bloomberg': ExtractorTier.ENTERPRISE,        # Bloomberg terminal data
    'factset': ExtractorTier.ENTERPRISE,          # FactSet
    'pitchbook': ExtractorTier.ENTERPRISE,        # PitchBook
    'crunchbase_enterprise': ExtractorTier.ENTERPRISE,
}


@dataclass
class ExtractorGroup:
    """
    Defines a group of extractors for a signal type.

    Attributes:
        global_extractors: Extractors that cover multiple jurisdictions
        locale_extractors: Mapping of locale code to locale-specific extractors
        primary_extractor: The recommended first-choice extractor
        requires_all: If True, all matching extractors should be called
    """
    global_extractors: List[str] = field(default_factory=list)
    locale_extractors: Dict[str, List[str]] = field(default_factory=dict)
    primary_extractor: Optional[str] = None
    requires_all: bool = False  # For sanctions, typically want comprehensive coverage


# Master jurisdiction mappings for all signal types
JURISDICTION_MAPPINGS: Dict[str, ExtractorGroup] = {
    # =========================================================================
    # SANCTIONS - Comprehensive coverage recommended (requires_all=True)
    # =========================================================================
    'sanctions': ExtractorGroup(
        global_extractors=[
            'opensanctions',          # 85+ sources, best single source
            'interpol_red_notices',   # Global law enforcement
            'fbi_most_wanted',        # US but global reach
            'worldbank_debarred',     # Global MDB
        ],
        locale_extractors={
            'US': ['ofac_sanctions'],
            'UK': ['uk_ofsi'],
            'EU': ['eu_sanctions'],
            'DE': ['eu_sanctions'],
            'FR': ['eu_sanctions'],
            'IT': ['eu_sanctions'],
            'ES': ['eu_sanctions'],
            'NL': ['eu_sanctions'],
            'BE': ['eu_sanctions'],
            # Asia-Pacific
            'JP': ['adb_sanctions'],
            'CN': ['adb_sanctions'],
            'KR': ['adb_sanctions'],
            'IN': ['adb_sanctions'],
            'AU': ['adb_sanctions'],
            'SG': ['adb_sanctions'],
            'TH': ['adb_sanctions'],
            'VN': ['adb_sanctions'],
            'PH': ['adb_sanctions'],
            'ID': ['adb_sanctions'],
            'MY': ['adb_sanctions'],
            # Americas
            'BR': ['idb_sanctions'],
            'MX': ['idb_sanctions'],
            'AR': ['idb_sanctions'],
            'CO': ['idb_sanctions'],
            'CL': ['idb_sanctions'],
            'PE': ['idb_sanctions'],
            # Europe/Central Asia (EBRD)
            'RU': ['ebrd_ineligible'],
            'UA': ['ebrd_ineligible'],
            'KZ': ['ebrd_ineligible'],
            'PL': ['ebrd_ineligible', 'eu_sanctions'],
            'RO': ['ebrd_ineligible', 'eu_sanctions'],
            'HU': ['ebrd_ineligible', 'eu_sanctions'],
            'CZ': ['ebrd_ineligible', 'eu_sanctions'],
            'TR': ['ebrd_ineligible'],
            # Africa
            'ZA': ['afdb_sanctions'],
            'NG': ['afdb_sanctions'],
            'KE': ['afdb_sanctions'],
            'EG': ['afdb_sanctions'],
            'MA': ['afdb_sanctions'],
            'GH': ['afdb_sanctions'],
            'TZ': ['afdb_sanctions'],
            'ET': ['afdb_sanctions'],
        },
        primary_extractor='opensanctions',
        requires_all=True,  # Sanctions require comprehensive coverage
    ),

    # =========================================================================
    # CORPORATE REGISTRIES
    # =========================================================================
    'corporate': ExtractorGroup(
        global_extractors=[
            'opencorporates',  # 145+ jurisdictions
            'gleif_lei',       # Global LEI registry
        ],
        locale_extractors={
            'UK': ['companies_house'],
            'AU': ['australia_abn'],
            'IN': ['india_mca'],
            # US uses SEC for public companies
            'US': [],  # OpenCorporates covers US
        },
        primary_extractor='opencorporates',
        requires_all=False,  # Usually one good source is enough
    ),

    # =========================================================================
    # SECURITIES REGULATORS
    # =========================================================================
    'securities': ExtractorGroup(
        global_extractors=[],  # No global securities regulator
        locale_extractors={
            'US': [
                'sec_filings',
                'sec_financials',
                'sec_litigation',
                'sec_governance',
            ],
            'CA': ['sedar_canada'],
        },
        primary_extractor='sec_filings',
        requires_all=False,
    ),

    # =========================================================================
    # REGULATORY / ENFORCEMENT
    # =========================================================================
    'regulatory': ExtractorGroup(
        global_extractors=[],
        locale_extractors={
            'US': [
                'ofac_sanctions',
                'epa_echo',
                'cfpb_complaints',
                'osha_violations',
                'faa_certificate',
                'fdic_enforcement',
                'bsee_incidents',
            ],
            'UK': ['uk_fca_register'],
            'EU': ['eu_safety_list'],
        },
        primary_extractor='epa_echo',
        requires_all=False,
    ),

    # =========================================================================
    # ENVIRONMENT
    # =========================================================================
    'environment': ExtractorGroup(
        global_extractors=[],
        locale_extractors={
            'US': ['epa_echo'],
            'EU': ['eea_environment'],
            'DE': ['eea_environment'],
            'FR': ['eea_environment'],
            'UK': ['eea_environment'],  # Historical data pre-Brexit
            'CA': ['canada_npri'],
        },
        primary_extractor='epa_echo',
        requires_all=False,
    ),

    # =========================================================================
    # DNS / DOMAIN - Always global
    # =========================================================================
    'dns': ExtractorGroup(
        global_extractors=[
            'email_auth',
            'dnssec',
            'dns_records',
            'whois_rdap',
        ],
        locale_extractors={},  # DNS is locale-independent
        primary_extractor='email_auth',
        requires_all=False,
    ),

    # =========================================================================
    # NETWORK SECURITY - Always global
    # =========================================================================
    'network': ExtractorGroup(
        global_extractors=[
            'security_headers',
            'security_txt',
            'cloud_infra',
            'cdn_usage',
            'waf_presence',
            'tls_config',
        ],
        locale_extractors={},
        primary_extractor='security_headers',
        requires_all=False,
    ),

    # =========================================================================
    # SECURITY / VULNERABILITIES
    # =========================================================================
    'security': ExtractorGroup(
        global_extractors=[
            'nvd_cve',
        ],
        locale_extractors={
            'US': ['hhs_breach'],  # HIPAA is US-only
        },
        primary_extractor='nvd_cve',
        requires_all=False,
    ),

    # =========================================================================
    # INDUSTRY REGISTRIES
    # =========================================================================
    'industry': ExtractorGroup(
        global_extractors=[
            'pcaob',           # International auditor registry
            'aviation_safety', # Global aviation database
        ],
        locale_extractors={},
        primary_extractor='pcaob',
        requires_all=False,
    ),

    # =========================================================================
    # MARITIME / AVIATION
    # =========================================================================
    'maritime': ExtractorGroup(
        global_extractors=[
            'imo_gisis',     # Global ship registry
            'iosa_registry', # Global airline safety
        ],
        locale_extractors={
            'US': ['faa_certificate'],
            'EU': ['eu_safety_list'],
        },
        primary_extractor='imo_gisis',
        requires_all=False,
    ),
}


# TLD to locale mapping for automatic detection
TLD_TO_LOCALE: Dict[str, str] = {
    # North America
    'us': 'US', 'ca': 'CA', 'mx': 'MX',
    # Europe
    'uk': 'UK', 'co.uk': 'UK', 'org.uk': 'UK',
    'de': 'DE', 'fr': 'FR', 'it': 'IT', 'es': 'ES',
    'nl': 'NL', 'be': 'BE', 'at': 'AT', 'ch': 'CH',
    'pl': 'PL', 'cz': 'CZ', 'hu': 'HU', 'ro': 'RO',
    'se': 'SE', 'no': 'NO', 'dk': 'DK', 'fi': 'FI',
    'ie': 'IE', 'pt': 'PT', 'gr': 'GR',
    # EU generic
    'eu': 'EU',
    # Asia-Pacific
    'jp': 'JP', 'cn': 'CN', 'kr': 'KR', 'in': 'IN',
    'au': 'AU', 'nz': 'NZ', 'sg': 'SG', 'hk': 'HK',
    'tw': 'TW', 'th': 'TH', 'vn': 'VN', 'ph': 'PH',
    'id': 'ID', 'my': 'MY',
    # South America
    'br': 'BR', 'ar': 'AR', 'cl': 'CL', 'co': 'CO', 'pe': 'PE',
    # Middle East / Africa
    'ae': 'AE', 'sa': 'SA', 'il': 'IL', 'za': 'ZA',
    'ng': 'NG', 'ke': 'KE', 'eg': 'EG', 'ma': 'MA',
    # CIS
    'ru': 'RU', 'ua': 'UA', 'kz': 'KZ', 'by': 'BY',
    # Others
    'tr': 'TR',
    # Generic TLDs default to global
    'com': None, 'org': None, 'net': None, 'io': None,
}


class JurisdictionRouter:
    """
    Routes signal extraction to appropriate data sources based on jurisdiction.

    The router considers:
    - Entity's detected locale (from domain TLD or explicit)
    - Signal type requirements (sanctions need comprehensive, corporate needs one)
    - Routing strategy (locale-only, global, combined, all)

    Example:
        router = JurisdictionRouter()

        # UK company sanctions check - gets UK-specific + global sources
        extractors = router.get_extractors(
            signal_type='sanctions',
            locale='UK',
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL
        )
        # Returns: ['uk_ofsi', 'opensanctions', 'interpol_red_notices', ...]

        # Quick corporate lookup - just needs one source
        extractors = router.get_extractors(
            signal_type='corporate',
            locale='UK',
            strategy=RoutingStrategy.PRIMARY_ONLY
        )
        # Returns: ['companies_house']  (locale-specific is preferred)
    """

    def __init__(
        self,
        mappings: Optional[Dict[str, ExtractorGroup]] = None,
        default_locale: str = 'US',
    ):
        """
        Initialize the router.

        Args:
            mappings: Custom jurisdiction mappings (uses defaults if None)
            default_locale: Fallback locale when detection fails
        """
        self.mappings = mappings or JURISDICTION_MAPPINGS
        self.default_locale = default_locale

    def detect_locale_from_domain(self, domain: str) -> Optional[str]:
        """
        Detect locale from domain TLD.

        Args:
            domain: Domain name (e.g., 'example.co.uk')

        Returns:
            Locale code or None for generic TLDs
        """
        if not domain:
            return None

        domain = domain.lower().strip()

        # Check compound TLDs first (e.g., co.uk)
        parts = domain.split('.')
        if len(parts) >= 2:
            compound_tld = '.'.join(parts[-2:])
            if compound_tld in TLD_TO_LOCALE:
                return TLD_TO_LOCALE[compound_tld]

        # Check simple TLD
        tld = parts[-1] if parts else None
        if tld and tld in TLD_TO_LOCALE:
            return TLD_TO_LOCALE[tld]

        return None

    def get_extractors(
        self,
        signal_type: str,
        locale: Optional[str] = None,
        domain: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.LOCALE_PLUS_GLOBAL,
        max_tier: ExtractorTier = ExtractorTier.FREE,
        include_tiers: Optional[List[ExtractorTier]] = None,
    ) -> List[str]:
        """
        Get list of extractors to use for a signal type and locale.

        Args:
            signal_type: Type of signal (sanctions, corporate, regulatory, etc.)
            locale: Explicit locale code (e.g., 'UK', 'US', 'DE')
            domain: Domain for automatic locale detection (used if locale is None)
            strategy: How to select extractors
            max_tier: Maximum tier to include (FREE only includes free extractors,
                     PAID_BASIC includes free + paid_basic, etc.)
            include_tiers: Explicit list of tiers to include (overrides max_tier)

        Returns:
            List of extractor names to call
        """
        # Get the extractor group for this signal type
        group = self.mappings.get(signal_type)
        if not group:
            logger.warning(f"Unknown signal type: {signal_type}")
            return []

        # Detect locale if not provided
        if locale is None and domain:
            locale = self.detect_locale_from_domain(domain)

        # Use default if still None
        if locale is None:
            locale = self.default_locale

        locale = locale.upper()

        # Build tier filter
        if include_tiers:
            allowed_tiers = set(include_tiers)
        else:
            # Build cumulative tier set based on max_tier
            tier_order = [
                ExtractorTier.FREE,
                ExtractorTier.PAID_BASIC,
                ExtractorTier.PAID_PREMIUM,
                ExtractorTier.ENTERPRISE,
            ]
            max_tier_index = tier_order.index(max_tier)
            allowed_tiers = set(tier_order[:max_tier_index + 1])

        # Select extractors based on strategy
        extractors: List[str] = []

        if strategy == RoutingStrategy.PRIMARY_ONLY:
            # Just the primary extractor
            if group.primary_extractor:
                # Prefer locale-specific primary if available
                locale_extractors = group.locale_extractors.get(locale, [])
                if locale_extractors:
                    extractors = [locale_extractors[0]]
                else:
                    extractors = [group.primary_extractor]

        elif strategy == RoutingStrategy.LOCALE_ONLY:
            # Only locale-specific extractors
            extractors = group.locale_extractors.get(locale, []).copy()

        elif strategy == RoutingStrategy.GLOBAL_ONLY:
            # Only global extractors
            extractors = group.global_extractors.copy()

        elif strategy == RoutingStrategy.LOCALE_PLUS_GLOBAL:
            # Combine locale-specific and global (recommended)
            extractors = group.locale_extractors.get(locale, []).copy()
            extractors.extend(group.global_extractors)

        elif strategy == RoutingStrategy.ALL:
            # All extractors regardless of locale
            extractors = group.global_extractors.copy()
            for locale_list in group.locale_extractors.values():
                for ext in locale_list:
                    if ext not in extractors:
                        extractors.append(ext)

        # Filter by tier
        def is_allowed_tier(ext_name: str) -> bool:
            tier = EXTRACTOR_TIERS.get(ext_name, ExtractorTier.FREE)
            return tier in allowed_tiers

        extractors = [e for e in extractors if is_allowed_tier(e)]

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_extractors: List[str] = []
        for ext in extractors:
            if ext not in seen:
                seen.add(ext)
                unique_extractors.append(ext)

        return unique_extractors

    def get_routing_plan(
        self,
        signal_type: str,
        locale: Optional[str] = None,
        domain: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.LOCALE_PLUS_GLOBAL,
    ) -> Dict:
        """
        Get a detailed routing plan with metadata.

        Returns a dict with:
        - extractors: List of extractor names
        - locale: Detected/provided locale
        - strategy: Strategy used
        - requires_all: Whether all extractors should complete
        - primary: Recommended primary extractor

        Useful for debugging and logging extraction plans.
        """
        group = self.mappings.get(signal_type)
        if not group:
            return {
                'extractors': [],
                'locale': locale,
                'strategy': strategy.value,
                'error': f'Unknown signal type: {signal_type}',
            }

        # Detect locale
        detected_locale = locale
        if detected_locale is None and domain:
            detected_locale = self.detect_locale_from_domain(domain)
        if detected_locale is None:
            detected_locale = self.default_locale

        extractors = self.get_extractors(
            signal_type=signal_type,
            locale=detected_locale,
            strategy=strategy,
        )

        return {
            'signal_type': signal_type,
            'extractors': extractors,
            'extractor_count': len(extractors),
            'locale': detected_locale,
            'locale_source': 'explicit' if locale else ('domain' if domain else 'default'),
            'strategy': strategy.value,
            'requires_all': group.requires_all,
            'primary_extractor': group.primary_extractor,
            'global_sources': [e for e in extractors if e in group.global_extractors],
            'locale_sources': [e for e in extractors if e in group.locale_extractors.get(detected_locale, [])],
        }

    def get_all_locales_for_signal(self, signal_type: str) -> List[str]:
        """Get all locales that have specific extractors for a signal type."""
        group = self.mappings.get(signal_type)
        if not group:
            return []
        return list(group.locale_extractors.keys())

    def get_signal_types(self) -> List[str]:
        """Get all available signal types."""
        return list(self.mappings.keys())
