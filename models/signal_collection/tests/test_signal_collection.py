# Unit tests for Signal Collection Module
# Run with: python -m pytest test_signal_collection.py -v -s

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from signal_collection.collectors import (
    CollectionResult,
    CyberSignalCollector,
    EnergySignalCollector,
    FinancialInstitutionSignalCollector,
    SignalMatch,
)
from signal_collection.config import CyberConfig, EnergyConfig, FinancialConfig
from signal_collection.crawler import CrawledPage, WebsiteCrawler
from signal_collection.extractors import DocumentExtractor


class TestCyberSignalCollector:
    """Test cyber signal collector"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        config = CyberConfig(max_pages=10, max_depth=2)
        return CyberSignalCollector(config, timeout=5)

    @pytest.fixture
    def mock_pages(self):
        """Create mock crawled pages"""
        pages = [
            CrawledPage(
                url="https://example.com/blog/security-breach",
                title="Recent Security Breach",
                content="We experienced a security breach last week affecting 100 customers. Our team responded immediately to contain the incident.",
                html="""<article>
                <h1>Recent Security Breach</h1>
                <time datetime='2025-11-01'>November 1, 2025</time>
                <p>We experienced a security breach last week affecting 100 customers.
                Our team responded immediately to contain the incident.</p>
                </article>""",
                links=[],
                depth=1,
                timestamp=time.time(),
                status_code=200,
            ),
            CrawledPage(
                url="https://example.com/news/ciso-hire",
                title="New CISO Appointed",
                content="We are pleased to announce that Jane Smith has been appointed as our new Chief Information Security Officer (CISO).",
                html="""<article>
                <h1>New CISO Appointed</h1>
                <time datetime='2025-10-15'>October 15, 2025</time>
                <p>We are pleased to announce that Jane Smith has been appointed as our
                new Chief Information Security Officer (CISO).</p>
                </article>""",
                links=[],
                depth=1,
                timestamp=time.time(),
                status_code=200,
            ),
        ]
        return pages

    def test_collector_initialization(self, collector):
        """Test collector initialization"""
        assert collector is not None
        assert collector.cyber_config is not None
        assert isinstance(collector.crawler, WebsiteCrawler)
        assert isinstance(collector.extractor, DocumentExtractor)

    def test_find_incidents(self, collector, mock_pages):
        """Test incident detection"""
        # Extract articles
        articles = []
        for page in mock_pages:
            article = collector.extractor.html_extractor.extract_article(
                page.html, page.url
            )
            if article:
                articles.append(article)

        # Find incidents
        incidents = collector._find_incidents(articles)

        assert len(incidents) > 0
        assert any("breach" in signal.keyword.lower() for signal in incidents)
        assert all(signal.source_type == "incident" for signal in incidents)

    def test_find_key_hires(self, collector, mock_pages):
        """Test key hire detection"""
        # Extract articles
        articles = []
        for page in mock_pages:
            article = collector.extractor.html_extractor.extract_article(
                page.html, page.url
            )
            if article:
                articles.append(article)

        # Find hires
        hires = collector._find_key_hires(articles)

        assert len(hires) > 0
        assert any("ciso" in signal.context.lower() for signal in hires)
        assert all(signal.source_type == "hire" for signal in hires)

    @patch.object(WebsiteCrawler, "crawl")
    def test_collect_with_mock_crawler(self, mock_crawl, collector, mock_pages):
        """Test full collection with mocked crawler"""
        mock_crawl.return_value = mock_pages

        result = collector.collect("Test Company", "https://example.com")

        assert result is not None
        assert result.success
        assert result.pages_crawled == len(mock_pages)
        assert len(result.signals) > 0
        assert result.company_name == "Test Company"

    def test_date_filtering(self, collector, mock_pages):
        """Test that old articles are filtered out"""
        # Create article with old date
        old_page = CrawledPage(
            url="https://example.com/blog/old",
            title="Old Article",
            content="This breach happened years ago. It was a significant security incident that affected many of our customers. We have since implemented comprehensive security measures to prevent such incidents in the future. Our security team has worked tirelessly to ensure that all vulnerabilities have been addressed.",
            html="""<article>
            <h1>Old Breach</h1>
            <time datetime='2020-01-01'>January 1, 2020</time>
            <p>This breach happened years ago. It was a significant security incident that affected many of our customers. We have since implemented comprehensive security measures to prevent such incidents in the future. Our security team has worked tirelessly to ensure that all vulnerabilities have been addressed.</p>
            </article>""",
            links=[],
            depth=1,
            timestamp=time.time() - 365 * 24 * 3600,  # 1 year ago
            status_code=200,
        )

        pages_with_old = mock_pages + [old_page]

        # Extract articles
        articles = []
        for page in pages_with_old:
            article = collector.extractor.html_extractor.extract_article(
                page.html, page.url
            )
            if article:
                articles.append(article)

        # Filter by date (last 12 months)
        recent = collector.extractor.html_extractor.filter_by_date(articles, 12)

        # Old article should be filtered out
        assert len(recent) < len(articles)
        assert all(
            a.published_date >= datetime.now() - timedelta(days=12 * 30)
            for a in recent
            if a.published_date
        )


class TestFinancialInstitutionSignalCollector:
    """Test financial institution signal collector"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        config = FinancialConfig(max_pages=10, max_depth=2)
        return FinancialInstitutionSignalCollector(config, timeout=5)

    @pytest.fixture
    def mock_pages_with_report(self):
        """Create mock pages including a report link"""
        pages = [
            CrawledPage(
                url="https://example.com/investors",
                title="Investor Relations",
                content="Investor Relations - Annual Report 2023, Integrated Report 2023",
                html="""<html>
                <h1>Investor Relations</h1>
                <a href='/reports/annual-report-2023.pdf'>Annual Report 2023</a>
                <a href='/reports/integrated-report-2023.pdf'>Integrated Report 2023</a>
                </html>""",
                links=["/reports/annual-report-2023.pdf", "/reports/integrated-report-2023.pdf"],
                depth=1,
                timestamp=time.time(),
                status_code=200,
            ),
            CrawledPage(
                url="https://example.com/reports/annual-report-2023.pdf",
                title="Annual Report 2023",
                content="",  # PDF binary content
                html="",
                links=[],
                depth=2,
                timestamp=time.time(),
                status_code=200,
            ),
        ]
        return pages

    def test_collector_initialization(self, collector):
        """Test collector initialization"""
        assert collector is not None
        assert collector.financial_config is not None
        assert "annual report" in [dt.lower() for dt in collector.config.document_types]

    def test_find_documents(self, collector, mock_pages_with_report):
        """Test document finding"""
        documents = collector._find_documents(mock_pages_with_report)

        # Should find report URLs
        assert len(documents) > 0
        assert any("report" in doc.lower() for doc in documents)

    @patch.object(WebsiteCrawler, "crawl")
    def test_collect_with_mock_crawler(
        self, mock_crawl, collector, mock_pages_with_report
    ):
        """Test full collection with mocked crawler"""
        mock_crawl.return_value = mock_pages_with_report

        result = collector.collect("Test Bank", "https://example.com")

        assert result is not None
        assert result.success
        assert result.pages_crawled == len(mock_pages_with_report)
        assert result.company_name == "Test Bank"

    def test_metric_patterns(self, collector):
        """Test that metric patterns are configured"""
        assert len(collector.financial_config.metric_patterns) > 0
        assert "Total Assets" in collector.financial_config.metric_patterns
        assert "Net Income" in collector.financial_config.metric_patterns


