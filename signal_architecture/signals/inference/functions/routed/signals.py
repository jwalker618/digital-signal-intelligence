"""
Routed Signal Functions

Ready-to-use inference functions that leverage the multi-source routing module
for comprehensive, jurisdiction-aware signal extraction.

Each function:
1. Uses the routing module to determine which extractors to call
2. Executes extractors in parallel
3. Normalizes results to a unified schema
4. Converts to a signal score (0-100)

These functions automatically use the entity's locale from InferenceContext
to route to appropriate regional and global data sources.
"""

import time
import logging
from typing import Optional

from ....types import SignalResult, InferenceContext
from ....aggregators.routing_bridges import (
    SanctionsSignalBridge,
    CorporateSignalBridge,
    DNSSignalBridge,
    NetworkSignalBridge,
    SecuritySignalBridge,
)

logger = logging.getLogger(__name__)


def sanctions_check_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Multi-source sanctions check using jurisdiction-aware routing.

    Checks against appropriate sanctions lists based on entity locale:
    - Global: OpenSanctions, Interpol, FBI, World Bank
    - US: OFAC SDN
    - UK: UK OFSI
    - EU: EU Consolidated Sanctions
    - Asia-Pacific: ADB
    - Americas: IDB
    - Europe/Central Asia: EBRD
    - Africa: AfDB

    Args:
        entity_id: Entity name to check
        context: InferenceContext with locale information

    Returns:
        SignalResult with score (95=clear, 5=confirmed sanctioned)

    Example YAML config:
        signal_features:
          - id: sanctions_exposure
            name: Sanctions Exposure
            weight: 0.15
            inference_utility_function: sanctions_check_routed
            score_conditions:
              - max: 30
                tier_override: 5
                modifier: null
                note: High sanctions risk - possible match
    """
    start_time = time.time()

    try:
        bridge = SanctionsSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        # Determine confidence based on sources
        confidence = data.get('confidence', 0.8)

        # V7 Phase 3: zero-match across the queried sanctions registers is an
        # authoritative-empty result, not absence-of-data. The signal is clean
        # AND the source has authoritatively confirmed there's nothing to find.
        total_matches = data.get('total_matches', 0)
        sources_checked = data.get('sources_checked', []) or []
        absence_sub_type = (
            "absence_authoritative_empty"
            if total_matches == 0 and not data.get('error') and len(sources_checked) > 0
            else None
        )

        return SignalResult(
            signal_id='sanctions_check_routed',
            score=data.get('score', 50),
            confidence=confidence,
            raw_data={
                'risk_level': data.get('risk_level'),
                'total_matches': data.get('total_matches', 0),
                'confirmed_sanctioned': data.get('confirmed_sanctioned', False),
                'highest_match_score': data.get('highest_match_score', 0),
            },
            aggregated_data=data,
            metadata={
                'sources_checked': data.get('sources_checked', []),
                'sources_with_matches': data.get('sources_with_matches', []),
                'locale': data.get('locale'),
                'strategy': data.get('strategy'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
            absence_sub_type=absence_sub_type,
        )

    except Exception as e:
        logger.error(f"sanctions_check_routed failed: {e}")
        return SignalResult(
            signal_id='sanctions_check_routed',
            score=50,  # Neutral on error
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def corporate_registry_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Multi-source corporate registry verification.

    Checks against appropriate registries based on locale:
    - Global: OpenCorporates (145 jurisdictions), GLEIF LEI
    - UK: Companies House
    - Australia: Australian Business Register
    - India: MCA

    Score interpretation:
    - 90+: Found in multiple registries, all details verified
    - 70-89: Found in registry, active status
    - 50-69: Found but limited information
    - 30-49: Not found or inactive
    - <30: Dissolved or concerning status

    Args:
        entity_id: Company name or registration number
        context: InferenceContext with locale

    Returns:
        SignalResult with combined registration score
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_registry_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'records_found': data.get('records_found', 0),
                'any_active': data.get('any_active', False),
                'lei': data.get('lei'),
            },
            aggregated_data=data,
            metadata={
                'sources_checked': data.get('sources_checked', []),
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"corporate_registry_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_registry_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def corporate_status_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Corporate status check - is the company active?

    Returns the status_score component from corporate lookup:
    - 90: Active in registry
    - 50: Status unknown
    - 20: Dissolved/inactive

    Use this when you specifically need the activity status signal
    separate from the full corporate registry check.
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_status_routed',
            score=data.get('status_score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'any_active': data.get('any_active', False),
                'any_dissolved': data.get('any_dissolved', False),
            },
            aggregated_data=data,
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"corporate_status_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_status_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def corporate_age_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Corporate age/establishment check.

    Returns the age_score component:
    - 95: > 10 years old
    - 85: > 5 years old
    - 70: > 2 years old
    - 55: > 1 year old
    - 35: < 1 year old (newly formed)

    Newer companies are generally higher risk in insurance contexts.
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='corporate_age_routed',
            score=data.get('age_score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'primary_record': data.get('primary_record'),
            },
            aggregated_data=data,
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"corporate_age_routed failed: {e}")
        return SignalResult(
            signal_id='corporate_age_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def lei_verification_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Legal Entity Identifier (LEI) verification.

    Checks if the entity has a valid LEI via GLEIF.
    Having an LEI indicates:
    - Regulated entity or significant financial participant
    - Verified legal identity
    - Meets ISO 17442 standards

    Score:
    - 90: Has valid LEI
    - 50: No LEI found (not necessarily bad for smaller entities)
    """
    start_time = time.time()

    try:
        bridge = CorporateSignalBridge()
        data = bridge.get_signal_score(
            entity_id=entity_id,
            context=context,
        )

        # LEI-specific scoring
        has_lei = data.get('lei') is not None
        lei_status = data.get('lei_status', '')

        if has_lei and lei_status.upper() in ('ISSUED', 'ACTIVE'):
            score = 90
        elif has_lei:
            score = 70  # Has LEI but status is unclear
        else:
            score = 50  # No LEI - neutral for most entities

        return SignalResult(
            signal_id='lei_verification_routed',
            score=score,
            confidence=data.get('confidence', 0.8),
            raw_data={
                'lei': data.get('lei'),
                'lei_status': lei_status,
            },
            aggregated_data={'lei_score': data.get('lei_score', 50)},
            metadata={
                'locale': data.get('locale'),
                'routing_type': 'multi_source',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"lei_verification_routed failed: {e}")
        return SignalResult(
            signal_id='lei_verification_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


# =============================================================================
# DNS Signal Functions
# =============================================================================

def email_auth_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Email authentication configuration check (SPF, DKIM, DMARC).

    Evaluates the entity's email security posture:
    - 95: All three mechanisms configured correctly
    - 75: Two of three configured
    - 50: Only one configured
    - 25: None configured (high spam/phishing risk)

    Strong email authentication indicates:
    - Security-conscious organization
    - Lower phishing risk
    - Professional IT operations

    Args:
        domain: Domain to check (uses context.discovered_domain if None)
        context: InferenceContext

    Returns:
        SignalResult with email auth score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='email_auth_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = DNSSignalBridge()
        data = bridge.get_email_auth_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='email_auth_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'spf_configured': data.get('spf_configured', False),
                'dkim_configured': data.get('dkim_configured', False),
                'dmarc_configured': data.get('dmarc_configured', False),
                'dmarc_policy': data.get('dmarc_policy'),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'mechanisms_configured': data.get('mechanisms_configured', 0),
                'routing_type': 'dns',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"email_auth_routed failed: {e}")
        return SignalResult(
            signal_id='email_auth_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def dnssec_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    DNSSEC validation check.

    Evaluates DNS security:
    - 90: DNSSEC enabled and validating correctly
    - 50: DNSSEC not enabled (neutral - many legitimate sites don't use it)
    - 20: DNSSEC configured but invalid (misconfiguration is concerning)

    Args:
        domain: Domain to check
        context: InferenceContext

    Returns:
        SignalResult with DNSSEC score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='dnssec_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = DNSSignalBridge()
        data = bridge.get_dnssec_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='dnssec_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'dnssec_enabled': data.get('dnssec_enabled', False),
                'dnssec_valid': data.get('dnssec_valid', False),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'routing_type': 'dns',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"dnssec_routed failed: {e}")
        return SignalResult(
            signal_id='dnssec_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def domain_age_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Domain age verification via WHOIS/RDAP.

    Older domains are generally lower risk:
    - 95: > 10 years old
    - 85: > 5 years old
    - 70: > 2 years old
    - 55: > 1 year old
    - 35: > 6 months old
    - 15: < 6 months old (very new - higher risk)

    Very new domains are commonly associated with fraud/phishing.

    Args:
        domain: Domain to check
        context: InferenceContext

    Returns:
        SignalResult with domain age score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='domain_age_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = DNSSignalBridge()
        data = bridge.get_domain_age_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='domain_age_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'domain_age_days': data.get('domain_age_days'),
                'domain_age_years': data.get('domain_age_years'),
                'registered': data.get('registered', True),
                'privacy_protected': data.get('privacy_protected', False),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'registrar': data.get('registrar'),
                'routing_type': 'dns',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"domain_age_routed failed: {e}")
        return SignalResult(
            signal_id='domain_age_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


# =============================================================================
# Network Signal Functions
# =============================================================================

def security_headers_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    HTTP security headers check.

    Evaluates security header configuration:
    - HSTS (Strict-Transport-Security)
    - CSP (Content-Security-Policy)
    - X-Content-Type-Options
    - X-Frame-Options
    - Referrer-Policy
    - Permissions-Policy

    Higher scores indicate better security posture.

    Args:
        domain: Domain to check
        context: InferenceContext

    Returns:
        SignalResult with security headers score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='security_headers_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = NetworkSignalBridge()
        data = bridge.get_security_headers_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='security_headers_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'hsts_present': data.get('hsts_present', False),
                'csp_present': data.get('csp_present', False),
                'headers_found': data.get('headers_found', []),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'routing_type': 'network',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"security_headers_routed failed: {e}")
        return SignalResult(
            signal_id='security_headers_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def tls_config_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    TLS/SSL configuration check.

    Evaluates:
    - TLS version (1.2 minimum, 1.3 preferred)
    - Certificate validity
    - Certificate expiration
    - Cipher strength

    Poor TLS configuration indicates security risk.

    Args:
        domain: Domain to check
        context: InferenceContext

    Returns:
        SignalResult with TLS configuration score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='tls_config_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = NetworkSignalBridge()
        data = bridge.get_tls_config_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='tls_config_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'tls_version': data.get('tls_version'),
                'certificate_valid': data.get('certificate_valid'),
                'days_until_expiry': data.get('days_until_expiry'),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'issuer': data.get('issuer'),
                'routing_type': 'network',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"tls_config_routed failed: {e}")
        return SignalResult(
            signal_id='tls_config_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def infrastructure_routed(
    domain: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Infrastructure maturity check.

    Evaluates enterprise infrastructure indicators:
    - Cloud provider (AWS, Azure, GCP, etc.)
    - CDN usage
    - WAF presence

    Using enterprise infrastructure indicates:
    - Technical maturity
    - Investment in operations
    - Better availability/security

    Args:
        domain: Domain to check
        context: InferenceContext

    Returns:
        SignalResult with infrastructure score
    """
    start_time = time.time()
    effective_domain = domain or (context.discovered_domain if context else None)

    if not effective_domain:
        return SignalResult(
            signal_id='infrastructure_routed',
            score=50,
            confidence=0.0,
            error='No domain provided or discovered',
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    try:
        bridge = NetworkSignalBridge()
        data = bridge.get_infrastructure_score(
            domain=effective_domain,
            context=context,
        )

        return SignalResult(
            signal_id='infrastructure_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'cloud_provider': data.get('cloud_provider'),
                'cdn': data.get('cdn'),
                'waf': data.get('waf'),
            },
            aggregated_data=data,
            metadata={
                'domain': effective_domain,
                'checks_completed': data.get('checks_completed', 0),
                'routing_type': 'network',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"infrastructure_routed failed: {e}")
        return SignalResult(
            signal_id='infrastructure_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


# =============================================================================
# Security Signal Functions
# =============================================================================

def vulnerability_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Vulnerability exposure check via NVD CVE database.

    Checks for known vulnerabilities in entity's products/technologies:
    - 95: No known critical/high vulnerabilities
    - 70: Some medium vulnerabilities
    - 40: High vulnerabilities present
    - 15: Critical vulnerabilities present

    This signal is most useful for technology companies or entities
    with known software products.

    Args:
        entity_id: Entity name or product identifier
        context: InferenceContext

    Returns:
        SignalResult with vulnerability score
    """
    start_time = time.time()

    try:
        bridge = SecuritySignalBridge()
        data = bridge.get_vulnerability_score(
            entity_id=entity_id,
            context=context,
        )

        return SignalResult(
            signal_id='vulnerability_routed',
            score=data.get('score', 50),
            confidence=data.get('confidence', 0.8),
            raw_data={
                'cve_count': data.get('cve_count', 0),
                'critical_count': data.get('critical_count', 0),
                'high_count': data.get('high_count', 0),
                'medium_count': data.get('medium_count', 0),
            },
            aggregated_data=data,
            metadata={
                'entity_id': entity_id,
                'routing_type': 'security',
            },
            error=data.get('error'),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
        )

    except Exception as e:
        logger.error(f"vulnerability_routed failed: {e}")
        return SignalResult(
            signal_id='vulnerability_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )


def breach_history_routed(
    entity_id: str,
    context: InferenceContext,
) -> SignalResult:
    """
    Data breach history check (HHS Breach Portal for healthcare).

    Checks if the entity has had reportable data breaches:
    - 95: No breaches found
    - 60: Minor breaches (< 500 affected)
    - 30: Major breaches (> 500 affected)
    - 10: Multiple major breaches

    Currently covers US healthcare via HHS Breach Portal.
    Lower scores indicate higher cyber risk.

    Args:
        entity_id: Entity name to check
        context: InferenceContext

    Returns:
        SignalResult with breach history score
    """
    start_time = time.time()

    try:
        bridge = SecuritySignalBridge()
        # Use the get_extractor pattern from bridge
        extractor = bridge._get_extractor('hhs_breach')

        if not extractor:
            return SignalResult(
                signal_id='breach_history_routed',
                score=50,
                confidence=0.0,
                error='HHS breach extractor not available',
                execution_time_ms=(time.time() - start_time) * 1000,
                evidence_grade="structured_attested",
                evidence_basis="Multi-source routed signal across authoritative registers",
                evidence_sources=[],
            )

        result = extractor.extract(entity_id)
        if not result.success:
            return SignalResult(
                signal_id='breach_history_routed',
                score=50,
                confidence=0.0,
                error=result.error,
                execution_time_ms=(time.time() - start_time) * 1000,
                evidence_grade="inferred",
                evidence_basis="Routed fallback (extractor/exception path)",
                evidence_sources=[],
            )

        data = result.data
        breaches = data.get('breaches', [])

        if not breaches:
            score = 95
            major_count = 0
            minor_count = 0
        else:
            major_count = sum(1 for b in breaches if b.get('individuals_affected', 0) >= 500)
            minor_count = len(breaches) - major_count

            if major_count > 1:
                score = 10
            elif major_count == 1:
                score = 30
            elif minor_count > 0:
                score = 60
            else:
                score = 80

        # V7 Phase 3: HHS confirmed zero breaches is an authoritative-empty
        # result — the source has affirmatively said "nothing here", not just
        # "no data".
        absence_sub_type = "absence_authoritative_empty" if not breaches else None

        return SignalResult(
            signal_id='breach_history_routed',
            score=score,
            confidence=0.85,
            raw_data={
                'breach_count': len(breaches),
                'major_breaches': major_count,
                'minor_breaches': minor_count,
            },
            aggregated_data=data,
            metadata={
                'entity_id': entity_id,
                'routing_type': 'security',
            },
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="structured_attested",
            evidence_basis="Multi-source routed signal across authoritative registers",
            evidence_sources=[],
            absence_sub_type=absence_sub_type,
        )

    except Exception as e:
        logger.error(f"breach_history_routed failed: {e}")
        return SignalResult(
            signal_id='breach_history_routed',
            score=50,
            confidence=0.0,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            evidence_grade="inferred",
            evidence_basis="Routed fallback (extractor/exception path)",
            evidence_sources=[],
        )
