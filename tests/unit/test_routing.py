"""
Tests for the DSI Routing Module.

Tests jurisdiction-aware routing, multi-source aggregation, caching,
and routed inference functions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from signal_architecture.signals.routing import (
    JurisdictionRouter,
    RoutingStrategy,
    ExtractorTier,
    EXTRACTOR_TIERS,
    RiskLevel,
    SanctionsMatch,
    SanctionsResult,
    SanctionsMatchType,
    SanctionsProgram,
    CorporateRecord,
    CorporateResult,
    RoutingCache,
    get_routing_cache,
    set_routing_cache,
    MultiSourceResult,
    ExtractorCallResult,
)
from signal_architecture.signals.types import InferenceContext, SignalResult


class TestJurisdictionRouter:
    """Tests for JurisdictionRouter."""

    def test_detect_locale_from_domain_uk(self):
        """UK domain should resolve to UK locale."""
        router = JurisdictionRouter()
        assert router.detect_locale_from_domain('example.co.uk') == 'UK'
        assert router.detect_locale_from_domain('company.uk') == 'UK'

    def test_detect_locale_from_domain_us(self):
        """US domain should resolve to US locale."""
        router = JurisdictionRouter()
        assert router.detect_locale_from_domain('example.com') == 'US'
        assert router.detect_locale_from_domain('company.us') == 'US'

    def test_detect_locale_from_domain_eu(self):
        """EU domains should resolve correctly."""
        router = JurisdictionRouter()
        assert router.detect_locale_from_domain('example.de') == 'DE'
        assert router.detect_locale_from_domain('company.fr') == 'FR'
        assert router.detect_locale_from_domain('business.nl') == 'NL'

    def test_detect_locale_from_domain_australia(self):
        """Australian domain should resolve to AU locale."""
        router = JurisdictionRouter()
        assert router.detect_locale_from_domain('example.com.au') == 'AU'
        assert router.detect_locale_from_domain('company.au') == 'AU'

    def test_get_extractors_sanctions_global_only(self):
        """GLOBAL_ONLY strategy should return only global extractors."""
        router = JurisdictionRouter()
        extractors = router.get_extractors(
            signal_type='sanctions',
            locale='UK',
            strategy=RoutingStrategy.GLOBAL_ONLY,
        )
        # Should include global sources but not UK-specific
        assert 'opensanctions' in extractors
        assert 'interpol_red_notices' in extractors
        assert 'uk_ofsi' not in extractors

    def test_get_extractors_sanctions_locale_plus_global(self):
        """LOCALE_PLUS_GLOBAL should return both locale and global extractors."""
        router = JurisdictionRouter()
        extractors = router.get_extractors(
            signal_type='sanctions',
            locale='UK',
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
        )
        # Should include both global and UK-specific
        assert 'opensanctions' in extractors
        assert 'uk_ofsi' in extractors

    def test_get_extractors_corporate_uk(self):
        """UK corporate lookup should include Companies House."""
        router = JurisdictionRouter()
        extractors = router.get_extractors(
            signal_type='corporate',
            locale='UK',
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
        )
        assert 'companies_house' in extractors
        assert 'opencorporates' in extractors

    def test_get_extractors_with_tier_filter(self):
        """Should filter extractors by tier."""
        router = JurisdictionRouter()
        # Get only free tier extractors
        extractors = router.get_extractors(
            signal_type='sanctions',
            locale='US',
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
            max_tier=ExtractorTier.FREE,
        )
        # All returned extractors should be FREE tier
        for ext in extractors:
            if ext in EXTRACTOR_TIERS:
                assert EXTRACTOR_TIERS[ext] == ExtractorTier.FREE

    def test_get_extractors_from_domain(self):
        """Should detect locale from domain."""
        router = JurisdictionRouter()
        extractors = router.get_extractors(
            signal_type='corporate',
            domain='example.co.uk',
            strategy=RoutingStrategy.LOCALE_PLUS_GLOBAL,
        )
        assert 'companies_house' in extractors


class TestRoutingCache:
    """Tests for RoutingCache."""

    def test_cache_set_and_get(self):
        """Should store and retrieve values."""
        cache = RoutingCache(default_ttl_seconds=60)
        cache.set('opensanctions', 'Acme Corp', {'matches': []})

        result = cache.get('opensanctions', 'Acme Corp')
        assert result is not None
        assert result.data == {'matches': []}

    def test_cache_miss(self):
        """Should return None for cache miss."""
        cache = RoutingCache()
        result = cache.get('opensanctions', 'Unknown Entity')
        assert result is None

    def test_cache_expiration(self):
        """Should expire entries after TTL."""
        cache = RoutingCache(default_ttl_seconds=1)
        cache.set('opensanctions', 'Acme Corp', {'matches': []})

        # Manually expire the entry
        key = cache._make_key('opensanctions', 'Acme Corp')
        cache._cache[key].expires_at = datetime.utcnow() - timedelta(seconds=1)

        result = cache.get('opensanctions', 'Acme Corp')
        assert result is None

    def test_cache_stats(self):
        """Should track cache statistics."""
        cache = RoutingCache()
        cache.set('ext1', 'entity1', {'data': 1})
        cache.get('ext1', 'entity1')  # Hit
        cache.get('ext1', 'entity2')  # Miss

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['stores'] == 1

    def test_cache_invalidate_specific(self):
        """Should invalidate specific entries."""
        cache = RoutingCache()
        cache.set('ext1', 'entity1', {'data': 1})
        cache.set('ext1', 'entity2', {'data': 2})

        count = cache.invalidate('ext1', 'entity1')
        assert count == 1

        assert cache.get('ext1', 'entity1') is None
        assert cache.get('ext1', 'entity2') is not None

    def test_cache_invalidate_all(self):
        """Should invalidate all entries."""
        cache = RoutingCache()
        cache.set('ext1', 'entity1', {'data': 1})
        cache.set('ext2', 'entity2', {'data': 2})

        count = cache.invalidate()
        assert count == 2

        assert cache.get('ext1', 'entity1') is None
        assert cache.get('ext2', 'entity2') is None

    def test_global_cache_singleton(self):
        """Should provide global cache singleton."""
        cache1 = get_routing_cache()
        cache2 = get_routing_cache()
        assert cache1 is cache2

    def test_set_custom_cache(self):
        """Should allow setting custom cache."""
        custom_cache = RoutingCache(default_ttl_seconds=120)
        set_routing_cache(custom_cache)
        assert get_routing_cache() is custom_cache


class TestSanctionsResult:
    """Tests for SanctionsResult schema."""

    def test_sanctions_result_creation(self):
        """Should create valid sanctions result."""
        result = SanctionsResult(
            entity_searched='Test Corp',
            sources_checked=['opensanctions', 'ofac_sdn'],
            sources_with_matches=['opensanctions'],
            total_matches=1,
            risk_level=RiskLevel.MEDIUM,
            matches=[
                SanctionsMatch(
                    matched_name='Test Corporation',
                    source='opensanctions',
                    match_score=75.0,
                    match_type=SanctionsMatchType.FUZZY,
                    program=SanctionsProgram.EU,
                )
            ],
        )
        assert result.entity_searched == 'Test Corp'
        assert result.total_matches == 1
        assert result.risk_level == RiskLevel.MEDIUM
        assert result.confirmed_sanctioned is False

    def test_sanctions_result_confirmed_sanctioned(self):
        """High match score should indicate confirmed sanction."""
        result = SanctionsResult(
            entity_searched='Bad Actor',
            sources_checked=['opensanctions'],
            sources_with_matches=['opensanctions'],
            total_matches=1,
            risk_level=RiskLevel.CRITICAL,
            confirmed_sanctioned=True,
            highest_match_score=98.0,
            matches=[],
        )
        assert result.confirmed_sanctioned is True
        assert result.highest_match_score == 98.0


class TestCorporateResult:
    """Tests for CorporateResult schema."""

    def test_corporate_result_active_company(self):
        """Should correctly identify active company."""
        result = CorporateResult(
            entity_searched='Active Ltd',
            sources_checked=['companies_house', 'opencorporates'],
            sources_with_results=['companies_house'],
            records_found=1,
            any_active=True,
            any_dissolved=False,
            primary_record=CorporateRecord(
                name='Active Ltd',
                jurisdiction='UK',
                status='Active',
                is_active=True,
                source='companies_house',
            ),
        )
        assert result.any_active is True
        assert result.primary_record.is_active is True

    def test_corporate_result_with_lei(self):
        """Should include LEI information."""
        result = CorporateResult(
            entity_searched='Big Bank',
            sources_checked=['gleif_lei'],
            sources_with_results=['gleif_lei'],
            records_found=1,
            any_active=True,
            lei='549300EXAMPLE01234567',
            lei_status='ACTIVE',
        )
        assert result.lei is not None
        assert result.lei_status == 'ACTIVE'


class TestExtractorCallResult:
    """Tests for ExtractorCallResult."""

    def test_successful_result(self):
        """Should represent successful extraction."""
        result = ExtractorCallResult(
            extractor_name='opensanctions',
            success=True,
            data={'matches': []},
            execution_time_ms=150.0,
        )
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        """Should represent failed extraction."""
        result = ExtractorCallResult(
            extractor_name='opensanctions',
            success=False,
            error='Connection timeout',
            execution_time_ms=30000.0,
        )
        assert result.success is False
        assert 'timeout' in result.error.lower()

    def test_cached_result(self):
        """Should indicate cached result."""
        result = ExtractorCallResult(
            extractor_name='opensanctions',
            success=True,
            data={'matches': []},
            from_cache=True,
            execution_time_ms=1.0,
        )
        assert result.from_cache is True


class TestInferenceContextLocale:
    """Tests for InferenceContext locale fields."""

    def test_context_with_locale(self):
        """Should store locale information."""
        context = InferenceContext(
            configuration={},
            coverage='general',
            config_name='test',
            entity_locale='UK',
            entity_country='United Kingdom',
            locale_source='submission',
        )
        assert context.entity_locale == 'UK'
        assert context.entity_country == 'United Kingdom'
        assert context.locale_source == 'submission'

    def test_context_locale_from_discovery(self):
        """Should support locale from discovery."""
        context = InferenceContext(
            configuration={},
            coverage='general',
            config_name='test',
            discovered_domain='example.co.uk',
            entity_locale='UK',
            locale_source='discovery',
        )
        assert context.locale_source == 'discovery'


class TestRoutedInferenceFunctions:
    """Tests for routed inference functions."""

    def test_sanctions_check_routed_import(self):
        """Should import sanctions_check_routed."""
        from signals.inference.functions.routed import (
            sanctions_check_routed,
        )
        assert callable(sanctions_check_routed)

    def test_corporate_registry_routed_import(self):
        """Should import corporate_registry_routed."""
        from signals.inference.functions.routed import (
            corporate_registry_routed,
        )
        assert callable(corporate_registry_routed)

    def test_email_auth_routed_import(self):
        """Should import email_auth_routed."""
        from signals.inference.functions.routed import (
            email_auth_routed,
        )
        assert callable(email_auth_routed)

    def test_security_headers_routed_import(self):
        """Should import security_headers_routed."""
        from signals.inference.functions.routed import (
            security_headers_routed,
        )
        assert callable(security_headers_routed)

    def test_vulnerability_routed_import(self):
        """Should import vulnerability_routed."""
        from signals.inference.functions.routed import (
            vulnerability_routed,
        )
        assert callable(vulnerability_routed)

    def test_register_all(self):
        """Should register all routed functions."""
        from signals.inference.functions.routed import register_all
        from signals.inference.functions.registry import (
            get_inference_function,
        )

        register_all()

        # Check some functions are registered
        assert get_inference_function('sanctions_check_routed') is not None
        assert get_inference_function('corporate_registry_routed') is not None
        assert get_inference_function('email_auth_routed') is not None


class TestRoutingBridges:
    """Tests for routing bridge aggregators."""

    def test_sanctions_bridge_import(self):
        """Should import SanctionsSignalBridge."""
        from signals.aggregators.routing_bridges import (
            SanctionsSignalBridge,
        )
        bridge = SanctionsSignalBridge()
        assert bridge is not None

    def test_corporate_bridge_import(self):
        """Should import CorporateSignalBridge."""
        from signals.aggregators.routing_bridges import (
            CorporateSignalBridge,
        )
        bridge = CorporateSignalBridge()
        assert bridge is not None

    def test_dns_bridge_import(self):
        """Should import DNSSignalBridge."""
        from signals.aggregators.routing_bridges import (
            DNSSignalBridge,
        )
        bridge = DNSSignalBridge()
        assert bridge is not None

    def test_network_bridge_import(self):
        """Should import NetworkSignalBridge."""
        from signals.aggregators.routing_bridges import (
            NetworkSignalBridge,
        )
        bridge = NetworkSignalBridge()
        assert bridge is not None

    def test_security_bridge_import(self):
        """Should import SecuritySignalBridge."""
        from signals.aggregators.routing_bridges import (
            SecuritySignalBridge,
        )
        bridge = SecuritySignalBridge()
        assert bridge is not None

    def test_get_bridge_factory(self):
        """Should get bridge by signal type."""
        from signals.aggregators.routing_bridges import get_bridge

        assert get_bridge('sanctions') is not None
        assert get_bridge('corporate') is not None
        assert get_bridge('dns') is not None
        assert get_bridge('network') is not None
        assert get_bridge('security') is not None
        assert get_bridge('unknown') is None


class TestExtractorTiers:
    """Tests for extractor tier system."""

    def test_tier_enum_values(self):
        """Should have all tier levels."""
        assert ExtractorTier.FREE.value == 'free'
        assert ExtractorTier.PAID_BASIC.value == 'paid_basic'
        assert ExtractorTier.PAID_PREMIUM.value == 'paid_premium'
        assert ExtractorTier.ENTERPRISE.value == 'enterprise'

    def test_extractors_have_tiers(self):
        """All production extractors should have tier assignments."""
        from signals.routing.router import EXTRACTOR_TIERS

        # Check some key extractors
        assert 'opensanctions' in EXTRACTOR_TIERS
        assert 'ofac_sdn' in EXTRACTOR_TIERS
        assert 'companies_house' in EXTRACTOR_TIERS
        assert 'opencorporates' in EXTRACTOR_TIERS

    def test_free_tier_extractors(self):
        """Free tier extractors should be marked FREE."""
        from signals.routing.router import EXTRACTOR_TIERS

        free_extractors = [
            'opensanctions',
            'ofac_sdn',
            'companies_house',
            'fbi_wanted',
        ]
        for ext in free_extractors:
            if ext in EXTRACTOR_TIERS:
                assert EXTRACTOR_TIERS[ext] == ExtractorTier.FREE
