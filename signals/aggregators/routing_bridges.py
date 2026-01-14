"""
Routing Bridge Aggregators

Bridge classes that connect the multi-source routing module to the existing
signal framework by converting unified schemas to signal scores.

These bridges allow inference functions to use the full power of multi-source
routing while returning standard SignalResult objects.

Usage:
    from signals.aggregators.routing_bridges import (
        SanctionsSignalBridge,
        CorporateSignalBridge,
    )

    # In an inference function
    bridge = SanctionsSignalBridge()
    result = bridge.get_signal_score(
        entity_id='Acme Corp',
        locale='UK',
        context=context
    )
    # Returns: {'score': 95, 'risk_level': 'clear', 'sources_checked': [...]}
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import AggregatorResult, ExtractorResult, InferenceContext
from ..routing import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    SanctionsAggregator,
    CorporateAggregator,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class RoutingBridge:
    """
    Base class for routing bridges.

    Provides common functionality for converting multi-source
    routing results to signal scores.
    """

    def __init__(
        self,
        router: Optional[JurisdictionRouter] = None,
        default_strategy: RoutingStrategy = RoutingStrategy.LOCALE_PLUS_GLOBAL,
        max_tier: ExtractorTier = ExtractorTier.FREE,
    ):
        self.router = router or JurisdictionRouter()
        self.default_strategy = default_strategy
        self.max_tier = max_tier

    def _get_locale(self, context: Optional[InferenceContext], locale: Optional[str]) -> str:
        """Get locale from context or parameter, with fallback to US."""
        if locale:
            return locale.upper()
        if context and context.entity_locale:
            return context.entity_locale.upper()
        if context and context.discovered_domain:
            detected = self.router.detect_locale_from_domain(context.discovered_domain)
            if detected:
                return detected.upper()
        return 'US'  # Default fallback


class SanctionsSignalBridge(RoutingBridge):
    """
    Bridge that converts SanctionsResult to a signal score.

    Maps risk levels to scores:
    - CLEAR: 95 (no concerns)
    - LOW: 75 (minor/unlikely matches)
    - MEDIUM: 50 (some concern, needs review)
    - HIGH: 25 (significant match)
    - CRITICAL: 5 (confirmed sanctioned)
    """

    RISK_TO_SCORE = {
        RiskLevel.CLEAR: 95,
        RiskLevel.LOW: 75,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 25,
        RiskLevel.CRITICAL: 5,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aggregator = SanctionsAggregator(
            router=self.router,
            default_strategy=self.default_strategy,
        )

    def get_signal_score(
        self,
        entity_id: str,
        locale: Optional[str] = None,
        context: Optional[InferenceContext] = None,
        strategy: Optional[RoutingStrategy] = None,
    ) -> Dict[str, Any]:
        """
        Get a signal score from multi-source sanctions check.

        Args:
            entity_id: Entity name or identifier to check
            locale: Explicit locale (uses context.entity_locale if None)
            context: InferenceContext with locale and caching
            strategy: Override routing strategy

        Returns:
            Dict with 'score', 'risk_level', 'confidence', 'sources_checked', etc.
        """
        start_time = time.time()
        effective_locale = self._get_locale(context, locale)
        effective_strategy = strategy or self.default_strategy

        try:
            # Run multi-source aggregation
            result = self.aggregator.aggregate(
                entity_id=entity_id,
                signal_type='sanctions',
                locale=effective_locale,
                strategy=effective_strategy,
            )

            sanctions_result = result.result
            score = self.RISK_TO_SCORE.get(sanctions_result.risk_level, 50)

            # Calculate confidence based on sources checked vs failed
            total_sources = len(result.extractors_called)
            failed_sources = len(result.extractors_failed)
            confidence = 1.0 - (failed_sources / total_sources) if total_sources > 0 else 0.5

            return {
                'score': score,
                'risk_level': sanctions_result.risk_level.value,
                'confidence': confidence,
                'total_matches': sanctions_result.total_matches,
                'confirmed_sanctioned': sanctions_result.confirmed_sanctioned,
                'highest_match_score': sanctions_result.highest_match_score,
                'sources_checked': sanctions_result.sources_checked,
                'sources_with_matches': sanctions_result.sources_with_matches,
                'failed_sources': sanctions_result.failed_sources,
                'locale': effective_locale,
                'strategy': effective_strategy.value,
                'execution_time_ms': (time.time() - start_time) * 1000,
                'matches': [
                    {
                        'name': m.matched_name,
                        'source': m.source,
                        'score': m.match_score,
                        'program': m.program.value,
                    }
                    for m in sanctions_result.matches[:10]  # Limit to top 10
                ],
            }

        except Exception as e:
            logger.error(f"Sanctions signal bridge failed: {e}")
            return {
                'score': 50,  # Neutral score on error
                'risk_level': 'unknown',
                'confidence': 0.0,
                'error': str(e),
                'locale': effective_locale,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

    def to_aggregator_result(
        self,
        entity_id: str,
        locale: Optional[str] = None,
        context: Optional[InferenceContext] = None,
    ) -> AggregatorResult:
        """
        Get result as standard AggregatorResult for pipeline compatibility.
        """
        data = self.get_signal_score(entity_id, locale, context)
        return AggregatorResult(
            success=data.get('error') is None,
            data=data,
            aggregated_at=datetime.utcnow(),
            source_extractions=len(data.get('sources_checked', [])),
            sources=data.get('sources_checked', []),
            warnings=data.get('failed_sources', []),
            error=data.get('error'),
        )


class CorporateSignalBridge(RoutingBridge):
    """
    Bridge that converts CorporateResult to signal scores.

    Produces multiple scores for different aspects:
    - registration_score: Is the company properly registered?
    - status_score: Is the company active?
    - age_score: How established is the company?
    - lei_score: Does it have a Legal Entity Identifier?
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aggregator = CorporateAggregator(
            router=self.router,
            default_strategy=self.default_strategy,
        )

    def get_signal_score(
        self,
        entity_id: str,
        locale: Optional[str] = None,
        context: Optional[InferenceContext] = None,
        strategy: Optional[RoutingStrategy] = None,
    ) -> Dict[str, Any]:
        """
        Get signal scores from multi-source corporate lookup.

        Args:
            entity_id: Company name or registration number
            locale: Explicit locale
            context: InferenceContext
            strategy: Override routing strategy

        Returns:
            Dict with multiple scores and corporate data
        """
        start_time = time.time()
        effective_locale = self._get_locale(context, locale)
        effective_strategy = strategy or self.default_strategy

        try:
            result = self.aggregator.aggregate(
                entity_id=entity_id,
                signal_type='corporate',
                locale=effective_locale,
                strategy=effective_strategy,
            )

            corp_result = result.result

            # Calculate registration score (found in registries = good)
            if corp_result.records_found > 0:
                registration_score = min(100, 70 + (corp_result.records_found * 10))
            else:
                registration_score = 30  # Not found is concerning

            # Calculate status score
            if corp_result.any_active:
                status_score = 90
            elif corp_result.any_dissolved:
                status_score = 20
            else:
                status_score = 50  # Unknown status

            # Calculate age score from primary record
            age_score = 50  # Default
            if corp_result.primary_record and corp_result.primary_record.incorporation_date:
                from datetime import date
                age_days = (date.today() - corp_result.primary_record.incorporation_date).days
                if age_days > 3650:  # > 10 years
                    age_score = 95
                elif age_days > 1825:  # > 5 years
                    age_score = 85
                elif age_days > 730:  # > 2 years
                    age_score = 70
                elif age_days > 365:  # > 1 year
                    age_score = 55
                else:
                    age_score = 35  # Very new company

            # Calculate LEI score (having an LEI is good for larger entities)
            lei_score = 80 if corp_result.lei else 50

            # Combined score (weighted average)
            combined_score = (
                registration_score * 0.3 +
                status_score * 0.4 +
                age_score * 0.2 +
                lei_score * 0.1
            )

            # Confidence based on sources
            total_sources = len(result.extractors_called)
            failed_sources = len(result.extractors_failed)
            confidence = 1.0 - (failed_sources / total_sources) if total_sources > 0 else 0.5

            return {
                'score': round(combined_score, 1),
                'registration_score': registration_score,
                'status_score': status_score,
                'age_score': age_score,
                'lei_score': lei_score,
                'confidence': confidence,
                'records_found': corp_result.records_found,
                'any_active': corp_result.any_active,
                'any_dissolved': corp_result.any_dissolved,
                'lei': corp_result.lei,
                'lei_status': corp_result.lei_status,
                'sources_checked': corp_result.sources_checked,
                'sources_with_results': corp_result.sources_with_results,
                'failed_sources': corp_result.failed_sources,
                'locale': effective_locale,
                'primary_record': {
                    'name': corp_result.primary_record.name,
                    'jurisdiction': corp_result.primary_record.jurisdiction,
                    'status': corp_result.primary_record.status,
                    'is_active': corp_result.primary_record.is_active,
                    'source': corp_result.primary_record.source,
                } if corp_result.primary_record else None,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Corporate signal bridge failed: {e}")
            return {
                'score': 50,
                'confidence': 0.0,
                'error': str(e),
                'locale': effective_locale,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

    def to_aggregator_result(
        self,
        entity_id: str,
        locale: Optional[str] = None,
        context: Optional[InferenceContext] = None,
    ) -> AggregatorResult:
        """Get result as standard AggregatorResult."""
        data = self.get_signal_score(entity_id, locale, context)
        return AggregatorResult(
            success=data.get('error') is None,
            data=data,
            aggregated_at=datetime.utcnow(),
            source_extractions=len(data.get('sources_checked', [])),
            sources=data.get('sources_checked', []),
            warnings=data.get('failed_sources', []),
            error=data.get('error'),
        )


class RegulatorySignalBridge(RoutingBridge):
    """
    Bridge for regulatory/compliance signal.

    Placeholder for future implementation - will aggregate from:
    - EPA ECHO
    - OSHA violations
    - CFPB complaints
    - FDIC enforcement
    - UK FCA
    - etc.
    """

    def get_signal_score(
        self,
        entity_id: str,
        locale: Optional[str] = None,
        context: Optional[InferenceContext] = None,
        strategy: Optional[RoutingStrategy] = None,
    ) -> Dict[str, Any]:
        """Placeholder for regulatory signal aggregation."""
        # TODO: Implement RegulatoryAggregator and integrate here
        return {
            'score': 50,
            'confidence': 0.0,
            'error': 'Regulatory aggregator not yet implemented',
            'locale': self._get_locale(context, locale),
        }


class DNSSignalBridge(RoutingBridge):
    """
    Bridge for DNS-based signals.

    Aggregates from DNS extractors:
    - email_auth: SPF, DKIM, DMARC
    - dnssec: DNSSEC validation
    - whois_rdap: Domain registration info
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extractor_cache: Dict[str, Any] = {}

    def _get_extractor(self, name: str):
        """Get extractor with caching."""
        if name not in self._extractor_cache:
            try:
                from ..extractors.production.factory import get_extractor
                self._extractor_cache[name] = get_extractor(name, mode='production')
            except Exception as e:
                logger.warning(f"Could not get extractor {name}: {e}")
                self._extractor_cache[name] = None
        return self._extractor_cache[name]

    def get_email_auth_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get email authentication score (SPF, DKIM, DMARC).

        Score interpretation:
        - 95: All three configured correctly
        - 75: Two of three configured
        - 50: Only one configured
        - 25: None configured (high spam/phishing risk)
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('email_auth')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(domain)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data
            spf = data.get('spf', {})
            dkim = data.get('dkim', {})
            dmarc = data.get('dmarc', {})

            # Count configured mechanisms
            configured = 0
            if spf.get('exists'):
                configured += 1
            if dkim.get('exists'):
                configured += 1
            if dmarc.get('exists'):
                configured += 1

            # Score based on configuration
            if configured == 3:
                score = 95
            elif configured == 2:
                score = 75
            elif configured == 1:
                score = 50
            else:
                score = 25

            # Bonus for strict policies
            if dmarc.get('policy') == 'reject':
                score = min(100, score + 5)

            return {
                'score': score,
                'confidence': 0.95,
                'spf_configured': spf.get('exists', False),
                'dkim_configured': dkim.get('exists', False),
                'dmarc_configured': dmarc.get('exists', False),
                'dmarc_policy': dmarc.get('policy'),
                'mechanisms_configured': configured,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Email auth check failed: {e}")
            return {
                'score': 50,
                'confidence': 0.0,
                'error': str(e),
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

    def get_dnssec_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get DNSSEC validation score.

        Score interpretation:
        - 90: DNSSEC enabled and valid
        - 50: DNSSEC not enabled (neutral - many legitimate sites don't use it)
        - 20: DNSSEC configured but invalid (concerning)
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('dnssec')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(domain)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data
            enabled = data.get('dnssec_enabled', False)
            valid = data.get('dnssec_valid', False)

            if enabled and valid:
                score = 90
            elif enabled and not valid:
                score = 20  # Misconfigured is worse than not having it
            else:
                score = 50  # Neutral - many sites don't use DNSSEC

            return {
                'score': score,
                'confidence': 0.9,
                'dnssec_enabled': enabled,
                'dnssec_valid': valid,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"DNSSEC check failed: {e}")
            return {'score': 50, 'confidence': 0.0, 'error': str(e)}

    def get_domain_age_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get domain age score from WHOIS/RDAP.

        Score interpretation:
        - 95: > 10 years old
        - 85: > 5 years old
        - 70: > 2 years old
        - 55: > 1 year old
        - 35: > 6 months old
        - 15: < 6 months old (very new - higher risk)
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('whois_rdap')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(domain)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data
            age_days = data.get('domain_age_days')

            if age_days is None:
                return {
                    'score': 50,
                    'confidence': 0.3,
                    'domain_age_days': None,
                    'error': 'Could not determine domain age',
                }

            # Score based on age
            if age_days > 3650:  # > 10 years
                score = 95
            elif age_days > 1825:  # > 5 years
                score = 85
            elif age_days > 730:  # > 2 years
                score = 70
            elif age_days > 365:  # > 1 year
                score = 55
            elif age_days > 180:  # > 6 months
                score = 35
            else:
                score = 15  # Very new domain

            return {
                'score': score,
                'confidence': 0.9,
                'domain_age_days': age_days,
                'domain_age_years': round(age_days / 365, 1),
                'registered': data.get('registered', True),
                'privacy_protected': data.get('privacy_protected', False),
                'registrar': data.get('registrar'),
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Domain age check failed: {e}")
            return {'score': 50, 'confidence': 0.0, 'error': str(e)}


class NetworkSignalBridge(RoutingBridge):
    """
    Bridge for network/infrastructure signals.

    Aggregates from network extractors:
    - security_headers: HTTP security headers
    - tls_config: TLS/SSL configuration
    - cloud_infra: Cloud provider detection
    - cdn_usage: CDN detection
    - waf_presence: WAF detection
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extractor_cache: Dict[str, Any] = {}

    def _get_extractor(self, name: str):
        """Get extractor with caching."""
        if name not in self._extractor_cache:
            try:
                from ..extractors.production.factory import get_extractor
                self._extractor_cache[name] = get_extractor(name, mode='production')
            except Exception as e:
                logger.warning(f"Could not get extractor {name}: {e}")
                self._extractor_cache[name] = None
        return self._extractor_cache[name]

    def get_security_headers_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get security headers score.

        Checks for:
        - Strict-Transport-Security (HSTS)
        - Content-Security-Policy (CSP)
        - X-Content-Type-Options
        - X-Frame-Options
        - X-XSS-Protection (deprecated but still checked)

        Score: Based on number and quality of headers present.
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('security_headers')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(domain)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data
            headers = data.get('headers', {})

            # Score components
            score = 30  # Base score

            # HSTS (most important)
            if headers.get('strict_transport_security'):
                score += 20
                if 'includeSubDomains' in str(headers.get('strict_transport_security', '')):
                    score += 5

            # CSP
            if headers.get('content_security_policy'):
                score += 15

            # X-Content-Type-Options
            if headers.get('x_content_type_options') == 'nosniff':
                score += 10

            # X-Frame-Options
            if headers.get('x_frame_options'):
                score += 10

            # Referrer-Policy
            if headers.get('referrer_policy'):
                score += 5

            # Permissions-Policy
            if headers.get('permissions_policy'):
                score += 5

            score = min(100, score)

            return {
                'score': score,
                'confidence': 0.95,
                'hsts_present': bool(headers.get('strict_transport_security')),
                'csp_present': bool(headers.get('content_security_policy')),
                'headers_found': list(headers.keys()),
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Security headers check failed: {e}")
            return {'score': 50, 'confidence': 0.0, 'error': str(e)}

    def get_tls_config_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get TLS/SSL configuration score.

        Evaluates:
        - TLS version (1.2 minimum, 1.3 preferred)
        - Certificate validity
        - Certificate expiration
        - Cipher strength
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('tls_config')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(domain)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data

            score = 50  # Base

            # TLS version
            tls_version = data.get('tls_version', '')
            if 'TLSv1.3' in tls_version:
                score += 25
            elif 'TLSv1.2' in tls_version:
                score += 15
            elif 'TLSv1.1' in tls_version or 'TLSv1.0' in tls_version:
                score -= 20  # Old versions are concerning

            # Certificate validity
            if data.get('certificate_valid', False):
                score += 15
            else:
                score -= 30  # Invalid cert is bad

            # Certificate expiration
            days_until_expiry = data.get('days_until_expiry')
            if days_until_expiry:
                if days_until_expiry > 60:
                    score += 10
                elif days_until_expiry > 14:
                    score += 5
                elif days_until_expiry <= 0:
                    score -= 20  # Expired

            score = max(0, min(100, score))

            return {
                'score': score,
                'confidence': 0.9,
                'tls_version': tls_version,
                'certificate_valid': data.get('certificate_valid'),
                'days_until_expiry': days_until_expiry,
                'issuer': data.get('issuer'),
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"TLS config check failed: {e}")
            return {'score': 50, 'confidence': 0.0, 'error': str(e)}

    def get_infrastructure_score(
        self,
        domain: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get overall infrastructure quality score.

        Combines cloud, CDN, and WAF detection into an infrastructure
        maturity score. Using enterprise infrastructure is positive.
        """
        start_time = time.time()
        scores = []
        details = {}

        # Check cloud infrastructure
        try:
            extractor = self._get_extractor('cloud_infra')
            if extractor:
                result = extractor.extract(domain)
                if result.success:
                    data = result.data
                    provider = data.get('provider', 'unknown')
                    # Known cloud providers indicate maturity
                    if provider in ('aws', 'azure', 'gcp', 'cloudflare'):
                        scores.append(85)
                    elif provider != 'unknown':
                        scores.append(70)
                    else:
                        scores.append(50)
                    details['cloud_provider'] = provider
        except Exception as e:
            logger.debug(f"Cloud check failed: {e}")

        # Check CDN
        try:
            extractor = self._get_extractor('cdn_usage')
            if extractor:
                result = extractor.extract(domain)
                if result.success:
                    data = result.data
                    if data.get('cdn_detected'):
                        scores.append(80)
                        details['cdn'] = data.get('cdn_provider')
                    else:
                        scores.append(50)
        except Exception as e:
            logger.debug(f"CDN check failed: {e}")

        # Check WAF
        try:
            extractor = self._get_extractor('waf_presence')
            if extractor:
                result = extractor.extract(domain)
                if result.success:
                    data = result.data
                    if data.get('waf_detected'):
                        scores.append(85)
                        details['waf'] = data.get('waf_provider')
                    else:
                        scores.append(50)
        except Exception as e:
            logger.debug(f"WAF check failed: {e}")

        # Calculate combined score
        if scores:
            combined_score = sum(scores) / len(scores)
        else:
            combined_score = 50

        return {
            'score': round(combined_score, 1),
            'confidence': 0.8 if scores else 0.0,
            'cloud_provider': details.get('cloud_provider'),
            'cdn': details.get('cdn'),
            'waf': details.get('waf'),
            'checks_completed': len(scores),
            'execution_time_ms': (time.time() - start_time) * 1000,
        }


class SecuritySignalBridge(RoutingBridge):
    """
    Bridge for security/vulnerability signals.

    Aggregates from security extractors:
    - nvd_cve: Known vulnerabilities
    - hhs_breach: Healthcare breaches (US)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extractor_cache: Dict[str, Any] = {}

    def _get_extractor(self, name: str):
        """Get extractor with caching."""
        if name not in self._extractor_cache:
            try:
                from ..extractors.production.factory import get_extractor
                self._extractor_cache[name] = get_extractor(name, mode='production')
            except Exception as e:
                logger.warning(f"Could not get extractor {name}: {e}")
                self._extractor_cache[name] = None
        return self._extractor_cache[name]

    def get_vulnerability_score(
        self,
        entity_id: str,
        context: Optional[InferenceContext] = None,
    ) -> Dict[str, Any]:
        """
        Get vulnerability exposure score.

        Checks NVD for known CVEs associated with the entity's
        products/technologies.

        Score interpretation:
        - 95: No known critical/high vulnerabilities
        - 70: Some medium vulnerabilities
        - 40: High vulnerabilities present
        - 15: Critical vulnerabilities present
        """
        start_time = time.time()

        try:
            extractor = self._get_extractor('nvd_cve')
            if not extractor:
                return {'score': 50, 'confidence': 0.0, 'error': 'Extractor not available'}

            result = extractor.extract(entity_id)
            if not result.success:
                return {'score': 50, 'confidence': 0.0, 'error': result.error}

            data = result.data
            cves = data.get('vulnerabilities', [])

            if not cves:
                return {
                    'score': 95,
                    'confidence': 0.8,
                    'cve_count': 0,
                    'critical_count': 0,
                    'high_count': 0,
                    'execution_time_ms': (time.time() - start_time) * 1000,
                }

            # Count by severity
            critical = 0
            high = 0
            medium = 0

            for cve in cves:
                severity = cve.get('severity', '').upper()
                if severity == 'CRITICAL':
                    critical += 1
                elif severity == 'HIGH':
                    high += 1
                elif severity == 'MEDIUM':
                    medium += 1

            # Calculate score
            if critical > 0:
                score = max(5, 30 - (critical * 5))
            elif high > 0:
                score = max(20, 60 - (high * 5))
            elif medium > 0:
                score = max(50, 80 - (medium * 3))
            else:
                score = 85

            return {
                'score': score,
                'confidence': 0.85,
                'cve_count': len(cves),
                'critical_count': critical,
                'high_count': high,
                'medium_count': medium,
                'execution_time_ms': (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Vulnerability check failed: {e}")
            return {'score': 50, 'confidence': 0.0, 'error': str(e)}


# Convenience factory function
def get_bridge(signal_type: str) -> Optional[RoutingBridge]:
    """
    Get the appropriate bridge for a signal type.

    Args:
        signal_type: 'sanctions', 'corporate', 'regulatory', 'dns', 'network', 'security'

    Returns:
        Appropriate bridge instance or None if not available
    """
    bridges = {
        'sanctions': SanctionsSignalBridge,
        'corporate': CorporateSignalBridge,
        'regulatory': RegulatorySignalBridge,
        'dns': DNSSignalBridge,
        'network': NetworkSignalBridge,
        'security': SecuritySignalBridge,
    }
    bridge_class = bridges.get(signal_type)
    return bridge_class() if bridge_class else None
