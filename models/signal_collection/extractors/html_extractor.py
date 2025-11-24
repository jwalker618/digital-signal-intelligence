# HTML content extractor with date awareness

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class HTMLArticle:
    """Extracted article from HTML"""

    title: str
    content: str
    url: str
    published_date: Optional[datetime]
    author: Optional[str]
    tags: List[str]


class HTMLExtractor:
    """Extracts structured content from HTML pages"""

    # Common date formats to try
    DATE_PATTERNS = [
        r"(\d{4})-(\d{2})-(\d{2})",  # 2024-11-22
        r"(\d{2})/(\d{2})/(\d{4})",  # 22/11/2024
        r"(\d{2})-(\d{2})-(\d{4})",  # 22-11-2024
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",  # November 22, 2024
    ]

    def extract_article(self, html: str, url: str) -> Optional[HTMLArticle]:
        """
        Extract article content from HTML.

        Args:
            html: HTML content
            url: Page URL

        Returns:
            HTMLArticle or None
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = self._extract_title(soup)

        # Extract content
        content = self._extract_content(soup)

        # Extract date
        published_date = self._extract_date(soup, html)

        # Extract author
        author = self._extract_author(soup)

        # Extract tags
        tags = self._extract_tags(soup)

        if not content:
            return None

        return HTMLArticle(
            title=title,
            content=content,
            url=url,
            published_date=published_date,
            author=author,
            tags=tags,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try various title sources
        # 1. Article title
        title_tag = soup.find("h1")
        if title_tag:
            return title_tag.get_text().strip()

        # 2. Meta title
        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            return meta_title["content"]

        # 3. Page title
        page_title = soup.find("title")
        if page_title:
            return page_title.get_text().strip()

        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content"""
        # Try to find main content area
        content_areas = [
            soup.find("article"),
            soup.find("main"),
            soup.find("div", class_=re.compile(r"content|post|article")),
            soup.find("div", id=re.compile(r"content|post|article")),
        ]

        for area in content_areas:
            if area:
                # Remove script and style elements
                for script in area(["script", "style", "nav", "footer"]):
                    script.decompose()

                text = area.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = "\n".join(chunk for chunk in chunks if chunk)

                if len(text) > 100:  # Minimum content length
                    return text

        return ""

    def _extract_date(self, soup: BeautifulSoup, html: str) -> Optional[datetime]:
        """Extract publication date"""
        # Try meta tags
        date_metas = [
            soup.find("meta", property="article:published_time"),
            soup.find("meta", property="og:published_time"),
            soup.find("meta", name="publish_date"),
            soup.find("meta", name="date"),
        ]

        for meta in date_metas:
            if meta and meta.get("content"):
                date = self._parse_date(meta["content"])
                if date:
                    return date

        # Try time tags
        time_tag = soup.find("time")
        if time_tag:
            datetime_attr = time_tag.get("datetime")
            if datetime_attr:
                date = self._parse_date(datetime_attr)
                if date:
                    return date

        # Try to find date in text
        date_patterns = [
            r"Published:?\s*(.+?)(?:\n|$)",
            r"Posted:?\s*(.+?)(?:\n|$)",
            r"Date:?\s*(.+?)(?:\n|$)",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                date = self._parse_date(match.group(1))
                if date:
                    return date

        return None

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date from string"""
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        except Exception:
            pass

        # Try common formats
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, date_string)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if pattern.startswith(r"(\d{4})"):
                            # YYYY-MM-DD
                            return datetime(
                                int(groups[0]), int(groups[1]), int(groups[2])
                            )
                        elif groups[0].isdigit():
                            # DD/MM/YYYY or MM/DD/YYYY
                            return datetime(
                                int(groups[2]), int(groups[1]), int(groups[0])
                            )
                        else:
                            # Month name format
                            month_name = groups[0]
                            day = int(groups[1])
                            year = int(groups[2])
                            # Convert month name to number
                            month = datetime.strptime(month_name, "%B").month
                            return datetime(year, month, day)
                except Exception:
                    pass

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author name"""
        # Try meta tags
        author_meta = soup.find("meta", {"name": "author"})
        if author_meta and author_meta.get("content"):
            return author_meta["content"]

        # Try article author
        author_tag = soup.find("span", class_=re.compile(r"author"))
        if author_tag:
            return author_tag.get_text().strip()

        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/categories"""
        tags = []

        # Try meta keywords
        keywords_meta = soup.find("meta", {"name": "keywords"})
        if keywords_meta and keywords_meta.get("content"):
            keywords = keywords_meta["content"]
            tags.extend([k.strip() for k in keywords.split(",")])

        # Try tag elements
        tag_elements = soup.find_all(["a", "span"], class_=re.compile(r"tag|category"))
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text().strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        return tags

    def filter_by_date(
        self, articles: List[HTMLArticle], months: int = 12
    ) -> List[HTMLArticle]:
        """
        Filter articles by date range.

        Args:
            articles: List of articles
            months: Number of months to look back

        Returns:
            Filtered articles
        """
        cutoff_date = datetime.now() - timedelta(days=months * 30)

        filtered = []
        for article in articles:
            if article.published_date:
                if article.published_date >= cutoff_date:
                    filtered.append(article)
            else:
                # Include articles without dates (cautiously)
                filtered.append(article)

        return filtered

    def find_keywords_in_articles(
        self, articles: List[HTMLArticle], keywords: List[str]
    ) -> List[dict]:
        """
        Find keywords in articles.

        Args:
            articles: List of articles
            keywords: Keywords to search for

        Returns:
            List of matches with context
        """
        matches = []

        for article in articles:
            content_lower = article.content.lower()
            title_lower = article.title.lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Check title
                if keyword_lower in title_lower:
                    matches.append(
                        {
                            "article_title": article.title,
                            "article_url": article.url,
                            "keyword": keyword,
                            "found_in": "title",
                            "published_date": article.published_date,
                            "context": article.title,
                        }
                    )

                # Check content
                if keyword_lower in content_lower:
                    # Extract context
                    pos = content_lower.find(keyword_lower)
                    start = max(0, pos - 100)
                    end = min(len(article.content), pos + len(keyword) + 100)
                    context = article.content[start:end].strip()

                    matches.append(
                        {
                            "article_title": article.title,
                            "article_url": article.url,
                            "keyword": keyword,
                            "found_in": "content",
                            "published_date": article.published_date,
                            "context": context,
                        }
                    )

        return matches
