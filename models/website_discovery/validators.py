# Website validation and scoring for corporate website discovery.'

import re
import ssl
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests


@dataclass
class ValidationResult:
    """
    Result of website validation.

    Attributes:
        is_valid (bool): Whether the website passed validation checks.
        confidence_score (float): Confidence score (0-100) indicating likelihood of being a corporate website.
        indicators (Dict[str, bool]): Dictionary of validation indicators and their boolean results.
        ssl_valid (bool): Whether the website uses a valid SSL certificate.
        response_time (float): Time taken to get a response from the website (in seconds).
        status_code (Optional[int]): HTTP status code returned by the website.
        title (str): Title of the website extracted from HTML.
        description (str): Meta description of the website extracted from HTML.
        corporate_indicators (List[str]): List of detected corporate-related keywords in the website content.
    """

    is_valid: bool
    confidence_score: float  # 0-100
    indicators: Dict[str, bool]
    ssl_valid: bool
    response_time: float
    status_code: Optional[int]
    title: str
    description: str
    corporate_indicators: List[str]


class WebsiteValidator:
    """ Validates and scores potential corporate websites"""

    CORPORATE_INDICATORS = [
        'investor relations',
        'corporate',
        'about us',
        'governance',
        'annual report',
        'press release',
        'leadership',
        'board of directors',
        'our company',
        'corporate information',
        'shareholder',
        'financial information',
        'sustainability',
        'esg',
    ]

    CORPORATE_URL_PATTERNS = [
        r'/investor',
        r'/corporate',
        r'/about',
        r'/governance',
        r'/sustainability',
        r'/company',
    ]

    def __init__(self, timeout: int = 10):
        """ Initialize validator.
        
            Args: timeout: Request timeout in seconds
        """

        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (DSI Corporate Website Discovery Bot)'}
        )

    def validate_website(self, url: str, company_name: str) -> ValidationResult:
        """
        Validate and score a potential corporate website.

        Args:
            url: Website URL to validate
            company_name: Expected company name
        #Returns:
            ValidationResult with confidence score
        
         Initialize result
        """

        indicators = {
            'ssl_valid': False,
            'status_ok': False,
            'corporate_keywords': False,
            'company_name_match': False,
            'corporate_urls': False,
        }

        try:
            # Make request
            import time

            start_time = time.time()
            response = self.session.get(
                url, timeout=self.timeout, allow_redirects=True, verify=True
            )
            response_time = time.time() - start_time

            # Check status
            status_code = response.status_code
            indicators['status_ok'] = 200 <= status_code < 300

            # Check SSL
            ssl_valid = url.startswith('https://')
            indicators['ssl_valid'] = ssl_valid

            # Parse content
            content = response.text.lower()
            title, description = self._extract_metadata(response.text)

            # Check for company name
            company_keywords = company_name.lower().split()
            company_match = any(
                keyword in content for keyword in company_keywords if len(keyword) > 2
            )
            indicators['company_name_match'] = company_match

            # Check for corporate indicators
            found_indicators = []
            for indicator in self.CORPORATE_INDICATORS:
                if indicator in content:
                    found_indicators.append(indicator)

            indicators['corporate_keywords'] = len(found_indicators) >= 3

            # Check for corporate URL patterns
            corporate_urls = any(
                re.search(pattern, content) for pattern in self.CORPORATE_URL_PATTERNS
            )
            indicators['corporate_urls'] = corporate_urls

            # Calculate confidence score
            confidence = self._calculate_confidence(indicators, found_indicators, company_match)

            return ValidationResult(
                is_valid=indicators['status_ok'],
                confidence_score=confidence,
                indicators=indicators,
                ssl_valid=ssl_valid,
                response_time=response_time,
                status_code=status_code,
                title=title,
                description=description,
                corporate_indicators=found_indicators,
            )

        except requests.exceptions.SSLError:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                indicators=indicators,
                ssl_valid=False,
                response_time=0.0,
                status_code=None,
                title='',
                description='',
                corporate_indicators=[],
            )
        except requests.exceptions.Timeout:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                indicators=indicators,
                ssl_valid=False,
                response_time=self.timeout,
                status_code=None,
                title='',
                description='',
                corporate_indicators=[],
            )
        except Exception:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                indicators=indicators,
                ssl_valid=False,
                response_time=0.0,
                status_code=None,
                title='',
                description='',
                corporate_indicators=[],
            )

    def _extract_metadata(self, html: str) -> tuple:
        #Extract title and description from HTML

        title = ''
        description = ''

        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()

        # Extract description
        desc_match = re.search(
            r"<meta[^>]*name=['\']description['\'][^>]*content=['\'](.*?)['\']",
            html,
            re.IGNORECASE,
        )
        if desc_match:
            description = desc_match.group(1).strip()

        return title, description

    def _calculate_confidence(
        self,
        indicators: Dict[str, bool],
        found_indicators: List[str],
        company_match: bool,
    ) -> float:
        '''
        Calculate confidence score based on indicators.

        Args:
            indicators: Dictionary of boolean indicators
            found_indicators: List of found corporate indicators
            company_match: Whether company name was found

        Returns:
            Confidence score 0-100
        '''
        score = 0.0

        # SSL valid: 20 points
        if indicators['ssl_valid']:
            score += 20.0

        # Status OK: 15 points
        if indicators['status_ok']:
            score += 15.0

        # Company name match: 25 points
        if company_match:
            score += 25.0

        # Corporate keywords: up to 30 points
        keyword_score = min(len(found_indicators) * 3, 30)
        score += keyword_score

        # Corporate URLs: 10 points
        if indicators['corporate_urls']:
            score += 10.0

        return min(score, 100.0)

    def check_ssl_certificate(self, url: str) -> Dict[str, any]:
        '''
        Check SSL certificate details.

        Args:
            url: Website URL

        Returns:
            Dictionary with SSL certificate information
        '''
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    return {
                        'valid': True,
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'version': cert.get('version'),
                        'notBefore': cert.get('notBefore'),
                        'notAfter': cert.get('notAfter'),
                    }
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def check_corporate_content(self, url: str) -> Dict[str, any]:
        '''
        Deep check for corporate content indicators.

        Args:
            url: Website URL

        Returns:
            Dictionary with corporate content analysis
        '''
        try:
            response = self.session.get(url, timeout=self.timeout)
            content = response.text.lower()

            # Check for specific corporate pages
            corporate_pages = {
                'investor_relations': 'investor' in content,
                'about_us': 'about us' in content or 'about' in content,
                'press_releases': 'press release' in content or 'news' in content,
                'leadership': 'leadership' in content or 'management team' in content,
                'board': 'board of directors' in content or 'board' in content,
                'careers': 'careers' in content or 'jobs' in content,
                'contact': 'contact us' in content or 'contact' in content,
            }

            # Count corporate indicators
            indicator_count = sum(indicator in content for indicator in self.CORPORATE_INDICATORS)

            return {
                'has_corporate_content': indicator_count >= 3,
                'indicator_count': indicator_count,
                'corporate_pages': corporate_pages,
                'corporate_page_count': sum(corporate_pages.values()),
            }

        except Exception as e:
            return {
                'has_corporate_content': False,
                'indicator_count': 0,
                'corporate_pages': {},
                'corporate_page_count': 0,
                'error': str(e),
            }


import socket
