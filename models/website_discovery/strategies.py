# Discovery strategies for finding corporate websites

import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

from .utils import (
    check_dns_exists,
    extract_company_keywords,
    generate_domain_variations,
    sanitize_url,
)


@dataclass
class SearchResult:
    '''Result from search strategy'''

    url: str
    title: str
    snippet: str
    source: str
    rank: int


class DomainGenerationStrategy:
    '''Strategy for generating and testing potential domains'''

    def __init__(self, max_attempts: int = 20):
        '''
        Initialize domain generation strategy.

        Args:
            max_attempts: Maximum number of domains to test
        '''
        self.max_attempts = max_attempts

    def discover(self, company_name: str) -> List[str]:
        '''
        Generate and test potential domains.

        Args:
            company_name: Company name to discover domain for

        Returns:
            List of valid domains (with DNS records)
        '''
        # Generate variations
        variations = generate_domain_variations(company_name)

        # Limit attempts
        variations = variations[: self.max_attempts]

        # Test which ones have DNS records
        valid_domains = []
        for domain in variations:
            if check_dns_exists(domain):
                valid_domains.append(sanitize_url(domain))
                # Small delay to avoid overwhelming DNS
                time.sleep(0.1)

        return valid_domains


class SearchStrategy:
    '''
    Strategy for using search engines to find corporate websites.

    Supports multiple search engines with API key configuration.
    '''

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        bing_api_key: Optional[str] = None,
    ):
        '''
        Initialize search strategy.

        Args:
            google_api_key: Google Custom Search API key
            google_cx: Google Custom Search Engine ID
            bing_api_key: Bing Search API key
        '''
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.google_cx = google_cx or os.getenv('GOOGLE_CX')
        self.bing_api_key = bing_api_key or os.getenv('BING_API_KEY')

    def discover(self, company_name: str, max_results: int = 10) -> List[SearchResult]:
        '''
        Search for company corporate website.

        Args:
            company_name: Company name to search for
            max_results: Maximum number of results to return

        Returns:
            List of search results
        '''
        results = []

        # Try Google Custom Search if API key available
        if self.google_api_key and self.google_cx:
            results.extend(self._google_search(company_name, max_results=max_results))

        # Try Bing Search if API key available
        elif self.bing_api_key:
            results.extend(self._bing_search(company_name, max_results=max_results))

        # Fallback to DuckDuckGo (no API key required, but limited)
        else:
            results.extend(self._duckduckgo_search(company_name, max_results=max_results))

        return results[:max_results]

    def _google_search(self, company_name: str, max_results: int = 10) -> List[SearchResult]:
        '''
        Search using Google Custom Search API.

        Args:
            company_name: Company name
            max_results: Maximum results

        Returns:
            List of search results
        '''
        results = []
        try:
            queries = [
                f"'{company_name}' corporate website",
                f"'{company_name}' investor relations",
                f"'{company_name}' official website",
            ]

            for query in queries:
                url = 'https://www.googleapis.com/customsearch/v1'
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cx,
                    'q': query,
                    'num': min(max_results, 10),
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()
                items = data.get('items', [])

                for idx, item in enumerate(items):
                    results.append(
                        SearchResult(
                            url=item.get('link', ''),
                            title=item.get('title', ''),
                            snippet=item.get('snippet', ''),
                            source='google',
                            rank=idx + 1,
                        )
                    )

                if results:
                    break  # If we got results, no need to try other queries

                time.sleep(1)  # Rate limiting

        except Exception:
            pass  # Silently fail and try other methods

        return results

    def _bing_search(self, company_name: str, max_results: int = 10) -> List[SearchResult]:
        '''
        Search using Bing Search API.

        Args:
            company_name: Company name
            max_results: Maximum results

        Returns:
            List of search results
        '''
        results = []
        try:
            query = f"'{company_name}' corporate website OR investor relations"
            url = 'https://api.bing.microsoft.com/v7.0/search'

            headers = {'Ocp-Apim-Subscription-Key': self.bing_api_key}
            params = {'q': query, 'count': max_results}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            web_pages = data.get('webPages', {}).get('value', [])

            for idx, page in enumerate(web_pages):
                results.append(
                    SearchResult(
                        url=page.get('url', ''),
                        title=page.get('name', ''),
                        snippet=page.get('snippet', ''),
                        source='bing',
                        rank=idx + 1,
                    )
                )

        except Exception:
            pass  # Silently fail

        return results

    def _duckduckgo_search(self, company_name: str, max_results: int = 10) -> List[SearchResult]:
        '''
        Search using DuckDuckGo (no API key required).

        Note: DuckDuckGo instant answer API is limited.
        This is a fallback when no API keys are available.

        Args:
            company_name: Company name
            max_results: Maximum results

        Returns:
            List of search results
        '''
        results = []
        try:
            # DuckDuckGo instant answer API
            url = 'https://api.duckduckgo.com/'
            params = {
                'q': f'{company_name} official website',
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Try to extract official website
            abstract_url = data.get('AbstractURL', '')
            if abstract_url:
                results.append(
                    SearchResult(
                        url=abstract_url,
                        title=data.get('Heading', ''),
                        snippet=data.get('Abstract', ''),
                        source='duckduckgo',
                        rank=1,
                    )
                )

            # Check related topics
            related = data.get('RelatedTopics', [])
            for idx, topic in enumerate(related[:max_results]):
                if isinstance(topic, dict) and 'FirstURL' in topic:
                    results.append(
                        SearchResult(
                            url=topic.get('FirstURL', ''),
                            title=topic.get('Text', '')[:100],
                            snippet=topic.get('Text', ''),
                            source='duckduckgo',
                            rank=idx + 2,
                        )
                    )

        except Exception:
            pass  # Silently fail

        return results


class LinkedInStrategy:
    '''
    Strategy for finding corporate website via LinkedIn company page.

    LinkedIn company pages typically link to the official corporate website.
    '''

    def discover(self, company_name: str) -> Optional[str]:
        '''
        Find company website via LinkedIn.

        Args:
            company_name: Company name

        Returns:
            Website URL if found, None otherwise
        '''
        # This would require LinkedIn API access or scraping
        # Placeholder for future implementation
        # For now, return None
        return None


class WikipediaStrategy:
    '''
    Strategy for finding corporate website via Wikipedia.

    Many companies have Wikipedia pages with official website links.
    '''

    def discover(self, company_name: str) -> Optional[str]:
        '''
        Find company website via Wikipedia.

        Args:
            company_name: Company name

        Returns:
            Website URL if found, None otherwise
        '''
        try:
            # Use Wikipedia API
            url = 'https://en.wikipedia.org/w/api.php'
            params = {
                'action': 'query',
                'format': 'json',
                'titles': company_name,
                'prop': 'info',
                'inprop': 'url',
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            pages = data.get('query', {}).get('pages', {})

            # Get first page
            for page_id, page_data in pages.items():
                if page_id != '-1':  # Page exists
                    # Would need to parse the page content for official website
                    # This is a simplified version
                    pass

        except Exception:
            pass

        return None
