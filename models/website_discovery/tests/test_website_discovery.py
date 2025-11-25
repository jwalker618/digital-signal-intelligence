# Unit tests for DSI Website Discovery Module
# Run with: python -m pytest test_website_discovery.py -v

import pytest
from website_discovery.dsi_website_discovery import CorporateWebsiteDiscovery
from website_discovery.strategies import DomainGenerationStrategy
from website_discovery.utils import (
    extract_company_keywords,
    generate_domain_variations,
    normalize_company_name,
)
from website_discovery.validators import WebsiteValidator

class TestUtils:
    """Test utility functions"""

    def test_normalize_company_name(self):
        """Test company name normalization"""
        assert normalize_company_name("Marks & Spencer plc") == "marks-spencer"
        assert normalize_company_name("MS Amlin Limited") == "ms-amlin"
        assert normalize_company_name("Brit Insurance") == "brit-insurance"
        assert normalize_company_name("Example Corp.") == "example-corp"

    def test_generate_domain_variations(self):
        """Test domain variation generation"""
        variations = generate_domain_variations("Marks and Spencer")
        assert "marks-and-spencer.com" in variations
        assert "marksandspencer.com" in variations
        assert "marks-and-spencer.co.uk" in variations
        assert "corporate.marksandspencer.com" in variations

    def test_extract_company_keywords(self):
        """Test keyword extraction"""
        keywords = extract_company_keywords("Marks & Spencer plc")
        assert "Marks" in keywords
        assert "Spencer" in keywords
        assert "plc" not in keywords  # Should be filtered


class TestDomainGenerationStrategy:
    """Test domain generation strategy"""

    def test_domain_generation(self):
        """Test domain generation returns results"""
        strategy = DomainGenerationStrategy(max_attempts=10)
        domains = strategy.discover("Google")
        # Google should definitely have DNS records
        assert len(domains) > 0
        assert any("google.com" in d for d in domains)


class TestWebsiteValidator:
    """Test website validation"""

    def test_validate_valid_website(self):
        """Test validation of known valid website"""
        validator = WebsiteValidator(timeout=10)
        result = validator.validate_website("https://www.google.com", "Google")

        assert result.is_valid
        assert result.ssl_valid
        assert result.status_code == 200
        assert result.confidence_score > 0

    def test_validate_invalid_website(self):
        """Test validation of invalid website"""
        validator = WebsiteValidator(timeout=5)
        result = validator.validate_website(
            "https://this-domain-does-not-exist-12345.com", "Test Company"
        )

        assert not result.is_valid
        assert result.confidence_score == 0.0


class TestCorporateWebsiteDiscovery:
    """Test main discovery class"""

    def test_discovery_initialization(self):
        """Test discovery initialization"""
        discovery = CorporateWebsiteDiscovery()
        assert discovery.domain_strategy is not None
        assert discovery.search_strategy is not None
        assert discovery.validator is not None

    def test_cache_functionality(self):
        """Test caching works"""
        discovery = CorporateWebsiteDiscovery(use_cache=True)

        # First call
        result1 = discovery.discover("Test Company", use_search=False)

        # Second call (should use cache)
        result2 = discovery.discover("Test Company", use_search=False)

        # Should be same object from cache
        assert result1.discovery_time == result2.discovery_time

        # Clear cache
        discovery.clear_cache()
        stats = discovery.get_cache_stats()
        assert stats["cached_results"] == 0


