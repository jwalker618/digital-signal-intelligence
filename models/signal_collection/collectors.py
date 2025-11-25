# Model-specific signal collectors for corporate website analysis

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from .config import CollectionConfig, CyberConfig, EnergyConfig, FinancialConfig
from .crawler import CrawledPage, WebsiteCrawler
from .extractors import DocumentExtractor, HTMLArticle


@dataclass
class SignalMatch:
    """A found signal/keyword match"""

    keyword: str
    context: str
    url: str
    date: Optional[datetime]
    source_type: str  # 'blog', 'report', 'news', etc.
    relevance_score: float  # 0-1


@dataclass
class CollectionResult:
    """Results from signal collection"""

    company_name: str
    website_url: str
    collection_date: datetime
    signals: List[SignalMatch]
    documents_found: List[str]
    pages_crawled: int
    collection_time: float
    success: bool
    errors: List[str] = field(default_factory=list)


class SignalCollector:
    """
    Base class for signal collection from corporate websites
    """

    def __init__(self, config: CollectionConfig, timeout: int = 30):
        """
        Initialize signal collector.

        Args:
            config: Collection configuration
            timeout: Request timeout in seconds
        """
        self.config = config
        self.crawler = WebsiteCrawler(
            #max_pages=config.max_pages,
            max_depth=config.max_depth,
            delay=config.delay,
            timeout=timeout,
        )
        self.extractor = DocumentExtractor(timeout=timeout)

    def collect(
        self, company_name: str, website_url: str
    ) -> Optional[CollectionResult]:
        """
        Collect signals from corporate website.

        Args:
            company_name: Company name
            website_url: Corporate website URL

        Returns:
            CollectionResult or None
        """
        start_time = datetime.now()
        errors = []

        try:
            # Crawl website
            pages = self.crawler.crawl(website_url, self.config.priority_urls)

            if not pages:
                errors.append("No pages could be crawled")
                return CollectionResult(
                    company_name=company_name,
                    website_url=website_url,
                    collection_date=start_time,
                    signals=[],
                    documents_found=[],
                    pages_crawled=0,
                    collection_time=(datetime.now() - start_time).total_seconds(),
                    success=False,
                    errors=errors,
                )

            # Extract and analyze content
            signals = self._analyze_pages(pages)

            # Find specific documents
            documents = self._find_documents(pages)

            collection_time = (datetime.now() - start_time).total_seconds()

            return CollectionResult(
                company_name=company_name,
                website_url=website_url,
                collection_date=start_time,
                signals=signals,
                documents_found=documents,
                pages_crawled=len(pages),
                collection_time=collection_time,
                success=True,
                errors=errors,
            )

        except Exception as e:
            errors.append(f"Collection failed: {str(e)}")
            return CollectionResult(
                company_name=company_name,
                website_url=website_url,
                collection_date=start_time,
                signals=[],
                documents_found=[],
                pages_crawled=0,
                collection_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                errors=errors,
            )

    def _analyze_pages(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Analyze crawled pages for signals.
        To be overridden by subclasses.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        raise NotImplementedError("Subclasses must implement _analyze_pages")

    def _find_documents(self, pages: List[CrawledPage]) -> List[str]:
        """
        Find specific documents from crawled pages.

        Args:
            pages: Crawled pages

        Returns:
            List of document URLs
        """
        documents = []
        for page in pages:
            for doc_type in self.config.document_types:
                if doc_type.lower() in page.url.lower():
                    documents.append(page.url)
        return documents

    def _calculate_relevance(self, context: str, keyword: str) -> float:
        """
        Calculate relevance score for a match.

        Args:
            context: Context around match
            keyword: Matched keyword

        Returns:
            Relevance score (0-1)
        """
        context_lower = context.lower()
        keyword_lower = keyword.lower()

        # Base score
        score = 0.5

        # Boost if keyword appears multiple times
        count = context_lower.count(keyword_lower)
        score += min(count * 0.1, 0.3)

        # Boost if in title or heading (rough heuristic)
        if len(context) < 100:
            score += 0.2

        return min(score, 1.0)


class CyberSignalCollector(SignalCollector):
    """
    Collects cyber security signals from corporate websites
    """

    def __init__(self, config: Optional[CyberConfig] = None, timeout: int = 30):
        """
        Initialize cyber signal collector.

        Args:
            config: Cyber configuration (uses default if not provided)
            timeout: Request timeout in seconds
        """
        if config is None:
            config = CyberConfig()
        super().__init__(config, timeout)
        self.cyber_config = config

    def _analyze_pages(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Analyze pages for cyber security signals.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        signals = []
        cutoff_date = datetime.now() - timedelta(
            days=self.config.time_window_months * 30
        )

        # Extract articles from pages
        articles = []
        for page in pages:
            if page.content_type and "html" in page.content_type.lower():
                article = self.extractor.html_extractor.extract_article(
                    page.content, page.url
                )
                if article:
                    articles.append(article)

        # Filter by date
        recent_articles = self.extractor.html_extractor.filter_by_date(
            articles, self.config.time_window_months
        )

        # Search for incidents
        incident_matches = self._find_incidents(recent_articles)
        signals.extend(incident_matches)

        # Search for key hires
        hire_matches = self._find_key_hires(recent_articles)
        signals.extend(hire_matches)

        # General keyword search
        keyword_matches = self.extractor.html_extractor.find_keywords_in_articles(
            recent_articles, self.cyber_config.keywords
        )

        for match in keyword_matches:
            if match["published_date"] and match["published_date"] >= cutoff_date:
                signals.append(
                    SignalMatch(
                        keyword=match["keyword"],
                        context=match["context"],
                        url=match["article_url"],
                        date=match["published_date"],
                        source_type="blog/news",
                        relevance_score=self._calculate_relevance(
                            match["context"], match["keyword"]
                        ),
                    )
                )

        return signals

    def _find_incidents(self, articles: List[HTMLArticle]) -> List[SignalMatch]:
        """
        Find security incidents in articles.

        Args:
            articles: List of articles

        Returns:
            List of incident matches
        """
        matches = []
        incident_matches = self.extractor.html_extractor.find_keywords_in_articles(
            articles, self.cyber_config.incident_keywords
        )

        for match in incident_matches:
            matches.append(
                SignalMatch(
                    keyword=match["keyword"],
                    context=match["context"],
                    url=match["article_url"],
                    date=match["published_date"],
                    source_type="incident",
                    relevance_score=self._calculate_relevance(
                        match["context"], match["keyword"]
                    )
                    * 1.2,  # Boost incidents
                )
            )

        return matches

    def _find_key_hires(self, articles: List[HTMLArticle]) -> List[SignalMatch]:
        """
        Find IT/security key hires in articles.

        Args:
            articles: List of articles

        Returns:
            List of hire matches
        """
        matches = []

        # Look for hire keywords
        hire_matches = self.extractor.html_extractor.find_keywords_in_articles(
            articles, self.cyber_config.hire_keywords
        )

        # Filter for IT/security roles
        it_roles = ["ciso", "cto", "it director", "security", "chief information"]

        for match in hire_matches:
            context_lower = match["context"].lower()
            # Check if IT/security role mentioned
            if any(role in context_lower for role in it_roles):
                matches.append(
                    SignalMatch(
                        keyword=match["keyword"],
                        context=match["context"],
                        url=match["article_url"],
                        date=match["published_date"],
                        source_type="hire",
                        relevance_score=self._calculate_relevance(
                            match["context"], match["keyword"]
                        )
                        * 1.3,  # Boost key hires
                    )
                )

        return matches


class FinancialInstitutionSignalCollector(SignalCollector):
    """
    Collects signals for financial institutions
    """

    def __init__(self, config: Optional[FinancialConfig] = None, timeout: int = 30):
        """
        Initialize financial institution signal collector.

        Args:
            config: Financial configuration (uses default if not provided)
            timeout: Request timeout in seconds
        """
        if config is None:
            config = FinancialConfig()
        super().__init__(config, timeout)
        self.financial_config = config

    def _analyze_pages(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Analyze pages for financial signals.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        signals = []

        # Find and analyze reports
        report_signals = self._analyze_reports(pages)
        signals.extend(report_signals)

        # Extract articles for general keyword search
        articles = []
        for page in pages:
            if page.content_type and "html" in page.content_type.lower():
                article = self.extractor.html_extractor.extract_article(
                    page.content, page.url
                )
                if article:
                    articles.append(article)

        # General keyword search
        keyword_matches = self.extractor.html_extractor.find_keywords_in_articles(
            articles, self.financial_config.keywords
        )

        for match in keyword_matches:
            signals.append(
                SignalMatch(
                    keyword=match["keyword"],
                    context=match["context"],
                    url=match["article_url"],
                    date=match["published_date"],
                    source_type="web_content",
                    relevance_score=self._calculate_relevance(
                        match["context"], match["keyword"]
                    ),
                )
            )

        return signals

    def _analyze_reports(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Find and analyze financial reports.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        signals = []

        # Find PDF reports
        for page in pages:
            if page.url.lower().endswith(".pdf"):
                # Check if it's a report type we care about
                url_lower = page.url.lower()
                if any(
                    doc_type.lower() in url_lower
                    for doc_type in self.config.document_types
                ):
                    # Extract PDF content
                    pdf_content = self.extractor.pdf_extractor.extract(page.url)

                    if pdf_content:
                        # Extract metrics using configured patterns
                        metrics = self.extractor.pdf_extractor.extract_metrics(
                            pdf_content, self.financial_config.metric_patterns
                        )

                        # Create signal for each found metric
                        for metric_name, value in metrics.items():
                            signals.append(
                                SignalMatch(
                                    keyword=metric_name,
                                    context=f"{metric_name}: {value}",
                                    url=page.url,
                                    date=pdf_content.metadata.get("created_date"),
                                    source_type="report",
                                    relevance_score=0.9,  # High relevance for reports
                                )
                            )

        return signals


class EnergySignalCollector(SignalCollector):
    """
    Collects signals for energy companies
    """

    def __init__(self, config: Optional[EnergyConfig] = None, timeout: int = 30):
        """
        Initialize energy signal collector.

        Args:
            config: Energy configuration (uses default if not provided)
            timeout: Request timeout in seconds
        """
        if config is None:
            config = EnergyConfig()
        super().__init__(config, timeout)
        self.energy_config = config

    def _analyze_pages(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Analyze pages for energy signals.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        signals = []

        # Find and analyze reports
        report_signals = self._analyze_reports(pages)
        signals.extend(report_signals)

        # Find incidents
        incident_signals = self._find_incidents(pages)
        signals.extend(incident_signals)

        # Extract articles for general keyword search
        articles = []
        for page in pages:
            if page.content_type and "html" in page.content_type.lower():
                article = self.extractor.html_extractor.extract_article(
                    page.content, page.url
                )
                if article:
                    articles.append(article)

        # General keyword search
        keyword_matches = self.extractor.html_extractor.find_keywords_in_articles(
            articles, self.energy_config.keywords
        )

        for match in keyword_matches:
            signals.append(
                SignalMatch(
                    keyword=match["keyword"],
                    context=match["context"],
                    url=match["article_url"],
                    date=match["published_date"],
                    source_type="web_content",
                    relevance_score=self._calculate_relevance(
                        match["context"], match["keyword"]
                    ),
                )
            )

        return signals

    def _analyze_reports(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Find and analyze energy reports.

        Args:
            pages: Crawled pages

        Returns:
            List of signal matches
        """
        signals = []

        # Find PDF reports
        for page in pages:
            if page.url.lower().endswith(".pdf"):
                # Check if it's a report type we care about
                url_lower = page.url.lower()
                if any(
                    doc_type.lower() in url_lower
                    for doc_type in self.config.document_types
                ):
                    # Extract PDF content
                    pdf_content = self.extractor.pdf_extractor.extract(page.url)

                    if pdf_content:
                        # Look for safety/sustainability keywords in report
                        for keyword in self.energy_config.keywords:
                            if keyword.lower() in pdf_content.content.lower():
                                # Extract context
                                pos = pdf_content.content.lower().find(keyword.lower())
                                start = max(0, pos - 150)
                                end = min(
                                    len(pdf_content.content), pos + len(keyword) + 150
                                )
                                context = pdf_content.content[start:end].strip()

                                signals.append(
                                    SignalMatch(
                                        keyword=keyword,
                                        context=context,
                                        url=page.url,
                                        date=pdf_content.metadata.get("created_date"),
                                        source_type="report",
                                        relevance_score=0.85,
                                    )
                                )

        return signals

    def _find_incidents(self, pages: List[CrawledPage]) -> List[SignalMatch]:
        """
        Find safety/environmental incidents.

        Args:
            pages: Crawled pages

        Returns:
            List of incident matches
        """
        signals = []

        # Extract articles
        articles = []
        for page in pages:
            if page.content_type and "html" in page.content_type.lower():
                article = self.extractor.html_extractor.extract_article(
                    page.content, page.url
                )
                if article:
                    articles.append(article)

        # Filter by date
        recent_articles = self.extractor.html_extractor.filter_by_date(
            articles, self.config.time_window_months
        )

        # Search for incident keywords
        incident_matches = self.extractor.html_extractor.find_keywords_in_articles(
            recent_articles, self.energy_config.incident_keywords
        )

        for match in incident_matches:
            signals.append(
                SignalMatch(
                    keyword=match["keyword"],
                    context=match["context"],
                    url=match["article_url"],
                    date=match["published_date"],
                    source_type="incident",
                    relevance_score=self._calculate_relevance(
                        match["context"], match["keyword"]
                    )
                    * 1.25,  # Boost incidents
                )
            )

        return signals
