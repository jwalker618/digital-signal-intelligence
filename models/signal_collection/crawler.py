# Website crawler for discovering and collecting content

import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import CollectionConfig


@dataclass
class CrawledPage:
    """Represents a crawled page"""

    url: str
    title: str
    content: str
    html: str
    links: List[str]
    depth: int
    timestamp: float
    status_code: int


class WebsiteCrawler:
    """
    Intelligent website crawler for corporate content discovery
    """

    def __init__(
        self,
        config: CollectionConfig,
        timeout: int = 10,
        delay: float = 1.0,
        user_agent: str = "DSI Signal Collector Bot",
    ):
        """
        Initialize crawler.

        Args:
            config: Collection configuration
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
            user_agent: User agent string
        """
        self.config = config
        self.timeout = timeout
        self.delay = delay

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        # Tracking
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[CrawledPage] = []

    def crawl(self, base_url: str) -> List[CrawledPage]:
        """
        Crawl website starting from base URL.

        Args:
            base_url: Starting URL

        Returns:
            List of crawled pages
        """
        print(f"🕷️  Starting crawl from: {base_url}")

        # Initialize queue with priority URLs
        to_visit = deque([(base_url, 0)])  # (url, depth)

        # Add priority URLs from config
        for priority_path in self.config.priority_urls:
            priority_url = urljoin(base_url, priority_path)
            to_visit.append((priority_url, 1))

        pages_crawled = 0

        while to_visit and pages_crawled < self.config.max_pages:
            url, depth = to_visit.popleft()

            # Skip if already visited
            if url in self.visited_urls:
                continue

            # Skip if too deep
            if depth > self.config.max_depth:
                continue

            # Skip if external (unless configured)
            if not self.config.follow_external:
                if not self._is_same_domain(url, base_url):
                    continue

            # Crawl page
            page = self._crawl_page(url, depth)
            if page:
                self.visited_urls.add(url)
                self.crawled_pages.append(page)
                pages_crawled += 1

                print(
                    f"  [{pages_crawled}/{self.config.max_pages}] ✓ {url} (depth: {depth})"
                )

                # Add links to queue
                for link in page.links:
                    if link not in self.visited_urls:
                        to_visit.append((link, depth + 1))

                # Rate limiting
                time.sleep(self.delay)

        print(f"✅ Crawl complete: {len(self.crawled_pages)} pages crawled")
        return self.crawled_pages

    def _crawl_page(self, url: str, depth: int) -> Optional[CrawledPage]:
        """Crawl a single page"""
        try:
            response = self.session.get(url, timeout=self.timeout)

            # Only process successful HTML responses
            if response.status_code != 200:
                return None

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = soup.find("title")
            title_text = title.get_text().strip() if title else ""

            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text_content = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = "\n".join(chunk for chunk in chunks if chunk)

            # Extract links
            links = self._extract_links(soup, url)

            return CrawledPage(
                url=url,
                title=title_text,
                content=text_content,
                html=response.text,
                links=links,
                depth=depth,
                timestamp=time.time(),
                status_code=response.status_code,
            )

        except Exception:
            return None

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and normalize links from page"""
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Skip anchors and javascript
            if href.startswith(("#", "javascript:", "mailto:")):
                continue

            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)

            # Remove fragments
            absolute_url = absolute_url.split("#")[0]

            links.append(absolute_url)

        return links

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc

        return domain1 == domain2

    def find_documents(self, document_type: str = None) -> List[CrawledPage]:
        """
        Find pages matching document types from config.

        Args:
            document_type: Specific document type to find (optional)

        Returns:
            List of matching pages
        """
        matching_pages = []

        # Determine which document types to search for
        if document_type:
            search_types = [document_type.lower()]
        else:
            search_types = [dt.lower() for dt in self.config.document_types]

        for page in self.crawled_pages:
            # Check title and content
            text = (page.title + " " + page.content).lower()

            for doc_type in search_types:
                if doc_type in text:
                    matching_pages.append(page)
                    break

        return matching_pages

    def find_pdfs(self) -> List[str]:
        """Find all PDF links in crawled pages"""
        pdf_links = []

        for page in self.crawled_pages:
            # Find PDF links in HTML
            soup = BeautifulSoup(page.html, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.lower().endswith(".pdf"):
                    absolute_url = urljoin(page.url, href)
                    if absolute_url not in pdf_links:
                        pdf_links.append(absolute_url)

        return pdf_links

    def search_content(self, keywords: List[str]) -> List[Dict]:
        """
        Search crawled content for keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of matches with context
        """
        matches = []

        for page in self.crawled_pages:
            content_lower = page.content.lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()

                if keyword_lower in content_lower:
                    # Find context around keyword
                    contexts = self._extract_context(
                        page.content, keyword, context_chars=200
                    )

                    for context in contexts:
                        matches.append(
                            {
                                "url": page.url,
                                "title": page.title,
                                "keyword": keyword,
                                "context": context,
                                "timestamp": page.timestamp,
                            }
                        )

        return matches

    def _extract_context(
        self, text: str, keyword: str, context_chars: int = 200
    ) -> List[str]:
        """Extract text context around keyword"""
        contexts = []
        keyword_lower = keyword.lower()
        text_lower = text.lower()

        # Find all occurrences
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break

            # Extract context
            context_start = max(0, pos - context_chars)
            context_end = min(len(text), pos + len(keyword) + context_chars)

            context = text[context_start:context_end].strip()
            contexts.append(context)

            start = pos + 1

        return contexts

    def get_pages_by_url_pattern(self, pattern: str) -> List[CrawledPage]:
        """Get pages matching URL pattern"""
        matching_pages = []

        regex = re.compile(pattern, re.IGNORECASE)

        for page in self.crawled_pages:
            if regex.search(page.url):
                matching_pages.append(page)

        return matching_pages

    def clear(self):
        """Clear crawled data"""
        self.visited_urls.clear()
        self.crawled_pages.clear(