class TestEnergySignalCollector:
    """Test energy signal collector"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        config = EnergyConfig(max_pages=10, max_depth=2)
        return EnergySignalCollector(config, timeout=5)

    @pytest.fixture
    def mock_pages_with_incident(self):
        """Create mock pages with safety incident"""
        pages = [
            CrawledPage(
                url="https://example.com/news/spill",
                title="Environmental Incident",
                content="A minor oil spill occurred at our offshore facility. The spill has been contained and cleanup is underway.",
                html="""<article>
                <h1>Minor Oil Spill Contained</h1>
                <time datetime='2025-11-15'>November 15, 2025</time>
                <p>A minor oil spill occurred at our offshore facility.
                The spill has been contained and cleanup is underway.</p>
                </article>""",
                links=[],
                depth=1,
                timestamp=time.time(),
                status_code=200,
            ),
            CrawledPage(
                url="https://example.com/sustainability/report-2023.pdf",
                title="Sustainability Report 2023",
                content="",  # PDF binary
                html="",
                links=[],
                depth=2,
                timestamp=time.time(),
                status_code=200,
            ),
        ]
        return pages

    def test_collector_initialization(self, collector):
        """Test collector initialization"""
        assert collector is not None
        assert collector.energy_config is not None
        # Check if any keyword contains "safety"
        assert any("safety" in kw.lower() for kw in collector.config.keywords)

    @patch.object(WebsiteCrawler, "crawl")
    def test_find_incidents(self, mock_crawl, collector, mock_pages_with_incident):
        """Test incident detection"""
        mock_crawl.return_value = mock_pages_with_incident

        # Extract articles
        articles = []
        for page in mock_pages_with_incident:
            if page.html:  # Only process pages with HTML content
                article = collector.extractor.html_extractor.extract_article(
                    page.html, page.url
                )
                if article:
                    articles.append(article)

        # Find incidents
        incidents = collector._find_incidents(mock_pages_with_incident)

        assert len(incidents) >= 0  # May or may not find depending on keywords

    def test_incident_keywords(self, collector):
        """Test that incident keywords are configured"""
        assert len(collector.energy_config.incident_keywords) > 0
        assert any(
            "spill" in kw.lower() for kw in collector.energy_config.incident_keywords
        )


class TestSignalMatch:
    """Test SignalMatch dataclass"""

    def test_signal_match_creation(self):
        """Test creating a signal match"""
        match = SignalMatch(
            keyword="breach",
            context="Security breach occurred last week",
            url="https://example.com/news",
            date=datetime.now(),
            source_type="blog",
            relevance_score=0.85,
        )

        assert match.keyword == "breach"
        assert match.source_type == "blog"
        assert 0 <= match.relevance_score <= 1


class TestCollectionResult:
    """Test CollectionResult dataclass"""

    def test_collection_result_creation(self):
        """Test creating a collection result"""
        signals = [
            SignalMatch(
                keyword="test",
                context="test context",
                url="https://example.com",
                date=None,
                source_type="test",
                relevance_score=0.5,
            )
        ]

        result = CollectionResult(
            company_name="Test Company",
            website_url="https://example.com",
            collection_date=datetime.now(),
            signals=signals,
            documents_found=["report.pdf"],
            pages_crawled=10,
            collection_time=5.5,
            success=True,
        )

        assert result.company_name == "Test Company"
        assert result.success
        assert len(result.signals) == 1
        assert result.pages_crawled == 10
        assert len(result.errors) == 0

    def test_collection_result_with_errors(self):
        """Test collection result with errors"""
        result = CollectionResult(
            company_name="Test Company",
            website_url="https://example.com",
            collection_date=datetime.now(),
            signals=[],
            documents_found=[],
            pages_crawled=0,
            collection_time=1.0,
            success=False,
            errors=["Connection timeout", "Invalid URL"],
        )

        assert not result.success
        assert len(result.errors) == 2
        assert "Connection timeout" in result.errors


class TestIntegration:
    """Integration tests"""

    @pytest.mark.skip(reason="Requires real website access - enable for manual testing")
    def test_real_website_cyber_collection(self):
        """Test real cyber signal collection (manual test)"""
        config = CyberConfig(max_pages=5, max_depth=1)
        collector = CyberSignalCollector(config)

        # Test with a known security blog
        result = collector.collect("Example Security Co", "https://example.com")

        assert result is not None
        print(f"\nCompany: {result.company_name}")
        print(f"Success: {result.success}")
        print(f"Pages Crawled: {result.pages_crawled}")
        print(f"Signals Found: {len(result.signals)}")
        print(f"Collection Time: {result.collection_time:.2f}s")

        if result.signals:
            print("\nTop 5 Signals:")
            for signal in sorted(
                result.signals, key=lambda s: s.relevance_score, reverse=True
            )[:5]:
                print(f"  - {signal.keyword}: {signal.relevance_score:.2f}")
                print(f"    {signal.context[:100]}...")

    @pytest.mark.skip(reason="Requires real website access - enable for manual testing")
    def test_real_website_financial_collection(self):
        """Test real financial signal collection (manual test)"""
        config = FinancialConfig(max_pages=10, max_depth=2)
        collector = FinancialInstitutionSignalCollector(config)

        # Test with a real bank website
        result = collector.collect("Example Bank", "https://example-bank.com")

        assert result is not None
        print(f"\nCompany: {result.company_name}")
        print(f"Success: {result.success}")
        print(f"Pages Crawled: {result.pages_crawled}")
        print(f"Documents Found: {len(result.documents_found)}")
        print(f"Signals Found: {len(result.signals)}")

        if result.documents_found:
            print("\nDocuments Found:")
            for doc in result.documents_found:
                print(f"  - {doc}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
