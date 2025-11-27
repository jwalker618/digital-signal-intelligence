"""
Digital Signal Intelligence (DSI) - Website Discovery Module
=============================================================

This module solves the critical problem of identifying the correct corporate 
website for an organisation. It handles:

1. Simple company name lookup
2. Company name with domain hints
3. Subsidiary/parent company relationships (e.g., MS Amlin → MS&AD Insurance)
4. Disambiguation of common names
5. Validation of discovered websites

This is a generic module used by all DSI pricing models.

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import re
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class DiscoveryMethod(Enum):
    """How the website was discovered"""
    DIRECT_DOMAIN = "direct_domain"           # Domain provided directly
    SEARCH_ENGINE = "search_engine"           # Found via search
    CORPORATE_REGISTRY = "corporate_registry" # Found via Companies House, SEC, etc.
    INDUSTRY_DATABASE = "industry_database"   # Found via industry-specific database
    PARENT_COMPANY = "parent_company"         # Derived from parent company relationship
    DNS_ENUMERATION = "dns_enumeration"       # Found via DNS analysis
    SOCIAL_MEDIA = "social_media"             # LinkedIn/social profiles point to it


class ConfidenceLevel(Enum):
    """Confidence that we have the correct corporate website"""
    HIGH = "high"           # 90%+ confidence - multiple signals align
    MEDIUM = "medium"       # 70-89% confidence - some ambiguity
    LOW = "low"             # 50-69% confidence - significant uncertainty
    UNVERIFIED = "unverified"  # <50% - requires manual verification


class WebsiteType(Enum):
    """Type of website discovered"""
    PRIMARY_CORPORATE = "primary_corporate"   # Main corporate website
    REGIONAL_VARIANT = "regional_variant"     # Regional version (e.g., .co.uk)
    PRODUCT_SITE = "product_site"             # Product-specific website
    INVESTOR_RELATIONS = "investor_relations" # Separate IR site
    CAREER_SITE = "career_site"               # Careers/jobs portal
    SUBSIDIARY = "subsidiary"                 # Subsidiary company site
    PARENT_COMPANY = "parent_company"         # Parent company site
    HOLDING_COMPANY = "holding_company"       # Ultimate holding company


class CompanyStructure(Enum):
    """Corporate structure type"""
    STANDALONE = "standalone"           # Independent company
    SUBSIDIARY = "subsidiary"           # Owned by parent
    HOLDING = "holding"                 # Holding company with subsidiaries
    DIVISION = "division"               # Division of larger company
    JOINT_VENTURE = "joint_venture"     # JV between companies
    BRAND = "brand"                     # Brand within larger company


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DomainInfo:
    """Information about a discovered domain"""
    domain: str
    tld: str
    registrar: Optional[str] = None
    registration_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    nameservers: List[str] = field(default_factory=list)
    dns_provider: Optional[str] = None
    hosting_provider: Optional[str] = None
    ssl_issuer: Optional[str] = None
    ssl_valid: bool = False
    redirects_to: Optional[str] = None
    is_parked: bool = False
    is_active: bool = True


@dataclass
class CorporateRelationship:
    """Relationship between companies"""
    related_company_name: str
    relationship_type: str  # "parent", "subsidiary", "sister", "brand"
    ownership_percentage: Optional[float] = None
    effective_date: Optional[datetime] = None
    source: str = ""
    related_domain: Optional[str] = None


@dataclass
class WebsiteCandidate:
    """A candidate website for the target company"""
    url: str
    domain: str
    website_type: WebsiteType
    discovery_method: DiscoveryMethod
    confidence_score: float  # 0-100
    evidence: List[str] = field(default_factory=list)
    domain_info: Optional[DomainInfo] = None
    
    # Validation signals
    company_name_match: float = 0.0        # How well does content match company name
    logo_match: bool = False                # Logo present and consistent
    contact_info_match: float = 0.0        # Contact info matches known data
    registration_match: float = 0.0        # Domain registration matches company
    ssl_organizational_match: float = 0.0  # SSL cert org matches
    social_links_valid: bool = False       # Social media links work and match
    
    # Red flags
    red_flags: List[str] = field(default_factory=list)


@dataclass
class CompanyIdentity:
    """Resolved company identity with all discovered information"""
    # Input
    input_name: str
    input_domain_hint: Optional[str] = None
    
    # Resolved identity
    legal_name: Optional[str] = None
    trading_names: List[str] = field(default_factory=list)
    company_number: Optional[str] = None  # Companies House, SEC CIK, etc.
    jurisdiction: Optional[str] = None
    
    # Corporate structure
    structure: CompanyStructure = CompanyStructure.STANDALONE
    parent_company: Optional['CompanyIdentity'] = None
    subsidiaries: List['CompanyIdentity'] = field(default_factory=list)
    relationships: List[CorporateRelationship] = field(default_factory=list)
    
    # Industry classification
    sic_codes: List[str] = field(default_factory=list)
    naics_codes: List[str] = field(default_factory=list)
    industry_description: Optional[str] = None


@dataclass
class DiscoveryResult:
    """Complete result of website discovery process"""
    # Input
    input_name: str
    input_domain_hint: Optional[str] = None
    
    # Primary result
    primary_website: Optional[WebsiteCandidate] = None
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    
    # All candidates
    all_candidates: List[WebsiteCandidate] = field(default_factory=list)
    
    # Corporate identity
    company_identity: Optional[CompanyIdentity] = None
    
    # Related websites
    related_websites: Dict[str, WebsiteCandidate] = field(default_factory=dict)
    # Keys: "parent", "subsidiaries", "regional", "product", etc.
    
    # Metadata
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    discovery_methods_used: List[DiscoveryMethod] = field(default_factory=list)
    search_queries_used: List[str] = field(default_factory=list)
    
    # Warnings and issues
    warnings: List[str] = field(default_factory=list)
    requires_manual_review: bool = False
    manual_review_reasons: List[str] = field(default_factory=list)


# =============================================================================
# WEBSITE DISCOVERY ENGINE
# =============================================================================

class WebsiteDiscoveryEngine:
    """
    Engine for discovering and validating corporate websites.
    
    Usage:
        engine = WebsiteDiscoveryEngine()
        result = engine.discover("MS Amlin")
        result = engine.discover("Petrobras", domain_hint="petrobras.com.br")
    """
    
    # Common corporate TLDs by priority
    CORPORATE_TLDS = [
        '.com', '.co.uk', '.com.au', '.co.nz', '.ca', '.de', '.fr', '.jp',
        '.com.br', '.mx', '.es', '.it', '.nl', '.ch', '.at', '.be',
        '.org', '.net', '.io', '.co', '.ai'
    ]
    
    # TLDs by country/region
    REGIONAL_TLDS = {
        'UK': ['.co.uk', '.uk', '.org.uk'],
        'US': ['.com', '.us', '.org'],
        'Germany': ['.de', '.com.de'],
        'France': ['.fr', '.com.fr'],
        'Japan': ['.jp', '.co.jp'],
        'Brazil': ['.com.br', '.br'],
        'Mexico': ['.mx', '.com.mx'],
        'Australia': ['.com.au', '.au'],
        'Netherlands': ['.nl'],
        'Switzerland': ['.ch'],
    }
    
    # Insurance-specific patterns
    INSURANCE_PATTERNS = {
        'parent_indicators': [
            'holdings', 'group', 'international', 'global', 'corporate',
            'plc', 'inc', 'ltd', 'gmbh', 'ag', 'sa', 'nv', 'bv'
        ],
        'subsidiary_indicators': [
            'insurance', 'underwriting', 'services', 'solutions',
            'reinsurance', 're', 'life', 'general', 'specialty'
        ]
    }
    
    # Common name variations to try
    NAME_VARIATIONS = [
        lambda x: x.lower().replace(' ', ''),      # "MS Amlin" → "msamlin"
        lambda x: x.lower().replace(' ', '-'),     # "MS Amlin" → "ms-amlin"
        lambda x: x.lower().replace(' ', '_'),     # "MS Amlin" → "ms_amlin"
        lambda x: ''.join(w[0] for w in x.split()).lower(),  # "MS Amlin" → "msa"
        lambda x: x.split()[0].lower() if ' ' in x else x.lower(),  # "MS Amlin" → "ms"
        lambda x: x.split()[-1].lower() if ' ' in x else x.lower(), # "MS Amlin" → "amlin"
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise the discovery engine.
        
        Args:
            config: Optional configuration dict with:
                - search_api_key: API key for search service
                - whois_service: WHOIS lookup service URL
                - registry_apis: Dict of corporate registry API configs
                - timeout: Request timeout in seconds
        """
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30)
        
    def discover(
        self,
        company_name: str,
        domain_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        industry_hint: Optional[str] = None,
        parent_company: Optional[str] = None
    ) -> DiscoveryResult:
        """
        Discover the corporate website for a company.
        
        Args:
            company_name: Company name to search for
            domain_hint: Optional domain hint (e.g., "petrobras.com.br")
            country_hint: Optional country hint (e.g., "Brazil", "UK")
            industry_hint: Optional industry (e.g., "insurance", "energy")
            parent_company: Optional parent company name
            
        Returns:
            DiscoveryResult with discovered websites and confidence levels
        """
        logger.info(f"Starting discovery for: {company_name}")
        
        result = DiscoveryResult(
            input_name=company_name,
            input_domain_hint=domain_hint
        )
        
        candidates: List[WebsiteCandidate] = []
        
        # Step 1: If domain hint provided, validate and use it
        if domain_hint:
            hint_candidate = self._validate_domain_hint(domain_hint, company_name)
            if hint_candidate:
                candidates.append(hint_candidate)
                result.discovery_methods_used.append(DiscoveryMethod.DIRECT_DOMAIN)
        
        # Step 2: Generate candidate domains from company name
        name_candidates = self._generate_name_candidates(
            company_name, country_hint, industry_hint
        )
        candidates.extend(name_candidates)
        
        # Step 3: Search corporate registries
        registry_candidates = self._search_corporate_registries(
            company_name, country_hint
        )
        candidates.extend(registry_candidates)
        if registry_candidates:
            result.discovery_methods_used.append(DiscoveryMethod.CORPORATE_REGISTRY)
        
        # Step 4: Search engine discovery
        search_candidates = self._search_engine_discovery(
            company_name, industry_hint
        )
        candidates.extend(search_candidates)
        if search_candidates:
            result.discovery_methods_used.append(DiscoveryMethod.SEARCH_ENGINE)
            result.search_queries_used.extend([
                f'"{company_name}" official website',
                f'"{company_name}" corporate',
                f'"{company_name}" investor relations'
            ])
        
        # Step 5: Check for parent company relationships
        if parent_company:
            parent_result = self.discover(parent_company, country_hint=country_hint)
            if parent_result.primary_website:
                result.related_websites['parent'] = parent_result.primary_website
                result.discovery_methods_used.append(DiscoveryMethod.PARENT_COMPANY)
        else:
            # Try to identify parent company from name patterns
            parent_info = self._identify_parent_company(company_name)
            if parent_info:
                result.company_identity = result.company_identity or CompanyIdentity(
                    input_name=company_name
                )
                result.company_identity.relationships.append(parent_info)
        
        # Step 6: Validate and score all candidates
        validated_candidates = self._validate_candidates(candidates, company_name)
        result.all_candidates = validated_candidates
        
        # Step 7: Select primary website
        if validated_candidates:
            primary = self._select_primary_website(validated_candidates)
            result.primary_website = primary
            result.confidence = self._determine_confidence(primary)
        
        # Step 8: Identify related websites
        result.related_websites.update(
            self._categorize_related_websites(validated_candidates, result.primary_website)
        )
        
        # Step 9: Check for manual review requirements
        self._check_manual_review_requirements(result)
        
        logger.info(f"Discovery complete. Confidence: {result.confidence.value}")
        return result
    
    def _validate_domain_hint(
        self, 
        domain_hint: str, 
        company_name: str
    ) -> Optional[WebsiteCandidate]:
        """Validate a provided domain hint"""
        # Clean the domain
        domain = self._clean_domain(domain_hint)
        
        if not domain:
            return None
        
        # Create candidate with high initial confidence since user provided it
        candidate = WebsiteCandidate(
            url=f"https://{domain}",
            domain=domain,
            website_type=WebsiteType.PRIMARY_CORPORATE,
            discovery_method=DiscoveryMethod.DIRECT_DOMAIN,
            confidence_score=80.0,  # Start high for user-provided hints
            evidence=["Domain provided as hint by user/system"]
        )
        
        # Validate the domain is accessible and related to company
        # In production, this would make actual HTTP requests
        candidate.evidence.append(f"Domain hint: {domain_hint}")
        
        return candidate
    
    def _generate_name_candidates(
        self,
        company_name: str,
        country_hint: Optional[str],
        industry_hint: Optional[str]
    ) -> List[WebsiteCandidate]:
        """Generate candidate domains from company name variations"""
        candidates = []
        
        # Clean and normalize company name
        clean_name = self._clean_company_name(company_name)
        
        # Get relevant TLDs
        tlds = self._get_relevant_tlds(country_hint)
        
        # Generate domain variations
        for variation_fn in self.NAME_VARIATIONS:
            try:
                name_variant = variation_fn(clean_name)
                if len(name_variant) < 2:
                    continue
                    
                for tld in tlds[:5]:  # Limit TLDs to check
                    domain = f"{name_variant}{tld}"
                    candidate = WebsiteCandidate(
                        url=f"https://{domain}",
                        domain=domain,
                        website_type=WebsiteType.PRIMARY_CORPORATE,
                        discovery_method=DiscoveryMethod.DNS_ENUMERATION,
                        confidence_score=50.0,  # Medium confidence for generated
                        evidence=[f"Generated from name: {company_name}"]
                    )
                    candidates.append(candidate)
            except Exception as e:
                logger.debug(f"Name variation failed: {e}")
                
        return candidates
    
    def _search_corporate_registries(
        self,
        company_name: str,
        country_hint: Optional[str]
    ) -> List[WebsiteCandidate]:
        """Search corporate registries for company information"""
        candidates = []
        
        # This would integrate with actual APIs in production:
        # - UK: Companies House API
        # - US: SEC EDGAR
        # - EU: European Business Register
        # - Global: OpenCorporates
        
        # Simulate registry lookup structure
        registry_sources = []
        
        if country_hint == 'UK' or not country_hint:
            registry_sources.append({
                'name': 'Companies House',
                'jurisdiction': 'UK',
                'api_endpoint': 'https://api.company-information.service.gov.uk'
            })
            
        if country_hint == 'US' or not country_hint:
            registry_sources.append({
                'name': 'SEC EDGAR',
                'jurisdiction': 'US',
                'api_endpoint': 'https://www.sec.gov/cgi-bin/browse-edgar'
            })
        
        # In production, actual API calls would be made here
        # For now, return empty list - to be implemented with real APIs
        
        return candidates
    
    def _search_engine_discovery(
        self,
        company_name: str,
        industry_hint: Optional[str]
    ) -> List[WebsiteCandidate]:
        """Use search engine to discover corporate website"""
        candidates = []
        
        # Search queries to try
        queries = [
            f'"{company_name}" official website',
            f'"{company_name}" corporate',
        ]
        
        if industry_hint:
            queries.append(f'"{company_name}" {industry_hint}')
        
        # In production, this would use search API (Google, Bing, etc.)
        # For now, return empty - to be implemented with actual search
        
        return candidates
    
    def _identify_parent_company(
        self,
        company_name: str
    ) -> Optional[CorporateRelationship]:
        """Attempt to identify parent company from name patterns"""
        
        # Known parent-subsidiary relationships in insurance
        KNOWN_RELATIONSHIPS = {
            'MS Amlin': {
                'parent': 'MS&AD Insurance Group Holdings',
                'relationship': 'subsidiary',
                'ownership': 100.0
            },
            'Amlin': {
                'parent': 'MS&AD Insurance Group Holdings',
                'relationship': 'brand',
                'note': 'Acquired by MS&AD in 2016'
            },
            'Lloyd\'s': {
                'parent': None,  # Lloyd's is a market, not a company
                'note': 'Lloyd\'s of London is an insurance market'
            },
            # Add more known relationships
        }
        
        # Check for exact match
        if company_name in KNOWN_RELATIONSHIPS:
            rel_info = KNOWN_RELATIONSHIPS[company_name]
            if rel_info.get('parent'):
                return CorporateRelationship(
                    related_company_name=rel_info['parent'],
                    relationship_type=rel_info.get('relationship', 'parent'),
                    ownership_percentage=rel_info.get('ownership'),
                    source='known_relationships_database'
                )
        
        # Check for parent company indicators in name
        name_lower = company_name.lower()
        for indicator in self.INSURANCE_PATTERNS['parent_indicators']:
            if indicator in name_lower:
                # This might be a holding company itself
                return None
        
        return None
    
    def _validate_candidates(
        self,
        candidates: List[WebsiteCandidate],
        company_name: str
    ) -> List[WebsiteCandidate]:
        """Validate all candidates and update their confidence scores"""
        validated = []
        
        for candidate in candidates:
            # In production, this would:
            # 1. Check if domain resolves
            # 2. Fetch the page and check for company name
            # 3. Verify SSL certificate organization
            # 4. Check WHOIS information
            # 5. Analyze page content for company indicators
            
            # For now, apply heuristic scoring
            score = candidate.confidence_score
            
            # Boost for known good TLDs
            if any(candidate.domain.endswith(tld) for tld in ['.com', '.co.uk', '.com.br']):
                score += 5
            
            # Boost for company name in domain
            clean_name = self._clean_company_name(company_name).lower()
            if clean_name.replace(' ', '') in candidate.domain.lower():
                score += 20
                candidate.company_name_match = 0.8
            
            # Penalize suspicious patterns
            if any(pattern in candidate.domain for pattern in ['-info', '-official', 'get', 'best']):
                score -= 20
                candidate.red_flags.append("Suspicious domain pattern")
            
            candidate.confidence_score = min(100, max(0, score))
            validated.append(candidate)
        
        # Sort by confidence
        validated.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Remove duplicates (same domain)
        seen_domains = set()
        unique = []
        for c in validated:
            if c.domain not in seen_domains:
                seen_domains.add(c.domain)
                unique.append(c)
        
        return unique
    
    def _select_primary_website(
        self,
        candidates: List[WebsiteCandidate]
    ) -> WebsiteCandidate:
        """Select the primary corporate website from candidates"""
        if not candidates:
            raise ValueError("No candidates to select from")
        
        # Already sorted by confidence
        primary = candidates[0]
        
        # Check if there's a clear winner
        if len(candidates) > 1:
            gap = primary.confidence_score - candidates[1].confidence_score
            if gap < 10:
                primary.red_flags.append(
                    f"Close second candidate: {candidates[1].domain} "
                    f"(score: {candidates[1].confidence_score})"
                )
        
        return primary
    
    def _determine_confidence(
        self,
        candidate: WebsiteCandidate
    ) -> ConfidenceLevel:
        """Determine overall confidence level"""
        score = candidate.confidence_score
        red_flag_count = len(candidate.red_flags)
        
        if score >= 85 and red_flag_count == 0:
            return ConfidenceLevel.HIGH
        elif score >= 70 and red_flag_count <= 1:
            return ConfidenceLevel.MEDIUM
        elif score >= 50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNVERIFIED
    
    def _categorize_related_websites(
        self,
        candidates: List[WebsiteCandidate],
        primary: Optional[WebsiteCandidate]
    ) -> Dict[str, WebsiteCandidate]:
        """Categorize non-primary websites by type"""
        related = {}
        
        if not primary:
            return related
        
        primary_base = self._get_base_domain(primary.domain)
        
        for candidate in candidates:
            if candidate.domain == primary.domain:
                continue
            
            candidate_base = self._get_base_domain(candidate.domain)
            
            # Check for regional variants
            if candidate_base == primary_base:
                related.setdefault('regional', []).append(candidate)
            
            # Check for product sites (subdomain patterns)
            if f".{primary_base}" in candidate.domain:
                related.setdefault('product_sites', []).append(candidate)
        
        # Convert lists to single best candidate per category
        return {k: v[0] if isinstance(v, list) else v for k, v in related.items()}
    
    def _check_manual_review_requirements(
        self,
        result: DiscoveryResult
    ) -> None:
        """Check if manual review is required"""
        reasons = []
        
        if result.confidence == ConfidenceLevel.UNVERIFIED:
            reasons.append("Confidence level below threshold")
        
        if result.confidence == ConfidenceLevel.LOW:
            reasons.append("Low confidence - verification recommended")
        
        if result.primary_website and len(result.primary_website.red_flags) > 0:
            reasons.append(f"Red flags detected: {result.primary_website.red_flags}")
        
        if len(result.all_candidates) == 0:
            reasons.append("No candidates found")
        
        if len(result.all_candidates) > 1:
            top_two = result.all_candidates[:2]
            if len(top_two) == 2:
                score_gap = top_two[0].confidence_score - top_two[1].confidence_score
                if score_gap < 15:
                    reasons.append(
                        f"Ambiguous results: top candidates within {score_gap} points"
                    )
        
        if reasons:
            result.requires_manual_review = True
            result.manual_review_reasons = reasons
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def _clean_domain(self, domain: str) -> str:
        """Clean and normalize a domain string"""
        # Remove protocol
        domain = re.sub(r'^https?://', '', domain)
        # Remove path
        domain = domain.split('/')[0]
        # Remove www
        domain = re.sub(r'^www\.', '', domain)
        # Lowercase
        domain = domain.lower().strip()
        return domain
    
    def _clean_company_name(self, name: str) -> str:
        """Clean company name for domain generation"""
        # Remove common suffixes
        suffixes = [
            'limited', 'ltd', 'plc', 'inc', 'incorporated', 'corp', 'corporation',
            'llc', 'llp', 'gmbh', 'ag', 'sa', 'nv', 'bv', 'pty', 'pvt',
            'holdings', 'group', 'international', '& co', 'and co'
        ]
        
        name_lower = name.lower()
        for suffix in suffixes:
            name_lower = re.sub(rf'\b{suffix}\b\.?', '', name_lower)
        
        # Remove special characters
        name_lower = re.sub(r'[^\w\s]', '', name_lower)
        
        # Normalize whitespace
        name_lower = ' '.join(name_lower.split())
        
        return name_lower.strip()
    
    def _get_relevant_tlds(self, country_hint: Optional[str]) -> List[str]:
        """Get relevant TLDs based on country hint"""
        if country_hint and country_hint in self.REGIONAL_TLDS:
            # Prioritize regional TLDs but include common ones
            regional = self.REGIONAL_TLDS[country_hint]
            return regional + [t for t in self.CORPORATE_TLDS if t not in regional]
        return self.CORPORATE_TLDS
    
    def _get_base_domain(self, domain: str) -> str:
        """Extract base domain from full domain"""
        # Simple extraction - in production use tldextract library
        parts = domain.split('.')
        if len(parts) >= 2:
            # Handle .co.uk, .com.br, etc.
            if parts[-2] in ['co', 'com', 'org', 'net', 'gov']:
                return '.'.join(parts[-3:]) if len(parts) >= 3 else domain
            return '.'.join(parts[-2:])
        return domain