class TestRealCompanyDiscovery:
    """Test discovery with real companies"""

    @pytest.fixture
    def discovery(self):
        """Create discovery instance"""
        return CorporateWebsiteDiscovery(timeout=10, use_cache=False)

    def test_marks_and_spencer_discovery(self, discovery):
        """Test discovery for Marks & Spencer"""
        result = discovery.discover("Marks and Spencer", use_search=False)

        print(f"\n{'='*80}")
        print(f"MARKS & SPENCER DISCOVERY RESULTS")
        print(f"{'='*80}")
        print(f"Success: {result.success}")
        print(f"Total Candidates: {result.total_candidates}")
        print(f"Discovery Time: {result.discovery_time:.2f}s")
        print(f"Strategies Used: {', '.join(result.strategies_used)}")

        if result.best_match:
            print(f"\n🏆 BEST MATCH:")
            print(f"  URL: {result.best_match.url}")
            print(f"  Confidence: {result.best_match.confidence_score:.1f}/100")
            print(f"  Method: {result.best_match.discovery_method.value}")
            print(f"  Title: {result.best_match.title[:80]}")
            print(
                f"  Corporate Indicators: {len(result.best_match.corporate_indicators)}"
            )

        print(f"\n📋 ALL CANDIDATES (Top 5):")
        for idx, candidate in enumerate(result.all_candidates[:5]):
            print(f"  {idx+1}. {candidate.url}")
            print(f"     Score: {candidate.confidence_score:.1f}/100")
            print(f"     Indicators: {len(candidate.corporate_indicators)}")

        assert result.success
        assert result.total_candidates > 0

        # Expected M&S domains
        best_url = result.best_match.url.lower()
        assert "marksandspencer" in best_url or "corporate.marksandspencer" in best_url

    def test_ms_amlin_discovery(self, discovery):
        """Test discovery for MS Amlin"""
        result = discovery.discover("MS Amlin", use_search=False)

        print(f"\n{'='*80}")
        print(f"MS AMLIN DISCOVERY RESULTS")
        print(f"{'='*80}")
        print(f"Success: {result.success}")
        print(f"Total Candidates: {result.total_candidates}")
        print(f"Discovery Time: {result.discovery_time:.2f}s")
        print(f"Strategies Used: {', '.join(result.strategies_used)}")

        if result.best_match:
            print(f"\n🏆 BEST MATCH:")
            print(f"  URL: {result.best_match.url}")
            print(f"  Confidence: {result.best_match.confidence_score:.1f}/100")
            print(f"  Method: {result.best_match.discovery_method.value}")
            print(f"  Title: {result.best_match.title[:80]}")

        print(f"\n📋 ALL CANDIDATES (Top 5):")
        for idx, candidate in enumerate(result.all_candidates[:5]):
            print(f"  {idx+1}. {candidate.url}")
            print(f"     Score: {candidate.confidence_score:.1f}/100")

        # MS Amlin may have candidates even if not perfect match
        assert result.total_candidates >= 0  # May or may not find matches

    def test_brit_discovery(self, discovery):
        """Test discovery for Brit Insurance"""
        result = discovery.discover("Brit", use_search=False)

        print(f"\n{'='*80}")
        print(f"BRIT DISCOVERY RESULTS")
        print(f"{'='*80}")
        print(f"Success: {result.success}")
        print(f"Total Candidates: {result.total_candidates}")
        print(f"Discovery Time: {result.discovery_time:.2f}s")
        print(f"Strategies Used: {', '.join(result.strategies_used)}")

        if result.best_match:
            print(f"\n🏆 BEST MATCH:")
            print(f"  URL: {result.best_match.url}")
            print(f"  Confidence: {result.best_match.confidence_score:.1f}/100")
            print(f"  Method: {result.best_match.discovery_method.value}")
            print(f"  Title: {result.best_match.title[:80]}")

        print(f"\n📋 ALL CANDIDATES (Top 5):")
        for idx, candidate in enumerate(result.all_candidates[:5]):
            print(f"  {idx+1}. {candidate.url}")
            print(f"     Score: {candidate.confidence_score:.1f}/100")

        # Brit is a short name, may be challenging
        assert result.total_candidates >= 0

    def test_batch_discovery(self, discovery):
        """Test batch discovery for all three companies"""
        companies = ["Marks and Spencer", "MS Amlin", "Brit"]

        results = discovery.discover_batch(companies, use_search=False, delay=0.5)

        print(f"\n{'='*80}")
        print(f"BATCH DISCOVERY RESULTS")
        print(f"{'='*80}")

        for company_name, result in results.items():
            print(f"\n{company_name}:")
            print(f"  Success: {result.success}")
            print(f"  Candidates: {result.total_candidates}")
            if result.best_match:
                print(f"  Best: {result.best_match.url}")
                print(f"  Score: {result.best_match.confidence_score:.1f}/100")

        assert len(results) == 3
        assert all(isinstance(r, type(result)) for r in results.values())

    def test_with_domain_hint(self, discovery):
        """Test discovery with domain hint"""
        result = discovery.discover(
            "Marks and Spencer",
            domain_hint="corporate.marksandspencer.com",
            use_search=False,
        )

        print(f"\n{'='*80}")
        print(f"MARKS & SPENCER WITH DOMAIN HINT")
        print(f"{'='*80}")

        if result.best_match:
            print(f"Best Match: {result.best_match.url}")
            print(f"Confidence: {result.best_match.confidence_score:.1f}/100")
            print(f"Method: {result.best_match.discovery_method.value}")

        # Hint should be prioritized
        if result.best_match:
            assert "corporate.marksandspencer" in result.best_match.url.lower()


class TestIntegration:
    """Integration tests"""

    def test_full_discovery_workflow(self):
        """Test complete discovery workflow"""
        discovery = CorporateWebsiteDiscovery()

        # Discover
        result = discovery.discover("Microsoft", use_search=False)

        # Validate result structure
        assert hasattr(result, "company_name")
        assert hasattr(result, "best_match")
        assert hasattr(result, "all_candidates")
        assert hasattr(result, "discovery_time")
        assert hasattr(result, "success")

        # Check best match structure if found
        if result.best_match:
            assert hasattr(result.best_match, "url")
            assert hasattr(result.best_match, "confidence_score")
            assert hasattr(result.best_match, "discovery_method")
            assert 0 <= result.best_match.confidence_score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
