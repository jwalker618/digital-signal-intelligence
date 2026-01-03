"""
Routing Bridge Aggregators

Bridge classes that connect the multi-source routing module to the existing
signal framework by converting unified schemas to signal scores.

These bridges allow inference functions to use the full power of multi-source
routing while returning standard SignalResult objects.

Usage:
    from technical_pricing.signals.aggregators.routing_bridges import (
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


# Convenience factory function
def get_bridge(signal_type: str) -> Optional[RoutingBridge]:
    """
    Get the appropriate bridge for a signal type.

    Args:
        signal_type: 'sanctions', 'corporate', 'regulatory', etc.

    Returns:
        Appropriate bridge instance or None if not available
    """
    bridges = {
        'sanctions': SanctionsSignalBridge,
        'corporate': CorporateSignalBridge,
        'regulatory': RegulatorySignalBridge,
    }
    bridge_class = bridges.get(signal_type)
    return bridge_class() if bridge_class else None