# =============================================================================
# BATCH DISCOVERY
# =============================================================================

class BatchWebsiteDiscovery:
    """
    Batch processing for multiple company website discoveries.
    """
    
    def __init__(self, engine: Optional[WebsiteDiscoveryEngine] = None):
        self.engine = engine or WebsiteDiscoveryEngine()
        
    def discover_batch(
        self,
        companies: List[Dict]
    ) -> Dict[str, DiscoveryResult]:
        """
        Discover websites for multiple companies.
        
        Args:
            companies: List of dicts with keys:
                - name: Company name (required)
                - domain_hint: Optional domain hint
                - country: Optional country hint
                - industry: Optional industry hint
                - parent: Optional parent company name
                
        Returns:
            Dict mapping company names to DiscoveryResults
        """
        results = {}
        
        for company in companies:
            name = company.get('name')
            if not name:
                continue
                
            result = self.engine.discover(
                company_name=name,
                domain_hint=company.get('domain_hint'),
                country_hint=company.get('country'),
                industry_hint=company.get('industry'),
                parent_company=company.get('parent')
            )
            
            results[name] = result
        
        return results
    
    def export_results(
        self,
        results: Dict[str, DiscoveryResult],
        format: str = 'dict'
    ) -> any:
        """Export results in specified format"""
        if format == 'dict':
            return {
                name: {
                    'primary_domain': r.primary_website.domain if r.primary_website else None,
                    'confidence': r.confidence.value,
                    'requires_review': r.requires_manual_review,
                    'candidates_count': len(r.all_candidates)
                }
                for name, r in results.items()
            }
        raise ValueError(f"Unknown format: {format}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def discover_website(
    company_name: str,
    domain_hint: Optional[str] = None,
    **kwargs
) -> DiscoveryResult:
    """
    Convenience function for single company discovery.
    
    Args:
        company_name: Company name to search for
        domain_hint: Optional domain hint
        **kwargs: Additional arguments passed to discover()
        
    Returns:
        DiscoveryResult
    """
    engine = WebsiteDiscoveryEngine()
    return engine.discover(company_name, domain_hint=domain_hint, **kwargs)


def validate_corporate_domain(
    domain: str,
    expected_company: str
) -> Tuple[bool, float, List[str]]:
    """
    Validate that a domain belongs to the expected company.
    
    Args:
        domain: Domain to validate
        expected_company: Expected company name
        
    Returns:
        Tuple of (is_valid, confidence_score, issues)
    """
    engine = WebsiteDiscoveryEngine()
    result = engine.discover(expected_company, domain_hint=domain)
    
    if result.primary_website and result.primary_website.domain == engine._clean_domain(domain):
        return (
            True,
            result.primary_website.confidence_score,
            result.primary_website.red_flags
        )
    
    return (False, 0.0, ["Domain does not match expected company"])


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Discover MS Amlin website
    engine = WebsiteDiscoveryEngine()
    
    # Simple discovery
    result = engine.discover("MS Amlin")
    print(f"MS Amlin Discovery:")
    print(f"  Primary: {result.primary_website.domain if result.primary_website else 'Not found'}")
    print(f"  Confidence: {result.confidence.value}")
    print(f"  Manual Review: {result.requires_manual_review}")
    print()
    
    # Discovery with hints
    result = engine.discover(
        "Petrobras",
        domain_hint="petrobras.com.br",
        country_hint="Brazil",
        industry_hint="energy"
    )
    print(f"Petrobras Discovery:")
    print(f"  Primary: {result.primary_website.domain if result.primary_website else 'Not found'}")
    print(f"  Confidence: {result.confidence.value}")
    print()
    
    # Batch discovery
    batch = BatchWebsiteDiscovery()
    results = batch.discover_batch([
        {"name": "MS Amlin", "country": "UK", "industry": "insurance"},
        {"name": "Petrobras", "domain_hint": "petrobras.com.br", "country": "Brazil"},
        {"name": "Boeing", "country": "US", "industry": "aerospace"}
    ])
    
    print("Batch Results:")
    for name, res in results.items():
        domain = res.primary_website.domain if res.primary_website else "Not found"
        print(f"  {name}: {domain} ({res.confidence.value})")
